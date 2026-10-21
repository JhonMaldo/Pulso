"""Explicación de una recomendación con Ollama + tools (sección 6.5 del plan).

Regla: el motor calcula y la IA solo explica. El modelo no recibe los números en el
prompt: los pide con las tools `calcular_afinidad` y `obtener_vacante`, que ejecuta
este backend con el perfil que llegó en la petición. Sigue el patrón del agente del
clima del equipo (`/api/chat` con `tools`, `think: false` y mensajes `role: tool`).

Si Ollama falla, tarda demasiado, no soporta tools o escribe un porcentaje distinto
al del motor, se devuelve la plantilla con `fuente: "plantilla"`.
"""
import json
import os
import re
import time
from collections import OrderedDict

import httpx

from motor import afinidad

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODELO = os.getenv("OLLAMA_MODELO", "granite4.2:3b")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "180"))
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "60m")  # el modelo sigue cargado entre explicaciones
MAX_TOOLS = 3
MAX_MEMORIA = 256

NOMBRES = {
    "A1": "Razonamiento lógico", "A2": "Razonamiento numérico",
    "A3": "Comunicación", "A4": "Trabajo en equipo",
    "A5": "Organización y planeación", "A6": "Resolución de problemas",
    "A7": "Atención al detalle", "A8": "Servicio al cliente",
}

SISTEMA = """Eres un orientador laboral. Para explicar una recomendación SIEMPRE llama primero a la herramienta calcular_afinidad con el id de la vacante que te piden (obtener_vacante es opcional, solo si necesitas la descripción).
Usa SOLO los datos que devuelven las herramientas. No inventes datos y no cambies los números: el único porcentaje que puedes escribir es la afinidad que devuelve calcular_afinidad.
No menciones edad, género ni datos personales.
Responde en español, en 2 o 3 oraciones sencillas: por qué encaja la vacante y qué puede mejorar la persona."""

TOOLS = [
    {"type": "function", "function": {
        "name": "calcular_afinidad",
        "description": "Calcula con el motor de Pulso la afinidad (porcentaje de 0 a 100) entre el perfil de la persona y una vacante, con sus fortalezas y brechas.",
        "parameters": {"type": "object", "required": ["vacante_id"], "properties": {
            "vacante_id": {"type": "string", "description": "Id de la vacante, por ejemplo V01"}}}}},
    {"type": "function", "function": {
        "name": "obtener_vacante",
        "description": "Devuelve el título, área, modalidad, descripción y habilidades clave de una vacante del catálogo.",
        "parameters": {"type": "object", "required": ["vacante_id"], "properties": {
            "vacante_id": {"type": "string", "description": "Id de la vacante, por ejemplo V01"}}}}},
]

_memoria = OrderedDict()
_PORCENTAJE = re.compile(r"(\d{1,3}(?:[.,]\d+)?)\s*(?:%|por\s*ciento)", re.IGNORECASE)


def _nombrar(items):
    return [{"aptitud": NOMBRES.get(i["aptitud"], i["aptitud"]), "perfil": i["perfil"], "minimo": i["minimo"]}
            for i in items]


def plantilla(vacante, puntaje, fortalezas, brechas):
    texto = f"Tu afinidad con {vacante['titulo']} es de {puntaje}%."
    if fortalezas:
        texto += " Tus fortalezas para este puesto: " + ", ".join(
            NOMBRES[i["aptitud"]] for i in fortalezas) + "."
    if brechas:
        texto += " Puedes mejorar en: " + ", ".join(
            NOMBRES[i["aptitud"]] for i in brechas) + "."
    return texto


def porcentajes_correctos(texto, puntaje):
    """True si todos los porcentajes del texto son el puntaje del motor."""
    for m in _PORCENTAJE.findall(texto):
        if float(m.replace(",", ".")) != puntaje:
            return False
    return True


def _ejecutar_tool(nombre, argumentos, vacante, perfil):
    """Ejecuta una tool pedida por el modelo. El perfil nunca viene del modelo."""
    if isinstance(argumentos, str):
        try:
            argumentos = json.loads(argumentos)
        except json.JSONDecodeError:
            argumentos = {}
    vid = str((argumentos or {}).get("vacante_id", "")).strip().upper()
    if vid != vacante["id"]:
        return {"error": f"Solo puedes consultar la vacante {vacante['id']}"}
    if nombre == "calcular_afinidad":
        puntaje, fortalezas, brechas = afinidad(perfil, vacante)
        return {"vacante_id": vid, "titulo": vacante["titulo"], "area": vacante["area"], "afinidad": puntaje,
                "fortalezas": _nombrar(fortalezas), "brechas": _nombrar(brechas)}
    if nombre == "obtener_vacante":
        return {k: vacante[k] for k in ("id", "titulo", "area", "modalidad", "descripcion", "habilidades_clave")}
    return {"error": f"Herramienta desconocida: {nombre}"}


def _con_ollama(vacante, perfil, puntaje, cliente):
    """Conversación con tools. Devuelve (texto, herramientas) o lanza una excepción."""
    limite = time.monotonic() + OLLAMA_TIMEOUT
    mensajes = [{"role": "system", "content": SISTEMA},
                {"role": "user", "content": f"Explícame por qué me recomiendan la vacante {vacante['id']} y qué puedo mejorar."}]
    usadas, afinidad_consultada = [], False
    while True:
        restante = limite - time.monotonic()
        if restante <= 0:
            raise TimeoutError("Ollama superó el límite de espera")
        cuerpo = {"model": OLLAMA_MODELO, "messages": mensajes, "stream": False,
                  "think": False, "keep_alive": OLLAMA_KEEP_ALIVE,
                  "options": {"temperature": 0.3, "num_predict": 160}}
        if len(usadas) < MAX_TOOLS:
            cuerpo["tools"] = TOOLS  # al llegar al máximo se pide la respuesta final sin tools
        r = cliente.post(f"{OLLAMA_URL}/api/chat", json=cuerpo, timeout=restante)
        r.raise_for_status()
        mensaje = r.json()["message"]
        llamadas = mensaje.get("tool_calls") or []
        if not llamadas:
            texto = re.sub(r"<think>.*?</think>", "", mensaje.get("content") or "", flags=re.S).strip()
            if not texto or not afinidad_consultada:
                raise ValueError("El modelo respondió sin consultar el motor")
            if not porcentajes_correctos(texto, puntaje):
                raise ValueError("El modelo escribió un porcentaje distinto al del motor")
            return texto, usadas
        mensajes.append(mensaje)
        for llamada in llamadas:
            if len(usadas) >= MAX_TOOLS:
                break
            nombre = llamada.get("function", {}).get("name", "")
            argumentos = llamada.get("function", {}).get("arguments", {})
            resultado = _ejecutar_tool(nombre, argumentos, vacante, perfil)
            if nombre == "calcular_afinidad" and "error" not in resultado:
                afinidad_consultada = True
            usadas.append(f"{nombre}({vacante['id'] if 'error' not in resultado else 'rechazada'})")
            mensajes.append({"role": "tool", "tool_name": nombre,
                             "content": json.dumps(resultado, ensure_ascii=False)})


def explicar(vacante, perfil, cliente=None):
    """Devuelve {"texto", "fuente": "ia" | "plantilla", "herramientas": [...]}."""
    clave = (vacante["id"], tuple(sorted(perfil.items())))
    if clave in _memoria:
        _memoria.move_to_end(clave)
        return dict(_memoria[clave], memoria=True)
    puntaje, fortalezas, brechas = afinidad(perfil, vacante)
    propio = cliente is None
    cliente = cliente or httpx.Client()
    try:
        texto, usadas = _con_ollama(vacante, perfil, puntaje, cliente)
    except Exception:
        # Ollama apagado, lento, sin soporte de tools o con números distintos: plantilla.
        return {"texto": plantilla(vacante, puntaje, fortalezas, brechas), "fuente": "plantilla",
                "herramientas": [], "afinidad": puntaje}
    finally:
        if propio:
            cliente.close()
    resultado = {"texto": texto, "fuente": "ia", "herramientas": usadas, "afinidad": puntaje}
    _memoria[clave] = resultado
    if len(_memoria) > MAX_MEMORIA:
        _memoria.popitem(last=False)
    return dict(resultado)


def estado_ollama(cliente=None):
    """Para /api/salud/ollama: ¿responde Ollama y está el modelo?"""
    try:
        with (cliente or httpx.Client()) as c:
            r = c.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            r.raise_for_status()
            modelos = [m.get("name") for m in r.json().get("models", [])]
        return {"ok": OLLAMA_MODELO in modelos, "modelo": OLLAMA_MODELO, "instalados": modelos}
    except Exception:
        return {"ok": False, "modelo": OLLAMA_MODELO, "instalados": []}

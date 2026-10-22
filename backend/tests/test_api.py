import json

import httpx
import pytest
from fastapi.testclient import TestClient

import ia
import main

cliente = TestClient(main.app)
PREGUNTAS = main.PREGUNTAS["preguntas"]


def respuestas(correctas=True, escala=4):
    r = {}
    for p in PREGUNTAS:
        if p["tipo"] == "opcion_multiple":
            r[str(p["id"])] = p["correcta"] if correctas else (p["correcta"] + 1) % 4
        else:
            r[str(p["id"])] = escala
    return r


def test_salud():
    assert cliente.get("/api/salud").json() == {"ok": True}


def test_prueba_no_revela_la_respuesta_correcta():
    datos = cliente.get("/api/prueba").json()
    assert len(datos["aptitudes"]) == 8 and len(datos["preguntas"]) == 24
    assert all("correcta" not in p for p in datos["preguntas"])


def test_evaluar_devuelve_perfil_y_5_recomendaciones():
    r = cliente.post("/api/evaluar", json={"respuestas": respuestas()})
    assert r.status_code == 200
    datos = r.json()
    assert set(datos["perfil"]) == {f"A{i}" for i in range(1, 9)}
    assert datos["perfil"]["A1"] == 100 and datos["perfil"]["A4"] == 58  # 4, 4 y 4 invertida = (75+75+25)/3
    assert len(datos["recomendaciones"]) == 5
    primera = datos["recomendaciones"][0]
    assert {"vacante", "afinidad", "fortalezas", "brechas"} <= set(primera)
    assert all("nombre" in f for f in primera["fortalezas"])


@pytest.mark.parametrize("cuerpo", [
    {"respuestas": {"1": 2}},                                  # incompletas
    {"respuestas": dict(respuestas(), **{"10": 6})},           # escala fuera de rango
    {"respuestas": dict(respuestas(), **{"1": 4})},            # opción fuera de rango
    {"respuestas": dict(respuestas(), **{"1": "2"})},          # texto en lugar de número
    {"respuestas": dict(respuestas(), **{"x": 1})},            # llave no numérica
    {"respuestas": dict(respuestas(), **{"99": 1})},           # pregunta que no existe
    {"respuestas": respuestas(), "nombre": "Ana"},             # campos extra: no se aceptan datos personales
    {},
])
def test_evaluar_rechaza_datos_invalidos_con_error_claro(cuerpo):
    r = cliente.post("/api/evaluar", json=cuerpo)
    assert r.status_code == 422
    assert "detail" in r.json()
    assert cliente.get("/api/salud").status_code == 200  # el servicio sigue arriba


def test_json_mal_formado_no_tumba_el_servicio():
    r = cliente.post("/api/evaluar", content="{no es json", headers={"content-type": "application/json"})
    assert r.status_code == 422


def test_explicar_valida_vacante_y_perfil():
    assert cliente.post("/api/explicar", json={"vacante_id": "V99", "perfil": {"A1": 50}}).status_code == 404
    assert cliente.post("/api/explicar", json={"vacante_id": "V01", "perfil": {"A1": 150}}).status_code == 422
    assert cliente.post("/api/explicar", json={"vacante_id": "V01", "perfil": {"Z9": 50}}).status_code == 422


def test_explicar_con_ollama_apagado_usa_plantilla(monkeypatch):
    monkeypatch.setattr(ia, "OLLAMA_URL", "http://127.0.0.1:9")
    ia._memoria.clear()
    r = cliente.post("/api/explicar", json={"vacante_id": "V01", "perfil": {"A1": 75, "A6": 45, "A3": 80, "A7": 90}})
    assert r.status_code == 200
    datos = r.json()
    assert datos["fuente"] == "plantilla"
    assert datos["texto"].startswith("Tu afinidad con Desarrollador/a web junior es de")


def test_vacantes():
    assert len(cliente.get("/api/vacantes").json()["vacantes"]) == 20


def test_ruta_api_desconocida():
    assert cliente.get("/api/no-existe").status_code == 404


# ---------- Ollama simulado ----------

VACANTE = main.POR_ID["V01"]
PERFIL = {"A1": 75, "A6": 45, "A3": 80, "A7": 90}


def ollama_simulado(respuestas_modelo, peticiones):
    """Simula /api/chat: devuelve en orden los mensajes de `respuestas_modelo`."""
    cola = list(respuestas_modelo)

    def manejar(request):
        peticiones.append(json.loads(request.content))
        return httpx.Response(200, json={"message": cola.pop(0)})
    return httpx.Client(transport=httpx.MockTransport(manejar))


def pide_tool(nombre, vid="V01"):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"function": {"name": nombre, "arguments": {"vacante_id": vid}}}]}


def test_explicacion_con_tool_calling():
    ia._memoria.clear()
    puntaje = ia.afinidad(PERFIL, VACANTE)[0]
    peticiones = []
    final = {"role": "assistant", "content": f"Tu afinidad es de {puntaje}%. Destacas en razonamiento lógico. Puedes mejorar en resolución de problemas."}
    c = ollama_simulado([pide_tool("calcular_afinidad"), pide_tool("obtener_vacante"), final], peticiones)
    r = ia.explicar(VACANTE, PERFIL, cliente=c)
    assert r["fuente"] == "ia"
    assert r["herramientas"] == ["calcular_afinidad(V01)", "obtener_vacante(V01)"]
    # El modelo no recibe los números en el prompt: llegan solo como respuesta de la tool.
    assert str(puntaje) not in json.dumps(peticiones[0]["messages"])
    assert peticiones[0]["tools"] and peticiones[0]["think"] is False
    ultimo = peticiones[1]["messages"][-1]
    assert ultimo["role"] == "tool" and ultimo["tool_name"] == "calcular_afinidad"
    resultado_tool = json.loads(ultimo["content"])
    assert resultado_tool["afinidad"] == puntaje
    assert {b["aptitud"] for b in resultado_tool["brechas"]} == {"Resolución de problemas"}
    # Memoria: la segunda vez no llama a Ollama.
    otra = ia.explicar(VACANTE, PERFIL, cliente=ollama_simulado([], []))
    assert otra["fuente"] == "ia" and otra["memoria"] is True


def test_porcentaje_equivocado_usa_plantilla():
    ia._memoria.clear()
    final = {"role": "assistant", "content": "Tu afinidad es de 97%, excelente."}
    r = ia.explicar(VACANTE, PERFIL, cliente=ollama_simulado([pide_tool("calcular_afinidad"), final], []))
    assert r["fuente"] == "plantilla"


def test_respuesta_sin_consultar_el_motor_usa_plantilla():
    ia._memoria.clear()
    peticiones = []
    sin_tool = {"role": "assistant", "content": "Encajas bien."}
    r = ia.explicar(VACANTE, PERFIL, cliente=ollama_simulado([sin_tool, sin_tool], peticiones))
    assert r["fuente"] == "plantilla"
    assert len(peticiones) == 2  # un solo recordatorio
    assert "calcular_afinidad" in peticiones[1]["messages"][-1]["content"]


def test_recordatorio_lleva_al_modelo_a_usar_la_tool():
    ia._memoria.clear()
    puntaje = ia.afinidad(PERFIL, VACANTE)[0]
    plan = {"role": "assistant", "content": "Primero calcularé la afinidad y luego te explico."}
    final = {"role": "assistant", "content": f"Tu afinidad es de {puntaje} %, con 75 % en razonamiento lógico."}
    r = ia.explicar(VACANTE, PERFIL, cliente=ollama_simulado([plan, pide_tool("calcular_afinidad"), final], []))
    assert r["fuente"] == "ia" and r["herramientas"] == ["calcular_afinidad(V01)"]


def test_tool_con_otra_vacante_se_rechaza_y_limita_a_3_llamadas():
    ia._memoria.clear()
    peticiones = []
    final = {"role": "assistant", "content": "Sin datos."}
    c = ollama_simulado([pide_tool("calcular_afinidad", "V02"), pide_tool("calcular_afinidad", "V03"),
                         pide_tool("calcular_afinidad", "V04"), final], peticiones)
    r = ia.explicar(VACANTE, PERFIL, cliente=c)
    assert r["fuente"] == "plantilla"
    assert "tools" not in peticiones[-1]  # tras 3 llamadas se pide la respuesta sin tools
    assert "Solo puedes consultar la vacante V01" in peticiones[1]["messages"][-1]["content"]


def test_modelo_sin_soporte_de_tools_usa_plantilla():
    ia._memoria.clear()
    c = httpx.Client(transport=httpx.MockTransport(
        lambda req: httpx.Response(400, json={"error": "model does not support tools"})))
    assert ia.explicar(VACANTE, PERFIL, cliente=c)["fuente"] == "plantilla"


def test_porcentajes_correctos():
    assert ia.porcentajes_correctos("Tienes 89 % de afinidad", 89)
    assert ia.porcentajes_correctos("Sin porcentajes", 89)
    assert not ia.porcentajes_correctos("Tienes 89% y antes 75 por ciento", 89)
    assert not ia.porcentajes_correctos("Tienes 89.3%", 89)
    # Números del motor: afinidad, perfil y mínimos de la vacante; nada más.
    permitidos = ia._numeros_del_motor(VACANTE, PERFIL, 92)
    assert ia.porcentajes_correctos("Afinidad 92 %; razonamiento 75 % de 60 % requerido", permitidos)
    assert not ia.porcentajes_correctos("Afinidad 92 % y 85 % en liderazgo", permitidos)

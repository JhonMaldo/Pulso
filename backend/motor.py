"""Motor de Pulso: calcula el perfil de aptitudes y la afinidad con cada vacante.

El motor es la única pieza que produce números. La IA (ia.py) solo los explica.
Fórmulas en la sección 6.4 del plan.
"""


def puntaje_pregunta(pregunta, valor):
    """Convierte una respuesta en un puntaje de 0 a 100."""
    if pregunta["tipo"] == "opcion_multiple":
        return 100 if valor == pregunta["correcta"] else 0
    if pregunta.get("invertida"):
        valor = 6 - valor
    return (valor - 1) / 4 * 100


def validar_respuestas(preguntas, respuestas):
    """Revisa que estén todas las respuestas y que cada valor esté en su rango.

    respuestas: {id_de_pregunta (int): valor (int)}. Lanza ValueError con un mensaje claro.
    """
    por_id = {p["id"]: p for p in preguntas}
    extra = sorted(set(respuestas) - set(por_id))
    if extra:
        raise ValueError(f"Preguntas que no existen: {extra}")
    faltan = sorted(set(por_id) - set(respuestas))
    if faltan:
        raise ValueError(f"Faltan respuestas de las preguntas: {faltan}")
    for pid, valor in respuestas.items():
        p = por_id[pid]
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ValueError(f"La respuesta de la pregunta {pid} debe ser un número entero")
        if p["tipo"] == "opcion_multiple":
            if not 0 <= valor < len(p["opciones"]):
                raise ValueError(f"La pregunta {pid} solo acepta opciones de 0 a {len(p['opciones']) - 1}")
        elif not 1 <= valor <= 5:
            raise ValueError(f"La pregunta {pid} solo acepta valores de 1 a 5")


def calcular_perfil(preguntas, respuestas):
    """respuestas: {id_de_pregunta: valor}. Devuelve {aptitud: puntaje de 0 a 100}."""
    puntos = {}
    for p in preguntas:
        if p["id"] not in respuestas:
            continue
        puntos.setdefault(p["aptitud"], []).append(puntaje_pregunta(p, respuestas[p["id"]]))
    return {a: round(sum(lista) / len(lista)) for a, lista in puntos.items()}


def afinidad(perfil, vacante):
    """Devuelve (puntaje, fortalezas, brechas) de un perfil contra una vacante.

    cumplimiento = min(perfil / mínimo, 1); afinidad = 100 * suma(peso * cumplimiento) / suma(peso)
    """
    suma, total = 0, 0
    fortalezas, brechas = [], []
    for apt, req in vacante["requisitos"].items():
        minimo, peso = req["minimo"], req["peso"]
        valor = perfil.get(apt, 0)
        cumplimiento = min(valor / minimo, 1) if minimo > 0 else 1
        suma += peso * cumplimiento
        total += peso
        dato = {"aptitud": apt, "perfil": valor, "minimo": minimo, "peso": peso}
        (fortalezas if valor >= minimo else brechas).append(dato)
    puntaje = round(100 * suma / total) if total else 0
    return puntaje, fortalezas, brechas


# Niveles de preparación para el puesto que mejor le queda a la persona (estadística del panel del jefe).
UMBRAL_REFORZAR = 75
NIVELES = {
    "preparado": "Preparado",
    "reforzar": "Le faltan habilidades",
    "no_apto": "No apto por ahora",
}


def clasificar(puntaje, brechas):
    """preparado: cumple todos los mínimos · reforzar: tiene brechas pero afinidad >= 75 · no_apto: afinidad < 75."""
    if not brechas:
        return "preparado"
    return "reforzar" if puntaje >= UMBRAL_REFORZAR else "no_apto"


def _margen(perfil, vacante):
    """Promedio ponderado del perfil sin tope. Solo desempata vacantes con la misma afinidad."""
    reqs = vacante["requisitos"].values()
    total = sum(r["peso"] for r in reqs)
    suma = sum(r["peso"] * perfil.get(a, 0) for a, r in vacante["requisitos"].items())
    return suma / total if total else 0


def recomendar(perfil, vacantes, n=5):
    """Las n vacantes con mayor afinidad. Empates: mayor margen sobre los mínimos, luego el id."""
    resultados = []
    for v in vacantes:
        puntaje, fortalezas, brechas = afinidad(perfil, v)
        resultados.append({"vacante": v, "afinidad": puntaje,
                           "fortalezas": fortalezas, "brechas": brechas})
    resultados.sort(key=lambda r: (-r["afinidad"], -_margen(perfil, r["vacante"]), r["vacante"]["id"]))
    return resultados[:n]

import json
from pathlib import Path

import pytest

from motor import afinidad, calcular_perfil, recomendar, validar_respuestas
from validar_datos import validar

DATOS = Path(__file__).resolve().parents[1] / "datos"
PREGUNTAS = json.loads((DATOS / "preguntas.json").read_text(encoding="utf-8"))
VACANTES = json.loads((DATOS / "vacantes.json").read_text(encoding="utf-8"))
AREA = {v["id"]: v["area"] for v in VACANTES["vacantes"]}


def test_afinidad_ejemplo_resuelto():
    vacante = {"requisitos": {
        "A1": {"minimo": 60, "peso": 3},
        "A6": {"minimo": 60, "peso": 3},
        "A3": {"minimo": 40, "peso": 1},
    }}
    perfil = {"A1": 75, "A6": 45, "A3": 80}
    puntaje, fortalezas, brechas = afinidad(perfil, vacante)
    assert puntaje == 89
    assert [f["aptitud"] for f in fortalezas] == ["A1", "A3"]
    assert [b["aptitud"] for b in brechas] == ["A6"]


def test_pregunta_invertida():
    p = [{"id": 1, "aptitud": "A4", "tipo": "escala", "invertida": True},
         {"id": 2, "aptitud": "A5", "tipo": "escala", "invertida": False}]
    assert calcular_perfil(p, {1: 5, 2: 5}) == {"A4": 0, "A5": 100}
    assert calcular_perfil(p, {1: 1, 2: 1}) == {"A4": 100, "A5": 0}
    assert calcular_perfil(p, {1: 3, 2: 3}) == {"A4": 50, "A5": 50}


def test_opcion_multiple_y_promedio():
    p = [{"id": 1, "aptitud": "A1", "tipo": "opcion_multiple", "opciones": ["a", "b", "c", "d"], "correcta": 2},
         {"id": 2, "aptitud": "A1", "tipo": "opcion_multiple", "opciones": ["a", "b", "c", "d"], "correcta": 0}]
    assert calcular_perfil(p, {1: 2, 2: 3}) == {"A1": 50}


def test_minimo_en_cero_no_divide_entre_cero():
    vacante = {"requisitos": {"A1": {"minimo": 0, "peso": 2}, "A2": {"minimo": 60, "peso": 2}}}
    puntaje, fortalezas, brechas = afinidad({"A1": 0, "A2": 30}, vacante)
    assert puntaje == 75
    assert [f["aptitud"] for f in fortalezas] == ["A1"]
    assert [b["aptitud"] for b in brechas] == ["A2"]


def test_aptitud_ausente_cuenta_como_cero():
    puntaje, _, brechas = afinidad({}, {"requisitos": {"A1": {"minimo": 60, "peso": 3}}})
    assert puntaje == 0 and brechas[0]["perfil"] == 0


TECNICO = {"A1": 90, "A2": 85, "A3": 50, "A4": 40, "A5": 40, "A6": 85, "A7": 80, "A8": 30}
SERVICIO = {"A1": 35, "A2": 30, "A3": 85, "A4": 85, "A5": 60, "A6": 45, "A7": 45, "A8": 90}
EQUILIBRADO = {a: 55 for a in TECNICO}


def test_perfil_tecnico_recibe_desarrollo_datos_o_soporte():
    top = recomendar(TECNICO, VACANTES["vacantes"])
    assert len(top) == 5
    assert all(AREA[r["vacante"]["id"]] in {"Desarrollo de software", "Datos", "Infraestructura y soporte"} for r in top)
    assert top[0]["afinidad"] == 100


def test_perfil_de_servicio_recibe_atencion_y_ventas():
    top = recomendar(SERVICIO, VACANTES["vacantes"])
    ids = [r["vacante"]["id"] for r in top]
    assert {"V13", "V15"} <= set(ids)
    assert not any(AREA[i] in {"Desarrollo de software", "Datos"} for i in ids)


def test_perfil_equilibrado_tiene_afinidad_media_alta_en_todo():
    todas = recomendar(EQUILIBRADO, VACANTES["vacantes"], n=len(VACANTES["vacantes"]))
    assert all(85 <= r["afinidad"] < 100 for r in todas)
    puntajes = [r["afinidad"] for r in todas]
    assert puntajes == sorted(puntajes, reverse=True)


def test_recomendar_no_modifica_el_catalogo():
    antes = json.dumps(VACANTES, sort_keys=True)
    recomendar(TECNICO, VACANTES["vacantes"])
    assert json.dumps(VACANTES, sort_keys=True) == antes


def respuestas_completas(valor_om=0, valor_escala=3):
    return {p["id"]: valor_om if p["tipo"] == "opcion_multiple" else valor_escala for p in PREGUNTAS["preguntas"]}


def test_validar_respuestas_acepta_completas():
    validar_respuestas(PREGUNTAS["preguntas"], respuestas_completas())


@pytest.mark.parametrize("cambio, mensaje", [
    ({1: 4}, "opciones de 0 a 3"),
    ({10: 6}, "de 1 a 5"),
    ({10: 0}, "de 1 a 5"),
    ({99: 1}, "no existen"),
    ({10: True}, "entero"),
])
def test_validar_respuestas_rechaza_invalidas(cambio, mensaje):
    r = respuestas_completas()
    r.update(cambio)
    with pytest.raises(ValueError, match=mensaje):
        validar_respuestas(PREGUNTAS["preguntas"], r)


def test_validar_respuestas_rechaza_incompletas():
    r = respuestas_completas()
    del r[5]
    with pytest.raises(ValueError, match="Faltan"):
        validar_respuestas(PREGUNTAS["preguntas"], r)


def test_datos_del_repositorio_son_validos():
    assert validar(PREGUNTAS, VACANTES) == []
    assert 16 <= len(PREGUNTAS["preguntas"]) <= 24


def test_validador_detecta_peso_en_cero_y_correcta_fuera_de_rango():
    malas = json.loads(json.dumps(PREGUNTAS))
    malas["preguntas"][0]["correcta"] = 7
    vac = json.loads(json.dumps(VACANTES))
    vac["vacantes"][0]["requisitos"]["A1"]["peso"] = 0
    errores = validar(malas, vac)
    assert any("correcta" in e for e in errores)
    assert any("peso en cero" in e for e in errores)

import logging

from fastapi.testclient import TestClient

import main

cliente = TestClient(main.app)


def apoyo(texto):
    r = cliente.post("/api/apoyo", json={"texto": texto})
    assert r.status_code == 200
    return r.json()


def test_entrevista_recupera_el_tag_problem_en_espanol():
    r = apoyo("estoy nervioso por mi entrevista")
    assert r["tag"] == "problem" and r["similitud"] >= 0.3 and not r["crisis"]
    assert "Lamento saberlo" in r["respuesta"]
    assert "no es atención profesional" in r["aviso"]


def test_texto_sin_relacion_da_mensaje_general():
    r = apoyo("receta de pastel de chocolate")
    assert r["tag"] is None and r["similitud"] < 0.3
    assert r["respuesta"].startswith("No encontré")


def test_preguntas_sobre_el_chatbot_no_se_responden():
    for texto in ["quien te creo", "cuentame un chiste", "donde vives"]:
        assert apoyo(texto)["tag"] is None


def test_frase_de_crisis_muestra_linea_de_la_vida_y_911():
    for texto in ["ya no quiero vivir", "pienso en quitarme la vida", "a veces pienso en el suicidio", "quiero matarme"]:
        r = apoyo(texto)
        assert r["crisis"] is True and r["tag"] == "suicide"
        assert "800 911 2000" in r["respuesta"] and "911" in r["contacto"]


def test_crisis_detectada_por_el_dataset_en_ingles():
    assert apoyo("I want to kill myself")["crisis"] is True


def test_validaciones_de_longitud_y_campos():
    assert cliente.post("/api/apoyo", json={"texto": ""}).status_code == 422
    assert cliente.post("/api/apoyo", json={"texto": "   "}).status_code == 422
    largo = cliente.post("/api/apoyo", json={"texto": "a" * 501})
    assert largo.status_code == 422 and "aaaa" not in largo.text  # no repite el texto
    assert cliente.post("/api/apoyo", json={"texto": "hola", "perfil": {}}).status_code == 422


def test_no_registra_el_texto_en_logs(caplog):
    with caplog.at_level(logging.DEBUG):
        apoyo("texto privado de prueba sobre mi entrevista")
    assert "texto privado" not in caplog.text


def test_apoyo_no_cambia_la_evaluacion():
    respuestas = {str(p["id"]): (p.get("correcta", 0) if p["tipo"] == "opcion_multiple" else 3)
                  for p in main.PREGUNTAS["preguntas"]}
    antes = cliente.post("/api/evaluar", json={"respuestas": respuestas}).json()
    apoyo("me siento triste porque no encuentro trabajo")
    despues = cliente.post("/api/evaluar", json={"respuestas": respuestas}).json()
    assert antes == despues

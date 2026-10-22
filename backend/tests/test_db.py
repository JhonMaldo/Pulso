import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

import db
import ia
import main

cliente = TestClient(main.app)
DATOS = main.BASE / "datos"


def respuestas_completas():
    return {str(p["id"]): (p["correcta"] if p["tipo"] == "opcion_multiple" else 3) for p in main.PREGUNTAS["preguntas"]}


def tablas():
    with db.conectar() as con:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def test_esquema_y_catalogo_igual_a_los_json():
    assert {"aptitudes", "preguntas", "vacantes", "requisitos", "evaluaciones",
            "evaluacion_aptitudes", "evaluacion_recomendaciones", "explicaciones"} <= tablas()
    preguntas_json = json.loads((DATOS / "preguntas.json").read_text(encoding="utf-8"))
    vacantes_json = json.loads((DATOS / "vacantes.json").read_text(encoding="utf-8"))
    desde_db = db.cargar_preguntas()
    assert desde_db["aptitudes"] == preguntas_json["aptitudes"]
    assert desde_db["preguntas"] == preguntas_json["preguntas"]
    assert db.cargar_vacantes() == vacantes_json["vacantes"]


def test_la_api_lee_el_catalogo_desde_sqlite():
    assert main.VACANTES == db.cargar_vacantes()
    assert len(cliente.get("/api/prueba").json()["preguntas"]) == 24


def test_volver_a_inicializar_no_duplica_el_catalogo():
    vacantes_json = json.loads((DATOS / "vacantes.json").read_text(encoding="utf-8"))
    db.inicializar(json.loads((DATOS / "preguntas.json").read_text(encoding="utf-8")), vacantes_json)
    with db.conectar() as con:
        assert con.execute("SELECT COUNT(*) FROM preguntas").fetchone()[0] == 24
        assert con.execute("SELECT COUNT(*) FROM vacantes").fetchone()[0] == 20
        assert con.execute("SELECT COUNT(*) FROM requisitos").fetchone()[0] == sum(
            len(v["requisitos"]) for v in vacantes_json["vacantes"])


def test_evaluar_registra_una_evaluacion_anonima():
    antes = db.resumen()["evaluaciones"]
    datos = cliente.post("/api/evaluar", json={"respuestas": respuestas_completas()}).json()
    with db.conectar() as con:
        eid = con.execute("SELECT MAX(id) FROM evaluaciones").fetchone()[0]
        perfil = dict(con.execute("SELECT aptitud_id, puntaje FROM evaluacion_aptitudes WHERE evaluacion_id = ?", (eid,)).fetchall())
        recs = con.execute("SELECT posicion, vacante_id, afinidad FROM evaluacion_recomendaciones "
                           "WHERE evaluacion_id = ? ORDER BY posicion", (eid,)).fetchall()
        columnas = {r[1] for t in ("evaluaciones", "evaluacion_aptitudes", "evaluacion_recomendaciones")
                    for r in con.execute(f"PRAGMA table_info({t})")}
    assert db.resumen()["evaluaciones"] == antes + 1
    assert perfil == datos["perfil"]
    assert [(r[1], r[2]) for r in recs] == [(r["vacante"]["id"], r["afinidad"]) for r in datos["recomendaciones"]]
    assert not columnas & {"alias", "nombre", "respuestas", "ip", "texto"}  # nada que identifique a la persona


def test_evaluacion_invalida_no_se_registra():
    antes = db.resumen()["evaluaciones"]
    cliente.post("/api/evaluar", json={"respuestas": {"1": 9}})
    assert db.resumen()["evaluaciones"] == antes


def test_el_modulo_de_apoyo_no_escribe_en_la_base_de_datos():
    with db.conectar() as con:
        antes = [con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in sorted(tablas())]
    cliente.post("/api/apoyo", json={"texto": "estoy nervioso por mi entrevista"})
    with db.conectar() as con:
        despues = [con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in sorted(tablas())]
    assert antes == despues


def test_explicar_registra_fuente_y_tiempo(monkeypatch):
    monkeypatch.setattr(ia, "OLLAMA_URL", "http://127.0.0.1:9")
    ia._memoria.clear()
    antes = db.resumen()["explicaciones"]["con_plantilla"]
    cliente.post("/api/explicar", json={"vacante_id": "V02", "perfil": {"A1": 70, "A6": 40}})
    assert db.resumen()["explicaciones"]["con_plantilla"] == antes + 1


def test_resumen_de_reportes():
    cliente.post("/api/evaluar", json={"respuestas": respuestas_completas()})
    r = cliente.get("/api/reportes/resumen").json()
    assert r["evaluaciones"] >= 1
    assert len(r["aptitudes"]) == 8 and all(0 <= a["promedio"] <= 100 for a in r["aptitudes"])
    assert len(r["vacantes"]) == 20
    assert sum(v["veces_top5"] for v in r["vacantes"]) == 5 * r["evaluaciones"]
    assert sum(v["veces_primera"] for v in r["vacantes"]) == r["evaluaciones"]
    assert r["por_dia"][-1]["fecha"] == db.hoy()


def test_filtro_de_fechas():
    assert cliente.get("/api/reportes/resumen?desde=2000-01-01&hasta=2000-01-02").json()["evaluaciones"] == 0
    assert cliente.get("/api/reportes/resumen?desde=ayer").status_code == 422
    assert cliente.get("/api/reportes/resumen?desde=2026-10-30&hasta=2026-10-01").status_code == 422


def test_csv_anonimo():
    r = cliente.get("/api/reportes/evaluaciones.csv")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    lineas = r.text.strip().split("\n")
    assert lineas[0] == "evaluacion,fecha,A1,A2,A3,A4,A5,A6,A7,A8,vacante_1,afinidad_1"
    assert len(lineas) - 1 == db.resumen()["evaluaciones"]


def test_clave_de_reportes(monkeypatch):
    monkeypatch.setattr(main, "REPORTES_CLAVE", "clave-de-prueba")
    assert cliente.get("/api/reportes/acceso").json() == {"requiere_clave": True}
    assert cliente.get("/api/reportes/resumen").status_code == 401
    assert cliente.get("/api/reportes/resumen", headers={"X-Clave-Reportes": "otra"}).status_code == 401
    assert cliente.get("/api/reportes/resumen", headers={"X-Clave-Reportes": "clave-de-prueba"}).status_code == 200
    assert cliente.get("/api/reportes/evaluaciones.csv").status_code == 401


def test_restricciones_del_esquema():
    with pytest.raises(sqlite3.IntegrityError):
        with db.conectar() as con:
            con.execute("INSERT INTO requisitos VALUES ('V01', 'A2', 50, 0, 9)")  # peso en cero
    with pytest.raises(sqlite3.IntegrityError):
        with db.conectar() as con:
            con.execute("INSERT INTO evaluacion_recomendaciones VALUES (999999, 1, 'V01', 90)")  # evaluación inexistente

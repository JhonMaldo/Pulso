import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

import db
import ia
import main
from motor import clasificar

cliente = TestClient(main.app)
DATOS = main.BASE / "datos"
CLAVE = "clave-de-prueba-jefe"
JEFE = {"X-Clave-Jefe": CLAVE}

PUESTO = {
    "titulo": "Recepcionista bilingüe", "empresa": "Hotel de prueba", "area": "Atención y ventas",
    "modalidad": "Presencial", "descripcion": "Recibe huéspedes, agenda reservaciones y atiende llamadas.",
    "habilidades_clave": ["Inglés", "Atención telefónica"],
    "requisitos": {"A8": "clave", "A3": "importante", "A5": "deseable"},
}


@pytest.fixture(autouse=True)
def sin_ollama(monkeypatch):
    # Las pruebas nunca llaman al Ollama real (aunque esté encendido en la PC).
    monkeypatch.setattr(ia, "OLLAMA_URL", "http://127.0.0.1:9")


@pytest.fixture
def jefe(monkeypatch):
    monkeypatch.setattr(main, "JEFE_CLAVE", CLAVE)


def respuestas(om=None, escala=3):
    return {str(p["id"]): (p["correcta"] if om is None else om) if p["tipo"] == "opcion_multiple" else escala
            for p in main.PREGUNTAS["preguntas"]}


def tablas():
    with db.conectar() as con:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}


def contar(tabla):
    with db.conectar() as con:
        return con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]


# ---------- Esquema y catálogo ----------

def test_esquema_solo_guarda_resultados():
    assert {"aptitudes", "preguntas", "vacantes", "requisitos", "resultados"} <= tablas()
    assert not tablas() & {"evaluaciones", "evaluacion_aptitudes", "evaluacion_recomendaciones", "explicaciones"}
    with db.conectar() as con:
        columnas = {r[1] for r in con.execute("PRAGMA table_info(resultados)")}
    assert columnas == {"id", "fecha", "vacante_id", "afinidad", "brechas", "nivel"}


def test_catalogo_igual_a_los_json():
    preguntas_json = json.loads((DATOS / "preguntas.json").read_text(encoding="utf-8"))
    vacantes_json = json.loads((DATOS / "vacantes.json").read_text(encoding="utf-8"))
    desde_db = db.cargar_preguntas()
    assert desde_db["aptitudes"] == preguntas_json["aptitudes"]
    assert desde_db["preguntas"] == preguntas_json["preguntas"]
    catalogo = [v for v in db.cargar_vacantes(incluir_inactivas=True) if v["id"].startswith("V")]
    assert catalogo == vacantes_json["vacantes"]


def test_migra_una_base_de_la_version_anterior(tmp_path, monkeypatch):
    vieja = tmp_path / "vieja.db"
    con = sqlite3.connect(vieja)
    con.executescript("""
        CREATE TABLE vacantes (id TEXT PRIMARY KEY, titulo TEXT NOT NULL, empresa TEXT NOT NULL, area TEXT NOT NULL,
            modalidad TEXT NOT NULL, descripcion TEXT NOT NULL, habilidades_clave TEXT NOT NULL);
        CREATE TABLE evaluaciones (id INTEGER PRIMARY KEY, fecha TEXT NOT NULL);
        CREATE TABLE evaluacion_aptitudes (evaluacion_id INTEGER, aptitud_id TEXT, puntaje INTEGER);
        CREATE TABLE explicaciones (id INTEGER PRIMARY KEY, fecha TEXT);
        INSERT INTO evaluaciones VALUES (1, '2026-10-21');
    """)
    con.close()
    monkeypatch.setattr(db, "DB_PATH", vieja)
    db.inicializar(json.loads((DATOS / "preguntas.json").read_text(encoding="utf-8")),
                   json.loads((DATOS / "vacantes.json").read_text(encoding="utf-8")))
    assert not tablas() & {"evaluaciones", "evaluacion_aptitudes", "explicaciones"}
    assert "resultados" in tablas()
    assert len(db.cargar_vacantes()) == 20
    with db.conectar() as con:
        assert con.execute("PRAGMA user_version").fetchone()[0] == db.VERSION_ESQUEMA


# ---------- Resultados ----------

def test_clasificacion():
    assert clasificar(100, []) == "preparado"
    assert clasificar(75, [{"aptitud": "A1"}]) == "reforzar"
    assert clasificar(92, [{"aptitud": "A1"}]) == "reforzar"
    assert clasificar(74, [{"aptitud": "A1"}]) == "no_apto"


def test_evaluar_guarda_solo_el_resultado():
    antes = contar("resultados")
    datos = cliente.post("/api/evaluar", json={"respuestas": respuestas()}).json()
    mejor = datos["recomendaciones"][0]
    with db.conectar() as con:
        r = dict(con.execute("SELECT * FROM resultados ORDER BY id DESC LIMIT 1").fetchone())
    assert contar("resultados") == antes + 1
    assert (r["vacante_id"], r["afinidad"], r["brechas"]) == (mejor["vacante"]["id"], mejor["afinidad"], len(mejor["brechas"]))
    assert r["nivel"] == datos["nivel"] == mejor["nivel"] == clasificar(mejor["afinidad"], mejor["brechas"])
    assert r["fecha"] == db.hoy()


def test_niveles_segun_las_respuestas():
    todo_bien = cliente.post("/api/evaluar", json={"respuestas": respuestas(escala=5)}).json()
    assert todo_bien["nivel"] == "preparado"
    malas = {p["id"]: (p["correcta"] + 1) % 4 for p in main.PREGUNTAS["preguntas"] if p["tipo"] == "opcion_multiple"}
    todo_mal = {str(p["id"]): malas.get(p["id"], 1 if not p.get("invertida") else 5) for p in main.PREGUNTAS["preguntas"]}
    assert cliente.post("/api/evaluar", json={"respuestas": todo_mal}).json()["nivel"] == "no_apto"


def test_evaluacion_invalida_y_apoyo_no_escriben():
    antes = contar("resultados")
    cliente.post("/api/evaluar", json={"respuestas": {"1": 9}})
    cliente.post("/api/apoyo", json={"texto": "estoy nervioso por mi entrevista"})
    cliente.post("/api/explicar", json={"vacante_id": "V01", "perfil": {"A1": 50}})
    assert contar("resultados") == antes


# ---------- Panel del jefe: acceso ----------

def test_panel_cerrado_sin_clave_configurada(monkeypatch):
    monkeypatch.setattr(main, "JEFE_CLAVE", "")
    for ruta in ("/api/jefe/acceso", "/api/jefe/estadisticas", "/api/jefe/puestos", "/api/jefe/resultados.csv"):
        assert cliente.get(ruta, headers=JEFE).status_code == 503
    assert cliente.post("/api/jefe/puestos", json=PUESTO, headers=JEFE).status_code == 503


def test_clave_incorrecta(jefe):
    assert cliente.get("/api/jefe/acceso").status_code == 401
    assert cliente.get("/api/jefe/acceso", headers={"X-Clave-Jefe": "otra"}).status_code == 401
    assert cliente.post("/api/jefe/puestos", json=PUESTO).status_code == 401
    assert cliente.get("/api/jefe/acceso", headers=JEFE).json()["umbral_reforzar"] == 75


# ---------- Panel del jefe: estadísticas ----------

def test_estadisticas(jefe):
    cliente.post("/api/evaluar", json={"respuestas": respuestas(escala=5)})
    e = cliente.get("/api/jefe/estadisticas", headers=JEFE).json()
    assert e["evaluaciones"] == contar("resultados") >= 1
    assert sum(e["niveles"].values()) == e["evaluaciones"]
    assert sum(p["personas"] for p in e["por_puesto"]) == e["evaluaciones"]
    assert all(p["preparado"] + p["reforzar"] + p["no_apto"] == p["personas"] for p in e["por_puesto"])
    assert e["por_dia"][-1]["fecha"] == db.hoy()
    vacio = cliente.get("/api/jefe/estadisticas?desde=2000-01-01&hasta=2000-01-02", headers=JEFE).json()
    assert vacio["evaluaciones"] == 0 and vacio["niveles"] == {"preparado": 0, "reforzar": 0, "no_apto": 0}
    assert cliente.get("/api/jefe/estadisticas?desde=ayer", headers=JEFE).status_code == 422


def test_csv_de_resultados(jefe):
    r = cliente.get("/api/jefe/resultados.csv", headers=JEFE)
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    lineas = r.text.strip().split("\n")
    assert lineas[0] == "resultado,fecha,vacante,titulo,afinidad,brechas,nivel"
    assert len(lineas) - 1 == contar("resultados")


# ---------- Panel del jefe: puestos ----------

def test_jefe_agrega_un_puesto_y_se_recomienda(jefe):
    r = cliente.post("/api/jefe/puestos", json=PUESTO, headers=JEFE)
    assert r.status_code == 201
    p = r.json()
    assert p["id"].startswith("P") and p["origen"] == "jefe" and p["activa"] is True
    assert p["requisitos"] == {"A8": {"minimo": 60, "peso": 3}, "A3": {"minimo": 50, "peso": 2},
                               "A5": {"minimo": 40, "peso": 1}}
    assert p["id"] in {v["id"] for v in cliente.get("/api/vacantes").json()["vacantes"]}
    # Una persona fuerte en servicio y comunicación ve el puesto nuevo entre sus recomendaciones.
    servicio = {str(q["id"]): (q["correcta"] if q["aptitud"] in ("A3",) else (q["correcta"] + 1) % 4)
                if q["tipo"] == "opcion_multiple" else (5 if not q["invertida"] else 1) for q in main.PREGUNTAS["preguntas"]}
    recs = cliente.post("/api/evaluar", json={"respuestas": servicio}).json()["recomendaciones"]
    assert p["id"] in [x["vacante"]["id"] for x in recs]
    # Se puede explicar con la IA (o la plantilla) como cualquier vacante.
    assert cliente.post("/api/explicar", json={"vacante_id": p["id"], "perfil": {"A8": 90}}).status_code == 200


def test_el_puesto_del_jefe_sobrevive_a_reiniciar(jefe):
    p = cliente.post("/api/jefe/puestos", json=dict(PUESTO, titulo="Puesto persistente"), headers=JEFE).json()
    db.inicializar(json.loads((DATOS / "preguntas.json").read_text(encoding="utf-8")),
                   json.loads((DATOS / "vacantes.json").read_text(encoding="utf-8")))
    guardado = next(v for v in db.cargar_vacantes(incluir_inactivas=True) if v["id"] == p["id"])
    assert guardado["titulo"] == "Puesto persistente" and len(guardado["requisitos"]) == 3


def test_desactivar_y_reactivar(jefe):
    p = cliente.post("/api/jefe/puestos", json=dict(PUESTO, titulo="Puesto temporal"), headers=JEFE).json()
    assert cliente.patch(f"/api/jefe/puestos/{p['id']}", json={"activa": False}, headers=JEFE).status_code == 200
    assert p["id"] not in {v["id"] for v in cliente.get("/api/vacantes").json()["vacantes"]}
    assert cliente.post("/api/explicar", json={"vacante_id": p["id"], "perfil": {"A8": 90}}).status_code == 404
    lista = cliente.get("/api/jefe/puestos", headers=JEFE).json()["puestos"]
    assert next(v for v in lista if v["id"] == p["id"])["activa"] is False
    cliente.patch(f"/api/jefe/puestos/{p['id']}", json={"activa": True}, headers=JEFE)
    assert p["id"] in {v["id"] for v in cliente.get("/api/vacantes").json()["vacantes"]}
    assert cliente.patch("/api/jefe/puestos/X99", json={"activa": False}, headers=JEFE).status_code == 404


@pytest.mark.parametrize("cambio", [
    {"titulo": "ab"},
    {"modalidad": "Marte"},
    {"descripcion": "corta"},
    {"requisitos": {}},
    {"requisitos": {"Z9": "clave"}},
    {"requisitos": {"A1": "imprescindible"}},
    {"habilidades_clave": ["x" * 41]},
    {"salario": 10000},
])
def test_puesto_invalido(jefe, cambio):
    r = cliente.post("/api/jefe/puestos", json=dict(PUESTO, **cambio), headers=JEFE)
    assert r.status_code == 422 and "detail" in r.json()


def test_restricciones_del_esquema():
    with pytest.raises(sqlite3.IntegrityError):
        with db.conectar() as con:
            con.execute("INSERT INTO resultados (fecha, vacante_id, afinidad, brechas, nivel) "
                        "VALUES ('2026-10-26', 'V01', 90, 1, 'excelente')")
    with pytest.raises(sqlite3.IntegrityError):
        with db.conectar() as con:
            con.execute("INSERT INTO resultados (fecha, vacante_id, afinidad, brechas, nivel) "
                        "VALUES ('2026-10-26', 'NO-EXISTE', 90, 1, 'reforzar')")

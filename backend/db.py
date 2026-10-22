"""Base de datos SQLite de Pulso: catálogo y registro anónimo para los reportes.

- Catálogo (aptitudes, preguntas, vacantes, requisitos): se sincroniza al arrancar desde
  datos/preguntas.json y datos/vacantes.json, que siguen siendo los archivos que editan los roles 2 y 3.
- Registro anónimo: por evaluación solo se guarda el día, el puntaje por aptitud y las 5 vacantes
  recomendadas; por explicación, la vacante, la fuente (ia/plantilla) y los segundos.
  Nunca se guarda el alias, las respuestas ni nada del módulo de apoyo.
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("PULSO_DB", BASE / "datos" / "pulso.db"))
MEXICO = timezone(timedelta(hours=-6), "America/Mexico_City")  # sin horario de verano desde 2022

ESQUEMA = """
CREATE TABLE IF NOT EXISTS aptitudes (
    id          TEXT PRIMARY KEY,
    nombre      TEXT NOT NULL,
    descripcion TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS preguntas (
    id         INTEGER PRIMARY KEY,
    aptitud_id TEXT NOT NULL REFERENCES aptitudes(id),
    tipo       TEXT NOT NULL CHECK (tipo IN ('opcion_multiple', 'escala')),
    texto      TEXT NOT NULL,
    opciones   TEXT,             -- JSON con las opciones (solo opción múltiple)
    correcta   INTEGER,          -- índice de la opción correcta (solo opción múltiple)
    invertida  INTEGER           -- 1 si la escala se invierte (solo escala)
);
CREATE TABLE IF NOT EXISTS vacantes (
    id                TEXT PRIMARY KEY,
    titulo            TEXT NOT NULL,
    empresa           TEXT NOT NULL,
    area              TEXT NOT NULL,
    modalidad         TEXT NOT NULL,
    descripcion       TEXT NOT NULL,
    habilidades_clave TEXT NOT NULL  -- JSON
);
CREATE TABLE IF NOT EXISTS requisitos (
    vacante_id TEXT NOT NULL REFERENCES vacantes(id),
    aptitud_id TEXT NOT NULL REFERENCES aptitudes(id),
    minimo     INTEGER NOT NULL CHECK (minimo BETWEEN 0 AND 100),
    peso       INTEGER NOT NULL CHECK (peso > 0),
    orden      INTEGER NOT NULL,
    PRIMARY KEY (vacante_id, aptitud_id)
);
CREATE TABLE IF NOT EXISTS evaluaciones (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL              -- solo el día (AAAA-MM-DD, hora de México)
);
CREATE TABLE IF NOT EXISTS evaluacion_aptitudes (
    evaluacion_id INTEGER NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
    aptitud_id    TEXT NOT NULL REFERENCES aptitudes(id),
    puntaje       INTEGER NOT NULL CHECK (puntaje BETWEEN 0 AND 100),
    PRIMARY KEY (evaluacion_id, aptitud_id)
);
CREATE TABLE IF NOT EXISTS evaluacion_recomendaciones (
    evaluacion_id INTEGER NOT NULL REFERENCES evaluaciones(id) ON DELETE CASCADE,
    posicion      INTEGER NOT NULL CHECK (posicion BETWEEN 1 AND 5),
    vacante_id    TEXT NOT NULL REFERENCES vacantes(id),
    afinidad      INTEGER NOT NULL,
    PRIMARY KEY (evaluacion_id, posicion)
);
CREATE TABLE IF NOT EXISTS explicaciones (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha      TEXT NOT NULL,
    vacante_id TEXT NOT NULL REFERENCES vacantes(id),
    fuente     TEXT NOT NULL CHECK (fuente IN ('ia', 'plantilla')),
    segundos   REAL NOT NULL,
    memoria    INTEGER NOT NULL DEFAULT 0
);
"""


@contextmanager
def conectar():
    """Conexión que confirma al salir sin error y siempre se cierra."""
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        with con:
            yield con
    finally:
        con.close()


def hoy():
    return datetime.now(MEXICO).date().isoformat()


def inicializar(preguntas_data, vacantes_data):
    """Crea las tablas y reemplaza el catálogo con el contenido de los JSON."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with conectar() as con:
        con.execute("PRAGMA journal_mode = WAL")
        con.executescript(ESQUEMA)
        for a in preguntas_data["aptitudes"]:
            con.execute("INSERT INTO aptitudes VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
                        "nombre = excluded.nombre, descripcion = excluded.descripcion",
                        (a["id"], a["nombre"], a["descripcion"]))
        con.execute("DELETE FROM preguntas")
        for p in preguntas_data["preguntas"]:
            om = p["tipo"] == "opcion_multiple"
            con.execute("INSERT INTO preguntas VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (p["id"], p["aptitud"], p["tipo"], p["texto"],
                         json.dumps(p["opciones"], ensure_ascii=False) if om else None,
                         p["correcta"] if om else None,
                         None if om else int(bool(p.get("invertida")))))
        con.execute("DELETE FROM requisitos")
        for v in vacantes_data["vacantes"]:
            con.execute("INSERT INTO vacantes VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
                        "titulo = excluded.titulo, empresa = excluded.empresa, area = excluded.area, "
                        "modalidad = excluded.modalidad, descripcion = excluded.descripcion, "
                        "habilidades_clave = excluded.habilidades_clave",
                        (v["id"], v["titulo"], v["empresa"], v["area"], v["modalidad"], v["descripcion"],
                         json.dumps(v["habilidades_clave"], ensure_ascii=False)))
            for orden, (apt, req) in enumerate(v["requisitos"].items()):
                con.execute("INSERT INTO requisitos VALUES (?, ?, ?, ?, ?)",
                            (v["id"], apt, req["minimo"], req["peso"], orden))


def cargar_preguntas():
    """El catálogo de la prueba con el mismo formato que preguntas.json."""
    with conectar() as con:
        aptitudes = [dict(r) for r in con.execute("SELECT id, nombre, descripcion FROM aptitudes ORDER BY id")]
        preguntas = []
        for r in con.execute("SELECT * FROM preguntas ORDER BY id"):
            p = {"id": r["id"], "aptitud": r["aptitud_id"], "tipo": r["tipo"], "texto": r["texto"]}
            if r["tipo"] == "opcion_multiple":
                p["opciones"] = json.loads(r["opciones"])
                p["correcta"] = r["correcta"]
            else:
                p["invertida"] = bool(r["invertida"])
            preguntas.append(p)
    return {"aptitudes": aptitudes, "preguntas": preguntas}


def cargar_vacantes():
    """Las vacantes con sus requisitos, con el mismo formato que vacantes.json."""
    with conectar() as con:
        vacantes = []
        for r in con.execute("SELECT * FROM vacantes ORDER BY id"):
            reqs = con.execute("SELECT aptitud_id, minimo, peso FROM requisitos WHERE vacante_id = ? ORDER BY orden",
                               (r["id"],))
            vacantes.append({"id": r["id"], "titulo": r["titulo"], "empresa": r["empresa"], "area": r["area"],
                             "modalidad": r["modalidad"], "descripcion": r["descripcion"],
                             "habilidades_clave": json.loads(r["habilidades_clave"]),
                             "requisitos": {q["aptitud_id"]: {"minimo": q["minimo"], "peso": q["peso"]} for q in reqs}})
    return vacantes


def registrar_evaluacion(perfil, recomendaciones):
    """Guarda una evaluación anónima: día, puntaje por aptitud y las 5 recomendaciones."""
    with conectar() as con:
        eid = con.execute("INSERT INTO evaluaciones (fecha) VALUES (?)", (hoy(),)).lastrowid
        con.executemany("INSERT INTO evaluacion_aptitudes VALUES (?, ?, ?)",
                        [(eid, a, v) for a, v in perfil.items()])
        con.executemany("INSERT INTO evaluacion_recomendaciones VALUES (?, ?, ?, ?)",
                        [(eid, i, r["vacante"]["id"], r["afinidad"]) for i, r in enumerate(recomendaciones, 1)])
    return eid


def registrar_explicacion(vacante_id, fuente, segundos, memoria=False):
    with conectar() as con:
        con.execute("INSERT INTO explicaciones (fecha, vacante_id, fuente, segundos, memoria) VALUES (?, ?, ?, ?, ?)",
                    (hoy(), vacante_id, fuente, round(segundos, 1), int(memoria)))


def _filtro(desde, hasta, campo="fecha"):
    sql, params = [], []
    if desde:
        sql.append(f"{campo} >= ?")
        params.append(desde)
    if hasta:
        sql.append(f"{campo} <= ?")
        params.append(hasta)
    return (" WHERE " + " AND ".join(sql)) if sql else "", params


def resumen(desde=None, hasta=None):
    """Datos agregados para la pantalla de reportes. Fechas en AAAA-MM-DD (incluidas)."""
    w, p = _filtro(desde, hasta, "e.fecha")
    we, pe = _filtro(desde, hasta)
    with conectar() as con:
        total = con.execute(f"SELECT COUNT(*) FROM evaluaciones e{w}", p).fetchone()[0]
        por_dia = [dict(r) for r in con.execute(
            f"SELECT e.fecha, COUNT(*) AS evaluaciones FROM evaluaciones e{w} GROUP BY e.fecha ORDER BY e.fecha", p)]
        aptitudes = [dict(r) for r in con.execute(
            f"""SELECT a.id, a.nombre, ROUND(AVG(ea.puntaje), 1) AS promedio, COUNT(ea.puntaje) AS n
                FROM aptitudes a
                LEFT JOIN evaluacion_aptitudes ea ON ea.aptitud_id = a.id
                     AND ea.evaluacion_id IN (SELECT e.id FROM evaluaciones e{w})
                GROUP BY a.id ORDER BY a.id""", p)]
        vacantes = [dict(r) for r in con.execute(
            f"""SELECT v.id, v.titulo, v.area,
                       COUNT(er.vacante_id) AS veces_top5,
                       SUM(CASE WHEN er.posicion = 1 THEN 1 ELSE 0 END) AS veces_primera,
                       ROUND(AVG(er.afinidad), 1) AS afinidad_promedio
                FROM vacantes v
                LEFT JOIN evaluacion_recomendaciones er ON er.vacante_id = v.id
                     AND er.evaluacion_id IN (SELECT e.id FROM evaluaciones e{w})
                GROUP BY v.id ORDER BY veces_top5 DESC, veces_primera DESC, v.id""", p)]
        ia = dict(con.execute(
            f"""SELECT COUNT(*) AS total,
                       SUM(CASE WHEN fuente = 'ia' THEN 1 ELSE 0 END) AS con_ia,
                       SUM(CASE WHEN fuente = 'plantilla' THEN 1 ELSE 0 END) AS con_plantilla,
                       ROUND(AVG(CASE WHEN fuente = 'ia' AND memoria = 0 THEN segundos END), 1) AS segundos_ia
                FROM explicaciones{we}""", pe).fetchone())
    for clave in ("con_ia", "con_plantilla"):
        ia[clave] = ia[clave] or 0
    return {"desde": desde, "hasta": hasta, "evaluaciones": total, "por_dia": por_dia,
            "aptitudes": aptitudes, "vacantes": vacantes, "explicaciones": ia}


def evaluaciones_csv(desde=None, hasta=None):
    """Una fila por evaluación anónima: id, fecha, puntaje por aptitud y la vacante con mayor afinidad."""
    w, p = _filtro(desde, hasta, "e.fecha")
    with conectar() as con:
        aptitudes = [r[0] for r in con.execute("SELECT id FROM aptitudes ORDER BY id")]
        filas = ["evaluacion,fecha," + ",".join(aptitudes) + ",vacante_1,afinidad_1"]
        for e in con.execute(f"SELECT e.id, e.fecha FROM evaluaciones e{w} ORDER BY e.id", p):
            puntajes = dict(con.execute("SELECT aptitud_id, puntaje FROM evaluacion_aptitudes WHERE evaluacion_id = ?",
                                        (e["id"],)).fetchall())
            top = con.execute("SELECT vacante_id, afinidad FROM evaluacion_recomendaciones "
                              "WHERE evaluacion_id = ? AND posicion = 1", (e["id"],)).fetchone()
            filas.append(",".join([str(e["id"]), e["fecha"]] + [str(puntajes.get(a, "")) for a in aptitudes]
                                  + [top["vacante_id"] if top else "", str(top["afinidad"]) if top else ""]))
    return "\n".join(filas) + "\n"

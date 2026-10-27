"""Base de datos SQLite de Pulso: catálogo, puestos del jefe y resultados para la estadística.

- Catálogo (aptitudes, preguntas, vacantes de ejemplo y sus requisitos): se sincroniza al arrancar desde
  datos/preguntas.json y datos/vacantes.json, que siguen siendo los archivos que editan los roles 2 y 3.
- Puestos del jefe: se crean desde el panel (origen = 'jefe') y se conservan entre reinicios.
- Resultados: por evaluación solo se guarda el día, el puesto que mejor le queda a la persona, su afinidad,
  cuántas brechas tiene y su nivel (preparado / reforzar / no_apto).
  Nunca se guarda el alias, las respuestas, los puntajes por aptitud ni nada del módulo de apoyo.
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
VERSION_ESQUEMA = 2

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
    habilidades_clave TEXT NOT NULL,                 -- JSON
    origen            TEXT NOT NULL DEFAULT 'catalogo' CHECK (origen IN ('catalogo', 'jefe')),
    activa            INTEGER NOT NULL DEFAULT 1 CHECK (activa IN (0, 1)),
    creada            TEXT                          -- día en que el jefe la agregó
);
CREATE TABLE IF NOT EXISTS requisitos (
    vacante_id TEXT NOT NULL REFERENCES vacantes(id),
    aptitud_id TEXT NOT NULL REFERENCES aptitudes(id),
    minimo     INTEGER NOT NULL CHECK (minimo BETWEEN 0 AND 100),
    peso       INTEGER NOT NULL CHECK (peso > 0),
    orden      INTEGER NOT NULL,
    PRIMARY KEY (vacante_id, aptitud_id)
);
CREATE TABLE IF NOT EXISTS resultados (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha      TEXT NOT NULL,                        -- solo el día (AAAA-MM-DD, hora de México)
    vacante_id TEXT NOT NULL REFERENCES vacantes(id),-- el puesto que mejor le queda
    afinidad   INTEGER NOT NULL CHECK (afinidad BETWEEN 0 AND 100),
    brechas    INTEGER NOT NULL CHECK (brechas >= 0),
    nivel      TEXT NOT NULL CHECK (nivel IN ('preparado', 'reforzar', 'no_apto'))
);
"""

# Importancia de una aptitud para un puesto del jefe -> (peso, mínimo). Misma regla que el catálogo de ejemplo.
IMPORTANCIA = {"clave": (3, 60), "importante": (2, 50), "deseable": (1, 40)}


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


def _migrar(con):
    """Versión 1 -> 2: el registro detallado se reemplaza por la tabla `resultados`; las vacantes ganan origen y estado."""
    version = con.execute("PRAGMA user_version").fetchone()[0]
    if version >= VERSION_ESQUEMA:
        return
    for tabla in ("evaluacion_aptitudes", "evaluacion_recomendaciones", "explicaciones", "evaluaciones"):
        con.execute(f"DROP TABLE IF EXISTS {tabla}")
    columnas = {r[1] for r in con.execute("PRAGMA table_info(vacantes)")}
    if columnas and "origen" not in columnas:
        con.execute("ALTER TABLE vacantes ADD COLUMN origen TEXT NOT NULL DEFAULT 'catalogo' "
                    "CHECK (origen IN ('catalogo', 'jefe'))")
        con.execute("ALTER TABLE vacantes ADD COLUMN activa INTEGER NOT NULL DEFAULT 1 CHECK (activa IN (0, 1))")
        con.execute("ALTER TABLE vacantes ADD COLUMN creada TEXT")
    con.execute(f"PRAGMA user_version = {VERSION_ESQUEMA}")


def inicializar(preguntas_data, vacantes_data):
    """Crea o migra las tablas y reemplaza el catálogo de ejemplo con el contenido de los JSON.
    Los puestos que agregó el jefe no se tocan."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with conectar() as con:
        con.execute("PRAGMA journal_mode = WAL")
        _migrar(con)
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
        con.execute("DELETE FROM requisitos WHERE vacante_id IN (SELECT id FROM vacantes WHERE origen = 'catalogo')")
        for v in vacantes_data["vacantes"]:
            con.execute("INSERT INTO vacantes (id, titulo, empresa, area, modalidad, descripcion, habilidades_clave) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET "
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


def _vacante(con, r, detalle=False):
    reqs = con.execute("SELECT aptitud_id, minimo, peso FROM requisitos WHERE vacante_id = ? ORDER BY orden", (r["id"],))
    v = {"id": r["id"], "titulo": r["titulo"], "empresa": r["empresa"], "area": r["area"],
         "modalidad": r["modalidad"], "descripcion": r["descripcion"],
         "habilidades_clave": json.loads(r["habilidades_clave"]),
         "requisitos": {q["aptitud_id"]: {"minimo": q["minimo"], "peso": q["peso"]} for q in reqs}}
    if detalle:
        v.update(origen=r["origen"], activa=bool(r["activa"]), creada=r["creada"])
    return v


def cargar_vacantes(incluir_inactivas=False, detalle=False):
    """Las vacantes con sus requisitos, con el mismo formato que vacantes.json (por omisión, solo las activas)."""
    filtro = "" if incluir_inactivas else " WHERE activa = 1"
    with conectar() as con:
        return [_vacante(con, r, detalle) for r in con.execute(f"SELECT * FROM vacantes{filtro} ORDER BY id")]


def crear_puesto(datos):
    """Agrega un puesto del jefe. `datos["requisitos"]` = {aptitud: 'clave' | 'importante' | 'deseable'}."""
    with conectar() as con:
        # P01, P02...: numeración propia para no chocar con las vacantes V## del catálogo de ejemplo.
        numeros = [int(r[0][1:]) for r in con.execute("SELECT id FROM vacantes WHERE id GLOB 'P[0-9]*'")]
        vid = f"P{max(numeros, default=0) + 1:02d}"
        con.execute("INSERT INTO vacantes (id, titulo, empresa, area, modalidad, descripcion, habilidades_clave, "
                    "origen, activa, creada) VALUES (?, ?, ?, ?, ?, ?, ?, 'jefe', 1, ?)",
                    (vid, datos["titulo"], datos["empresa"], datos["area"], datos["modalidad"], datos["descripcion"],
                     json.dumps(datos["habilidades_clave"], ensure_ascii=False), hoy()))
        orden_importancia = sorted(datos["requisitos"].items(), key=lambda kv: (-IMPORTANCIA[kv[1]][0], kv[0]))
        for orden, (apt, importancia) in enumerate(orden_importancia):
            peso, minimo = IMPORTANCIA[importancia]
            con.execute("INSERT INTO requisitos VALUES (?, ?, ?, ?, ?)", (vid, apt, minimo, peso, orden))
        return _vacante(con, con.execute("SELECT * FROM vacantes WHERE id = ?", (vid,)).fetchone(), detalle=True)


def cambiar_estado(vacante_id, activa):
    """Activa o desactiva un puesto. Devuelve False si no existe."""
    with conectar() as con:
        return con.execute("UPDATE vacantes SET activa = ? WHERE id = ?", (int(activa), vacante_id)).rowcount == 1


def registrar_resultado(vacante_id, afinidad, brechas, nivel):
    """Guarda solo el resultado de una evaluación: día, mejor puesto, afinidad, número de brechas y nivel."""
    with conectar() as con:
        return con.execute("INSERT INTO resultados (fecha, vacante_id, afinidad, brechas, nivel) VALUES (?, ?, ?, ?, ?)",
                           (hoy(), vacante_id, afinidad, brechas, nivel)).lastrowid


def _filtro(desde, hasta, campo="r.fecha"):
    sql, params = [], []
    if desde:
        sql.append(f"{campo} >= ?")
        params.append(desde)
    if hasta:
        sql.append(f"{campo} <= ?")
        params.append(hasta)
    return (" WHERE " + " AND ".join(sql)) if sql else "", params


_CUENTA_NIVELES = """SUM(CASE WHEN r.nivel = 'preparado' THEN 1 ELSE 0 END) AS preparado,
                     SUM(CASE WHEN r.nivel = 'reforzar'  THEN 1 ELSE 0 END) AS reforzar,
                     SUM(CASE WHEN r.nivel = 'no_apto'   THEN 1 ELSE 0 END) AS no_apto"""


def estadisticas(desde=None, hasta=None):
    """Cuántas personas están preparadas, a cuántas les faltan habilidades y cuántas no son aptas todavía.
    Fechas en AAAA-MM-DD (incluidas)."""
    w, p = _filtro(desde, hasta)
    with conectar() as con:
        total = con.execute(f"SELECT COUNT(*) FROM resultados r{w}", p).fetchone()[0]
        niveles = dict(con.execute(f"SELECT {_CUENTA_NIVELES} FROM resultados r{w}", p).fetchone())
        niveles = {k: niveles[k] or 0 for k in ("preparado", "reforzar", "no_apto")}
        por_puesto = [dict(r) for r in con.execute(
            f"""SELECT v.id, v.titulo, v.area, v.origen, COUNT(*) AS personas,
                       ROUND(AVG(r.afinidad), 1) AS afinidad_promedio, {_CUENTA_NIVELES}
                FROM resultados r JOIN vacantes v ON v.id = r.vacante_id{w}
                GROUP BY v.id ORDER BY personas DESC, v.id""", p)]
        por_dia = [dict(r) for r in con.execute(
            f"SELECT r.fecha, COUNT(*) AS evaluaciones, {_CUENTA_NIVELES} FROM resultados r{w} "
            "GROUP BY r.fecha ORDER BY r.fecha", p)]
    return {"desde": desde, "hasta": hasta, "evaluaciones": total, "niveles": niveles,
            "por_puesto": por_puesto, "por_dia": por_dia}


def resultados_csv(desde=None, hasta=None):
    """Una fila por evaluación: fecha, mejor puesto, afinidad, brechas y nivel. Sin datos de la persona."""
    w, p = _filtro(desde, hasta)
    filas = ["resultado,fecha,vacante,titulo,afinidad,brechas,nivel"]
    with conectar() as con:
        for r in con.execute(f"SELECT r.*, v.titulo FROM resultados r JOIN vacantes v ON v.id = r.vacante_id{w} "
                             "ORDER BY r.id", p):
            titulo = '"' + r["titulo"].replace('"', '""') + '"'
            filas.append(f"{r['id']},{r['fecha']},{r['vacante_id']},{titulo},{r['afinidad']},{r['brechas']},{r['nivel']}")
    return "\n".join(filas) + "\n"

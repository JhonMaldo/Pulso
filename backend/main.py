"""API de Pulso (sección 6.6 del plan) + módulo de apoyo + panel del jefe + pantallas ya compiladas.

Correr en la VM:  uvicorn main:app --host 0.0.0.0 --port 8000   (desde backend/)
"""
import json
import logging
import os
import re
import secrets
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator

import apoyo
import db
import ia
from motor import NIVELES, UMBRAL_REFORZAR, calcular_perfil, clasificar, recomendar, validar_respuestas

BASE = Path(__file__).resolve().parent
DIST = Path(os.getenv("PULSO_DIST", BASE.parent / "dist"))

# Contraseña del panel del jefe (estadísticas y alta de puestos). Vacía = panel cerrado.
JEFE_CLAVE = os.getenv("JEFE_CLAVE", "")
MAX_PUESTOS = 60
log = logging.getLogger("pulso")

# Los JSON son la fuente que editan los roles 2 y 3; al arrancar se copian a SQLite y la API lee de ahí.
_preguntas_json = json.loads((BASE / "datos" / "preguntas.json").read_text(encoding="utf-8"))
db.inicializar(_preguntas_json, json.loads((BASE / "datos" / "vacantes.json").read_text(encoding="utf-8")))
PREGUNTAS = dict(db.cargar_preguntas(), escala=_preguntas_json["escala"])
APTITUDES = {a["id"] for a in PREGUNTAS["aptitudes"]}
APOYO = apoyo.cargar()
VACANTES, POR_ID = [], {}


def recargar_vacantes():
    """Las vacantes activas que se recomiendan. Se llama al arrancar y cada vez que el jefe cambia un puesto."""
    global VACANTES, POR_ID
    VACANTES = db.cargar_vacantes()
    POR_ID = {v["id"]: v for v in VACANTES}


recargar_vacantes()

app = FastAPI(title="Pulso: aptitudes y vacantes", docs_url="/api/docs", openapi_url="/api/openapi.json")


class Evaluacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    respuestas: dict[str, StrictInt]  # las llaves de un JSON siempre son texto


class PedidoExplicacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vacante_id: Annotated[str, Field(min_length=1, max_length=10)]
    perfil: dict[str, StrictInt]


class PedidoApoyo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    texto: Annotated[str, Field(min_length=1, max_length=apoyo.MAX_TEXTO)]


Texto = lambda minimo, maximo: Annotated[str, Field(min_length=minimo, max_length=maximo)]


class NuevoPuesto(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    titulo: Texto(3, 80)
    empresa: Texto(2, 80)
    area: Texto(2, 60)
    modalidad: Literal["Presencial", "Híbrido", "Remoto"]
    descripcion: Texto(10, 400)
    habilidades_clave: Annotated[list[Texto(1, 40)], Field(max_length=8)] = []
    requisitos: dict[str, Literal["clave", "importante", "deseable"]]

    @field_validator("requisitos")
    @classmethod
    def requisitos_validos(cls, v):
        if not v:
            raise ValueError("elige al menos una aptitud que pida el puesto")
        desconocidas = sorted(set(v) - APTITUDES)
        if desconocidas:
            raise ValueError(f"aptitudes desconocidas: {desconocidas}")
        return v


class CambioEstado(BaseModel):
    model_config = ConfigDict(extra="forbid")
    activa: StrictBool


@app.exception_handler(RequestValidationError)
def error_de_validacion(_: Request, exc: RequestValidationError):
    # Mensajes claros y sin repetir lo que envió la persona (el texto de apoyo no se devuelve ni se registra).
    detalles = [f"{'.'.join(str(p) for p in e['loc'][1:]) or 'cuerpo'}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": "Datos inválidos", "errores": detalles})


def _con_nombres(items):
    nombres = {a["id"]: a["nombre"] for a in PREGUNTAS["aptitudes"]}
    return [dict(i, nombre=nombres.get(i["aptitud"], i["aptitud"])) for i in items]


def _validar_perfil(perfil):
    desconocidas = sorted(set(perfil) - APTITUDES)
    if desconocidas:
        raise HTTPException(422, f"Aptitudes desconocidas: {desconocidas}")
    fuera = sorted(a for a, v in perfil.items() if not 0 <= v <= 100)
    if fuera:
        raise HTTPException(422, f"El perfil debe ir de 0 a 100 en: {fuera}")


@app.get("/api/salud")
def salud():
    return {"ok": True}


@app.get("/api/salud/ollama")
def salud_ollama():
    return ia.estado_ollama()


@app.get("/api/prueba")
def prueba():
    preguntas = [{k: v for k, v in p.items() if k != "correcta"} for p in PREGUNTAS["preguntas"]]
    return {"aptitudes": PREGUNTAS["aptitudes"], "escala": PREGUNTAS["escala"], "preguntas": preguntas}


@app.post("/api/evaluar")
def evaluar(e: Evaluacion):
    try:
        respuestas = {int(k): v for k, v in e.respuestas.items()}
    except ValueError:
        raise HTTPException(422, "Las llaves de 'respuestas' deben ser los números de pregunta")
    try:
        validar_respuestas(PREGUNTAS["preguntas"], respuestas)
    except ValueError as err:
        raise HTTPException(422, str(err))
    perfil = calcular_perfil(PREGUNTAS["preguntas"], respuestas)
    recomendaciones = [dict(r, fortalezas=_con_nombres(r["fortalezas"]), brechas=_con_nombres(r["brechas"]),
                            nivel=clasificar(r["afinidad"], r["brechas"]))
                       for r in recomendar(perfil, VACANTES, n=5)]
    mejor = recomendaciones[0]
    try:
        # Solo el resultado: sin alias, respuestas ni puntajes por aptitud.
        db.registrar_resultado(mejor["vacante"]["id"], mejor["afinidad"], len(mejor["brechas"]), mejor["nivel"])
    except Exception:
        log.warning("No se pudo registrar el resultado en la base de datos")
    return {"perfil": perfil, "recomendaciones": recomendaciones, "nivel": mejor["nivel"]}


@app.post("/api/explicar")
def explicar_vacante(p: PedidoExplicacion):
    vacante = POR_ID.get(p.vacante_id.strip().upper())
    if vacante is None:
        raise HTTPException(404, "Vacante no encontrada")
    _validar_perfil(p.perfil)
    return ia.explicar(vacante, p.perfil)


@app.get("/api/vacantes")
def vacantes():
    return {"vacantes": VACANTES}


@app.post("/api/apoyo")
def apoyo_busqueda(p: PedidoApoyo):
    # No se guarda ni se registra el texto; no toca el perfil ni las recomendaciones.
    if not p.texto.strip():
        raise HTTPException(422, "Escribe cómo te sientes con tu búsqueda")
    return APOYO.buscar(p.texto)


# ---------- Panel del jefe ----------

def _autorizar(clave):
    if not JEFE_CLAVE:
        raise HTTPException(503, "El panel del jefe está cerrado: falta definir JEFE_CLAVE en backend/.env")
    if not secrets.compare_digest(clave or "", JEFE_CLAVE):
        raise HTTPException(401, "Contraseña del jefe incorrecta")


ClaveJefe = Annotated[str | None, Header(alias="X-Clave-Jefe")]
_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _fechas(desde, hasta):
    for f in (desde, hasta):
        if f and not _FECHA.match(f):
            raise HTTPException(422, "Las fechas van en formato AAAA-MM-DD")
    if desde and hasta and desde > hasta:
        raise HTTPException(422, "'desde' no puede ser posterior a 'hasta'")


@app.get("/api/jefe/acceso")
def jefe_acceso(x_clave_jefe: ClaveJefe = None):
    """Comprueba la contraseña y devuelve las reglas del panel."""
    _autorizar(x_clave_jefe)
    return {"ok": True, "niveles": NIVELES, "umbral_reforzar": UMBRAL_REFORZAR,
            "aptitudes": PREGUNTAS["aptitudes"], "importancia": {k: {"peso": p, "minimo": m}
                                                                 for k, (p, m) in db.IMPORTANCIA.items()}}


@app.get("/api/jefe/estadisticas")
def jefe_estadisticas(desde: str | None = None, hasta: str | None = None, x_clave_jefe: ClaveJefe = None):
    _autorizar(x_clave_jefe)
    _fechas(desde, hasta)
    return db.estadisticas(desde, hasta)


@app.get("/api/jefe/resultados.csv")
def jefe_csv(desde: str | None = None, hasta: str | None = None, x_clave_jefe: ClaveJefe = None):
    _autorizar(x_clave_jefe)
    _fechas(desde, hasta)
    return Response(db.resultados_csv(desde, hasta), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="pulso_resultados.csv"'})


@app.get("/api/jefe/puestos")
def jefe_puestos(x_clave_jefe: ClaveJefe = None):
    _autorizar(x_clave_jefe)
    return {"puestos": db.cargar_vacantes(incluir_inactivas=True, detalle=True)}


@app.post("/api/jefe/puestos", status_code=201)
def jefe_crear_puesto(p: NuevoPuesto, x_clave_jefe: ClaveJefe = None):
    _autorizar(x_clave_jefe)
    if len(db.cargar_vacantes(incluir_inactivas=True)) >= MAX_PUESTOS:
        raise HTTPException(409, f"Se alcanzó el máximo de {MAX_PUESTOS} puestos; desactiva o revisa los existentes")
    puesto = db.crear_puesto(p.model_dump())
    recargar_vacantes()
    return puesto


@app.patch("/api/jefe/puestos/{vacante_id}")
def jefe_cambiar_estado(vacante_id: str, c: CambioEstado, x_clave_jefe: ClaveJefe = None):
    _autorizar(x_clave_jefe)
    vid = vacante_id.strip().upper()
    if c.activa is False and vid in POR_ID and len(VACANTES) <= 5:
        raise HTTPException(409, "Debe haber al menos 5 puestos activos para poder recomendar")
    if not db.cambiar_estado(vid, c.activa):
        raise HTTPException(404, "Puesto no encontrado")
    recargar_vacantes()
    return {"id": vid, "activa": c.activa}


@app.get("/api/{resto:path}", include_in_schema=False)
def ruta_desconocida(resto: str):
    raise HTTPException(404, "Ruta de la API no encontrada")


# Pantallas (build de Vite). Se monta al final para no tapar /api.
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="pantallas")

"""API de Pulso (sección 6.6 del plan) + módulo de apoyo + pantallas ya compiladas.

Correr en la VM:  uvicorn main:app --host 0.0.0.0 --port 8000   (desde backend/)
"""
import json
import logging
import os
import re
import secrets
import time
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictInt

import apoyo
import db
import ia
from motor import calcular_perfil, recomendar, validar_respuestas

BASE = Path(__file__).resolve().parent
DIST = Path(os.getenv("PULSO_DIST", BASE.parent / "dist"))

REPORTES_CLAVE = os.getenv("REPORTES_CLAVE", "")  # vacía = reportes sin clave (solo datos anónimos y agregados)
log = logging.getLogger("pulso")

# Los JSON son la fuente que editan los roles 2 y 3; al arrancar se copian a SQLite y la API lee de ahí.
_preguntas_json = json.loads((BASE / "datos" / "preguntas.json").read_text(encoding="utf-8"))
db.inicializar(_preguntas_json, json.loads((BASE / "datos" / "vacantes.json").read_text(encoding="utf-8")))
PREGUNTAS = dict(db.cargar_preguntas(), escala=_preguntas_json["escala"])
VACANTES = db.cargar_vacantes()
POR_ID = {v["id"]: v for v in VACANTES}
APTITUDES = {a["id"] for a in PREGUNTAS["aptitudes"]}
APOYO = apoyo.cargar()

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
    recomendaciones = [dict(r, fortalezas=_con_nombres(r["fortalezas"]), brechas=_con_nombres(r["brechas"]))
                       for r in recomendar(perfil, VACANTES, n=5)]
    try:
        db.registrar_evaluacion(perfil, recomendaciones)  # anónimo: sin alias ni respuestas
    except Exception:
        log.warning("No se pudo registrar la evaluación en la base de datos")
    return {"perfil": perfil, "recomendaciones": recomendaciones}


@app.post("/api/explicar")
def explicar_vacante(p: PedidoExplicacion):
    vacante = POR_ID.get(p.vacante_id.strip().upper())
    if vacante is None:
        raise HTTPException(404, "Vacante no encontrada")
    _validar_perfil(p.perfil)
    inicio = time.monotonic()
    resultado = ia.explicar(vacante, p.perfil)
    try:
        db.registrar_explicacion(vacante["id"], resultado["fuente"], time.monotonic() - inicio,
                                 resultado.get("memoria", False))
    except Exception:
        log.warning("No se pudo registrar la explicación en la base de datos")
    return resultado


@app.get("/api/vacantes")
def vacantes():
    return {"vacantes": VACANTES}


@app.post("/api/apoyo")
def apoyo_busqueda(p: PedidoApoyo):
    # No se guarda ni se registra el texto; no toca el perfil ni las recomendaciones.
    if not p.texto.strip():
        raise HTTPException(422, "Escribe cómo te sientes con tu búsqueda")
    return APOYO.buscar(p.texto)


def _autorizar(clave):
    if REPORTES_CLAVE and not secrets.compare_digest(clave or "", REPORTES_CLAVE):
        raise HTTPException(401, "Clave de reportes incorrecta")


_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _fechas(desde, hasta):
    for f in (desde, hasta):
        if f and not _FECHA.match(f):
            raise HTTPException(422, "Las fechas van en formato AAAA-MM-DD")
    if desde and hasta and desde > hasta:
        raise HTTPException(422, "'desde' no puede ser posterior a 'hasta'")


@app.get("/api/reportes/acceso")
def reportes_acceso():
    return {"requiere_clave": bool(REPORTES_CLAVE)}


@app.get("/api/reportes/resumen")
def reportes_resumen(desde: str | None = None, hasta: str | None = None,
                     x_clave_reportes: Annotated[str | None, Header()] = None):
    _autorizar(x_clave_reportes)
    _fechas(desde, hasta)
    return db.resumen(desde, hasta)


@app.get("/api/reportes/evaluaciones.csv")
def reportes_csv(desde: str | None = None, hasta: str | None = None,
                 x_clave_reportes: Annotated[str | None, Header()] = None):
    _autorizar(x_clave_reportes)
    _fechas(desde, hasta)
    return Response(db.evaluaciones_csv(desde, hasta), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="pulso_evaluaciones.csv"'})


@app.get("/api/{resto:path}", include_in_schema=False)
def ruta_desconocida(resto: str):
    raise HTTPException(404, "Ruta de la API no encontrada")


# Pantallas (build de Vite). Se monta al final para no tapar /api.
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="pantallas")

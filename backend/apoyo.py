"""Módulo "Apoyo en la búsqueda de empleo" sobre el dataset KB_limpio.json.

Compara el texto de la persona con las frases del dataset (en inglés), con sus
traducciones al español (src/data/KB_es.json) y con unas frases semilla del equipo,
usando TF-IDF y similitud coseno. Devuelve la respuesta del dataset más parecida.

Reglas: no guarda ni registra el texto, nunca afecta el perfil ni las recomendaciones
y, ante señales de crisis, siempre muestra la Línea de la Vida y el 911.
"""
import json
import math
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
KB_PATH = Path(os.getenv("KB_PATH", RAIZ / "KB_limpio.json"))
KB_ES_PATH = Path(os.getenv("KB_ES_PATH", RAIZ / "src" / "data" / "KB_es.json"))
SEMILLAS_PATH = Path(__file__).resolve().parent / "datos" / "apoyo_semillas.json"

TAGS = {"problem", "stressed", "anxious", "scared", "sad", "worthless", "depressed", "sleep",
        "no-approach", "learn-more", "meditation", "user-advice", "help", "suicide"}
UMBRAL = 0.30
MAX_TEXTO = 500
PALABRAS_CRISIS = ["quitarme la vida", "suicid", "no quiero vivir", "matarme", "kill myself"]
CONTACTO_CRISIS = "Línea de la Vida: 800 911 2000 (gratis, 24 horas). Emergencias: 911."
GENERAL = ("No encontré en el dataset una respuesta que se parezca a lo que escribiste. "
           "Buscar empleo puede ser pesado; hablar con alguien de confianza suele ayudar. "
           "Si lo necesitas, busca a un profesional de salud mental.")
AVISO = "Este módulo no es atención profesional ni influye en tus resultados. Lo que escribes no se guarda."

STOP = set("""a al algo de del el en es esta este esto estoy la las lo los me mi mis muy para por que se si
sin su sus te tu un una y yo o con como cual cuales quien quienes donde cuando creo crees pero ya hay ser son fue mas mucho mucha tan
i im am is are a an the to of and or in on my me it its at be been for with that this you your
was have has had do does did so as but not very because about feel feeling""".split())


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9ñ\s]", " ", texto)).strip()


def _tokens(texto):
    return [t for t in normalizar(texto).split() if len(t) > 1 and t not in STOP]


def es_permitido(tag):
    return tag in TAGS or tag.startswith("fact-")


class Apoyo:
    def __init__(self, kb, kb_es, semillas):
        es = {i["tag"]: i for i in kb_es["intents"]}
        self.respuestas = {}
        frases = []  # (tag, texto)
        for intent in kb["intents"]:
            tag = intent["tag"]
            if not es_permitido(tag):
                continue
            local = es.get(tag, {})
            frases += [(tag, p) for p in intent["patterns"]]
            frases += [(tag, p["text"]) for p in local.get("patterns", [])
                       if isinstance(intent["patterns"][p["sourceIndex"]], str)]
            traducidas = [r for r in local.get("responses", [])
                          if isinstance(intent["responses"][r["sourceIndex"]], str)]
            if traducidas:
                # Hasta 3 respuestas traducidas del mismo tag, en el orden del dataset.
                self.respuestas[tag] = {
                    "texto": " ".join(r["text"] for r in traducidas[:3]),
                    "original": " ".join(intent["responses"][r["sourceIndex"]] for r in traducidas[:3])}
        for tag, lista in semillas["frases"].items():
            if es_permitido(tag) and tag in self.respuestas:
                frases += [(tag, f) for f in lista]

        docs = [Counter(_tokens(texto)) for _, texto in frases]
        df = Counter(t for d in docs for t in d)
        n = len(docs)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.indice = []
        for (tag, _), d in zip(frases, docs):
            vec = self._vector(d)
            if vec:
                self.indice.append((tag, vec))

    def _vector(self, conteo):
        vec = {t: c * self.idf[t] for t, c in conteo.items() if t in self.idf}
        norma = math.sqrt(sum(v * v for v in vec.values()))
        return {t: v / norma for t, v in vec.items()} if norma else {}

    def buscar(self, texto):
        """Devuelve {"tag", "respuesta", "similitud", "crisis", "aviso", ...}. No guarda nada."""
        consulta = self._vector(Counter(_tokens(texto)))
        tag, mejor = None, 0.0
        for t, vec in self.indice:
            sim = sum(v * vec.get(k, 0.0) for k, v in consulta.items())
            if sim > mejor:
                tag, mejor = t, sim
        mejor = round(mejor, 3)
        crisis = tag == "suicide" and mejor >= UMBRAL or any(p in normalizar(texto) for p in PALABRAS_CRISIS)
        if crisis:
            r = self.respuestas.get("suicide", {"texto": CONTACTO_CRISIS, "original": ""})
            return {"tag": "suicide", "respuesta": r["texto"], "original": r["original"], "similitud": mejor,
                    "crisis": True, "contacto": CONTACTO_CRISIS, "aviso": AVISO}
        if tag is None or mejor < UMBRAL or tag not in self.respuestas:
            return {"tag": None, "respuesta": GENERAL, "original": "", "similitud": mejor,
                    "crisis": False, "aviso": AVISO}
        r = self.respuestas[tag]
        return {"tag": tag, "respuesta": r["texto"], "original": r["original"], "similitud": mejor,
                "crisis": False, "aviso": AVISO}


def cargar():
    leer = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
    return Apoyo(leer(KB_PATH), leer(KB_ES_PATH), leer(SEMILLAS_PATH))

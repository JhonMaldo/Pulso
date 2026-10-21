"""Revisa preguntas.json y vacantes.json antes de subirlos.

Uso: python backend/validar_datos.py   (sale con código 1 si hay errores)
"""
import json
import sys
from pathlib import Path

DATOS = Path(__file__).resolve().parent / "datos"


def validar(preguntas_data, vacantes_data):
    """Devuelve una lista de errores (vacía si todo está bien)."""
    errores = []
    aptitudes = {a["id"] for a in preguntas_data.get("aptitudes", [])}
    if len(aptitudes) != 8:
        errores.append(f"Se esperaban 8 aptitudes y hay {len(aptitudes)}")

    ids = set()
    por_aptitud = {a: 0 for a in aptitudes}
    for p in preguntas_data.get("preguntas", []):
        pid = p.get("id")
        if pid in ids:
            errores.append(f"Pregunta {pid}: id repetido")
        ids.add(pid)
        if p.get("aptitud") not in aptitudes:
            errores.append(f"Pregunta {pid}: aptitud desconocida {p.get('aptitud')}")
            continue
        por_aptitud[p["aptitud"]] += 1
        if not str(p.get("texto", "")).strip():
            errores.append(f"Pregunta {pid}: sin texto")
        if p.get("tipo") == "opcion_multiple":
            opciones = p.get("opciones", [])
            if len(opciones) != 4:
                errores.append(f"Pregunta {pid}: debe tener 4 opciones y tiene {len(opciones)}")
            correcta = p.get("correcta")
            if not isinstance(correcta, int) or not 0 <= correcta < len(opciones):
                errores.append(f"Pregunta {pid}: 'correcta' fuera de rango ({correcta})")
        elif p.get("tipo") == "escala":
            if not isinstance(p.get("invertida"), bool):
                errores.append(f"Pregunta {pid}: 'invertida' debe ser true o false")
        else:
            errores.append(f"Pregunta {pid}: tipo desconocido {p.get('tipo')}")
    for a, n in sorted(por_aptitud.items()):
        if n < 2:
            errores.append(f"Aptitud {a}: tiene {n} preguntas (mínimo 2)")

    vids = set()
    for v in vacantes_data.get("vacantes", []):
        vid = v.get("id")
        if vid in vids:
            errores.append(f"Vacante {vid}: id repetido")
        vids.add(vid)
        for campo in ("titulo", "area", "descripcion"):
            if not str(v.get(campo, "")).strip():
                errores.append(f"Vacante {vid}: falta '{campo}'")
        reqs = v.get("requisitos", {})
        if not reqs:
            errores.append(f"Vacante {vid}: sin requisitos")
        for a, r in reqs.items():
            if a not in aptitudes:
                errores.append(f"Vacante {vid}: aptitud desconocida {a}")
            if not isinstance(r.get("peso"), (int, float)) or r["peso"] <= 0:
                errores.append(f"Vacante {vid}, {a}: peso en cero o inválido")
            if not isinstance(r.get("minimo"), (int, float)) or not 0 < r["minimo"] <= 100:
                errores.append(f"Vacante {vid}, {a}: mínimo fuera de 1 a 100")
    if len(vids) < 20:
        errores.append(f"Se esperaban al menos 20 vacantes y hay {len(vids)}")
    return errores


def main():
    try:
        preguntas = json.loads((DATOS / "preguntas.json").read_text(encoding="utf-8"))
        vacantes = json.loads((DATOS / "vacantes.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: no se pudo abrir un JSON: {e}")
        return 1
    errores = validar(preguntas, vacantes)
    for e in errores:
        print("ERROR:", e)
    if errores:
        return 1
    print(f"OK: {len(preguntas['aptitudes'])} aptitudes, {len(preguntas['preguntas'])} preguntas, "
          f"{len(vacantes['vacantes'])} vacantes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import os
import sys
import tempfile
from pathlib import Path

# Las pruebas usan una base de datos SQLite temporal, nunca datos/pulso.db.
os.environ["PULSO_DB"] = os.path.join(tempfile.mkdtemp(prefix="pulso_pruebas_"), "pulso.db")

# Permite importar motor, ia, apoyo, db y main desde las pruebas.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

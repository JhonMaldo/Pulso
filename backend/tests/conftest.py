import sys
from pathlib import Path

# Permite importar motor, ia, apoyo y main desde las pruebas.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

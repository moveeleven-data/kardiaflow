# tests/conftest.py
import sys
import pathlib

# Ensure utils/ and rest of project is importable
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

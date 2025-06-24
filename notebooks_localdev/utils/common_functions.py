"""
common_functions.py
Portable path resolver for KardiaFlow.

DEV  -> local filesystem inside repo (fast, visible)
PROD -> DBFS paths used by Databricks
"""

import os, pathlib

MODE = os.getenv("KARDIA_ENV", "dev")          # dev | prod
_repo_root = pathlib.Path(__file__).resolve().parents[2]

DEV = {
    "raw_root":    f"{_repo_root}/data/raw/ehr",
    "bronze_root": f"{_repo_root}/data/bronze",
    "silver_root": f"{_repo_root}/data/silver",
    "gold_root":   f"{_repo_root}/data/gold"
}

PROD = {
    "raw_root":    "/kardia/incoming",
    "bronze_root": "dbfs:/kardia/bronze",
    "silver_root": "dbfs:/kardia/silver",
    "gold_root":   "dbfs:/kardia/gold",
}

def cfg(key: str) -> str:
    """Return path based on current environment."""
    return (DEV if MODE == "dev" else PROD)[key]

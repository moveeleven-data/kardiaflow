import os, pathlib

MODE = os.getenv("KARDIA_ENV", "dev")   # dev | prod

_repo_root = pathlib.Path(__file__).resolve().parents[2]

DEV = {
    "raw_root":   f"file://{_repo_root}/data/raw/ehr",
    "bronze_root": "file:/tmp/kardia/bronze",
    "silver_root": "file:/tmp/kardia/silver",
    "gold_root":   "file:/tmp/kardia/gold"
}

PROD = {
    "raw_root":   "/kardia/incoming",
    "bronze_root": "dbfs:/kardia/bronze",
    "silver_root": "dbfs:/kardia/silver",
    "gold_root":   "dbfs:/kardia/gold"
}

def cfg(key: str) -> str:
    return (DEV if MODE == "dev" else PROD)[key]

"""
load_feedback.py
Loads feedback.json into MongoDB (kardia_mongo on localhost:27017).

Schema expected:
    patient_id (str)
    visit_id   (str)
    timestamp  (ISODate string)
    satisfaction_score (int 1-5)
    comments   (str)

• Drops/creates the collection for idempotent reloads
• Validates basic field presence
"""

import json
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

# ───────── config ─────────
MONGO_URI   = "mongodb://localhost:27017/"
DB_NAME     = "healthcare"
COLL_NAME   = "feedback"
INPUT_PATH  = "data/raw/feedback/feedback.json"

# ───────── connect ────────
client = MongoClient(MONGO_URI)
db  = client[DB_NAME]

# idempotent load: drop then recreate
if COLL_NAME in db.list_collection_names():
    db.drop_collection(COLL_NAME)

coll = db[COLL_NAME]

# ───────── load JSON ──────
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, list):
    raise ValueError("Expected a JSON array at top level.")

# ───────── simple validation / coercion ──────
def clean(doc: dict) -> dict:
    required = {"patient_id", "visit_id", "timestamp",
                "satisfaction_score", "comments"}
    if not required.issubset(doc):
        missing = required - doc.keys()
        raise ValueError(f"Missing keys {missing} in record {doc}")

    # Convert 'Z' to '+00:00' so datetime.fromisoformat works
    ts = doc["timestamp"].replace("Z", "+00:00")
    doc["timestamp"] = datetime.fromisoformat(ts)
    doc["satisfaction_score"] = int(doc["satisfaction_score"])
    return doc


docs = [clean(d) for d in data]

# ───────── bulk insert ────
try:
    result = coll.insert_many(docs)
    print(f"Inserted {len(result.inserted_ids):,} feedback documents.")
except BulkWriteError as bwe:
    print("Bulk insert error:", bwe.details)
finally:
    client.close()

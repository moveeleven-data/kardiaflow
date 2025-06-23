"""
load_providers.py
Loads providers.csv into PostgreSQL (kardia_postgres on port 5433).

• snake_case headers  (ProviderID → provider_id, etc.)
• Deduplicates on provider_id
• Batch-inserts with execute_batch()
"""

import os, re, time
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# ───────────── Postgres connection ─────────────
DB_PARAMS = {
    "dbname":   "claims",
    "user":     "postgres",
    "password": "yourpass",        # noqa: S105
    "host":     "localhost",
    "port":     5433,              # kardia_postgres container
}

INPUT_PATH = "data/raw/claims/providers.csv"
SKIP_LOG   = "logs/skipped_providers.csv"
BATCH_SIZE = 5_000

# ───────────── read & clean CSV ────────────────
print("Loading CSV …")
df = pd.read_csv(INPUT_PATH)
print(f"{len(df):,} rows read.")

def snake(col: str) -> str:
    return re.sub(r"([0-9a-z])([A-Z])", r"\1_\2", col).lower()

df.columns = [snake(c) for c in df.columns]

required = {"provider_id", "provider_specialty", "provider_location"}
missing  = required - set(df.columns)
if missing:
    raise ValueError(f"Missing expected columns: {missing}")

df = df.where(pd.notnull(df), None)
df["provider_id"] = df["provider_id"].astype(str).str.strip()
df["provider_specialty"]  = df["provider_specialty"].astype(str).str.strip()
df["provider_location"]   = df["provider_location"].astype(str).str.strip()

# ───────────── connect to Postgres ─────────────
conn = psycopg2.connect(**DB_PARAMS)
cur  = conn.cursor()

cur.execute("SELECT provider_id FROM providers")
existing = {r[0] for r in cur.fetchall()}
df = df[~df["provider_id"].isin(existing)]
print(f"{len(df):,} new rows after dedup.")

# ───────────── batch insert ────────────────────
cols = ["provider_id", "provider_specialty", "provider_location"]
insert_sql = f"INSERT INTO providers ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))})"
rows = df[cols].values.tolist()

skipped, start = [], time.time()
print("Inserting …")

for i in range(0, len(rows), BATCH_SIZE):
    batch = rows[i : i + BATCH_SIZE]
    try:
        execute_batch(cur, insert_sql, batch)
        conn.commit()
        if (i // BATCH_SIZE) % 10 == 0:
            print(f"Committed {i + len(batch):,} rows")
    except Exception:
        conn.rollback()
        for r in batch:            # isolate offenders
            try:
                cur.execute(insert_sql, r)
            except Exception as err:
                skipped.append(r + [str(err)])
        conn.commit()

# ───────────── summary ─────────────────────────
loaded = len(rows) - len(skipped)
print(f"Inserted {loaded:,} rows, skipped {len(skipped):,}.")

if skipped:
    os.makedirs("logs", exist_ok=True)
    pd.DataFrame(skipped, columns=cols + ["error"]).to_csv(SKIP_LOG, index=False)
    print(f"Skip-log → {SKIP_LOG}")

cur.close()
conn.close()
print(f"Done in {time.time() - start:.1f}s.")

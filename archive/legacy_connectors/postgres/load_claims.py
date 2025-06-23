"""
load_claims.py
Loads claims.csv into PostgreSQL (kardia_postgres on port 5433).

• snake_case headers (ClaimID → claim_id, etc.)
• Renames claim_amount → amount to match table schema
• Cleans numeric amount
• Deduplicates on claim_id
• Batch-inserts with execute_batch()
"""

import os, re, time
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# ───────────────────────── config ─────────────────────────
DB_PARAMS = {
    "dbname":   "claims",
    "user":     "postgres",
    "password": "yourpass",         # noqa: S105
    "host":     "localhost",
    "port":     5433,               # kardia_postgres
}

INPUT_PATH = "data/raw/claims/claims.csv"
SKIP_LOG   = "logs/skipped_claims.csv"
BATCH_SIZE = 5_000

# ───────────────────── read & clean CSV ───────────────────
print("Loading CSV …")
df = pd.read_csv(INPUT_PATH)
print(f"{len(df):,} rows read.")

# snake_case headers  (ClaimID → claim_id)
df.columns = [re.sub(r"([0-9a-z])([A-Z])", r"\1_\2", c).lower() for c in df.columns]

# verify required columns exist
required = {"claim_id", "patient_id", "provider_id", "claim_amount", "diagnosis_code"}
missing  = required - set(df.columns)
if missing:
    raise ValueError(f"Missing expected columns after snake_case: {missing}")

# rename to match table schema
df.rename(columns={"claim_amount": "amount"}, inplace=True)

# clean fields
df = df.where(pd.notnull(df), None)
for c in ["claim_id", "patient_id", "provider_id", "diagnosis_code"]:
    df[c] = df[c].astype(str).str.strip()

# numeric amount → float
df["amount"] = (df["amount"]
                .astype(str)
                .str.replace(r"[\$,]", "", regex=True)
                .astype(float))

# ───────────────────── connect ────────────────────────────
conn = psycopg2.connect(**DB_PARAMS)
cur  = conn.cursor()

cur.execute("SELECT claim_id FROM claims")
existing = {r[0] for r in cur.fetchall()}
df = df[~df["claim_id"].isin(existing)]
print(f"{len(df):,} new rows after dedup.")

# ───────────────────── batch insert ───────────────────────
cols = ["claim_id", "patient_id", "provider_id", "amount", "diagnosis_code"]
insert_sql = f"INSERT INTO claims ({', '.join(cols)}) VALUES ({', '.join(['%s']*len(cols))})"
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
        for r in batch:  # isolate offenders
            try:
                cur.execute(insert_sql, r)
            except Exception as err:
                skipped.append(r + [str(err)])
        conn.commit()

# ───────────────────── summary ────────────────────────────
loaded = len(rows) - len(skipped)
print(f"Inserted {loaded:,} rows, skipped {len(skipped):,}.")

if skipped:
    os.makedirs("logs", exist_ok=True)
    pd.DataFrame(skipped, columns=cols + ["error"]).to_csv(SKIP_LOG, index=False)
    print(f"Skip-log → {SKIP_LOG}")

cur.close()
conn.close()
print(f"Done in {time.time() - start:.1f}s.")

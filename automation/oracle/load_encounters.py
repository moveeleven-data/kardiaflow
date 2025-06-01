"""
load_encounters.py
------------------
Loads (or retries) synthetic encounter data from CSV into Oracle XE.
• Reads logs/skipped_encounters.csv (if present) and retries only those IDs.
• Cleans data (trim / parse date) with vectorised Pandas ops.
• Bulk-loads with cursor.executemany() + batch commits.
• Writes a fresh skip-log if anything still fails.
"""

import os, time
import numpy as np
import pandas as pd
import cx_Oracle

# --------------------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------------------
EXPECTED_COLUMNS = [
    "ID", "DATE", "PATIENT", "CODE",
    "DESCRIPTION", "REASONCODE", "REASONDESCRIPTION"
]

INPUT_PATH  = "data/raw/ehr/encounters.csv"
SKIP_LOG    = "logs/skipped_encounters.csv"        # created on previous run
ORACLE_DSN  = cx_Oracle.makedsn("localhost", 1521, service_name="XE")
BATCH_SIZE  = 10_000                               # rows per commit
ARRAY_SIZE  = 2_000                                # rows per executemany() call

# --------------------------------------------------------------------------------------
# LOAD / FILTER CSV
# --------------------------------------------------------------------------------------
print("Reading CSV …")
df = pd.read_csv(INPUT_PATH, usecols=EXPECTED_COLUMNS)
print(f"   {len(df):,} rows read.")

# Optional retry-mode: only keep IDs listed in the prior skip-log
if os.path.exists(SKIP_LOG):
    retry_ids = set(pd.read_csv(SKIP_LOG)["encounter_id"].astype(str))
    df = df[df["ID"].astype(str).isin(retry_ids)]
    print(f"Retry mode: {len(df):,} rows queued from previous failures.")

# Replace pandas NA with None early
df = df.where(pd.notnull(df), None)

# --------------------------------------------------------------------------------------
# CLEANING (vectorised)
# --------------------------------------------------------------------------------------
print("Cleaning data …")
t0 = time.time()

# Trim / truncate strings
for col, maxlen in {
    "ID": 50, "PATIENT": 50, "CODE": 20,
    "DESCRIPTION": 255, "REASONCODE": 20, "REASONDESCRIPTION": 255
}.items():
    df[col] = df[col].astype(str).str.strip().str[:maxlen]

# Fast date mask + parse
exact_mask = df["DATE"].str.match(r"\d{4}-\d{2}-\d{2}")
df.loc[exact_mask, "DATE"] = pd.to_datetime(
    df.loc[exact_mask, "DATE"], format="%Y-%m-%d"
).dt.strftime("%Y-%m-%d")
df.loc[~exact_mask, "DATE"] = np.nan               # becomes NULL in Oracle

print(f" Cleaning finished in {time.time()-t0:.1f}s")

# --------------------------------------------------------------------------------------
# CONNECT & FILTER OUT ALREADY-LOADED IDs
# --------------------------------------------------------------------------------------
print("Connecting to Oracle XE …")
conn = cx_Oracle.connect(user="system", password="oracle", dsn=ORACLE_DSN)
cur  = conn.cursor()

cur.execute("SELECT ID FROM encounters")
existing_ids = {r[0] for r in cur.fetchall()}
df = df[~df["ID"].isin(existing_ids)]
print(f"   {len(df):,} rows remain after duplicate check.")

# --------------------------------------------------------------------------------------
# BULK INSERT WITH executemany()
# --------------------------------------------------------------------------------------
insert_sql = """
INSERT INTO encounters (
  ID, "DATE", PATIENT, CODE,
  DESCRIPTION, REASONCODE, REASONDESCRIPTION
) VALUES (
  :1, TO_DATE(:2,'YYYY-MM-DD'), :3, :4, :5, :6, :7
)
"""
cur.prepare(insert_sql)
cur.bindarraysize = ARRAY_SIZE

rows          = df[EXPECTED_COLUMNS].to_numpy().tolist()
skipped_rows  = []
start_time    = time.time()

print("Inserting …")
for offset in range(0, len(rows), BATCH_SIZE):
    batch = rows[offset : offset + BATCH_SIZE]
    try:
        for sub in range(0, len(batch), ARRAY_SIZE):
            cur.executemany(None, batch[sub : sub + ARRAY_SIZE])
        conn.commit()
        if offset % (100_000) == 0:
            rate = (offset + len(batch)) / (time.time() - start_time + 0.01)
            print(f"   {offset + len(batch):,} rows committed ({rate:,.0f} rows/s)")
    except Exception as e:
        # Fallback: insert rows one-by-one to isolate offenders
        for r in batch:
            try:
                cur.execute(None, r)
            except Exception as inner:
                skipped_rows.append((*r, str(inner)))
        conn.commit()

print(f"Load finished in {time.time()-start_time:.1f}s")

# --------------------------------------------------------------------------------------
# LOG RESULTS
# --------------------------------------------------------------------------------------
print(f" Loaded {len(rows) - len(skipped_rows):,} rows.")
print(f" Skipped {len(skipped_rows):,} rows.")

if skipped_rows:
    os.makedirs(os.path.dirname(SKIP_LOG), exist_ok=True)
    pd.DataFrame(
        skipped_rows,
        columns=[
            "ID", "DATE", "PATIENT", "CODE",
            "DESCRIPTION", "REASONCODE", "REASONDESCRIPTION", "error"
        ],
    ).to_csv(SKIP_LOG, index=False)
    print(f"New skip log written → {SKIP_LOG}")

cur.close()
conn.close()
print("Done.")

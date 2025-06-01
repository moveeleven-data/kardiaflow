"""
Script: load_procedures.py
Loads synthetic procedure data from CSV into Oracle XE with validation,
trimming, and error logging.
"""

import os
import time
import numpy as np
import cx_Oracle
import pandas as pd

EXPECTED_COLUMNS = [
    'DATE', 'PATIENT', 'ENCOUNTER',
    'CODE', 'DESCRIPTION', 'REASONCODE', 'REASONDESCRIPTION'
]
INPUT_PATH  = "data/raw/ehr/procedures.csv"
OUTPUT_LOG  = "logs/skipped_procedures.csv"
ORACLE_DSN  = cx_Oracle.makedsn("localhost", 1521, service_name="XE")

def safe_date(val):
    try:
        if pd.isnull(val):
            return None
        parsed = pd.to_datetime(val, errors="coerce")
        if pd.isnull(parsed) or parsed.year <= 0:
            return None
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return None

def trim(val, maxlen):
    if pd.isnull(val):
        return None
    return str(val).strip()[:maxlen]

print("Starting script…")
df = pd.read_csv(INPUT_PATH, usecols=EXPECTED_COLUMNS)
print(f"Loaded {len(df)} rows from CSV.")
df = df.where(pd.notnull(df), None)

print("Connecting to Oracle…")
conn   = cx_Oracle.connect(user="system", password="oracle", dsn=ORACLE_DSN)
cursor = conn.cursor()
print("Connected.")

print("Cleaning data…")
t0 = time.time()

# ---- 1. vectorized trim on all string columns ----
for col, maxlen in {
        'PATIENT':50, 'ENCOUNTER':50,
        'CODE':20, 'DESCRIPTION':255,
        'REASONCODE':20, 'REASONDESCRIPTION':255
    }.items():
    df[col] = df[col].astype(str).str.strip().str[:maxlen]

# ---- 2. fast date parse (no slow fallback) ----
exact_mask = df['DATE'].str.match(r'\d{4}-\d{2}-\d{2}')
df.loc[exact_mask, 'DATE'] = (
    pd.to_datetime(df.loc[exact_mask, 'DATE'], format="%Y-%m-%d")
      .dt.strftime("%Y-%m-%d")
)
df.loc[~exact_mask, 'DATE'] = np.nan   # Oracle will treat as NULL

print(f"Cleaning finished in {time.time()-t0:.2f}s")

skipped_rows = []
print("Beginning insert loop…")
for i, row in df.iterrows():
    try:
        cursor.execute("""
            INSERT INTO procedures (
              "DATE", PATIENT, ENCOUNTER,
              CODE, DESCRIPTION, REASONCODE, REASONDESCRIPTION
            ) VALUES (
              TO_DATE(:1,'YYYY-MM-DD'), :2, :3,
              :4, :5, :6, :7
            )
        """, (
            row['DATE'], row['PATIENT'], row['ENCOUNTER'],
            row['CODE'], row['DESCRIPTION'],
            row['REASONCODE'], row['REASONDESCRIPTION']
        ))
        if i % 1000 == 0:
            print(f"Processed row {i}")
    except Exception as e:
        skipped_rows.append((i, None, str(e)))

print("Committing…")
conn.commit()
conn.close()
print(f"Loaded {len(df) - len(skipped_rows)} procedures.")
print(f"Skipped {len(skipped_rows)} rows.")

if skipped_rows:
    os.makedirs(os.path.dirname(OUTPUT_LOG), exist_ok=True)
    pd.DataFrame(skipped_rows, columns=["row_index", "procedure_id", "error"]).to_csv(
        OUTPUT_LOG, index=False
    )
    print(f"Log saved → {OUTPUT_LOG}")

"""
Script: load_patients.py

This script loads synthetic patient data from a CSV file into an Oracle XE database, ensuring
data quality through cleaning, deduplication, and validation. It’s designed for batch ingestion
in pipelines where raw data may be incomplete, inconsistent, or exceed schema constraints.

1. Read only the expected columns from the CSV.
2. Clean the data: malformed dates are nulled, long strings are trimmed to match Oracle limits,
   and missing values are normalized to None.
3. Query the Oracle DB to identify existing patient IDs and filter them out of the load.
4. Attempt to insert each cleaned record; if it fails (e.g. due to constraint violations),
   we skip it and log the issue.
"""

import os
import cx_Oracle
import pandas as pd

# ---------- CONFIG ----------
expected_columns = [
    'ID', 'BIRTHDATE', 'DEATHDATE', 'SSN', 'DRIVERS', 'PASSPORT',
    'PREFIX', 'FIRST', 'LAST', 'SUFFIX', 'MAIDEN', 'MARITAL',
    'RACE', 'ETHNICITY', 'GENDER', 'BIRTHPLACE', 'ADDRESS'
]

input_path = "data/raw/ehr/patients.csv"
output_log = "logs/skipped_patients.csv"
# ----------------------------

print("Starting script...")

# ---------- HELPER FUNCTIONS ----------
def safe_date(val):
    try:
        if pd.isnull(val): return None
        parsed = pd.to_datetime(val, errors='coerce')
        if pd.isnull(parsed) or parsed.year <= 0: return None
        return parsed.strftime('%Y-%m-%d')
    except:
        return None

def trim(val, maxlen):
    if pd.isnull(val): return None
    return str(val).strip()[:maxlen]

# ---------- LOAD CSV ----------
print("Loading CSV...")
df = pd.read_csv(input_path, usecols=expected_columns)
print(f"Loaded {len(df)} rows from CSV.")

df = df.where(pd.notnull(df), None)

# ---------- CONNECT TO ORACLE ----------
print("Connecting to Oracle...")
dsn = cx_Oracle.makedsn("localhost", 1521, service_name="XE")
conn = cx_Oracle.connect(user="system", password="oracle", dsn=dsn)
cursor = conn.cursor()
print("Connected.")

print("Fetching existing patient IDs...")
cursor.execute("SELECT ID FROM patients")
existing_ids = set(r[0] for r in cursor.fetchall())
print(f"Found {len(existing_ids)} existing patients in the database.")

# ---------- FILTER OUT EXISTING ----------
print("Filtering out already-inserted rows...")
df = df[~df['ID'].isin(existing_ids)]
df = df[df['ID'].notnull()]  # Ensure no missing IDs
print(f"{len(df)} rows remaining to process.")

# ---------- CLEAN DATA ----------
print("Cleaning data...")
df['ID']         = df['ID'].apply(lambda x: trim(x, 50))
df['BIRTHDATE']  = df['BIRTHDATE'].apply(safe_date)
df['DEATHDATE']  = df['DEATHDATE'].apply(safe_date)
df['GENDER']     = df['GENDER'].apply(lambda x: trim(x, 1))
df['SSN']        = df['SSN'].apply(lambda x: trim(x, 20))
df['PREFIX']     = df['PREFIX'].apply(lambda x: trim(x, 10))
df['SUFFIX']     = df['SUFFIX'].apply(lambda x: trim(x, 10))
df['MARITAL']    = df['MARITAL'].apply(lambda x: trim(x, 10))
df['DRIVERS']    = df['DRIVERS'].apply(lambda x: trim(x, 50))
df['ETHNICITY']  = df['ETHNICITY'].apply(lambda x: trim(x, 50))

# ---------- INSERT ROWS ----------
skipped_rows = []
print("Beginning insert loop...")
for i, row in df.iterrows():
    try:
        if not row['ID']:
            raise ValueError("Missing patient ID")

        cursor.execute("""
            INSERT INTO patients (
                ID, BIRTHDATE, DEATHDATE, SSN, DRIVERS, PASSPORT,
                PREFIX, FIRST, LAST, SUFFIX, MAIDEN, MARITAL,
                RACE, ETHNICITY, GENDER, BIRTHPLACE, ADDRESS
            ) VALUES (
                :1, TO_DATE(:2, 'YYYY-MM-DD'), TO_DATE(:3, 'YYYY-MM-DD'),
                :4, :5, :6, :7, :8, :9, :10, :11, :12,
                :13, :14, :15, :16, :17
            )
        """, (
            row['ID'], row['BIRTHDATE'], row['DEATHDATE'], row['SSN'], row['DRIVERS'], row['PASSPORT'],
            row['PREFIX'], row['FIRST'], row['LAST'], row['SUFFIX'], row['MAIDEN'], row['MARITAL'],
            row['RACE'], row['ETHNICITY'], row['GENDER'], row['BIRTHPLACE'], row['ADDRESS']
        ))

        if i % 1000 == 0:
            print(f"Processed row {i}")

    except Exception as e:
        skipped_rows.append((i, row['ID'], str(e)))

# ---------- FINISH ----------
print("Committing changes...")
conn.commit()
conn.close()
print(f"Loaded {len(df) - len(skipped_rows)} new patients into Oracle.")
print(f"Skipped {len(skipped_rows)} rows.")

# ---------- SAVE SKIPPED ROWS ----------
if skipped_rows:
    os.makedirs(os.path.dirname(output_log), exist_ok=True)
    pd.DataFrame(skipped_rows, columns=["row_index", "patient_id", "error"]).to_csv(output_log, index=False)
    print(f"Logged skipped rows to {output_log}")

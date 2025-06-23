"""
Script: load_patients.py

This script loads synthetic patient data from a CSV file into an Oracle XE database.
It validates, cleans, and inserts rows while skipping and logging any that fail.

Steps:
1. Read expected columns from CSV using pandas.
2. Normalize values (nulls, string length, dates).
3. Filter out patients already in the database (via ID).
4. Insert each new record into Oracle; log failures.
"""

import os
import cx_Oracle
import pandas as pd

# ---------- CONFIGURATION ----------
EXPECTED_COLUMNS = [
    'ID', 'BIRTHDATE', 'DEATHDATE', 'SSN', 'DRIVERS', 'PASSPORT',
    'PREFIX', 'FIRST', 'LAST', 'SUFFIX', 'MAIDEN', 'MARITAL',
    'RACE', 'ETHNICITY', 'GENDER', 'BIRTHPLACE', 'ADDRESS'
]

INPUT_PATH = "data/raw/ehr/patients.csv"
OUTPUT_LOG = "logs/skipped_patients.csv"
ORACLE_DSN = cx_Oracle.makedsn("localhost", 1521, service_name="XE")

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

# ---------- MAIN SCRIPT ----------
print("Starting script...")

# Load and preprocess CSV
print("Loading CSV...")
df = pd.read_csv(INPUT_PATH, usecols=EXPECTED_COLUMNS)
print(f"Loaded {len(df)} rows from CSV.")
df = df.where(pd.notnull(df), None)

# Connect to Oracle
print("Connecting to Oracle...")
conn = cx_Oracle.connect(user="system", password="oracle", dsn=ORACLE_DSN)
cursor = conn.cursor()
print("Connected.")

# Get already existing patient IDs
print("Fetching existing patient IDs...")
cursor.execute("SELECT ID FROM patients")
existing_ids = set(row[0] for row in cursor.fetchall())
print(f"Found {len(existing_ids)} existing patients.")

# Filter and validate rows
print("Filtering and validating rows...")
df = df[~df['ID'].isin(existing_ids)]
df = df[df['ID'].notnull()]
print(f"{len(df)} new rows to process.")

# Clean field values
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

# Insert into Oracle
print("Beginning insert loop...")
skipped_rows = []

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

# Commit and cleanup
print("Committing changes...")
conn.commit()
conn.close()
print(f"Loaded {len(df) - len(skipped_rows)} new patients into Oracle.")
print(f"Skipped {len(skipped_rows)} rows.")

# Log skipped rows
if skipped_rows:
    os.makedirs(os.path.dirname(OUTPUT_LOG), exist_ok=True)
    pd.DataFrame(skipped_rows, columns=["row_index", "patient_id", "error"]).to_csv(OUTPUT_LOG, index=False)
    print(f"Logged skipped rows to {OUTPUT_LOG}")

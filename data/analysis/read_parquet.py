from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder.appName("ParquetCheck").getOrCreate()

patients_parquet = "file:///mnt/c/Users/KV-62/Desktop/KardiaFlow/data/analysis/full_load_patients_20250603_1941.parquet"
encounters_parquet = "file:///mnt/c/Users/KV-62/Desktop/KardiaFlow/data/analysis/full_load_encounters_20250603_1942.parquet"
procedures_parquet = "file:///mnt/c/Users/KV-62/Desktop/KardiaFlow/data/analysis/full_load_procedures_20250603_1944.parquet"

# Read the Parquet files
df_patients = spark.read.parquet(patients_parquet)
df_encounters = spark.read.parquet(encounters_parquet)
df_procedures = spark.read.parquet(procedures_parquet)

# Show the first few rows for quick preview (for each dataset)
print("Patients Data:")
df_patients.show(5)

print("Encounters Data:")
df_encounters.show(5)

print("Procedures Data:")
df_procedures.show(5)

# Get the number of rows (faster than pandas) for each dataset
print(f"Patients Rows: {df_patients.count()}")
print(f"Encounters Rows: {df_encounters.count()}")
print(f"Procedures Rows: {df_procedures.count()}")

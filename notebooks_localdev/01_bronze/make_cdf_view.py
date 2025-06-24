from pyspark.sql import SparkSession, functions as F
import pathlib, os

# --- paths ----------------------------------------------------------
REPO = pathlib.Path(__file__).resolve().parents[2]
BRONZE = REPO / "data" / "bronze" / "bronze_patients"          # <— already written

spark = (
    SparkSession.builder
      .appName("cdf_view")
      .master("local[1]")
      .config("spark.sql.extensions","io.delta.sql.DeltaSparkSessionExtension")
      .config("spark.sql.catalog.spark_catalog","org.apache.spark.sql.delta.catalog.DeltaCatalog")
      .getOrCreate()
)

bronze_uri = f"delta.`{BRONZE.as_posix()}`"                    # delta.`file:///…`

spark.sql(f"""
CREATE OR REPLACE TEMP VIEW bronze_patients_changes AS
SELECT * FROM table_changes('{bronze_uri}', 0)
""")

print("\n-- change_type counts ---------------------------")
spark.sql("""
SELECT _change_type AS change_type, COUNT(*) cnt
FROM bronze_patients_changes
GROUP BY _change_type
""").show()
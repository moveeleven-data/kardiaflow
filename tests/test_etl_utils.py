from pyspark.sql import Row
from kflow.etl_utils import add_audit_cols

def test_add_audit_cols_adds_expected_columns(spark, mocker):
    # Patch current_batch_id to a stable value
    mocker.patch("kflow.etl_utils.current_batch_id", return_value="test-batch-id")

    df = spark.createDataFrame([Row(id=1, val="A")])
    out = add_audit_cols(df)
    for c in ["_ingest_ts", "_source_file", "_batch_id"]:
        assert c in out.columns

    # _batch_id contains patched value
    assert out.select("_batch_id").first()[0] == "test-batch-id"

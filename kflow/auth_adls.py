# kflow/auth_adls.py
"""Kardiaflow - ADLS Gen2 OAuth on Databricks.

Configures Spark to access ADLS Gen2 using a service principal (OAuth).
This function:
  - Reads client credentials from a Databricks secret scope
  - Writes OAuth configuration to spark.hadoop.* (the settings ABFS/Hive read)
  - Removes any SharedKey/SAS leftovers that might override OAuth
"""

from __future__ import annotations
from pyspark.sql import SparkSession


def ensure_adls_oauth(
    *,
    account: str = "kardiaadlsdemo",
    scope: str = "kardia",
    tenant_key: str = "sp_tenant_id",
    client_id_key: str = "sp_client_id",
    client_secret_key: str = "sp_client_secret",
) -> None:
    spark = SparkSession.builder.getOrCreate()

    # Load service principal credentials (tenant, client ID, secret) from a Databricks secret scope
    try:
        from pyspark.dbutils import DBUtils
        dbu = DBUtils(spark)
    except Exception:
        dbu = globals().get("dbutils", None)
    if dbu is None:
        raise RuntimeError("dbutils is not available; run on a Databricks cluster.")

    def _secret(k: str) -> str:
        v = dbu.secrets.get(scope=scope, key=k)  # type: ignore[attr-defined]
        if not v or not v.strip():
            raise ValueError(f"Secret '{scope}/{k}' is empty or missing.")
        return v.strip()

    tenant_id     = _secret(tenant_key)
    client_id     = _secret(client_id_key)
    client_secret = _secret(client_secret_key)

    host = f"{account}.dfs.core.windows.net"
    base = "fs.azure.account"

    # Also grab the live Hadoop conf (used by driver FS ops)
    hconf = spark.sparkContext._jsc.hadoopConfiguration()

    # 1) Write OAuth to BOTH spark.hadoop.* (what Hive/ABFS read) and live Hadoop conf
    oauth = {
        f"{base}.auth.type.{host}": "OAuth",
        f"{base}.oauth.provider.type.{host}": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
        f"{base}.oauth2.client.id.{host}": client_id,
        f"{base}.oauth2.client.secret.{host}": client_secret,
        f"{base}.oauth2.client.endpoint.{host}": f"https://login.microsoftonline.com/{tenant_id}/oauth2/token",
    }
    for k, v in oauth.items():
        spark.conf.set(f"spark.hadoop.{k}", v)
        try:
            hconf.set(k, v)
        except Exception:
            pass

    # 2) Remove SharedKey/SAS on both layers so nothing overrides OAuth
    bad = (
        f"{base}.key",
        f"{base}.key.{host}",
        f"{base}.sas.token.provider.type",
        f"{base}.sas.token.provider.type.{host}",
        f"{base}.sas.fixed.token",
        f"{base}.sas.fixed.token.{host}",
    )
    for k in bad:
        for name in (k, f"spark.hadoop.{k}"):
            try:
                spark.conf.unset(name)
            except Exception:
                pass
        try:
            hconf.unset(k)
        except Exception:
            pass

    # 3) Reset cached FileSystem clients so the new config is used immediately
    spark.sparkContext._jvm.org.apache.hadoop.fs.FileSystem.closeAll()
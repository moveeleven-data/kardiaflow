# src/kflow/auth_adls.py
# Idempotent ADLS Gen2 OAuth setup for ABFS on Databricks jobs clusters

from __future__ import annotations
from typing import Optional
from pyspark.sql import SparkSession

def ensure_adls_oauth(
    *,
    account: str = "kardiaadlsdemo",
    container: str = "lake",
    tenant_secret_scope: str = "kardia",
    tenant_secret_key: str = "sp_tenant_id",
    client_id_secret_scope: str = "kardia",
    client_id_secret_key: str = "sp_client_id",
    client_secret_scope: str = "kardia",
    client_secret_key: str = "sp_client_secret",
    validate_path: Optional[str] = "",   # NOTE: default = container root, always present
) -> str:
    """
    Configure the current Spark session for ADLS Gen2 (ABFS) OAuth using a service principal.
    - Reads secrets from the given Databricks secret scope.
    - Sets ABFS client-credentials properties on *this* Spark session.
    - Optionally validates by listing a path (default: container root).
    Returns: the ABFSS base URI, e.g. "abfss://lake@<account>.dfs.core.windows.net".
    Safe to call multiple times per session.
    """
    spark = SparkSession.builder.getOrCreate()

    # Get a dbutils handle (works in jobs & notebooks)
    try:
        from pyspark.dbutils import DBUtils  # on DBR runtimes that provide it
        dbu = DBUtils(spark)
    except Exception:
        dbu = globals().get("dbutils", None)
    if dbu is None:
        raise RuntimeError("dbutils is not available; run this on a Databricks cluster.")

    def _secret(scope: str, key: str) -> str:
        val = dbu.secrets.get(scope=scope, key=key)  # type: ignore[attr-defined]
        if not val or not val.strip():
            raise ValueError(f"Secret '{scope}/{key}' is empty or missing.")
        return val.strip()

    tenant_id     = _secret(tenant_secret_scope, tenant_secret_key)
    client_id     = _secret(client_id_secret_scope, client_id_secret_key)
    client_secret = _secret(client_secret_scope, client_secret_key)

    host = f"{account}.dfs.core.windows.net"
    pfx  = "fs.azure.account"

    # Always set explicitly (don't attempt read-before-set)
    spark.conf.set(f"{pfx}.auth.type.{host}", "OAuth")
    spark.conf.set(
        f"{pfx}.oauth.provider.type.{host}",
        "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
    )
    spark.conf.set(f"{pfx}.oauth2.client.id.{host}", client_id)
    spark.conf.set(f"{pfx}.oauth2.client.secret.{host}", client_secret)
    # Use AAD v1 endpoint (resource flow) — this is what ABFS expects
    spark.conf.set(
        f"{pfx}.oauth2.client.endpoint.{host}",
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/token",
    )

    # Defensive: clear any storage key auth that could conflict
    spark.conf.set(f"{pfx}.key.{host}", "")

    base = f"abfss://{container}@{host}"

    # Validation: list the container root by default; exists even on first run
    path = base if validate_path in (None, "", "/") else f"{base}/{validate_path.lstrip('/')}"
    try:
        dbu.fs.ls(path)  # type: ignore[attr-defined]
    except Exception as e:
        msg = str(e)
        hint = (
            "ADLS OAuth validation failed.\n"
            "- Ensure the Databricks secret scope values (tenant, client id, client secret) match "
            "today's service principal.\n"
            "- Ensure the SP has 'Storage Blob Data Contributor' on the storage account.\n"
            f"- Tried to list: {path}"
        )
        raise RuntimeError(f"{hint}\nUnderlying error: {msg}") from e

    return base

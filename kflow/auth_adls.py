# src/kflow/auth_adls.py
# ADLS Gen2 OAuth setup for ABFS on Databricks (idempotent per session)

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
    validate_path: Optional[str] = "",  # default: container root
) -> str:
    """
    Configure this Spark session to access ADLS Gen2 (ABFS) via SPN OAuth.
    Secrets come from a Databricks scope. Optionally validate by listing a path.
    Safe to call multiple times. Returns the base abfss:// URI.

    Args:
        account: Storage account name (without domain).
        container: ADLS container name.
        tenant_secret_scope: Secret scope containing the AAD tenant id.
        tenant_secret_key: Secret key for the AAD tenant id.
        client_id_secret_scope: Secret scope containing the service principal client id.
        client_id_secret_key: Secret key for the service principal client id.
        client_secret_scope: Secret scope containing the service principal client secret.
        client_secret_key: Secret key for the service principal client secret.
        validate_path: Optional path (relative to the container) to list for validation.

    Returns:
        The ABFSS base URI, e.g. "abfss://lake@<account>.dfs.core.windows.net".
    """
    spark = SparkSession.builder.getOrCreate()

    # dbutils handle (works in jobs and notebooks)
    try:
        from pyspark.dbutils import DBUtils
        dbu = DBUtils(spark)
    except Exception:
        dbu = globals().get("dbutils", None)
    if dbu is None:
        raise RuntimeError("dbutils is not available; run on a Databricks cluster.")

    # secret helper: fetch or fail
    def _secret(scope: str, key: str) -> str:
        val = dbu.secrets.get(scope=scope, key=key)  # type: ignore[attr-defined]
        if not val or not val.strip():
            raise ValueError(f"Secret '{scope}/{key}' is empty or missing.")
        return val.strip()

    tenant_id = _secret(tenant_secret_scope, tenant_secret_key)
    client_id = _secret(client_id_secret_scope, client_id_secret_key)
    client_secret = _secret(client_secret_scope, client_secret_key)

    host = f"{account}.dfs.core.windows.net"
    cfg = "fs.azure.account"

    # OAuth credentials for ABFS
    spark.conf.set(f"{cfg}.auth.type.{host}", "OAuth")
    spark.conf.set(
        f"{cfg}.oauth.provider.type.{host}",
        "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
    )
    spark.conf.set(f"{cfg}.oauth2.client.id.{host}", client_id)
    spark.conf.set(f"{cfg}.oauth2.client.secret.{host}", client_secret)
    # ABFS expects AAD v1 token endpoint
    spark.conf.set(
        f"{cfg}.oauth2.client.endpoint.{host}",
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/token",
    )

    # Clear any shared-key auth to avoid conflicts
    spark.conf.set(f"{cfg}.key.{host}", "")

    base = f"abfss://{container}@{host}"

    # Validate by listing root or a child path
    path = base if validate_path in (None, "", "/") else f"{base}/{validate_path.lstrip('/')}"
    try:
        dbu.fs.ls(path)  # type: ignore[attr-defined]
    except Exception as e:
        hint = (
            "ADLS OAuth validation failed.\n"
            "- Check tenant/client id/client secret in the Databricks scope.\n"
            "- Ensure the SPN has 'Storage Blob Data Contributor' on the account.\n"
            f"- Tried to list: {path}"
        )
        raise RuntimeError(f"{hint}\nUnderlying error: {e}") from e

    return base

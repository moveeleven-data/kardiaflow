# kflow/auth_adls.py
"""
ADLS Gen2 OAuth helper for Databricks.

Context: Small demo without Unity Catalog. This is a lightweight way to make
ABFS use a service principal at runtime so Bronze/Silver/Gold layers all work
the same. It fixes common auth errors but does so by changing cluster-wide settings.

What it does:
  - Pulls credentials from a Databricks secret scope
  - Sets OAuth options in Spark and the driver so reads/writes work
  - Clears out any leftover SharedKey or SAS settings

This is a bit of a hack: it mutates global config for the whole cluster. On
shared it has a blast radius. In those cases, we could use Unity Catalog with a
Storage Credential and an External Location, so access is handled natively.
"""

from pyspark.sql import SparkSession


def ensure_adls_oauth(
    *,
    account: str = "kardiaadlsdemo",
    scope: str = "kardia",
    tenant_key: str = "sp_tenant_id",
    client_id_key: str = "sp_client_id",
    client_secret_key: str = "sp_client_secret",
) -> None:
    # Use the active Spark session provided by Databricks
    spark = SparkSession.builder.getOrCreate()


    # Helper to read a service principal credential from the secret scope.
    # Returns a trimmed string and raises if the secret is missing or blank.
    def _secret(key: str) -> str:
        """Return a secret value (e.g. tenant ID, client ID, client secret)."""
        secret_value = dbutils.secrets.get(scope=scope, key=key)  # type: ignore[attr-defined]
        if not secret_value or not secret_value.strip():
            raise ValueError(f"Secret '{scope}/{key}' is empty or missing.")
        return secret_value.strip()

    # Load service principal credentials from secrets
    tenant_id     = _secret(tenant_key)
    client_id     = _secret(client_id_key)
    client_secret = _secret(client_secret_key)

    # Build common strings used in configuration keys
    adls_host = f"{account}.dfs.core.windows.net"
    conf_base = "fs.azure.account"

    # Driver-side Hadoop configuration used by filesystem clients
    hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()

    # Define OAuth settings for this ADLS account
    oauth_conf = {
        f"{conf_base}.auth.type.{adls_host}": "OAuth",
        f"{conf_base}.oauth.provider.type.{adls_host}":
            "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
        f"{conf_base}.oauth2.client.id.{adls_host}": client_id,
        f"{conf_base}.oauth2.client.secret.{adls_host}": client_secret,
        f"{conf_base}.oauth2.client.endpoint.{adls_host}":
            f"https://login.microsoftonline.com/{tenant_id}/oauth2/token",
    }

    # Apply settings to spark.conf and driver config
    for conf_key, conf_value in oauth_conf.items():
        spark.conf.set(f"spark.hadoop.{conf_key}", conf_value)
        try:
            hadoop_conf.set(conf_key, conf_value)
        except Exception:
            pass

    # Remove SharedKey and SAS settings that could override OAuth
    conflicting_keys = (
        f"{conf_base}.key",
        f"{conf_base}.key.{adls_host}",
        f"{conf_base}.sas.token.provider.type",
        f"{conf_base}.sas.token.provider.type.{adls_host}",
        f"{conf_base}.sas.fixed.token",
        f"{conf_base}.sas.fixed.token.{adls_host}",
    )


    def _unset_conf(conf_key: str) -> None:
        # Remove plain key from Spark configuration
        try:
            spark.conf.unset(conf_key)
        except Exception:
            pass

        # Remove the "spark.hadoop.*" variant from Spark's configuration
        try:
            spark.conf.unset(f"spark.hadoop.{conf_key}")
        except Exception:
            pass

        # Remove the key from the driver's Hadoop configuration
        try:
            hadoop_conf.unset(conf_key)
        except Exception:
            pass

    # Remove all conflicting SharedKey/SAS settings
    for conf_key in conflicting_keys:
        _unset_conf(conf_key)

    # Reset FileSystem clients so new settings take effect immediately
    spark.sparkContext._jvm.org.apache.hadoop.fs.FileSystem.closeAll()
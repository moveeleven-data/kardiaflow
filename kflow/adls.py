# src/kflow/adls.py
# ADLS authentication and path configuration utilities
# - Constructs the base ABFS path for the data lake
# - Resolves the SAS token securely at runtime using secrets
# - Configures Spark to authenticate against ADLS Gen2 using that token

from typing import Final
import os

from pyspark.sql import SparkSession

# ------------------------------------------------------------------------------
# Static ADLS configuration — these remain stable across environments.
# These values are intentionally hardcoded to ensure reliable access to
# known paths during job execution or notebook runs.
# ------------------------------------------------------------------------------

ADLS_ACCOUNT:     Final = "kardiaadlsdemo"     # ADLS Gen2 storage account name
ADLS_SUFFIX:      Final = "core.windows.net"   # DNS suffix for Azure Data Lake
LAKE_CONTAINER:   Final = "lake"               # Single lake container

# SAS token is not hardcoded — it's resolved dynamically from the secret scope.
ADLS_SAS_SCOPE:   Final = "kardia"             # Databricks secret scope
ADLS_SAS_KEYNAME: Final = "adls_lake_sas"      # Secret key holding SAS token

# Constructed ABFS URI prefix for raw data files
LAKE_BASE: Final = f"abfss://{LAKE_CONTAINER}@{ADLS_ACCOUNT}.dfs.{ADLS_SUFFIX}"

# Folder for landing data
RAW_BASE: Final = f"{LAKE_BASE}/kardia/raw"

def _get_dbutils():
    """
    Retrieve the Databricks `dbutils` utility object if available.

    `dbutils` is used to retrieve secrets, manage files, or interact with jobs.
    """

    # Case 1: Running in a notebook or interactive Databricks context
    # In notebooks, `dbutils` is automatically injected into the global namespace.
    if "dbutils" in globals():
        return globals()["dbutils"]

    # Case 2: Running in a job or script context
    # Try to construct dbutils manually via Spark session.
    # This works in non-notebook Databricks jobs, such as triggered jobs.
    try:
        from pyspark.dbutils import DBUtils
        spark = SparkSession.builder.getOrCreate()
        return DBUtils(spark)

    # Case 3: Not running in any Databricks context
    # Fail silently and return None
    except Exception:
        return None


def _resolve_sas(
    scope: str,
    key: str,
    explicit: str | None = None,
    env_var: str = "KARDIA_ADLS_SAS"
) -> str | None:
    """
    Resolve a SAS token for authenticating with ADLS.

    Used internally by ensure_adls_auth().

    Args:
        scope (str): The name of the secret scope containing the SAS token.
        key (str): The key within the secret scope that holds the SAS token.
        explicit (str | None, optional): A SAS token string passed to the function.
        env_var (str, optional): Name of an fallback environment variable.
    """

    # Option 1: Use an explicitly passed SAS token (mostly for manual use/testing)
    if explicit:
        return explicit.lstrip("?")

    # Option 2: Load token from Databricks Secret Scope
    dbu = _get_dbutils()
    if dbu:
        try:
            # Mypy cannot verify that `dbu.secrets.get` exists on this object,
            # because it's dynamically injected by Databricks at runtime,
            # so we suppress this type-checking error.
            tok = dbu.secrets.get(scope, key)  # type: ignore[attr-defined]
            if tok:
                return tok.lstrip("?")
        except Exception:
            pass

    # Option 3: Fallback to an environment variable (used in local development)
    env_tok = os.getenv(env_var)
    return env_tok.lstrip("?") if env_tok else None


def _set_sas(
    account: str,
    token: str,
    suffix: str = "core.windows.net"
) -> None:
    """
    Configure Spark to authenticate with ADLS.

    This registers the token with the current Spark session, enabling read/write access
    to `abfss://` paths in the specified ADLS Gen2 account.

    Used internally by ensure_adls_auth().

    Args:
        account: The ADLS account name (e.g. 'kardiaadlsdemo')
        token:   The SAS token string
        suffix:  Azure DNS suffix
    """
    spark = SparkSession.builder.getOrCreate()

    # Build the base DNS domain for Spark ABFS config
    # Example: 'kardiaadlsdemo.dfs.core.windows.net'
    base = f"{account}.dfs.{suffix}"

    token = token.lstrip("?")

    # 1. Tell Spark to use SAS as the authentication method
    spark.conf.set(f"fs.azure.account.auth.type.{base}", "SAS")

    # 2. tells Spark to treat the SAS token as a constant, fixed string.
    spark.conf.set(
        f"fs.azure.sas.token.provider.type.{base}",
        "org.apache.hadoop.fs.azurebfs.sas.FixedSASTokenProvider"
    )

    # 3. Register the actual SAS token value that will be used to authenticate ABFS
    spark.conf.set(f"fs.azure.sas.fixed.token.{base}", token)


def ensure_adls_auth(sas: str | None = None) -> None:
    """
    Ensure that the current Spark session is authenticated to access ADLS.

    This function is typically called once at the start of a notebook.
    It resolves the token from one of three sources, in order of precedence:
      1. An explicit SAS token passed to this function (rarely used—mainly for testing)
      2. A Databricks Secret Scope
      3. An environment variable named `KARDIA_ADLS_SAS`
    """

    # Attempt to resolve a valid SAS token from any supported source
    tok = _resolve_sas(ADLS_SAS_SCOPE, ADLS_SAS_KEYNAME, sas)

    if not tok:
        raise RuntimeError(
            "No SAS token found. Provide via `ensure_adls_auth(sas=...)`, "
            "Databricks secrets, or the KARDIA_ADLS_SAS env var."
        )

    # Register the token in the Spark session so ABFS paths can be accessed
    _set_sas(ADLS_ACCOUNT, tok, suffix=ADLS_SUFFIX)

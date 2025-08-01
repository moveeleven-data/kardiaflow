# tests/test_auth_adls.py
import pytest
from pyspark.sql import SparkSession

# Reuse your session fixture if you already have it in conftest.py.
# Otherwise, uncomment this local fixture:
#
# @pytest.fixture(scope="session")
# def spark():
#     spark = (
#         SparkSession.builder
#         .master("local[*]")
#         .appName("kflow-tests")
#         .getOrCreate()
#     )
#     yield spark
#     spark.stop()

def test_ensure_adls_oauth_sets_expected_spark_confs(monkeypatch, spark):
    from kflow import auth_adls

    # ---- Fake dbutils for local test (no Databricks) ----
    class _FakeSecrets:
        def __init__(self, mapping):
            self._m = mapping
        def get(self, scope, key):
            k = f"{scope}/{key}"
            if k not in self._m:
                return ""
            return self._m[k]

    class _FakeFS:
        def ls(self, path):
            # No network call; just succeed
            return []

    class _FakeDbutils:
        def __init__(self, secrets_map):
            self.secrets = _FakeSecrets(secrets_map)
            self.fs = _FakeFS()

    secrets_map = {
        "kardia/sp_tenant_id":     "11111111-2222-3333-4444-555555555555",
        "kardia/sp_client_id":     "cid-abc",
        "kardia/sp_client_secret": "csecret-xyz",
    }

    fake = _FakeDbutils(secrets_map)
    # Make ensure_adls_oauth find our fake dbutils
    monkeypatch.setattr(auth_adls, "dbutils", fake, raising=False)

    # Use a small custom account/container to keep assertions tight
    base = auth_adls.ensure_adls_oauth(
        account="unitacct",
        container="lake",
        # keep default secret scopes/keys; our fake secrets satisfy them
        validate_path=""  # list container root (handled by fake.fs.ls)
    )

    host = "unitacct.dfs.core.windows.net"
    pfx  = "fs.azure.account"

    # Auth type & provider
    assert spark.conf.get(f"{pfx}.auth.type.{host}") == "OAuth"
    assert spark.conf.get(f"{pfx}.oauth.provider.type.{host}") == \
        "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider"

    # Client creds
    assert spark.conf.get(f"{pfx}.oauth2.client.id.{host}") == "cid-abc"
    assert spark.conf.get(f"{pfx}.oauth2.client.secret.{host}") == "csecret-xyz"

    # Token endpoint
    assert spark.conf.get(f"{pfx}.oauth2.client.endpoint.{host}") == \
        "https://login.microsoftonline.com/11111111-2222-3333-4444-555555555555/oauth2/token"

    # Storage key auth cleared defensively
    assert spark.conf.get(f"{pfx}.key.{host}") == ""

    # Return value convenience
    assert base == f"abfss://lake@{host}"

def test_ensure_adls_oauth_missing_secret_raises(monkeypatch, spark):
    from kflow import auth_adls

    class _FakeSecrets:
        def get(self, scope, key):
            # Simulate missing/empty secret
            return ""

    class _FakeFS:
        def ls(self, path):
            return []

    class _FakeDbutils:
        def __init__(self):
            self.secrets = _FakeSecrets()
            self.fs = _FakeFS()

    monkeypatch.setattr(auth_adls, "dbutils", _FakeDbutils(), raising=False)

    with pytest.raises(ValueError):
        auth_adls.ensure_adls_oauth(
            account="unitacct",
            container="lake",
            validate_path=""
        )

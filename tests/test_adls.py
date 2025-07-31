# tests/test_adls.py
# Unit tests for ADLS helpers:
# - _resolve_sas: explicit param, env var, and "absent" behavior
# - _set_sas: critical Spark confs are written (token is de-prefixed)

from kflow import adls


def test_resolve_sas_from_explicit():
    # Leading "?" must be stripped
    assert adls._resolve_sas("scope", "key", explicit="?abc") == "abc"


def test_resolve_sas_from_env(monkeypatch):
    monkeypatch.setenv("KARDIA_ADLS_SAS", "?tok123")
    assert adls._resolve_sas(
        "scope", "key", explicit=None, env_var="KARDIA_ADLS_SAS"
    ) == "tok123"


def test_resolve_sas_returns_none_when_absent(monkeypatch):
    # No explicit, no dbutils, no env var -> should return None (caller decides next step)
    monkeypatch.delenv("KARDIA_ADLS_SAS", raising=False)
    assert adls._resolve_sas(
        "scope", "key", explicit=None, env_var="KARDIA_ADLS_SAS"
    ) is None


def test_set_sas_sets_conf_values(spark):
    # Sanity-check key confs are set and token loses leading "?"
    adls._set_sas(account=adls.ADLS_ACCOUNT, token="?abc", suffix=adls.ADLS_SUFFIX)
    base = f"{adls.ADLS_ACCOUNT}.dfs.{adls.ADLS_SUFFIX}"

    assert spark.conf.get(f"fs.azure.account.auth.type.{base}") == "SAS"
    assert (
        spark.conf.get(f"fs.azure.sas.token.provider.type.{base}")
        == "org.apache.hadoop.fs.azurebfs.sas.FixedSASTokenProvider"
    )
    assert spark.conf.get(f"fs.azure.sas.fixed.token.{base}") == "abc"

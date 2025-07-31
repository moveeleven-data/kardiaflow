import importlib
import os
from kflow import adls

def test_resolve_sas_from_explicit():
    assert adls._resolve_sas("scope","key", explicit="?abc") == "abc"

def test_resolve_sas_from_env(monkeypatch):
    monkeypatch.setenv("KARDIA_ADLS_SAS", "?tok123")
    assert adls._resolve_sas("scope","key", explicit=None, env_var="KARDIA_ADLS_SAS") == "tok123"

def test_set_sas_sets_conf_values(spark):
    # sanity-check a few critical confs get set
    adls._set_sas(account=adls.ADLS_ACCOUNT, token="?abc", suffix=adls.ADLS_SUFFIX)
    base = f"{adls.ADLS_ACCOUNT}.dfs.{adls.ADLS_SUFFIX}"
    assert spark.conf.get(f"fs.azure.account.auth.type.{base}") == "SAS"
    assert spark.conf.get(f"fs.azure.sas.token.provider.type.{base}") == "org.apache.hadoop.fs.azurebfs.sas.FixedSASTokenProvider"
    assert spark.conf.get(f"fs.azure.sas.fixed.token.{base}") == "abc"

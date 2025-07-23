# src/kflow/display_utils.py
"""
Display helpers that work both on Databricks and locally.
- Tries Databricks runtime imports first.
- Falls back to IPython.display + SparkSession locally.
"""

from __future__ import annotations

# Try native Databricks objects
try:
    from databricks.sdk.runtime import display, displayHTML, spark  # type: ignore
except Exception:  # local / unit-test fallback
    from pyspark.sql import SparkSession
    from IPython.display import HTML as _HTML, display as _ip_display

    def displayHTML(html: str):
        _ip_display(_HTML(html))

    display = _ip_display
    spark = SparkSession.builder.getOrCreate()


def banner(msg: str, ok: bool = True) -> None:
    color = "green" if ok else "red"
    displayHTML(f"<div style='color:{color};font-weight:bold'>{msg}</div>")


def show_history(delta_path: str, limit: int = 5) -> None:
    hist = (
        spark.sql(f"DESCRIBE HISTORY delta.`{delta_path}`")
             .select("version", "timestamp", "operation", "operationParameters")
             .limit(limit)
    )
    displayHTML("<div style='margin-top:10px;font-weight:bold'>Recent Delta History:</div>")
    display(hist)


def show_head(df, n: int = 5) -> None:
    display(df.limit(n))


def banner_stream(name: str, trigger: str, source: str) -> None:
    banner(f"Stream started: {name} • Trigger: {trigger} • Source: {source}", ok=True)

import pytest
pytest.skip("Legacy Oracle test skipped — no listener available.", allow_module_level=True)

import cx_Oracle

conn = cx_Oracle.connect(
    user="system",
    password="oracle",
    dsn="localhost:1521/XE"
)

print("Connected to Oracle XE!")
conn.close()

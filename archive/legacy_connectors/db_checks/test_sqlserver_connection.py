import pyodbc

def test_sqlserver_connection():
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=localhost,1433;'
            'UID=sa;'
            'PWD=YourStrong!Passw0rd',
            timeout=5
        )
        print("Connected to SQL Server successfully.")
        conn.close()
    except Exception as e:
        print("SQL Server connection failed.")
        print(e)

if __name__ == "__main__":
    test_sqlserver_connection()

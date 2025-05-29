import psycopg2
from psycopg2 import OperationalError

def test_postgres_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            user="postgres",
            password="pass"
        )
        print("Connected to PostgreSQL successfully.")
        conn.close()
    except OperationalError as e:
        print("Connection failed.")
        print(e)

if __name__ == "__main__":
    test_postgres_connection()

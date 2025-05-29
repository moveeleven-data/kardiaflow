from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def test_mongo_connection():
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=2000)
        # The ismaster command is cheap and does not require auth
        client.admin.command('ping')
        print("Connected to MongoDB successfully.")
    except ConnectionFailure as e:
        print("MongoDB connection failed.")
        print(e)

if __name__ == "__main__":
    test_mongo_connection()

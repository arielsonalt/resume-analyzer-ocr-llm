import os
from pymongo import MongoClient
from app.store.models import LogEntry

class MongoLogStore:
    def __init__(self):
        uri = os.getenv("MONGO_URI", "mongodb://mongo:27017")
        db_name = os.getenv("MONGO_DB", "techmatch")
        col_name = os.getenv("MONGO_COLLECTION", "cv_tool_logs")
        self.client = MongoClient(uri)
        self.col = self.client[db_name][col_name]
        self.col.create_index("request_id", unique=True)
        self.col.create_index([("user_id", 1), ("timestamp", -1)])

    def insert(self, entry: LogEntry) -> None:
        doc = {
            "request_id": entry.request_id,
            "user_id": entry.user_id,
            "timestamp": entry.timestamp,
            "query": entry.query,
            "result": entry.result,
        }
        self.col.insert_one(doc)
    
    def find_all(self, limit: int = 50):
        docs = self.col.find().sort("timestamp", -1).limit(limit)
        return [self._serialize(d) for d in docs]

    def find_by_user(self, user_id: str, limit: int = 50):
        docs = self.col.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
        return [self._serialize(d) for d in docs]

    def _serialize(self, doc):
        doc["_id"] = str(doc["_id"])
        return doc


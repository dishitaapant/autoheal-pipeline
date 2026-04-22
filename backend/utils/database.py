"""
Database connection utility using Motor (async pymongo)
"""
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING

logger = logging.getLogger("autoheal.db")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "autoheal")

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    try:
        client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        await client.admin.command("ping")
        logger.info(f"Connected to MongoDB at {MONGO_URL}, database: {DB_NAME}")
        await _create_indexes()
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        logger.warning("Running without persistent storage (in-memory mode)")
        db = InMemoryDB()


async def disconnect_db():
    global client
    if client:
        client.close()
        logger.info("Disconnected from MongoDB")


async def _create_indexes():
    """Create indexes for performance"""
    try:
        await db.pipeline_runs.create_index([("created_at", DESCENDING)])
        await db.pipeline_runs.create_index([("repo", 1), ("status", 1)])
        await db.healing_actions.create_index([("pipeline_run_id", 1)])
        await db.healing_actions.create_index([("created_at", DESCENDING)])
        logger.info("Database indexes created")
    except Exception as e:
        logger.warning(f"Index creation failed: {e}")


def get_db():
    return db


class InMemoryDB:
    """Fallback in-memory database when MongoDB is unavailable"""
    def __init__(self):
        self._collections = {}
        logger.warning("Using InMemoryDB — data will not persist across restarts")

    def __getattr__(self, name):
        if name not in self._collections:
            self._collections[name] = InMemoryCollection(name)
        return self._collections[name]


class InMemoryCollection:
    def __init__(self, name):
        self.name = name
        self._data = []
        self._id_counter = 1

    async def insert_one(self, doc):
        from bson import ObjectId
        doc["_id"] = str(ObjectId())
        self._data.append(doc.copy())
        return type("Result", (), {"inserted_id": doc["_id"]})()

    async def find_one(self, query):
        for doc in self._data:
            if self._matches(doc, query):
                return doc
        return None

    async def update_one(self, query, update, upsert=False):
        for doc in self._data:
            if self._matches(doc, query):
                if "$set" in update:
                    doc.update(update["$set"])
                if "$push" in update:
                    for k, v in update["$push"].items():
                        doc.setdefault(k, []).append(v)
                return
        if upsert:
            new_doc = {**query}
            if "$set" in update:
                new_doc.update(update["$set"])
            await self.insert_one(new_doc)

    def find(self, query=None, *args, **kwargs):
        return InMemoryCursor(self._data, query or {})

    async def count_documents(self, query=None):
        results = [d for d in self._data if self._matches(d, query or {})]
        return len(results)

    async def aggregate(self, pipeline):
        return []

    async def create_index(self, *args, **kwargs):
        pass

    def _matches(self, doc, query):
        for k, v in query.items():
            if isinstance(v, dict):
                doc_val = doc.get(k)
                if "$in" in v and doc_val not in v["$in"]:
                    return False
                if "$gte" in v and (doc_val is None or doc_val < v["$gte"]):
                    return False
            elif doc.get(k) != v:
                return False
        return True


class InMemoryCursor:
    def __init__(self, data, query):
        self._data = [d for d in data if self._matches(d, query)]
        self._sort_key = None
        self._limit_val = None
        self._skip_val = 0

    def sort(self, key, direction=None):
        if isinstance(key, list):
            for k, d in reversed(key):
                self._data.sort(key=lambda x: x.get(k, ""), reverse=(d == -1))
        else:
            self._data.sort(key=lambda x: x.get(key, ""), reverse=(direction == -1))
        return self

    def limit(self, n):
        self._limit_val = n
        return self

    def skip(self, n):
        self._skip_val = n
        return self

    def __aiter__(self):
        data = self._data[self._skip_val:]
        if self._limit_val:
            data = data[: self._limit_val]
        return self._async_gen(data)

    async def _async_gen(self, data):
        for item in data:
            yield item

    async def to_list(self, length=None):
        data = self._data[self._skip_val:]
        if self._limit_val:
            data = data[: self._limit_val]
        if length:
            data = data[:length]
        return data

    def _matches(self, doc, query):
        for k, v in query.items():
            if isinstance(v, dict):
                doc_val = doc.get(k)
                if "$in" in v and doc_val not in v["$in"]:
                    return False
                if "$gte" in v and (doc_val is None or doc_val < v["$gte"]):
                    return False
            elif doc.get(k) != v:
                return False
        return True

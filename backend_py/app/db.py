import logging

from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

log = logging.getLogger("db")


class Database:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self, uri: str, name: str):
        if not uri:
            raise RuntimeError("MONGO_URI not found in environment variables")
        self.client = AsyncMongoClient(
            uri,
            server_api=ServerApi("1", strict=True, deprecation_errors=True),
            tz_aware=True,
        )
        await self.client.admin.command("ping")
        self.db = self.client[name]
        log.info("✅ Successfully connected to MongoDB!")

    async def disconnect(self):
        if self.client:
            await self.client.close()
            log.info("MongoDB connection closed")

    def collection(self, name: str):
        if self.db is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return self.db[name]


database = Database()

import asyncio
import json
import logging
import os
import time
from typing import Any

import aiosqlite
from config import config
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("Astra.Database")


class Database:
    def __init__(self):
        self.mongo_client = None
        self.mongo_db = None
        self.sqlite_conn = None
        self.initialized = False

    async def initialize(self):
        if self.initialized:
            return

        # Initialize SQLite
        self.sqlite_conn = await aiosqlite.connect(config.SQLITE_PATH)
        await self.sqlite_conn.execute(
            "CREATE TABLE IF NOT EXISTS state (key TEXT PRIMARY KEY, value TEXT, updated_at INTEGER)"
        )
        await self.sqlite_conn.execute(
            "CREATE TABLE IF NOT EXISTS seen_memes (post_id TEXT PRIMARY KEY, subreddit TEXT, fetched_at INTEGER)"
        )
        await self.sqlite_conn.commit()

        # Initialize MongoDB
        if config.MONGO_URI:
            try:
                self.mongo_client = AsyncIOMotorClient(config.MONGO_URI)
                # Parse DB name from URI or use default
                db_name = config.MONGO_URI.split("/")[-1].split("?")[0] or "astra_userbot"
                self.mongo_db = self.mongo_client[db_name]
                logger.info("Connected to MongoDB")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                self.mongo_client = None

        await self._sync_on_startup()
        self.initialized = True

    async def _sync_on_startup(self):
        """Syncs data between SQLite and MongoDB."""
        if self.mongo_db is None:
            # If no mongo, maybe migrate from JSON to SQLite?
            await self._migrate_from_json()
            return

        logger.info("Starting database synchronization...")

        # 1. Get everything from SQLite
        cursor = await self.sqlite_conn.execute("SELECT key, value, updated_at FROM state")
        sqlite_data = {}
        for row in await cursor.fetchall():
            try:
                sqlite_data[row[0]] = {"value": json.loads(row[1]), "updated_at": row[2]}
            except Exception as e:
                logger.warning(f"Failed to parse SQLite value for key {row[0]}: {e}")
                continue

        # 2. Get everything from MongoDB
        mongo_data = {}
        try:
            async for doc in self.mongo_db.state.find({}):
                mongo_data[doc["_id"]] = {"value": doc.get("value"), "updated_at": doc.get("updated_at", 0)}
        except Exception as e:
            logger.error(f"Failed to fetch data from MongoDB for sync: {e}")
            return

        # 3. Synchronize
        all_keys = set(sqlite_data.keys()) | set(mongo_data.keys())

        for key in all_keys:
            s_val = sqlite_data.get(key)
            m_val = mongo_data.get(key)

            # Case: Only in SQLite
            if s_val is not None and m_val is None:
                await self._mongo_update_task(
                    "state", {"_id": key}, {"$set": {"value": s_val["value"], "updated_at": s_val["updated_at"]}}
                )
            
            # Case: Only in MongoDB
            elif m_val is not None and s_val is None:
                await self.sqlite_conn.execute(
                    "INSERT INTO state (key, value, updated_at) VALUES (?, ?, ?)",
                    (key, json.dumps(m_val["value"]), m_val["updated_at"]),
                )
            
            # Case: Both exist -> Use timestamps or handle null-ish values
            elif s_val is not None and m_val is not None:
                s_value = s_val["value"]
                m_value = m_val["value"]
                s_ts = s_val["updated_at"]
                m_ts = m_val["updated_at"]

                # If SQLite value is null/empty but Mongo has a real value, pull it
                is_sqlite_null = s_value is None or s_value == "" or s_value == [] or s_value == {}
                is_mongo_null = m_value is None or m_value == "" or m_value == [] or m_value == {}

                if is_sqlite_null and not is_mongo_null:
                    logger.debug(f"Pulling real value for {key} from MongoDB to SQLite (SQLite was null/empty)")
                    await self.sqlite_conn.execute(
                        "UPDATE state SET value = ?, updated_at = ? WHERE key = ?",
                        (json.dumps(m_value), m_ts, key),
                    )
                elif is_mongo_null and not is_sqlite_null:
                    logger.debug(f"Pushing real value for {key} from SQLite to MongoDB (MongoDB was null/empty)")
                    await self._mongo_update_task(
                        "state",
                        {"_id": key},
                        {"$set": {"value": s_value, "updated_at": s_ts}},
                    )
                elif m_ts > s_ts:
                    # Normal update: Mongo is newer
                    await self.sqlite_conn.execute(
                        "UPDATE state SET value = ?, updated_at = ? WHERE key = ?",
                        (json.dumps(m_value), m_ts, key),
                    )
                elif s_ts > m_ts:
                    # Normal update: SQLite is newer
                    await self._mongo_update_task(
                        "state",
                        {"_id": key},
                        {"$set": {"value": s_value, "updated_at": s_ts}},
                    )

        await self.sqlite_conn.execute("COMMIT")
        logger.info("Database synchronization complete.")

    async def _migrate_from_json(self):
        """Migrates data from bot_state.json if SQLite is empty."""
        json_path = os.path.join(os.path.dirname(config.SQLITE_PATH), "bot_state.json")
        if os.path.exists(json_path):
            cursor = await self.sqlite_conn.execute("SELECT COUNT(*) FROM state")
            count = (await cursor.fetchone())[0]
            if count == 0:
                logger.info("Migrating data from bot_state.json to SQLite...")
                try:
                    with open(json_path) as f:
                        data = json.load(f)
                        now = int(time.time())
                        for key, val in data.items():
                            await self.sqlite_conn.execute(
                                "INSERT INTO state (key, value, updated_at) VALUES (?, ?, ?)",
                                (key, json.dumps(val), now),
                            )
                        await self.sqlite_conn.commit()
                except Exception as e:
                    logger.error(f"Migration failed: {e}")

    async def get(self, key: str, default: Any = None) -> Any:
        if not self.initialized:
            await self.initialize()
        cursor = await self.sqlite_conn.execute("SELECT value FROM state WHERE key = ?", (key,))
        row = await cursor.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except Exception as e:
                logger.error(f"Failed to parse JSON for key {key}: {e}")
                return default
        return default

    async def get_all_with_prefix(self, prefix: str) -> dict:
        if not self.initialized:
            await self.initialize()
        cursor = await self.sqlite_conn.execute("SELECT key, value FROM state WHERE key LIKE ?", (f"{prefix}%",))
        results = {}
        for row in await cursor.fetchall():
            try:
                results[row[0]] = json.loads(row[1])
            except Exception as e:
                logger.error(f"Failed to parse JSON for key {row[0]}: {e}")
        return results

    async def _mongo_update_task(self, collection_name: str, filter_query: dict, update_data: dict, upsert: bool = True):
        """Helper for fire-and-forget MongoDB updates to prevent Future vs Coroutine errors."""
        try:
            if self.mongo_db is not None:
                await self.mongo_db[collection_name].update_one(filter_query, update_data, upsert=upsert)
        except Exception as e:
            logger.error(f"Background MongoDB update failed: {e}")

    async def _mongo_delete_task(self, collection_name: str, filter_query: dict):
        """Helper for fire-and-forget MongoDB deletions."""
        try:
            if self.mongo_db is not None:
                await self.mongo_db[collection_name].delete_one(filter_query)
        except Exception as e:
            logger.error(f"Background MongoDB delete failed: {e}")

    async def set(self, key: str, value: Any):
        if not self.initialized:
            await self.initialize()
        now = int(time.time())
        # Update SQLite
        await self.sqlite_conn.execute(
            "INSERT INTO state (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, json.dumps(value), now),
        )
        await self.sqlite_conn.commit()

        # Update MongoDB (fire and forget)
        if self.mongo_db is not None:
            asyncio.create_task(
                self._mongo_update_task("state", {"_id": key}, {"$set": {"value": value, "updated_at": now}})
            )

    async def increment(self, key: str, amount: int = 1):
        if not self.initialized:
            await self.initialize()
        now = int(time.time())
        # Update SQLite using UPSERT pattern
        await self.sqlite_conn.execute(
            "INSERT INTO state (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = CAST(json_extract(value, '$') AS INTEGER) + ?, updated_at = ?",
            (key, json.dumps(amount), now, amount, now),
        )
        await self.sqlite_conn.commit()

        # Update MongoDB using $inc (fire and forget)
        if self.mongo_db is not None:
            asyncio.create_task(
                self._mongo_update_task("state", {"_id": key}, {"$inc": {"value": amount}, "$set": {"updated_at": now}})
            )

    async def delete(self, key: str):
        if not self.initialized:
            await self.initialize()
        await self.sqlite_conn.execute("DELETE FROM state WHERE key = ?", (key,))
        await self.sqlite_conn.commit()
        if self.mongo_db is not None:
            asyncio.create_task(self._mongo_delete_task("state", {"_id": key}))

    async def get_stats(self) -> dict:
        """Returns statistics about the database."""
        if not self.initialized:
            await self.initialize()
            
        # SQLite Stats
        cursor = await self.sqlite_conn.execute("SELECT COUNT(*) FROM state")
        state_count = (await cursor.fetchone())[0]
        
        cursor = await self.sqlite_conn.execute("SELECT COUNT(*) FROM seen_memes")
        meme_count = (await cursor.fetchone())[0]
        
        sqlite_size = 0
        if os.path.exists(config.SQLITE_PATH):
            sqlite_size = os.path.getsize(config.SQLITE_PATH) / 1024 / 1024 # MB
            
        stats = {
            "sqlite": {
                "state_records": state_count,
                "meme_records": meme_count,
                "size_mb": round(sqlite_size, 2)
            }
        }
        
        # MongoDB Stats
        if self.mongo_db is not None:
            try:
                m_state_count = await self.mongo_db.state.count_documents({})
                stats["mongodb"] = {
                    "state_records": m_state_count,
                    "connected": True
                }
            except:
                stats["mongodb"] = {"connected": False}
        else:
            stats["mongodb"] = {"connected": False}
            
        return stats


db = Database()

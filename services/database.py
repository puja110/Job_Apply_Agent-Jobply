# services/database.py
import asyncpg
import logging
from typing import Optional
from contextlib import asynccontextmanager
from config.settings import settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create database connection pool"""
        try:
            # Use individual settings instead of DATABASE_URL
            connect_kwargs = {
                'host': settings.DB_HOST,
                'port': settings.DB_PORT,
                'user': settings.DB_USER,
                'database': settings.DB_NAME,
                'min_size': 2,
                'max_size': 10
            }
            
            # Only add password if it exists
            if settings.DB_PASSWORD:
                connect_kwargs['password'] = settings.DB_PASSWORD
            
            logger.info(f"Connecting to database: {settings.DB_NAME} as user: {settings.DB_USER}")
            self.pool = await asyncpg.create_pool(**connect_kwargs)
            logger.info("Database pool created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool (context manager)"""
        async with self.pool.acquire() as conn:
            yield conn

    async def fetch(self, query: str, *args):
        """Fetch multiple rows"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """Fetch single value"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute(self, query: str, *args):
        """Execute query without return"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def executemany(self, query: str, args_list):
        """Execute query multiple times"""
        async with self.pool.acquire() as conn:
            await conn.executemany(query, args_list)


# Global database instance
db = Database()
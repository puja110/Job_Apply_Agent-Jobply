"""
Database connection management using asyncpg
"""
import asyncpg
from typing import Optional, List, Any
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    """PostgreSQL database connection wrapper"""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.connection: Optional[asyncpg.Connection] = None
    
    async def connect(self):
        """Establish database connection"""
        if self.pool is None:
            db_password = os.getenv('DB_PASSWORD')
        
        connect_kwargs = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'user': os.getenv('DB_USER', 'pujashrestha'),  # Your macOS username
            'database': os.getenv('DB_NAME', 'jobply'),
            'min_size': 2,
            'max_size': 10
        }
        
        # Only add password if it exists
        if db_password:
            connect_kwargs['password'] = db_password
        
        self.pool = await asyncpg.create_pool(**connect_kwargs)
    
    async def disconnect(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """Execute a query and return all results"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """Execute a query and return a single row"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchval(self, query: str, *args) -> Any:
        """Execute a query and return a single value"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute(self, query: str, *args) -> str:
        """Execute a query without returning results"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def executemany(self, query: str, args: List[tuple]) -> None:
        """Execute a query multiple times with different parameters"""
        async with self.pool.acquire() as conn:
            await conn.executemany(query, args)
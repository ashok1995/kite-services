"""
Database Manager for Market Context Persistent Data
===================================================

This module manages SQLite database operations for storing and retrieving
market data that doesn't change frequently, such as:
- Support and resistance levels
- Pivot points
- Historical calculations
- Market structure data

Features:
- SQLite database with proper schema
- Async operations for FastAPI compatibility
- Data outside code repository (in /data/ directory)
- Automatic table creation and migration
- Efficient caching of expensive calculations
"""

import sqlite3
import aiosqlite
import os
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class PivotLevels:
    """Data class for pivot point levels."""
    symbol: str
    date: str
    pivot_point: float
    support_1: float
    support_2: float
    support_3: float
    resistance_1: float
    resistance_2: float
    resistance_3: float
    horizon: str
    created_at: str

class DatabaseManager:
    """
    Manages SQLite database operations for market context data.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to SQLite database file. Defaults to data/market_context.db
        """
        if db_path is None:
            # Ensure data directory exists outside code repo
            data_dir = os.path.join(os.getcwd(), 'data')
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, 'market_context.db')
        else:
            self.db_path = db_path
        
        print(f"📂 Database path: {self.db_path}")
    
    async def initialize_database(self):
        """Create database tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create pivot levels table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS pivot_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    pivot_point REAL NOT NULL,
                    support_1 REAL NOT NULL,
                    support_2 REAL NOT NULL,
                    support_3 REAL NOT NULL,
                    resistance_1 REAL NOT NULL,
                    resistance_2 REAL NOT NULL,
                    resistance_3 REAL NOT NULL,
                    horizon TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(symbol, date, horizon)
                )
            ''')
            
            # Create market cache table for expensive calculations
            await db.execute('''
                CREATE TABLE IF NOT EXISTS market_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    data TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            # Create index for performance
            await db.execute('CREATE INDEX IF NOT EXISTS idx_pivot_symbol_date ON pivot_levels(symbol, date)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_cache_key ON market_cache(cache_key)')
            
            await db.commit()
            print("✅ Database initialized successfully")

    async def calculate_and_store_pivot_levels(self, symbol: str, high: float, low: float, close: float, horizon: str) -> PivotLevels:
        """
        Calculate and store pivot point levels for a symbol.
        
        Args:
            symbol: Index symbol (e.g., "NIFTY50")
            high: High price
            low: Low price  
            close: Close price
            horizon: Trading horizon
            
        Returns:
            PivotLevels object with calculated levels
        """
        # Calculate pivot point
        pivot_point = (high + low + close) / 3
        
        # Calculate support and resistance levels
        support_1 = (2 * pivot_point) - high
        resistance_1 = (2 * pivot_point) - low
        
        support_2 = pivot_point - (high - low)
        resistance_2 = pivot_point + (high - low)
        
        support_3 = low - 2 * (high - pivot_point)
        resistance_3 = high + 2 * (pivot_point - low)
        
        pivot_data = PivotLevels(
            symbol=symbol,
            date=date.today().isoformat(),
            pivot_point=pivot_point,
            support_1=support_1,
            support_2=support_2,
            support_3=support_3,
            resistance_1=resistance_1,
            resistance_2=resistance_2,
            resistance_3=resistance_3,
            horizon=horizon,
            created_at=datetime.now().isoformat()
        )
        
        # Store in database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO pivot_levels 
                (symbol, date, pivot_point, support_1, support_2, support_3, 
                 resistance_1, resistance_2, resistance_3, horizon, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pivot_data.symbol, pivot_data.date, pivot_data.pivot_point,
                pivot_data.support_1, pivot_data.support_2, pivot_data.support_3,
                pivot_data.resistance_1, pivot_data.resistance_2, pivot_data.resistance_3,
                pivot_data.horizon, pivot_data.created_at
            ))
            await db.commit()
        
        print(f"💾 Stored pivot levels for {symbol} ({horizon}): PP={pivot_point:.2f}")
        return pivot_data

    async def get_pivot_levels(self, symbol: str, horizon: str, date_str: str = None) -> Optional[PivotLevels]:
        """
        Retrieve pivot levels for a symbol and horizon.
        
        Args:
            symbol: Index symbol
            horizon: Trading horizon
            date_str: Date string (defaults to today)
            
        Returns:
            PivotLevels object or None if not found
        """
        if date_str is None:
            date_str = date.today().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT symbol, date, pivot_point, support_1, support_2, support_3,
                       resistance_1, resistance_2, resistance_3, horizon, created_at
                FROM pivot_levels 
                WHERE symbol = ? AND horizon = ? AND date = ?
            ''', (symbol, horizon, date_str)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return PivotLevels(
                        symbol=row[0], date=row[1], pivot_point=row[2],
                        support_1=row[3], support_2=row[4], support_3=row[5],
                        resistance_1=row[6], resistance_2=row[7], resistance_3=row[8],
                        horizon=row[9], created_at=row[10]
                    )
                
                return None

    async def cache_data(self, key: str, data: Dict, expiry_minutes: int = 15):
        """
        Cache expensive calculation results.
        
        Args:
            key: Unique cache key
            data: Data to cache (will be JSON serialized)
            expiry_minutes: Cache expiry in minutes
        """
        from datetime import timedelta
        expires_at = (datetime.now() + timedelta(minutes=expiry_minutes)).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO market_cache (cache_key, data, expires_at, created_at)
                VALUES (?, ?, ?, ?)
            ''', (key, json.dumps(data), expires_at, datetime.now().isoformat()))
            await db.commit()

    async def get_cached_data(self, key: str) -> Optional[Dict]:
        """
        Retrieve cached data if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if expired/not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT data, expires_at FROM market_cache 
                WHERE cache_key = ? AND expires_at > ?
            ''', (key, datetime.now().isoformat())) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    return json.loads(row[0])
                
                return None

    async def cleanup_expired_cache(self):
        """Remove expired cache entries."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                DELETE FROM market_cache WHERE expires_at <= ?
            ''', (datetime.now().isoformat(),))
            await db.commit()

# Global database manager instance
db_manager = DatabaseManager()


import aiosqlite
import json
import logging
from datetime import datetime
from typing import List, Optional
from config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = config.db.PATH):
        self.db_path = db_path

    async def init_database(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_name TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    service TEXT NOT NULL,
                    likes TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    comment TEXT,
                    generated_review TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    date_created DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()

    async def save_review(self, user_id: int, user_name: str, gender: str, service: str, 
                         likes: List[str], recommendation: str, comment: str, generated_review: str):
        likes_json = json.dumps(likes, ensure_ascii=False)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO reviews (user_id, user_name, gender, service, likes, recommendation, comment, generated_review)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, user_name, gender, service, likes_json, recommendation, comment, generated_review))

            await db.commit()

db_manager = DatabaseManager()
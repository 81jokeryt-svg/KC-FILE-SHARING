# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import motor.motor_asyncio
from config import DB_NAME, DB_URI

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
        )
    
    async def add_user(self, id, name):
        user = self.new_user(id, name)
        await self.col.insert_one(user)
    
    async def is_user_exist(self, id):
        user = await self.col.find_one({'id':int(id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count
    
    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({'id': int(user_id)})

    # ─── STORE CHANNELS / STORIES METHODS (ASYNC MOTOR INTEGRATION) ───
    async def get_stories_by_filter(self, query, skip, limit):
        """Asynchronously fetch filtered items from channels_col"""
        cursor = self.db.channels_col.find(query).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_stories_by_filter(self, query):
        """Asynchronously count matching documents from channels_col"""
        return await self.db.channels_col.count_documents(query)

    async def find_single_story(self, query):
        """Asynchronously find one precise document from channels_col"""
        return await self.db.channels_col.find_one(query)


db = Database(DB_URI, DB_NAME)

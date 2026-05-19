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
            verify_time = 0 # 🌟 NEW: Default verification time initialized to 0
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

    # 🌟 NEW: User ka verification time database me permanently update karne ke liye
    async def update_verify_time(self, user_id, verify_time):
        await self.col.update_one(
            {'id': int(user_id)},
            {'$set': {'verify_time': verify_time}},
            upsert=True
        )

    # 🌟 NEW: User ka saved verification time database se fetch karne ke liye
    async def get_verify_time(self, user_id):
        user = await self.col.find_one({'id': int(user_id)})
        return user.get('verify_time', 0) if user else 0


db = Database(DB_URI, DB_NAME)

# dbusers.py

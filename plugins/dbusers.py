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
        # Admin Settings ke liye alag collection
        self.settings = self.db.settings

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            verify_time = 0
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

    # User verification ke liye
    async def update_verify_time(self, user_id, verify_time):
        await self.col.update_one({'id': int(user_id)}, {'$set': {'verify_time': verify_time}}, upsert=True)

    async def get_verify_time(self, user_id):
        user = await self.col.find_one({'id': int(user_id)})
        return user.get('verify_time', 0) if user else 0

    # Dynamic Admin Panel Settings (Get and Update)
    async def get_settings(self):
        settings = await self.settings.find_one({"_id": "bot_config"})
        if not settings:
            default = {
                "_id": "bot_config",
                "verify_mode": True,
                "auto_delete_mode": True,
                "auto_delete_time": 1800, # Default: 30 minutes (in seconds)
                "protect_content": False,
                "shortlink_url": "linkshortify.com",
                "shortlink_api": "9d9199caec2c2e30e0670f1549ffa1a316caa541"
            }
            await self.settings.insert_one(default)
            return default
        return settings

    async def update_setting(self, key, value):
        await self.settings.update_one({"_id": "bot_config"}, {"$set": {key: value}}, upsert=True)

db = Database(DB_URI, DB_NAME)

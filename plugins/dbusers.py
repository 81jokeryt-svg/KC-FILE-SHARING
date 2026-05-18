# Don't Remove Credit @VJ_Bots
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import motor.motor_asyncio
from config import DB_NAME, DB_URI, DEFAULT_SETTINGS, ADMINS

class Database:
    
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users
        # 🌟 NEW: Global settings ke liye ek alag collection ya specific fixed document system
        self.settings_col = self.db.global_settings

    def new_user(self, id, name):
        return dict(
            id = id,
            name = name,
            verify_time = 0, 
            settings = DEFAULT_SETTINGS.copy() 
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

    async def update_verify_time(self, user_id, verify_time):
        await self.col.update_one(
            {'id': int(user_id)},
            {'$set': {'verify_time': verify_time}},
            upsert=True
        )

    async def get_verify_time(self, user_id):
        user = await self.col.find_one({'id': int(user_id)})
        return user.get('verify_time', 0) if user else 0


    # 🌟 🌟 🌟 REFACTORED: GLOBAL ADMIN-CENTRIC SETTINGS LAYER 🌟 🌟 🌟
    # Ab se user_id kuch bhi aaye, settings hamesha ek hi jagah save hogi aur wahin se pure bot par chalegi.

    # 1. Fetch Global Settings (Jo pure bot ke sabhi users par lagengi)
    async def get_user_settings(self, user_id=None):
        # Hum user_id ko bypass kar rahe hain taaki agar koi plugin purane tareeke se bhi call kare, toh galti se user ki personal setting na khule.
        settings_doc = await self.settings_col.find_one({'id': 'GLOBAL_BOT_SETTINGS'})
        
        if settings_doc and 'settings' in settings_doc:
            current_settings = DEFAULT_SETTINGS.copy()
            current_settings.update(settings_doc['settings'])
            return current_settings
        
        # Agar pehli baar chal raha hai aur document nahi mila toh default settings set kar dega database me
        await self.settings_col.update_one(
            {'id': 'GLOBAL_BOT_SETTINGS'},
            {'$set': {'settings': DEFAULT_SETTINGS.copy()}},
            upsert=True
        )
        return DEFAULT_SETTINGS.copy()

    # 2. Update Settings Key (Sirf Admin isko trigger karega via buttons)
    async def update_user_setting(self, user_id, key, value):
        # Yahan bhi user_id ignore hokar direct Central Database record update hoga
        await self.settings_col.update_one(
            {'id': 'GLOBAL_BOT_SETTINGS'},
            {'$set': {f'settings.{key}': value}},
            upsert=True
        )


db = Database(DB_URI, DB_NAME)

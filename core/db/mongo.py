from pymongo import AsyncMongoClient
from core.config import settings
import os
from datetime import datetime
from core.utils.utils import get_user_id

class DB:

    _client = None

    @property
    def client(self):
        if DB._client is None:    
            DB._client = AsyncMongoClient(settings.MONGO_URI)
        return DB._client
    
    def get_collection(self, name: str):
        db = self.client.get_database(settings.DB_NAME)
        collection = db.get_collection(name)
        return collection
    
    async def api_logger(self, data):
        events = self.get_collection('api_events')
        event = {
            "payload": data,
            "timestamp": datetime.now()
        }
        await events.insert_one(event)

    async def logger(self, user, type, details):
        events = self.get_collection('events')
        event = {
                "type": type,
                "user_id": get_user_id(user),
                "timestamp": datetime.now(),
                **details
            }
        
        await events.insert_one(event)

    async def add_contribution(self, user, amount, source, **kwargs):
        contributions = self.get_collection('contributions')
        await contributions.update_one({'user_id': get_user_id(user)}, {"$inc": {"contribution": amount}})
        await self.logger(user, type='contribution_added', details={'source': source, 'amount': amount, **kwargs})

    async def get_user_rsn(self, rsn: str):
        contributions = self.get_collection('contributions')
        user = await contributions.find_one({'rsn': rsn})
        return user
    
    async def get_events(self, user: dict = {}, filter: dict = {}, limit: int = None):
        events_collection = self.get_collection('events')
        query = {}
        if user:
            query['user_id'] = get_user_id(user)
        if filter:
            query = {**query, **filter}
        events = await events_collection.find(filter).to_list()
        if limit:
            events = events.limit(limit)
        return events
    
    async def add_user(self, user):
        contributions = self.get_collection('contributions')
        if await contributions.find_one({'user_id': user}):
            return
        await contributions.insert_one({
            'user_id': user,
            'contribution': 0,
            'rsn': ''
        })
        await self.logger({'user_id': user}, type='create new user', details={'source': 'bot'})

    async def get_user(self, user):
        contributions = self.get_collection('contributions')
        user = await contributions.find_one({'user_id': get_user_id(user)})
        return user

    async def sync_rsn(self, user, rsn):
        contributions = self.get_collection('contributions')
        await contributions.update_one({'user_id': get_user_id(user)}, {'$set': {'rsn': rsn}})
        await self.logger(user, type='sync_rsn', details={'source': 'bot', 'rsn': rsn})
        
    async def get_logs(self, user, max=10):
        logs_collection = self.get_collection('events')
        api_logs_collection = self.get_collection('api_events')
        event_logs = await logs_collection.find({'user_id': get_user_id(user)}).sort({'timestamp': -1})
        api_logs = await api_logs_collection.find({'user_id': get_user_id(user)}).sort({'timestamp': -1})
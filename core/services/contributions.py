from core.db.mongo import DB
from core.config import MESSAGE_CONTRIBUTION, MESSAGE_CONTRIBUTION_LIMIT

async def add_message_contribution(data):
    db = DB()
    await db.api_logger(data)
    if data['clan_name'] != "Eternal Gems":
        return
    
    if data['rank'] == 'Guest':
        return
    
    sender = data['sender']
    # clan notification
    if sender == "Eternal Gems":
        return

    user = await db.get_user_rsn(sender)
    if user:
        message_contributions = await db.get_events(user, {'type': 'message'})
        if len(message_contributions) < MESSAGE_CONTRIBUTION_LIMIT:
            await db.add_contribution(user, MESSAGE_CONTRIBUTION, 'message')
        await db.logger(user, type='message', details={'message': data['message']})
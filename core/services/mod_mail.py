import discord
from core.db.mongo import DB
from core.utils.utils import get_user_id

async def create_modmail_ticket(channel_id, user, guild_id):
    ### TODO check that a ticket doesn't already exist with user
    db = DB()
    mod_mail = db.get_collection('modmail')
    user = get_user_id(user)
    await mod_mail.insert_one({
            'user': user,
            'staff_channel': channel_id,
            'DM': True,
            'status': 'open',
            'guild': guild_id,
            'user_channel': 0
        })

async def get_ticket(channel_id, guild_id):
    db = DB()
    mod_mail = db.get_collection('modmail')
    ticket = await mod_mail.find_one({'staff_channel': channel_id, 'status': 'open', 'guild': guild_id})
    return ticket

async def staff_message_ticket(channel):
    guild = channel.guild.id
    channel = channel.id
    if not channel:
        return False
    ticket = await get_ticket(channel, guild)
    if not ticket:
        return False
    return True

async def stop_dm(ticket, user_channel):
    db = DB()
    mod_mail = db.get_collection('modmail')
    await mod_mail.update_one({'user': ticket['user'], 'status': 'open', 'guild': ticket['guild']},
                              {"$set": {"DM": False, "user_channel": user_channel}})
    ticket = await get_ticket(ticket['staff_channel'], ticket['guild'])
    return ticket

async def send_staff_message(ctx, message):
    ticket = await get_ticket(ctx.channel.id, ctx.channel.guild.id)
    user_id = ticket['user']
    user_channel = None

    author = ctx.author

    embed = discord.Embed(description=message)
    embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)

    if ticket['DM']:
        # try to send DM
        user = ctx.bot.get_user(user_id)
        try:
            await user.send(embed=embed)
            return
        except discord.HTTPException or discord.Forbidden:
            category = ctx.channel.category
            ### TODO check that user is still in server
            user_channel = await category.create_text_channel(f'ModMail_{user.name}')
            ### TODO handle permissions
            ### TODO mention user
            user = ctx.guild.get_user(user_id)
            await user_channel.send(f'{user.mention}')
            ticket = await stop_dm(ticket, user_channel.id)
    if not user_channel:    
        user_channel = ticket['user_channel']
        user_channel = ctx.guild.get_channel(user_channel)
    await user_channel.send(embed=embed)

async def user_message_ticket(user_id):
    db = DB()
    mod_mail = db.get_collection('modmail')
    ticket = await mod_mail.find_one({'user': user_id, 'status': 'open'})
    return ticket

async def send_user_message(message, bot):
    ticket = await user_message_ticket(message.author.id)
    staff_channel = ticket['staff_channel']
    guild = ticket['guild']
    guild = bot.get_guild(guild)
    channel = guild.get_channel(staff_channel)
    await channel.send(message.content)

async def close_ticket(interaction, bot):
    db = DB()
    ticket = await get_ticket(interaction.channel.id, interaction.guild_id)
    guild = interaction.guild
    staff_channel = ticket['staff_channel']
    channel = guild.get_channel(staff_channel)
    # no need to check if channel exists since function call can only happen if command triggered in the channel
    await channel.delete()
    if not ticket['DM']:
        user_channel = ticket['user_channel']
        channel = guild.get_channel(user_channel)
        # in case channel was already deleted
        if channel:
            await channel.delete()
    else:
        user = bot.get_user(ticket['user'])
        try:
            await user.send('Ticket has been closed')
        except discord.HTTPException or discord.Forbidden:
            # cannot send message to user
            pass
    mod_mail = db.get_collection('modmail')
    await mod_mail.update_one({'user': ticket['user'], 'status': 'open', 'guild': interaction.guild.id},
                              {"$set": {"status": 'closed'}})
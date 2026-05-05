import discord
from core.config import ALLOWED_ROLE_ID

def get_user_id(user):
    # user given by functions sometimes is User type or directly user id
    # function returns user_id
    if type(user) is discord.Member:
        return user.id
    try:
        return user['user_id']
    except:
        return user
    

def is_staff():
    def predicate(interaction: discord.Interaction) -> bool:
        if not any(role.id in ALLOWED_ROLE_ID for role in interaction.user.roles):
            return False
        return True
    return discord.app_commands.check(predicate)

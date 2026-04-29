import discord


def get_user_id(user):
    # user given by functions sometimes is User type or directly user id
    # function returns user_id
    if type(user) is discord.Member:
        return user.id
    try:
        return user['user_id']
    except:
        return user
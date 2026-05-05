from core.db.mongo import DB

def get_motus(guild_id):
    db = DB()
    motus = db.get_collection('motus')
    result = motus.find_one({'guild': guild_id})
    return result


def add_word(interaction, word):
    motus = get_motus(interaction.guild_id)
    if not motus:
        return
    
    
    if len(temp) != 2:
        await ctx.send("```Tu ne dois donner que des lettres```")
        return
    for letter in word:
        if letter not in al:
            await ctx.send("```Tu ne dois donner que des lettres```")
            return
    if not dico.check(word):
        await ctx.send("```Ce mot n'existe pas ou n'est pas dans le dictionnaire```")
        return
    if 'word' in Motus[name]['motus'].keys():
        await ctx.send("```Il y a encore un mot a trouver```")
        return
    if not 'winner' in Motus[name]['motus'].keys() or (Motus[name]['motus']['winner'] != ctx.author.id and Motus[name]['motus']['winner'] != -1):
        await ctx.send("```Tu n'es pas le dernier vainqueur```")
        return
    if len(word) < 2 or len(word) > 17:
        await ctx.send("```Le mot doit avoir une longueur comprise entre 5 lettres et 17 lettres```")
        return
    
    Motus[name]['motus']['word'] = word
    Motus[name]['motus']['author'] = ctx.author.id
    Motus[name]['motus']['players'] = {}
    Motus[name]['motus']['counter'] = 0
    Motus[name]['motus']['status'] = []
    save_motus(name)
    for guild in await get_guilds():
        if guild.name == name:
            channel = guild.get_channel(Motus[name]['channels'][0])
            await channel.send(f"```Le mot actuel contient {len(Motus[channel.guild.name]['motus']['word'])} lettres et commence par un {Motus[channel.guild.name]['motus']['word'][0]}```")
    await ctx.send("```Ton mot est enregistré```")
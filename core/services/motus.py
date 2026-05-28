from core.db.mongo import DB
from core.config import dico

async def get_motus(guild_id):
    db = DB()
    motus = db.get_collection('motus')
    result = await motus.find_one({'guild': guild_id})
    return result

async def get_players(guild_id):
    db = DB()
    players_col = db.get_collection('players')
    result = await players_col.find({'guild': guild_id})
    return result

async def update_motus(game, interaction, word):
    db = DB()
    motus = db.get_collection('motus')
    await motus.update_one({'guild': game['guild']},
                     {'$set': {'word': word,
                               'author': interaction.user.id,
                               'players': {},
                               'counter': 0,
                               'status': [0]*len(word)}})

def check_word(given_word,word):#given_word=word word=motus['word']
    state = []#0=:x: 1=:large_orange_diamond: 2= the corresponding letter 3= dash
    word_list = list(word)
    for i in range(len(given_word)):
        state.append(0)
    for i in range(len(given_word)):
        if word[i] == '-':
            word_list[i] = '!'
            state[i] = 3
        elif given_word[i] == word[i]:
            word_list[i] = '!'
            state[i] = 2
    for i in range(len(given_word)):
        if given_word[i] in word_list and state[i] < 2:
            index = word_list.index(given_word[i])
            word_list[index] = '!'
            state[i] = 1
        elif state[i] < 2:
            state[i] = 0
    return state

def convert(state,word):
    good = 0
    text = ''
    for i in range(len(state)):
        if state[i] == 0:
            text += ':x:'
        if state[i] == 1:
            text += ':large_orange_diamond:'
        if state[i] == 2:
            good += 1
            text += ':regional_indicator_' + word[i].lower() + ':'
        if state[i] == 3:
            good += 1
            text += ':heavy_minus_sign:'
    return [text, good]

async def updateStatus(state, motus):
    word = motus['word']
    status = motus['status']
    count = 0
    for i in range(len(word)):
        if status[i] == 0:
            if state[i] == 2:
                status[i] = 2
                count += 1
            if state[i] == 3:
                status[i] = 3
    db = DB()
    motus_col = db.get_collection('motus')
    await motus_col.update_one({'guild': motus['guild']},
                     {'$set': {'status': status}})
    return count

async def send_points(message, motus):
    guild = message.channel.guild
    text = ""
    list_players = [[player, points] for player, points in motus['players'].items()]
    list_players.sort(key = lambda x: x[1])
    list_players.append([motus['author'], motus['counter']])
    for player in list_players:
        if guild.get_member(int(player[0])) is not None:
            text += f"{guild.get_member(int(player[0])).display_name} gains {player[1]} point{'s' if player[1] > 1 else ''}\n"
    await message.channel.send(f"```{text}```")

async def add_points(guild, player, points):
    db = DB()
    players = db.get_collection('players')
    await players.update_one({'guild': guild, 'user_id': player}, {'$inc': {'total': points}}, upsert=True)

async def save_points(motus):
    for player, points in motus['players'].items():
        await add_points(motus['guild'], player, points)
    author = motus['author']
    await add_points(motus['guild'], author, motus['counter'])

async def reset_motus(motus, author):
    db = DB()
    motus_col = db.get_collection('motus')
    await motus_col.update_one({'guild': motus['guild']},
                     {'$set': {'word': None, 'winner': author}})

async def add_word(interaction, word):
    motus = await get_motus(interaction.guild_id)
    if not motus:
        return
    
    if interaction.channel_id != motus['channel_id']:
        await interaction.response.send_message("Motus isn't activated in this channel")
        return

    if motus['winner'] != interaction.user.id and motus['winner'] != -1:
        await interaction.response.send_message("You are not the last winner")
        return

    if not word.isalpha():
        await interaction.response.send_message(
            "You must give only letters"
        )
        return

    if not dico.check(word):
        await interaction.response.send_message("This word doesn't exist or isn't in the dictionnary")
        return
    if motus['word']:
        await interaction.response.send_message("There is still a word to be found")
        return
    
    if len(word) < 2 or len(word) > 17:
        await interaction.response.send_message("The word must have length between 5 and 17 letters")
        return
    
    await update_motus(motus, interaction, word)
    channel = interaction.channel
    await channel.send(f"The word is {len(word)} long and start by a {word[0]}")
    ### TODO make it not visible to others
    await interaction.response.send_message("You word has been registered")


async def handle_motus_guess(motus, message):
    word = message.content
    if '-' in word:
        temp = ''.join(word.split('-'))
    else:
        temp = word
    if not temp.isupper():
        return
    
    if not word.isalpha():
        await message.delete(delay=20)
        await message.channel.send("You must only give letters", delete_after=20)
        return
    
    if not motus['word']:
        await message.delete(delay=20)
        await message.channel.send("There is no word to be found for now", delete_after=20)
        return
    
    author = message.author.id

    db = DB()
    await db.logger(author, 'motus', {'word': word})

    if author == motus['author']:
        await message.delete(delay=20)
        await message.channel.send("The word to find is yours, you can't guess it", delete_after=20)
        return

    if len(word) != len(motus['word']):
        await message.delete(delay=20)
        await message.channel.send(f"Your word is {len(word)} long, the word to find is {len(motus['word'])} long and starts with a {motus['word'][0]}", delete_after=20)
        return

    if word[0] != motus['word'][0]:
        await message.delete(delay=20)
        await message.channel.send(f"You must give a word starting with {motus['word'][0]}", delete_after=20)
        return
    
    if not dico.check(word):
        await message.delete(delay=20)
        await message.channel.send("This word doesn't exist in the dictionnary", delete_after=20)
        return

    motus['counter'] += 1
    print(motus['counter'])
    word_state = check_word(word, motus['word'])
    count = await updateStatus(word_state, motus)
    if str(author) in motus['players'].keys():
        motus['players'][str(author)] += count
    else:
        motus['players'][str(author)] = count
    motus_col = db.get_collection('motus')
    await motus_col.update_one({'guild': motus['guild']},
                           {'$set': {'players': motus['players']}})
    temp = convert(word_state, word)
    good = temp[1]
    text = temp[0]
    await message.channel.send(text)

    if good != len(motus['word']):
        return

    if motus['counter'] == 1:
        if str(author) in motus['players'].keys():
            motus['players'][str(author)] += 3*(int(len(motus['word'])/2))
        else:
            motus['players'][str(author)] = 3*(int(len(motus['word'])/2))
    else:
        if str(author) in motus['players'].keys():
            motus['players'][str(author)] += int(len(motus['word'])/2)
        else:
            motus['players'][str(author)] = int(len(motus['word'])/2)
    await message.channel.send(f"Congrats, {message.author.mention}!\n The word has been found in {motus['counter']} tr{'ies' if motus['counter' > 1] else 'y'}")
    await send_points(message, motus)
    await message.channel.send(f"{message.author.mention} You can now give the next work to be found using /giveword")
    await save_points(motus)
    await reset_motus(motus, author)

async def init_motus(interaction):
    db = DB()
    motus = db.get_collection('motus')
    if await motus.find_one({'guild': interaction.guild_id}):
        await interaction.response.send_message("Motus has already been initialized in this server")
        return
    await motus.insert_one({
            'guild': interaction.guild_id,
            'channel_id': interaction.channel_id,
            'word': None,
            'winner': -1,
        })
    await interaction.response.send_message("Motus has been properly initialized")
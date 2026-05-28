import discord
from discord.ext import commands
from core.config import GUILD_ID
from core.services.motus import add_word, get_motus, handle_motus_guess, init_motus


class Motus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="giveword", description="Give the next word to be guessed")
    @discord.app_commands.describe(word="Next word to be guessed")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def giveword(self, interaction: discord.Interaction, word: str):
        await add_word(interaction, word)

    @discord.app_commands.command(name="init_motus", description="initialize Motus in the channel")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def initialization(self, interaction: discord.Interaction):
        await init_motus(interaction)

    @commands.Cog.listener('on_message')
    async def handle_message(self, message):
        try:
            id = message.guild.id
        except:
            id = 0
        motus = await get_motus(id)
        if not motus:
            return
        
        if message.channel.id != motus['channel_id']:
            return

        await handle_motus_guess(motus, message)

async def setup(bot):
    await bot.add_cog(Motus(bot))
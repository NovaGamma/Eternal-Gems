import discord
from discord.ext import commands
from core.config import GUILD_ID

class Motus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="giveword", description="Give the next word to be guessed")
    @discord.app_commands.describe(word="Next word to be guessed")
    #@is_staff()
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def giveword(self, interaction: discord.Interaction, word: str):
        add_word(interaction, word)


async def setup(bot):
    await bot.add_cog(Motus(bot))
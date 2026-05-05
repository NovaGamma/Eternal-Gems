import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="$",
    intents=intents
)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(e)

@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync(guild=ctx.guild)
    await ctx.send(f"Synced {len(synced)} guild commands.")
    for command in synced:
        print(command.name)

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: Exception):
    print("SLASH COMMAND ERROR:", repr(error))

    try:
        if interaction.response.is_done():
            await interaction.followup.send(
                f"Error: {error}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"Error: {error}",
                ephemeral=True
            )
    except Exception as e:
        print("Failed to send error message:", e)

@bot.event
async def on_command_error(ctx, error):
    print("PREFIX COMMAND ERROR:", repr(error))

    # Unwrap original error if it's a CommandInvokeError
    if hasattr(error, "original"):
        error = error.original

    try:
        await ctx.send(f"Error: {error}")
    except Exception as e:
        print("Failed to send error message:", e)

async def load_cogs():
    for filename in os.listdir("./apps/bot/cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"apps.bot.cogs.{filename[:-3]}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

import asyncio
asyncio.run(main())
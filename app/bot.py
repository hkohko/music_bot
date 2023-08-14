import discord
import os
from asyncio import run
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=";", intents=intents)

bot.remove_command("help")


@bot.event
async def on_ready():
    print(f"{bot.user} is online.")


@bot.command()
@commands.is_owner()
async def admin_key__load(ctx, extension):
    await bot.load_extension(f"cogs.{extension}")
    await ctx.send(f"Loaded {extension} command(s)")


@bot.command()
@commands.is_owner()
async def admin_key__unload(ctx, extension):
    await bot.unload_extension(f"cogs.{extension}")
    await ctx.send(f"Unloaded {extension} command(s)")


async def load():
    for filename in os.listdir("./app/cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


run(load())
load_dotenv()
bot.run(os.getenv("BOT_TOKEN"))

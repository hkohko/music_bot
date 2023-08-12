import discord
from discord.ext import commands


class help_cog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.help_message = """
        Commands:
        /help
        /p <song name> - Finds song on YouTube and plays it.
        /q - display current queue.
        /skip
        /clear - Stops music + clear the queue.
        /leave
        /pause
        /resume
        """
        self.text_channel_text = []

    # @commands.Cog.listener()
    # async def on_ready(self):
    #     for guild in self.bot.guilds:
    #         for channel in guild.text_channels:
    #             self.text_channel_text.append(channel)

    #     await self.send_to_all(self.help_message)

    # async def send_to_all(self, msg):
    #     for text_channel in self.text_channel_text:
    #         await text_channel.send(msg)

    @commands.command(name="help", help="Displays bot command.")
    async def help(self, ctx):
        await ctx.send(self.help_message)


async def setup(bot):
    await bot.add_cog(help_cog(bot))

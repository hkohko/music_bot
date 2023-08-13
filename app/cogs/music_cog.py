import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from pprint import pprint

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {"format": "bestaudio/best", "noplaylist": "True", "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "opus"
        }]}
        self.FFMPEG_OPTIONS = {"before_options": "-reconnect 1 -reconnect_streamed 1"}

        self.vc = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("music_cog online.")

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info_dict = ydl.extract_info("ytsearch:%s" % item, download=False)
                info = info_dict["entries"][-1]
            except Exception:
                return False
        return {"source": info["url"], "title": info["title"]}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]["source"]
            self.music_queue.pop(0)
            self.vc.play(
                discord.FFmpegPCMAudio(m_url),
                after=lambda e: self.play_next(),
            )
        else:
            self.is_playing = False

    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]["source"]

            if self.vc is None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                if self.vc is None:
                    await ctx.send("Can't connect to voice channel")
                    return
                else:
                    await self.vc.move_to(self.music_queue[0][1])

                self.music_queue.pop(0)

                self.vc.play(
                    discord.FFmpegPCMAudio(m_url),
                    after=lambda e: self.play_next()
                )
        else:
            self.is_playing = False

    @commands.command(
        name="play", aliases=["p", "playing"], help="Play the song from Youtube"
    )
    async def play(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel
        print(voice_channel)
        if voice_channel is None:
            await ctx.send("Connect to a voice channel")
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            if not song:
                await ctx.send(
                    "Cannot download song because of incorrect format, try another search."
                )
            else:
                await ctx.send("Added to the queue")
                self.music_queue.append([song, voice_channel])
                if self.is_playing is False:
                    await self.play_music(ctx)
                    

    @commands.command(name="pause", help="Pause currently playing song.")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    @commands.command(
        name="resume", aliases=["r"], help="Resumes currently paused song."
    )
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    @commands.command(name="skip", aliases=["s"], help="Skips a song.")
    async def skip(self, ctx, *args):
        if self.vc is not None and self.vc:
            self.vc.stop()
            await self.play_music(ctx)

    @commands.command(name="queue", aliases=["q"], help="Display current queue.")
    async def queue(self, ctx):
        retval = ""

        for i in range(0, len(self.music_queue)):
            if i > 4:
                break
            retval += self.music_queue[i][0]["title"] + "\n"

        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send("Queue is empty.")

    @commands.command(
        name="clear", aliases=["c"], help="Stops the song and clears queue"
    )
    async def clear(self, ctx, *args):
        if self.vc is not None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("Queue cleared.")

    @commands.command(
        name="leave", aliases=["disconnect", "l", "d"], help="Disconnect the bot"
    )
    async def leave(self, ctx):
        self.is_playing = False
        self.is_paused = True
        await self.vc.disconnect()


async def setup(bot):
    await bot.add_cog(music_cog(bot))

import discord
from discord.ext import commands
from yt_dlp import YoutubeDL


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.embed = discord.Embed(color=discord.Color.dark_red())
        self.bot = bot

        self.is_playing = False
        self.is_paused = False
        self.repeat = False

        self.music_queue = []
        self.YDL_OPTIONS = {"format": "bestaudio/best", "noplaylist": "True"}
        self.FFMPEG_OPTIONS = {"before_options": "-reconnect 1 -reconnect_streamed 1"}

        self.vc = None

    def get_repeat_status(self) -> str:
        if self.repeat:
            return " (repeat)"
        else:
            return ""

    def get_now_playing(self):
        return (
            self.music_queue[0][0]["title"].strip(),
            self.music_queue[0][0]["duration"].strip(),
        )

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
        return {
            "source": info["url"],
            "title": info["title"],
            "duration": info["duration_string"],
        }

    def play_next(self):
        self.is_playing = True
        if self.repeat is False:
            try:
                self.music_queue.pop(0)
            except IndexError:
                self.is_playing = False
                return
        if len(self.music_queue) == 0:
            self.is_playing = False
            return
        m_url = self.music_queue[0][0]["source"]
        self.vc.play(
            discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
            after=lambda _: self.play_next()  # idk the behaviour of anon func
        )
            

    async def play_music(self, ctx):
        if len(self.music_queue) == 0:
            self.is_playing = False
            return
        self.is_playing = True
        m_url = self.music_queue[0][0]["source"]
        if self.vc is None or self.vc.is_connected():
            try:
                self.vc = await self.music_queue[0][1].connect()
            except discord.errors.ClientException:
                if self.vc is None:
                    await ctx.send("Can't connect to voice channel")
                    return
                await self.vc.move_to(self.music_queue[0][1])
            finally:
                if self.repeat is False:
                    title, duration = self.get_now_playing()
                    self.embed.add_field(
                        name=f"**Now Playing{self.get_repeat_status()}**",
                        value=f"```{title} | {duration}```",
                    )
                    await ctx.send(embed=self.embed)
                    self.embed.clear_fields()
                self.vc.play(
                    discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                    after=lambda _: self.play_next()
                )
            

    @commands.command(
        name="play", aliases=["p", "playing"], help="Play the song from Youtube"
    )
    async def play(self, ctx, *args):
        query = " ".join(args)
        try:
            voice_channel = ctx.author.voice.channel
            print(voice_channel)
            print(self.music_queue)
            in_vc = True
        except AttributeError:
            in_vc = False
            await ctx.send("Connect to a voice channel")
        if self.is_paused:
            self.vc.resume()
        elif in_vc:
            song = self.search_yt(query)
            if not song:
                await ctx.send(
                    "Cannot download song because of incorrect format, try another search."
                )
            else:
                await ctx.send("Added to the queue")
                self.music_queue.append([song, voice_channel])
                if self.is_playing is False:  # will only connect and play if its False
                    await self.play_music(ctx)
        else:
            pass

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

    @commands.command(name="repeat", help="Repeats currently playing song.")
    async def repeat_track(self, ctx):
        if self.repeat is True:
            self.repeat = False
            await ctx.send(f"Tracks now plays normally.")
            return
        if self.repeat is False:
            title, _ = self.get_now_playing()
            self.repeat = True
            await ctx.send(f"`{title}` is on repeat")
            return

    @commands.command(
        name="resume", aliases=["r"], help="Resumes currently paused song."
    )
    async def resume(self, ctx, *args):
        if self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    @commands.command(name="skip", aliases=["s"], help="Skips a song.")
    async def skip(self, ctx):
        if self.vc is not None and self.vc:
            self.vc.stop()
            if self.repeat:
                self.music_queue.pop(0)
            self.play_next(ctx)  # never change this line, it breaks everything

    @commands.command(name="queue", aliases=["q"], help="Display current queue.")
    async def queue(self, ctx):
        retval = []
        newline = "\n"
        for index, i in enumerate(range(0, len(self.music_queue))):
            retval.append(
                f"{index + 1}. {self.music_queue[i][0]['title']} | {self.music_queue[i][0]['duration']}"
            )

        if retval:
            self.embed.add_field(
                name=f"**Queue{self.get_repeat_status()}**",
                value=f"```{newline.join(retval)}```",
            )
            await ctx.send(embed=self.embed)
            self.embed.clear_fields()
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
        name="leave",
        aliases=["disconnect", "l", "d", "reset"],
        help="Disconnect the bot",
    )
    async def leave(self, ctx):
        self.is_playing = False
        self.is_paused = False
        await self.vc.disconnect()
        self.music_queue.clear()
        self.repeat = False
        self.vc = None  # can only join one channel currently

    @commands.command(name="np", aliases=["nowplaying"], help="Shows now playing song.")
    async def nowplaying(self, ctx):
        if len(self.music_queue) > 0:
            title, duration = self.get_now_playing()
            self.embed.add_field(
                name=f"**Now Playing{self.get_repeat_status()}**",
                value=f"```{title} | {duration}```",
            )
            await ctx.send(embed=self.embed)
            self.embed.clear_fields()
        else:
            await ctx.send("No music is playing.")


async def setup(bot):
    await bot.add_cog(music_cog(bot))

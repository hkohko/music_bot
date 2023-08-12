import discord
from discord.ext import commands
from youtube_dl import YoutubeDL


class music_cog(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {"format": "bestaudio", "noplaylist": "True"}
        self.FFMPEG_OPTIONS = {"before_options": "-reconnect 1 -reconnected_streamed 1"}

        self.vc = None

    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info_dict = ydl.extract_info("ytsearch:%s" % item, download=False)
                info = info_dict["entries"][0]
            except Exception:
                return False
        return {"source": info["formats"][0]["url"], "title": info["title"]}

    def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True
            m_url = self.music_queue[0][0]["source"]
            self.music_queue.pop(0)
            self.vc.play(
                discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
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
                    **self.FFMPEG_OPTIONS,
                    after=lambda e: self.play_next()
                )
        else:
            self.is_playing = False
    @commands.command(name="play", aliases=["p", "playing"], help="Play the song from Youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)

        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("Connect to a voice channel")
        elif self.is_paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            if isinstance(song, True):
                await ctx.send("Cannot download song because of incorrect format, try another search")
            else:
                await ctx.send("Added to the queue")
                self.music_queue.append([song, voice_channel])
                if self.is_playing is False:
                    await self.play_music(ctx)
import uuid
from datetime import datetime

import discord
import yt_dlp as youtube_dl
from aiogtts import aiogTTS

tts = aiogTTS()

class TimeGenerator:
    def __repr__(self) -> str:
        now = datetime.now()
        return f"{now:%H 點 %M 分}"

mktime = TimeGenerator()

class LofiChannel:
    """The lofi radio channel."""

    __slots__ = (
        'url',
        'bot'
    )
    url: str
    bot: discord.Bot

    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
        ydl_opts = {'format': 'bestaudio', 'noplaylist':'True', 'quiet': 'True'}

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                'ytsearch:https://www.youtube.com/watch?v=jfKfPfyJRdk',
                download=False
            )
            self.url = info['entries'][0]['formats'][0]['url']

    @property
    def interval(self) -> int:
        return 60 * 5

    def _new(self) -> str:
        fn = ".store/" + str(uuid.uuid4()) + ".mp3"
        return fn

    async def process(self):
        while True:
            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            obj = await discord.FFmpegOpusAudio.from_probe(
                self.url,
                **FFMPEG_OPTIONS
            )
            yield obj

            fn = self._new()
            await tts.save(
                f"{mktime}",
                fn,
                'zh-TW'
            )
            yield [
                fn
            ]

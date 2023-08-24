import json

import discord
import yt_dlp as youtube_dl


class WorkChannel:
    """The work / study radio channel."""

    __slots__ = (
        'url',
        'bot',
    )
    url: str
    bot: discord.Bot

    def __init__(self, bot: discord.Bot):
        self.bot = bot
    
        ydl_opts = {
            'format': 'm4a/bestaudio/best',
            'noplaylist': 'True',
            'dump_single_json': 'True',
            'extract_flat': 'True',
            'quiet': 'True'
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                'https://www.youtube.com/watch?v=8_xP8WBqy7k',
                download=False,
            )
            with open("data.json", "w") as file:
                file.write(json.dumps(info, indent=4))

            self.url = info['url']

    @property
    def interval(self) -> None:
        return None

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

            yield []

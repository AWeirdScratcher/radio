import json
import uuid

import discord
import g4f
import yt_dlp as youtube_dl
from aiogtts import aiogTTS
from youtubesearchpython import VideosSearch

tts = aiogTTS()

class WTFRadioChannel:
    """The WTF radio channel."""

    __slots__ = (
        'url',
        'bot',
        'messages',
        'suggestions'
    )
    url: str
    bot: discord.Bot
    messages: list[dict[str, str]]
    suggestions: list[str]

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.messages = [
            {
                "role": "system",
                "content": """You're a radio broadcaster bot. You play songs. When you receive CHOOSE_SONG, you'll need to choose a pop song to play for your audience. But your response MUST ONLY INCLUDE THE SONG NAME, JUST THE NAME.
When you receive SONG_END, describe why the song was good briefly, < 30 words, respond in Traditional Chinese (Taiwan).
Choose any genre, never describe or ask the user anything besides SONG_END.
DO NOT REPEAT SONGS."""
            },
        ]
        self.suggestions = []

    def suggest(self, song: str):
        self.suggestions.append(song)

    def get_url(self, query: str):
        searcher = VideosSearch(query, limit = 2)
        vid_id = searcher.result()['result'][0]['id']
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'dump_single_json': True,
            'extract_flat': True,
            'quiet': True
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f"https://youtube.com/watch?v={vid_id}",
                download=False,
            )

            with open("data.json", "w") as file:
                file.write(json.dumps(info, indent=4))

            self.url = info['url']

    def _new(self) -> str:
        return f".store/{uuid.uuid4()}.mp3"

    @property
    def interval(self) -> None:
        return None

    async def process(self):
        while True:
            was_a_suggestion = False

            if not self.suggestions:
                self.messages.append({
                    "role": "system",
                    "content": "CHOOSE_SONG; taiwan pop songs"
                })
                response = g4f.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    provider=g4f.Provider.DeepAi,
                    messages=self.messages
                )
                self.messages.append({
                    "role": "assistant",
                    "content": response
                })
            else:
                was_a_suggestion = True
                response = self.suggestions[0]

            self.get_url(response + " lyrics")

            fn = self._new()

            if not self.suggestions:
                await tts.save(
                    "下一首：" + response,
                    fn,
                    "zh-TW"
                )
            else:
                await tts.save(
                    "下一首：" + response + "\n由聽眾推薦！",
                    fn,
                    "zh-TW"
                )

            yield [fn]

            FFMPEG_OPTIONS = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            obj = await discord.FFmpegOpusAudio.from_probe(
                self.url,
                **FFMPEG_OPTIONS
            )

            yield obj

            if not was_a_suggestion:
                self.messages.append({
                    "role": "system",
                    "content": "SONG_END; respond in traditional chinese < 30 words"
                })

                response = g4f.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    provider=g4f.Provider.DeepAi,
                    messages=self.messages
                )
                self.messages.append({
                    "role": "assistant",
                    "content": response
                })
            else:
                response = "感謝聽眾建議的歌曲！"
                del self.suggestions[0]

            fn = self._new()
            await tts.save(
                response,
                fn,
                "zh-TW"
            )

            yield [
                fn
            ]

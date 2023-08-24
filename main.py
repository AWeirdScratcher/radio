# required db:
# key: vc (default {})

import asyncio
import os
import uuid
from threading import Thread

import discord
import fastapi
import uvicorn
from aiogtts import aiogTTS
from replit import db

from channels.chip import ChipChannel
from channels.lofi import LofiChannel
from channels.wtf import WTFRadioChannel

TOKEN = os.environ['TOKEN']
intents = discord.Intents.default()
bot = discord.Bot(command_prefix='!', intents=intents)
tts = aiogTTS()
FORCE_STOPS = []
guild_to_session = {}
guild_to_channel = {}

discord.opus.load_opus('opus-1.3.1/.libs/libopus.so')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}') # type: ignore

    for guild in bot.guilds:
        if not str(guild.id) in db['vc']:
            continue

        meta = db['vc'][str(guild.id)]
        channel = bot.get_channel(meta['channel'])
        voice_client = await channel.connect() # type: ignore
        SESSION = str(uuid.uuid4())
        await start_radio(None, voice_client, SESSION, meta['radio'], guild.id)

@bot.event
async def on_music_done(_, session, is_force):
    if is_force:
        FORCE_STOPS.append(session)

@bot.command()
async def play(ctx, radio: discord.Option(
    str,
    "The radio channel",
    choices=[
        discord.OptionChoice(
            name="lofi-time"
        ),
        discord.OptionChoice(
            name="chip"
        ),
        discord.OptionChoice(
            name="wtf"
        )
    ]
)):
    voice = ctx.author.voice

    if not voice:
        await ctx.respond("You're not connected to a voice channel.")
        return

    db['vc'][str(ctx.guild.id)] = {
        "channel": voice.channel.id,
        "radio": radio
    }

    SESSION = str(uuid.uuid4())
    guild_to_session[ctx.guild.id] = SESSION

    await ctx.defer()
    if not ctx.voice_client:
        channel = voice.channel
        voice_client = await channel.connect()
    else:
        voice_client = ctx.voice_client

    if voice_client.is_playing():
        bot.dispatch('music_done', ctx, SESSION, True)
        voice_client.stop()

    msg = await ctx.respond("請稍後 uwu...")
    await start_radio(ctx, voice_client, SESSION, radio, ctx.guild.id, msg)

async def start_radio(
    ctx, 
    voice_client, 
    SESSION: str, 
    radio: str,
    guild_id: int,
    msg=None
):
    async def runner():
        bot.dispatch("music_done", ctx, SESSION, False)
    
    handler = lambda _: asyncio.run_coroutine_threadsafe(runner(), bot.loop) # noqa

    channel = {
        "lofi-time": LofiChannel,
        "chip": ChipChannel,
        "wtf": WTFRadioChannel
    }[radio](bot)
    interval = channel.interval

    guild_to_channel[guild_id] = channel

    async def wait_done() -> bool:
        def checker(_, session: str, is_force: bool = False):
            return session == SESSION
        _, _, is_force = await bot.wait_for('music_done', check=checker)
        return is_force

    played: bool = False

    async for obj in channel.process():
        if SESSION in FORCE_STOPS:
            return FORCE_STOPS.remove(SESSION)

        if not played:
            played = True
            if msg:
                await msg.edit(content="完成囉 :D")
    
        if not isinstance(obj, list):
            try:
                voice_client.stop()
            except:
                pass # noqa
            voice_client.play(
                obj,
                after=handler
            )
            if interval:
                await asyncio.sleep(interval)
                if SESSION in FORCE_STOPS:
                    return FORCE_STOPS.remove(SESSION)
            else:
                if await wait_done():
                    return FORCE_STOPS.remove(SESSION)

        else:
            voice_client.stop()
            for v in obj:
                voice_client.play(
                    await discord.FFmpegOpusAudio.from_probe(
                        v
                    ),
                    after=handler
                )
                if await wait_done():
                    return FORCE_STOPS.remove(SESSION)

                os.remove(v)

@bot.command()
async def leave(ctx):
    voice_client = ctx.voice_client

    if voice_client.is_connected():
        await voice_client.disconnect()
        try:
            bot.dispatch("music_done", ctx, guild_to_session[ctx.guild.id], True)
        except:
            pass # noqa

        await ctx.respond('bye')
        del db['vc'][str(ctx.guild.id)]

@bot.command()
async def suggest(ctx, song: str):
    if db['vc'][str(ctx.guild.id)]['radio'] != 'wtf':
        return await ctx.respond("radio is not WTFRadio")

    channel: WTFRadioChannel = guild_to_channel[ctx.guild.id]
    channel.suggest(song)

    await ctx.respond("已向主持人推薦。")

@bot.command()
async def skip(ctx):
    if ctx.guild.id not in guild_to_channel:
        return await ctx.respond("no radio for now")

    ctx.voice_client.stop()

app = fastapi.FastAPI()

@app.get('/')
async def index():
    return "hi"

Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=8080)).start()
bot.run(TOKEN)

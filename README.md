# radio

The infamous Python Discord radio bot.

## Installation

1. Environment variables: Contain `TOKEN`. To do that, simply run:

```shell
export TOKEN=bot-token
```

2. Configuring Replit Database: Contains Replit database key `vc`, used for re-joining voice channels. To initialize:

```shell
python3 -c "import replit;replit.db['vc']={}"
```

3. Installing ffmpeg, opus and yt-dlp: Use `replit-ffmpeg` to install them:

```shell
pip install replit-ffmpeg && replit-ffmpeg
```

4. Install `py-cord`:

```shell
pip install py-cord
```

5. Run the bot:

```shell
python3 main.py
```

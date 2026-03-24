import os
import requests
import subprocess
import random
import time
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo

# =========================
# TELEGRAM CONFIG
# =========================

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

client = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

# =========================
# PATH
# =========================

BASE = os.path.dirname(os.path.abspath(__file__))

VIDEO_DIR = os.path.join(BASE, "downloads", "videos")
IMAGE_DIR = os.path.join(BASE, "downloads", "images")

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

# =========================
# USER AGENTS
# =========================

USER_AGENTS = [
"Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
"Mozilla/5.0 (X11; Linux x86_64)",
"Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
"Mozilla/5.0 (Linux; Android 13)"
]

def headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://x.com/"
    }

# =========================
# DOWNLOAD FILE
# =========================

def download_file(url, path):

    r = requests.get(url, headers=headers(), stream=True)

    with open(path, "wb") as f:
        for chunk in r.iter_content(1024):
            if chunk:
                f.write(chunk)

# =========================
# TIKTOK
# =========================

def get_tiktok(url):

    try:
        r = requests.get(
            "https://tikwm.com/api/",
            params={"url": url},
            headers=headers()
        )
        return r.json()["data"]
    except:
        return None


async def handle_tt(event, url):

    await event.reply("🔎 Fetching TikTok...")

    data = get_tiktok(url)

    if not data:
        await event.reply("❌ Tidak bisa mengambil video")
        return

    if data.get("images"):

        files = []

        for i, img in enumerate(data["images"]):

            path = os.path.join(IMAGE_DIR, f"{data['id']}_{i}.jpg")

            download_file(img, path)

            files.append(path)

        await client.send_file(event.chat_id, files)

    else:

        video = data["play"]

        path = os.path.join(VIDEO_DIR, f"{data['id']}.mp4")

        download_file(video, path)

        await client.send_file(event.chat_id, path)


# =========================
# X / TWITTER
# =========================

def get_x_data(url):

    api = url.replace("x.com", "api.vxtwitter.com")

    try:
        r = requests.get(api, headers=headers())
        return r.json()
    except:
        return None


async def handle_x(event, url):

    await event.reply("🔎 Fetching X media...")

    data = get_x_data(url)

    if not data:
        await event.reply("❌ Media tidak ditemukan")
        return

    media_list = data.get("media_extended", [])

    if not media_list:
        await event.reply("❌ Tidak ada media")
        return

    files = []

    tweet_id = url.split("/")[-1]

    for i, media in enumerate(media_list):

        if media["type"] == "image":

            img = media["url"] + "?name=orig"

            path = os.path.join(IMAGE_DIR, f"{tweet_id}_{i}.jpg")

            download_file(img, path)

            files.append(path)

        elif media["type"] == "video":

            m3u8 = media["url"]

            path = os.path.join(VIDEO_DIR, f"{tweet_id}.mp4")

            subprocess.run([
                "ffmpeg",
                "-loglevel","error",
                "-y",
                "-i",m3u8,
                "-c","copy",
                path
            ])

            files.append(path)

    if files:
        await client.send_file(event.chat_id, files)

# =========================
# COMMANDS
# =========================

@client.on(events.NewMessage(pattern="/start"))
async def start(event):

    await event.reply(
        "Downloader Bot\n\n"
        "/tt <link> → TikTok\n"
        "/x <link> → X/Twitter"
    )


@client.on(events.NewMessage(pattern="/tt"))
async def tt(event):

    try:
        url = event.message.text.split(" ",1)[1]
    except:
        await event.reply("Format:\n/tt link")
        return

    await handle_tt(event, url)


@client.on(events.NewMessage(pattern="/x"))
async def x(event):

    try:
        url = event.message.text.split(" ",1)[1]
    except:
        await event.reply("Format:\n/x link")
        return

    await handle_x(event, url)


print("Bot running...")

client.run_until_disconnected()

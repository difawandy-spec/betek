import os
import requests
import subprocess
import random
import re
from urllib.parse import urlparse
from telethon import TelegramClient, events

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
XNXX_DIR = os.path.join(BASE, "downloads", "xnxx")

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(XNXX_DIR, exist_ok=True)

# =========================
# USER AGENT
# =========================

USER_AGENTS = [
"Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
"Mozilla/5.0 (X11; Linux x86_64)",
"Mozilla/5.0 (Linux; Android 13)",
"Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"
]

def headers():
    return {
        "User-Agent": random.choice(USER_AGENTS)
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
            headers=headers(),
            timeout=30
        )

        return r.json()["data"]

    except:
        return None


async def handle_tt(event, url):

    await event.reply("🔎 Fetching TikTok...")

    data = get_tiktok(url)

    if not data:
        await event.reply("❌ Video tidak ditemukan")
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

    api = url.replace("x.com", "api.vxtwitter.com").replace(
        "twitter.com", "api.vxtwitter.com"
    )

    try:
        r = requests.get(api, headers=headers(), timeout=30)
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

    await client.send_file(event.chat_id, files)

# =========================
# XNXX
# =========================

def extract_title(url):

    path = urlparse(url).path
    return path.split("/")[-1]


def get_m3u8(url):

    try:

        r = requests.get(url, headers=headers(), timeout=15)

        html = r.text

        match = re.search(r'https://[^"\']+\.m3u8[^"\']*', html)

        if match:
            return match.group(0)

        return None

    except:
        return None


async def handle_xn(event, url):

    if "video" not in url:

        await event.reply("❌ Link harus berupa halaman video XNXX")

        return

    await event.reply("🔎 Mencari stream video...")

    m3u8 = get_m3u8(url)

    if not m3u8:

        await event.reply("❌ Stream tidak ditemukan")

        return

    filename = extract_title(url)

    path = os.path.join(XNXX_DIR, filename + ".mp4")

    await event.reply("📥 Downloading video...")

    subprocess.run([
        "ffmpeg",
        "-loglevel","error",
        "-y",
        "-i",m3u8,
        "-c","copy",
        "-bsf:a","aac_adtstoasc",
        path
    ])

    await client.send_file(event.chat_id, path)

# =========================
# COMMANDS
# =========================

@client.on(events.NewMessage(pattern=r"^/start"))
async def start(event):

    await event.reply(
        "Downloader Bot\n\n"
        "/tt <link> → TikTok\n"
        "/x <link> → X / Twitter\n"
        "/xn <link> → XNXX"
    )


@client.on(events.NewMessage(pattern=r"^/tt "))
async def tt(event):

    url = event.message.text.split(" ",1)[1]

    await handle_tt(event, url)


@client.on(events.NewMessage(pattern=r"^/x "))
async def x(event):

    url = event.message.text.split(" ",1)[1]

    await handle_x(event, url)


@client.on(events.NewMessage(pattern=r"^/xn "))
async def xn(event):

    url = event.message.text.split(" ",1)[1]

    await handle_xn(event, url)


print("Bot running...")

client.run_until_disconnected()

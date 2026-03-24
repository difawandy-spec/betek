import os
import requests
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo

API_TT = "https://tikwm.com/api/"

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

client = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

BASE = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE, "downloads")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}


# =========================
# UTIL DOWNLOAD
# =========================

def download_file(url, path):

    r = requests.get(url, headers=HEADERS, stream=True)

    with open(path, "wb") as f:
        for chunk in r.iter_content(1024):
            if chunk:
                f.write(chunk)


# =========================
# TIKTOK
# =========================

def get_tiktok(url):

    r = requests.get(API_TT, params={"url": url}, headers=HEADERS)

    try:
        return r.json()["data"]
    except:
        return None


async def handle_tiktok(event, url):

    await event.reply("🔎 Fetching TikTok...")

    data = get_tiktok(url)

    if not data:
        await event.reply("❌ Tidak bisa mengambil video")
        return

    if data.get("images"):

        files = []

        for i, img in enumerate(data["images"]):

            path = os.path.join(DOWNLOAD_DIR, f"{data['id']}_{i}.jpg")

            download_file(img, path)

            files.append(path)

        await client.send_file(event.chat_id, files)

    else:

        video = data["play"]

        path = os.path.join(DOWNLOAD_DIR, f"{data['id']}.mp4")

        download_file(video, path)

        await client.send_file(
            event.chat_id,
            path,
            attributes=[
                DocumentAttributeVideo(
                    duration=0,
                    w=720,
                    h=1280,
                    supports_streaming=True
                )
            ]
        )


# =========================
# X / TWITTER
# =========================

def get_x_media(url):

    api = url.replace("x.com", "api.vxtwitter.com").replace("twitter.com", "api.vxtwitter.com")

    r = requests.get(api)

    try:
        return r.json()
    except:
        return None


async def handle_x(event, url):

    await event.reply("🔎 Fetching X media...")

    data = get_x_media(url)

    if not data:
        await event.reply("❌ Media tidak ditemukan")
        return

    files = []

    media = data.get("media_extended", [])

    for i, m in enumerate(media):

        if m["type"] == "image":

            path = os.path.join(DOWNLOAD_DIR, f"x_{i}.jpg")

            download_file(m["url"], path)

            files.append(path)

        elif m["type"] == "video":

            path = os.path.join(DOWNLOAD_DIR, f"x_video.mp4")

            download_file(m["url"], path)

            files.append(path)

    if files:
        await client.send_file(event.chat_id, files)
    else:
        await event.reply("❌ Media tidak ditemukan")


# =========================
# COMMANDS
# =========================

@client.on(events.NewMessage(pattern="/start"))
async def start(event):

    await event.reply(
        "🤖 Downloader Bot\n\n"
        "Commands:\n"
        "/tt <link> → download TikTok\n"
        "/x <link> → download X/Twitter"
    )


@client.on(events.NewMessage(pattern="/tt"))
async def tt(event):

    try:
        url = event.message.text.split(" ", 1)[1]
    except:
        await event.reply("Format:\n/tt link")
        return

    await handle_tiktok(event, url)


@client.on(events.NewMessage(pattern="/x"))
async def x(event):

    try:
        url = event.message.text.split(" ", 1)[1]
    except:
        await event.reply("Format:\n/x link")
        return

    await handle_x(event, url)


print("Bot running...")

client.run_until_disconnected()

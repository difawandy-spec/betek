import os
import requests
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeVideo

API = "https://tikwm.com/api/"

api_id = 1916950
api_hash = "9e268fee501ad809e4f5f598adcb970c"
bot_token = "7990971853:AAEcjoTqHNd_T-pc747-47AuBHCN1CXt7A8"

client = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE, "downloads")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_data(url):
    r = requests.get(API, params={"url": url}, headers=HEADERS)

    try:
        return r.json()["data"]
    except:
        return None


def download_file(url, path):

    r = requests.get(url, headers=HEADERS, stream=True)

    with open(path, "wb") as f:
        for chunk in r.iter_content(1024):
            if chunk:
                f.write(chunk)


async def handle_download(event, data):

    if data.get("images"):

        await event.reply("📸 Photo post detected...")

        images = data["images"]

        files = []

        for i, img in enumerate(images):

            path = os.path.join(DOWNLOAD_DIR, f"{data['id']}_{i}.jpg")

            download_file(img, path)

            files.append(path)

        await client.send_file(event.chat_id, files)

    else:

        await event.reply("⬇ Downloading video...")

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


@client.on(events.NewMessage(pattern="/start"))
async def start(event):

    await event.reply(
        "🤖 TikTok Downloader Bot\n\n"
        "Send TikTok URL to download video or photos."
    )


@client.on(events.NewMessage)
async def handler(event):

    text = event.text

    if "tiktok.com" in text:

        await event.reply("🔎 Fetching video...")

        data = get_data(text)

        if not data:
            await event.reply("❌ Failed to fetch video")
            return

        await handle_download(event, data)


print("Bot running...")

client.run_until_disconnected()

import logging
import os

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VIDEOS_API_HOST = os.getenv("VIDEOS_API_HOST")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")


async def get_video(q, lang="en") -> str:
    async with aiohttp.ClientSession() as session:
        url = f"{VIDEOS_API_HOST}/api/v1/videos/?q={q}&lang={lang}"
        logger.info("Get videos %s", url)
        async with session.get(url) as resp:
            videos = await resp.json()
            return videos[0]["url"]


# Create a bot object and set up a dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)


# Define a function to handle the /start command
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply(
        "Hi! Send me a English word and I'll send you YouTube video with this word."
    )


# Define a function to handle messages
@dp.message_handler()
async def handle_message(message: types.Message):
    video_url = await get_video(message.text)
    logger.info("Word: '%s' founded video: %s", message.text, video_url)
    await bot.send_message(
        chat_id=message.chat.id,
        text=video_url,
        disable_web_page_preview=False,
        parse_mode=ParseMode.HTML,
    )


# Start the bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)

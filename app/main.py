import asyncio
import logging
import os
import re
from collections import defaultdict

import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from jinja2 import Environment, PackageLoader, select_autoescape

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VIDEOS_API_HOST = os.getenv("VIDEOS_API_HOST")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

env = Environment(
    loader=PackageLoader("app", "templates"),
    autoescape=select_autoescape(["html", "xml", "j2"]),
    trim_blocks=True,
    lstrip_blocks=True,
)
message_template = env.get_template("definition_message.j2")
video_template = env.get_template("video_message.j2")


async def get_video(q, lang="en") -> dict:
    async with aiohttp.ClientSession() as session:
        url = f"{VIDEOS_API_HOST}/api/v1/videos/?q={q}&lang={lang}"
        logger.info("Get videos %s", url)
        async with session.get(url) as resp:
            videos = await resp.json()
            return {"video_url": videos[0]["url"], "caption_text": videos[0]["text"]}


def aggregate_definitions(data, meanings_limit: int = 3):
    phonetic_groups_audio = defaultdict(list)
    phonetic_groups_definition = defaultdict(lambda: defaultdict(list))
    for phonetic in data:
        phonetic_group = phonetic.get("phonetic", "")
        for audio in phonetic["phonetics"]:
            if audio["audio"]:
                phonetic_groups_audio[phonetic_group].append(audio["audio"])

        for meaning in phonetic["meanings"]:
            phonetic_groups_definition[phonetic_group][meaning["partOfSpeech"]].extend(
                meaning["definitions"]
            )

    out = []
    for phonetic, audios in phonetic_groups_audio.items():
        meanings = {}
        for part_of_speech, meanings_ in phonetic_groups_definition[phonetic].items():
            meanings[part_of_speech] = [meaning["definition"] for meaning in meanings_][
                :meanings_limit
            ]
        out.append({"audio": audios[0], "meanings": meanings})
    return out


async def get_audio_and_definition(word):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        async with session.get(url.format(word=word)) as resp:
            response = await resp.json()
            return aggregate_definitions(response)


async def get_word_data(word):
    video_data, definitions = await asyncio.gather(
        get_video(word), get_audio_and_definition(word)
    )
    return {**video_data, "definitions": definitions}


# Create a bot object and set up a dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)


# Define a function to handle the /start command
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply(
        "Hi! Send me a English word and I'll send you YouTube video with this word."
    )


def highlight_text(text, highlighting_text) -> str:
    highlighting_text = highlighting_text.strip()
    return str(re.sub(highlighting_text, f"*{highlighting_text}*", text, flags=re.I))


# Define a function to handle messages
@dp.message_handler()
async def handle_message(message: types.Message):
    data = await get_word_data(message.text)
    logger.info("Word: '%s' founded video: %s", message.text, data["video_url"])
    await bot.send_message(
        chat_id=message.chat.id,
        text=video_template.render(
            {
                **data,
                "word": message.text,
                "caption_text": highlight_text(data["caption_text"], message.text),
            }
        ),
        disable_web_page_preview=False,
        parse_mode=ParseMode.MARKDOWN,
    )
    for definition in data["definitions"]:
        await bot.send_audio(
            chat_id=message.chat.id,
            audio=definition["audio"],
            caption=message_template.render({**definition, "word": message.text}),
            parse_mode=ParseMode.HTML,
        )


# Start the bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)

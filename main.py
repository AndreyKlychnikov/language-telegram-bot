import asyncio
import logging
import os
from collections import defaultdict

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
        meanings = []
        for part_of_speech, meanings_ in phonetic_groups_definition[phonetic].items():
            for meaning in meanings_:
                meanings.append(
                    {
                        "part_of_speech": part_of_speech,
                        "definition": meaning["definition"],
                    }
                )
        out.append({"audio": audios[0], "meanings": meanings[:meanings_limit]})
    return out


async def get_audio_and_definition(word):
    async with aiohttp.ClientSession() as session:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        async with session.get(url.format(word=word)) as resp:
            response = await resp.json()
            return aggregate_definitions(response)


async def get_word_data(word):
    video_url, definitions = await asyncio.gather(
        get_video(word), get_audio_and_definition(word)
    )
    return {"video_url": video_url, "definitions": definitions}


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
    data = await get_word_data(message.text)
    logger.info("Word: '%s' founded video: %s", message.text, data["video_url"])
    await bot.send_message(
        chat_id=message.chat.id,
        text=data["video_url"],
        disable_web_page_preview=False,
        parse_mode=ParseMode.HTML,
    )
    sent_audios = set()
    for definition in data["definitions"]:
        text = [
            (
                f"{meaning['part_of_speech'].capitalize()}\n"
                f"Definition:\n{meaning['definition']}"
            )
            for meaning in definition["meanings"]
        ]

        await bot.send_message(
            chat_id=message.chat.id,
            text="\n\n".join(text),
            disable_web_page_preview=False,
            parse_mode=ParseMode.HTML,
        )
        if definition["audio"] not in sent_audios:
            await bot.send_audio(message.chat.id, audio=definition["audio"])
            sent_audios.add(definition["audio"])


# Start the bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)

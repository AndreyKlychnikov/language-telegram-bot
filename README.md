# Telegram Bot

This is a Telegram bot that can find and send YouTube videos based on English words. The bot is built using Python and the aiogram library.

## Requirements

- Python 3.7+
- `aiogram` and `aiohttp` Python packages
- Telegram Bot API token
- A running instance of the Videos API [repo](https://github.com/AndreyKlychnikov/youtube-search)

## Installation

1. Clone this repository:

```shell
git clone https://github.com/AndreyKlychnikov/language-telegram-bot.git
```

2. Install the required packages:
```shell
poetry install
```

3. Copy `.env.template` file as `.env` and set the following environment variables:

- `VIDEOS_API_HOST`: the URL of the videos API
- `TELEGRAM_TOKEN`: your Telegram Bot API token

4. Run the bot:
```shell
poetry shell
python main.py
```


## Usage

To use the bot, simply send an English word to it and it will find a related YouTube video and send it back to you. You can also use the `/start` command to get a brief introduction to the bot.

Note that the bot requires a running instance of the videos API, which should be accessible at the URL specified in the `VIDEOS_API_HOST` environment variable.

## Contributing

If you find any bugs or issues with the bot, or if you have suggestions for new features or improvements, please feel free to open an issue or submit a pull request. All contributions are welcome!

## License

This bot is released under the CC BY-NC license. See the [LICENSE](LICENSE) file for more information.


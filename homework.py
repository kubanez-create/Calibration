"""Telegram bot which keeps track of your predictions."""
from __future__ import annotations

import logging
import os
import sys
import time
from logging import StreamHandler
from typing import Any, Union
from http import HTTPStatus

import requests
import mysql.connector
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from dotenv import load_dotenv


from myexceptions import (
    APIExceptionError,
    BadRequestError,
    MissingKyeError,
    TokenExceptionError,
)

load_dotenv()


TELEGRAM_TOKEN: str = str(os.getenv("TELEGRAM_TOKEN"))
TELEGRAM_CHAT_ID: Union[str, None] = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD: int = 600
WAITING_TIME: int = 500


def check_tokens() -> bool:
    """Function which ckecks availability of global variables."""
    return all((TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))

def send_form(update, context):
    # Create the form
    form = []
    form.append(['Name:', 'Age:'])
    form.append(['', ''])

    # Send the form
    update.message.reply_text('Please fill out the following form:', reply_markup=form)

def send_message(bot: telegram.Bot, message: str) -> None:
    """Function which sends a message to a telegram chat.

    Telegram chat defined in TELEGRAM_CHAT_ID global variable.

    Args:
        bt (telegram.Bot): an instance of a Telegram bot class
        message (str): text of a message which is to be sent to the chat
    """
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=f"{message}",
        )
        logging.debug("We have started sending a message")
    except Exception as error:
        logging.error(
            f"An error occured during sending of a message. Error: {error}"
        )
    logging.debug("Message successfully sent to the user")


def get_api_answer(timestamp: int) -> dict[str, Any]:
    """Function which sends request to the API's endpoint.

    It returns the API's response cast to a python's dict.

    Args:
        timestamp (int): starting Unix time to check homework

    Returns:
        dict[str, Any]: API's response casted to python dict
    """
    url: str = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
    headers: dict[str, str] = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}
    payload: dict[str, int] = {"from_date": timestamp}

    try:
        logging.debug("We have sended a request to an API")
        homework_statuses: requests.Response = requests.get(
            url, headers=headers, params=payload, timeout=WAITING_TIME
        )
    except requests.RequestException:
        raise BadRequestError("RequestException error")
    status: int = homework_statuses.status_code
    if status != HTTPStatus.OK:
        raise APIExceptionError(
            f"Server returned error with the status {status}"
        )
    return homework_statuses.json()


def check_response(response: dict[str, Any]) -> list[dict[str, str]]:
    """Checks if API's response complies with documentation.

    Args:
        response (dict): API's response casted to a dict type

    Returns:
        list[dict[str, str]]: python list of dictionaries
    """
    if not isinstance(response, dict):
        raise TypeError("Response must be a python dictionary but it is not")
    if "current_date" not in response:
        raise MissingKyeError("Response lacks the 'current_date' key")
    if "homeworks" not in response:
        raise MissingKyeError("Response lacks the 'homeworks' key")

    homeworks = response.get("homeworks")

    if not isinstance(homeworks, list):
        raise TypeError("Response['homeworks'] is not a python list")

    return homeworks


def parse_status(homework: dict[str, str]) -> str:
    """Function which processes json response into python format.

    It takes information abour some specific homework and returns
    python string which contains this information.

    Args:
        homework (dict[str, str]): API's response
        related to some particular homework casted to a python dict

    Returns:
        str: python string
    """
    if "homework_name" not in homework:
        raise MissingKyeError(
            "An API's response lacks the 'homework_name' key"
        )
    if "status" not in homework:
        raise MissingKyeError(
            "An API's response lacks the 'status' key"
        )
    if homework.get("status") not in HOMEWORK_VERDICTS:
        raise MissingKyeError(
            "An API's responded with an unknown homework status"
        )
    homework_name: str = homework["homework_name"]
    homework_status: str = homework["status"]
    verdict: str = HOMEWORK_VERDICTS[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger: logging.Logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler: StreamHandler = StreamHandler(stream=sys.stdout)
    logger.addHandler(handler)

    # Connect to the database
    cnx = mysql.connector.connect(
        host='YOUR_DB_HOST',
        user='YOUR_DB_USER',
        password='YOUR_DB_PASSWORD',
        database='YOUR_DB_NAME'
    )

    # Create a cursor
    cursor = cnx.cursor()

    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add a command handler to send the form
    dp.add_handler(CommandHandler('send_form', send_form))

    # Add a message handler to handle form submissions
    dp.add_handler(MessageHandler(Filters.text, form_submission))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

    """Основная логика работы бота."""
    

if __name__ == "__main__":
    main()

"""Telegram bot which keeps track of your predictions."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
import re
import tempfile
from enum import Enum, auto
from logging.handlers import RotatingFileHandler
from itertools import chain

import mysql.connector
from dotenv import load_dotenv
# pip install telethon
from telethon import Button, TelegramClient, events

from helpers import create_message_categories, create_message_select_query
from converter import converter
from validators import (
    validate_checking,
    validate_creating,
    validate_deletion,
    validate_outcome,
    validate_updating,
)

load_dotenv()

TELEGRAM_TOKEN: str = '5846308603:AAETAEAYZ5GCXf09bYDQgznz14WjO6qEXZ8'
API_HASH: str = str(os.getenv("API_HASH"))
API_ID: int = int(os.getenv("API_ID"))
USER: str = str(os.getenv("USER"))
PASSWORD: str = str(os.getenv("PASSWORD"))
HOST: str = str(os.getenv("HOST"))
PORT: str = str(os.getenv("PORT"))
DATABASE: str = str(os.getenv("DATABASE"))

SESSION_NAME: str = "sessions/ruBot"
CHUNK_SIZE: int = 10
COUNTER: int = None

# Start the Client (telethon)
client = TelegramClient(
    SESSION_NAME, API_ID, API_HASH
).start(bot_token=TELEGRAM_TOKEN)


class State(Enum):
    WAIT_CHECK = auto()
    WAIT_UPDATE = auto()
    WAIT_ENTER = auto()
    WAIT_DELETE = auto()


# The state in which different users are, {user_id: state}
conversation_state = {}


def check_tokens() -> bool:
    """Check availability of global variables."""
    return all((TELEGRAM_TOKEN, API_HASH, API_ID))


@client.on(events.NewMessage(pattern="(?i)/start"))
async def start(event):
    """Initialize the bot and show keyboard to a user.

    Args:
        event (EventCommon): NewMessage event
    """
    sender = await event.get_sender()
    SENDER = sender.id

    markup = event.client.build_reply_markup(
        [
            [
                Button.text("Добавить предсказание", resize=True),
                Button.text("Показать предсказания"),
            ],
            [
                Button.text("Обновить предсказание"),
                Button.text("Удалить предсказание")
            ],
            [
                Button.text("Результат предсказания"),
                Button.text("Проверить калибровку")
            ],
            [
                Button.text("Мои категории"),
                Button.text("Как пользоваться")
            ],
        ]
    )

    text = (
        "Привет! Здесь можно оставлять предсказания, записывать, что случилось"
        " в реальности, проверять и, мы все надеемся, -  улучшать свою"
        " калибровку. Начните знакомство с ботом нажав кнопку Как пользоваться."
        " За ней Вы найдете краткую инструкцию к данному боту."
    )
    await client.send_message(SENDER, text, buttons=markup)
    logger.info("Looks like we have a new user!", exc_info=1)


@client.on(events.NewMessage(pattern="Как"))
async def guide(event):
    """Show to a user 'help page'.

    With possible commands and their use cases.

    Args:
        event (EventCommon): NewMessage event
    """
    try:
        text = (
            "Целью создания данного бота был сбор Ваших предсказаний"
            ", сохранение их, чтобы Вы смогли проверить насколько"
            " хорошо Вы калиброваны в целом и/или в какой-то отдельной"
            " категории.\n"
            "**Чтобы добавить новое предсказание** - нажмите на кнопку"
            " Добавить предсказание; \n"
            "Для того, чтобы удалить, обновить или внести итог ранее"
            " сделанного предсказания Вам понадобится **уточнить номер**"
            " этого предсказания. Для этого нажмите на кнопку"
            " Показать предсказания;\n"
            "**Для того, чтобы обновить ранее сделанное предсказание ("
            "обычно в свете некоторых новых наблюдений)** - нажмите на"
            " кнопку Обновить предсказание;\n"
            "**В случае, если в процессе добавления новое предсказания"
            " Вы совершили больше ошибок, нежели то дозволяет Ваша"
            " натура перфекциониста** - нажмите на кнопку Удалить"
            " предсказание и затем внесите Ваше предсказание заново;\n"
            "**После того как Вы узнали, чем в реальности обернулись"
            " предсказанные Вами события** - нажмите на кнопку Результат"
            " предсказания;\n"
            " **Наконец, для того, чтобы уточнить свою калибровку"
            " на основе внесенных ранее предсказаний с известным исходом** - "
            "нажмите на кнопку Проверить калибровку и следуйте дальнейшим"
            " инструкциям;\n"
            "Если же, по какой-то причине, Вы начали пользоваться данным ботом"
            " и ощутили желание поучаствовать в улучшении его фунциональности"
            " или высказать автору что за полный отстой он создал (даже в "
            "змейку не поиграешь) - отправьте мне письмо по адресу"
            " kubanez74@gmail.com."
        )
        await event.respond(text)

    except Exception as e:
        logger.error(
            "Something went wrong when showing help page"
            f" with an error: {e}"
        )
        return


@client.on(events.NewMessage(pattern=validate_checking))
async def CUEDhandler(event):
    sender = await event.get_sender()
    who = sender.id
    state = conversation_state.get(who)
    mes = event.message.raw_text

    # CHECK CALIBRATION
    if re.match(r"Проверить", mes):
        conversation_state[who] = State.WAIT_CHECK
        text = (
            "Если Вы хотели бы проверить общую калибровку по всем сделанным"
            " предсказаниям - отправьте слово общая. Если Вас интересует"
            " калибровка по какой-то отдельной категории - отправьте"
            " название данной категории. Например, можно отправить <общая>"
            " или <работа> или <политика> без кавычек и/или знаков препинания."
            )
        await event.respond(text)

    elif state == State.WAIT_CHECK:
        # get a list of user's categories!
        query = (
            "SELECT DISTINCT task_category FROM"
            " predictions.raw_predictions WHERE user_id = %s"
        )
        crsr.execute(query, [who])
        res = crsr.fetchall()  # fetch all the results
        # If there is no categories yet, print a warning
        if not res:
            text = (
                "Кажется, Вы еще не сохраняли предсказаний."
                " Попробуйте."
            )
            del conversation_state[who]
            await client.send_message(who, text, parse_mode="html")
        else:
            cat_list = [a for a in chain.from_iterable(res)] + ["общая", "Общая"]
            if mes not in cat_list:
                await client.send_message(
                    who, ("Вы не создали ни одного предсказания в данной"
                          " категории.")
                )
                del conversation_state[who]
                logger.info("Categories request isn't valid")

            else:
                # Execute the query and get all (*) predictions
                if mes.lower() == "общая":
                    query = """SELECT tot_acc_50 / tot_num_pred AS calibration_50,
                        tot_acc_90 / tot_num_pred AS calibration_90
                    FROM (
                        SELECT COUNT(id) AS tot_num_pred,
                        SUM(acc_50) AS tot_acc_50,
                        SUM(acc_90) AS tot_acc_90
                    FROM (
                        SELECT
                        id, user_id,
                        pred_low_50_conf <= actual_outcome AND
                        pred_high_50_conf >= actual_outcome AS acc_50,
                        pred_low_90_conf <= actual_outcome AND
                        pred_high_90_conf >= actual_outcome AS acc_90
                        FROM predictions.raw_predictions
                        WHERE user_id = %s AND
                        actual_outcome IS NOT NULL)
                        AS base_table
                    GROUP BY user_id
                    ) AS outer_table;"""
                    crsr.execute(query, [who])
                    res = crsr.fetchall()  # fetch all the results

                    text = (
                        "Ваша общая калибровка на текущий момент составляет:"
                        f"для 50% уровня уверенности - {res[0][0]:.2f}"
                        "\n"
                        f"для 90% уровня уверенности - {res[0][1]:.2f}"
                    )
                else:
                    # Or get results for a specific category
                    query = (
                        "SELECT tot_acc_50 / tot_num_pred AS calibration_50,"
                        " tot_acc_90 / tot_num_pred AS calibration_90"
                        " FROM ("
                        "SELECT COUNT(id) AS tot_num_pred,"
                        " SUM(acc_50) AS tot_acc_50,"
                        " SUM(acc_90) AS tot_acc_90"
                        " FROM ("
                        "SELECT"
                        " id, user_id,"
                        " pred_low_50_conf <= actual_outcome AND"
                        " pred_high_50_conf >= actual_outcome AS acc_50,"
                        " pred_low_90_conf <= actual_outcome AND"
                        " pred_high_90_conf >= actual_outcome AS acc_90"
                        " FROM predictions.raw_predictions"
                        " WHERE user_id = %s AND"
                        " task_category = %s AND"
                        " actual_outcome IS NOT NULL)"
                        " AS base_table"
                        " GROUP BY user_id"
                        ") AS outer_table;"
                    )
                    crsr.execute(query, (who, mes))
                    res = crsr.fetchall()  # fetch all the results
                    text = (
                        "Ваша калибровка для выбранной категории"
                        " на текущий момент составляет:"
                        f"для 50% уровня уверенности - {res[0][0]:.2f}"
                        "\n"
                        f"для 90% уровня уверенности - {res[0][1]:.2f}"
                    )
                await client.send_message(who, text, parse_mode="html")
                del conversation_state[who]
                logger.debug(f" Check function returned following: {text}")

    # UPDATE METHOD
    elif re.match(r"Обновить", mes):
        conversation_state[who] = State.WAIT_UPDATE
        text = (
            "Для того, чтобы обновить ранее внесенное предсказание ("
            "изменить нижнюю и верхнюю границу), обычно в свете нового"
            " знания, внесите номер предсказания, которое Вы желаете обновить"
            " и затем 4 цифры, разделенные точкой с запятой и пробелом"
            " - новую нижнюю и верхнюю границы"
            " для 50% и 90% уровней уверенности.\nНапример: 1; 3; 5; 1; 8"
        )
        await event.respond(text)

    elif state == State.WAIT_UPDATE:
        query = (
            "SELECT id FROM"
            " predictions.raw_predictions WHERE user_id = %s"
        )
        crsr.execute(query, [who])
        user_predictions = crsr.fetchall()  # fetch all the results
        # If there is no categories yet, print a warning
        if not user_predictions:
            text = (
                "Кажется, Вы еще не сохраняли предсказаний."
                " Попробуйте."
            )
            del conversation_state[who]
            await client.send_message(who, text, parse_mode="html")
            logger.info("Someone tried to update a prediction without"
                        "making at least one themselve")
        if not validate_updating(mes):
            await client.send_message(
                (
                    "К сожалению, отправленное вами сообщение не похоже на"
                    " 5 цифр, разделенных точкой с запятой и пробелом.\n"
                    "Проверьте ваше сообщение, нажмите еще раз на кнопку"
                    " Обновить предсказание и отправьте сообщение с"
                    " обновленными цифрами еще раз."
                )
            )
            del conversation_state[who]
            logger.info("Update message isn't valid")
        else:
            mes_list = [str(x) for x in chain.from_iterable(user_predictions)]
            message = mes.split("; ")
            index = message[0]
            low_50 = message[1]
            hi_50 = message[2]
            low_90 = message[3]
            hi_90 = message[4]
            if index not in mes_list:
                await client.send_message(
                    who,
                    ("Номер предсказания не совпадает ни с одним из сделанных"
                     " Вами предсказаний. Пожалуйста внесите корректный номер.")
                )
                del conversation_state[who]
            else:
                params = (low_50, hi_50, low_90, hi_90, index)
                sql_command = """UPDATE predictions.raw_predictions SET
                pred_low_50_conf=%s, pred_high_50_conf=%s,
                pred_low_90_conf=%s, pred_high_50_conf=%s
                WHERE id=%s;"""

                crsr.execute(sql_command, params)  # Execute the query
                conn.commit()  # Commit the changes
                await client.send_message(
                    who,
                    f"Предсказание с номером {index} успешно обновлено."
                )
                logger.info(f"Prediction with id {index} successfully updated")
                del conversation_state[who]
    # ENTER OUTCOME
    elif re.match(r"Результат", mes):
        conversation_state[who] = State.WAIT_ENTER
        text = (
            "Для того чтобы внести результат предсказания, отправьте две"
            " цифры - номер предсказания и итог, например - <17; 0.00008>"
            " без кавычек."
            )
        await event.respond(text)
    elif state == State.WAIT_ENTER:
        query = (
            "SELECT id FROM"
            " predictions.raw_predictions WHERE user_id = %s"
        )
        crsr.execute(query, [who])
        user_predictions = crsr.fetchall()  # fetch all the results
        # If there is no categories yet, print a warning
        if not user_predictions:
            text = (
                "Кажется, Вы еще не сохраняли предсказаний."
                " Попробуйте."
            )
            del conversation_state[who]
            await client.send_message(who, text, parse_mode="html")
            logger.info("Someone tried to enter an outcome of a prediction"
                        " without making at least one themselve")

        if not validate_outcome(mes):
            await client.send_message(
                (
                    "К сожалению Ваше сообщение не похоже на две цифры,"
                    " разделенные точкой с запятой и пробелом. Пожалуйста"
                    " повторно нажмите на кнопку Результат предсказания"
                    ", исправьте текст сообщения и отправьте его еще раз."
                )
            )
            logger.info("Outcome message isn't valid")
            del conversation_state[who]

        else:
            mes_list = [str(x) for x in chain.from_iterable(user_predictions)]
            list_of_words = mes.split("; ")
            pred_id = list_of_words[0]
            actual_outcome = list_of_words[1]

            if pred_id not in mes_list:
                await client.send_message(
                    who,
                    ("Номер предсказания не совпадает ни с одним из сделанных"
                     " Вами предсказаний. Пожалуйста внесите корректный номер.")
                )
                del conversation_state[who]
            # Create the tuple "params" with all the parameters inserted
            # by the user
            else:
                params = (actual_outcome, pred_id)
                sql_command = """UPDATE predictions.raw_predictions SET
                actual_outcome=%s WHERE id=%s;"""

                crsr.execute(sql_command, params)  # Execute the query
                conn.commit()  # Commit the changes
                await client.send_message(
                    who,
                    (f"Результат предсказание с номером {pred_id}"
                     " успешно внесен.")
                )
                logger.info(
                    f"Outcome of the prediction with id {pred_id}"
                    "successfully entered")
                del conversation_state[who]


@client.on(events.NewMessage(pattern="Make"))
async def add_prediction(event):
    """Add new prediction.

    Args:
        event (EventCommon): NewMessage event
    """
    try:
        sender = await event.get_sender()
        SENDER = sender.id
        # Start a conversation
        async with client.conversation(
            await event.get_chat(), exclusive=True
        ) as conv:
            text = (
                "Enter your prediction in a form:\n"
                "- **description** - what you predict specifically "
                "(not longer then 200 characters so try to be concise);\n"
                "- **category** of your prediction - one word;\n"
                "- **unit of measure** whether it is minutes, days,"
                " persons or chickens - one word;\n"
                "- **lower bound on your prediction with a 50 percent**"
                " **condidence**;\n"
                "- **upper bound on your prediction with a 50 percent**"
                " **condidence**;\n"
                "- **lower bound on your prediction with a 90 percent**"
                " **condidence**;\n"
                "- **upper bound on your prediction with a 90 percent**"
                " **condidence**;\n"
                "For example type in:\n"
                " How long does it going to take?; work; hours; 2; 8;"
                " 1; 16\n"
                "Please use '; ' to separate field values and '.' to"
                " separate decimal part in numbers."
            )
            await conv.send_message(text, parse_mode="md")
            response = await conv.get_response(timeout=600)
            if not validate_creating(response.text):
                await conv.send_message(
                    (
                        "Sorry but your input isn't valid."
                        " Please check that what your are trying to add"
                        " consists of text description and/or punctiation"
                        " marks ('.', ',', '?', '!'), a single word for a"
                        " category of your prediction, another word for a"
                        " nessesary unit of measure, 4 numbers which stand for"
                        " your upper and lower predicted bounds and all"
                        " of those are divided by semicolon and whitespace."
                        " Also chech that a decimal part of numbers separated"
                        " by a dot (.) not a colon (,)."
                    )
                )
                logger.info("Prediction isn't valid")
            else:
                list_of_words = response.text.split("; ")
                user_id = SENDER
                # Use the datetime library to get the date
                # (and format it as DAY/MONTH/YEAR)
                date = datetime.now().strftime("%d/%m/%Y")
                task_description = list_of_words[0]
                task_category = list_of_words[1]
                unit_of_measure = list_of_words[2]
                pred_low_50_conf = list_of_words[3]
                pred_high_50_conf = list_of_words[4]
                pred_low_90_conf = list_of_words[5]
                pred_high_90_conf = list_of_words[6]
                actual_outcome = None

                # Create the tuple "params" with all the parameters inserted
                # by the user
                params = (
                    user_id,
                    date,
                    task_description,
                    task_category,
                    unit_of_measure,
                    pred_low_50_conf,
                    pred_high_50_conf,
                    pred_low_90_conf,
                    pred_high_90_conf,
                    actual_outcome,
                )
                # the initial NULL is for the AUTOINCREMENT id inside the table
                sql_command = """
                    INSERT INTO predictions.raw_predictions
                    VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
                crsr.execute(sql_command, params)  # Execute the query
                conn.commit()  # commit the changes

                # If at least 1 row is affected by the query we send specific
                # messages
                if crsr.rowcount < 1:
                    text = "Something went wrong, please try again"
                    await client.send_message(SENDER, text, parse_mode="html")
                    logger.info("Creation of a prediction was aborted"
                                f" with the text: {text}")
                else:
                    text = "Prediction correctly inserted"
                    await client.send_message(SENDER, text, parse_mode="html")
                    logger.debug("Someone just added a prediction!")
                global COUNTER
                COUNTER += 1
        await conv.cancel_all()
        return

    except Exception as e:
        logger.error(
            "Something went wrong when inserting a new prediction "
            f"with an error: {e}"
        )
        return


@client.on(events.NewMessage(pattern="Show"))
async def display(event):
    """Show predictions to a user.

    Args:
        event (EventCommon): NewMessage event
    """
    try:
        sender = await event.get_sender()
        SENDER = sender.id
        query = "SELECT * FROM predictions.raw_predictions WHERE user_id = %s"
        crsr.execute(query, [SENDER])
        res = crsr.fetchall()  # fetch all the results
        # If there is at least 1 row selected, print a message with the list
        # of all predictions
        if res:
            message = res[0:CHUNK_SIZE]
            if len(res) <= CHUNK_SIZE:
                with tempfile.TemporaryDirectory() as tmpdirname:
                    text = create_message_select_query(message)
                    converter(text, tmpdirname)
                    await client.send_file(
                        SENDER,
                        f'{tmpdirname}/out.jpg')
                # send_message(SENDER, text, parse_mode="html")
            else:
                callback_data = f"page_{1}"
                button = event.client.build_reply_markup(
                    [Button.inline("Next", data=callback_data)]
                )
                with tempfile.TemporaryDirectory() as tmpdirname:
                    text = create_message_select_query(message)
                    converter(text, tmpdirname)
                    await client.send_file(
                        SENDER,
                        f'{tmpdirname}/out.jpg',
                        buttons=button)
                # send_message(
                # SENDER, text, parse_mode="html", buttons=button
                # )
        # Otherwhise, print a default text
        else:
            text = (
                "You have made no predictions so far. Give it a try!"
                " It is for free."
            )
            await client.send_message(SENDER, text, parse_mode="html")

    except Exception as e:
        logger.error(
            "Something went wrong when showing user's predictions "
            f"with an error: {e}"
        )
        return


@client.on(events.CallbackQuery(data=re.compile(b"page")))
async def show(event):
    """Show to a user their predictions.

    Activated only if user has more then 10 predictions, using
    ad-hoc pagination.

    Args:
        event (EventCommon): CallbackQuery event
    """
    try:
        sender = await event.get_sender()
        SENDER = sender.id
        page = int(event.data.split(b"page_")[1])
        query = (
            "SELECT * FROM predictions.raw_predictions WHERE user_id = %s"
            " LIMIT %s, %s;"
        )
        crsr.execute(query, [SENDER, page * CHUNK_SIZE, CHUNK_SIZE])
        res = crsr.fetchall()  # fetch all the results

        if page >= 1 and (COUNTER - page * CHUNK_SIZE) > CHUNK_SIZE:
            forward = f"page_{page + 1}"
            backward = f"page_{page - 1}"
            button = event.client.build_reply_markup(
                [
                    Button.inline("Previous", data=backward),
                    Button.inline("Next", data=forward),
                ]
            )
            with tempfile.TemporaryDirectory() as tmpdirname:
                text = create_message_select_query(res)
                converter(text, tmpdirname)
                await client.send_file(
                    SENDER,
                    f'{tmpdirname}/out.jpg',
                    buttons=button)
            # await client.send_message(SENDER, text, parse_mode="html",
            #                           buttons=button)
        elif page >= 1 and (COUNTER - page * CHUNK_SIZE) <= CHUNK_SIZE:
            backward = f"page_{page - 1}"
            button = event.client.build_reply_markup(
                [
                    Button.inline("Previous", data=backward),
                ]
            )
            with tempfile.TemporaryDirectory() as tmpdirname:
                text = create_message_select_query(res)
                converter(text, tmpdirname)
                await client.send_file(
                    SENDER,
                    f'{tmpdirname}/out.jpg',
                    buttons=button)
            # await client.send_message(SENDER, text, parse_mode="html",
            #                           buttons=button)
        else:
            forward = f"page_{page + 1}"
            button = event.client.build_reply_markup(
                [
                    Button.inline("Next", data=forward),
                ]
            )
            with tempfile.TemporaryDirectory() as tmpdirname:
                text = create_message_select_query(res)
                converter(text, tmpdirname)
                await client.send_file(
                    SENDER,
                    f'{tmpdirname}/out.jpg',
                    buttons=button)
            # await client.send_message(SENDER, text, parse_mode="html",
            #                           buttons=button)

    except Exception as e:
        logger.error(
            f"Something went wrong when showing page {page} user's predictions"
            f" with an error: {e}"
        )
        return


@client.on(events.NewMessage(pattern="My"))
async def display_categories(event):
    """Show to a user their unique categories.

    Which they have already inputed.

    Args:
        event (EventCommon): NewMessage event
    """
    try:
        sender = await event.get_sender()
        SENDER = sender.id
        query = (
            "SELECT DISTINCT task_category FROM"
            " predictions.raw_predictions WHERE user_id = %s"
        )
        crsr.execute(query, [SENDER])
        res = crsr.fetchall()  # fetch all the results
        # If there is at least 1 row selected, print a message with the list
        # of all predictions
        if res:
            text = create_message_categories(res)
            await client.send_message(SENDER, text, parse_mode="html")
        # Otherwhise, print a default text
        else:
            text = (
                "You have made no predictions so far. Give it a try! "
                "It is for free."
            )
            await client.send_message(SENDER, text, parse_mode="html")
            logger.debug("Someone tried to have a look at their categories"
                         " without any made predictions.")

    except Exception as e:
        logger.error(
            "Something went wrong when showing user's predictions "
            f"with an error: {e}"
        )
        return



@client.on(events.NewMessage(pattern="Enter"))
async def enter(event):
    """Enter an actual outcome for a made prediction.

    Args:
        event (EventCommon): NewMessage event
    """
    try:
        sender = await event.get_sender()
        SENDER = sender.id

        async with client.conversation(
            await event.get_chat(), exclusive=True
        ) as conv:
            text = (
                "Has reality surprised you this time, eh?"
                " Anyway just enter the id of your prediction; and"
                " an actual outcome of an event."
                " For example: 1; 7"
            )
            await conv.send_message(text)
            response = await conv.get_response(timeout=600)
            if not validate_outcome(response.text):
                await conv.send_message(
                    (
                        "Sorry but your input isn't valid."
                        " Please check that your message consists of"
                        " 2 numbers separated by semicolon and whitespace"
                        " and also make sure your first number is decimal."
                    )
                )
                logger.info("Outcome message isn't valid")
            else:
                list_of_words = response.text.split("; ")
                user_id = SENDER
                # Use the datetime library to the get the date
                # (and format it as DAY/MONTH/YEAR)
                date = datetime.now().strftime("%d/%m/%Y")
                pred_id = list_of_words[0]
                actual_outcome = list_of_words[1]

                # Create the tuple "params" with all the parameters inserted
                # by the user
                params = (pred_id, user_id, date, actual_outcome, pred_id)
                sql_command = """UPDATE predictions.raw_predictions SET id=%s,
                user_id=%s, date=%s, actual_outcome=%s WHERE id=%s;"""

                crsr.execute(sql_command, params)  # Execute the query
                conn.commit()  # Commit the changes

                # If at least 1 row is affected by the query we send
                # a specific message
                if crsr.rowcount < 1:
                    text = f"Prediction with id {pred_id} is not present"
                    await client.send_message(SENDER, text, parse_mode="html")
                    logger.info("Enter outcome function was aborted"
                                f" with the text: {text}")
                else:
                    text = (
                        "An actual outcome of an event with "
                        f"id {pred_id} correctly saved"
                    )
                    await client.send_message(SENDER, text, parse_mode="html")
                    logger.debug(text)
        await conv.cancel_all()
        return

    except Exception as e:
        logger.error(
            "Something went wrong when entering an outcome"
            f" with an error: {e}"
        )
        return


@client.on(events.NewMessage(pattern="Check"))
async def check(event):
    """Get user's calibration.

    User can get their overall calibration or choose one
    particular category.

    Args:
        event (EventCommon): NewMessage event
    """
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id

        async with client.conversation(
            await event.get_chat(), exclusive=True
        ) as conv:
            text = (
                "Type all and then enter if you'd like to get your current"
                " overall calibration. In case you're after some specific"
                " area of your life's calibration just type the category"
                " and press enter. So either enter 'all' or e.g. 'work'"
                " as one word without any punctuation."
            )
            await conv.send_message(text)
            response = await conv.get_response(timeout=600)
            ans: str = response.text
            if not validate_calibration(response.text):
                await conv.send_message(
                    (
                        "Sorry but your input isn't valid."
                        " Please make sure it consists of a single word"
                        " without any numbers or punctuation marks."
                    )
                )
                logger.info("Categories request isn't valid")
            else:

                # Execute the query and get all (*) predictions
                if ans.lower() == "all":
                    query = """SELECT tot_acc_50 / tot_num_pred AS calibration_50,
                        tot_acc_90 / tot_num_pred AS calibration_90
                    FROM (
                        SELECT COUNT(id) AS tot_num_pred,
                        SUM(acc_50) AS tot_acc_50,
                        SUM(acc_90) AS tot_acc_90
                    FROM (
                        SELECT
                        id, user_id,
                        pred_low_50_conf <= actual_outcome AND
                        pred_high_50_conf >= actual_outcome AS acc_50,
                        pred_low_90_conf <= actual_outcome AND
                        pred_high_90_conf >= actual_outcome AS acc_90
                        FROM predictions.raw_predictions
                        WHERE user_id = %s AND
                        actual_outcome IS NOT NULL)
                        AS base_table
                    GROUP BY user_id
                    ) AS outer_table;"""
                    crsr.execute(query, [SENDER])
                    res = crsr.fetchall()  # fetch all the results

                    if not res:
                        await client.send_message(
                            SENDER,
                            ("There's currently nothing your calibration"
                             " might possibly be calculated on. Make at least"
                             " one prediction and then enter an actual outcome"
                             " for it."),
                            parse_mode="html")
                        return

                    text = (
                        "Your overall calibration so far:\n"
                        f"for a 50 percent confidence level - {res[0][0]:.2f}"
                        "\n"
                        f"for a 90 percent confidence level - {res[0][1]:.2f}"
                    )
                else:
                    # Or get results for a specific category
                    query = (
                        "SELECT tot_acc_50 / tot_num_pred AS calibration_50,"
                        " tot_acc_90 / tot_num_pred AS calibration_90"
                        " FROM ("
                        "SELECT COUNT(id) AS tot_num_pred,"
                        " SUM(acc_50) AS tot_acc_50,"
                        " SUM(acc_90) AS tot_acc_90"
                        " FROM ("
                        "SELECT"
                        " id, user_id,"
                        " pred_low_50_conf <= actual_outcome AND"
                        " pred_high_50_conf >= actual_outcome AS acc_50,"
                        " pred_low_90_conf <= actual_outcome AND"
                        " pred_high_90_conf >= actual_outcome AS acc_90"
                        " FROM predictions.raw_predictions"
                        " WHERE user_id = %s AND"
                        " task_category = %s AND"
                        " actual_outcome IS NOT NULL)"
                        " AS base_table"
                        " GROUP BY user_id"
                        ") AS outer_table;"
                    )
                    crsr.execute(query, (SENDER, ans))
                    res = crsr.fetchall()  # fetch all the results

                    if not res:
                        await client.send_message(
                            SENDER,
                            ("There's currently nothing your calibration"
                             " might possibly be calculated on. Make at least"
                             " one prediction and then enter an actual outcome"
                             " for it."),
                            parse_mode="html")
                        return

                    text = (
                        "Your overall calibration so far:\n"
                        " for a 50 percent confidence level"
                        f" - {res[0][0]:.2f}\n"
                        f" for a 90 percent confidence level - {res[0][1]:.2f}"
                    )
                await client.send_message(SENDER, text, parse_mode="html")
                logger.debug(f" Check function returned following: {text}")
        await conv.cancel_all()
        return

    except Exception as e:
        logger.error(
            "Something went wrong in calibration's calculation"
            f" with an error: {e}"
        )
        return


@client.on(events.NewMessage(pattern="Delete"))
async def delete(event):
    """Delete one of made predictions specified by an id.

    Args:
        event (EventCommon): NewMessage event
    """
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id

        async with client.conversation(
            await event.get_chat(), exclusive=True
        ) as conv:
            text = "Enter an id for a prediction you are going to delete"
            await conv.send_message(text)
            response = await conv.get_response(timeout=600)
            idn = response.text
            if not validate_deletion(response.text):
                await conv.send_message(
                    (
                        "Sorry but your input isn't valid."
                        " Please make sure it consists of a single"
                        " integer and nothing else."
                    )
                )
                logger.info("Deletion request isn't valid")
            else:

                # Create the DELETE query passing the id as a parameter
                sql_command = """DELETE FROM predictions.raw_predictions
                WHERE id = (%s);"""

                # ans here will be the number of rows affected by the delete
                crsr.execute(sql_command, [idn])
                conn.commit()

                # If at least 1 row is affected by the query we send
                # a specific message
                if crsr.rowcount < 1:
                    text = f"Prediction with id {idn} is not present"
                    await client.send_message(SENDER, text, parse_mode="html")
                    logger.info(f"Deletion was aborted with the text {text}")
                else:
                    text = f"Prediction with id {idn} correctly deleted"
                    await client.send_message(SENDER, text, parse_mode="html")
                    logger.debug(text)
                global COUNTER
                COUNTER -= 1
        await conv.cancel_all()
        return

    except Exception as e:
        logger.error(
            "Something went wrong when deleting user's prediction "
            f"with an error: {e}"
        )
        return


if __name__ == "__main__":
    try:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            filemode="w"
        )
        logger: logging.Logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        handler: RotatingFileHandler = RotatingFileHandler(
            "main.log", maxBytes=50000000, backupCount=5
        )
        logger.addHandler(handler)
        # Создаем форматер
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Применяем его к хэндлеру
        handler.setFormatter(formatter)

        if not check_tokens():
            logger.critical("Bot stopped due missing some token",
                            exc_info=1
                            )
            sys.exit(2)

        # Connect to the database
        conn = mysql.connector.connect(
            host=HOST, user=USER, password=PASSWORD, database=DATABASE
        )

        # Create a cursor
        crsr = conn.cursor()

        # Command that creates the "raw_predictions" table
        sql_command = """CREATE TABLE IF NOT EXISTS raw_predictions (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            user_id VARCHAR(20),
            date VARCHAR(100),
            task_description VARCHAR(200),
            task_category VARCHAR(50),
            unit_of_measure VARCHAR(30),
            pred_low_50_conf FLOAT(10),
            pred_high_50_conf FLOAT(10),
            pred_low_90_conf FLOAT(10),
            pred_high_90_conf FLOAT(10),
            actual_outcome FLOAT(10));"""

        crsr.execute(sql_command)
        logger.info("All tables are ready")

        crsr.execute("SELECT COUNT(*) FROM predictions.raw_predictions;")
        COUNTER = crsr.fetchall()[0][0]

        logger.info("Bot Started...")
        client.run_until_disconnected()

    except Exception as error:
        client.send_message('me', "Bot isn't working!!")
        logger.fatal("Bot isn't working due to a %s", error, exc_info=1)

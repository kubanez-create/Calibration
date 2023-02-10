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
from alternative_helper import one_message
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
TEXT: dict = {}

# Start the Client (telethon)
client = TelegramClient(
    SESSION_NAME, API_ID, API_HASH
).start(bot_token=TELEGRAM_TOKEN)


class State(Enum):
    WAIT_CHECK = auto()
    WAIT_UPDATE = auto()
    WAIT_ENTER = auto()
    WAIT_DELETE = auto()
    WAIT_ADD_PREDICTION = auto()
    WAIT_ADD_CATEGORY = auto()
    WAIT_ADD_UNIT = auto()
    WAIT_ADD_LOW_50 = auto()
    WAIT_ADD_HI_50 = auto()
    WAIT_ADD_LOW_90 = auto()
    WAIT_ADD_HI_90 = auto()
    WAIT_ADD_FINAL = auto()
    WAIT_ADD_SAVE = auto()
    WAIT_ADD_REDO = auto()


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


@client.on(events.NewMessage(pattern="Мои"))
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
                "Складывается впечатление, что вы еще не внесли ни одного"
                " предсказания. Попробуйте."
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

# Detail view block: update, delete, list, enter outcome methods
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
                logger.info(
                    "Someone tried to get a list of categories"
                    " but have not made any themselves.")

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
                logger.info(
                    "Someone tried to update a someone else's prediction "
                )
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
                     " Вами предсказаний. Пожалуйста внесите корректный номер."
                     )
                )
                del conversation_state[who]
                logger.info(
                    "Someone tried to enter outcome for a someone else's"
                    " prediction."
                )
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
    # DELETE METHOD
    elif re.match(r"Удалить", mes):
        conversation_state[who] = State.WAIT_DELETE
        text = (
            "Для того, чтобы удалить ранее сделанное предсказание,"
            " отправьте его номер в ответном сообщении."
            )
        await event.respond(text)
    elif state == State.WAIT_DELETE:
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
            logger.info("Someone tried to delete a prediction"
                        " without making at least one themselves")

        if not validate_outcome(mes):
            await client.send_message(
                (
                    "К сожалению, Ваше сообщение не похоже на цифру."
                    " Что именно Вы пытаетесь отправить? Попробуйте отправить"
                    " номер предсказания, которое вы пытаетесь удалить еще раз,"
                    " пожалуйста."
                )
            )
            logger.info("Outcome message isn't valid")
            del conversation_state[who]

        else:
            mes_list = [str(x) for x in chain.from_iterable(user_predictions)]
            pred_id = mes_list[0]
            if pred_id not in mes_list:
                await client.send_message(
                    who,
                    ("Номер предсказания не совпадает ни с одним из сделанных"
                     " Вами предсказаний. Пожалуйста внесите корректный номер.")
                )
                del conversation_state[who]
                logger.info(
                    "Someone tried to deleto a someone else's prediction."
                )
            else:
                # Create the DELETE query passing the id as a parameter
                sql_command = """DELETE FROM predictions.raw_predictions
                WHERE id = (%s);"""

                # ans here will be the number of rows affected by the delete
                crsr.execute(sql_command, [pred_id])
                conn.commit()
                global COUNTER
                COUNTER -= 1
                await client.send_message(
                    who,
                    (f"Предсказание с номером {pred_id}"
                     " успешно удалено.")
                )
                logger.info(
                    f"Prediction with id {pred_id}"
                    "successfully deleted")
                del conversation_state[who]


@client.on(events.NewMessage(pattern="Добавить"))
async def add_prediction(event):
    """Add new prediction.

    Args:
        event (EventCommon): NewMessage event
    """
    sender = await event.get_sender()
    SENDER = sender.id
    state = conversation_state.get(SENDER)
    mes = event.message.raw_text
    if state is None:
        conversation_state[SENDER] = State.WAIT_ADD_PREDICTION
        await client.send_message(
            SENDER,
            ("Отправьте текст предсказания - что должно произойти, по"
             " Вашему мнению.\nДалее следуйте подсказкам"),
            buttons=[
                Button.inline(
                    "Предсказание",
                    data="Добавить текст предсказания"
                )
            ]
        )
    elif state == State.WAIT_ADD_PREDICTION:
        TEXT['prediction'] = mes
        conversation_state[SENDER] = State.WAIT_ADD_CATEGORY
        await client.send_message(
            SENDER,
            ("Отправьте категорию предсказания для того, чтобы у Вас"
             " была возможность уточнить свою калибровку не только по всем"
             " сохраненным предсказаниям, но и по отдельной категории.\n"
             "Это может быть полезно, т.к. мы можем быть одновременно"
             " великолепно калиброваны во всех, например, рабочих вопросах, но"
             " быть ужасно калиброваны в вопросах касающихся"
             " взаимоотношений с людьми.\nДля того, чтобы иметь возможность"
             " совершенствоваться, нужно понимать, в какой сфере мы не"
             " совершенны. Отправьте одно слово, характеризующее категорию."
             ),
            buttons=[
                Button.inline("Категория", data="Добавить текст категории")
            ]
        )
    elif state == State.WAIT_ADD_CATEGORY:
        TEXT['category'] = mes
        conversation_state[SENDER] = State.WAIT_ADD_UNIT
        await client.send_message(
            SENDER,
            ("В будущем может так случиться, что Вы захотите узнать"
             " в каких единицах Вы вносили данное предсказание. Чтобы"
             " такая возможность у Вас была - отправьте одно слово,"
             " обозначающее единицу измерения. Например: час, день,"
             " ребёнки."
             ),
            buttons=[
                Button.inline(
                    "Единицы измерения",
                    data="Добавить единицу измерения"
                )
            ]
        )
    elif state == State.WAIT_ADD_UNIT:
        TEXT['unit'] = mes
        conversation_state[SENDER] = State.WAIT_ADD_LOW_50
        await client.send_message(
            SENDER,
            ("Отправьте цифру, соответствующую нижней границе, которую"
             " может принять предсказанная величина с уверенностью 50%."
             "Одна цифра и ничего более."
             ),
            buttons=[
                Button.inline(
                    "Нижняя граница при 50% уверенности",
                    data="Добавить ниж границу 50"
                )
            ]
        )
    elif state == State.WAIT_ADD_LOW_50:
        TEXT['low_50'] = mes
        conversation_state[SENDER] = State.WAIT_ADD_HI_50
        await client.send_message(
            SENDER,
            ("Отправьте цифру, соответствующую верхней границе, которую"
             " может принять предсказанная величина с уверенностью 50%."
             "Одна цифра и ничего более."
             ),
            buttons=[
                Button.inline(
                    "Верхняя граница при 50% уверенности",
                    data="Добавить вер границу 50"
                )
            ]
        )
    elif state == State.WAIT_ADD_HI_50:
        TEXT['hi_50'] = mes
        conversation_state[SENDER] = State.WAIT_ADD_LOW_90
        await client.send_message(
            SENDER,
            ("Отправьте цифру, соответствующую нижней границе, которую"
             " может принять предсказанная величина с уверенностью 90%."
             "Одна цифра и ничего более."
             ),
            buttons=[
                Button.inline(
                    "Нижняя граница при 90% уверенности",
                    data="Добавить ниж границу 90"
                )
            ]
        )
    elif state == State.WAIT_ADD_LOW_90:
        TEXT['low_90'] = mes
        conversation_state[SENDER] = State.WAIT_ADD_HI_90
        await client.send_message(
            SENDER,
            ("Отправьте цифру, соответствующую верхней границе, которую"
             " может принять предсказанная величина с уверенностью 90%."
             "Одна цифра и ничего более."
             ),
            buttons=[
                Button.inline(
                    "Верхняя граница при 90% уверенности",
                    data="Добавить вер границу 90"
                )
            ]
        )
    elif state == State.WAIT_ADD_HI_90:
        await client.send_message(
            SENDER,
            ("Проверьте, пожалуйста, получившееся предсказание."
             " Если все верно - нажмите <Сохранить>, если нет - "
             " нажмите на кнопку <Внести повторно>"
             ),
            buttons=[
                Button.inline(
                    "Сохранить",
                    data="Добавить сохранить"
                ),
                Button.inline(
                    "Внести повторно",
                    data="Добавить повторно"
                )
            ]
        )


@client.on(events.CallbackQuery(data=re.compile(r"Добавить сохранить")))
async def show(event):
    try:
        global TEXT
        sender = await event.get_sender()
        SENDER = sender.id
        user_id = SENDER
        date = datetime.now().strftime("%d/%m/%Y")
        task_description = TEXT['prediction']
        task_category = TEXT['category']
        unit_of_measure = TEXT['unit']
        pred_low_50_conf = TEXT['low_50']
        pred_high_50_conf = TEXT['hi_50']
        pred_low_90_conf = TEXT['low_90']
        pred_high_90_conf = TEXT['hi_90']
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
        await client.send_message(
            SENDER,
            "Предсказание успешно сохранено"
        )
        global COUNTER
        COUNTER += 1
        del conversation_state[SENDER]
        del TEXT

    except Exception as e:
        logging.error(
            "Something went wrong when inserting a new prediction "
            f"with an error: {e}"
        )


@client.on(events.CallbackQuery(data=re.compile(r"Добавить повторно")))
async def show_again(event):
    """Add new prediction again.

    Args:
        event (EventCommon): NewMessage event
    """
    sender = await event.get_sender()
    SENDER = sender.id
    state = conversation_state.get(SENDER)
    if state is None or state == State.WAIT_ADD_HI_90:
        conversation_state[SENDER] = State.WAIT_ADD_PREDICTION
        await client.send_message(
            SENDER,
            ("Отправьте текст предсказания - что должно произойти, по"
             " Вашему мнению.\nДалее следуйте подсказкам"),
            buttons=[
                Button.inline(
                    "Предсказание",
                    data="Добавить текст предсказания"
                )
            ]
        )
        global TEXT
        del TEXT


# LIST METHOD
@client.on(events.NewMessage(pattern="Показать"))
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
                    Button.inline("Предыдущий", data=backward),
                    Button.inline("Следующий", data=forward),
                ]
            )
            with tempfile.TemporaryDirectory() as tmpdirname:
                text = create_message_select_query(res)
                converter(text, tmpdirname)
                await client.send_file(
                    SENDER,
                    f'{tmpdirname}/out.jpg',
                    buttons=button)
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

    except Exception as e:
        logger.error(
            f"Something went wrong when showing page {page} user's predictions"
            f" with an error: {e}"
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

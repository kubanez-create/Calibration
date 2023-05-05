"""Telegram bot which keeps track of your predictions."""

from __future__ import annotations

import logging
import os
import re
import sys
from datetime import datetime
from enum import Enum, auto
from itertools import chain
from logging.handlers import RotatingFileHandler

import mysql.connector
from dotenv import load_dotenv

# pip install telethon
from telethon import Button, TelegramClient, events

from alternative_helper import (
    one_message,
    create_message_select_query,
    create_message_categories,
    check_click,
    err_message,
)
from validators import (
    validate_checking,
    validate_outcome,
    validate_updating,
    validate_deletion,
)

load_dotenv()

TELEGRAM_TOKEN: str = str(os.getenv("TELEGRAM_TOKEN"))
API_HASH: str = str(os.getenv("API_HASH"))
API_ID: int = int(os.getenv("API_ID"))
USER: str = str(os.getenv("USER"))
PASSWORD: str = str(os.getenv("PASSWORD"))
HOST: str = str(os.getenv("HOST"))
PORT: str = str(os.getenv("PORT"))
DATABASE: str = str(os.getenv("DATABASE"))

SESSION_NAME: str = "sessions/conBot"
CHUNK_SIZE: int = 10
COUNTER: int = None
TEXT: dict = {}

# Start the Client (telethon)
client = TelegramClient(SESSION_NAME, API_ID, API_HASH).start(bot_token=TELEGRAM_TOKEN)


class State(Enum):
    """User' states."""

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
            [Button.text("Обновить предсказание"), Button.text("Удалить предсказание")],
            [
                Button.text("Результат предсказания"),
                Button.text("Проверить калибровку"),
            ],
            [Button.text("Мои категории"), Button.text("Как пользоваться")],
        ]
    )

    text = (
        "Привет! Здесь можно оставлять предсказания, записывать, что случилось"
        " в реальности, проверять и, мы все надеемся, -  улучшать свою"
        " калибровку. Начните знакомство с ботом нажав кнопку <i>Как"
        " пользоваться</i>. За ней Вы найдете краткую инструкцию к данному"
        " боту."
    )
    await client.send_message(SENDER, text, buttons=markup, parse_mode="html")
    logger.info("Looks like we have a new user!", exc_info=1)


@client.on(events.NewMessage(pattern="Как"))
async def guide(event):
    """Show to a user 'help page'.

    With possible commands and their use cases.

    Args:
        event (EventCommon): NewMessage event
    """
    SMILE_MAIN: str = "\U0001F535"
    SMILE_INFO: str = "\U00002139"
    try:
        text = (
            "Целью создания данного бота был сбор Ваших предсказаний"
            ", сохранение их, чтобы Вы смогли проверить насколько"
            " хорошо Вы калиброваны в целом и/или в какой-то отдельной"
            " категории.\n\nЧто означают кнопки, которые Вы видите внизу:\n"
            f"{SMILE_MAIN} <b>Чтобы добавить новое предсказание</b> - нажмите"
            " на кнопку <i>Добавить предсказание</i>; \n\n"
            f"{SMILE_MAIN} Для того, чтобы удалить, обновить или внести итог"
            " ранее сделанного предсказания Вам понадобится <b>уточнить"
            " номер</b> этого предсказания. Для этого нажмите на кнопку"
            " <i>Показать предсказания</i>;\n\n"
            f"{SMILE_MAIN} <b>Для того, чтобы обновить ранее сделанное"
            " предсказание (обычно в свете некоторых новых наблюдений)</b>"
            " - нажмите на кнопку <i>Обновить предсказание</i>;\n\n"
            f"{SMILE_MAIN} <b>В случае, если в процессе добавления новое"
            " предсказания Вы совершили больше ошибок, нежели то дозволяет"
            " Ваша натура перфекциониста</b> - нажмите на кнопку <i>Удалить"
            " предсказание</i> и затем внесите Ваше предсказание заново;\n\n"
            f"{SMILE_MAIN} <b>После того как Вы узнали, чем в реальности"
            " обернулись предсказанные Вами события</b> - нажмите на кнопку"
            " <i>Результат предсказания</i>;\n\n"
            f"{SMILE_MAIN} <b>Наконец, для того, чтобы уточнить свою"
            " калибровку на основе внесенных ранее предсказаний с"
            " известным исходом</b> - нажмите на кнопку <i>Проверить"
            " калибровку</i> и следуйте дальнейшим инструкциям;\n\n"
            f"{SMILE_INFO} Если же, по какой-то причине, Вы начали"
            " пользоваться данным ботом и ощутили желание поучаствовать в"
            " улучшении его фунциональности или высказать автору что за полный"
            " отстой он создал (даже в змейку не поиграешь) - отправьте мне"
            " письмо по адресу kubanez74@gmail.com."
        )
        await event.respond(text, parse_mode="html")

    except Exception as e:
        logger.error(
            ("Something went wrong when showing help page" f" with an error: {e}")
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
            await err_message(client, parse_mode="html", del_state=False)
            logger.debug(
                "Someone tried to have a look at their categories"
                " without any made predictions."
            )

    except Exception as e:
        logger.error(
            "Something went wrong when showing user's predictions "
            f"with an error: {e}"
        )
        return


# Detail view block: update, delete, list, enter outcome methods
@client.on(events.NewMessage(pattern=validate_checking))
async def CUEDhandler(event):
    """Handle update, delete, list, create and enter outcome methods.

    We check what message we've got and change a user's state.
    If the message isn't trigger state's change and a user alreade
    has a state we process given message in a subsequent method
    below.

    Args:
        event (EventCommon): NewMessage event
    """
    sender = await event.get_sender()
    who = sender.id
    mes = event.message.raw_text
    global TEXT

    # CHECK CALIBRATION
    if re.match(r"Проверить", mes):
        conversation_state[who] = State.WAIT_CHECK
        text = (
            "Если Вы хотели бы проверить общую калибровку по всем сделанным"
            " предсказаниям - отправьте слово общая.\n\n Если Вас интересует"
            " калибровка по какой-то отдельной категории - отправьте"
            " название данной категории. Например, можно отправить <общая>"
            " или <работа> или <политика> без кавычек и/или знаков препинания."
        )
        await event.respond(text)
        return

    if re.match(r"Обновить", mes):
        conversation_state[who] = State.WAIT_UPDATE
        text = (
            "Для того, чтобы обновить ранее внесенное предсказание ("
            "изменить нижнюю и верхнюю границу предсказанного значения),"
            " обычно в свете нового знания, внесите номер предсказания,"
            " которое Вы желаете обновить и затем 4 цифры, разделенные"
            " точкой с запятой и пробелом - новую нижнюю и верхнюю границы"
            " для 50% и 90% уровней уверенности.\n\nНапример: 1; 3; 5; 1; 8"
        )
        await event.respond(text)
        return

    if re.match(r"Результат", mes):
        conversation_state[who] = State.WAIT_ENTER
        text = (
            "Для того чтобы внести результат предсказания, отправьте две"
            " цифры - номер предсказания и итог, например - <17; 0.00008>"
            " без кавычек."
        )
        await event.respond(text)
        return

    if re.match(r"Удалить", mes):
        conversation_state[who] = State.WAIT_DELETE
        text = (
            "Для того, чтобы удалить ранее сделанное предсказание,"
            " отправьте его номер в ответном сообщении."
        )
        await event.respond(text)
        return

    if re.match("Добавить", mes):
        conversation_state[who] = State.WAIT_ADD_PREDICTION
        await client.send_message(
            who,
            (
                "Отправьте текст предсказания - что должно произойти, по"
                " Вашему мнению.\n\nДалее следуйте подсказкам"
            ),
        )
        return

    # CHECK CALIBRATION
    if conversation_state.get(who) == State.WAIT_CHECK:
        query = (
            "SELECT DISTINCT task_category FROM"
            " predictions.raw_predictions WHERE user_id = %s"
        )
        crsr.execute(query, [who])
        res = crsr.fetchall()  # fetch all the results
        # If there is no categories yet, print a warning
        if not res:
            await err_message(client, who, parse_mode="html", state_dict=conversation_state)
            return
        else:
            cat_list = [a for a in chain.from_iterable(res)] + ["общая", "Общая"]
            if mes.lower() not in cat_list:
                await err_message(
                    client,
                    who,
                    state_dict=conversation_state,
                    mess=(
                        "Вы не создали ни одного предсказания в данной" " категории."
                    ),
                )
                logger.info(
                    "Someone tried to get a list of categories"
                    " but have not made any themselves."
                )
                return

            else:
                if mes.lower() == "общая":
                    query = """SELECT tot_acc_50 / tot_num_pred AS
                            calibration_50,
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
                        "Ваша общая калибровка на текущий момент:"
                        f"для 50% уровня уверенности - {res[0][0]:.2f}"
                        "\n"
                        f"для 90% уровня уверенности - {res[0][1]:.2f}"
                    )
                else:
                    # Or get results for a specific category
                    query = (
                        "SELECT tot_acc_50 / tot_num_pred AS"
                        " calibration_50,"
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
                    crsr.execute(query, (who, mes.lower()))
                    res = crsr.fetchall()  # fetch all the results
                    if not res:
                        text = (
                            "В данной категории у Вас нет ни одного"
                            " предсказания с известным исходом."
                            " Расчет калибровки пока не возможен."
                        )
                    else:
                        text = (
                            "Ваша калибровка для выбранной категории"
                            " на текущий момент составляет:\n\n"
                            f"для 50% уровня уверенности - {res[0][0]:.2f}"
                            "\n"
                            f"для 90% уровня уверенности - {res[0][1]:.2f}"
                        )
                await client.send_message(who, text, parse_mode="html")
                del conversation_state[who]
                logger.debug(f" Check function returned following: {text}")
                return

    # UPDATE METHOD
    if conversation_state.get(who) == State.WAIT_UPDATE:
        query = "SELECT id FROM" " predictions.raw_predictions WHERE user_id = %s"
        crsr.execute(query, [who])
        user_predictions = crsr.fetchall()  # fetch all the results
        # If there is no categories yet, print a warning
        if not user_predictions:
            await err_message(client, who, state_dict=conversation_state)
            logger.info(
                "Someone tried to update a prediction without"
                "making at least one themselve"
            )
            return
        if not validate_updating(mes):
            await err_message(
                client,
                who,
                parse_mode="html",
                mess=(
                    "К сожалению, отправленное вами сообщение не похоже на"
                    " 5 цифр, разделенных точкой с запятой и пробелом.\n\n"
                    "Проверьте ваше сообщение, нажмите еще раз на кнопку"
                    " <i>Обновить предсказание</i> и отправьте сообщение с"
                    " обновленными цифрами еще раз."
                ),
                state_dict=conversation_state,
            )
            logger.info("Update message isn't valid")
            return
        else:
            mes_list = [str(x) for x in chain.from_iterable(user_predictions)]
            message = mes.split("; ")
            index = message[0]
            low_50 = message[1]
            hi_50 = message[2]
            low_90 = message[3]
            hi_90 = message[4]
            if index not in mes_list:
                await err_message(
                    client,
                    who,
                    mess=(
                        "Номер предсказания не совпадает ни с одним из"
                        " сделанных Вами предсказаний. Пожалуйста"
                        " внесите корректный номер."
                    ),
                    state_dict=conversation_state,
                )
                logger.info("Someone tried to update a someone else's prediction.")
                return
            else:
                params = (low_50, hi_50, low_90, hi_90, index)
                sql_command = """UPDATE predictions.raw_predictions SET
                pred_low_50_conf=%s, pred_high_50_conf=%s,
                pred_low_90_conf=%s, pred_high_50_conf=%s
                WHERE id=%s;"""

                crsr.execute(sql_command, params)  # Execute the query
                conn.commit()  # Commit the changes
                await client.send_message(
                    who, f"Предсказание с номером {index} успешно обновлено."
                )
                logger.info(f"Prediction with id {index} successfully updated")
                del conversation_state[who]
                return

    # ENTER OUTCOME
    if conversation_state.get(who) == State.WAIT_ENTER:
        query = "SELECT id FROM" " predictions.raw_predictions WHERE user_id = %s"
        crsr.execute(query, [who])
        user_predictions = crsr.fetchall()  # fetch all the results
        # If there is no categories yet, print a warning
        if not user_predictions:
            await err_message(client, who, state_dict=conversation_state)
            logger.info(
                "Someone tried to enter an outcome of a prediction"
                " without making at least one themselve"
            )
            return

        if not validate_outcome(mes):
            await err_message(
                client,
                who,
                mess=(
                    "К сожалению Ваше сообщение не похоже на две цифры,"
                    " разделенные точкой с запятой и пробелом. Пожалуйста"
                    " повторно нажмите на кнопку <i>Результат предсказания"
                    "</i>, исправьте текст сообщения и отправьте его"
                    " еще раз."
                ),
                state_dict=conversation_state,
                parse_mode="html",
            )
            logger.info("Outcome message isn't valid")
            return

        else:
            mes_list = [str(x) for x in chain.from_iterable(user_predictions)]
            list_of_words = mes.split("; ")
            pred_id = list_of_words[0]
            actual_outcome = list_of_words[1]

            if pred_id not in mes_list:
                await err_message(
                    client,
                    who,
                    mess=(
                        "Номер предсказания не совпадает ни с одним из"
                        " сделанных Вами предсказаний. Пожалуйста"
                        " внесите корректный номер."
                    ),
                    state_dict=conversation_state,
                )
                logger.info(
                    (
                        "Someone tried to enter outcome for a someone else's"
                        " prediction."
                    )
                )
                return
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
                    (f"Результат предсказание с номером {pred_id}" " успешно внесен."),
                )
                logger.info(
                    f"Outcome of the prediction with id {pred_id}"
                    "successfully entered"
                )
                del conversation_state[who]
                return

    # DELETE METHOD
    elif conversation_state.get(who) == State.WAIT_DELETE:
        query = "SELECT id FROM" " predictions.raw_predictions WHERE user_id = %s"
        crsr.execute(query, [who])
        user_predictions = crsr.fetchall()  # fetch all the results
        # If there is no categories yet, print a warning
        if not user_predictions:
            await err_message(client, who)
            await client.send_message(who, text, parse_mode="html")
            logger.info(
                "Someone tried to delete a prediction"
                " without making at least one themselves"
            )
            return

        if not validate_deletion(mes):
            await err_message(
                client,
                who,
                mess=(
                    "К сожалению, Ваше сообщение не похоже на цифру."
                    " Что именно Вы пытаетесь отправить? Попробуйте"
                    " отправить номер предсказания, которое вы"
                    " пытаетесь удалить еще раз, пожалуйста."
                ),
                state_dict=conversation_state,
            )
            logger.info("Outcome message isn't valid")
            return

        else:
            mes_list = [str(x) for x in chain.from_iterable(user_predictions)]
            pred_id = mes_list[0]
            if pred_id not in mes_list:
                await err_message(
                    client,
                    who,
                    mess=(
                        "Номер предсказания не совпадает ни с одним из"
                        " сделанных Вами предсказаний. Пожалуйста"
                        " внесите корректный номер."
                    ),
                    state_dict=conversation_state,
                )
                logger.info("Someone tried to deleto a someone else's prediction.")
                return
            else:
                # Create the DELETE query passing the id as a parameter
                sql_command = """DELETE FROM predictions.raw_predictions
                WHERE id = (%s);"""

                crsr.execute(sql_command, [pred_id])
                conn.commit()
                await client.send_message(
                    who, (f"Предсказание с номером {pred_id} успешно удалено.")
                )
                logger.info(f"Prediction with id {pred_id} successfully deleted")
                del conversation_state[who]
                return

    # ADD PREDICTION METHOD
    if conversation_state.get(who) == State.WAIT_ADD_PREDICTION:
        if check_click(mes):
            global TEXT
            TEXT = {}
            TEXT["prediction"] = mes
            BLACK_HEART = "\U0001F5A4"
            SMILE_INFO: str = "\U00002139"
            DEFAULT_ERROR_MESSAGE: str = (
                "Прошу простить мне мое занудство, но нажимать"
                " на случайные кнопки в середине разговора не лучший"
                " метод улучшить собственную калибровку."
                "Нажмите на любую кнопку сейчас и продолжите."
            )
            conversation_state[who] = State.WAIT_ADD_CATEGORY
            await client.send_message(
                who,
                (
                    "Отправьте категорию предсказания для того, чтобы у Вас"
                    " была возможность уточнить свою калибровку не только по"
                    " всем сохраненным предсказаниям, но и по отдельной"
                    f" категории.\n\n{SMILE_INFO}Это может быть полезно,"
                    " т.к. мы можем быть одновременно великолепно калиброваны"
                    " во всех, например, рабочих вопросах, но быть ужасно"
                    " калиброваны в вопросах касающихся взаимоотношений"
                    f" с людьми{BLACK_HEART}\n\nДля того, чтобы иметь"
                    " возможность совершенствоваться, нужно понимать, в"
                    " какой сфере мы не совершенны. Отправьте одно слово,"
                    " характеризующее категорию."
                ),
            )
            return
        else:
            await err_message(client, who, mess=DEFAULT_ERROR_MESSAGE)
            return
    elif conversation_state.get(who) == State.WAIT_ADD_CATEGORY:
        if check_click(mes):
            TEXT["category"] = mes
            conversation_state[who] = State.WAIT_ADD_UNIT
            await client.send_message(
                who,
                (
                    "В будущем может так случиться, что Вы захотите узнать"
                    " в каких единицах Вы вносили данное предсказание. Чтобы"
                    " такая возможность у Вас была - отправьте одно слово,"
                    " обозначающее единицу измерения. Например: час, день,"
                    " ребёнки."
                ),
            )
            return
        else:
            await err_message(client, who, mess=DEFAULT_ERROR_MESSAGE)
            return
    elif conversation_state.get(who) == State.WAIT_ADD_UNIT:
        if check_click(mes):
            TEXT["unit"] = mes
            conversation_state[who] = State.WAIT_ADD_LOW_50
            await client.send_message(
                who,
                (
                    "Отправьте число, соответствующее нижней границе, которую"
                    " может принять предсказанная величина с уверенностью"
                    " в 50%. Одно число и ничего более."
                ),
            )
            return
        else:
            await err_message(client, who, mess=DEFAULT_ERROR_MESSAGE)
            return
    elif conversation_state.get(who) == State.WAIT_ADD_LOW_50:
        if check_click(mes):
            TEXT["low_50"] = mes
            conversation_state[who] = State.WAIT_ADD_HI_50
            await client.send_message(
                who,
                (
                    "Отправьте число, соответствующее верхней границе, которую"
                    " может принять предсказанная величина с уверенностью"
                    " в 50%. Одно число и ничего более."
                ),
            )
            return
        else:
            await err_message(client, who, mess=DEFAULT_ERROR_MESSAGE)
            return
    elif conversation_state.get(who) == State.WAIT_ADD_HI_50:
        if check_click(mes):
            TEXT["hi_50"] = mes
            conversation_state[who] = State.WAIT_ADD_LOW_90
            await client.send_message(
                who,
                (
                    "Отправьте число, соответствующую нижней границе, которую"
                    " может принять предсказанная величина с уверенностью"
                    " в 90%. Одно число и ничего более."
                ),
            )
            return
        else:
            await err_message(client, who, mess=DEFAULT_ERROR_MESSAGE)
            return
    elif conversation_state.get(who) == State.WAIT_ADD_LOW_90:
        if check_click(mes):
            TEXT["low_90"] = mes
            conversation_state[who] = State.WAIT_ADD_HI_90
            await client.send_message(
                who,
                (
                    "Отправьте цифру, соответствующую верхней границе, которую"
                    " может принять предсказанная величина с уверенностью"
                    " в 90%. Одна цифра и ничего более."
                ),
            )
            return
        else:
            await err_message(client, who, mess=DEFAULT_ERROR_MESSAGE)
            return
    elif conversation_state.get(who) == State.WAIT_ADD_HI_90:
        if check_click(mes):
            TEXT["hi_90"] = mes
            mess = one_message(TEXT)
            await client.send_message(
                who,
                (
                    "Проверьте, пожалуйста, получившееся предсказание."
                    " Если все верно - нажмите <i>Сохранить</i>, если нет - "
                    " нажмите на кнопку </i>Внести повторно</i>\n\n"
                    f"{mess}"
                ),
                buttons=[
                    Button.inline("Сохранить", data="Добавить сохранить"),
                    Button.inline("Внести повторно", data="Добавить повторно"),
                ],
                parse_mode="html",
            )
            return
        else:
            await err_message(client, who, mess=DEFAULT_ERROR_MESSAGE)
            return


@client.on(events.CallbackQuery(data=re.compile(r"Добавить сохранить")))
async def add(event):
    """Save user's prediction.

    Args:
        event (EventCommon): NewMessage event
    """
    try:
        global TEXT
        sender = await event.get_sender()
        SENDER = sender.id
        user_id = SENDER
        date = datetime.now().strftime("%d/%m/%Y")
        task_description = TEXT["prediction"]
        task_category = TEXT["category"].lower()
        unit_of_measure = TEXT["unit"]
        pred_low_50_conf = TEXT["low_50"]
        pred_high_50_conf = TEXT["hi_50"]
        pred_low_90_conf = TEXT["low_90"]
        pred_high_90_conf = TEXT["hi_90"]
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
        await client.send_message(SENDER, "Предсказание успешно сохранено")
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
            (
                "Отправьте текст предсказания - что должно произойти, по"
                " Вашему мнению.\n\nДалее следуйте подсказкам"
            ),
        )
        global TEXT
        del TEXT


# LIST METHOD
@client.on(events.NewMessage(pattern="Показать"))
async def display(event):
    """Give a choice to a user about what they's like to see.

    Their choices are:
    - whole list with and without known results;
    - partial list containing only prediction w/o results.

    Args:
        event (EventCommon): NewMessage event
    """
    text = (
        "Выберите пожалуйста - хотели ли бы Вы увидеть все"
        " сохраненные предсказания или же исключительно те,"
        " исход которых еще не внесен."
    )
    sender = await event.get_sender()
    SENDER = sender.id
    await client.send_message(
        SENDER,
        text,
        buttons=[
            Button.inline("Полный список", data="list_whole"),
            Button.inline("Предсказания без результата", data="list_empty"),
        ],
    )


# LIST METHOD FOR A WHOLE LIST OF PREDICTIONS
@client.on(events.CallbackQuery(data=re.compile(b"list_whole")))
async def display_whole(event):
    """Show all predictions to a user.

    Args:
        event (EventCommon): NewMessage event
    """
    try:
        sender = await event.get_sender()
        SENDER = sender.id
        query = "SELECT * FROM predictions.raw_predictions WHERE user_id = %s"
        crsr.execute(query, [SENDER])
        res = crsr.fetchall()
        # If there is at least 1 row selected, print a message with the list
        # of all predictions
        global COUNTER
        COUNTER = len(res)
        if res:
            message = res[0:CHUNK_SIZE]
            if len(res) <= CHUNK_SIZE:
                text = create_message_select_query(message)
                await client.send_message(SENDER, text, parse_mode="html")
            else:
                callback_data = f"page_whole_{1}"
                button = event.client.build_reply_markup(
                    [Button.inline("Next", data=callback_data)]
                )
                text = create_message_select_query(message)
                await client.send_message(
                    SENDER, text, buttons=button, parse_mode="html"
                )

        # Otherwhise, print a default text
        else:
            await err_message(client, SENDER, del_state=False)

    except Exception as e:
        logger.error(
            "Something went wrong when showing user's predictions "
            f"with an error: {e}"
        )
        return


@client.on(events.CallbackQuery(data=re.compile(b"page_whole")))
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
        page = int(event.data.split(b"page_whole_")[1])
        query = (
            "SELECT * FROM predictions.raw_predictions WHERE user_id = %s"
            " LIMIT %s, %s;"
        )
        crsr.execute(query, [SENDER, page * CHUNK_SIZE, CHUNK_SIZE])
        res = crsr.fetchall()  # fetch all the results
        text = create_message_select_query(res)

        if page >= 1 and (COUNTER - page * CHUNK_SIZE) > CHUNK_SIZE:
            forward = f"page_whole_{page + 1}"
            backward = f"page_whole_{page - 1}"
            button = event.client.build_reply_markup(
                [
                    Button.inline("Предыдущий", data=backward),
                    Button.inline("Следующий", data=forward),
                ]
            )

        elif page >= 1 and (COUNTER - page * CHUNK_SIZE) <= CHUNK_SIZE:
            backward = f"page_whole{page - 1}"
            button = event.client.build_reply_markup(
                [
                    Button.inline("Предыдущий", data=backward),
                ]
            )

        await client.send_message(SENDER, text, parse_mode="html", buttons=button)

    except Exception as e:
        logger.error(
            f"Something went wrong when showing page {page} user's predictions"
            f" with an error: {e}"
        )
        return


# LIST METHOD FOR A LIST OF PREDICTIONS W/O OUTCOMES
@client.on(events.CallbackQuery(data=re.compile(b"list_empty")))
async def display_empty(event):
    """Show predictions whithout outcomes to a user.

    Args:
        event (EventCommon): NewMessage event
    """
    try:
        sender = await event.get_sender()
        SENDER = sender.id
        query = (
            "SELECT * FROM predictions.raw_predictions WHERE user_id = %s"
            " AND actual_outcome IS NULL"
        )
        crsr.execute(query, [SENDER])
        res = crsr.fetchall()
        # If there is at least 1 row selected, print a message with the list
        # of all predictions
        global COUNTER
        COUNTER = len(res)
        if res:
            message = res[0:CHUNK_SIZE]
            if len(res) <= CHUNK_SIZE:
                text = create_message_select_query(message)
                await client.send_message(SENDER, text, parse_mode="html")
            else:
                callback_data = f"page_empty_{1}"
                button = event.client.build_reply_markup(
                    [Button.inline("Next", data=callback_data)]
                )
                text = create_message_select_query(message)
                await client.send_message(
                    SENDER, text, buttons=button, parse_mode="html"
                )

        # Otherwhise, print a default text
        else:
            await err_message(client, SENDER, del_state=False)

    except Exception as e:
        logger.error(
            "Something went wrong when showing user's predictions "
            f"with an error: {e}"
        )
        return


@client.on(events.CallbackQuery(data=re.compile(b"page_empty")))
async def show_empty(event):
    """Show to a user their predictions w/o outcomes.

    Activated only if user has more then 10 predictions, using
    ad-hoc pagination.

    Args:
        event (EventCommon): CallbackQuery event
    """
    try:
        sender = await event.get_sender()
        SENDER = sender.id
        page = int(event.data.split(b"page_empty_")[1])
        query = (
            "SELECT * FROM predictions.raw_predictions WHERE user_id = %s"
            " AND actual_outcome IS NULL LIMIT %s, %s;"
        )
        crsr.execute(query, [SENDER, page * CHUNK_SIZE, CHUNK_SIZE])
        res = crsr.fetchall()  # fetch all the results
        text = create_message_select_query(res)

        if page >= 1 and (COUNTER - page * CHUNK_SIZE) > CHUNK_SIZE:
            forward = f"page_empty_{page + 1}"
            backward = f"page_empty_{page - 1}"
            button = event.client.build_reply_markup(
                [
                    Button.inline("Предыдущий", data=backward),
                    Button.inline("Следующий", data=forward),
                ]
            )

        elif page >= 1 and (COUNTER - page * CHUNK_SIZE) <= CHUNK_SIZE:
            backward = f"page_empty{page - 1}"
            button = event.client.build_reply_markup(
                [
                    Button.inline("Предыдущий", data=backward),
                ]
            )

        await client.send_message(SENDER, text, parse_mode="html", buttons=button)

    except Exception as e:
        logger.error(
            f"Something went wrong when showing page {page} user's predictions"
            f" with an error: {e}"
        )
        return


if __name__ == "__main__":
    try:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", filemode="w"
        )
        logger: logging.Logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        handler: RotatingFileHandler = RotatingFileHandler(
            "main.log", maxBytes=50000000, backupCount=5
        )
        logger.addHandler(handler)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        handler.setFormatter(formatter)

        if not check_tokens():
            logger.critical("Bot stopped due missing some token", exc_info=1)
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

        logger.info("Bot Started...")
        client.run_until_disconnected()

    except Exception as error:
        logger.fatal("Bot isn't working due to a %s", error, exc_info=1)

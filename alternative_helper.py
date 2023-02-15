"""Helper functions for the bot."""
from __future__ import annotations

import re

from itertools import chain

SMILES_NUMBER: int = 60
SMALL_DIAMOND = "\U0001F538"
PENCIL = "\U0000270F"
BLACK_SQUARE = "\U000025AA"


def create_message_categories(ans: list[str]):
    """Create a coherent message out of a given categories' list.

    Args:
        ans (list[str]): list of user's categories

    Returns:
        str: message ready to be sent to a user
    """
    return ('Ваши категории: '
            f'{"; ".join(chain.from_iterable(ans))}'
            )


def create_message_select_query(ans):
    """Create a coherent message out of a given predictions' list.

    Args:
        ans (list[str]): list of user's predictions

    Returns:
        str: message ready to be sent to a user
    """
    
    text = ""
    for n, i in enumerate(ans):
        id = i[0]
        date = i[2]
        task_description = i[3]
        task_category = i[4]
        unit_of_measure = i[5]
        pred_low_50_conf = i[6]
        pred_high_50_conf = i[7]
        pred_low_90_conf = i[8]
        pred_high_90_conf = i[9]
        actual_outcome = i[10]

        text += (
            f"<b>№: {str(id)}</b>\n"
            f"<b>{date}</b>\n\n{PENCIL}"
            f" {task_description}\n\n<b>Категория:</b>"
            f" {task_category}\n<b>Единица измерения:</b> {unit_of_measure}\n\n"
            "<b>ГРАНИЦЫ</b>\n"
            f"{SMALL_DIAMOND} <b>Нижняя 50%:</b> {pred_low_50_conf}\n"
            f"{SMALL_DIAMOND} <b>Верхняя 50%:</b> {pred_high_50_conf}\n"
            f"{SMALL_DIAMOND} <b>Нижняя 90%:</b> {pred_low_90_conf}\n"
            f"{SMALL_DIAMOND} <b>Верхняя 90%:</b> {pred_high_90_conf}\n\n"
            f"{BLACK_SQUARE} <b>Результат:</b> {actual_outcome or ''}\n"
            f"{'_' * SMILES_NUMBER}\n\n"
        )
    message = "Предсказания, сделанные Вами на текущий момент:\n\n" + text
    return message


def one_message(ans: dict[str, str]):
    """Create a message to show to a user.

    Args:
        ans (dict[str, str]): dictionary with inputed values
    """
    message = (
        f"{PENCIL} {ans['prediction']}\n\n"
        f"<b>Категория:</b> {ans['category']}\n"
        f"<b>Единица измерения:</b> {ans['unit']}\n\n"
        "<b>ГРАНИЦЫ</b>\n"
        f"{SMALL_DIAMOND} <b>Нижняя 50%:</b> {ans['low_50']}\n"
        f"{SMALL_DIAMOND} <b>Верхняя 50%:</b> {ans['hi_50']}\n"
        f"{SMALL_DIAMOND} <b>Нижняя 90%:</b> {ans['low_90']}\n"
        f"{SMALL_DIAMOND} <b>Верхняя 90%:</b> {ans['hi_90']}"
    )
    return message


def check_click(load: str) -> bool:
    commands = [
        "Добавить предсказание",
        "Обновить предсказание",
        "Удалить предсказание",
        "Результат предсказания",
        "Проверить калибровку"
    ]
    for comm in commands:
        if re.match(comm, load):
            return False
    return True

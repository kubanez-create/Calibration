"""Helper functions for the bot."""
from __future__ import annotations

from itertools import chain

SMILES_NUMBER: int = 20


def create_message_categories(ans: list[str]):
    """Create a coherent message out of a given categories' list.

    Args:
        ans (list[str]): list of user's categories

    Returns:
        str: message ready to be sent to a user
    """
    return ('Зарегистрированные Вами категории:'
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

        text += (
            f"Номер предсказания: <b>{str(id)}</b>\n"
            "Дата предсказания или дата последнего обновления предсказания:"
            f" {date}\nТекст предсказания: {task_description}\n"
            f"Категория предсказания: {task_category}\n"
            f"Единица измерения: {unit_of_measure}\n"
            "Нижняя граница диапазона, в котором с уверенностью в 50% будет"
            f" находиться предсказанное значение: {pred_low_50_conf}\n"
            "Верхняя граница диапазона, в котором с уверенностью в 50% будет"
            f" находиться предсказанное значение:{pred_high_50_conf}\n"
            "Нижняя граница диапазона, в котором с уверенностью в 90% будет"
            f" находиться предсказанное значение: {pred_low_90_conf}\n"
            "Верхняя граница диапазона, в котором с уверенностью в 90% будет"
            f" находиться предсказанное значение: {pred_high_90_conf}\n"
            f"{['%xE2%x9C%x85'] * SMILES_NUMBER}\n"
        )
    message = "Предсказания, сделанные Вами на текущий момент:\n" + text
    return message


def one_message(ans: dict[str, str]):
    """Create a message to show to a user.

    Args:
        ans (dict[str, str]): dictionary with inputed values
    """
    message = (
        f"<b>Текст предсказания:</b> {ans['prediction']}\n"
        f"<b>Категория предсказания:</b> {ans['category']}\n"
        f"<b>Единица измерения:</b> {ans['unit']}\n"
        "<b>Нижняя граница диапазона</b>, в котором с уверенностью в 50% будет"
        f" находиться предсказанное значение: {ans['low_50']}\n"
        "<b>Верхняя граница диапазона</b>, в котором с уверенностью в 50%"
        f" будет находиться предсказанное значение:{ans['hi_50']}\n"
        "<b>Нижняя граница диапазона</b>, в котором с уверенностью в 90%"
        f" будет находиться предсказанное значение: {ans['low_90']}\n"
        "<b>Верхняя граница диапазона</b>, в котором с уверенностью в 90%"
        f" будет находиться предсказанное значение: {ans['hi_90']}\n"
        f"{['%xE2%x9C%x85'] * SMILES_NUMBER}\n"
    )
    return message

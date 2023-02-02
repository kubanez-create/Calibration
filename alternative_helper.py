"""Helper functions for the bot."""
from __future__ import annotations

from itertools import chain


def create_message_categories(ans: list[str]):
    """Create a coherent message out of a given categories' list.

    Args:
        ans (list[str]): list of user's categories

    Returns:
        str: message ready to be sent to a user
    """
    return f'Зарегистрированные Вами категории: {"; ".join(chain.from_iterable(ans))}'


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

        even: str = "even" if n % 2 == 0 else "odd"
        text += (
            f"<tr class={even}><td>{str(id)}</td><td>{date}</td><td>"
            f"{task_description}</td><td>{task_category}</td><td>"
            f"{unit_of_measure}</td><td>{str(pred_low_50_conf)}</td>"
            f"<td>{str(pred_high_50_conf)}</td>"
            f"<td>{str(pred_low_90_conf)}</td>"
            f"<td>{str(pred_high_90_conf)}</td>"
            f"<td>{str(actual_outcome)}</td></tr>"
        )
    message = (
        "<html><head></head><body><table class='center'>"
        "<tr><th>id</th><th>date</th><th>task description</th>"
        "<th>task category</th><th>unit of measure</th>"
        "<th>confidence 50 low</th><th>confidence 50 high</th>"
        "<th>confidence 90 low</th><th>confidence 90 high</th>"
        "<th>outcome</th></tr>"
        f"{text}"
        "</table></body></html>"
    )
    return message

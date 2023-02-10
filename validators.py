"""Validating functions."""

import re


def validate_creating(ans):
    """Validate user provided prediction string.

    Args:
        ans (str): user's prediction string

    Returns:
        bool: whether given prediction string mathes the pattern or not
    """
    return re.fullmatch(
        (
            r"^[a-яА-ЯЁё\w.?,!'\s]{1,200};\s+[a-яА-ЯЁё\w]{1,50};"
            r"\s+[a-яА-ЯЁё\w]{1,30};\s[+-]?(\d*\.)?\d+;\s[+-]?(\d*\.)?"
            r"\d+;\s[+-]?(\d*\.)?\d+;\s[+-]?(\d*\.)?\d+$"
        ),
        ans,
    )


def validate_updating(ans):
    """Validate user provided update string.

    Args:
        ans (str): user's update string

    Returns:
        bool: whether given update string mathes the pattern or not
    """
    return re.fullmatch(
        (
            r"^\d+;\s[+-]?(\d*\.)?\d+;\s[+-]?(\d*\.)?\d+;\s[+-]?(\d*\.)?\d+;"
            r"\s[+-]?(\d*\.)?\d+$"
        ),
        ans,
    )


def validate_checking(string: str):
    commands = [
        "/start",
        "Добавить предсказание",
        "Показать предсказания",
        "Мои категории",
        "Как пользоваться"
    ]
    for comm in commands:
        if re.match(comm, string):
            return False
    return True


def validate_calibration(ans):
    """This function here entirely for the backward compatibility."""
    return True

def validate_deletion(ans):
    """Validate user provided id.

    Args:
        ans (str): user's id

    Returns:
        bool: whether given id mathes the pattern or not
    """
    return re.fullmatch(r"^\d+$", ans)


def validate_outcome(ans: str):
    """Validate user provided string.

    Args:
        ans (str): user's string

    Returns:
        bool: whether given string mathes the pattern or not
    """
    return re.fullmatch(r"^\d+;\s[+-]?(\d*\.)?\d+$", ans)

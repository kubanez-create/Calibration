"""Converter from plain text to an img file."""

import imgkit


def converter(text: str, temp_location):
    """Convert plain text into jpg image.

    Args:
        text (str): plain text for a table
        temp_location (path-like): temporary location storing an image
        with user's predictions 

    Returns:
        bool: whether or not transfomation was successful
    """
    return imgkit.from_string(text, f'{temp_location}/out.jpg',
                              css='table.css')

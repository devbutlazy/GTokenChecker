from typing import Optional, Union, Literal, Tuple
from datetime import datetime
import traceback

import asyncio
import os


def create_needed(
    time: datetime,
) -> Union[tuple[str, ...], Tuple[None, None, None, None]]:
    """
    Create needed files

    :param time: current time
    :return: tuple of file paths
    """
    file_names = [
        "valid_tokens.txt",
        "invalid_tokens.txt",
        "phonelock_tokens.txt",
        "nitro_tokens.txt",
    ]
    formatted_time = format_datetime_humanly(
        date=time, format_string="%d.%m.%Y %H_%M_%S"
    )
    directory_path = f"results/result-{formatted_time}"
    os.makedirs(directory_path, exist_ok=True)

    file_paths = tuple(os.path.join(directory_path, file) for file in file_names)
    for file_path in file_paths:
        with open(file_path, "w"):
            pass

    return file_paths


async def run_tasks(self, tasks: list[asyncio.Task]) -> None:
    """
    Run the given tasks

    :param tasks: the tasks to run
    :return: None
    """
    os.system("cls" if os.name == "nt" else "clear")

    try:
        await asyncio.gather(*tasks)
    except (BaseException, ExceptionGroup) as load_error:
        custom_print(f"An error occurred: {load_error}", color="error", print_bool=True)


def custom_print(
    text: str,
    color: Literal["info", "debug", "error", "warn"] = "warn",
    print_bool: bool = True,
    write_file: bool = False,
    file: Optional[str] = None,
) -> str:
    """
    Print text with colors

    :param text: the text to print
    :param color: the color of the text
    :param print_bool: whether to print the text
    :param write_file: whether to write the text to a file
    :param file: the file to write the text to
    :return: the color of the text
    """
    colors = {
        "info": f"\033[1;32;48m{text}\033[1;37;0m ",
        "debug": f"\033[1;34;48m{text}\033[1;37;0m",
        "error": f"\033[1;31;48m{text}\033[1;37;0m",
        "warn": f"\033[1;33;48m{text}\033[1;37;0m",
    }

    print(colors[color]) if print_bool else None
    if write_file and file:
        write_to_file(info=text, file=file)
    return colors[color]


def write_to_file(info: str, file: str) -> None:
    """
    Write text to file

    :param info: the text to write
    :param file: the file to write the text to
    :return: None
    """
    try:
        if not isinstance(file, (str, os.PathLike)):
            raise ValueError("File must be a string or a path-like object")

        with open(file, "a+", encoding="utf-8") as file:  # type: ignore
            file.write(f"{info}\n")  # type: ignore

    except BaseException as error:
        traceback.print_exc()
        custom_print(f"Error writing to file: {error}", color="error", print_bool=True)


def format_datetime_humanly(
    date: Union[datetime, str], format_string: str = "%d.%m.%Y %H:%M:%S"
) -> str:
    """
    Format datetime to human readable format

    :param date: the datetime to format
    :param format_string: the format string
    :return: the formatted datetime
    """
    if isinstance(date, str):  # mypy moment
        date = datetime.fromisoformat(date)
    return date.strftime(format_string)


def convert_iso_to_human_readable(
    iso: str, format_string: str = "%d.%m.%Y %H:%M:%S"
) -> str:
    """
    Convert ISO format to human readable format

    :param iso: the ISO format
    :param format_string: the format string
    :return: the human readable format
    """
    date = datetime.fromisoformat(iso)
    return format_datetime_humanly(date, format_string)

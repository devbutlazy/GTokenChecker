from typing import Dict, Optional, Union, Literal
from datetime import datetime

import aiofiles
import os

# CONSTANTS


startup_text = """
================================================================================================

   ____   _____    ___    _  __  _____   _   _    ____   _   _   _____   _  __  _____   ____  
  / ___| |_   _|  / _ \  | |/ / | ____| | \ | |  / ___| | | | | | ____| | |/ / | ____| |  _ \ 
 | |  _    | |   | | | | | ' /  |  _|   |  \| | | |     | |_| | |  _|   | ' /  |  _|   | |_) |
 | |_| |   | |   | |_| | | . \  | |___  | |\  | | |___  |  _  | | |___  | . \  | |___  |  _ < 
  \____|   |_|    \___/  |_|\_\ |_____| |_| \_|  \____| |_| |_| |_____| |_|\_\ |_____| |_| \_\

  
================================================================================================
                                                                                              
"""

text = """
~~~~~~~~~~~~~~~ INFO ~~~~~~~~~~~~~~~
Token {masked_token} is valid
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

~~~~~~~~~~~ Account INFO ~~~~~~~~~~~
[ ID ]: {user_id}
[ Name ]: {username}
[ Bio ]: {bio}
[ Locale ]: {locale}
[ Avatar URL ]: {avatar}
[ Banner URL ]: {banner}
[ E-mail ]: {email}
[ E-mail verified bool ] {verified}
[ Phone number ]: {phone}
[ 2FA enabled ]: {mfa}
[ Created at ]: {user_creation}
[ Public Flags ]: {flags}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

~~~~~~~~~~ Nitro INFO ~~~~~~~~~~~~
[ Nitro ]: {premium_type}
[ Nitro started ]: {nitro_start}
[ Nitro ends ]: {nitro_end}
{nitro_credits}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{payments_text}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{guilds_text}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{gifts_text}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{promotions_text}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{connections_text}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{boosts_text}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{rel_text}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{private_channels_text}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

headers = {
    "Accept": "*/*",
    "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
    "Alt-Used": "discord.com",
    "Authorization": "{token}",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Cookie": "__dcfduid=8ae3ca90b4d911ec998447df76ccab6d; "
    "__sdcfduid"
    "=8ae3ca91b4d911ec998447df76ccab6d07a29d8ce7d96383bcbf0ff"
    "12d2f61052dd1691af72d9101442df895f59aa340; "
    "OptanonConsent=isIABGlobal=false&datestamp=Tue+Sep+20+2022+15%3A55%3A24+GMT%2B0200+("
    "hora+de+verano+de+Europa+central)&version=6.33.0&hosts=&landingPath=NotLandingPage"
    "&groups=C0001"
    "%3A1%2CC0002%3A1%2CC0003%3A1&AwaitingReconsent=false&geolocation=ES%3BMD; "
    "__stripe_mid=1798dff8-2674-4521-a787-81918eb7db2006dc53; "
    "OptanonAlertBoxClosed=2022-04-15T16:00:46.081Z; _ga=GA1.2.313716522.1650038446; "
    "_gcl_au=1.1.1755047829.1662931666; _gid=GA1.2.778764533.1663618168; locale=es-ES; "
    "__cfruid=fa5768ee3134221f82348c02f7ffe0ae3544848a-1663682124",
    "Host": "discord.com",
    "Origin": "https://discord.com",
    "Referer": "https://discord.com/app",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "TE": "trailers",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 "
    "Firefox/105.0",
}

sections = {
    "guilds_text": "~~~~~~~~~~ Guilds ~~~~~~~~~~~\n",
    "payments_text": "~~~~~~~~~~ Payments ~~~~~~~~~~\n",
    "gifts_text": "~~~~~~~~~~ Gifts info ~~~~~~~~~~\n",
    "promotions_text": "~~~~~~~~~~ Promotions ~~~~~~~~~~\n",
    "connections_text": "~~~~~~~~~~ Account connections ~~~~~~~~~~\n",
    "boosts_text": "~~~~~~~~~~ Boosts ~~~~~~~~~~\n",
    "rel_text": "~~~~~~~~~~ Relationships ~~~~~~~~~~\n",
    "private_channels_text": "~~~~~~~~~~ Private channels ~~~~~~~~~~\n",
}

friend_type = {
    1: "Friend",
    2: "Block",
    3: "incoming friend request",
    4: "outgoing friend request",
}

flags: Dict[int, str] = {
    1 << 0: "Staff Team",
    1 << 1: "Guild Partner",
    1 << 2: "HypeSquad Events Member",
    1 << 3: "Bug Hunter Level 1",
    1 << 5: "Dismissed Nitro promotion",
    1 << 6: "House Bravery Member",
    1 << 7: "House Brilliance Member",
    1 << 8: "House Balance Member",
    1 << 9: "Early Nitro Supporter",
    1 << 10: "Team Supporter",
    1 << 14: "Bug Hunter Level 2",
    1 << 16: "Verified Bot",
    1 << 17: "Early Verified Bot Developer",
    1 << 18: "Moderator Programs Alumni",
    1 << 19: "Bot uses only http interactions",
    1 << 22: "Active Developer",
}

premium_types = {
    0: "No nitro",
    1: "Nitro Classic",
    2: "Nitro Boost",
}

# BASIC


def create_needed(
    time: datetime,
) -> Union[tuple[str, ...], tuple[None, None, None, None]]:
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


async def custom_print(
    text: str,
    color: Literal["info", "debug", "error", "warn"] = "warn",
    print_bool: bool = True,
    write_file: bool = False,
    file: Optional[str] = None,
) -> str:

    colors = {
        "info": f"\033[1;32;48m{text}\033[1;37;0m ",
        "debug": f"\033[1;34;48m{text}\033[1;37;0m",
        "error": f"\033[1;31;48m{text}\033[1;37;0m",
        "warn": f"\033[1;33;48m{text}\033[1;37;0m ",
    }

    print(colors[color]) if print_bool else None
    if write_file and file:
        await write_to_file(info=text, file=file)
    return colors[color]


async def write_to_file(info: str, file: str) -> None:
    try:
        if not isinstance(file, (str, os.PathLike)):
            raise ValueError("File must be a string or a path-like object")

        async with aiofiles.open(file, "a+", encoding="utf-8", errors="ignore") as file:  # type: ignore
            await file.write(f"{info}\n")  # type: ignore
    except Exception as error:
        await custom_print(
            f"Error writing to file: {error}", color="error", print_bool=True
        )


def format_datetime_humanly(
    date: Union[datetime, str], format_string: str = "%d.%m.%Y %H:%M:%S"
) -> str:
    if isinstance(date, str):  # mypy moment
        date = datetime.fromisoformat(date)
    return date.strftime(format_string)


def convert_iso_to_human_readable(
    iso: str, format_string: str = "%d.%m.%Y %H:%M:%S"
) -> str:
    date = datetime.fromisoformat(iso)
    return format_datetime_humanly(date, format_string)

import os
from datetime import datetime
from json import load
from re import findall
from typing import Any, Coroutine, Dict, List, Literal, Optional, Tuple, Union

import aiofiles
from aiohttp import ClientSession

pattern = r"\b[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"
BASE_URL = "https://discord.com/"

config = load(open("src/config.json", "r"))
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

startup_text = """
   ____   _____    ___    _  __  _____   _   _    ____   _   _   _____   _  __  _____   ____  
  / ___| |_   _|  / _ \  | |/ / | ____| | \ | |  / ___| | | | | | ____| | |/ / | ____| |  _ \ 
 | |  _    | |   | | | | | ' /  |  _|   |  \| | | |     | |_| | |  _|   | ' /  |  _|   | |_) |
 | |_| |   | |   | |_| | | . \  | |___  | |\  | | |___  |  _  | | |___  | . \  | |___  |  _ < 
  \____|   |_|    \___/  |_|\_\ |_____| |_| \_|  \____| |_| |_| |_____| |_|\_\ |_____| |_| \_\
                                                                                              
"""

async def custom_print(
        text: str,
        color: Literal["info", "debug", "error", "warn"] = "warn",
        print_bool: bool = False,
        write_file: bool = False,
        file: str = None,
) -> None:
    colors = {
        "info": f"\033[1;32;48m{text}\033[1;37;0m ",
        "debug": f"\033[1;34;48m{text}\033[1;37;0m",
        "error": f"\033[1;31;48m{text}\033[1;37;0m",
        "warn": f"\033[1;33;48m{text}\033[1;37;0m ",
    }
    if print_bool:
        print(colors[color])
    if write_file and file:
        await write_to_file(info=text, file=file)
    return colors[color]


def count_tokens() -> int:
    with open("src/tokens.txt", "r", errors="ignore") as file:
        lines = file.read()
    return len(findall(pattern, lines))


async def gen_parse_token(tokens: str) -> tuple:
    token_list = findall(pattern, tokens)
    token_count = len(token_list)
    if token_count >= 1:
        return token_list, token_count
    else:
        await custom_print("Please provide at least one token in the 'tokens.txt' file.", color="error", print_bool=True)
        exit(0)


def get_user_flags(public_flags: int) -> List[str]:
    flags_all: List[str] = []

    if config.get("show_flags", False):
        for key, value in flags.items():
            if key & public_flags == key:
                flags_all.append(value)
    else:
        flags_all.append("Enable the \"show_flags\" feature in config.json!")

    return flags_all


def mask_token(token: str) -> str:
    token_segments = token.split(".")
    if len(token_segments) > 1:
        last_segment = token_segments[-1]
        masked_last_segment = "*" * len(last_segment)
        masked_token = ".".join(token_segments[:-1] + [masked_last_segment])
        return masked_token
    else:
        return token


def format_datetime_humanly(
        date: datetime, format_string: Union[datetime.strptime, str] = "%d.%m.%Y %H:%M:%S"
) -> str:
    return date.strftime(format_string)


def convert_iso_to_human_readable(
        iso: str, format_string: Union[datetime.strptime, str] = "%d.%m.%Y %H:%M:%S"
) -> str:
    date = datetime.fromisoformat(iso)
    return format_datetime_humanly(date, format_string)


def get_account_creation(
        snowflake_id: str, to_humanly: bool = True
) -> Union[datetime, str]:
    timestamp = (int(snowflake_id) >> 22) + 1420070400000
    creation_time = datetime.fromtimestamp(timestamp / 1000.0)

    if to_humanly:
        creation_time = format_datetime_humanly(creation_time)

    return creation_time


async def get_tokens() -> tuple[Union[str, Any], int]:
    if not os.path.exists("src/tokens.txt"):
        await custom_print("Error: Please create a 'tokens.txt' file!", color="error", print_bool=True)
        exit(0)
    async with aiofiles.open("src/tokens.txt", "r", errors="ignore") as file:
        lines = await file.read()
    for token in await gen_parse_token(lines):
        return token


async def write_to_file(info: str, file: str) -> None:
    if config.get("write_tokens_to_file", False):
        try:
            async with aiofiles.open(file, "a+", encoding="utf-8", errors="ignore") as file:
                await file.write(f"{info}\n")
        except (Exception, BaseException) as error:
            await custom_print(f"Error writing to file: {error}", color="error", print_bool=True)

    return


async def check_nitro_credit(headers: Dict[str, str]) -> Tuple[int, int]:
    nitro_credits = {"classic_credits": 0, "boost_credits": 0}

    async with ClientSession(base_url=BASE_URL) as session:
        endpoint = "/api/v10/users/@me/applications/521842831262875670/entitlements?exclude_consumed=true"
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                text = await response.text()
                nitro_credits["classic_credits"] = text.count("Nitro Classic")
                nitro_credits["boost_credits"] = text.count("Nitro Monthly")

    return nitro_credits["classic_credits"], nitro_credits["boost_credits"]


async def check_payments(headers: Dict[str, str]) -> Union[Optional[List[str]], int]:
    cc_digits = {"american express": "3", "visa": "4", "mastercard": "5"}
    account_cards = []
    card_info = None

    async with ClientSession(base_url=BASE_URL) as session:
        endpoint = "/api/v10/users/@me/billing/payment-sources"
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                payment_sources = await response.json()
            elif response.status == 40002:
                return 403

    if payment_sources:
        for payment_source in payment_sources:
            billing_address = payment_source["billing_address"]
            card_type = "Credit card" if payment_source["type"] == 1 else "PayPal"

            if card_type == "Credit card":
                cc_brand = payment_source["brand"]
                cc_first_digit = cc_digits.get(cc_brand)
                cc_last_digits = payment_source["last_4"]
                cc_number = f"{cc_first_digit if cc_first_digit else '*'}{'*' * 11}{cc_last_digits}"
                cc_month = str(payment_source["expires_month"]).zfill(2)
                cc_year = str(payment_source["expires_year"])[2:]

                card_info = (
                    f"Payment Type: {card_type}\n"
                    f"Valid: {not payment_source['invalid']}\n"
                    f"CC Holder Name: {billing_address['name']}\n"
                    f"CC Brand: {cc_brand.title()}\n"
                    f"CC Number: {' '.join(z if (i + 1) % 2 else f'{z}' for i, z in enumerate(cc_number))}\n"
                    f"CC Date: {cc_month}/{cc_year}\n"
                    f"Address 1: {billing_address['line_1']}\n"
                    f"Address 2: {billing_address['line_2'] or ''}\n"
                    f"City: {billing_address['city']}\n"
                    f"Postal code: {billing_address['postal_code']}\n"
                    f"State: {billing_address['state'] or ''}\n"
                    f"Country: {billing_address['country']}\n"
                    f"Default Payment Method: {payment_source['default']}\n"
                )

            elif card_type == "PayPal":
                card_info = (
                    f"Payment Type: {card_type}\n"
                    f"Valid: {not payment_source['invalid']}\n"
                    f"PayPal Name: {billing_address['name']}\n"
                    f"PayPal Email: {payment_source['email']}\n"
                    f"Address 1: {billing_address['line_1']}\n"
                    f"Address 2: {billing_address['line_2'] or ''}\n"
                    f"City: {billing_address['city']}\n"
                    f"Postal code: {billing_address['postal_code']}\n"
                    f"State: {billing_address['state'] or ''}\n"
                    f"Country: {billing_address['country']}\n"
                    f"Default Payment Method: {payment_source['default']}\n"
                )

            account_cards.append(card_info)

    return account_cards


async def get_guilds(headers: Dict[str, str]) -> Dict[str, list[str]]:
    guilds_info: Dict[str, list[str]] = {}

    async with ClientSession(base_url=BASE_URL) as session:
        endpoint = "/api/v9/users/@me/guilds?with_counts=true"
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                guilds_json = await response.json()

                for guild_info in guilds_json:
                    guild_id = guild_info["id"]
                    guild_name = guild_info["name"]
                    guild_owner = guild_info["owner"]
                    guilds_info[guild_id] = [guild_name, guild_owner]

    return guilds_info


async def get_gifts(headers: Dict[str, str]) -> List[str]:
    user_gifts: List[str] = []

    async with ClientSession(base_url=BASE_URL) as session:
        endpoint = "/api/v10/users/@me/entitlements/gifts"
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                gifts_json = await response.json()

                for gift_info in gifts_json:
                    subscription_plan_name = gift_info["subscription_plan"]["name"]
                    user_gifts.append(subscription_plan_name)

    return user_gifts


async def get_me(headers: Dict[str, str]) -> Union[Coroutine[Any, Any, None], Dict[str, Any], None, Tuple[int, str]]:
    user_info = None

    async with ClientSession(base_url=BASE_URL) as session:
        endpoint = "/api/v10/users/@me"
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                user_info = await response.json()
            elif response.status in {401, 403}:
                return response.status, ""

    return response.status, user_info


async def get_connections(headers: Dict[str, str]) -> Dict[str, Any]:
    user_connections: Dict[str, Any] = {}

    async with ClientSession(base_url=BASE_URL) as session:
        endpoint = "/api/v10/users/@me/connections"
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                connections_info = await response.json()
            else:
                return user_connections

    for connection_info in connections_info:
        connection_type = connection_info["type"]
        name = connection_info["name"]
        shows_in_profile = connection_info["visibility"] == 1
        verified = connection_info["verified"]
        revoked = connection_info["revoked"]

        user_connections[connection_type] = [name, shows_in_profile, verified, revoked]

    return user_connections


async def get_promotions(headers: Dict[str, str], locale: Optional[str] = None) -> Dict[str, Any]:
    user_promotions: Dict[str, Any] = {}

    async with ClientSession(base_url=BASE_URL) as session:
        endpoint = f"/api/v10/users/@me/outbound-promotions/codes?locale={locale or 'us'}"
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                promotions_info = await response.json()
            else:
                return user_promotions  # Return an empty dictionary if the request was not successful

    for promotion_info in promotions_info:
        name = promotion_info["promotion"]["outbound_title"]
        start_time = convert_iso_to_human_readable(promotion_info["promotion"]["start_date"])
        end_time = convert_iso_to_human_readable(promotion_info["promotion"]["end_date"])
        link_to = promotion_info["promotion"]["outbound_redemption_page_link"]
        code = promotion_info["code"]

        user_promotions[name] = [start_time, end_time, link_to, code]

    return user_promotions


async def check_boosts(headers: Dict[str, str]) -> Dict[str, Any]:
    user_boosts: Dict[str, Any] = {}

    async with ClientSession(base_url=BASE_URL) as session:
        endpoint = "/api/v10/users/@me/guilds/premium/subscription-slots"
        async with session.get(endpoint, headers=headers) as response:
            if response.status == 200:
                boosts_info = await response.json()
            else:
                return user_boosts

    if boosts_info:
        for boost_info in boosts_info:
            boost_id = boost_info.get("id")
            guild_id, ended = "Unused boost", False
            subscription_id = boost_info["subscription_id"]

            if boost_info.get("premium_guild_subscription") is not None:
                guild_id = boost_info["premium_guild_subscription"]["guild_id"]
                ended = boost_info["premium_guild_subscription"]["ended"]

            boost_status = "Unused (maybe cooldown)" if guild_id == "Unused boost" else "Used"
            canceled = boost_info["canceled"]
            cooldown_ends_at = (
                "No cooldown"
                if boost_info["cooldown_ends_at"] is None
                else convert_iso_to_human_readable(boost_info["cooldown_ends_at"])
            )

            user_boosts[boost_id] = [guild_id, ended, boost_status, canceled, cooldown_ends_at, subscription_id]

    return user_boosts


async def get_nitro_info(headers: Dict[str, str]) -> Tuple[Union[str, None], Union[str, None]]:
    nitro_start, nitro_end = None, None

    async with ClientSession(base_url=BASE_URL) as session:
        endpoint = "/api/v10/users/@me/billing/subscriptions"
        async with session.get(endpoint, headers=headers) as resp:
            if resp.status == 200:
                nitro_billing = await resp.json()
            else:
                return nitro_start, nitro_end  # Return None for both dates if the request was not successful

    if nitro_billing:
        nitro_start = convert_iso_to_human_readable(nitro_billing[0]["current_period_start"])
        nitro_end = convert_iso_to_human_readable(nitro_billing[0]["current_period_end"])

    return nitro_start, nitro_end


async def get_relationships(headers: Dict[str, str]) -> Tuple[int, List[str]]:
    relationship_info: List[str] = []

    async with ClientSession(base_url=BASE_URL) as session:
        endpoint = "/api/v10/users/@me/relationships"
        async with session.get(endpoint, headers=headers) as resp:
            relationship_json = await resp.json()

    if isinstance(relationship_json, list):
        for index, friend in enumerate(relationship_json, start=1):
            user_flags = get_user_flags(friend["user"]["public_flags"])
            user_id = friend["user"]["id"]
            user_name = friend["user"]["username"]
            avatar_url = (
                f"https://cdn.discordapp.com/avatars/{user_id}/{friend['user']['avatar']}."
                f"{'gif' if str(friend['user']['avatar']).startswith('a_') else 'png'}"
                if friend["user"]["avatar"]
                else None
            )
            nickname = friend['nickname'] if friend['nickname'] is not None else user_name
            friend_type_str = friend_type.get(friend['type'], 'Unknown')
            flags_str = ', '.join(user_flags) if user_flags else 'No flags'

            relationship_info.append(
                f"\n[ # ]: {index}\n"
                f"[ ID ]: {user_id}\n"
                f"[ Avatar URL ]: {avatar_url}\n"
                f"[ Account Creation ]: {get_account_creation(user_id)}\n"
                f"[ Nickname ]: {nickname}\n"
                f"[ Friend type ]: {friend_type_str}\n"
                f"[ Flags ]: {flags_str}"
            )

    return len(relationship_info), relationship_info


async def get_dms(headers: Dict[str, str]) -> List[str]:
    direct_messages: List[str] = []

    async with ClientSession(base_url=BASE_URL) as session:
        endpoint = "/api/v10/users/@me/channels"
        async with session.get(endpoint, headers=headers) as resp:
            if resp.status == 200:
                dms_json = await resp.json()

    if dms_json:
        for i, dm in enumerate(dms_json, start=1):
            recipients_info = ""
            for recipient in dm["recipients"]:
                user_flags = get_user_flags(recipient["public_flags"])
                user_id = recipient["id"]
                user_name = recipient["username"]
                avatar_url = (
                    f"https://cdn.discordapp.com/avatars/{user_id}/{recipient['avatar']}."
                    f"{'gif' if str(recipient['avatar']).startswith('a_') else 'png'}"
                    if recipient.get("avatar", None)
                    else None
                )
                recipients_info += (
                    f"\n[ ID ]: {user_id}\n"
                    f"[ Avatar URL ]: {avatar_url}\n"
                    f"[ Account Creation ]: {get_account_creation(user_id)}\n"
                    f"[ Global Name ]: {recipient.get('global_name', user_name)}\n"
                    f"[ Display Name ]: {recipient.get('display_name', user_name)}\n"
                    f"[ Bot ]: {recipient.get('bot', False)}\n"
                    f"[ Flags ]: {', '.join(user_flags) if user_flags else 'No flags'}\n\n"
                )

            dm_info = (
                f"\nPrivate channel №{i}\n[ ID ]: {dm['id']}\n"
                f"[ Friend type ]: {friend_type.get(dm['type'], 'Unknown')}\n"
                f"[ Last message id ]: {dm.get('last_message_id', None)}\n"
                f"[ Channel created at ]: {get_account_creation(dm['id'])}\n\n[ Recipients ]:{recipients_info}"
            )
            direct_messages.append(dm_info)

    return direct_messages


def create_needed(time: datetime) -> tuple[str, ...] | tuple[None, None, None, None]:
    if config["write_tokens_to_file"]:
        file_names = [
            "valid_tokens.txt",
            "invalid_tokens.txt",
            "phonelock_tokens.txt",
            "nitro_tokens.txt",
        ]
        formatted_time = format_datetime_humanly(date=time, format_string="%d.%m.%Y %H_%M_%S")
        directory_path = f"results/result-{formatted_time}"
        os.makedirs(directory_path, exist_ok=True)

        file_paths = tuple(os.path.join(directory_path, file) for file in file_names)
        for file_path in file_paths:
            with open(file_path, "w"):
                pass

        return file_paths
    else:
        return None, None, None, None

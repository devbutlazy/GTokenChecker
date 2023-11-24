import asyncio
import os
from datetime import datetime
from json import load

from rich.progress import Progress, TaskID

import src.utils as utils

config = load(open("src/config.json", "r"))
progress_bar = Progress()
all_tokens = utils.count_tokens()

index = 0
valid_count = 0
invalid_count = 0
nitro_count = 0

if all_tokens >= 1:
    progress = progress_bar.add_task("[red]Status: ", total=all_tokens)

start_time = datetime.now()
valid, invalid, phone_lock, nitro = utils.create_needed(start_time)
(
    show_flags,
    show_guilds,
    check_nitro_credits,
    check_promotions,
    check_connections,
    check_boosts,
    mask_tokens,
    show_relationships,
    check_private_channels,
    dont_show_enable_feature,
    write_only_tokens,
    print_only_tokens,
) = (
    config[key]
    for key in [
        "show_flags",
        "show_guilds",
        "check_nitro_credits",
        "check_promotions",
        "check_connections",
        "check_boosts",
        "mask_tokens",
        "show_relationships",
        "check_private_channels",
        "dont_show_enable_feature",
        "write_only_tokens",
        "print_only_tokens"
    ]
)


async def check_token(token: str, prog: Progress, task: TaskID) -> None:
    global index, valid_count, nitro_count, invalid_count

    headers = {
        "Accept": "*/*",
        "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
        "Alt-Used": "discord.com",
        "Authorization": token,
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

    masked_token = utils.mask_token(token) if mask_tokens else token

    status, info = await utils.get_me(headers=headers)

    index += 1

    if status == 200:
        locale = info.get("locale")
        user_creation = utils.get_account_creation(info["id"])
        nitro_credits = (
            (
                f'[ Nitro classic/boost credits ]: Enable "check_nitro_credits" feature in '
                "config.json!"
            )
            if not dont_show_enable_feature
            else ""
        )

        (
            guilds_text,
            payments_text,
            gifts_text,
            promotions_text,
            connections_text,
            boosts_text,
            rel_text,
            private_channels_text,
        ) = (
            "~~~~~~~~~~ Guilds ~~~~~~~~~~~\n",
            "~~~~~~~~~~ Payments ~~~~~~~~~~\n",
            "~~~~~~~~~~ Gifts info ~~~~~~~~~~\n",
            "~~~~~~~~~~ Promotions ~~~~~~~~~~\n",
            "~~~~~~~~~~ Account connections ~~~~~~~~~~\n",
            "~~~~~~~~~~ Boosts ~~~~~~~~~~\n",
            "~~~~~~~~~~ Relationships ~~~~~~~~~~\n",
            "~~~~~~~~~~ Private channels ~~~~~~~~~~\n",
        )

        flags_all = utils.get_user_flags(info["public_flags"])

        premium_type = (
            "No nitro"
            if info["premium_type"] == 0
            else "Nitro Classic"
            if info["premium_type"] == 1
            else "Nitro Boost"
            if info["premium_type"] == 2
            else "Nitro Basic"
        )

        nitro_start, nitro_end = (
            await utils.get_nitro_info(headers=headers)
            if premium_type != "No nitro"
            else ("No nitro", "No nitro")
        )

        if check_nitro_credits:
            classic_credits, nitro_boost_credits = await utils.check_nitro_credit(
                headers=headers
            )
            nitro_credits = (
                f"[ Nitro classic/boost credits ]: "
                f"{classic_credits}/{nitro_boost_credits}"
            )

        if check_nitro_credits:
            gifts = await utils.get_gifts(headers=headers)
            gifts_text += (
                "".join(f"{gift}\n" for gift in gifts) if len(gifts) >= 1 else "No gifts in account"
            )
        elif not dont_show_enable_feature:
            gifts_text += (
                '[ Gifts ]: Enable "check_nitro_credits" feature in config.json!'
            )

        # "You need to verify your account in order to perform this action." check
        if (payments := await utils.check_payments(headers=headers)) != 403:
            payments_text += (
                "".join(f"{payment}\n" for payment in payments) if len(payments) >= 1 else "No payments in account"
            )
        else:
            invalid_count += 1
            await utils.custom_print(
                f"token {masked_token} phone locked!",
                color="error",
                print_bool=True,
                write_file=True,
                file=phone_lock,
            )
            prog.update(
                task,
                advance=1,
                description=f"{valid_count} valid / {invalid_count} invalid / "
                            f"{nitro_count} nitro tokens (Total checked {index}/{all_tokens})",
            )
            return

        if show_relationships:
            count, relationships = await utils.get_relationships(headers=headers)
            rel_text += f"[ Total relationships ]: {count}\n"
            rel_text += "".join(text for text in relationships)
        elif not dont_show_enable_feature:
            rel_text += (
                '[ Relationships ]: Enable "show_relationships" feature in config.json!'
            )

        if show_guilds:
            guilds = await utils.get_guilds(headers=headers)
            guilds_text += (
                "".join(
                    f"ID: {_id} | Name: {name} | Owner: {owner}\n"
                    for _id, (name, owner) in guilds.items()
                )
                if len(guilds) >= 1
                else "No guilds in account"
            )
        elif not dont_show_enable_feature:
            guilds_text += (
                '[ Guilds info ]: Enable "show_guilds" feature in config.json!'
            )

        if check_connections:
            connections = await utils.get_connections(headers=headers)
            connections_text += (
                "".join(
                    f"Connection type: {conn_type} | Nickname: {name} | "
                    f"shows in profile: {sh_prof} |"
                    f" Verified?: {verified} | Revoked: {revoked}\n"
                    for conn_type, (name, sh_prof, verified, revoked) in connections.items()
                )
                if len(connections) >= 1
                else "No connections in account"
            )
        elif not dont_show_enable_feature:
            connections_text += (
                '[ Connections ]: Enable "check_connections" feature in config.json!'
            )

        if check_promotions and locale is not None:
            promotions = await utils.get_promotions(headers=headers, locale=locale)
            promotions_text += (
                "".join(
                    f"Promo: {name} | Start time: {s_time} | End time: {end_time} |"
                    f" Link to activate: {link} | Code: {code}\n"
                    for name, (s_time, end_time, link, code) in promotions.items()
                )
                if len(promotions) >= 1
                else "No promotions in account"
            )
        elif not dont_show_enable_feature:
            promotions_text += (
                '[ Promotions ]: Enable "check_promotions" feature in config.json!'
            )

        if check_boosts:
            boosts = await utils.check_boosts(headers=headers)
            boosts_text += (
                "".join(
                    f"Boost status: {boost_status} | "
                    f"Guild id: {guild_id} | Boost id: {boost_id} "
                    f"| ended: {ended} | canceled: {canceled} "
                    f"| Cooldown ends: {cooldown_end}\n"
                    for boost_id, (guild_id, ended, boost_status, canceled, cooldown_end, subscription_id) in
                    boosts.items()
                )
                if len(boosts) >= 1
                else "No boosts in account"
            )
        elif not dont_show_enable_feature:
            boosts_text += '[ Boosts ]: Enable "check_boosts" feature in config.json!'

        if check_private_channels:
            direct_messages = await utils.get_dms(headers=headers)
            private_channels_text += f"[ Total private channels ]: {len(direct_messages)}\n"
            private_channels_text += "".join(text for text in direct_messages)
        elif not dont_show_enable_feature:
            private_channels_text += (
                '[ Private channels ]: Enable "check_private_channels" '
                "feature in config.json!"
            )

        username = info["username"]
        avatar = (
            f"https://cdn.discordapp.com/avatars/{info['id']}/{info['avatar']}."
            f"{'gif' if str(info['avatar']).startswith('a_') else 'png'}"
            if info["avatar"]
            else None
        )
        banner = (
            f"https://cdn.discordapp.com/banners/{info['id']}/{info['banner']}."
            f"{'gif' if str(info['banner']).startswith('a_') else 'png'}"
            if info["banner"]
            else None
        )
        email = info["email"]
        phone = info["phone"]
        verified = info["verified"]
        mfa = info["mfa_enabled"]
        bio = info["bio"] if info["bio"] else None
        user_id = info["id"]

        text = f"""
~~~~~~~~~~~~~~~ INFO ~~~~~~~~~~~~~~~
Token {masked_token} is valid
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

~~~~~~~~~~~ Account INFO ~~~~~~~~~~~
[ ID ]: {user_id}
[ name#tag ]: {username}
[ Bio ]: {bio}
[ locale ]: {locale if locale is not None else 'cannot fetch account locale'}
[ Avatar URL ]: {avatar}
[ Banner URL ]: {banner}
[ E-mail ]: {email}
[ E-mail is verified? ] {verified}
[ Phone number ]: {phone}
[ 2FA enabled ]: {mfa}
[ Created at ]: {user_creation}
[ Public Flags ]: {', '.join(flags_all) if flags_all else 'No flags'}
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

        await utils.custom_print(
            text=f"token {masked_token} is valid!" if print_only_tokens else text,
            color="info",
            print_bool=True,
        )
        await utils.custom_print(
            text=token if write_only_tokens else text, write_file=True, file=valid
        )
        if premium_type != "No nitro":
            await utils.custom_print(
                text=token if write_only_tokens else text, write_file=True, file=nitro
            )
            nitro_count += 1
        valid_count += 1
        prog.update(
            task,
            advance=1,
            description=f"{valid_count} valid / {invalid_count} invalid / "
                        f"{nitro_count} nitro tokens (Total checked {index}/{all_tokens})",
        )
    elif status == 401:
        invalid_count += 1
        await utils.custom_print(
            f"token {masked_token} invalid!",
            color="error",
            print_bool=True,
            write_file=True,
            file=invalid,
        )
        prog.update(
            task,
            advance=1,
            description=f"{valid_count} valid / {invalid_count} invalid / "
                        f"{nitro_count} nitro tokens (Total checked {index}/{all_tokens})",
        )
    elif status == 403:
        invalid_count += 1
        await utils.custom_print(
            f"token {masked_token} phone locked!",
            color="error",
            print_bool=True,
            write_file=True,
            file=phone_lock,
        )
        prog.update(
            task,
            advance=1,
            description=f"{valid_count} valid / {invalid_count} invalid / "
                        f"{nitro_count} nitro tokens (Total checked {index}/{all_tokens})",
        )
    elif status == 429:
        await utils.custom_print("Rate Limit", color="error", print_bool=True)
        prog.update(
            task,
            advance=1,
            description=f"{valid_count} valid / {invalid_count} invalid / "
                        f"{nitro_count} nitro tokens (Total checked {index}/{all_tokens})",
        )
    return


async def main() -> None:
    try:
        await utils.custom_print("[1] One token (input)", color="info", print_bool=True)
        await utils.custom_print("[2] Some tokens (file)", color="info", print_bool=True)

        choice = int(input(">>> "))

        if choice == 1:
            token = input("Enter token: ")
            await process_single_token(token)
        elif choice == 2:
            await process_multiple_tokens()
        else:
            await utils.custom_print("Invalid choice", color="error", print_bool=True)
    except (Exception, BaseException):
        await utils.custom_print("Sorry, an error occurred. Please try again.", color="error", print_bool=True)


async def process_single_token(token: str) -> None:
    task = asyncio.create_task(check_token(token, progress_bar, progress))
    await run_tasks([task])


async def process_multiple_tokens() -> None:
    tasks = []
    tokens = await utils.get_tokens()

    for token in tokens:
        tasks.append(asyncio.create_task(check_token(token, progress_bar, progress)))
        await asyncio.sleep(0.3)

    await run_tasks(tasks)


async def run_tasks(tasks: list[asyncio.Task]) -> None:
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except (BaseException, ExceptionGroup):
        pass

    try:
        with progress_bar:
            await asyncio.gather(*tasks)
    except (BaseException, ExceptionGroup) as load_error:
        await utils.custom_print(f"An error occurred: {load_error}", color="error", print_bool=True)


if __name__ == "__main__":
    asyncio.run(main())

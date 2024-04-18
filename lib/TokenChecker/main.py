import asyncio
import os
from datetime import datetime

import utils


class TokenChecker:
    def __init__(self) -> None:
        self.headers = utils.headers

        self.index = 0
        self.all_tokens = utils.count_tokens()
        self.valid_count = 0
        self.invalid_count = 0
        self.nitro_count = 0

        self.valid, self.invalid, self.phone_lock, self.nitro = utils.create_needed(
            datetime.now()
        )

    async def run_tasks(self, tasks: list[asyncio.Task]) -> None:
        try:
            os.system("cls" if os.name == "nt" else "clear")
        except (BaseException, ExceptionGroup):
            pass

        try:
            await asyncio.gather(*tasks)
        except (BaseException, ExceptionGroup) as load_error:
            await utils.custom_print(
                f"An error occurred: {load_error}", color="error", print_bool=True
            )

    async def check_token(self, token: str) -> None:
        mask_token = lambda token: (
            ".".join(token.split(".")[:-1] + ["*" * len(token.split(".")[-1])])
            if len(token.split(".")) > 1
            else token
        )

        masked_token = mask_token(token)

        headers = self.headers.copy()
        headers["Authorization"] = token
        self.headers = headers

        status, info = await utils.get_me(headers=self.headers)
        self.index += 1

        if status == 200:
            locale = info.get("locale")
            user_creation = utils.get_account_creation(info["id"])
            nitro_credits = ""

            sections = utils.sections.values()
            (
                guilds_text,
                payments_text,
                gifts_text,
                promotions_text,
                connections_text,
                boosts_text,
                rel_text,
                private_channels_text,
            ) = sections

            flags = utils.get_user_flags(info["public_flags"])
            premium_type = utils.premium_types.get(info["premium_type"], "Nitro Basic")

            if premium_type != "No nitro":
                nitro_start, nitro_end = await utils.get_nitro_info(
                    headers=self.headers
                )
            else:
                nitro_start = nitro_end = "No nitro"

            classic_credits, nitro_boost_credits = await utils.check_nitro_credit(
                headers=self.headers
            )
            gifts = await utils.get_gifts(headers=self.headers)

            nitro_credits = (
                f"[ Nitro classic/boost credits  ]: "
                f"{classic_credits}/{nitro_boost_credits}"
            )

            gifts_text += (
                "".join(f"{gift}\n" for gift in gifts)
                if gifts
                else "No gifts on account"
            )

            # You need to verify your account in order to perform this action.
            if (payments := await utils.check_payments(headers=self.headers)) != 403:
                payments_text += (
                    "".join(f"{payment}\n" for payment in payments)
                    if len(payments) >= 1
                    else "No payments on account"
                )
            else:
                self.invalid_count += 1
                return await utils.custom_print(
                    f"Token {masked_token} phone locked!",
                    color="error",
                    print_bool=True,
                    write_file=True,
                    file=self.phone_lock,
                )

            count, relationships = await utils.get_relationships(headers=self.headers)
            rel_text += f"[Total relationships]: {count}\n"
            rel_text += "".join(text for text in relationships)

            guilds = await utils.get_guilds(headers=self.headers)
            guilds_text += (
                "".join(
                    f"ID: {_id} | Name: {name} | Owner: {owner}\n"
                    for _id, (name, owner) in guilds.items()
                )
                if len(guilds) >= 1
                else "No guilds in account"
            )

            connections = await utils.get_connections(headers=self.headers)
            connections_text += (
                "".join(
                    f"Connection type: {conn_type} | Nickname: {name} | "
                    f"Show Bool: {sh_prof} |"
                    f"Verify Bool: {verified} | Revoked: {revoked}\n"
                    for conn_type, (
                        name,
                        sh_prof,
                        verified,
                        revoked,
                    ) in connections.items()
                )
                if len(connections) >= 1
                else "No connections in account"
            )

            if locale is not None:
                promotions = await utils.get_promotions(
                    headers=self.headers, locale=locale
                )
                promotions_text += (
                    "".join(
                        f"Promo: {name} | Start time: {s_time} | End time: {end_time} |"
                        f" Link to activate: {link} | Code: {code}\n"
                        for name, (s_time, end_time, link, code) in promotions.items()
                    )
                    if len(promotions) >= 1
                    else "No promotions in account"
                )

            boosts = await utils.check_boosts(headers=self.headers)
            boosts_text += (
                "".join(
                    f"Boost status: {boost_status} | "
                    f"Guild id: {guild_id} | Boost id: {boost_id} "
                    f"| ended: {ended} | canceled: {canceled} "
                    f"| Cooldown ends: {cooldown_end}\n"
                    for boost_id, (
                        guild_id,
                        ended,
                        boost_status,
                        canceled,
                        cooldown_end,
                    ) in boosts.items()
                )
                if len(boosts) >= 1
                else "No boosts on account"
            )

            direct_messages = await utils.get_dms(headers=self.headers)
            private_channels_text += (
                f"[Total private channels]: {len(direct_messages)}\n"
            )
            private_channels_text += "".join(text for text in direct_messages)

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

            text = utils.text.format(
                masked_token=masked_token,
                user_id=user_id,
                username=username,
                bio=bio,
                locale=locale if locale else "Cannot fetch account locale",
                avatar=avatar,
                banner=banner,
                email=email,
                verified=verified,
                phone=phone,
                mfa=mfa,
                user_creation=user_creation,
                flags=", ".join(flags) if flags else "No flags",
                premium_type=premium_type,
                nitro_start=nitro_start,
                nitro_end=nitro_end,
                nitro_credits=nitro_credits,
                payments_text=payments_text,
                guilds_text=guilds_text,
                gifts_text=gifts_text,
                promotions_text=promotions_text,
                connections_text=connections_text,
                boosts_text=boosts_text,
                rel_text=rel_text,
                private_channels_text=private_channels_text,
            )

            await utils.custom_print(
                text=text,
                color="info",
                print_bool=True,
                write_file=True,
                file=self.valid,
            )

            if premium_type != "No nitro":
                await utils.custom_print(
                    text=text,
                    print_bool=False,
                    write_file=True,
                    file=self.nitro,
                )
                self.nitro_count += 1

            self.valid_count += 1

        elif status == 401:
            self.invalid_count += 1
            await utils.custom_print(
                f"Token {masked_token} is invalid!",
                color="error",
                print_bool=True,
                write_file=True,
                file=self.invalid,
            )

        elif status == 403:
            invalid_count += 1
            await utils.custom_print(
                f"Token {masked_token} phone locked!",
                color="error",
                print_bool=True,
                write_file=True,
                file=self.phone_lock,
            )

        elif status == 429:
            await utils.custom_print("Rate Limit", color="error", print_bool=True)

        return None
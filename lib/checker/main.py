import traceback
from typing import Optional
from datetime import datetime

import static
import utils
from lib.discord.main import DiscordAPI, DiscordToken


class TokenChecker:
    def __init__(self) -> None:
        self.headers = static.headers
        self.token: Optional[str] = None
        self.masked_token: Optional[str] = None

        # self.all_tokens = self.DiscordToken.count_tokens()
        self.valid: Optional[str]
        self.invalid: Optional[str]
        self.phone_lock: Optional[str]
        self.nitro: Optional[str]

        self.valid, self.invalid, self.phone_lock, self.nitro = utils.create_needed(
            datetime.now()
        )
        self.DiscordToken = DiscordToken()
        self.DiscordAPI = DiscordAPI()

    async def check_token(self, token: str) -> None:
        """
        Check if the given token is valid

        :param token: the token to check
        :return: None
        """
        self.token = token
        self.masked_token = self.DiscordToken.mask_token(self.token)

        headers = self.headers.copy()
        headers["Authorization"] = self.token
        self.headers = headers

        status, _ = await self.DiscordAPI.get_me(headers=self.headers)

        status_actions = {
            200: self.handle_200,
            403: self.handle_403,
            401: self.handle_401,
        }
        utils.custom_print(
            f"Please wait, fetching information...",
            color="warn",
            print_bool=True,
        )

        handler = status_actions.get(status)

        (
            await handler()
            if handler
            else utils.custom_print(
                f"An unexpected error occurred! Status: {status}",
                color="error",
                print_bool=True,
            )
        )

    async def handle_200(self) -> None:
        """
        Handle 200 status while checking token(s)

        :return: None
        """

        _, info = await self.DiscordAPI.get_me(headers=self.headers)
        if isinstance(info, dict):
            locale = info.get("locale")
        else:
            return await self.handle_401()

        user_creation = self.DiscordAPI.get_account_creation(info["id"])

        sections = static.sections.values()
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

        flags = self.DiscordAPI.get_user_flags(info["public_flags"])
        premium_type = static.premium_types.get(info["premium_type"], "Nitro Basic")

        if premium_type != "No nitro":
            nitro_start, nitro_end = await self.DiscordAPI.get_nitro_info(
                headers=self.headers
            )
        else:
            nitro_start = nitro_end = "No nitro"

        classic_credits, nitro_boost_credits = await self.DiscordAPI.check_nitro_credit(
            headers=self.headers
        )
        gifts = await self.DiscordAPI.get_gifts(headers=self.headers)

        nitro_credits = (
            f"[ Nitro classic/boost credits  ]: "
            f"{classic_credits}/{nitro_boost_credits}"
        )

        gifts_text += (
            "".join(f"{gift}\n" for gift in gifts) if gifts else "No gifts on account"
        )

        # You need to verify your account in order to perform this action.
        if (
            payments := await self.DiscordAPI.check_payments(headers=self.headers)
        ) != 403 and isinstance(payments, list):
            payments_text += (
                "".join(f"{payment}\n" for payment in payments)
                if len(payments) >= 1
                else "No payments on account"
            )
        else:
            utils.custom_print(
                f"Token {self.masked_token} phone locked!",
                color="error",
                print_bool=True,
                write_file=True,
                file=self.phone_lock,
            )
            return  # type: ignore

        count, relationships = await self.DiscordAPI.get_relationships(
            headers=self.headers
        )

        rel_text += f"[ Total relationships ]: {count}\n"
        rel_text += "".join(text for text in relationships)

        guilds = await self.DiscordAPI.get_guilds(headers=self.headers)
        guilds_text += (
            "".join(
                f"ID: {_id} | Name: {name} | Owner: {owner}\n"
                for _id, (name, owner) in guilds.items()
            )
            if len(guilds) >= 1
            else "No guilds in account"
        )

        connections = await self.DiscordAPI.get_connections(headers=self.headers)
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
            else "No connections on account"
        )

        if locale:
            promotions = await self.DiscordAPI.get_promotions(
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

        boosts = await self.DiscordAPI.check_boosts(headers=self.headers)
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

        direct_messages = await self.DiscordAPI.get_dms(headers=self.headers)

        private_channels_text += f"[ Total private channels ]: {len(direct_messages)}\n"
        private_channels_text += "".join(text for text in direct_messages)

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

        text = static.text.format(
            masked_token=self.masked_token,
            user_id=info["id"],
            username=info["username"],
            bio=info.get("bio"),
            locale=locale if locale else "Cannot fetch account locale",
            avatar=avatar,
            banner=banner,
            email=info.get("email"),
            verified=info["verified"],
            phone=info.get("phone"),
            mfa=info["mfa_enabled"],
            auth_types=", ".join(
                static.auth_types.get(auth_type, "None")
                for auth_type in info.get("authenticator_types", "None")
            )
            or "None",
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

        utils.custom_print(
            text=text,
            color="info",
            print_bool=True,
            write_file=True,
            file=self.valid,
        )

        if premium_type != "No nitro":
            utils.custom_print(
                text=text,
                print_bool=False,
                write_file=True,
                file=self.nitro,
            )

    async def handle_401(self):
        """
        Handle 401 errors while checking token(s)

        :return: None
        """
        utils.custom_print(
            f"Token {self.masked_token} is invalid!",
            color="error",
            print_bool=True,
            write_file=True,
            file=self.invalid,
        )

    async def handle_403(self):
        """
        Handle 403 errors while checking token(s)

        :return: None
        """
        utils.custom_print(
            f"Token {self.masked_token} phone locked!",
            color="error",
            print_bool=True,
            write_file=True,
            file=self.phone_lock,
        )

import asyncio
import os

from static import startup_text
import utils
from lib.checker.main import TokenChecker
from lib.discord.main import DiscordToken


TOKEN = DiscordToken()


async def main() -> None:
    """
    Start all the tasks, and wait for the input

    :return: None
    """
    try:
        utils.custom_print(startup_text, color="info", print_bool=True)
        utils.custom_print("[1] One token (hand-input)", color="info", print_bool=True)
        utils.custom_print(
            "[2] Two or more tokens (file)", color="info", print_bool=True
        )

        choice = int(input("\033[1;33;48m>>> \033[1;37;0m"))
        match choice:
            case 1:
                token = input("Enter token: ")
                task = asyncio.create_task(TokenChecker().check_token(token))
                await utils.run_tasks([task])
            case 2:
                tasks = []
                tokens, _ = await TOKEN.get_tokens()

                for token in tokens:
                    tasks.append(
                        asyncio.ensure_future(
                            asyncio.shield(TokenChecker().check_token(token))
                        )
                    )
                    await asyncio.sleep(0.3)

                await asyncio.gather(*tasks)
            case _:
                utils.custom_print("Invalid choice", color="error", print_bool=True)

    except ValueError:
        utils.custom_print(
            "Sorry, an error occurred. Please try again.",
            color="error",
            print_bool=True,
        )


if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        asyncio.run(utils.custom_print("Exiting...", color="info"))

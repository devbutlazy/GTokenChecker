import asyncio
import os

from lib.TokenChecker.main import TokenChecker
from lib.Utilities.main import TokenManipulations
import utils


TOKEN_MANIPULATION = TokenManipulations()


async def main() -> None:
    """
    Start all the tasks, and wait for the input

    :return: None
    """
    try:
        await utils.custom_print(utils.startup_text, color="info", print_bool=True)
        await utils.custom_print("[1] One token (hand-input)", color="info", print_bool=True)
        await utils.custom_print(
            "[2] Two or more tokens (file)", color="info", print_bool=True
        )

        choice = int(input("\033[1;33;48m>>> \033[1;37;0m"))
        match choice:
            case 1:
                TOKEN_CHECKER = TokenChecker()

                token = input("Enter token: ")
                task = asyncio.create_task(TOKEN_CHECKER.check_token(token))
                await TOKEN_CHECKER.run_tasks([task])
            case 2:
                tasks = []
                tokens, _ = await TOKEN_MANIPULATION.get_tokens()

                for token in tokens:
                    tasks.append(
                        asyncio.ensure_future(
                            asyncio.shield(TokenChecker().check_token(token))
                        )
                    )
                    await asyncio.sleep(0.3)

                await asyncio.gather(*tasks)
            case _:
                await utils.custom_print(
                    "Invalid choice", color="error", print_bool=True
                )

    except ValueError:
        await utils.custom_print(
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

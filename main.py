import asyncio
import os

from lib.TokenChecker.main import TokenChecker
from lib.Utilities.main import TokenManipulations
import utils

TOKEN_CHECKER = TokenChecker()
TOKEN_MANIPULATION = TokenManipulations()


async def main() -> None:
    try:
        await utils.custom_print(utils.startup_text, color="info", print_bool=True)
        await utils.custom_print("[1] One token (input)", color="info", print_bool=True)
        await utils.custom_print(
            "[2] Some tokens (file)", color="info", print_bool=True
        )

        choice = int(input(">>> "))
        match choice:
            case 1:
                token = input("Enter token: ")
                task = asyncio.create_task(TOKEN_CHECKER.check_token(token))
                await TOKEN_CHECKER.run_tasks([task])
            case 2:
                tasks = []
                tokens = await TOKEN_MANIPULATION.get_tokens()

                for token in tokens:
                    tasks.append(asyncio.create_task(TOKEN_CHECKER.check_token(token)))
                    await asyncio.sleep(0.3)

                await TOKEN_CHECKER.run_tasks(tasks)
            case _:
                await utils.custom_print(
                    "Invalid choice", color="error", print_bool=True
                )

    except (Exception, BaseException):
        await utils.custom_print(
            "Sorry, an error occurred. Please try again.",
            color="error",
            print_bool=True,
        )


if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    asyncio.run(main())

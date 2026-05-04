import asyncio

from logs import logger
import state
from state import sbot, shutdown, NonAsync_loadArr, init_chat_id_dict
from cycle import cycleCheck
from scrapeAPI import NonAsync_RefreshPrayerTime

# Import the handler modules so their decorators register with sbot
import commands  # noqa: F401  (side-effect: registers user-facing handlers)
import commands_admin  # noqa: F401  (side-effect: registers admin handlers)


async def main():
    while True:
        try:
            await cycleCheck(
                state.chat_id_dict,
                state.reminders_enabled_arr,
                state.daily_enabled_arr,
                state.custom_5_enabled_arr,
                state.custom_10_enabled_arr,
                state.custom_15_enabled_arr,
            )

            print("Suspend")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"An error occurred in the main function: {e}")


async def poll():
    await sbot.infinity_polling()


if __name__ == '__main__':
    logger.info("Bot is initialised and will run.")

    init_chat_id_dict()
    print("User profiles have been loaded")
    logger.info("User profiles have been loaded")

    pt = NonAsync_RefreshPrayerTime()
    if pt:
        state.database_prayer_times = pt

    NonAsync_loadArr(state.chat_id_dict)
    print("Prayer Times have been loaded")
    logger.info("Prayer Times have been loaded")

    logger.info("Logging begin.")

    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(poll()),
        loop.create_task(main()),
    ]

    try:
        loop.run_until_complete(asyncio.wait(tasks))
    except KeyboardInterrupt:
        loop.run_until_complete(shutdown())
    finally:
        loop.close()

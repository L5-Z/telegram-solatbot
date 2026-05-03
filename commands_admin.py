import os

from telebot import apihelper

from logs import logger
from state import (
    sbot, chat_id_dict, is_admin, ADMIN_CHAT_ID,
    _purge_user, checker, delete_user, shutdown,
)
from storage import save_data
from blocked import block_check


# /announce — broadcast to every registered user
@sbot.message_handler(commands=['announce'])
async def announce(message):
    if not is_admin(message.chat.id):
        return

    print("\nAdmin is sending an announcement")
    announcement_text = message.text.split(' ', 1)[1]
    admin_message = "Welcome Admin, the following announcement has been posted:\n"
    welcome_admin = admin_message + announcement_text

    for chat_id, _ in chat_id_dict.items():
        if chat_id == str(ADMIN_CHAT_ID):
            await sbot.send_message(chat_id, welcome_admin)
            continue
        logger.info(f"Attempting to send announcement to {chat_id}")
        try:
            await sbot.send_message(chat_id, announcement_text)
            logger.info(f"Sent announcement to {chat_id}")
            print("sent announcement", chat_id)
        except apihelper.ApiException as e:
            logger.error(f"Failed to send announcement to {chat_id}")
            if e.result.status_code == 403 and "bot was blocked by the user" in e.result.text:
                logger.warning(f"Bot was blocked by user {chat_id}")
                print(f"\n\nBot was blocked by user {chat_id}\n\n")
            else:
                logger.error(f"An error occurred in sending announcement: {e}")
        except Exception as e:
            if "403" in str(e) and "blocked" in str(e).lower():
                logger.warning(f"Bot was blocked by user {chat_id} (caught in generic Exception)")
            else:
                logger.error(f"Unexpected error for {chat_id}: {e}")
        finally:
            continue

    print("Announcement: ", announcement_text, " has been sent\n")


# /add — manually register a user
@sbot.message_handler(commands=['add'])
async def addUser(message):
    if not is_admin(message.chat.id):
        return

    new_chat_id = message.text.split(' ', 1)[1]
    print("\nAdmin is adding user: ", new_chat_id)
    admin_message = "Welcome Admin, the following user is being added:\n"
    notify = admin_message + new_chat_id

    await checker(new_chat_id)

    print("User: ", new_chat_id, " has been added\n")
    await sbot.send_message(message.chat.id, notify)


# /del — purge a user from chat_id_dict and runtime arrays
@sbot.message_handler(commands=['del'])
async def delUser(message):
    if not is_admin(message.chat.id):
        return

    try:
        chat_id = message.text.split(' ', 1)[1]
    except IndexError:
        await sbot.send_message(message.chat.id, "Usage: /del <chat_id>")
        return

    success = await _purge_user(chat_id, notify_requester=message.chat.id)
    if not success:
        await sbot.send_message(message.chat.id, f"User {chat_id} not found in database")


# /dump — list every chat_id with totals
@sbot.message_handler(commands=['dump'])
async def dumpDict(message):
    if not is_admin(message.chat.id):
        return

    print("\nAdmin is dumping user database:\n")
    data_dump = "User ID Dump:\n\n"

    usercount = 0
    for chat_id in chat_id_dict:
        data_dump += str(chat_id) + "\n"
        if chat_id > 0:
            usercount += 1

    data_dump += "\nTotal Individual Users: " + str(usercount) + "\n"
    data_dump += "\n\nTotal Users: " + str(len(chat_id_dict)) + "\n"
    print("Successfully dumped data\n")
    await sbot.send_message(message.chat.id, data_dump)


# /peek — print the entire chat_id_dict
@sbot.message_handler(commands=['peek'])
async def peekDict(message):
    if not is_admin(message.chat.id):
        return

    print("\nAdmin is viewing user database:\n")

    data_dump = "User Settings:\n\n"
    data_dump += str(chat_id_dict) + "\n"

    print("Successfully output data\n")
    await sbot.send_message(message.chat.id, data_dump)


# /updatedb — normalise the custom_durations slot for every user
@sbot.message_handler(commands=['updatedb'])
async def updateDB(message):
    if not is_admin(message.chat.id):
        return

    print("\nAdmin is updating database")
    admin_message = "Welcome Admin, the database has been updated.\n"

    for chat_id, chat_data in chat_id_dict.items():
        existing_durations = chat_data.get('custom_durations', [])
        normalized_durations = (existing_durations + [False, False, False])[:3]
        new_chat_data = {
            'reminders_enabled': chat_data.get('reminders_enabled', True),
            'daily_timings_enabled': chat_data.get('daily_timings_enabled', True),
            'custom_durations': normalized_durations,
        }
        chat_id_dict[chat_id] = new_chat_data
    await save_data(chat_id_dict)

    await sbot.send_message(message.chat.id, admin_message)
    print("The database has been updated.\n")


# /blocked — scan and purge users who blocked the bot
@sbot.message_handler(commands=['blocked'])
async def blockedUsers(message):
    if not is_admin(message.chat.id):
        return

    print("\nAdmin is viewing blockers")

    admin_message = "Welcome Admin, here are the blockers:\n"
    await sbot.send_message(message.chat.id, admin_message)
    await block_check(chat_id_dict, logger, delete_user)

    print("The blockers have been displayed.\n")


# /whisper — send a private message to a single user
@sbot.message_handler(commands=['whisper'])
async def whisper_user(message):
    if not is_admin(message.chat.id):
        return

    print("\nAdmin is whispering")
    _, receiver, whisper_text = message.text.split(' ', 2)
    admin_message = "Welcome Admin, whisper received:\n"
    receiver_message = f"\nWas sent to {receiver}"
    welcome_admin = admin_message + whisper_text + receiver_message

    logger.info(f"Attempting to send whisper to {receiver}")
    try:
        await sbot.send_message(receiver, whisper_text)
        logger.info(f"Sent whisper to {receiver}")
        await sbot.send_message(str(ADMIN_CHAT_ID), welcome_admin)
        print("sent whisper: ", receiver)
    except apihelper.ApiException as e:
        logger.error(f"Failed to send whisper to {receiver}")
        if e.result.status_code == 403 and "bot was blocked by the user" in e.result.text:
            logger.warning(f"Bot was blocked by user {receiver}")
            print(f"\n\nBot was blocked by user {receiver}\n\n")
        else:
            logger.error(f"An error occurred in sending whisper: {e}")
    except Exception as e:
        if "403" in str(e) and "blocked" in str(e).lower():
            logger.warning(f"Bot was blocked by user {receiver} (caught in generic Exception)")
        else:
            logger.error(f"Unexpected error for {receiver}: {e}")


# /exit — graceful shutdown
@sbot.message_handler(commands=['exit'])
async def exitBot(message):
    if not is_admin(message.chat.id):
        return

    print("Admin has initiated bot shutdown.")
    logger.info("Admin has initiated bot shutdown.")
    await sbot.send_message(message.chat.id, "Bot shutting down.")
    await shutdown()
    os._exit(0)

from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    KeyboardButton, ReplyKeyboardMarkup,
)

from logs import logger
from storage import save_data, load_data


# --- Bot instance (single source of truth, shared with blocked.py and cycle.py) ---
with open('botKey.txt', 'r') as file:
    bot_key = str(file.read())

TELEGRAM_BOT_TOKEN = bot_key
sbot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)


# --- Admin gate ---
ADMIN_CHAT_ID = 51719761


def is_admin(chat_id) -> bool:
    try:
        return int(chat_id) == ADMIN_CHAT_ID
    except (ValueError, TypeError):
        return False


# --- Shared mutable state (mutated in place; never reassigned, except database_prayer_times) ---
chat_id_dict = {}
database_prayer_times = {}

reminders_enabled_arr = []
daily_enabled_arr = []
custom_5_enabled_arr = []
custom_10_enabled_arr = []
custom_15_enabled_arr = []


# --- Reply-keyboard menus ---
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.row(KeyboardButton('Upcoming Timings'), KeyboardButton('Current Timings'))
main_menu.row(KeyboardButton('Settings'), KeyboardButton('Information'))
main_menu.row(KeyboardButton('Help'))

toggle_menu = ReplyKeyboardMarkup(resize_keyboard=True)
toggle_menu.row(KeyboardButton('General'), KeyboardButton('Pre-Reminders'))
toggle_menu.row(KeyboardButton('Back'))

info_menu = ReplyKeyboardMarkup(resize_keyboard=True)
info_menu.row(KeyboardButton('Qiblat'), KeyboardButton('Donate'))
info_menu.row(KeyboardButton('Feedback'), KeyboardButton('Zakat'))
info_menu.row(KeyboardButton('Back'))

donate_menu = ReplyKeyboardMarkup(resize_keyboard=True)
donate_menu.row(KeyboardButton('North'), KeyboardButton('South'))
donate_menu.row(KeyboardButton('East'), KeyboardButton('West'))
donate_menu.row(KeyboardButton('Back'))


# --- User-management helpers ---
def purge_runtime_arrays(chat_id):
    for arr in (custom_5_enabled_arr, custom_10_enabled_arr, custom_15_enabled_arr,
                reminders_enabled_arr, daily_enabled_arr):
        if chat_id in arr:
            arr.remove(chat_id)


async def _purge_user(chat_id, notify_requester=None):
    chat_id = str(chat_id)
    if chat_id not in chat_id_dict:
        logger.warning(f"User {chat_id} not found in database")
        return False

    chat_id_dict.pop(chat_id, None)
    purge_runtime_arrays(chat_id)

    logger.info(f"User {chat_id} has been deleted")
    await save_data(chat_id_dict)
    logger.info(f"Database updated after deleting user {chat_id}")

    await sbot.send_message(ADMIN_CHAT_ID, f"User {chat_id} has been deleted")

    if notify_requester:
        await sbot.send_message(notify_requester, f"User {chat_id} has been deleted")

    return True


async def delete_user(remove_chat_id):
    await _purge_user(remove_chat_id, notify_requester=None)


async def checker(chat_id):
    chat_id = str(chat_id)
    if chat_id not in chat_id_dict:
        chat_id_dict[chat_id] = {
            'reminders_enabled': True,
            'daily_timings_enabled': True,
            'custom_durations': [False, False, False],
        }

        await save_data(chat_id_dict)

        reminders_enabled_arr.append(chat_id)
        daily_enabled_arr.append(chat_id)

        logger.info(f"Saved {chat_id} to database.")
        await sbot.send_message(str(ADMIN_CHAT_ID), f"[Admin] New User Joined: {chat_id}")


# --- Toggle helpers (shared between slash commands and inline callbacks) ---
async def toggle_reminders(chat_id) -> bool:
    chat_id = str(chat_id)
    chat_info = chat_id_dict[chat_id]
    new_state = not chat_info.get('reminders_enabled', True)
    chat_info['reminders_enabled'] = new_state
    if new_state:
        if chat_id not in reminders_enabled_arr:
            reminders_enabled_arr.append(chat_id)
    else:
        if chat_id in reminders_enabled_arr:
            reminders_enabled_arr.remove(chat_id)
    await save_data(chat_id_dict)
    return new_state


async def toggle_daily(chat_id) -> bool:
    chat_id = str(chat_id)
    chat_info = chat_id_dict[chat_id]
    new_state = not chat_info.get('daily_timings_enabled', True)
    chat_info['daily_timings_enabled'] = new_state
    if new_state:
        if chat_id not in daily_enabled_arr:
            daily_enabled_arr.append(chat_id)
    else:
        if chat_id in daily_enabled_arr:
            daily_enabled_arr.remove(chat_id)
    await save_data(chat_id_dict)
    return new_state


# --- Boot helpers (in-place population of shared containers) ---
def NonAsync_loadArr(loaded_dict):
    reminders_enabled_arr.clear()
    daily_enabled_arr.clear()
    custom_5_enabled_arr.clear()
    custom_10_enabled_arr.clear()
    custom_15_enabled_arr.clear()
    for chat_id, chat_data in loaded_dict.items():
        if chat_data.get('reminders_enabled', True):
            reminders_enabled_arr.append(chat_id)
        if chat_data.get('daily_timings_enabled', True):
            daily_enabled_arr.append(chat_id)
        durations = (chat_data.get('custom_durations', []) + [False, False, False])[:3]
        if durations[0]:
            custom_5_enabled_arr.append(chat_id)
        if durations[1]:
            custom_10_enabled_arr.append(chat_id)
        if durations[2]:
            custom_15_enabled_arr.append(chat_id)


async def loadArr(loaded_dict):
    NonAsync_loadArr(loaded_dict)
    return [reminders_enabled_arr, daily_enabled_arr,
            custom_5_enabled_arr, custom_10_enabled_arr, custom_15_enabled_arr]


def init_chat_id_dict():
    loaded = load_data()
    chat_id_dict.clear()
    chat_id_dict.update(loaded)


# --- Shutdown ---
async def shutdown():
    await save_data(chat_id_dict)
    logger.info("Bot has been shut down.")
    print("Bot has been shut down.")

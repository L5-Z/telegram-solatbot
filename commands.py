import asyncio

from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove,
)

from logs import logger
from state import (
    sbot, chat_id_dict,
    main_menu, toggle_menu, info_menu, donate_menu,
    checker, _purge_user, toggle_reminders, toggle_daily,
    ADMIN_CHAT_ID,
)
from storage import save_data
from scrapeAPI import printTimes, printUpcomingTimes
from donate import get_mosques, select_mosque, get_qr, mosque_extract
from funcs import format_text


# /menu — show main reply keyboard
@sbot.message_handler(commands=['menu'])
async def send_menu(message):
    await sbot.send_message(message.chat.id, "Please select an option:", reply_markup=main_menu)


# Donate-region reply keyboard
@sbot.message_handler(func=lambda message: message.text in ['North', 'South', 'East', 'West'])
async def handle_region_click(message):
    region = message.text
    await sbot.send_message(message.chat.id, f"You selected {region}. Please select an index value:")

    inline_kb = InlineKeyboardMarkup(row_width=3)

    mosques = await get_mosques(region)
    if mosques:
        response = f"\n\nMosques in {region.capitalize()}:\n"
        for idx, mosque in enumerate(mosques):
            response += f"{idx + 1}. {list(mosque.keys())[0]}\n"
        response += "\nSelect the mosque index to get the QR code."

        buttons = [InlineKeyboardButton(str(i), callback_data=f'index_{region}_{i}') for i in range(1, len(mosques) + 1)]
        inline_kb.add(*buttons) # Unpack the list of buttons with add method of InlineKeyboardMarkup
    else:
        response = "No mosques found in this region."

    await sbot.send_message(message.chat.id, response, reply_markup=inline_kb)


# Mosque-index inline callback (PayNow QR)
@sbot.callback_query_handler(func=lambda call: call.data.startswith('index_'))
async def handle_index_selection(call):
    data = call.data.split('_')
    region = data[1]
    index = data[2]

    mosque, path = await select_mosque(region, index)

    await sbot.answer_callback_query(call.id, f"Selected {index} for {region} mosque: {mosque}")

    qr_result = await get_qr(path)

    mosque_info = f"*__{mosque}__*\n"
    mosque_info += await mosque_extract(path)

    mosque_info = await format_text(mosque_info)
    mosque_replaced = await format_text(mosque)
    qr_result_formatted = await format_text(qr_result)

    await sbot.send_message(call.message.chat.id, mosque_info, 'MarkdownV2')
    await sbot.send_message(call.message.chat.id, f"*__PayNow QR link for {mosque_replaced}:__*\n\n{qr_result_formatted}", 'MarkdownV2', reply_markup=info_menu)


# Catch-all for reply-keyboard text (slash commands fall through to their decorators)
@sbot.message_handler(func=lambda message: message.text and not message.text.startswith('/'))
async def handle_click(message):
    if message.text == 'Settings':
        await settings_command(message)
    elif message.text == 'Current Timings':
        await timings_command(message)
    elif message.text == 'Upcoming Timings':
        await upcoming_command(message)
    elif message.text == 'Help':
        await help_command(message)
    elif message.text == 'General':
        await generalSettings_command(message)
    elif message.text == 'Pre-Reminders':
        await prereminder_command(message)
    elif message.text == 'Back':
        await sbot.send_message(message.chat.id, "Back to main menu:", reply_markup=main_menu)
    elif message.text == 'Information':
        await sbot.send_message(message.chat.id, "More Information:", reply_markup=info_menu)
    elif message.text == 'Qiblat':
        await qiblat_info(message)
    elif message.text == 'Zakat':
        await zakat_info(message)
    elif message.text == 'Donate':
        await donate_info(message)
    elif message.text == 'Feedback':
        await feedback_form(message)


# /start
@sbot.message_handler(regexp='start')
@sbot.message_handler(commands=['start'])
async def start_command(message):
    intro_message = "Assalamu'alaikum! I am a bot that provides prayer time notifications for Singapore.\n\n"
    intro_message += "I fetch prayer times directly from [MUIS](https://www.muis.gov.sg), the religious authority for Muslims in Singapore!\n"
    intro_message += "Prayer times are fetched from [here](https://isomer-user-content.by.gov.sg/muis_prayers_timetable.json)!\n\n"
    intro_message += "What I can do:\n"
    intro_message += "- Send you azan reminders at each prayer time\n"
    intro_message += "- Send the full daily prayer times at 5 AM each morning\n"
    intro_message += "- Provide the Qiblat direction for Singapore\n\n"

    welcome_message = "Thanks for using my bot!\n\n"
    welcome_message += "Note:\n"
    welcome_message += "- Do /help for a list of commands\n"
    welcome_message += "- Reminders are ON by default, do /toggle to turn them off\n"
    welcome_message += "- Daily Prayer Time notifications (at 5AM) are ON by default, do /daily to turn them off\n\n"
    welcome_message += "- Please run /stop to stop receiving notifications instead of blocking the bot\n\n"
    welcome_message += "=============================\n"
    welcome_message += "Current Version: v2.0.0 (Stable Release)\n"
    welcome_message += "Updated and Patched as of 1/5/26\n"
    welcome_message += "\nBot made by L5Z (Faatih) :)"

    await checker(message.chat.id)
    await sbot.send_message(message.chat.id, intro_message, parse_mode='Markdown', reply_markup=main_menu)
    await asyncio.sleep(10)
    await help_command(message)
    await sbot.send_message(message.chat.id, welcome_message)


# /stop
@sbot.message_handler(regexp='stop')
@sbot.message_handler(commands=['stop'])
async def stop_command(message):
    await checker(message.chat.id)
    chat_id = str(message.chat.id)
    await _purge_user(chat_id, notify_requester=message.chat.id)
    await sbot.send_message(message.chat.id, "You will no longer receive notifications. Thank you for using my bot!")
    await sbot.send_message(str(ADMIN_CHAT_ID), f"[Admin] Current User Left: {chat_id}")


# /settings
@sbot.message_handler(regexp='settings')
@sbot.message_handler(commands=['settings'])
async def settings_command(message):
    await checker(message.chat.id)

    chat_id = str(message.chat.id)
    chat_info = chat_id_dict[chat_id]

    if chat_info['reminders_enabled'] is True:
        rem_tog = "On ✅"
    else:
        rem_tog = "Off ❌"

    if chat_info['daily_timings_enabled'] is True:
        dly_tog = "On ✅"
    else:
        dly_tog = "Off ❌"

    reply = "_Current Settings:_\n\n"
    reply += "*General:*\n"
    reply += f"Azan Reminders: {rem_tog}\n"
    reply += f"Daily Timings: {dly_tog}\n\n"

    durations = chat_info.get('custom_durations', [False, False, False])
    durations = (durations + [False, False, False])[:3]
    labels = ['5min', '10min', '15min']
    reply += "*Pre\\-Reminders:*\n"
    for i, lbl in enumerate(labels):
        state_str = "On ✅" if durations[i] else "Off ❌"
        reply += f"  {lbl}: {state_str}\n"

    await sbot.send_message(message.chat.id, reply, 'MarkdownV2', reply_markup=toggle_menu)


# /timings
@sbot.message_handler(regexp='timings')
@sbot.message_handler(commands=['timings'])
async def timings_command(message):
    await checker(message.chat.id)
    reply = await printTimes()
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')


# /upcoming
@sbot.message_handler(commands=['upcoming'])
async def upcoming_command(message):
    await checker(message.chat.id)
    reply = await printUpcomingTimes()
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')


# /qiblat
@sbot.message_handler(regexp='qiblat')
@sbot.message_handler(commands=['qiblat'])
async def qiblat_info(message):
    await checker(message.chat.id)
    reply = "\U0001F54B _*Qiblat for Singapore:*_\n\n"
    reply += "\U0001F9ED *293* degrees \\[NW\\]"
    reply += "\n\n\nAugmented Reality with Google: https://qiblafinder\\.withgoogle\\.com/"
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')


# /feedback
@sbot.message_handler(regexp='feedback')
@sbot.message_handler(commands=['feedback'])
async def feedback_form(message):
    await checker(message.chat.id)
    reply = "*__Feedback Form:__*\n\n"
    reply += "https://forms\\.gle/JhB5MdtFsiX7zYC78"
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')


# /donate
@sbot.message_handler(regexp='donate')
@sbot.message_handler(commands=['donate'])
async def donate_info(message):
    await checker(message.chat.id)

    reply = "*__How Do I Donate?__*\n\n"
    reply += "1\\. Open your preferred Mobile Banking App and navigate to the PayNow function\n"
    reply += "2\\. Select the function to scan a PayNow QR Code\n"
    reply += "3\\. Scan the QR Code in the link provided\n"
    reply += "4\\. Confirm that the account name/UEN number corresponds to the name of your selected mosque\\. In the case it is not available, you may refer to the tabung\\.sg link attached below the Mosque header\\.\n"
    reply += "5\\. Enter your intended donation amount and complete your donation\n\n"
    reply += "If you are viewing this on your mobile device, tap on the *QR* link\\. Press and hold on the QR Code to save the image to your phone\\. You may also take a screenshot\\.\n\n"
    reply += "In the PayNow function in your Mobile Banking App, click on the option to access your images album and select the QR Code image that you have just saved\\."
    reply += "\n\n\n_powered by tabung\\.sg_"

    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')
    await sbot.send_message(message.chat.id, "Please select a region:", reply_markup=donate_menu)


# /zakat
@sbot.message_handler(regexp='zakat')
@sbot.message_handler(commands=['zakat'])
async def zakat_info(message):
    await checker(message.chat.id)
    reply = "[Zakat Singapore](https://www.zakat.sg/)"
    await sbot.send_message(message.chat.id, reply, 'Markdown')


# /daily
@sbot.message_handler(regexp='daily')
@sbot.message_handler(commands=['daily'])
async def daily_command(message):
    await checker(message.chat.id)
    new_state = await toggle_daily(message.chat.id)
    if new_state:
        await sbot.send_message(message.chat.id, "Daily Prayer Times are now enabled. ✅")
    else:
        await sbot.send_message(message.chat.id, "Daily Prayer Times are now disabled. ❌")


# /toggle
@sbot.message_handler(regexp='toggle')
@sbot.message_handler(commands=['toggle'])
async def toggle_command(message):
    await checker(message.chat.id)
    new_state = await toggle_reminders(message.chat.id)
    if new_state:
        await sbot.send_message(message.chat.id, "Azan reminders are now enabled. ✅")
    else:
        await sbot.send_message(message.chat.id, "Azan reminders are now disabled. ❌")


# General inline keyboard (Reminders + Daily Updates) — sent by "General" reply button
async def generalSettings_command(message):
    await checker(message.chat.id)
    chat_id = str(message.chat.id)
    chat_info = chat_id_dict[chat_id]

    rem_mark = '✅' if chat_info.get('reminders_enabled', True) else '❌'
    daily_mark = '✅' if chat_info.get('daily_timings_enabled', True) else '❌'

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(f"Reminders {rem_mark}", callback_data='general_reminders'))
    kb.add(InlineKeyboardButton(f"Daily Updates {daily_mark}", callback_data='general_daily'))

    await sbot.send_message(
        message.chat.id,
        "Toggle general notifications:",
        reply_markup=kb,
    )


@sbot.callback_query_handler(func=lambda call: call.data.startswith('general_'))
async def handle_general_toggle(call):
    chat_id = str(call.message.chat.id)
    await checker(chat_id)

    which = call.data.split('_', 1)[1]

    if which == 'reminders':
        new_state = await toggle_reminders(chat_id)
        label = 'Azan reminders'
    elif which == 'daily':
        new_state = await toggle_daily(chat_id)
        label = 'Daily prayer times'
    else:
        return

    await sbot.answer_callback_query(
        call.id,
        f"{label} {'enabled' if new_state else 'disabled'}",
    )

    chat_info = chat_id_dict[chat_id]
    rem_mark = '✅' if chat_info.get('reminders_enabled', True) else '❌'
    daily_mark = '✅' if chat_info.get('daily_timings_enabled', True) else '❌'

    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(f"Reminders {rem_mark}", callback_data='general_reminders'))
    kb.add(InlineKeyboardButton(f"Daily Updates {daily_mark}", callback_data='general_daily'))
    try:
        await sbot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb,
        )
    except Exception as e:
        logger.warning(f"Failed to edit general keyboard: {e}")


# /prereminder
@sbot.message_handler(commands=['prereminder'])
async def prereminder_command(message):
    await checker(message.chat.id)
    chat_id = str(message.chat.id)
    chat_info = chat_id_dict[chat_id]

    durations = chat_info.get('custom_durations', [False, False, False])
    durations = (durations + [False, False, False])[:3]
    chat_info['custom_durations'] = durations

    kb = InlineKeyboardMarkup(row_width=1)
    for idx, label in enumerate(['5 min', '10 min', '15 min']):
        mark = '✅' if durations[idx] else '❌'
        kb.add(InlineKeyboardButton(f"{label} {mark}", callback_data=f'prerem_{idx}'))

    await sbot.send_message(
        message.chat.id,
        "Toggle pre-prayer reminders (any combination):",
        reply_markup=kb,
    )


@sbot.callback_query_handler(func=lambda call: call.data.startswith('prerem_'))
async def handle_prereminder_toggle(call):
    from state import custom_5_enabled_arr, custom_10_enabled_arr, custom_15_enabled_arr

    idx = int(call.data.split('_')[1])
    minutes = [5, 10, 15][idx]
    chat_id = str(call.message.chat.id)

    await checker(chat_id)
    chat_info = chat_id_dict[chat_id]
    durations = (chat_info.get('custom_durations', []) + [False, False, False])[:3]
    durations[idx] = not durations[idx]
    chat_info['custom_durations'] = durations

    arrays = [custom_5_enabled_arr, custom_10_enabled_arr, custom_15_enabled_arr]
    target_arr = arrays[idx]
    if durations[idx]:
        if chat_id not in target_arr:
            target_arr.append(chat_id)
    else:
        if chat_id in target_arr:
            target_arr.remove(chat_id)

    await save_data(chat_id_dict)

    await sbot.answer_callback_query(
        call.id,
        f"{minutes}-min pre-reminder {'enabled' if durations[idx] else 'disabled'}",
    )

    kb = InlineKeyboardMarkup(row_width=1)
    for i, label in enumerate(['5 min', '10 min', '15 min']):
        mark = '✅' if durations[i] else '❌'
        kb.add(InlineKeyboardButton(f"{label} {mark}", callback_data=f'prerem_{i}'))
    try:
        await sbot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb,
        )
    except Exception as e:
        logger.warning(f"Failed to edit pre-reminder keyboard: {e}")


# /menu_off
@sbot.message_handler(regexp='menu_off')
@sbot.message_handler(commands=['menu_off'])
async def menu_off_command(message):
    await checker(message.chat.id)
    reply = "Menu is disabled"
    await sbot.send_message(message.chat.id, reply, reply_markup=ReplyKeyboardRemove())


# /help
@sbot.message_handler(regexp='help')
@sbot.message_handler(commands=['help'])
async def help_command(message):
    await checker(message.chat.id)
    cmds = [
        "/stop - Stops the bot",
        "/menu - Displays menu buttons",
        "/menu_off - Disables menu buttons",
        "/settings - Displays current notification settings",
        "/toggle - Toggle reminders on or off",
        "/timings - Get current prayer times",
        "/daily - Toggle daily prayer times (at 5AM) notifications on or off",
        "/prereminder - Toggle 5/10/15 min pre-prayer reminders",
        "/upcoming - Get prayer times up to a week ahead (not inclusive of today)",
        "/help - List available commands",
    ]
    reply = "Help Menu (List of Commands):\n"
    reply += "\n".join(cmds)
    await sbot.send_message(message.chat.id, reply)


# /patch
@sbot.message_handler(regexp='patch')
@sbot.message_handler(commands=['patch'])
async def patch_command(message):
    await checker(message.chat.id)
    patch_0_0_2 = [
        "\nPatch: v0.0.2  |  27/9/23",
        "- Fixed an issue where reminders failed to work",
        "- Enabled group chat option, invite your bot into your group to have everyone be reminded!",
        "- Updated /start message for clarity\n",
    ]
    patch_0_0_3 = [
        "\nPatch: v0.0.3  |  27/9/23",
        "- Integrated /edit into /customreminder. Run /help for instructions",
        "- Created /patch for patchnotes and relevant updates",
        "- Fixed a temporary repetitive loop when receiving reminders\n",
        "- New version with additional features coming soon!\n",
    ]
    patch_0_0_4 = [
        "\nPatch: v0.0.4  |  28/9/23",
        "- Fixed looping reminders",
        "- Fixed bot only able to serve one user at a time",
        "- Fixed clashing data with users\n",
        "- New Feature: /list to view current custom times",
        "- New Feature: /daily to toggle on or off daily prayer times at 5AM\n",
    ]
    reply = "Patchnotes Thread:\n"
    reply += "\n".join(patch_0_0_2)
    reply += "\n".join(patch_0_0_3)
    reply += "\n".join(patch_0_0_4)
    await sbot.send_message(message.chat.id, reply)

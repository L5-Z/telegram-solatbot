from logs import logger
import asyncio
import os
import telebot
from telebot import apihelper
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.types import *

from storage import *
from scrapeAPI import *
from cycle import *
from blocked import *
from donate import *
from funcs import format_text

# Bot token
with open('botKey.txt', 'r') as file:
    bot_key = str(file.read())

TELEGRAM_BOT_TOKEN = bot_key

# Create a Bot instance with bot token
sbot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)

# Initialize a global dictionary to store chat_id information
global chat_id_dict
chat_id_dict = {}

# Initialize a global dictionary to store prayer_times information
database_prayer_times = {}

# Initialize runtime arrays
reminders_enabled_arr = []
daily_enabled_arr = []
custom_5_enabled_arr = []
custom_10_enabled_arr = []
custom_15_enabled_arr = []

def purge_runtime_arrays(chat_id):
    for arr in (custom_5_enabled_arr, custom_10_enabled_arr, custom_15_enabled_arr,
                reminders_enabled_arr, daily_enabled_arr):
        if chat_id in arr:
            arr.remove(chat_id)

# Define the menus
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
toggle_menu = ReplyKeyboardMarkup(resize_keyboard=True)
info_menu = ReplyKeyboardMarkup(resize_keyboard=True)
donate_menu = ReplyKeyboardMarkup(resize_keyboard=True)

# Main Menu buttons
main_menu.row(KeyboardButton('Upcoming Timings'), KeyboardButton('Current Timings'))
main_menu.row(KeyboardButton('Settings'), KeyboardButton('Information'))
main_menu.row(KeyboardButton('Help'))

toggle_menu.row(KeyboardButton('Reminders'), KeyboardButton('Daily Updates'))
toggle_menu.row(KeyboardButton('Pre-Reminders'))
toggle_menu.row(KeyboardButton('Back'))

info_menu.row(KeyboardButton('Qiblat'), KeyboardButton('Donate'))
info_menu.row(KeyboardButton('Feedback'), KeyboardButton('Zakat'))
info_menu.row(KeyboardButton('Back'))

donate_menu.row(KeyboardButton('North'), KeyboardButton('South'))
donate_menu.row(KeyboardButton('East'), KeyboardButton('West'))
donate_menu.row(KeyboardButton('Back'))

# Command handler for the /menu command
@sbot.message_handler(commands=['menu'])
async def send_menu(message):
    await sbot.send_message(message.chat.id, "Please select an option:", reply_markup=main_menu)

# Handler for processing region menu button clicks
@sbot.message_handler(func=lambda message: message.text in ['North', 'South', 'East', 'West'])
async def handle_region_click(message):
    region = message.text
    await sbot.send_message(message.chat.id, f"You selected {region}. Please select an index value:")
    
    # Inline keyboard for index selection
    inline_kb = InlineKeyboardMarkup(row_width=3)

    mosques = await get_mosques(region)
    if mosques:
        response = f"\n\nMosques in {region.capitalize()}:\n"
        for idx, mosque in enumerate(mosques):
            response += f"{idx + 1}. {list(mosque.keys())[0]}\n"
        response += "\nSelect the mosque index to get the QR code."

        # Create all buttons first
        buttons = [InlineKeyboardButton(str(i), callback_data=f'index_{region}_{i}') for i in range(1, len(mosques) + 1)]
        inline_kb.add(*buttons)  # Unpack the list of buttons with add method of InlineKeyboardMarkup

    else:
        response = "No mosques found in this region."

    await sbot.send_message(message.chat.id, response, reply_markup=inline_kb)

# Handler for processing index selection
@sbot.callback_query_handler(func=lambda call: call.data.startswith('index_'))
async def handle_index_selection(call):
    data = call.data.split('_')
    region = data[1]
    index = data[2]

    # Call the select_mosque function with the selected region and index
    mosque, path = await select_mosque(region, index)
    
    # New message on selection
    await sbot.answer_callback_query(call.id,f"Selected {index} for {region} mosque: {mosque}")
    
    # Call the get_qr function with the path
    qr_result = await get_qr(path)

    # Mosque details
    mosque_info = f"*__{mosque}__*\n"
    mosque_info += await mosque_extract(path)

    # Formatting the text to escape special characters for MarkdownV2
    mosque_info = await format_text(mosque_info)
    mosque_replaced = await format_text(mosque)
    qr_result_formatted = await format_text(qr_result)
    
    await sbot.send_message(call.message.chat.id, mosque_info, 'MarkdownV2')
    await sbot.send_message(call.message.chat.id, f"*__PayNow QR link for {mosque_replaced}:__*\n\n{qr_result_formatted}", 'MarkdownV2', reply_markup=info_menu)

# Handler for processing button clicks
@sbot.message_handler(func=lambda message: True)
async def handle_click(message):
    if message.text == 'Settings' or message.text == '/settings':
        await settings_command(message)
        await sbot.send_message(message.chat.id, "Edit notification settings with the toggle buttons below:", reply_markup=toggle_menu)
    elif message.text == 'Current Timings' or message.text == '/timings':
        await timings_command(message)
    elif message.text == 'Upcoming Timings' or message.text == '/upcoming':
        await upcoming_command(message)
    elif message.text == 'Help' or '/help' in message.text:
        await help_command(message)
    elif message.text == 'Reminders' or message.text == '/toggle':
        await toggle_command(message)
        await settings_command(message)
    elif message.text == 'Daily Updates' or message.text == '/daily':
        await daily_command(message)
        await settings_command(message)
    elif message.text == 'Pre-Reminders' or message.text == '/prereminder':
        await prereminder_command(message)
    elif message.text == 'Back':
        await sbot.send_message(message.chat.id, "Back to main menu:", reply_markup=main_menu)
    elif message.text == 'Information':
        await sbot.send_message(message.chat.id, "More Information:", reply_markup=info_menu)
    elif message.text == 'Qiblat' or message.text == '/qiblat':
        await qiblat_info(message)
    elif message.text == 'Zakat' or message.text == '/zakat':
        await zakat_info(message)
    elif message.text == 'Donate' or message.text == '/donate':
        await donate_info(message)
    elif message.text == 'Feedback' or message.text == '/feeback':
        await feedback_form(message)
    elif '/announce' in message.text:
        await announce(message)
    elif '/add' in message.text:
        await addUser(message)
    elif '/del' in message.text:
        await delUser(message)
    elif '/whisper' in message.text:
        await whisper_user(message)
    elif message.text == '/dump':
        await dumpDict(message)
    elif message.text == '/peek':
        await peekDict(message)
    elif message.text == '/updatedb':
        await updateDB(message)
    elif message.text == '/blocked':
        await blockedUsers(message)
    elif message.text == '/exit':
        await exitBot(message)
    elif message.text == '/start':
        await start_command(message)
    elif message.text == '/menu_off':
        await menu_off_command(message)

# ADMIN FUNCTION (51719761): ANNOUNCEMENTS
@sbot.message_handler(commands=['announce'])
async def announce(message):
    if message.chat.id == 51719761:
        print("\nAdmin is sending an announcement")
        announcement_text = message.text.split(' ', 1)[1] # Extract text after the command
        admin_message = "Welcome Admin, the following announcement has been posted:\n"
        welcome_admin = admin_message + announcement_text

        for chat_id, _ in chat_id_dict.items():
                if chat_id == '51719761':
                    await sbot.send_message(chat_id, welcome_admin)
                    continue
                else:
                    logger.info(f"Attempting to send announcement to {chat_id}")
                    try:
                        # Try to send the announcement to check if the bot is blocked
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
                        # Check if it's a 403 from the generic exception
                        if "403" in str(e) and "blocked" in str(e).lower():
                            logger.warning(f"Bot was blocked by user {chat_id} (caught in generic Exception)")
                        else:
                            # Catch all other possible errors to avoid stopping the loop
                            logger.error(f"Unexpected error for {chat_id}: {e}")
                    finally:
                        continue
        
        print("Announcement: ", announcement_text, " has been sent\n")      
    else:
        return
    
# ADMIN FUNCTION (51719761): ADD USER
@sbot.message_handler(commands=['add'])
async def addUser(message):
    if message.chat.id == 51719761:
        new_chat_id = message.text.split(' ', 1)[1] # Extract text after the command
        print("\nAdmin is adding user: ", new_chat_id)
        admin_message = "Welcome Admin, the following user is being added:\n"
        notify = admin_message + new_chat_id

        await checker(new_chat_id)
        
        print("User: ", new_chat_id, " has been added\n")
        await sbot.send_message(message.chat.id, notify)
    else:
        return


# Internal unified user deletion function
async def _purge_user(chat_id, notify_requester=None):
    global chat_id_dict
    chat_id = str(chat_id)
    if chat_id not in chat_id_dict:
        logger.warning(f"User {chat_id} not found in database")
        return False

    chat_id_dict.pop(chat_id, None)
    purge_runtime_arrays(chat_id)

    logger.info(f"User {chat_id} has been deleted")
    await save_data(chat_id_dict)
    logger.info(f"Database updated after deleting user {chat_id}")

    await sbot.send_message(51719761, f"User {chat_id} has been deleted")

    if notify_requester:
        await sbot.send_message(notify_requester, f"User {chat_id} has been deleted")

    return True


# ADMIN FUNCTION (51719761): REMOVE USER
@sbot.message_handler(commands=['del'])
async def delUser(message):
    if message.chat.id != 51719761:
        return

    try:
        chat_id = message.text.split(' ', 1)[1]
    except IndexError:
        await sbot.send_message(message.chat.id, "Usage: /del <chat_id>")
        return

    success = await _purge_user(chat_id, notify_requester=message.chat.id)
    if not success:
        await sbot.send_message(message.chat.id, f"User {chat_id} not found in database")
    
    try:
        chat_id = message.text.split(' ', 1)[1]
    except IndexError:
        await sbot.send_message(message.chat.id, "Usage: /del <chat_id>")
        return

    success = await _purge_user(chat_id, notify_requester=message.chat.id)
    if not success:
        await sbot.send_message(message.chat.id, f"User {chat_id} not found in database")
    
# ADMIN FUNCTION (51719761): PRINT ALL USER ID
@sbot.message_handler(commands=['dump'])
async def dumpDict(message):
    if message.chat.id == 51719761:
        print("\nAdmin is dumping user database:\n")
        data_dump = "User ID Dump:\n\n"

        usercount = 0
        for chat_id in chat_id_dict:
            data_dump += str(chat_id) + "\n"
            if chat_id > 0: # Only count individual users, not groups
                usercount += 1
        
        data_dump += "\nTotal Individual Users: " + str(usercount) + "\n"
        data_dump += "\n\nTotal Users: " + str(len(chat_id_dict)) + "\n"
        print("Successfully dumped data\n")
        await sbot.send_message(message.chat.id, data_dump)     
    else:
        return
    
# ADMIN FUNCTION (51719761): PRINT ALL USER ID
@sbot.message_handler(commands=['peek'])
async def peekDict(message):
    if message.chat.id == 51719761:
        print("\nAdmin is viewing user database:\n")

        data_dump = "User Settings:\n\n"
        data_dump += str(chat_id_dict) + "\n"
            
        print("Successfully output data\n")
        await sbot.send_message(message.chat.id, data_dump)     
    else:
        return
    
# ADMIN FUNCTION (51719761): UPDATE DATABASE
@sbot.message_handler(commands=['updatedb'])
async def updateDB(message):
    if message.chat.id == 51719761:
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
    else:
        return

# ADMIN FUNCTION (51719761): VIEW BLOCKED USERS
@sbot.message_handler(commands=['blocked'])
async def blockedUsers(message):
    if message.chat.id == 51719761:
        print("\nAdmin is viewing blockers")

        admin_message = "Welcome Admin, here are the blockers:\n"
        await sbot.send_message(message.chat.id, admin_message)
        await block_check(chat_id_dict, logger, delete_user)

        print("The blockers have been displayed.\n")
    else:
        return

# ADMIN FUNCTION (51719761): WHISPER USER
@sbot.message_handler(commands=['whisper'])
async def whisper_user(message):
    if message.chat.id == 51719761:
        print("\nAdmin is whispering")
        _, receiver, whisper_text = message.text.split(' ', 2) # Extract text after the command
        admin_message = "Welcome Admin, whisper received:\n"
        receiver_message = f"\nWas sent to {receiver}"
        welcome_admin = admin_message + whisper_text + receiver_message

        logger.info(f"Attempting to send whisper to {receiver}")
        try:
            # Try to send the whisper to check if the bot is blocked
            await sbot.send_message(receiver, whisper_text)
            logger.info(f"Sent whisper to {receiver}")
            await sbot.send_message('51719761', welcome_admin)
            print("sent whisper: ", receiver)
        except apihelper.ApiException as e:
            logger.error(f"Failed to send whisper to {receiver}")
            if e.result.status_code == 403 and "bot was blocked by the user" in e.result.text:
                logger.warning(f"Bot was blocked by user {receiver}")
                print(f"\n\nBot was blocked by user {receiver}\n\n")
            else:
                logger.error(f"An error occurred in sending whisper: {e}")
        except Exception as e:
            # Check if it's a 403 from the generic exception
            if "403" in str(e) and "blocked" in str(e).lower():
                logger.warning(f"Bot was blocked by user {receiver} (caught in generic Exception)")
            else:
                # Catch all other possible errors to avoid stopping the loop
                logger.error(f"Unexpected error for {receiver}: {e}")
    else:
        return

# ADMIN FUNCTION (51719761): SHUTDOWN BOT
@sbot.message_handler(commands=['exit'])
async def exitBot(message):
    if message.chat.id == 51719761:
        print("Admin has initiated bot shutdown.")
        logger.info("Admin has initiated bot shutdown.")
        await sbot.send_message(message.chat.id, "Bot shutting down.")
        await shutdown()
        os._exit(0)
    else:
        return

# Check chat_id if present in dict
async def checker(chat_id):
    global chat_id_dict, reminders_enabled_arr, daily_enabled_arr

    # Convert chat_id to string to ensure consistency
    chat_id = str(chat_id)

    if chat_id not in chat_id_dict:
        chat_id_dict[chat_id] = {
            'reminders_enabled': True,
            'daily_timings_enabled': True,
            'custom_durations': [False, False, False], # Time for 5, 10, 15
        }

        await save_data(chat_id_dict)

        # Add the new chat ID to the arrays
        reminders_enabled_arr.append(chat_id)
        daily_enabled_arr.append(chat_id)

        logger.info(f"Saved {chat_id} to database.")
        await sbot.send_message('51719761', f"[Admin] New User Joined: {chat_id}")


# Command Handlers

# /start command handler
@sbot.message_handler(regexp='start')
@sbot.message_handler(commands=['start'])
async def start_command(message):
    # Intro message
    intro_message = "Assalamu'alaikum! I am a bot that provides prayer time notifications for Singapore.\n\n"
    intro_message += "I fetch prayer times direct from [MUIS](https://www.muis.gov.sg), the religious authority for Muslims in Singapore!\n"
    intro_message += "Prayer times are fetched from [here](https://isomer-user-content.by.gov.sg/muis_prayers_timetable.json)!\n\n"
    intro_message += "What I can do:\n"
    intro_message += "- Send you azan reminders at each prayer time\n"
    intro_message += "- Send the full daily prayer times at 5 AM each morning\n"
    intro_message += "- Provide the Qiblat direction for Singapore\n\n"
    # Welcome message
    welcome_message = "Thanks for using my bot!\n\n"
    welcome_message += "Note:\n"
    welcome_message += "- Do /help for a list of commands\n"
    welcome_message += "- Reminders are ON by default, do /toggle to turn them off\n"
    welcome_message += "- Daily Prayer Time notifications (at 5AM) are ON by default, do /daily to turn them off\n\n"
    welcome_message += "- Please run /stop to stop receiving notifications instead of blocking the bot\n\n"
    welcome_message += "=============================\n"
    welcome_message += "Current Version: v2.0.0 (Stable Release)\n"
    welcome_message += "Updated and Patched as of 1/5/26\n"
    #welcome_message += "Do /patch to view patchnotes\n\n"
    welcome_message += "\nBot made by L5Z (Faatih) :)"
    await checker(message.chat.id)
    await sbot.send_message(message.chat.id, intro_message, parse_mode='Markdown', reply_markup=main_menu)
    await asyncio.sleep(10)
    await help_command(message)
    await sbot.send_message(message.chat.id, welcome_message)

# /stop command handler
@sbot.message_handler(regexp='stop')
@sbot.message_handler(commands=['stop'])
async def stop_command(message):
    await checker(message.chat.id)
    chat_id = str(message.chat.id)
    if chat_id in chat_id_dict:
        del chat_id_dict[chat_id]
        purge_runtime_arrays(chat_id)
        await save_data(chat_id_dict)
        logger.info(f"Removed {chat_id} from database.")
    await sbot.send_message(message.chat.id, "You will no longer receive notifications. Thank you for using my bot!")
    await sbot.send_message('51719761', f"[Admin] Current User Left: {chat_id}")

# /settings command handler
@sbot.message_handler(regexp='settings')
@sbot.message_handler(commands=['settings'])
async def settings_command(message):
    await checker(message.chat.id)
    
    chat_id = str(message.chat.id)
    chat_info = chat_id_dict[chat_id]

    if (chat_info['reminders_enabled'] is True):
        rem_tog = "On \u2705"
    else:
        rem_tog = "Off \u274c"
    
    if (chat_info['daily_timings_enabled'] is True):
        dly_tog = "On \u2705"
    else:
        dly_tog = "Off \u274c"

    reply = "_Current Settings:_\n\n"
    reply += f"*Reminders Enabled:* {rem_tog}\n"
    reply += f"*Daily Timings Enabled:* {dly_tog}\n\n"

    durations = chat_info.get('custom_durations', [False, False, False])
    durations = (durations + [False, False, False])[:3]
    labels = ['5min', '10min', '15min']
    reply += "*Pre\\-Reminders:*\n"
    for i, lbl in enumerate(labels):
        state = "On ✅" if durations[i] else "Off ❌"
        reply += f"  {lbl}: {state}\n"

    # Send the message with prayer times
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')

# /timings command handler
@sbot.message_handler(regexp='timings')
@sbot.message_handler(commands=['timings'])
async def timings_command(message):
    await checker(message.chat.id)
    reply = await printTimes()
    # Send the message with prayer times
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')

# /upcoming command handler
@sbot.message_handler(commands=['upcoming'])
async def upcoming_command(message):
    await checker(message.chat.id)
    reply = await printUpcomingTimes()
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')

# /qiblat command handler
@sbot.message_handler(regexp='qiblat')
@sbot.message_handler(commands=['qiblat'])
async def qiblat_info(message):
    await checker(message.chat.id)
    reply = "\U0001F54B _*Qiblat for Singapore:*_\n\n"
    reply += "\U0001F9ED *293* degrees \\[NW\\]"
    reply += "\n\n\nAugmented Reality with Google: https://qiblafinder\.withgoogle\.com/"
    # Send the message with qiblat directions
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')

# /feedback command handler
@sbot.message_handler(regexp='feedback')
@sbot.message_handler(commands=['feedback'])
async def feedback_form(message):
    await checker(message.chat.id)
    reply = "*__Feedback Form:__*\n\n"
    reply += "https://forms\.gle/JhB5MdtFsiX7zYC78"
    # Send the message with feedback form link
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')

# /donate command handler
@sbot.message_handler(regexp='donate')
@sbot.message_handler(commands=['donate'])
async def donate_info(message):
    await checker(message.chat.id)

    reply = "*__How Do I Donate?__*\n\n"

    reply += "1\. Open your preferred Mobile Banking App and navigate to the PayNow function\n"
    reply += "2\. Select the function to scan a PayNow QR Code\n"
    reply += "3\. Scan the QR Code in the link provided\n"
    reply += "4\. Confirm that the account name/UEN number corresponds to the name of your selected mosque\. In the case it is not available, you may refer to the tabung\.sg link attached below the Mosque header\.\n"
    reply += "5\. Enter your intended donation amount and complete your donation\n\n"

    reply += "If you are viewing this on your mobile device, tap on the *QR* link\. Press and hold on the QR Code to save the image to your phone\. You may also take a screenshot\.\n\n"

    reply += "In the PayNow function in your Mobile Banking App, click on the option to access your images album and select the QR Code image that you have just saved\."
    
    reply += "\n\n\n_powered by tabung\.sg_"
    # Send the message with the donate reply
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')
    await sbot.send_message(message.chat.id, "Please select a region:", reply_markup=donate_menu)

# /zakat command handler
@sbot.message_handler(regexp='zakat')
@sbot.message_handler(commands=['zakat'])
async def zakat_info(message):
    await checker(message.chat.id)
    reply = "[Zakat Singapore](https://www.zakat.sg/)"
    # Send the message with zakat link
    await sbot.send_message(message.chat.id, reply, 'Markdown')

# /daily command handler
@sbot.message_handler(regexp='daily')
@sbot.message_handler(commands=['daily'])
async def daily_command(message):
    global daily_enabled_arr
    await checker(message.chat.id)

    chat_id = str(message.chat.id)
    
    chat_info = chat_id_dict[chat_id]
    daily_timings_enabled = not chat_info.get('daily_timings_enabled', True)
    chat_info['daily_timings_enabled'] = daily_timings_enabled

    if daily_timings_enabled:
        daily_enabled_arr.append(chat_id)  # Add to the array
        await sbot.send_message(message.chat.id, "Daily Prayer Times are now enabled. \u2705")
    else:
        daily_enabled_arr.remove(chat_id)  # Remove from the array
        await sbot.send_message(message.chat.id, "Daily Prayer Times are now disabled. \u274c")



# /toggle command handler
@sbot.message_handler(regexp='toggle')
@sbot.message_handler(commands=['toggle'])
async def toggle_command(message):
    global reminders_enabled_arr
    await checker(message.chat.id)

    chat_id = str(message.chat.id)

    # Toggle the reminders state
    chat_info = chat_id_dict[chat_id]
    reminders_enabled = not chat_info.get('reminders_enabled', True)
    chat_info['reminders_enabled'] = reminders_enabled

    if reminders_enabled:
        reminders_enabled_arr.append(chat_id)  # Add to the array
        await sbot.send_message(message.chat.id, "Azan reminders are now enabled. \u2705")
    else:
        reminders_enabled_arr.remove(chat_id)  # Remove from the array
        await sbot.send_message(message.chat.id, "Azan reminders are now disabled. \u274c")

# /prereminder command handler
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

# Callback handler for the inline pre-reminder toggle keyboard
@sbot.callback_query_handler(func=lambda call: call.data.startswith('prerem_'))
async def handle_prereminder_toggle(call):
    global custom_5_enabled_arr, custom_10_enabled_arr, custom_15_enabled_arr

    idx = int(call.data.split('_')[1])
    minutes = [5, 10, 15][idx]
    chat_id = str(call.message.chat.id)

    # Ensure the user record exists and has a 3-slot array
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

    # Re-render the inline keyboard in place with updated marks
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

# /menu_off command handler
@sbot.message_handler(regexp='menu_off')
@sbot.message_handler(commands=['menu_off'])
async def menu_off_command(message):
    await checker(message.chat.id)
    reply = "Menu is disabled"
    await sbot.send_message(message.chat.id, reply, reply_markup=ReplyKeyboardRemove())

# /help command handler
@sbot.message_handler(regexp='help')
@sbot.message_handler(commands=['help'])
async def help_command(message):
  await checker(message.chat.id)
  # List of available commands
  commands = [
      "/stop - Stops the bot",
      "/menu - Displays menu buttons",
      "/menu_off - Disables menu buttons",
      "/settings - Displays current notification settings",
      "/toggle - Toggle reminders on or off",
      "/timings - Get current prayer times",
      "/daily - Toggle daily prayer times (at 5AM) notifications on or off",
      "/prereminder - Toggle 5/10/15 min pre-prayer reminders",
      "/upcoming - Get prayer times up to a week ahead (not inclusive of today)",
      # "/list - List current slots\n",
      # "/customreminder [<index>] <minutes> - Set or edit a custom reminder (0 minutes to disable)\n(e.g. /customreminder 30 creates a new 30 minute pre-reminder while /customreminder 1 45 edits the pre-reminder in Slot 1 to 45 minutes.\nOmitting <index> changes the bot to 'create' mode\nNote: This is the only command with a format)\n",
      # "/patch - Lists updates to the bot", 
      "/help - List available commands"
  ]
  # Create a message with available commands
  reply = "Help Menu (List of Commands):\n"
  reply += "\n".join(commands)
  # Send the message with available commands
  await sbot.send_message(message.chat.id, reply)


# /patch command handler
@sbot.message_handler(regexp='patch')
@sbot.message_handler(commands=['patch'])
async def patch_command(message):
  await checker(message.chat.id)
  # Patch thread
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
  # Create a message with available commands
  reply = "Patchnotes Thread:\n"
  reply += "\n".join(patch_0_0_2)
  reply += "\n".join(patch_0_0_3)
  reply += "\n".join(patch_0_0_4)
  # Send the message with available commands
  await sbot.send_message(message.chat.id, reply)

# Populate the arrays based on the loaded data
def NonAsync_loadArr(chat_id_dict):
    reminders_enabled_arr = []
    daily_enabled_arr = []
    custom_5 = []
    custom_10 = []
    custom_15 = []
    for chat_id, chat_data in chat_id_dict.items():
        if chat_data.get('reminders_enabled', True):
            reminders_enabled_arr.append(chat_id)
        if chat_data.get('daily_timings_enabled', True):
            daily_enabled_arr.append(chat_id)
        durations = (chat_data.get('custom_durations', []) + [False, False, False])[:3]
        if durations[0]:
            custom_5.append(chat_id)
        if durations[1]:
            custom_10.append(chat_id)
        if durations[2]:
            custom_15.append(chat_id)

    return [reminders_enabled_arr, daily_enabled_arr, custom_5, custom_10, custom_15]


# Populate the arrays based on the loaded data
async def loadArr(chat_id_dict):
    global reminders_enabled_arr, daily_enabled_arr
    global custom_5_enabled_arr, custom_10_enabled_arr, custom_15_enabled_arr
    for chat_id, chat_data in chat_id_dict.items():
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

    return [reminders_enabled_arr, daily_enabled_arr,
            custom_5_enabled_arr, custom_10_enabled_arr, custom_15_enabled_arr]


# Deleteing user
async def delete_user(remove_chat_id):
    await _purge_user(remove_chat_id, notify_requester=None)
        

# Shutdown function to handle cleanup before exiting
async def shutdown():
    # Save data before shutdown
    global chat_id_dict
    await save_data(chat_id_dict)
    logger.info("Bot has been shut down.")
    print("Bot has been shut down.")

async def main():
    while(True):
        try:
            await cycleCheck(
                chat_id_dict,
                reminders_enabled_arr,
                daily_enabled_arr,
                custom_5_enabled_arr,
                custom_10_enabled_arr,
                custom_15_enabled_arr,
            )

            print("Suspend")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"An error occurred in the main function: {e}")

async def poll():
    await sbot.infinity_polling()

if __name__ == '__main__':

    # Configure the logger
    logging.basicConfig(
        filename='app.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger.info("Bot is initialised and will run.")

    chat_id_dict = load_data()
    print("User profiles have been loaded")
    logger.info("User profiles have been loaded")
    database_prayer_times = NonAsync_RefreshPrayerTime()
    (reminders_enabled_arr, daily_enabled_arr,
     custom_5_enabled_arr, custom_10_enabled_arr, custom_15_enabled_arr) = NonAsync_loadArr(chat_id_dict)
    print("Prayer Times have been loaded")
    logger.info("Prayer Times have been loaded")

    logger.info("Logging begin.")

    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(poll()),
        loop.create_task(main())
    ]

    try:

        loop.run_until_complete(asyncio.wait(tasks))

    except KeyboardInterrupt:

        loop.run_until_complete(shutdown())

    finally:

        loop.close()



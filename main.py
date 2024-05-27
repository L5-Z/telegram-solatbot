import logging
import asyncio
import telebot
from telebot import apihelper
from telebot.async_telebot import AsyncTeleBot
from telebot.types import *

from storage import *
from scrapeAPI import *
from cycle import *
from blocked import *

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
global database_prayer_times
database_prayer_times = {}

# Initialize runtime arrays
reminders_enabled_arr = []
daily_enabled_arr = []
custom_5_enabled_arr = []
custom_10_enabled_arr = []
custom_15_enabled_arr = []
custom_20_enabled_arr = []
custom_25_enabled_arr = []

# Define the menus
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
toggle_menu = ReplyKeyboardMarkup(resize_keyboard=True)
info_menu = ReplyKeyboardMarkup(resize_keyboard=True)

# Main Menu buttons
main_menu.row(KeyboardButton('Notifications'), KeyboardButton('Current Timings'))
main_menu.row(KeyboardButton('Settings'), KeyboardButton('Information'))
main_menu.row(KeyboardButton('Help'))
toggle_menu.row(KeyboardButton('Reminders'), KeyboardButton('Daily Updates'))
toggle_menu.row(KeyboardButton('Back'))
info_menu.row(KeyboardButton('Qiblat'), KeyboardButton('Zakat'))
info_menu.row(KeyboardButton('Back'))

# Command handler for the /menu command
@sbot.message_handler(commands=['menu'])
async def send_menu(message):
    await sbot.send_message(message.chat.id, "Please select an option:", reply_markup=main_menu)

# Handler for processing button clicks
@sbot.message_handler(func=lambda message: True)
async def handle_click(message):
    if message.text == 'Settings' or message.text == '/settings':
        await settings_command(message)
    elif message.text == 'Current Timings' or message.text == '/timings':
        await timings_command(message)
    elif message.text == 'Notifications':
        await sbot.send_message(message.chat.id, "Edit your notification settings:", reply_markup=toggle_menu)
    elif message.text == 'Help' or message.text == '/help':
        await help_command(message)
    elif message.text == 'Reminders' or message.text == '/toggle':
        await toggle_command(message)
        await settings_command(message)
    elif message.text == 'Daily Updates' or message.text == '/daily':
        await daily_command(message)
        await settings_command(message)
    elif message.text == 'Back':
        await sbot.send_message(message.chat.id, "Back to main menu:", reply_markup=main_menu)
    elif message.text == 'Information':
        await sbot.send_message(message.chat.id, "More Information:", reply_markup=info_menu)
    elif message.text == 'Qiblat' or message.text == '/qiblat':
        await qiblat_info(message)
    elif message.text == 'Zakat' or message.text == '/zakat':
        await zakat_info(message)
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
                            blocked_users.append(chat_id)
                            chat_id_dict.pop(chat_id, None)
                            print("Removed blocker: ", chat_id, "\n\n")
                            logger.info(f"Removed {len(blocked_users)} blocked users from the chat_id_dict database.")
                        else:
                            logger.error(f"An error occurred in sending announcement: {e}")
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


# ADMIN FUNCTION (51719761): REMOVE USER
@sbot.message_handler(commands=['del'])
async def delUser(message):
    global reminders_enabled_arr, daily_enabled_arr

    if message.chat.id == 51719761:
        remove_chat_id = message.text.split(' ', 1)[1] # Extract text after the command
        print("\nAdmin is deleting user: ", remove_chat_id)
        admin_message = "Welcome Admin, the following user is being deleted:\n"
        notify = admin_message + remove_chat_id

        if remove_chat_id in chat_id_dict:
            chat_id_dict.pop(remove_chat_id, None)

            # Remove the chat ID from the arrays
            reminders_enabled_arr.remove(remove_chat_id)  # Remove from the array
            daily_enabled_arr.remove(remove_chat_id)  # Remove from the array
        
        print("User: ", remove_chat_id, " has been deleted\n")
        await sbot.send_message(message.chat.id, notify)     
    else:
        return
    
# ADMIN FUNCTION (51719761): PRINT ALL USER ID
@sbot.message_handler(commands=['dump'])
async def dumpDict(message):
    if message.chat.id == 51719761:
        print("\nAdmin is dumping user database:\n")
        data_dump = "User ID Dump:\n\n"

        for chat_id in chat_id_dict:
            data_dump += str(chat_id) + "\n"
            
        
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
            new_chat_data = {
            'reminders_enabled': chat_data.get('reminders_enabled', True),
            'daily_timings_enabled': chat_data.get('daily_timings_enabled', True),
            'custom_durations': chat_data.get('custom_durations', [False, False, False, False, False]),
            }
            chat_id_dict[chat_id] = new_chat_data
        
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

        # Remove blocked users from database
        for blocked_user in blocked_users:
            admin_message += blocked_user
            admin_message += "\n"
        
        await sbot.send_message(message.chat.id, admin_message)  
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
            logger.error(f"Failed to send announcement to {receiver}")
            if e.result.status_code == 403 and "bot was blocked by the user" in e.result.text:
                logger.warning(f"Bot was blocked by user {receiver}")
                print(f"\n\nBot was blocked by user {receiver}\n\n")
                blocked_users.append(receiver)
                chat_id_dict.pop(receiver, None)
                print("Removed blocker: ", receiver, "\n\n")
                logger.info(f"Removed {len(blocked_users)} blocked users from the chat_id_dict database.")
            else:
                logger.error(f"An error occurred in sending announcement: {e}")  
    else:
        return

# ADMIN FUNCTION (51719761): SHUTDOWN BOT
@sbot.message_handler(commands=['exit'])
async def exitBot(message):
    if message.chat.id == 51719761:
        print("Admin has initiated bot shutdown.")
        logger.info("Admin has initiated bot shutdown.")
        await shutdown()     
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
            'custom_durations': [False, False, False, False, False], # Time for 5, 10, 15, 20, 30
        }

        await save_data(chat_id_dict)

        # Add the new chat ID to the arrays
        reminders_enabled_arr.append(chat_id)
        daily_enabled_arr.append(chat_id)

        logger.info(f"Saved {chat_id} to database.")
        await sbot.send_message('51719761', f"Admin New User Joined: {chat_id}")


# Command Handlers

# /start command handler
@sbot.message_handler(regexp='start')
@sbot.message_handler(commands=['start'])
async def start_command(message):
    # Welcome message
    welcome_message = "Thanks for using my bot!\n\n"
    welcome_message += "Do /help for a list of commands\n"
    welcome_message += "Reminders are ON by default, do /toggle to turn them on\n"
    welcome_message += "Daily Prayer Time notifications (at 5AM) are ON by default, do /daily to turn them on\n\n"
    welcome_message += "Current Version: v1.0.0 (Stable Release)\n"
    welcome_message += "Updated and Patched as of 22/3/24\n"
    welcome_message += "Do /patch to view patchnotes\n\n"
    welcome_message += "Bot made by L5Z (Faatih) :)"
    await checker(message.chat.id)
    await sbot.send_message(message.chat.id, welcome_message)

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

# /qiblat command handler
@sbot.message_handler(regexp='qiblat')
@sbot.message_handler(commands=['qiblat'])
async def qiblat_info(message):
    await checker(message.chat.id)
    reply = "\U0001F54B _*Qiblat for Singapore:*_\n\n"
    reply += "\U0001F9ED *293* degrees \[NW\]"
    # Send the message with qiblat directions
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')

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



# /help command handler
@sbot.message_handler(regexp='help')
@sbot.message_handler(commands=['help'])
async def help_command(message):
  await checker(message.chat.id)
  # List of available commands
  commands = [
      "/menu - Displays menu buttons",
      "/settings - Displays current notification settings",
      "/toggle - Toggle reminders on or off",
      "/timings - Get current prayer times",
      "/daily - Toggle daily prayer times (at 5AM) notifications on or off",
      # "/list - List current slots\n",
      # "/customreminder [<index>] <minutes> - Set or edit a custom reminder (0 minutes to disable)\n(e.g. /customreminder 30 creates a new 30 minute pre-reminder while /customreminder 1 45 edits the pre-reminder in Slot 1 to 45 minutes.\nOmitting <index> changes the bot to 'create' mode\nNote: This is the only command with a format)\n",
      # "/patch - Lists updates to the bot", 
      "/help - List available commands"
  ]
  # Create a message with available commands
  reply = "Available commands:\n"
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
    for chat_id, chat_data in chat_id_dict.items():
        if chat_data.get('reminders_enabled', True):
            reminders_enabled_arr.append(chat_id)
        if chat_data.get('daily_timings_enabled', True):
            daily_enabled_arr.append(chat_id)
    
    return [reminders_enabled_arr, daily_enabled_arr]


 # Populate the arrays based on the loaded data
async def loadArr(chat_id_dict):
    reminders_enabled_arr = []
    daily_enabled_arr = []
    for chat_id, chat_data in chat_id_dict.items():
        if chat_data.get('reminders_enabled', True):
            reminders_enabled_arr.append(chat_id)
        if chat_data.get('daily_timings_enabled', True):
            daily_enabled_arr.append(chat_id)
    
    return [reminders_enabled_arr, daily_enabled_arr]


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
<<<<<<< Updated upstream
            await cycleCheck(chat_id_dict, database_prayer_times)
=======
            await cycleCheck(chat_id_dict)
>>>>>>> Stashed changes
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
    # Get the logger instance
    logger = logging.getLogger(__name__)

    logger.info("Bot is initialised and will run.")

    chat_id_dict = load_data()
    print("User profiles have been loaded")
    logger.info("User profiles have been loaded")
    database_prayer_times = NonAsync_RefreshPrayerTime()
    reminders_enabled_arr, daily_enabled_arr = NonAsync_loadArr()
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



import logging
import asyncio
import telebot
from telebot import apihelper
from telebot.async_telebot import AsyncTeleBot
from telebot.types import *

from storage import *
from scrapeAPI import *
from convertAPI import *
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

        checker(new_chat_id)
        
        print("User: ", new_chat_id, " has been added\n")
        await sbot.send_message(message.chat.id, notify)     
    else:
        return


# ADMIN FUNCTION (51719761): REMOVE USER
@sbot.message_handler(commands=['del'])
async def addUser(message):
    if message.chat.id == 51719761:
        remove_chat_id = message.text.split(' ', 1)[1] # Extract text after the command
        print("\nAdmin is deleting user: ", remove_chat_id)
        admin_message = "Welcome Admin, the following user is being deleted:\n"
        notify = admin_message + remove_chat_id

        if remove_chat_id in chat_id_dict:
            chat_id_dict.pop(remove_chat_id, None)
        
        print("User: ", remove_chat_id, " has been deleted\n")
        await sbot.send_message(message.chat.id, notify)     
    else:
        return
    
# ADMIN FUNCTION (51719761): PRINT ALL USER ID
@sbot.message_handler(commands=['dump'])
async def addUser(message):
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
async def addUser(message):
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
async def announce(message):
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
async def announce(message):
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

# ADMIN FUNCTION (51719761): SHUTDOWN BOT
@sbot.message_handler(commands=['exit'])
async def addUser(message):
    if message.chat.id == 51719761:
        print("Admin has initiated bot shutdown.")
        logger.info("Admin has initiated bot shutdown.")
        await shutdown()     
    else:
        return

# Check chat_id if present in dict
def checker(chat_id):
    global chat_id_dict

    # Convert chat_id to string to ensure consistency
    chat_id = str(chat_id)

    if chat_id not in chat_id_dict:
        chat_id_dict[chat_id] = {
            'reminders_enabled': True,
            'daily_timings_enabled': True,
            'custom_durations': [False, False, False, False, False], # Time for 5, 10, 15, 20, 30
        }


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
    checker(message.chat.id)
    await sbot.send_message(message.chat.id, welcome_message)

# /settings command handler
@sbot.message_handler(regexp='settings')
@sbot.message_handler(commands=['settings'])
async def settings_command(message):
    checker(message.chat.id)
    
    chat_id = str(message.chat.id)
    chat_info = chat_id_dict[chat_id]

    reply = "_Current Settings:_\n\n"
    reply += f"*Reminders Enabled:* {chat_info['reminders_enabled']}\n"
    reply += f"*Daily Timings Enabled:* {chat_info['daily_timings_enabled']}\n\n"

    # Send the message with prayer times
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')

# /timings command handler
@sbot.message_handler(regexp='timings')
@sbot.message_handler(commands=['timings'])
async def timings_command(message):
    checker(message.chat.id)
    reply = await printTimes()
    # Send the message with prayer times
    await sbot.send_message(message.chat.id, reply, 'MarkdownV2')


# /daily command handler
@sbot.message_handler(regexp='daily')
@sbot.message_handler(commands=['daily'])
async def daily_command(message):
    checker(message.chat.id)

    chat_id = str(message.chat.id)
    
    chat_info = chat_id_dict[chat_id]
    daily_timings_enabled = not chat_info.get('daily_timings_enabled', True)
    chat_info['daily_timings_enabled'] = daily_timings_enabled

    if daily_timings_enabled:
        await sbot.send_message(message.chat.id, "Daily Prayer Times are now enabled.")
    else:
        await sbot.send_message(message.chat.id, "Daily Prayer Times are now disabled.")



# /toggle command handler
@sbot.message_handler(regexp='toggle')
@sbot.message_handler(commands=['toggle'])
async def toggle_command(message):
    checker(message.chat.id)

    chat_id = str(message.chat.id)

    # Toggle the reminders state
    chat_info = chat_id_dict[chat_id]
    reminders_enabled = not chat_info.get('reminders_enabled', True)
    chat_info['reminders_enabled'] = reminders_enabled

    if reminders_enabled:
        await sbot.send_message(message.chat.id, "Azan reminders are now enabled.")
    else:
        await sbot.send_message(message.chat.id, "Azan reminders are now disabled.")



# /help command handler
@sbot.message_handler(regexp='help')
@sbot.message_handler(commands=['help'])
async def help_command(message):
  checker(message.chat.id)
  # List of available commands
  commands = [
      "/toggle - Toggle reminders on or off",
      "/timings - Get current prayer times",
      "/daily - Toggle daily prayer times (at 5AM) notifications on or off",
      "/list - List current slots\n",
      "/customreminder [<index>] <minutes> - Set or edit a custom reminder (0 minutes to disable)\n(e.g. /customreminder 30 creates a new 30 minute pre-reminder while /customreminder 1 45 edits the pre-reminder in Slot 1 to 45 minutes.\nOmitting <index> changes the bot to 'create' mode\nNote: This is the only command with a format)\n",
      "/patch - Lists updates to the bot", 
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
  checker(message.chat.id)
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
            logger.info("Starting the main function...")
            
            logger.info("Initialising cycleCheck in main now")
            await cycleCheck(chat_id_dict)
            logger.info("Suspending now")
            print("Suspend")
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"An error occurred in the main function: {e}")

async def poll():
    await sbot.infinity_polling()

if __name__ == '__main__':

    chat_id_dict = load_data()
    print("User profiles have been loaded")

    # Configure the logger
    logging.basicConfig(
        filename='app.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    # Get the logger instance
    logger = logging.getLogger(__name__)
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



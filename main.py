import os
import asyncio
import schedule
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from storage import *
from scrapeAPI import *
from convertAPI import *

# Bot token
with open('botKey.txt', 'r') as file:
    bot_key = str(file.read())

TELEGRAM_BOT_TOKEN = bot_key

# Create a Bot instance with bot token
sbot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)

# Initialize a global dictionary to store chat_id information
global chat_id_dict
chat_id_dict = {}

# ADMIN FUNCTION (51719761): ANOUNCEMENTS
@sbot.message_handler(commands=['announce'])
async def announce(message):
    if message.chat.id == 51719761:
        print("\nAdmin is sending an announcement")
        announcement_text = message.text.split(' ', 1)[1] # Extract text after the command
        admin_message = "Welcome Admin, the following announcement has been posted:\n"
        welcome_admin = admin_message + announcement_text

        for chat_id, _ in chat_id_dict.items():
                if chat_id == 51719761:
                    await sbot.send_message(chat_id, welcome_admin)
                    continue
                else:
                    await sbot.send_message(chat_id, announcement_text)
        
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
    

# Check chat_id if present in dict
def checker(chat_id):
    global chat_id_dict

    # Convert chat_id to string to ensure consistency
    chat_id = str(chat_id)

    if chat_id not in chat_id_dict:
        chat_id_dict[chat_id] = {
            'reminders_enabled': True,
            'daily_timings_enabled': False,
            'custom_durations': [False, False, False, False, False], # Time for 5, 10, 15, 20, 30
            'custom_reminder_sent': False,
            'prayer_reminder_sent': False
        }


# Command Handlers

#Basics

# Function to send a reminder
async def send_reminder(message):
    await sbot.send_message(message.chat.id, message)

# /start command handler
@sbot.message_handler(regexp='start')
@sbot.message_handler(commands=['start'])
async def start_command(message):
    # Welcome message
    welcome_message = "Thanks for using my bot!\n\nDo /help for a list of commands\nReminders are ON by default, do /toggle to turn them on\n\nCurrent Version: v0.0.4\nUpdated and Patched as of 29/9/23\nDo /patch to view patchnotes\n\n"
    welcome_message += "Bot made by L5Z (Faatih) :)"
    checker(message.chat.id)
    await sbot.send_message(message.chat.id, welcome_message)

# /echo
#@sbot.message_handler(regexp=['echo'])
@sbot.message_handler(commands=['echo'])
async def echo_msg(message):
    text = message.text.split(' ', 1)[1] # Extract text after the command
    await sbot.send_message(message.chat.id, text)

# /test command handler
@sbot.message_handler(regexp='test')
@sbot.message_handler(commands=['test'])
async def test_command(message):
    # Execute your test logic here
    await sbot.send_message(message.chat.id, "Test command has been run. Bot is up and running.\n Use '/help' for command list")


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
    chat_id = message.chat.id
    checker(chat_id)
    chat_info = chat_id_dict[chat_id]
    daily_timings_enabled = not chat_info.get('daily_timings_enabled', False)
    chat_info['daily_timings_enabled'] = daily_timings_enabled

    if daily_timings_enabled:
        await sbot.send_message(message.chat.id, "Daily Times are now enabled.")
    else:
        await sbot.send_message(message.chat.id, "Daily Times are now disabled.")



# /toggle command handler
@sbot.message_handler(regexp='toggle')
@sbot.message_handler(commands=['toggle'])
async def toggle_command(message):
    checker(message.chat.id)

    chat_id = str(message.chat.id)

    # Toggle the reminders state
    if chat_id in chat_id_dict:
        chat_info = chat_id_dict[chat_id]
        reminders_enabled = not chat_info.get('reminders_enabled', False)
        chat_info['reminders_enabled'] = reminders_enabled

        if reminders_enabled:
            await sbot.send_message(message.chat.id, "Azan reminders are now enabled.")
        else:
            await sbot.send_message(message.chat.id, "Azan reminders are now disabled.")
    else:
        await sbot.send_message(message.chat.id, "Please use /start to initialize the chat.")


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

print("Bot will now run...")

# Shutdown function to handle cleanup before exiting
async def shutdown():

    # Get all running tasks
    tasks = [task for task in asyncio.all_tasks() if not task.done()]

    # Cancel all tasks
    for task in tasks:
        task.cancel()

    # Wait for all tasks to be cancelled
    await asyncio.gather(*tasks, return_exceptions=True)

    # Save data before shutdown
    global chat_id_dict
    await save_data(chat_id_dict)

    print("Bot has been shut down.")

async def main():
    
    chat_id_dict = await load_data()
    print(chat_id_dict)
    
    await cycleCheck(chat_id_dict)
    print("Suspend...")
    await asyncio.sleep(60)
    await main()

async def run_bot():
    await sbot.infinity_polling(interval=1, timeout=0)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(run_bot()),
        loop.create_task(main())
    ]
    try:
        loop.run_until_complete(asyncio.wait(tasks))
    except (KeyboardInterrupt, SystemExit):
        loop.run_until_complete(shutdown())
    finally:
        loop.close()


import os
import requests
import httpx
import json
import schedule
import threading
import time
import pytz
from datetime import datetime, timedelta, timezone
from itertools import islice
from threading import Timer
from requests.exceptions import ConnectionError
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext, ApplicationBuilder
from asyncio import Queue

# Set the maximum connection pool size to 8
#request = Request(con_pool_size=20)

# Your bot token and chat ID
with open('botKey.txt', 'r') as file:
    bot_key = str(file.read())

TELEGRAM_BOT_TOKEN = bot_key
chat_id = None

# Build app
app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Establish Chat IDs


# Initialize a global dictionary to store chat_id information
global chat_id_dict
chat_id_dict = {}

# Custom durations in minutes (initially empty)
custom_durations = [False, False, False, False, False], #Time for 5,10,15,20,30

# Set the timezone to Singapore (Asia/Singapore)
singapore_timezone = pytz.timezone('Asia/Singapore')

# Global variable to track whether reminders are enabled or disabled
reminders_enabled = False
daily_timings_enabled = False

# Function to scrape prayer times from the website
def GetPrayerTime():
  url = 'https://www.muis.gov.sg/api/pagecontentapi/GetPrayerTime'
  try:
    response = requests.get(url)
    if response.status_code == 200:
      data = response.json()
      return data
    else:
      print(f"Failed to retrieve data. Status code: {response.status_code}")
      return None
  except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
    return None
  except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
    return None


def checker(update: Update, context: CallbackContext):
    global chat_id
    global chat_id_dict
    global custom_durations
    global reminders_enabled
    global daily_timings_enabled
    chat_id = update.message.chat_id
    bot = context.bot

    if chat_id not in chat_id_dict:
        chat_id_dict[chat_id] = {
            'reminders_enabled': False,  # Correctly set 'reminders_enabled' here
            'daily_timings_enabled': False,
            'custom_durations': [False, False, False, False, False], #Time for 5,10,15,20,30
            'custom_reminder_sent': False,
            'prayer_reminder_sent': False
        }
    else:
        reminders_enabled = chat_id_dict[chat_id]['reminders_enabled']  # Corrected line
        daily_timings_enabled = chat_id_dict[chat_id]['daily_timings_enabled']  # Corrected line
        custom_durations = chat_id_dict[chat_id]['custom_durations'].copy()

    # Rest of your checker function...

    
# Function to send a reminder
def send_reminder(bot, chat_id, message):
  bot.send_message(chat_id, message)

# Function to send a custom reminder
def send_custom_reminder(bot, chat_id, prayer, time, custom_timedelta):
    prayer_time = datetime.strptime(time, '%H:%M')  # Use the correct format for 24-hour time
    c_timedelta = timedelta(minutes=custom_timedelta)  # Convert custom_timedelta to a timedelta object
    reminder_time = prayer_time - c_timedelta
    reminder_message = f'{prayer} is in {custom_timedelta} minutes'
    send_reminder(bot, chat_id, reminder_message)



# Command handlers


# /start command handler
def start_command(update: Update, context: CallbackContext):
  global chat_id
  chat_id = update.message.chat_id
  bot = context.bot
  checker(update, context)
  
  # Save chat ID and timestamp to a text file
  current_time_str = datetime.now().isoformat()
  with open("chat_ids.txt", "a") as chat_id_file:
    chat_id_file.write(f"Chat ID: {chat_id} - Timestamp: {current_time_str}\n")

  # Welcome message
  welcome_message = "Thanks for using my bot!\n\nDo /help for a list of commands\nReminders are OFF by default, do /toggle to turn them on\n\nCurrent Version: v0.0.4\nUpdated and Patched as of 29/9/23\nDo /patch to view patchnotes\n\n"
  welcome_message += "Bot made by L5Z (Faatih) :)"
  bot.send_message(chat_id, welcome_message)


# /test command handler
def test_command(update: Update, context: CallbackContext):
  global chat_id
  chat_id = update.message.chat_id
  bot = context.bot
  checker(update, context)
  # Execute your test logic here
  bot.send_message(
      chat_id,
      "Test command has been run. Bot is up and running.\n Use '/help' for command list"
  )


# /timings command handler
def timings_command(update: Update, context: CallbackContext):
  global chat_id
  chat_id = update.message.chat_id
  bot = context.bot

  # Get current prayer times
  prayer_times = GetPrayerTime()
  if prayer_times is not None:
    # Extract the date and Hijri information
    prayer_date = prayer_times.get('PrayerDate', 'N/A')
    hijri_date = prayer_times.get('Hijri', 'N/A')

    # Extract the AM and PM timings from the JSON response
    subuh_time = prayer_times.get('Subuh', 'N/A')
    syuruk_time = prayer_times.get('Syuruk', 'N/A')
    zohor_time = prayer_times.get('Zohor', 'N/A')
    asar_time = prayer_times.get('Asar', 'N/A')
    maghrib_time = prayer_times.get('Maghrib', 'N/A')
    isyak_time = prayer_times.get('Isyak', 'N/A')

    # Create a message with the prayer times and additional information
    message = f"Current Prayer Times for {prayer_date}\n----------------------------------------\nHijri: {hijri_date}\n----------------------------------------\n\n"
    message += f"Subuh: {subuh_time} AM\n"
    message += f"Syuruk: {syuruk_time} AM\n"
    message += f"Zohor: {zohor_time} PM\n"
    message += f"Asar: {asar_time} PM\n"
    message += f"Maghrib: {maghrib_time} PM\n"
    message += f"Isyak: {isyak_time} PM\n"
    # Send the message with prayer times
    bot.send_message(chat_id, message)
  else:
    bot.send_message(chat_id, "Failed to retrieve prayer times.")

# Define a command handler for /list
def list_command(update: Update, context: CallbackContext):
    global chat_id
    chat_id = update.message.chat_id
    bot = context.bot
    checker(update, context)
    # Check if there are any slots to list
    if custom_durations:
        # Convert integers to strings and label the slots from 1 to 5
        slots_message = "\n".join([f"Slot {i + 1}: {duration} minutes" for i, duration in enumerate(custom_durations)])
        response_message = f"Current Slots:\n{slots_message}"
    else:
        response_message = "There are no slots in use."

    bot.send_message(chat_id, response_message)

# /customreminder command handler
def custom_reminder_command(update: Update, context: CallbackContext):
    global chat_id
    global chat_id_dict
    global custom_durations  # Make custom_durations global
    chat_id = update.message.chat_id
    bot = context.bot
    args = context.args  # Get the user's command arguments
    checker(update, context)

    if chat_id in chat_id_dict:
        chat_info = chat_id_dict[chat_id]
        custom_durations = chat_info.get('custom_durations', custom_durations)

        if args:
            if len(args) == 1:
                # User provided only minutes, create a new custom reminder
                try:
                    custom_duration = int(args[0])
                    if custom_duration >= 0:
                        if all(custom_durations):
                            current_values = "\n".join([
                                f"Slot {i + 1}: {d} minutes"
                                for i, d in enumerate(custom_durations)
                            ])
                            bot.send_message(
                                chat_id,
                                f"Your current custom reminder durations are:\n{current_values}"
                            )
                            bot.send_message(chat_id, "All custom reminder slots are occupied. Please specify the index of the reminder to overwrite (starting from 1), or use a different duration.")
                        else:
                            index_to_overwrite = None
                            for i, duration in enumerate(custom_durations):
                                if duration == 0:
                                    custom_durations[i] = custom_duration
                                    chat_info['custom_durations'] = custom_durations.copy()  # Update custom_durations in chat_info
                                    bot.send_message(
                                        chat_id,
                                        f"Custom reminder set for {custom_duration} minutes before azan in slot {i + 1}."
                                    )
                                    break
                                elif duration == custom_duration:
                                    index_to_overwrite = i

                            if index_to_overwrite is not None:
                                chat_info['custom_durations'] = custom_durations.copy()  # Update custom_durations in chat_info
                                bot.send_message(
                                    chat_id,
                                    f"Custom reminder updated for {custom_duration} minutes before azan in slot {index_to_overwrite + 1}."
                                )
                    else:
                        bot.send_message(
                            chat_id,
                            "Invalid custom duration. Please provide a non-negative number of minutes."
                        )
                except ValueError:
                    bot.send_message(
                        chat_id,
                        "Invalid custom duration. Please provide a valid number of minutes."
                    )
            elif len(args) == 2:
                # User provided both index and minutes, edit an existing custom reminder
                try:
                    index = int(args[0]) - 1  # Subtract 1 to get the zero-based index
                    new_duration = int(args[1])
                    if 0 <= index < len(custom_durations):
                        custom_durations[index] = new_duration
                        chat_info['custom_durations'] = custom_durations.copy()  # Update custom_durations in chat_info
                        bot.send_message(
                            chat_id,
                            f"Custom reminder duration for Slot {index + 1} updated to {new_duration} minutes before azan."
                        )
                    else:
                        bot.send_message(
                            chat_id, "Invalid index. Please specify a valid slot index.")
                except (ValueError, IndexError):
                    bot.send_message(
                        chat_id, "Invalid index or duration. Please specify valid values.")
            else:
                bot.send_message(
                    chat_id,
                    "Invalid command. Usage: /customreminder [<index>] <minutes>")
        else:
            bot.send_message(
                chat_id,
                "Please provide a custom duration in minutes with the command. Usage: /customreminder [<index>] <minutes>")
    else:
        bot.send_message(chat_id, "Please use /start to initialize the chat.")

# Rest of your code...



# /daily command handler
def daily_command(update: Update, context: CallbackContext):
    global chat_id_dict
    chat_id = update.message.chat_id
    bot = context.bot
    checker(update, context)

    if chat_id in chat_id_dict:
        chat_info = chat_id_dict[chat_id]
        daily_timings_enabled = not chat_info.get('daily_timings_enabled', False)
        chat_info['daily_timings_enabled'] = daily_timings_enabled

        if daily_timings_enabled:
            # Schedule the /timings command to run daily at a specific time (e.g., 3 AM)
            schedule.every().day.at("05:00").do(timings_command, update, context)

        else:
            # Clear the scheduled job for /timings if daily timings are disabled
            schedule.clear("05:00")

        if daily_timings_enabled:
            bot.send_message(chat_id, "Daily Times are now enabled.")
        else:
            bot.send_message(chat_id, "Daily Times are now disabled.")
    else:
        bot.send_message(chat_id, "Please use /start to initialize the chat.")

# Rest of your code...



# /toggle command handler
def toggle_command(update: Update, context: CallbackContext):
    global chat_id_dict
    chat_id = update.message.chat_id
    bot = context.bot
    checker(update, context)

    # Toggle the reminders state
    if chat_id in chat_id_dict:
        chat_info = chat_id_dict[chat_id]
        reminders_enabled = not chat_info.get('reminders_enabled', False)
        chat_info['reminders_enabled'] = reminders_enabled

        if reminders_enabled:
            bot.send_message(chat_id, "Reminders are now enabled.")
        else:
            bot.send_message(chat_id, "Reminders are now disabled.")
    else:
        bot.send_message(chat_id, "Please use /start to initialize the chat.")

# Rest of your code...



# /help command handler
def help_command(update: Update, context: CallbackContext):
  global chat_id
  chat_id = update.message.chat_id
  bot = context.bot
  # List of available commands
  commands = [
      "/toggle - Toggle reminders on or off",
      "/timings - Get current prayer times",
      "/daily - Toggle daily prayer times (at 5AM) on or off",
      "/list - List current slots\n",
      "/customreminder [<index>] <minutes> - Set or edit a custom reminder (0 minutes to disable)\n(e.g. /customreminder 30 creates a new 30 minute pre-reminder while /customreminder 1 45 edits the pre-reminder in Slot 1 to 45 minutes.\nOmitting <index> changes the bot to 'create' mode\nNote: This is the only command with a format)\n",
      "/patch - Lists updates to the bot", 
      "/help - List available commands"
  ]
  # Create a message with available commands
  message = "Available commands:\n"
  message += "\n".join(commands)
  # Send the message with available commands
  bot.send_message(chat_id, message)


# /patch command handler
def patch_command(update: Update, context: CallbackContext):
  global chat_id
  chat_id = update.message.chat_id
  bot = context.bot
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
  message = "Patchnotes Thread:\n"
  message += "\n".join(patch_0_0_2)
  message += "\n".join(patch_0_0_3)
  message += "\n".join(patch_0_0_4)
  # Send the message with available commands
  bot.send_message(chat_id, message)


# Function to run the scraper
def run_scraper():
  # Get current prayer times
  prayer_times = GetPrayerTime()
  if prayer_times is not None:
    # You can process the prayer times here if needed
    pass
  else:
    print("Failed to retrieve prayer times.")


# Create a Bot instance with your bot token
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Create an update queue
update_queue = Queue()
# Now initialize the Updater with both bot and update_queue, Create an Updater with the Bot instance
updater = Updater(bot=bot, update_queue=update_queue)

# Register the command handlers
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("test", test_command))
app.add_handler(CommandHandler("timings", timings_command))
app.add_handler(CommandHandler("list", list_command))
app.add_handler(CommandHandler("customreminder", custom_reminder_command))
app.add_handler(CommandHandler("daily", daily_command))
app.add_handler(CommandHandler("toggle", toggle_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("patch", patch_command))

# Start the bot
updater.start_polling()

print("Bot will now run...")

# Schedule the scraper to run daily at 4 AM SGT
schedule.every().day.at("04:00").do(run_scraper)

# Function to convert 12-hour time to 24-hour time
def convert_to_24_hour_format(time_str):
    try:
        dt = datetime.strptime(time_str, '%I:%M %p')
        return dt.strftime('%H:%M')
    except ValueError:
        return time_str  # Return the input unchanged if it's not in the expected format

# Function to manually add AM/PM based on prayer type
def add_am_pm(prayer_times_dict):
    for prayer, time in prayer_times_dict.items():
        if prayer in ("Subuh", "Syuruk"):
            prayer_times_dict[prayer] = f"{time} AM"
        else:
            prayer_times_dict[prayer] = f"{time} PM"
    return prayer_times_dict



def set_prayer_reminder_sent_false(chat_info):
    chat_info['prayer_reminder_sent'] = False

def set_custom_reminder_sent_false(chat_info):
    chat_info['custom_reminder_sent'] = False

# Main loop to check and send reminders
while True:
    print("current chatid ", chat_id)
    now = datetime.now(singapore_timezone)  # Use the Singapore timezone

    # Get prayer times
    prayer_times_ori = GetPrayerTime()

    # Remove the 'Hijri' and 'PrayerDate' key and value from the dictionary
    date_dict = {}

    if prayer_times_ori is not None:
      date_dict['Hijri'] = prayer_times_ori.pop('Hijri')
      date_dict['PrayerDate'] = prayer_times_ori.pop('PrayerDate')
    else:
      continue
  
    # Add AM/PM indications based on prayer type
    prayer_times_with_am_pm = add_am_pm(prayer_times_ori)
  
    # Convert prayer times to 24-hour format in SGT, excluding 'PrayerDate'
    prayer_times = {prayer: convert_to_24_hour_format(time) for prayer, time in prayer_times_with_am_pm.items() if prayer != 'PrayerDate'}

    # Extract the date value and convert it to a datetime object
    prayer_date_str = date_dict.get('PrayerDate', '')  # Use the original dictionary here
    prayer_date_format = '%d %B %Y'  # Define the format of the date string
    try:
        prayer_date = datetime.strptime(prayer_date_str, prayer_date_format)
    except ValueError:
        print("Invalid date format")
        continue  # Exit the function if the date format is invalid


    prayer_times.pop('PrayerDate', None)

    # Initialize variables for nearest time and threshold
    nearest_time = None
    threshold_hour = None
    threshold_minute = None

    next_waktu = False
    # Find the nearest upcoming prayer time
    for prayer, masa in prayer_times.items():
        if prayer == 'PrayerDate':
            continue  # Skip 'PrayerDate' key

        # Convert the masa time to a datetime object
        masa_time = datetime.strptime(masa, '%H:%M')
        
        # Combine the date and time
        prayer_time = prayer_date.replace(
            hour=masa_time.hour,
            minute=masa_time.minute,
            second=0,
            microsecond=0,
            tzinfo=timezone(timedelta(hours=8))
        )
        
        if prayer_time > now and (nearest_time is None or prayer_time < nearest_time):
            nearest_time = prayer_time
            threshold_hour = prayer_time.hour
            threshold_minute = prayer_time.minute
            next_waktu = True
            break

    # Check if a nearest prayer time was found
    print("saved: ", chat_id_dict)
    if nearest_time is not None:
        # Define the threshold time as the nearest upcoming prayer time
        threshold_time = now.replace(
          hour=threshold_hour,
          minute=threshold_minute,
          second=0,
          microsecond=0,
          tzinfo=timezone(timedelta(hours=8))
        )

        # Iterate through chat_id_dict to check and update values
        for chat_id, chat_info in chat_id_dict.items():
            # Check and update chat_info values as needed
            # Send reminders when now >= threshold time
            if chat_info['reminders_enabled'] and now <= threshold_time + timedelta(minutes=1) and not chat_info['prayer_reminder_sent'] and now >= threshold_time:
                reminder_message = f'{prayer} time: {masa}'
                send_reminder(bot, chat_id, reminder_message)
                chat_info['prayer_reminder_sent'] = True
                t = Timer(65, set_prayer_reminder_sent_false, args=(chat_info,))
                t.start()

            # Check if 'custom_duration' key exists in chat_info
            if chat_info['custom_durations']:
                # Trigger the custom reminders based on custom durations
                for i, custom_duration in enumerate(chat_info.get('custom_durations', [])):
                    # Calculate the time difference as a timedelta
                    time_difference = nearest_time - timedelta(minutes=custom_duration)
                    if now >= time_difference and now <= time_difference + timedelta(minutes=1) and not chat_info['custom_reminder_sent']:
                        # Trigger the custom reminder for slot i
                        send_custom_reminder(bot, chat_id, f"{prayer}", masa, custom_duration)
                        chat_info['custom_reminder_sent'] = True
                        t = Timer(65, set_custom_reminder_sent_false, args=(chat_info,))
                        t.start()

    
    # Run scheduled tasks
    schedule.run_pending()

    # Sleep for 1 secs before checking again
    time.sleep(1)

#finally works

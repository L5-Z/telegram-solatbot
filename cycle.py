# Converts solat times into 24-hour format in SGT and handles time based events
import re
import pytz
import datetime
import logging
import asyncio

from telebot.async_telebot import AsyncTeleBot
from datetime import *
from typing import List

from scrapeAPI import *
from blocked import *
from storage import save_data
from main import database_prayer_times, loadArr, delete_user

logger = logging.getLogger(__name__)

global upcoming_prayer_time
upcoming_prayer_time = None
global change_prayer_time
change_prayer_time = None


# Bot token
with open('botKey.txt', 'r') as file:
    bot_key = str(file.read())

TELEGRAM_BOT_TOKEN = bot_key

# Create a Bot instance with bot token
sbot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)

# Set the timezone to Singapore (Asia/Singapore)
sg_timezone = pytz.timezone('Asia/Singapore')
custom_timezone = pytz.FixedOffset(480) # Default 480 for SG, 450 for 7h:30mins ahead UTC and behind SG by 30 mins


# Function to format reminder text
async def format_reminder(chat_id, prayer, masa):
    masa = masa[:5]
    try:
        dt = datetime.strptime(masa, '%H:%M')
        masa = dt.strftime('%I:%M %p')
    except ValueError as e:
        logger.error(f"ValueError converting masa to 12H, send_reminder: {e}")
    finally:
        header_art = '\U0001F54B'

        if prayer == "Subuh":
            header_art = '\U0001F30C'
        if prayer == "Syuruk":
            header_art = '\U0001F305'
        if prayer == "Zohor":
            header_art = '\U0001F3D9'
        if prayer == "Asar":
            header_art = '\U0001F307'
        if prayer == "Maghrib":
            header_art = '\U0001F304'
        if prayer == "Isyak":
            header_art = '\U0001F303'

        reminder_message = f'{header_art} It is now *{prayer} ({masa})* {header_art}\n\n'

        if prayer == "Syuruk":
            reminder_message += "\u2600\uFE0F The sun is up! \u2600\uFE0F"
        else:
            reminder_message += "May your fardh prayer be blessed! \U0001F932"

        # Send message
        await sbot.send_message(chat_id, reminder_message, 'Markdown')


# Execute the send_reminder
async def send_reminder(chat_id: str, prayer: str, masa: str, reminders_enabled_arr, upcoming_prayer_name):
    # Iterate through chat_id_dict to send reminders
    #for chat_id, chat_info in chat_id_dict.items():
    try:
        await format_reminder(chat_id, prayer, masa)
        logger.info(f"Sent reminder to {chat_id} for {upcoming_prayer_name} prayer")
        print("sent reminder", chat_id)
    
    except telebot.apihelper.ApiException as e:
        if "bot was blocked by the user" in e.result.text:
            logger.warning(f"Bot was blocked by user {chat_id}")
            print(f"\n\nBot was blocked by user {chat_id}\n\n")

            reminders_enabled_arr.remove(chat_id)
            await delete_user(chat_id)

            print("Removed blocker: ", chat_id, "\n\n")
            logger.info(f"Removed {len(blocked_users)} blocked users from the chat_id_dict database.")
        else:
            logger.error(f"An error occurred in sending reminders: {e}")
    
    finally:
        return

# Bulk Send reminders at once
async def bulk_send_reminders(chat_ids: List[str], prayer: str, masa: str, upcoming_prayer_name):
    tasks = [send_reminder(chat_id, prayer, masa, chat_ids, upcoming_prayer_name) for chat_id in chat_ids]
    await asyncio.gather(*tasks)

# Schedule the scraper to run daily at 5 AM SGT
async def scheduleRun(chat_id_dict):

    # Iterate through chat_id_dict to check relevant ids for sending
    for chat_id, chat_info in chat_id_dict.items():
        if chat_info['daily_timings_enabled']:

            try:
                    # Try to send the reminder to check if the bot is blocked
                    # fetch formatted times
                    times_text = await printTimes()

                    # Send message
                    await sbot.send_message(chat_id, times_text, 'MarkdownV2')
                    logger.info(f"Sent daily reminder to {chat_id}")
                    print("sent reminder", chat_id)
            except telebot.apihelper.ApiException as e:
                if "bot was blocked by the user" in e.result.text: # e.result.status_code == 403 and 
                    logger.warning(f"Bot was blocked by user {chat_id}")
                    print(f"\n\nBot was blocked by user {chat_id}\n\n")
                    blocked_users.append(chat_id)
                    chat_id_dict.pop(chat_id, None)
                    print("Removed blocker: ", chat_id, "\n\n")
                    logger.info(f"Removed {len(blocked_users)} blocked users from the chat_id_dict database.")
                else:
                    logger.error(f"An error occurred in sending reminders: {e}")
            finally:
                continue

    await save_data(chat_id_dict)
    logger.info(f"Updated database.")
    print("Scheduled daily has been run\n")


async def cycleCheck(chat_id_dict, reminders_enabled_arr, daily_enabled_arr):

    now = datetime.now(sg_timezone) # Use the Singapore timezone
    new_day = now.replace(hour=23, minute=59, second=0, microsecond=0)

    global upcoming_prayer_time, change_prayer_time
    global database_prayer_times
    
    # Get raw prayer time data
    solatTimesRaw = database_prayer_times
    if solatTimesRaw is None or not solatTimesRaw:
        logger.error("Failed to retrieve prayer times from local database scan")
        logger.info("Fetching from API database")
        database_prayer_times = await RefreshPrayerTime()
        logger.info("Successfully fetched")
        return
    print("RAW:", solatTimesRaw)

    # Check reminder array
    # Check daily array
    reminders_arr = reminders_enabled_arr
    daily_arr = daily_enabled_arr
    if reminders_arr is None or not reminders_arr or daily_arr is None or not daily_arr:
        logger.error("Failed to retrieve runtime reminder/daily array from local database")
        reminders_enabled_arr, daily_enabled_arr = await loadArr(chat_id_dict)
        return
    print("reminders_arr:", reminders_arr)
    print("daily_arr:", daily_arr)
    
    # Update times
    AM_12 = now.replace(hour=0, minute=1, second=0, microsecond=0)
    if now < AM_12 + timedelta(minutes=2) and now >= AM_12:
        logger.info("Updating Prayer Times")
        database_prayer_times = await RefreshPrayerTime()
        print("Updated: ", database_prayer_times)
        logger.info("Entering deep sleep after 12:00 AM")
        await asyncio.sleep(17100)
        return
    
    # /daily command
    # Set the target time to 5:00 AM
    AM_5 = now.replace(hour=5, minute=0, second=0, microsecond=0)
    if now < AM_5 + timedelta(minutes=1) and now >= AM_5:
        logger.info("Sending daily prayer times at 5:00 AM")
        await scheduleRun(chat_id_dict)
        await asyncio.sleep(61)

    # Resource Preservation
    # Set the target time to between 9:00 to 10:00 PM
    PM_9 = now.replace(hour=21, minute=0, second=0, microsecond=0)
    if now < PM_9 + timedelta(hours=1) and now >= PM_9:
        logger.info("Entering deep sleep after 9:00 PM")
        await asyncio.sleep(7200)
    # Set the target time to between 8:00 to 9:00 AM
    AM_8 = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if now < AM_8 + timedelta(hours=1) and now >= AM_8:
        logger.info("Entering deep sleep after 8:00 AM")
        await asyncio.sleep(10800)

    
    # Filter data
    filtered_data = formatData(solatTimesRaw)
    if filtered_data is None:
        logger.error("Failed to filter prayer time data in filtered_data")
        return
    solatTimes = filtered_data[0] # Only prayer times
    dateCalendar = filtered_data[1] # Only dates Islamic, Roman
    

    dateToday = datetime.now()
    
    # Find the nearest upcoming prayer time
    for prayer, masa in solatTimes.items():

        try:
            masa_trimmed = masa[:5]
            # Convert the masa time to a datetime object
            masa_time = datetime.strptime(masa_trimmed, '%H:%M')
        except ValueError:
            logger.warning(f"Invalid time format, masa: {masa}")
            continue

        # Combine the date and time
        this_prayer_time = dateToday.replace(
            hour=masa_time.hour,
            minute=masa_time.minute,
            second=0,
            microsecond=0
        )
        this_prayer_time = sg_timezone.localize(this_prayer_time)

        upcoming_prayer_time = this_prayer_time
        upcoming_prayer_name = prayer

        # Reduce CPU Load, fast return
        if (prayer == 'Isyak') and now > this_prayer_time + timedelta(minutes=1) and now <= new_day:
            print ("Returning: ", now)
            return


        if now <= this_prayer_time + timedelta(minutes=1):
            break

    # Define the threshold time as the nearest upcoming prayer time
    print("Confirmed upcoming: ", upcoming_prayer_name)
    print("Now: ", now)

        
    # If time is within 1 minute after azan
    if now < upcoming_prayer_time + timedelta(minutes=1) and now >= upcoming_prayer_time:
        
        await bulk_send_reminders(reminders_enabled_arr, prayer, masa, upcoming_prayer_name)
        # change_prayer_time = upcoming_prayer_time
        
        await asyncio.sleep(61)


    '''
        for loop and if conditionals updated. do a new for loop and shift these one tab left when reimplementing
        # Check if 'custom_duration' key exists in chat_info
        if chat_info['custom_durations']:
            # Trigger the custom reminders based on custom durations
            for i, custom_duration in enumerate(chat_info.get('custom_durations', [])):
                # Calculate the time difference as a timedelta
                time_difference = last_prayer_time - timedelta(minutes=custom_duration)
                if now >= time_difference and now <= time_difference + timedelta(minutes=1) and not chat_info['custom_reminder_sent']:
                    # Trigger the custom reminder for slot i
                    send_custom_reminder(sbot, chat_id, f"{prayer}", masa, custom_duration)
                    chat_info['custom_reminder_sent'] = True
                    t = Timer(65, set_custom_reminder_sent_false, args=(chat_info, ))
                    t.start()
    '''
# Converts solat times into 24-hour format in SGT and handles time based events
import pytz
import datetime
import schedule
from telebot.async_telebot import AsyncTeleBot
from threading import Timer
from datetime import datetime, timedelta, timezone

from scrapeAPI import GetPrayerTime, formatTimes, filterInput

def testprint():
    print("works")

# Bot token
with open('botKey.txt', 'r') as file:
    bot_key = str(file.read())

TELEGRAM_BOT_TOKEN = bot_key

# Create a Bot instance with bot token
sbot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)

# Function to send a reminder
async def send_reminder(chat_id, message):
    await sbot.reply_to(chat_id, message)

# Set the timezone to Singapore (Asia/Singapore)
sg_timezone = pytz.timezone('Asia/Singapore')
offset1Behind = pytz.timezone('Asia/Bangkok')
offset1HalfBehind = pytz.timezone('Asia/Yangon')
offset2Behind = pytz.timezone('Australia/Brisbane')

def scheduleRunFeedback():
    print("Retrieved updated prayer times\n")

# Schedule the scraper to run daily at 4 AM SGT
async def scheduleRun():
    schedule.every().day.at("04:00").do(await GetPrayerTime())
    schedule.every().day.at("04:00").do(scheduleRunFeedback)


# Function to convert 12-hour time to 24-hour time
def convert_to_24_hour_format(time_str):
    try:
        dt = datetime.strptime(time_str, '%I:%M %p')
        return dt.strftime('%H:%M')
    except ValueError:
        return time_str  # Return the input unchanged if it's not in the expected format

async def set_prayer_reminder_sent_false(chat_info):
    chat_info['prayer_reminder_sent'] = False

async def set_custom_reminder_sent_false(chat_info):
    chat_info['custom_reminder_sent'] = False

async def cycleCheck(chat_id_dict):
    #now = datetime.now(sg_timezone)  # Use the Singapore timezone
    now = datetime.now(offset2Behind)
    
    # Get raw prayer time data
    solatTimesRaw = await GetPrayerTime()

    # Filter data
    filtered_data = filterInput(solatTimesRaw)
    solatTimes = filtered_data[0] # Only prayer times
    dateCalendar = filtered_data[1] # Only dates Islamic, Roman

    # Add AM/PM indications based on prayer type
    solatTimesAMPM = formatTimes(solatTimes)

    # Convert prayer times to 24-hour format in SGT, excluding 'PrayerDate'
    solatTimesFormatted = {prayer: convert_to_24_hour_format(time) for prayer, time in solatTimesAMPM.items()}
    # Extract the date value and convert it to a datetime object
    prayer_date_str = dateCalendar.get('PrayerDate', '')  # Use the calendar dictionary here
    prayer_date_format = '%d %B %Y'  # Define the format of the date string
    solatDateFormatted = datetime.strptime(prayer_date_str, prayer_date_format)

    # Find the nearest upcoming prayer time
    for prayer, masa in solatTimesFormatted.items():
        # Convert the masa time to a datetime object
        masa_time = datetime.strptime(masa, '%H:%M')

        # Combine the date and time
        prayer_time = solatDateFormatted.replace(
            hour=masa_time.hour,
            minute=masa_time.minute,
            second=0,
            microsecond=0
        )
        #prayer_time = sg_timezone.localize(prayer_time)
        prayer_time = offset2Behind.localize(prayer_time)

        if (prayer == 'Isyak') and prayer_time < now :
            print ("Returning")
            return

        
        if prayer_time > now : #and (last_prayer_time is None or prayer_time < last_prayer_time):
            threshold_time = prayer_time
            print("exit on iteration: ", prayer, masa)
            print(now, "<", prayer_time)
            print("exit")
            break

    # Define the threshold time as the nearest upcoming prayer time
    print("Confirmed upcoming: ", threshold_time) 

    # Iterate through chat_id_dict to check and update values
    for chat_id, chat_info in chat_id_dict.items():
        # Check and update chat_info values as needed
        # Send reminders when now >= threshold time
        if chat_info['reminders_enabled'] and now <= threshold_time + timedelta(minutes=1) and not chat_info['prayer_reminder_sent'] and now >= threshold_time:
            print("filter")
            reminder_message = f'{prayer} time: {masa}'
            await send_reminder(chat_id, reminder_message)
            chat_info['prayer_reminder_sent'] = True
            t = Timer(65, set_prayer_reminder_sent_false, args=(chat_info))
            t.start()

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
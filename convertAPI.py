# Converts solat times into 24-hour format in SGT and handles time based events
import pytz
import datetime
from telebot.async_telebot import AsyncTeleBot
from datetime import *

from scrapeAPI import *

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

# Function to send a reminder
async def send_reminder(chat_id, prayer, masa):
    try:
        dt = datetime.strptime(masa, '%H:%M')
        masa = dt.strftime('%I:%M %p')
    except ValueError:
        print("ValueError converting masa to 12H") # Return the input unchanged if it's not in the expected format
    finally:
        reminder_message = f'\U0001F54B It is now *{prayer} ({masa})* \U0001F54B\n\n'

        if prayer == "Syuruk":
            reminder_message += "\U0001F305 The sun is up! \U0001F305"
        else:
            reminder_message += "\U0001F932 May your fardh prayer be blessed! \U0001F932"

        # Send message
        await sbot.send_message(chat_id, reminder_message, 'Markdown')


# Set the timezone to Singapore (Asia/Singapore)
sg_timezone = pytz.timezone('Asia/Singapore')
offsetHalfBehind = pytz.FixedOffset(837) # Default 450 for 7h:30mins ahead UTC, behind SG by 30 mins
offset1Behind = pytz.timezone('Asia/Bangkok')
offset1HalfBehind = pytz.timezone('Asia/Yangon')
offset2HalfBehind = pytz.timezone('Asia/Kolkata')

# Schedule the scraper to run daily at 5 AM SGT
async def scheduleRun(chat_id_dict):

    # Iterate through chat_id_dict to check relevant ids for sending
    for chat_id, chat_info in chat_id_dict.items():
        if chat_info['daily_timings_enabled']:

            # fetch formatted times
            times_text = await printTimes()

            # Send message
            await sbot.send_message(chat_id, times_text, 'MarkdownV2')

    print("Scheduled daily has been run\n")


# Function to convert 12-hour time to 24-hour time
def convert_to_24_hour_format(time_str):
    try:
        dt = datetime.strptime(time_str, '%I:%M %p')
        return dt.strftime('%H:%M')
    except ValueError:
        return time_str  # Return the input unchanged if it's not in the expected format

async def cycleCheck(chat_id_dict):

    now = datetime.now(sg_timezone) # Use the Singapore timezone
    new_day = now.replace(hour=23, minute=59, second=0, microsecond=0)

    global upcoming_prayer_time
    global change_prayer_time
    
    # Get raw prayer time data
    solatTimesRaw = await GetPrayerTime()

    # /daily command
    # Set the target time to 5:00 AM
    AM_5 = now.replace(hour=5, minute=0, second=0, microsecond=0)
    if now < AM_5 + timedelta(minutes=1) and now >= AM_5:
        print("Standby Daily Send\n", now)
        await scheduleRun(chat_id_dict)


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
        this_prayer_time = solatDateFormatted.replace(
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
            for chat_id, chat_info in chat_id_dict.items():
                chat_info['prayer_reminder_sent'] = False
                chat_info['custom_reminder_sent'] = False
            print ("Returning: ", now)
            return


        if now <= this_prayer_time + timedelta(minutes=1):
            break

    # Define the threshold time as the nearest upcoming prayer time
    print("Confirmed upcoming: ", upcoming_prayer_name)
    print("Now: ", now)

    # Iterate through chat_id_dict to check and update values
    for chat_id, chat_info in chat_id_dict.items():
        # Check and update chat_info values as needed
        # Send reminders when now >= threshold time
        if chat_info['reminders_enabled'] and now < upcoming_prayer_time + timedelta(minutes=1) and not chat_info['prayer_reminder_sent'] and now >= upcoming_prayer_time:
            await send_reminder(chat_id, prayer, masa)
            print("sent reminder", chat_id)
            chat_info['prayer_reminder_sent'] = True
            change_prayer_time = upcoming_prayer_time

        # Sets any prayer time to false beforehand, after 1.5mins has elapsed after prayer time to avoid recurring reminders
        if upcoming_prayer_time != change_prayer_time: #and threshold_time is not None and chat_id is not None and chat_info['prayer_reminder_sent'] and chat_info['custom_reminder_sent']:
            chat_info['prayer_reminder_sent'] = False
            chat_info['custom_reminder_sent'] = False

        
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
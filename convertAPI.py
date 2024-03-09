# Converts solat times into 24-hour format in SGT and handles time based events
import pytz
import schedule
from datetime import datetime, timedelta, timezone

from scrapeAPI import GetPrayerTime, formatTimes, filterInput


# Set the timezone to Singapore (Asia/Singapore)
sg_timezone = pytz.timezone('Asia/Singapore')

def scheduleRunFeedback():
    print("Retrieved updated prayer times\n")

# Schedule the scraper to run daily at 4 AM SGT
schedule.every().day.at("04:00").do(GetPrayerTime)
schedule.every().day.at("04:00").do(scheduleRunFeedback)


# Function to convert 12-hour time to 24-hour time
def convert_to_24_hour_format(time_str):
    try:
        dt = datetime.strptime(time_str, '%I:%M %p')
        return dt.strftime('%H:%M')
    except ValueError:
        return time_str  # Return the input unchanged if it's not in the expected format

def cycleCheck():
    now = datetime.now(sg_timezone)  # Use the Singapore timezone

    # Get raw prayer time data
    solatTimesRaw = GetPrayerTime()

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

    # Initialize variables for nearest time and threshold
    nearest_time = None
    threshold_hour = None
    threshold_minute = None

    # Find the nearest upcoming prayer time
    for prayer, masa in solatTimesFormatted.items():

        # Convert the masa time to a datetime object
        masa_time = datetime.strptime(masa, '%H:%M')
        
        # Combine the date and time
        prayer_time = solatDateFormatted.replace(
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
            break

    # Check if a nearest prayer time was found
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
                send_reminder(sbot, chat_id, reminder_message)
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
                        send_custom_reminder(sbot, chat_id, f"{prayer}", masa, custom_duration)
                        chat_info['custom_reminder_sent'] = True
                        t = Timer(65, set_custom_reminder_sent_false, args=(chat_info,))
                        t.start()
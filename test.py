from datetime import datetime, timedelta
import pytz

# Define a function to test the nearest prayer time logic
def test_nearest_prayer_time():
    # Sample prayer times
    prayer_times = {
        'Subuh': '05:36 AM',
        'Syuruk': '06:53 AM',
        'Zohor': '12:57 PM',
        'Asar': '04:02 PM',
        'Maghrib': '06:59 PM',
        'Isyak': '08:08 PM'
    }

    # Sample current time (adjust this to your testing needs)
    now = datetime.now(pytz.timezone('Asia/Singapore'))

    # Sample prayer_date (adjust this to your testing needs)
    prayer_date_str = '27 September 2023'
    prayer_date_format = '%d %B %Y'
    prayer_date = datetime.strptime(prayer_date_str, prayer_date_format)

    # Initialize variables for nearest time and threshold
    nearest_time = None
    threshold_hour = None
    threshold_minute = None

    # Find the nearest upcoming prayer time
    for prayer, masa in prayer_times.items():
        if prayer == 'PrayerDate':
            continue  # Skip 'PrayerDate' key

        # Convert the masa time to a datetime object
        masa_time = datetime.strptime(masa, '%I:%M %p')

        # Combine the date and time
        prayer_time = prayer_date.replace(
            hour=masa_time.hour,
            minute=masa_time.minute,
            second=0,
            microsecond=0,
            tzinfo=pytz.timezone('Asia/Singapore')
        )

        if prayer_time > now and (nearest_time is None or prayer_time < nearest_time):
            nearest_time = prayer_time
            threshold_hour = prayer_time.hour
            threshold_minute = prayer_time.minute

    # Check if a nearest prayer time was found
    print("Nearest Time: ", nearest_time)
    if nearest_time is not None:
        # Define the threshold time as the nearest upcoming prayer time
        threshold_time = now.replace(
            hour=threshold_hour,
            minute=threshold_minute,
            second=0,
            microsecond=0,
            tzinfo=pytz.timezone('Asia/Singapore')
        )

        # Check if the current time is equal to or greater than the threshold time
        print("Current Time: ", now)
        print("Threshold Time: ", threshold_time)
        if now >= threshold_time:
            # Trigger any actions you want when the threshold time is reached
            print("Threshold time reached. Execute your actions here.")

# Test the function
test_nearest_prayer_time()

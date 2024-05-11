# Scrapes and returns solat times
import requests
import json
import time
import logging

logger = logging.getLogger(__name__)

# ASYNC Function to scrape prayer times from the website
async def GetPrayerTime():
  url = f'https://www.muis.gov.sg/api/pagecontentapi/GetPrayerTime?v=${str(int(time.time()))}'
  try:
    response = requests.get(url, headers={'Cache-Control': 'no-cache'})
    if response.status_code == 200:
      data = response.json()
      return data
    else:
      logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
      return None
  except requests.exceptions.RequestException as e:
    logger.error(f"Error: {e}")
    return None
  except json.JSONDecodeError as e:
    logger.error(f"Error decoding JSON: {e}")
    return None

# Function to scrape prayer times from the website
def NonAsync_GetPrayerTime():
  url = f'https://www.muis.gov.sg/api/pagecontentapi/GetPrayerTime?v=${str(int(time.time()))}'
  try:
    response = requests.get(url, headers={'Cache-Control': 'no-cache'})
    if response.status_code == 200:
      data = response.json()
      return data
    else:
      logger.error(f"Failed to retrieve data. Status code: {response.status_code}")
      return None
  except requests.exceptions.RequestException as e:
    logger.error(f"Error: {e}")
    return None
  except json.JSONDecodeError as e:
    logger.error(f"Error decoding JSON: {e}")
    return None

# ASYNC Function to save prayer times from the website to a local dict
async def RefreshPrayerTime():
  database_prayer_times = await GetPrayerTime()
  logger.info("Succesfully updated Prayer Times")
  logger.info("Updated Prayer Time: ", database_prayer_times)
  return database_prayer_times

# Function to save prayer times from the website to a local dict
def NonAsync_RefreshPrayerTime():
  database_prayer_times = NonAsync_GetPrayerTime()
  logger.info("Succesfully updated Prayer Times")
  logger.info("Updated Prayer Time: ", database_prayer_times)
  return database_prayer_times
    
# Function to manually add AM/PM based on prayer type
def formatTimes(input_dict):

  for prayer, time in input_dict.items():
    if prayer in ("Subuh", "Syuruk") and "AM" not in time and "PM" not in time:
      input_dict[prayer] = f"{time} AM"
    elif prayer in ("Zohor", "Asar", "Maghrib", "Isyak") and "AM" not in time and "PM" not in time:
      input_dict[prayer] = f"{time} PM"
  return input_dict


def filterInput(input_dict):
  date_dict = {}
  time_dict = input_dict.copy() if input_dict else None

  if time_dict is not None:
    if 'Hijri' in time_dict:
      date_dict['Hijri'] = time_dict.pop('Hijri')
    if 'PrayerDate' in time_dict:
      date_dict['PrayerDate'] = time_dict.pop('PrayerDate')

    return [time_dict, date_dict]
  else:
    logger.warning("Failed to filter data.")
    return None

# Prints the timings
async def printTimes():
  prayer_times = await GetPrayerTime()

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
    message = ""
    message += u"\U0001F54C"
    message += f"   *Daily Prayer Times*   "
    message += u"\U0001F54C"
    message += f"\n\n"
    message += f"*Date:* {prayer_date}\n"
    message += f"*Hijri:* {hijri_date}\n"
    message += f"\n"
    message += f"          *Subuh:* {subuh_time} AM\n\n"
    message += f"          *Syuruk:* {syuruk_time} AM\n\n"
    message += f"          *Zohor:* {zohor_time} PM\n\n"
    message += f"          *Asar:* {asar_time} PM\n\n"
    message += f"          *Maghrib:* {maghrib_time} PM\n\n"
    message += f"          *Isyak:* {isyak_time} PM\n"
    message += f"\u00A0 ㅤ"

    # Escape special characters like '-' using '\'
    message = message.replace('-', r'\-')
    message = message.replace('#', r'\#')
    message = message.replace('.', r'\.')

    logger.info("Successfully formatted prayer times")

    # Send the message with prayer times
    return message
  else:
    logger.error("Failed to retrieve prayer times.")
    return "Failed to retrieve prayer times."



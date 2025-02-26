# Scrapes and returns solat times
import re
import pytz
import requests
import json
#import time
from datetime import *
import logging

logger = logging.getLogger(__name__)
sg_timezone = pytz.timezone('Asia/Singapore')

# ASYNC Function to scrape prayer times from the website
async def GetPrayerTime():
    url = 'https://isomer-user-content.by.gov.sg/muis_prayers_timetable_2025.json'
    headers = {
      'Cache-Control': 'no-cache',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }

    try:
      response = requests.get(url, headers=headers)
      if response.status_code == 200:
        data = response.json()
        # Use today's date as the key (format: YYYY-MM-DD)
        today_key = datetime.now(sg_timezone).strftime("%Y-%m-%d")
        prayer_times = data.get(today_key)
        if prayer_times:
          logger.info("Successfully retrieved prayer times for today")
          return prayer_times
        else:
          logger.error("No prayer times found for today")
          return None
      else:
        logger.error(f"Failed to retrieve data from MUIS. Status code: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        return None
    
'''async def GetPrayerTime():
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
    return None'''

# Function to scrape prayer times from the website
def NonAsync_GetPrayerTime():
  url = 'https://isomer-user-content.by.gov.sg/muis_prayers_timetable_2025.json'
  headers = {
    'Cache-Control': 'no-cache',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
  }

  try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      data = response.json()
      # Use today's date as the key (format: YYYY-MM-DD)
      today_key = datetime.now(sg_timezone).strftime("%Y-%m-%d")
      prayer_times = data.get(today_key)
      if prayer_times:
        logger.info("Successfully retrieved prayer times for today")
        return prayer_times
      else:
        logger.error("No prayer times found for today")
        return None
    else:
      logger.error(f"Failed to retrieve data from MUIS. Status code: {response.status_code}")
      return None
  except requests.exceptions.RequestException as e:
    logger.error(f"Error: {e}")
    return None
  except json.JSONDecodeError as e:
    logger.error(f"Error decoding JSON: {e}")
    return None
    
  '''url = f'https://www.muis.gov.sg/api/pagecontentapi/GetPrayerTime?v=${str(int(time.time()))}'
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
    '''
  

# ASYNC Function to save prayer times from the website to a local dict
async def RefreshPrayerTime():
  database_prayer_times = await GetPrayerTime()
  logger.info("Succesfully updated Prayer Times")
  return database_prayer_times

# Function to save prayer times from the website to a local dict
def NonAsync_RefreshPrayerTime():
  database_prayer_times = NonAsync_GetPrayerTime()
  logger.info("Succesfully updated Prayer Times")
  return database_prayer_times


def formatData(input_dict):
  if not input_dict:
    logger.error("formatData: input_dict is empty")

  date_dict = {}
  time_dict = input_dict.copy() if input_dict else None

  if time_dict is not None:
    if 'hijri_date' in time_dict:
      date_dict['hijri_date'] = time_dict.pop('hijri_date')
    #if 'PrayerDate' in time_dict:
    #  date_dict['PrayerDate'] = time_dict.pop('PrayerDate')

    for prayer, time in time_dict.items():
      # Remove extra whitespace
      format_time = time.strip()
      # Insert a space before am/pm if missing (e.g., "5:43am" -> "5:43 am")
      format_time = re.sub(r'(\d)(am|pm)$', r'\1 \2', format_time, flags=re.IGNORECASE)
      # Pad the hour with a leading zero if needed (e.g., "5:43 am" -> "05:43 am")
      parts = format_time.split(':', 1)
      if parts and len(parts[0]) == 1:
        format_time = "0" + format_time
        # Ensure the am/pm part is uppercase
        format_time = re.sub(r'(am|pm)$', lambda m: m.group(0).upper(), format_time, flags=re.IGNORECASE)
        time_dict[prayer] = format_time

    return [time_dict, date_dict]
  else:
    logger.warning("Failed to filter data.")
    return None
  
async def formatTimesData(input_dict):
  if not input_dict:
    logger.error("formatData: input_dict is empty")

  date_dict = {}
  time_dict = input_dict.copy() if input_dict else None

  if time_dict is not None:
    if 'hijri_date' in time_dict:
      date_dict['hijri_date'] = time_dict.pop('hijri_date')
    #if 'PrayerDate' in time_dict:
    #  date_dict['PrayerDate'] = time_dict.pop('PrayerDate')

    for prayer, time in time_dict.items():
      # Remove extra whitespace
      format_time = time.strip()
      # Insert a space before am/pm if missing (e.g., "5:43am" -> "5:43 am")
      format_time = re.sub(r'(\d)(am|pm)$', r'\1 \2', format_time, flags=re.IGNORECASE)
      # Pad the hour with a leading zero if needed (e.g., "5:43 am" -> "05:43 am")
      parts = format_time.split(':', 1)
      if parts and len(parts[0]) == 1:
        format_time = "0" + format_time
        # Ensure the am/pm part is uppercase
        format_time = re.sub(r'(am|pm)$', lambda m: m.group(0).upper(), format_time, flags=re.IGNORECASE)
        time_dict[prayer] = format_time

    return [time_dict, date_dict]
  else:
    logger.warning("Failed to filter data.")
    return None

# Prints the timings
async def printTimes():
  prayer_times = await GetPrayerTime()
  prayer_times = await formatTimesData(prayer_times)
  if prayer_times is None:
    logger.error("Failed to print prayer time data in printTimes()")
    return
  hijri_date = prayer_times[1]
  prayer_times = prayer_times[0]
  

  if prayer_times is not None:
    # Extract the date and Hijri information
    prayer_date = datetime.now(sg_timezone).strftime("%d %B %Y")
    hijri_date = hijri_date.get('hijri_date', 'N/A')

    # Extract the AM and PM timings from the JSON response
    subuh_time = prayer_times.get('subuh', 'N/A')
    syuruk_time = prayer_times.get('syuruk', 'N/A')
    zohor_time = prayer_times.get('zohor', 'N/A')
    asar_time = prayer_times.get('asar', 'N/A')
    maghrib_time = prayer_times.get('maghrib', 'N/A')
    isyak_time = prayer_times.get('isyak', 'N/A')

    # Create a message with the prayer times and additional information
    message = ""
    message += u"\U0001F54C"
    message += f"   *Daily Prayer Times*   "
    message += u"\U0001F54C"
    message += f"\n\n"
    message += f"*Date:* {prayer_date}\n"
    message += f"*Hijri:* {hijri_date}\n"
    message += f"\n"
    message += f"          *Subuh:* {subuh_time}\n\n"
    message += f"          *Syuruk:* {syuruk_time}\n\n"
    message += f"          *Zohor:* {zohor_time}\n\n"
    message += f"          *Asar:* {asar_time}\n\n"
    message += f"          *Maghrib:* {maghrib_time}\n\n"
    message += f"          *Isyak:* {isyak_time}\n"
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



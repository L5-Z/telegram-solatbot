# Scrapes and returns solat times
import requests
import json
import time
import asyncio

# Function to scrape prayer times from the website
async def GetPrayerTime():
  url = f'https://www.muis.gov.sg/api/pagecontentapi/GetPrayerTime?v=${str(int(time.time()))}'
  try:
      response = requests.get(url, headers={'Cache-Control': 'no-cache'})
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
    
# Function to manually add AM/PM based on prayer type
def formatTimes(input_dict):
  for prayer, time in input_dict.items():
    if prayer in ("Subuh", "Syuruk"):
      input_dict[prayer] = f"{time} AM"
    else:
      input_dict[prayer] = f"{time} PM"
  return input_dict


def filterInput(input_dict):
  date_dict = {}

  if input_dict is not None:
    if 'Hijri' in input_dict:
      date_dict['Hijri'] = input_dict.pop('Hijri')
    if 'PrayerDate' in input_dict:
      date_dict['PrayerDate'] = input_dict.pop('PrayerDate')

    return [input_dict, date_dict]
  else:
    print("Failed to filter data.")
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
    # Send the message with prayer times
    return message
  else:
    message = "Failed to retrieve prayer times."
    return message



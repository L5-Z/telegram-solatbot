# Scrapes and returns solat times
import re
import pytz
import requests
from datetime import datetime, timedelta

from logs import logger
from text import current_prayertimes, upcoming_prayertimes

sg_timezone = pytz.timezone('Asia/Singapore')


def _fetch_timetable():
    """Fetch the full MUIS timetable JSON (all dates for the year, keyed by YYYY-MM-DD)."""
    url = 'https://isomer-user-content.by.gov.sg/muis_prayers_timetable.json'
    # url = f'https://www.muis.gov.sg/api/pagecontentapi/GetPrayerTime?v=${str(int(time.time()))}'
    headers = {
        'Cache-Control': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.exceptions.Timeout:
        logger.error("_fetch_timetable: request timed out after 10s")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"_fetch_timetable: connection error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"_fetch_timetable: request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"_fetch_timetable: unexpected error: {e}")
        return None

    if response.status_code != 200:
        logger.error(f"_fetch_timetable: HTTP {response.status_code}")
        return None

    try:
        return response.json()
    except ValueError as e:  # JSONDecodeError is a ValueError subclass
        logger.error(f"_fetch_timetable: invalid JSON response: {e}")
        return None


def GetPrayerTime():
    data = _fetch_timetable()
    if data:
        today_key = datetime.now(sg_timezone).strftime("%Y-%m-%d")
        prayer_times = data.get(today_key)
        if prayer_times:
            logger.info("Successfully retrieved prayer times for today")
            return prayer_times
        logger.error("No prayer times found for today")
    return None


def get_tomorrow_subuh():
    data = _fetch_timetable()
    if data:
        tomorrow_key = (datetime.now(sg_timezone) + timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow_times = data.get(tomorrow_key)
        if tomorrow_times:
            formatted = formatData(tomorrow_times)
            if formatted:
                return formatted[0].get('subuh')
    logger.error("get_tomorrow_subuh: failed to retrieve tomorrow's Subuh time")
    return None


def RefreshPrayerTime():
    database_prayer_times = GetPrayerTime()
    logger.info("Successfully updated Prayer Times")
    return database_prayer_times


def formatData(input_dict):
    """Split a raw MUIS day entry into [formatted_times, date_dict].

    time_dict keys are normalized to 'HH:MM AM/PM'. date_dict holds
    metadata like hijri_date.
    """
    if not input_dict:
        logger.error("formatData: input_dict is empty")
        return None

    time_dict = input_dict.copy()
    date_dict = {}

    if 'hijri_date' in time_dict:
        date_dict['hijri_date'] = time_dict.pop('hijri_date')

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


async def printTimes():
    prayer_times = GetPrayerTime()
    formatted = formatData(prayer_times)
    if formatted is None:
        logger.error("Failed to format prayer time data in printTimes()")
        return "Failed to retrieve prayer times."

    times = formatted[0]
    dates = formatted[1]

    prayer_date = datetime.now(sg_timezone).strftime("%d %B %Y")
    hijri_date = dates.get('hijri_date', 'N/A')

    message = await current_prayertimes(
        prayer_date=prayer_date,
        hijri_date=hijri_date,
        subuh_time=times.get('subuh', 'N/A'),
        syuruk_time=times.get('syuruk', 'N/A'),
        zohor_time=times.get('zohor', 'N/A'),
        asar_time=times.get('asar', 'N/A'),
        maghrib_time=times.get('maghrib', 'N/A'),
        isyak_time=times.get('isyak', 'N/A'),
    )

    logger.info("Successfully formatted prayer times")
    return message


async def printUpcomingTimes():
    """Prayer times for the next 7 days (strictly future, tomorrow through day 7)."""
    raw = _fetch_timetable()
    if raw is None:
        logger.error("Failed to retrieve prayer times in printUpcomingTimes()")
        return "Failed to retrieve prayer times."

    today = datetime.now(sg_timezone).date()
    days_data = []
    for offset in range(1, 8):
        target = today + timedelta(days=offset)
        key = target.strftime("%Y-%m-%d")
        entry = raw.get(key)
        if entry is None:
            logger.warning(f"No MUIS data for {key}")
            continue
        formatted = formatData(entry)
        if formatted is None:
            continue
        times = formatted[0]
        dates = formatted[1]
        days_data.append({
            'date': target.strftime("%a, %d %b %Y"),
            'hijri': dates.get('hijri_date', 'N/A'),
            'subuh': times.get('subuh', 'N/A'),
            'syuruk': times.get('syuruk', 'N/A'),
            'zohor': times.get('zohor', 'N/A'),
            'asar': times.get('asar', 'N/A'),
            'maghrib': times.get('maghrib', 'N/A'),
            'isyak': times.get('isyak', 'N/A'),
        })

    if not days_data:
        logger.error("No upcoming prayer time data could be assembled")
        return "Failed to retrieve upcoming prayer times."

    message = await upcoming_prayertimes(days_data)
    logger.info(f"Successfully formatted {len(days_data)} upcoming prayer times")
    return message

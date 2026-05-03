from datetime import datetime
from logs import logger

from funcs import format_text

async def pre_reminder_text(prayer, masa, minutes_before):
    prayer = prayer.capitalize()

    header_art = {
        'Subuh': '\U0001F30C',
        'Syuruk': '\U0001F305',
        'Zohor': '\U0001F3D9',
        'Asar': '\U0001F307',
        'Maghrib': '\U0001F304',
        'Isyak': '\U0001F303',
    }.get(prayer, '\U0001F54B')

    return (
        f"⏰ *Reminder:* {prayer} in *{minutes_before} minutes* "
        f"({masa}) {header_art}\n\n"
    )

async def reminder_text(chat_id, prayer, masa, next_prayer=None, next_prayer_time=None):

    prayer = prayer.capitalize()

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

    reminder_message = f"{header_art} It is now *{prayer} ({masa})* {header_art}\n\n"

    if prayer == "Syuruk":
        reminder_message += "☀️ The sun is up! ☀️"
    else:
        reminder_message += "May your fardh prayer be blessed! \U0001F932\n"

    if next_prayer and next_prayer_time:
        reminder_message += f"*Next prayer:* {next_prayer.capitalize()} at *{next_prayer_time}*"

    return reminder_message

async def current_prayertimes(prayer_date=None, hijri_date=None, subuh_time=None, syuruk_time=None, zohor_time=None, asar_time=None, maghrib_time=None, isyak_time=None):
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
    message += f"  ㅤ"

    # Escape special chars
    message = await format_text(message)

    return message

async def upcoming_prayertimes(days=None):
    message = ""
    message += u"\U0001F54C"
    message += "   *Upcoming Prayer Times*   "
    message += u"\U0001F54C"
    message += "\n\n"

    if not days:
        message += "No upcoming prayer times available.\n"
    else:
        for d in days:
            hijri = d.get('hijri') or 'N/A'
            if hijri and hijri != 'N/A':
                message += f"*{d['date']}*  \\(_{hijri}_\\)\n"
            else:
                message += f"*{d['date']}*\n"
            prayer_keys = ['subuh', 'syuruk', 'zohor', 'asar', 'maghrib', 'isyak']
            times = [f"{key[:3].upper()}@{d[key]}" for key in prayer_keys]
            message += f"{' • '.join(times[:2])}\n{' • '.join(times[2:4])}\n{' • '.join(times[4:])}\n\n"

    message = message[:-1]  # Remove one newline
    message += "  ㅤ"

    return message

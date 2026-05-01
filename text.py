from datetime import datetime
import pytz
from logs import logger

from funcs import format_text

sg_timezone = pytz.timezone('Asia/Singapore')

async def reminder_text(chat_id, prayer, masa, next_prayer=None, next_prayer_time=None):

    prayer = prayer.capitalize()

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

        reminder_message = f"{header_art} It is now *{prayer} ({masa})* {header_art}\n\n"

        if next_prayer and next_prayer_time:
            reminder_message += f"*Next prayer:* {next_prayer.capitalize()} at *{next_prayer_time}*\n"

        if prayer == "Syuruk":
            reminder_message += "\u2600\uFE0F The sun is up! \u2600\uFE0F"
        else:
            reminder_message += "May your fardh prayer be blessed! \U0001F932"

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
    message += f"\u00A0 ㅤ"

    # Escape special chars
    message = await format_text(message)

    return message

async def upcoming_prayertimes(prayer_date=None, hijri_date=None, subuh_time=None, syuruk_time=None, zohor_time=None, asar_time=None, maghrib_time=None, isyak_time=None):
    now = datetime.now(sg_timezone)

    prayers = [
        ("Subuh", subuh_time),
        ("Syuruk", syuruk_time),
        ("Zohor", zohor_time),
        ("Asar", asar_time),
        ("Maghrib", maghrib_time),
        ("Isyak", isyak_time),
    ]

    upcoming = []
    for name, time_str in prayers:
        if not time_str or time_str == "N/A":
            continue
        try:
            t = datetime.strptime(time_str, "%I:%M %p")
            prayer_dt = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
            if prayer_dt > now:
                upcoming.append((name, time_str))
        except ValueError as e:
            logger.error(f"upcoming_prayertimes parse error for {name} ({time_str}): {e}")

    message = ""
    message += u"⏰"
    message += f"   *Upcoming Prayer Times*   "
    message += u"⏰"
    message += f"\n\n"
    message += f"*Date:* {prayer_date}\n"
    message += f"*Hijri:* {hijri_date}\n"
    message += f"\n"

    if upcoming:
        for i, (name, time_str) in enumerate(upcoming):
            marker = u"  \U0001F53C" if i == 0 else ""
            message += f"          *{name}:* {time_str}{marker}\n\n"
    else:
        message += f"          _All prayers for today have passed._\n\n"

    message += f"\u00A0 ㅤ"

    # Escape special chars
    message = await format_text(message)

    return message

import pytz
import datetime
import logging
import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import *
from datetime import *

logger = logging.getLogger(__name__)

# Bot token
with open('botKey.txt', 'r') as file:
    bot_key = str(file.read())

TELEGRAM_BOT_TOKEN = bot_key

# Create a Bot instance with bot token
sbot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)

# Set the timezone to Singapore (Asia/Singapore)
sg_timezone = pytz.timezone('Asia/Singapore')

# Check for blocked users
async def check_for_blocked_users(chat_id_dict, logger):
    blocked_users = []
    for chat_id in chat_id_dict:
        try:
            # Send a dummy message to check if the bot is blocked
            await sbot.send_chat_action(chat_id=chat_id, action='typing')
        except telebot.apihelper.ApiException as e:
            if e.result.status_code == 403 and "bot was blocked by the user" in e.result.text:
                logger.warning(f"Bot was blocked by user {chat_id}")
                print(f"Bot was blocked by user {chat_id}")
                blocked_users.append(chat_id)
    return blocked_users

# Blocked user process
async def blocked_users_handling(chat_id_dict, logger):
    logger.info("Block Check...")
    print("Block Check...")
    # Remove blocked users from chat_id_dict or take other appropriate action
    blocked_users = await check_for_blocked_users(chat_id_dict)
    if blocked_users:
        # Notify of blocked users
        logger.info(f"Bot was blocked by the following users: {', '.join(map(str, blocked_users))}")
            
        # Remove blocked users from database
        for blocked_user in blocked_users:
            chat_id_dict.pop(blocked_user, None)
            print("Removed blocker: ", blocked_user)
            logger.info(f"Removed {len(blocked_users)} blocked users from the chat_id_dict database.")

    else:
        logger.info("No users have blocked the bot. Proceeding...")
        print("No blocks")

'''
# Schedule block check
async def schedule_block_check(chat_id_dict, logger):
    now = datetime.now(sg_timezone) # Use the Singapore timezone
    new_day = now.replace(hour=23, minute=59, second=0, microsecond=0)
    
    # Get raw prayer time data
    solatTimesRaw = await GetPrayerTime()
    if solatTimesRaw is None:
        logger.error("Failed to retrieve prayer times from MUIS")
        return

    # /daily command
    # Set the target time to 5:00 AM
    AM_5 = now.replace(hour=5, minute=0, second=0, microsecond=0)
    if now < AM_5 + timedelta(minutes=1) and now >= AM_5:
        logger.info("Sending daily prayer times at 5:00 AM")
        await blocked_users_handling(chat_id_dict, logger)
'''
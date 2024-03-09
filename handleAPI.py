# Provides Handlers for any command run
from datetime import datetime, timedelta, timezone
import telebot
from telebot import TeleBot
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from main import sbot
from scrapeAPI import printTimes

@sbot.message_handler(commands=['start', 'help'])
def send_welcome(message):
  sbot.reply_to(message, "Howdy, how are you doing?")

# Function to send a reminder
async def send_reminder(message):
    await sbot.reply_to(message.chat.id, message)

@sbot.message_handler(commands=['start'])
async def sendWelcome(message):
    await sbot.reply_to(message.chat.id, "test")

# /start command handler
@sbot.message_handler(commands=['start'])
async def start_command(message):
    # Welcome message
    welcome_message = "Thanks for using my bot!\n\nDo /help for a list of commands\nReminders are OFF by default, do /toggle to turn them on\n\nCurrent Version: v0.0.4\nUpdated and Patched as of 29/9/23\nDo /patch to view patchnotes\n\n"
    welcome_message += "Bot made by L5Z (Faatih) :)"
    await sbot.reply_to(message.chat.id, welcome_message)

# /test command handler
@sbot.message_handler(commands=['test'])
async def test_command(message):
    # Execute your test logic here
    await sbot.reply_to(message.chat.id, "Test command has been run. Bot is up and running.\n Use '/help' for command list")

# /timings command handler
@sbot.message_handler(commands=['timings'])
async def timings_command(message):
    reply = printTimes()
    # Send the message with prayer times
    await sbot.reply_to(message.chat.id, reply)

# Rest of your command handlers...

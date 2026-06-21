from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

import requests
import sqlite3
import time
import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# =========================
# تحميل المفاتيح من ملف .env (محلياً) أو من Environment Variables (على Render)
# =========================
load_dotenv()

TOKEN = os.environ.get("BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# =========================
# سيرفر Flask صغير (مطلوب عشان Render يعتبر الخدمة شغالة)
# =========================
web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is alive"

def run_web():
    web_app.run(host='0.0.0.0', port=8080)

Thread(target=run_web).start()

# =========================
# إعدادات
# =========================
DAILY_LIMIT = 20
last_request_time = {}

# =========================
# قاعدة بيانات
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    date TEXT,
    count INTEGER
)
""")
conn.commit()

# =========================
# System Prompt (اللغة + الأسلوب)
# =========================
SYSTEM_PROMPT = {
    "role": "system",
    "content": """
أنت مساعد ذكي متعدد اللغات.

قواعد اللغة:
- يجب الرد بنفس لغة المستخدم 100%
- إذا المستخدم كتب عربي → رد عربي فقط
- إذا المستخدم كتب إنجليزي → رد إنجليزي فقط
- إذا المستخدم كتب أي لغة أخرى → رد بنفس اللغة
- ممنوع تغيير اللغة أو المزج بين اللغات

طريقة الإجابة:
- جاوب بشكل واضح ودقيق
- إذا السؤال بسيط اختصر
- إذا السؤال معقد اشرح خطوة خطوة
- لا تخترع معلومات إذا غير متأكد
"""
}

# =========================
# AI FUNCTION (GROQ)
# =========================
def ask_ai(messages):
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 1500
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=20)
        res = r.json()

        if "choices" not in res:
            return f"API ERROR: {res}"

        return res["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Error: {str(e)}"

# =========================
# نظام الحد اليومي
# =========================
def check_limit(user_id):
    today = str(datetime.now().date())

    cursor.execute("SELECT date, count FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (user_id, today, 0))
        conn.commit()
        return True

    date, count = row

    if date != today:
        cursor.execute("UPDATE users SET date=?, count=? WHERE user_id=?", (today, 0, user_id))
        conn.commit()
        return True

    return count < DAILY_LIMIT


def add_usage(user_id):
    cursor.execute("SELECT count FROM users WHERE user_id=?", (user_id,))
    count = cursor.fetchone()[0]

    cursor.execute("UPDATE users SET count=? WHERE user_id=?", (count + 1, user_id))
    conn.commit()

# =========================
# /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 البوت الذكي كَيَان شغال الآن 🤖")

# =========================
# الردود
# =========================
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    text = update.message.text

    # ⏳ منع سبام
    now = time.time()
    if user_id in last_request_time:
        if now - last_request_time[user_id] < 2:
            await update.message.reply_text("⏳ استنى شوي")
            return

    last_request_time[user_id] = now

    # 🚫 حد يومي
    if not check_limit(user_id):
        await update.message.reply_text("❌ خلصت حدك اليومي، حاول بكرا 👍")
        return

    # 🧠 الرسائل
    messages = [
        SYSTEM_PROMPT,
        {"role": "user", "content": text}
    ]

    bot_reply = ask_ai(messages)

    add_usage(user_id)

    await update.message.reply_text(bot_reply)

# =========================
# تشغيل البوت
# =========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

print("🤖 Bot running...")
app.run_polling()

# 🤖 Kayan AI Telegram Bot

A smart Telegram bot built with Python, powered by the Llama 3.3 70B model via the Groq API, capable of responding to users in whatever language they write in.

## ✨ Features

- Intelligent responses powered by Llama 3.3 70B (via Groq API)
- Automatic language detection (replies in the same language the user writes in)
- Daily usage limit per user (rate limiting)
- Spam protection (delay between consecutive messages)
- Usage data stored in a SQLite database

## 🛠️ Tech Stack

- Python
- python-telegram-bot
- Groq API (Llama 3.3 70B)
- SQLite
- Flask (keeps the bot running 24/7 on Render)

## ⚙️ Setup and Local Installation

1. Clone the repository:
```bash
git clone https://github.com/username/repo-name.git
cd repo-name
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file and add:
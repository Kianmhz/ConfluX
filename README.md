# ConfluX

**ConfluX** is a real-time Telegram bot that monitors on-chain wallet activity and detects **confluence signals**—patterns where multiple independent transactions align within a short time window.

The goal is to reduce noise in raw transaction feeds and surface **meaningful coordinated activity** in near real time.

---

## 🔍 What ConfluX Does
- Monitors blockchain wallet transactions in real time
- Detects **confluence events** based on multiple unique participants
- Filters duplicate or noisy signals to reduce false positives
- Sends alerts through Telegram with minimal latency
- Supports continuous monitoring across active wallets

---

## 🧠 Core Logic
- **Event-driven pipeline** for incoming transactions
- **Confluence detection** based on temporal clustering and unique buyers
- **Stateful filtering** to avoid repeated alerts for the same activity
- **Asynchronous processing** for low-latency updates

---

## 🛠️ Tech Stack
- **Language:** Python  
- **Messaging:** Telegram (Telethon)  
- **Architecture:** Event-driven, asynchronous  
- **Data Handling:** Real-time stream processing  

---

## 🚀 Getting started

Follow these steps to set up a local development environment and run ConfluX.

1. Create and activate a virtual environment (macOS / Linux):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Upgrade pip and install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the required environment variables (example):

```env
API_ID=your_api_id
API_HASH=your_api_hash
DEFINED_BOT_USERNAME=the_defined_bot_username
TELEGRAM_TOKEN=your_telegram_bot_token
```

4. Run the bot:

```bash
python main.py
```

Notes:
- Ensure your Telegram API credentials are valid and that the bot account has the necessary permissions.
- For production deployments, prefer running the bot under a process manager (systemd, pm2, supervisord) and secure your environment variables.


## ⚠️ Disclaimer
ConfluX is a **signal detection and monitoring tool**, not a trading bot or financial advisor. It does not execute trades or provide investment recommendations.

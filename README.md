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

## ⚠️ Disclaimer
ConfluX is a **signal detection and monitoring tool**, not a trading bot or financial advisor. It does not execute trades or provide investment recommendations.

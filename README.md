# 📈 Stock Tracker Telegram Bot

> Real-time stock price tracking, portfolio management, and price alerts — all in Telegram.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram)
![Railway](https://img.shields.io/badge/Deployed-Railway-black?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## ✨ Features

| Command | Description |
|--------|-------------|
| `/start` | Welcome message and list of commands |
| `/price AAPL` | Get real-time price of any stock |
| `/top` | Top 7 most popular stocks right now |
| `/portfolio add TSLA` | Add a stock to your personal portfolio |
| `/portfolio remove TSLA` | Remove a stock from your portfolio |
| `/portfolio` | View your portfolio with live prices |
| `/alert AAPL 200` | Get notified when a stock hits your target price |

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **python-telegram-bot** — Telegram API wrapper
- **Yahoo Finance API** — Real-time stock data (no API key needed)
- **Railway** — 24/7 cloud hosting

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/stock-bot.git
cd stock-bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your bot token
Get your token from [@BotFather](https://t.me/BotFather) on Telegram, then set it as an environment variable:

```bash
export BOT_TOKEN=your_token_here
```

### 4. Run the bot
```bash
python stock_parser.py
```

---

## ☁️ Deploy to Railway (24/7)

1. Fork this repository
2. Go to [railway.app](https://railway.app) and create a new project
3. Connect your GitHub repository
4. Add environment variable: `BOT_TOKEN = your_token`
5. Done! Your bot runs 24/7 🎉

---

## 📁 Project Structure

```
stock-bot/
├── stock_parser.py     # Main bot file
├── requirements.txt    # Python dependencies
├── railway.toml        # Railway deployment config
├── portfolios.json     # User portfolios (auto-created)
├── alerts.json         # User alerts (auto-created)
└── README.md           # You are here
```

---

## 🤝 Custom Bot Development

Need a custom Telegram bot for your business?

📩 Feel free to reach out — I build custom bots starting at **$50**

---

## 📜 License

MIT License — free to use and modify.

---

<p align="center">Built with ❤️ by <a href="https://github.com/YOUR_USERNAME">YOUR_USERNAME</a></p>

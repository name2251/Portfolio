# ============================================================
# 📈 TELEGRAM БОТ ДЛЯ ОТСЛЕЖИВАНИЯ АКЦИЙ
# ============================================================
# Что нужно установить перед запуском:
#   pip install python-telegram-bot requests
#
# Как получить токен бота:
#   1. Открой Telegram и найди @BotFather
#   2. Напиши /newbot
#   3. Придумай имя и username для бота
#   4. BotFather даст тебе токен — вставь его ниже
# ============================================================

import requests
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ============================================================
# ⚙️ НАСТРОЙКИ — ИЗМЕНИ ЭТО!
# ============================================================

# Вставь сюда токен от @BotFather
BOT_TOKEN = "8650899818:AAH3nm3ne6o4A77aG-vwMHlrx4Uq4ITOgp8"

# Файл где будут храниться портфолио пользователей
PORTFOLIO_FILE = "portfolios.json"

# Файл где будут храниться алерты пользователей
ALERTS_FILE = "alerts.json"

# ============================================================
# 💾 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ СОХРАНЕНИЯ ДАННЫХ
# ============================================================

def load_json(filename: str) -> dict:
    """
    Загружает данные из JSON файла.
    Если файл не существует — возвращает пустой словарь.
    """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(filename: str, data: dict):
    """
    Сохраняет данные в JSON файл.
    indent=2 делает файл читаемым (с отступами).
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# 📊 ФУНКЦИЯ ПОЛУЧЕНИЯ ЦЕНЫ АКЦИИ
# ============================================================

def get_stock_price(ticker: str) -> dict:
    """
    Получает цену акции с Yahoo Finance.
    ticker — это символ акции, например "AAPL" или "TSLA"
    
    Возвращает словарь с данными или пустой словарь если ошибка.
    """
    # URL для запроса к Yahoo Finance API
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    
    # Заголовки чтобы сайт не блокировал нас
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    # Параметры запроса — берём данные за 1 день
    params = {"interval": "1d", "range": "1d"}

    try:
        # Делаем запрос к API
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # Вызовет ошибку если статус не 200
        
        # Парсим JSON ответ
        data = response.json()
        result = data["chart"]["result"][0]
        meta = result["meta"]
        
        # Достаём нужные данные
        price = meta.get("regularMarketPrice", 0)
        prev_close = meta.get("chartPreviousClose", price)
        
        # Считаем изменение в процентах
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0

        return {
            "ticker": ticker.upper(),
            "price": round(price, 2),
            "currency": meta.get("currency", "USD"),
            "change_percent": round(change_pct, 2),
            "prev_close": round(prev_close, 2),
            "volume": meta.get("regularMarketVolume", 0),
        }
    except Exception as e:
        # Если что-то пошло не так — возвращаем пустой словарь
        print(f"Ошибка при получении {ticker}: {e}")
        return {}


# ============================================================
# 🤖 КОМАНДЫ БОТА
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /start — приветствие когда пользователь впервые открывает бота.
    Каждая команда бота принимает update (сообщение) и context (контекст).
    """
    # update.effective_user.first_name — имя пользователя в Telegram
    name = update.effective_user.first_name
    
    text = (
        f"👋 Привет, {name}!\n\n"
        f"Я бот для отслеживания акций 📈\n\n"
        f"Вот что я умею:\n"
        f"/price AAPL — цена любой акции\n"
        f"/top — топ акций прямо сейчас\n"
        f"/portfolio — твой список акций\n"
        f"/alert AAPL 200 — уведомить когда AAPL достигнет $200\n\n"
        f"Попробуй написать /price AAPL 🚀"
    )
    
    # Отправляем ответ пользователю
    await update.message.reply_text(text)


# ─────────────────────────────────────────────────────────────
# Команда /price
# ─────────────────────────────────────────────────────────────

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /price TICKER — показывает текущую цену акции.
    Пример: /price AAPL
    
    context.args — это список аргументов после команды.
    Если написать /price AAPL, то context.args = ["AAPL"]
    """
    
    # Проверяем что пользователь написал тикер
    if not context.args:
        await update.message.reply_text(
            "❌ Укажи тикер акции!\nПример: /price AAPL"
        )
        return
    
    # Берём первый аргумент и делаем заглавными буквами
    ticker = context.args[0].upper()
    
    # Сообщаем что загружаем данные
    await update.message.reply_text(f"⏳ Загружаю данные для {ticker}...")
    
    # Получаем данные
    data = get_stock_price(ticker)
    
    # Если данных нет — скорее всего неверный тикер
    if not data:
        await update.message.reply_text(
            f"❌ Не удалось найти акцию {ticker}\n"
            f"Проверь правильность тикера. Например: AAPL, TSLA, GOOGL"
        )
        return
    
    # Выбираем эмодзи в зависимости от изменения цены
    arrow = "📈" if data["change_percent"] >= 0 else "📉"
    sign = "+" if data["change_percent"] >= 0 else ""
    
    text = (
        f"{arrow} *{data['ticker']}*\n\n"
        f"💵 Цена: *{data['price']} {data['currency']}*\n"
        f"📊 Изменение: {sign}{data['change_percent']}%\n"
        f"⬅️ Закрытие вчера: {data['prev_close']} {data['currency']}\n"
        f"📦 Объём: {data['volume']:,}\n\n"
        f"🕐 {datetime.now().strftime('%H:%M:%S')}"
    )
    
    # parse_mode="Markdown" позволяет использовать *жирный* текст
    await update.message.reply_text(text, parse_mode="Markdown")


# ─────────────────────────────────────────────────────────────
# Команда /top
# ─────────────────────────────────────────────────────────────

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /top — показывает топ популярных акций.
    Просто загружает фиксированный список популярных тикеров.
    """
    
    # Список популярных акций
    TOP_TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "META"]
    
    await update.message.reply_text("⏳ Загружаю топ акций...")
    
    lines = ["📊 *Топ акций прямо сейчас:*\n"]
    
    # Проходим по каждому тикеру и получаем данные
    for ticker in TOP_TICKERS:
        data = get_stock_price(ticker)
        
        if data:
            arrow = "🟢" if data["change_percent"] >= 0 else "🔴"
            sign = "+" if data["change_percent"] >= 0 else ""
            lines.append(
                f"{arrow} *{data['ticker']}*: "
                f"{data['price']}$ "
                f"({sign}{data['change_percent']}%)"
            )
    
    lines.append(f"\n🕐 {datetime.now().strftime('%H:%M:%S')}")
    
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─────────────────────────────────────────────────────────────
# Команда /my portfolio
# ─────────────────────────────────────────────────────────────

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /portfolio — управление личным списком акций.
    
    /portfolio — показать свои акции
    /portfolio add AAPL — добавить акцию
    /portfolio remove AAPL — удалить акцию
    """
    
    # ID пользователя — уникальный для каждого человека в Telegram
    user_id = str(update.effective_user.id)
    
    # Загружаем все портфолио из файла
    portfolios = load_json(PORTFOLIO_FILE)
    
    # Если у пользователя нет портфолио — создаём пустой список
    if user_id not in portfolios:
        portfolios[user_id] = []
    
    # Получаем список акций этого пользователя
    user_portfolio = portfolios[user_id]
    
    # Если нет аргументов — показываем портфолио
    if not context.args:
        if not user_portfolio:
            await update.message.reply_text(
                "📂 Твой портфель пуст!\n\n"
                "Добавь акции командой:\n"
                "/portfolio add AAPL"
            )
            return
        
        await update.message.reply_text("⏳ Загружаю твой портфель...")
        
        lines = ["💼 *Твой портфель:*\n"]
        
        for ticker in user_portfolio:
            data = get_stock_price(ticker)
            if data:
                arrow = "🟢" if data["change_percent"] >= 0 else "🔴"
                sign = "+" if data["change_percent"] >= 0 else ""
                lines.append(
                    f"{arrow} *{ticker}*: "
                    f"{data['price']}$ "
                    f"({sign}{data['change_percent']}%)"
                )
        
        lines.append("\nДля управления:")
        lines.append("/portfolio add TSLA — добавить")
        lines.append("/portfolio remove TSLA — удалить")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return
    
    # Если есть аргументы — обрабатываем команды add/remove
    action = context.args[0].lower()  # "add" или "remove"
    
    # Проверяем что указан тикер
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Укажи тикер!\n"
            "Пример: /portfolio add AAPL"
        )
        return
    
    ticker = context.args[1].upper()
    
    if action == "add":
        # Добавляем акцию если её ещё нет в портфеле
        if ticker in user_portfolio:
            await update.message.reply_text(f"⚠️ {ticker} уже есть в портфеле!")
        else:
            user_portfolio.append(ticker)
            portfolios[user_id] = user_portfolio
            save_json(PORTFOLIO_FILE, portfolios)  # Сохраняем изменения
            await update.message.reply_text(f"✅ {ticker} добавлен в портфель!")
    
    elif action == "remove":
        # Удаляем акцию если она есть в портфеле
        if ticker not in user_portfolio:
            await update.message.reply_text(f"⚠️ {ticker} нет в портфеле!")
        else:
            user_portfolio.remove(ticker)
            portfolios[user_id] = user_portfolio
            save_json(PORTFOLIO_FILE, portfolios)  # Сохраняем изменения
            await update.message.reply_text(f"✅ {ticker} удалён из портфеля!")
    
    else:
        await update.message.reply_text(
            "❌ Неверная команда!\n"
            "Используй: add или remove\n"
            "Пример: /portfolio add AAPL"
        )


# ─────────────────────────────────────────────────────────────
# Команда /alert
# ─────────────────────────────────────────────────────────────

async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /alert TICKER ЦЕНА — установить уведомление.
    Пример: /alert AAPL 200
    
    Бот сохранит алерт и при каждом запуске check_alerts()
    будет проверять достигнута ли цена.
    """
    
    user_id = str(update.effective_user.id)
    
    # Проверяем что указаны тикер и цена
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Укажи тикер и цену!\n"
            "Пример: /alert AAPL 200\n"
            "(уведомит когда AAPL достигнет $200)"
        )
        return
    
    ticker = context.args[0].upper()
    
    # Пробуем преобразовать цену в число
    try:
        target_price = float(context.args[1])
    except ValueError:
        await update.message.reply_text(
            "❌ Цена должна быть числом!\n"
            "Пример: /alert AAPL 200.50"
        )
        return
    
    # Загружаем все алерты
    alerts = load_json(ALERTS_FILE)
    
    if user_id not in alerts:
        alerts[user_id] = []
    
    # Получаем текущую цену чтобы понять — ждём роста или падения
    data = get_stock_price(ticker)
    if not data:
        await update.message.reply_text(f"❌ Не удалось найти акцию {ticker}")
        return
    
    current_price = data["price"]
    direction = "выше" if target_price > current_price else "ниже"
    
    # Сохраняем алерт
    alerts[user_id].append({
        "ticker": ticker,
        "target_price": target_price,
        "direction": direction,  # "выше" или "ниже"
        "chat_id": update.effective_chat.id,  # Нужно для отправки уведомления
    })
    
    save_json(ALERTS_FILE, alerts)
    
    await update.message.reply_text(
        f"🔔 Алерт установлен!\n\n"
        f"Акция: *{ticker}*\n"
        f"Текущая цена: {current_price}$\n"
        f"Уведомлю когда цена станет {direction} {target_price}$",
        parse_mode="Markdown"
    )


# ─────────────────────────────────────────────────────────────
# Проверка алертов (запускается автоматически каждые 5 минут)
# ─────────────────────────────────────────────────────────────

async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    """
    Эта функция запускается автоматически каждые 5 минут.
    Проверяет все алерты и отправляет уведомления если цена достигнута.
    """
    
    alerts = load_json(ALERTS_FILE)
    
    if not alerts:
        return  # Нет алертов — ничего не делаем
    
    # Собираем уникальные тикеры чтобы не делать лишних запросов
    all_tickers = set()
    for user_alerts in alerts.values():
        for alert_item in user_alerts:
            all_tickers.add(alert_item["ticker"])
    
    # Получаем текущие цены для всех тикеров
    prices = {}
    for ticker in all_tickers:
        data = get_stock_price(ticker)
        if data:
            prices[ticker] = data["price"]
    
    # Проверяем каждый алерт
    alerts_to_keep = {}  # Алерты которые ещё не сработали
    
    for user_id, user_alerts in alerts.items():
        remaining = []
        
        for alert_item in user_alerts:
            ticker = alert_item["ticker"]
            target = alert_item["target_price"]
            direction = alert_item["direction"]
            current = prices.get(ticker)
            
            if current is None:
                remaining.append(alert_item)  # Оставляем если не получили цену
                continue
            
            # Проверяем достигнута ли целевая цена
            triggered = (
                (direction == "выше" and current >= target) or
                (direction == "ниже" and current <= target)
            )
            
            if triggered:
                # Отправляем уведомление пользователю
                try:
                    await context.bot.send_message(
                        chat_id=alert_item["chat_id"],
                        text=(
                            f"🔔 *АЛЕРТ СРАБОТАЛ!*\n\n"
                            f"Акция *{ticker}* достигла цели!\n"
                            f"Текущая цена: *{current}$*\n"
                            f"Целевая цена: {target}$"
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Ошибка отправки алерта: {e}")
            else:
                remaining.append(alert_item)  # Алерт ещё не сработал
        
        if remaining:
            alerts_to_keep[user_id] = remaining
    
    # Сохраняем только несработавшие алерты
    save_json(ALERTS_FILE, alerts_to_keep)


# ============================================================
# 🚀 ЗАПУСК БОТА
# ============================================================

def main():
    """
    Главная функция — запускает бота.
    """
    
    print("🤖 Запускаю бота...")
    
    # Создаём приложение с нашим токеном
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    # Каждая строка говорит: "если пользователь написал /команда — вызови функцию"
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("alert", alert))
    
    # Запускаем проверку алертов каждые 5 минут (300 секунд)
    app.job_queue.run_repeating(check_alerts, interval=300, first=10)
    
    print("✅ Бот запущен! Нажми Ctrl+C чтобы остановить.")
    
    # Запускаем бота (он будет работать пока не нажмёшь Ctrl+C)
    app.run_polling()


# Это стандартная проверка — код внутри запустится только
# если ты запускаешь этот файл напрямую (не импортируешь его)
if __name__ == "__main__":
    main()
    # ============================================================
# 📈 TELEGRAM БОТ ДЛЯ ОТСЛЕЖИВАНИЯ АКЦИЙ
# ============================================================
# Что нужно установить перед запуском:
#   pip install python-telegram-bot requests
#
# Как получить токен бота:
#   1. Открой Telegram и найди @BotFather
#   2. Напиши /newbot
#   3. Придумай имя и username для бота
#   4. BotFather даст тебе токен — вставь его ниже
# ============================================================

import requests
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ============================================================
# ⚙️ НАСТРОЙКИ — ИЗМЕНИ ЭТО!
# ============================================================

# Вставь сюда токен от @BotFather
BOT_TOKEN = "ВСТАВЬ_СВОЙ_ТОКЕН_СЮДА"

# Файл где будут храниться портфолио пользователей
PORTFOLIO_FILE = "portfolios.json"

# Файл где будут храниться алерты пользователей
ALERTS_FILE = "alerts.json"

# ============================================================
# 💾 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ СОХРАНЕНИЯ ДАННЫХ
# ============================================================

def load_json(filename: str) -> dict:
    """
    Загружает данные из JSON файла.
    Если файл не существует — возвращает пустой словарь.
    """
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(filename: str, data: dict):
    """
    Сохраняет данные в JSON файл.
    indent=2 делает файл читаемым (с отступами).
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# 📊 ФУНКЦИЯ ПОЛУЧЕНИЯ ЦЕНЫ АКЦИИ
# ============================================================

def get_stock_price(ticker: str) -> dict:
    """
    Получает цену акции с Yahoo Finance.
    ticker — это символ акции, например "AAPL" или "TSLA"
    
    Возвращает словарь с данными или пустой словарь если ошибка.
    """
    # URL для запроса к Yahoo Finance API
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    
    # Заголовки чтобы сайт не блокировал нас
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    # Параметры запроса — берём данные за 1 день
    params = {"interval": "1d", "range": "1d"}

    try:
        # Делаем запрос к API
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()  # Вызовет ошибку если статус не 200
        
        # Парсим JSON ответ
        data = response.json()
        result = data["chart"]["result"][0]
        meta = result["meta"]
        
        # Достаём нужные данные
        price = meta.get("regularMarketPrice", 0)
        prev_close = meta.get("chartPreviousClose", price)
        
        # Считаем изменение в процентах
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0

        return {
            "ticker": ticker.upper(),
            "price": round(price, 2),
            "currency": meta.get("currency", "USD"),
            "change_percent": round(change_pct, 2),
            "prev_close": round(prev_close, 2),
            "volume": meta.get("regularMarketVolume", 0),
        }
    except Exception as e:
        # Если что-то пошло не так — возвращаем пустой словарь
        print(f"Ошибка при получении {ticker}: {e}")
        return {}


# ============================================================
# 🤖 КОМАНДЫ БОТА
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /start — приветствие когда пользователь впервые открывает бота.
    Каждая команда бота принимает update (сообщение) и context (контекст).
    """
    # update.effective_user.first_name — имя пользователя в Telegram
    name = update.effective_user.first_name
    
    text = (
        f"👋 Привет, {name}!\n\n"
        f"Я бот для отслеживания акций и крипты 📈\n\n"
        f"Вот что я умею:\n"
        f"/price AAPL — цена любой акции\n"
        f"/crypto BTC — цена криптовалюты\n"
        f"/crypto — топ криптовалют\n"
        f"/top — топ акций прямо сейчас\n"
        f"/portfolio — твой список акций\n"
        f"/alert AAPL 200 — уведомить когда AAPL достигнет $200\n\n"
        f"Попробуй написать /crypto BTC 🚀"
    )
    
    # Отправляем ответ пользователю
    await update.message.reply_text(text)


# ─────────────────────────────────────────────────────────────
# Команда /price
# ─────────────────────────────────────────────────────────────

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /price TICKER — показывает текущую цену акции.
    Пример: /price AAPL
    
    context.args — это список аргументов после команды.
    Если написать /price AAPL, то context.args = ["AAPL"]
    """
    
    # Проверяем что пользователь написал тикер
    if not context.args:
        await update.message.reply_text(
            "❌ Укажи тикер акции!\nПример: /price AAPL"
        )
        return
    
    # Берём первый аргумент и делаем заглавными буквами
    ticker = context.args[0].upper()
    
    # Сообщаем что загружаем данные
    await update.message.reply_text(f"⏳ Загружаю данные для {ticker}...")
    
    # Получаем данные
    data = get_stock_price(ticker)
    
    # Если данных нет — скорее всего неверный тикер
    if not data:
        await update.message.reply_text(
            f"❌ Не удалось найти акцию {ticker}\n"
            f"Проверь правильность тикера. Например: AAPL, TSLA, GOOGL"
        )
        return
    
    # Выбираем эмодзи в зависимости от изменения цены
    arrow = "📈" if data["change_percent"] >= 0 else "📉"
    sign = "+" if data["change_percent"] >= 0 else ""
    
    text = (
        f"{arrow} *{data['ticker']}*\n\n"
        f"💵 Цена: *{data['price']} {data['currency']}*\n"
        f"📊 Изменение: {sign}{data['change_percent']}%\n"
        f"⬅️ Закрытие вчера: {data['prev_close']} {data['currency']}\n"
        f"📦 Объём: {data['volume']:,}\n\n"
        f"🕐 {datetime.now().strftime('%H:%M:%S')}"
    )
    
    # parse_mode="Markdown" позволяет использовать *жирный* текст
    await update.message.reply_text(text, parse_mode="Markdown")


# ─────────────────────────────────────────────────────────────
# Команда /top
# ─────────────────────────────────────────────────────────────

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /top — показывает топ популярных акций.
    Просто загружает фиксированный список популярных тикеров.
    """
    
    # Список популярных акций
    TOP_TICKERS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "META"]
    
    await update.message.reply_text("⏳ Загружаю топ акций...")
    
    lines = ["📊 *Топ акций прямо сейчас:*\n"]
    
    # Проходим по каждому тикеру и получаем данные
    for ticker in TOP_TICKERS:
        data = get_stock_price(ticker)
        
        if data:
            arrow = "🟢" if data["change_percent"] >= 0 else "🔴"
            sign = "+" if data["change_percent"] >= 0 else ""
            lines.append(
                f"{arrow} *{data['ticker']}*: "
                f"{data['price']}$ "
                f"({sign}{data['change_percent']}%)"
            )
    
    lines.append(f"\n🕐 {datetime.now().strftime('%H:%M:%S')}")
    
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ─────────────────────────────────────────────────────────────
# Команда /portfolio
# ─────────────────────────────────────────────────────────────

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /portfolio — управление личным списком акций.
    
    /portfolio — показать свои акции
    /portfolio add AAPL — добавить акцию
    /portfolio remove AAPL — удалить акцию
    """
    
    # ID пользователя — уникальный для каждого человека в Telegram
    user_id = str(update.effective_user.id)
    
    # Загружаем все портфолио из файла
    portfolios = load_json(PORTFOLIO_FILE)
    
    # Если у пользователя нет портфолио — создаём пустой список
    if user_id not in portfolios:
        portfolios[user_id] = []
    
    # Получаем список акций этого пользователя
    user_portfolio = portfolios[user_id]
    
    # Если нет аргументов — показываем портфолио
    if not context.args:
        if not user_portfolio:
            await update.message.reply_text(
                "📂 Твой портфель пуст!\n\n"
                "Добавь акции командой:\n"
                "/portfolio add AAPL"
            )
            return
        
        await update.message.reply_text("⏳ Загружаю твой портфель...")
        
        lines = ["💼 *Твой портфель:*\n"]
        
        for ticker in user_portfolio:
            data = get_stock_price(ticker)
            if data:
                arrow = "🟢" if data["change_percent"] >= 0 else "🔴"
                sign = "+" if data["change_percent"] >= 0 else ""
                lines.append(
                    f"{arrow} *{ticker}*: "
                    f"{data['price']}$ "
                    f"({sign}{data['change_percent']}%)"
                )
        
        lines.append("\nДля управления:")
        lines.append("/portfolio add TSLA — добавить")
        lines.append("/portfolio remove TSLA — удалить")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return
    
    # Если есть аргументы — обрабатываем команды add/remove
    action = context.args[0].lower()  # "add" или "remove"
    
    # Проверяем что указан тикер
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Укажи тикер!\n"
            "Пример: /portfolio add AAPL"
        )
        return
    
    ticker = context.args[1].upper()
    
    if action == "add":
        # Добавляем акцию если её ещё нет в портфеле
        if ticker in user_portfolio:
            await update.message.reply_text(f"⚠️ {ticker} уже есть в портфеле!")
        else:
            user_portfolio.append(ticker)
            portfolios[user_id] = user_portfolio
            save_json(PORTFOLIO_FILE, portfolios)  # Сохраняем изменения
            await update.message.reply_text(f"✅ {ticker} добавлен в портфель!")
    
    elif action == "remove":
        # Удаляем акцию если она есть в портфеле
        if ticker not in user_portfolio:
            await update.message.reply_text(f"⚠️ {ticker} нет в портфеле!")
        else:
            user_portfolio.remove(ticker)
            portfolios[user_id] = user_portfolio
            save_json(PORTFOLIO_FILE, portfolios)  # Сохраняем изменения
            await update.message.reply_text(f"✅ {ticker} удалён из портфеля!")
    
    else:
        await update.message.reply_text(
            "❌ Неверная команда!\n"
            "Используй: add или remove\n"
            "Пример: /portfolio add AAPL"
        )


# ─────────────────────────────────────────────────────────────
# Команда /alert
# ─────────────────────────────────────────────────────────────

async def alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /alert TICKER ЦЕНА — установить уведомление.
    Пример: /alert AAPL 200
    
    Бот сохранит алерт и при каждом запуске check_alerts()
    будет проверять достигнута ли цена.
    """
    
    user_id = str(update.effective_user.id)
    
    # Проверяем что указаны тикер и цена
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Укажи тикер и цену!\n"
            "Пример: /alert AAPL 200\n"
            "(уведомит когда AAPL достигнет $200)"
        )
        return
    
    ticker = context.args[0].upper()
    
    # Пробуем преобразовать цену в число
    try:
        target_price = float(context.args[1])
    except ValueError:
        await update.message.reply_text(
            "❌ Цена должна быть числом!\n"
            "Пример: /alert AAPL 200.50"
        )
        return
    
    # Загружаем все алерты
    alerts = load_json(ALERTS_FILE)
    
    if user_id not in alerts:
        alerts[user_id] = []
    
    # Получаем текущую цену чтобы понять — ждём роста или падения
    data = get_stock_price(ticker)
    if not data:
        await update.message.reply_text(f"❌ Не удалось найти акцию {ticker}")
        return
    
    current_price = data["price"]
    direction = "выше" if target_price > current_price else "ниже"
    
    # Сохраняем алерт
    alerts[user_id].append({
        "ticker": ticker,
        "target_price": target_price,
        "direction": direction,  # "выше" или "ниже"
        "chat_id": update.effective_chat.id,  # Нужно для отправки уведомления
    })
    
    save_json(ALERTS_FILE, alerts)
    
    await update.message.reply_text(
        f"🔔 Алерт установлен!\n\n"
        f"Акция: *{ticker}*\n"
        f"Текущая цена: {current_price}$\n"
        f"Уведомлю когда цена станет {direction} {target_price}$",
        parse_mode="Markdown"
    )


# ─────────────────────────────────────────────────────────────
# Проверка алертов (запускается автоматически каждые 5 минут)
# ─────────────────────────────────────────────────────────────

async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    """
    Эта функция запускается автоматически каждые 5 минут.
    Проверяет все алерты и отправляет уведомления если цена достигнута.
    """
    
    alerts = load_json(ALERTS_FILE)
    
    if not alerts:
        return  # Нет алертов — ничего не делаем
    
    # Собираем уникальные тикеры чтобы не делать лишних запросов
    all_tickers = set()
    for user_alerts in alerts.values():
        for alert_item in user_alerts:
            all_tickers.add(alert_item["ticker"])
    
    # Получаем текущие цены для всех тикеров
    prices = {}
    for ticker in all_tickers:
        data = get_stock_price(ticker)
        if data:
            prices[ticker] = data["price"]
    
    # Проверяем каждый алерт
    alerts_to_keep = {}  # Алерты которые ещё не сработали
    
    for user_id, user_alerts in alerts.items():
        remaining = []
        
        for alert_item in user_alerts:
            ticker = alert_item["ticker"]
            target = alert_item["target_price"]
            direction = alert_item["direction"]
            current = prices.get(ticker)
            
            if current is None:
                remaining.append(alert_item)  # Оставляем если не получили цену
                continue
            
            # Проверяем достигнута ли целевая цена
            triggered = (
                (direction == "выше" and current >= target) or
                (direction == "ниже" and current <= target)
            )
            
            if triggered:
                # Отправляем уведомление пользователю
                try:
                    await context.bot.send_message(
                        chat_id=alert_item["chat_id"],
                        text=(
                            f"🔔 *АЛЕРТ СРАБОТАЛ!*\n\n"
                            f"Акция *{ticker}* достигла цели!\n"
                            f"Текущая цена: *{current}$*\n"
                            f"Целевая цена: {target}$"
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Ошибка отправки алерта: {e}")
            else:
                remaining.append(alert_item)  # Алерт ещё не сработал
        
        if remaining:
            alerts_to_keep[user_id] = remaining
    
    # Сохраняем только несработавшие алерты
    save_json(ALERTS_FILE, alerts_to_keep)


# ─────────────────────────────────────────────────────────────
# Команда /crypto
# ─────────────────────────────────────────────────────────────

# Список популярных криптовалют и их тикеры на Yahoo Finance
CRYPTO_TICKERS = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "BNB": "BNB-USD",
    "XRP": "XRP-USD",
    "DOGE": "DOGE-USD",
    "ADA": "ADA-USD",
    "AVAX": "AVAX-USD",
    "DOT": "DOT-USD",
    "MATIC": "MATIC-USD",
}

async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /crypto BTC — показывает текущую цену криптовалюты.
    Пример: /crypto BTC
    Пример: /crypto ETH

    Без аргументов — показывает топ криптовалют.
    """

    # Если нет аргументов — показываем топ крипты
    if not context.args:
        await update.message.reply_text("⏳ Загружаю топ криптовалют...")

        lines = ["🪙 *Топ криптовалют прямо сейчас:*\n"]

        for symbol, ticker in CRYPTO_TICKERS.items():
            data = get_stock_price(ticker)
            if data:
                # Определяем направление цены
                change = data["change_percent"]
                arrow = "🟢" if change >= 0 else "🔴"
                sign = "+" if change >= 0 else ""

                # Форматируем цену красиво
                price = data["price"]
                if price >= 1:
                    price_str = f"${price:,.2f}"
                else:
                    price_str = f"${price:.6f}"

                lines.append(
                    f"{arrow} *{symbol}*: {price_str} ({sign}{change}%)"
                )

        lines.append(f"\n🕐 {datetime.now().strftime('%H:%M:%S')}")
        lines.append("\nДля деталей: /crypto BTC")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    # Если есть аргумент — показываем конкретную монету
    symbol = context.args[0].upper()

    # Проверяем известна ли нам эта монета
    # Если нет в нашем списке — пробуем добавить -USD
    ticker = CRYPTO_TICKERS.get(symbol, f"{symbol}-USD")

    await update.message.reply_text(f"⏳ Загружаю данные для {symbol}...")

    data = get_stock_price(ticker)

    if not data:
        await update.message.reply_text(
            f"❌ Не удалось найти криптовалюту {symbol}\n"
            f"Попробуй: BTC, ETH, SOL, BNB, XRP, DOGE"
        )
        return

    # Определяем направление цены
    change = data["change_percent"]
    arrow = "📈" if change >= 0 else "📉"
    sign = "+" if change >= 0 else ""

    # Форматируем цену — для дешёвых монет показываем больше знаков
    price = data["price"]
    if price >= 1:
        price_str = f"{price:,.2f}"
    else:
        price_str = f"{price:.6f}"

    # Определяем настроение рынка
    if change >= 5:
        mood = "🚀 Сильный рост!"
    elif change >= 2:
        mood = "📈 Растёт"
    elif change >= 0:
        mood = "😐 Стабильно"
    elif change >= -2:
        mood = "📉 Небольшое падение"
    elif change >= -5:
        mood = "😨 Падает"
    else:
        mood = "💥 Сильное падение!"

    text = (
        f"{arrow} *{symbol}*\n\n"
        f"💵 Цена: *${price_str}*\n"
        f"📊 Изменение: {sign}{change}%\n"
        f"💬 Настроение: {mood}\n"
        f"📦 Объём: {data.get('volume', 0):,}\n\n"
        f"🔔 Поставь алерт: /alert {ticker} <цена>\n"
        f"🕐 {datetime.now().strftime('%H:%M:%S')}"
    )

    await update.message.reply_text(text, parse_mode="Markdown")


# ============================================================
# 🚀 ЗАПУСК БОТА
# ============================================================

def main():
    """
    Главная функция — запускает бота.
    """
    
    print("🤖 Запускаю бота...")
    
    # Создаём приложение с нашим токеном
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    # Каждая строка говорит: "если пользователь написал /команда — вызови функцию"
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("alert", alert))
    app.add_handler(CommandHandler("crypto", crypto))
    
    # Запускаем проверку алертов каждые 5 минут (300 секунд)
    app.job_queue.run_repeating(check_alerts, interval=300, first=10)
    
    print("✅ Бот запущен! Нажми Ctrl+C чтобы остановить.")
    
    # Запускаем бота (он будет работать пока не нажмёшь Ctrl+C)
    app.run_polling()


# Это стандартная проверка — код внутри запустится только
# если ты запускаешь этот файл напрямую (не импортируешь его)
if __name__ == "__main__":
    main()
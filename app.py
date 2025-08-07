import json
import os
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request
import random

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Переменные окружения
TOKEN = os.getenv("TOKEN", "YOUR_BOT_TOKEN_HERE")
CARAPI_TOKEN = os.getenv("CARAPI_TOKEN", "YOUR_CARAPI_TOKEN")
CARAPI_SECRET = os.getenv("CARAPI_SECRET", "YOUR_CARAPI_SECRET")
JWT_TOKEN = None
application = None

# Инициализация бота (отложенная)
def init_bot():
    global application
    if not application and TOKEN != "YOUR_BOT_TOKEN_HERE":
        try:
            application = Application.builder().token(TOKEN).http_timeout(5).build()
            logger.info("Telegram Application initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telegram Application: {e}")
            return False
    return bool(application)

# Функция для получения JWT
def get_jwt():
    global JWT_TOKEN
    if not CARAPI_TOKEN or not CARAPI_SECRET:
        logger.error("CARAPI_TOKEN or CARAPI_SECRET is missing or empty")
        return None
    url = "https://carapi.app/api/auth/login"
    headers = {"accept": "text/plain", "Content-Type": "application/json"}
    payload = {"api_token": CARAPI_TOKEN, "api_secret": CARAPI_SECRET}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"JWT request status: {response.status_code}, content: {response.text[:500]}... (truncated)")
        if response.status_code == 200:
            JWT_TOKEN = response.text.strip()
            logger.info(f"Successfully obtained JWT: {JWT_TOKEN[:50]}... (truncated)")
            return JWT_TOKEN
        else:
            logger.error(f"Failed to get JWT: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        logger.error(f"JWT request error: {str(e)}")
        return None

# Flask: Корневой маршрут
@app.route("/")
def index():
    logger.info("Accessed root route")
    return "Car Finder Bot is running! Open the bot in Telegram or use /webapp for the Mini App."

# Flask: Webhook
@app.route("/webhook", methods=["POST"])
async def webhook():
    logger.info("Received webhook update")
    if not init_bot():
        return {"status": "error", "message": "Application not initialized"}, 500
    try:
        update = Update.de_json(request.get_json(), application.bot)
        if update:
            await application.process_update(update)
            logger.info("Update processed successfully")
        else:
            logger.warning("Invalid update received")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}, 500

# Flask: Тестовый маршрут
@app.route("/test")
def test():
    logger.info("Accessed test route")
    return {
        "status": "ok",
        "token_set": TOKEN != "YOUR_BOT_TOKEN_HERE",
        "webhook_active": init_bot()
    }

# Flask: Ручная установка webhook
@app.route("/setwebhook")
def set_webhook_manual():
    logger.info("Accessed setwebhook route")
    if not init_bot():
        return {"status": "error", "message": "Application not initialized"}, 500
    try:
        webhook_url = "https://cars-dun-phi.vercel.app/webhook"
        application.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
        return {"status": "ok", "message": f"Webhook set to {webhook_url}"}
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return {"status": "error", "message": str(e)}, 500

# Flask: Favicon
@app.route("/favicon.ico")
def favicon():
    return "", 204

# Flask: API для данных
@app.route("/api/cars")
def api_cars():
    logger.info("Accessed api/cars route")
    if not JWT_TOKEN:
        logger.info("Getting new JWT...")
        JWT_TOKEN = get_jwt()
        if not JWT_TOKEN:
            return {"error": "Failed to obtain JWT"}, 500
    headers = {"accept": "application/json", "Authorization": f"Bearer {JWT_TOKEN}"}
    try:
        response = requests.get("https://carapi.app/api/models/v2", headers=headers, timeout=10)
        logger.info(f"API response status: {response.status_code}, content: {response.text[:500]}... (truncated)")
        if response.status_code == 401:
            logger.info("JWT expired or invalid, refreshing...")
            JWT_TOKEN = get_jwt()
            if not JWT_TOKEN:
                return {"error": "Failed to refresh JWT"}, 500
            headers["Authorization"] = f"Bearer {JWT_TOKEN}"
            response = requests.get("https://carapi.app/api/models/v2", headers=headers, timeout=10)
        if response.status_code != 200:
            raise Exception(f"API returned status {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return {"error": str(e)}, 500

# Flask: Mini App
@app.route("/webapp")
def webapp():
    logger.info("Redirecting to React app")
    return app.send_static_file("index.html")

# Flask: Статические файлы
@app.route('/<path:path>')
def static_proxy(path):
    return app.send_static_file(path)

# Telegram: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Processing /start command")
    keyboard = [
        [InlineKeyboardButton("Открыть Car Finder", web_app={"url": "https://cars-dun-phi.vercel.app/webapp"})],
        [InlineKeyboardButton("Популярные бренды", callback_data="brands")]
    ]
    await update.message.reply_text("Добро пожаловать в Car Finder! Открой Mini App или выбери бренд.", reply_markup=InlineKeyboardMarkup(keyboard))

# Telegram: /search
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Processing /search command: {context.args}")
    args = context.args
    if not args:
        await update.message.reply_text("Используй: /search бренд год_от-год_до цена_от-цена_до тип (например, /search Toyota 2020-2023 2000000-3000000 Sedan)")
        return
    brand = args[0] if args else ""
    year_range = args[1].split("-") if len(args) > 1 else [2015, 2020]
    price_range = args[2].split("-") if len(args) > 2 else [0, float("inf")]
    car_type = args[3] if len(args) > 3 else ""
    
    if not JWT_TOKEN:
        JWT_TOKEN = get_jwt()
        if not JWT_TOKEN:
            await update.message.reply_text("Ошибка аутентификации. Проверь токены.")
            return
    headers = {"accept": "application/json", "Authorization": f"Bearer {JWT_TOKEN}"}
    params = {"json": json.dumps([
        {"field": "make", "op": "in", "val": [brand] if brand else []},
        {"field": "year", "op": ">=", "val": year_range[0]},
        {"field": "year", "op": "<=", "val": year_range[1]},
        {"field": "price", "op": ">=", "val": price_range[0]},
        {"field": "price", "op": "<=", "val": price_range[1]},
        {"field": "type", "op": "in", "val": [car_type] if car_type else []}
    ])}
    try:
        response = requests.get("https://carapi.app/api/models/v2", headers=headers, params=params, timeout=10)
        cars = response.json().get("data", [])
        if not cars:
            await update.message.reply_text("Автомобили не найдены.")
            return
        for car in cars[:5]:
            await update.message.reply_text(f"{car.get('name', '')} ({car.get('year', '')}) - {car.get('price', 0):,} ₽")
    except Exception as e:
        await update.message.reply_text(f"Ошибка поиска: {e}")

# Telegram: /list
async def list_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Processing /list command")
    if not JWT_TOKEN:
        JWT_TOKEN = get_jwt()
        if not JWT_TOKEN:
            await update.message.reply_text("Ошибка аутентификации. Проверь токены.")
            return
    headers = {"accept": "application/json", "Authorization": f"Bearer {JWT_TOKEN}"}
    try:
        response = requests.get("https://carapi.app/api/models/v2", headers=headers, params={"limit": 5}, timeout=10)
        cars = response.json().get("data", [])
        message = "Доступные автомобили:\n" + "\n".join([f"{car.get('name', '')} ({car.get('year', '')}) - {car.get('price', 0):,} ₽" for car in cars])
        keyboard = [[InlineKeyboardButton("Далее", callback_data="next_0")]] if response.json().get("collection", {}).get("pages", 1) > 1 else []
        await update.message.reply_text(message or "Автомобили не найдены.", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await update.message.reply_text(f"Ошибка загрузки: {e}")

# Telegram: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Processing /help command")
    await update.message.reply_text(
        "Команды:\n"
        "/start - Начать\n"
        "/search - Поиск (пример: /search Toyota 2020-2023 2000000-3000000 Sedan)\n"
        "/list - Список всех автомобилей\n"
        "/game - Угадай автомобиль\n"
        "/help - Справка"
    )

# Telegram: /game
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Processing /game command")
    if not JWT_TOKEN:
        JWT_TOKEN = get_jwt()
        if not JWT_TOKEN:
            await update.message.reply_text("Ошибка аутентификации. Проверь токены.")
            return
    headers = {"accept": "application/json", "Authorization": f"Bearer {JWT_TOKEN}"}
    try:
        response = requests.get("https://carapi.app/api/models/v2", headers=headers, params={"limit": 10}, timeout=10)
        cars = response.json().get("data", [])
        if not cars:
            await update.message.reply_text("Автомобили не найдены.")
            return
        car = random.choice(cars)
        options = random.sample(cars, min(3, len(cars)-1)) + [car]
        random.shuffle(options)
        keyboard = [[InlineKeyboardButton(f"{c.get('name', '')}", callback_data="correct" if c == car else "wrong")] for c in options]
        await update.message.reply_text("Угадай автомобиль!", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        await update.message.reply_text(f"Ошибка игры: {e}")

# Telegram: Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    logger.info(f"Processing button callback: {query.data}")
    if query.data == "brands":
        keyboard = [
            [InlineKeyboardButton("Toyota", callback_data="search_Toyota")],
            [InlineKeyboardButton("Honda", callback_data="search_Honda")],
            [InlineKeyboardButton("Ford", callback_data="search_Ford")],
            [InlineKeyboardButton("BMW", callback_data="search_BMW")],
            [InlineKeyboardButton("Mercedes", callback_data="search_Mercedes")]
        ]
        await query.message.reply_text("Выбери бренд:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("search_"):
        brand = query.data.split("_")[1]
        if not JWT_TOKEN:
            JWT_TOKEN = get_jwt()
            if not JWT_TOKEN:
                await query.message.reply_text("Ошибка аутентификации. Проверь токены.")
                return
        headers = {"accept": "application/json", "Authorization": f"Bearer {JWT_TOKEN}"}
        params = {"json": json.dumps([{"field": "make", "op": "in", "val": [brand]}])}
        try:
            response = requests.get("https://carapi.app/api/models/v2", headers=headers, params=params, timeout=10)
            cars = response.json().get("data", [])
            for car in cars[:5]:
                await query.message.reply_text(f"{car.get('name', '')} ({car.get('year', '')}) - {car.get('price', 0):,} ₽")
        except Exception as e:
            await query.message.reply_text(f"Ошибка поиска: {e}")
    elif query.data.startswith("next_"):
        page = int(query.data.split("_")[1]) + 1
        if not JWT_TOKEN:
            JWT_TOKEN = get_jwt()
            if not JWT_TOKEN:
                await query.message.reply_text("Ошибка аутентификации. Проверь токены.")
                return
        headers = {"accept": "application/json", "Authorization": f"Bearer {JWT_TOKEN}"}
        try:
            response = requests.get("https://carapi.app/api/models/v2", headers=headers, params={"page": page, "limit": 5}, timeout=10)
            cars = response.json().get("data", [])
            message = "\n".join([f"{car.get('name', '')} ({car.get('year', '')}) - {car.get('price', 0):,} ₽" for car in cars])
            keyboard = [[InlineKeyboardButton("Далее", callback_data=f"next_{page}")]] if response.json().get("collection", {}).get("pages", 1) > page else []
            await query.message.reply_text(message or "Больше нет автомобилей.", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.message.reply_text(f"Ошибка загрузки: {e}")
    elif query.data == "correct":
        await query.message.reply_text("Правильно! 🚗")
    elif query.data == "wrong":
        await query.message.reply_text("Неправильно, попробуй ещё!")

# Инициализация
def main():
    logger.info("Starting bot initialization")
    if init_bot():
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("search", search))
        application.add_handler(CommandHandler("list", list_cars))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("game", game))
        application.add_handler(CallbackQueryHandler(button))
        import asyncio
        asyncio.run(application.bot.setWebhook("https://cars-dun-phi.vercel.app/webhook"))
        logger.info("Webhook and handlers set successfully")
    else:
        logger.error("Bot initialization failed, handlers not added")

# Запуск Flask
if __name__ == "__main__":
    main()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
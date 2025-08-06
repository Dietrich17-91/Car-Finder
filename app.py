import json
import os
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Telegram bot token
TOKEN = os.getenv("TOKEN", "YOUR_BOT_TOKEN_HERE")
try:
    application = Application.builder().token(TOKEN).http_timeout(5).build()
    logger.info("Telegram Application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Telegram Application: {e}")
    application = None

# API credentials
API_TOKEN = os.getenv("CARAPI_TOKEN", "YOUR_CARAPI_TOKEN")
API_SECRET = os.getenv("CARAPI_SECRET", "YOUR_CARAPI_SECRET")

# Flask: Корневой маршрут
@app.route("/")
def index():
    logger.info("Accessed root route")
    return "Car Finder Bot is running! Open the bot in Telegram or use /webapp for the Mini App."

# Flask: Тестовый маршрут для отладки
@app.route("/test")
def test():
    logger.info("Accessed test route")
    webhook_info = application.bot.get_webhook_info() if application else None
    return {
        "status": "ok",
        "token_set": TOKEN != "YOUR_BOT_TOKEN_HERE",
        "webhook_set": webhook_info.url if webhook_info else False
    }

# Flask: Ручная установка webhook
@app.route("/setwebhook")
def set_webhook_manual():
    logger.info("Accessed setwebhook route")
    if not application:
        logger.error("Application not initialized")
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
    if not API_TOKEN or not API_SECRET:
        logger.error("API_TOKEN or API_SECRET is missing or empty")
        return {"error": "API credentials not configured"}, 500
    logger.info(f"API_TOKEN: {API_TOKEN[:5]}... (masked), API_SECRET: {API_SECRET[:5]}... (masked)")
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'X-API-KEY': API_SECRET
    }
    try:
        response = requests.get('https://api.carapi.com/cars', headers=headers, timeout=10)
        logger.info(f"API response status: {response.status_code}, content: {response.text[:500]}... (truncated)")
        if response.status_code == 410:
            logger.error("API endpoint returned 410 Gone. Trying alternative endpoint...")
            # Попытка альтернативного эндпоинта (если есть документация API)
            alt_response = requests.get('https://api.carapi.com/v2/cars', headers=headers, timeout=10)
            if alt_response.status_code == 200:
                logger.info(f"Alternative endpoint worked: {alt_response.text[:500]}... (truncated)")
                return alt_response.json()
            else:
                logger.error(f"Alternative endpoint failed with status: {alt_response.status_code}")
                raise Exception(f"API returned status {alt_response.status_code}")
        elif response.status_code != 200:
            raise Exception(f"API returned status {response.status_code}")
        return response.json()
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return {"error": str(e)}, 500

# Flask: Mini App теперь перенаправляет на React
@app.route("/webapp")
def webapp():
    logger.info("Redirecting to React app")
    return "Please use the Telegram Mini App via /webapp URL.", 200

# Flask: Статические файлы
@app.route('/<path:path>')
def static_proxy(path):
    return app.send_static_file(path)

# Telegram: Webhook
@app.route("/webhook", methods=["POST"])
async def webhook():
    logger.info("Received webhook update")
    try:
        if not application:
            logger.error("Application not initialized")
            return {"status": "error", "message": "Application not initialized"}, 500
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
    year_range = args[1].split("-") if len(args) > 1 else [0, 9999]
    price_range = args[2].split("-") if len(args) > 2 else [0, float("inf")]
    car_type = args[3] if len(args) > 3 else ""
    
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'X-API-KEY': API_SECRET
    }
    params = {
        'brand': brand,
        'year_min': year_range[0],
        'year_max': year_range[1],
        'price_min': price_range[0],
        'price_max': price_range[1],
        'type': car_type
    }
    try:
        response = requests.get('https://api.carapi.com/cars', headers=headers, params=params, timeout=10)
        cars = response.json().get('results', [])
        if not cars:
            await update.message.reply_text("Автомобили не найдены.")
            return
        for car in cars[:5]:
            await update.message.reply_photo(
                photo=car.get('image', ''),
                caption=f"{car.get('brand', '')} {car.get('model', '')} ({car.get('year', '')}) - {car.get('price', 0):,} ₽ - {car.get('type', '')}\n{car.get('details', '')}"
            )
    except Exception as e:
        await update.message.reply_text(f"Ошибка поиска: {e}")

# Telegram: /list
async def list_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Processing /list command")
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'X-API-KEY': API_SECRET
    }
    try:
        response = requests.get('https://api.carapi.com/cars', headers=headers, timeout=10)
        cars = response.json().get('results', [])[:5]
        message = "Доступные автомобили:\n" + "\n".join([f"{car.get('brand', '')} {car.get('model', '')} ({car.get('year', '')}) - {car.get('price', 0):,} ₽ - {car.get('type', '')}" for car in cars])
        keyboard = [[InlineKeyboardButton("Далее", callback_data="next_0")]] if len(cars) > 5 else []
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
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'X-API-KEY': API_SECRET
    }
    try:
        response = requests.get('https://api.carapi.com/cars', headers=headers, timeout=10)
        cars = response.json().get('results', [])
        if not cars:
            await update.message.reply_text("Автомобили не найдены.")
            return
        car = random.choice(cars)
        options = random.sample(cars, min(3, len(cars)-1)) + [car]
        random.shuffle(options)
        keyboard = [[InlineKeyboardButton(f"{c.get('brand', '')} {c.get('model', '')}", callback_data="correct" if c == car else "wrong")] for c in options]
        await update.message.reply_photo(
            photo=car.get('image', ''),
            caption="Угадай автомобиль!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
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
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'X-API-KEY': API_SECRET
        }
        params = {'brand': brand}
        try:
            response = requests.get('https://api.carapi.com/cars', headers=headers, params=params, timeout=10)
            cars = response.json().get('results', [])
            for car in cars[:5]:
                await query.message.reply_photo(
                    photo=car.get('image', ''),
                    caption=f"{car.get('brand', '')} {car.get('model', '')} ({car.get('year', '')}) - {car.get('price', 0):,} ₽ - {car.get('type', '')}\n{car.get('details', '')}"
                )
        except Exception as e:
            await query.message.reply_text(f"Ошибка поиска: {e}")
    elif query.data.startswith("next_"):
        page = int(query.data.split("_")[1]) + 1
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'X-API-KEY': API_SECRET
        }
        try:
            response = requests.get('https://api.carapi.com/cars', headers=headers, timeout=10)
            cars = response.json().get('results', [])
            start = page * 5
            filtered = cars[start:start+5]
            message = "\n".join([f"{car.get('brand', '')} {car.get('model', '')} ({car.get('year', '')}) - {car.get('price', 0):,} ₽ - {car.get('type', '')}" for car in filtered])
            keyboard = [[InlineKeyboardButton("Далее", callback_data=f"next_{page}")]] if start + 5 < len(cars) else []
            await query.message.reply_text(message or "Больше нет автомобилей.", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            await query.message.reply_text(f"Ошибка загрузки: {e}")
    elif query.data == "correct":
        await query.message.reply_text("Правильно! 🚗")
    elif query.data == "wrong":
        await query.message.reply_text("Неправильно, попробуй ещё!")

# Настройка webhook
async def set_webhook():
    webhook_url = "https://cars-dun-phi.vercel.app/webhook"
    logger.info(f"Setting webhook: {webhook_url}")
    if not application:
        logger.error("Application not initialized")
        raise Exception("Application not initialized")
    await application.bot.setWebhook(webhook_url)

# Инициализация
def main():
    logger.info("Starting bot initialization")
    if not application:
        logger.error("Application not initialized, skipping handlers")
        return
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("list", list_cars))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("game", game))
    application.add_handler(CallbackQueryHandler(button))
    import asyncio
    try:
        asyncio.run(set_webhook())
        logger.info("Webhook set successfully")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")

# Запуск Flask
if __name__ == "__main__":
    main()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
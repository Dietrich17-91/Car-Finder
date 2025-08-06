import json
import os
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, render_template_string
import random

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)

# Тестовые данные (49 автомобилей с фото из izmostock)
cars = [
    {"id": 1, "brand": "Toyota", "model": "Camry", "year": 2020, "price": 2500000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Toyota/Camry/2020/hero.jpg", "details": "Мощность: 200 л.с., Объём двигателя: 2.5 л, Привод: Передний, Топливо: Бензин"},
    {"id": 2, "brand": "Honda", "model": "Civic", "year": 2018, "price": 1800000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Honda/Civic/2018/hero.jpg", "details": "Мощность: 158 л.с., Объём двигателя: 2.0 л, Привод: Передний, Топливо: Бензин"},
    {"id": 3, "brand": "Ford", "model": "Explorer", "year": 2022, "price": 3500000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Ford/Explorer/2022/hero.jpg", "details": "Мощность: 300 л.с., Объём двигателя: 3.0 л, Привод: Полный, Топливо: Бензин"},
    {"id": 4, "brand": "BMW", "model": "X5", "year": 2021, "price": 4500000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/BMW/X5/2021/hero.jpg", "details": "Мощность: 340 л.с., Объём двигателя: 3.0 л, Привод: Полный, Топливо: Дизель"},
    {"id": 5, "brand": "Mercedes", "model": "C-Class", "year": 2019, "price": 3800000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Mercedes/C-Class/2019/hero.jpg", "details": "Мощность: 255 л.с., Объём двигателя: 2.0 л, Привод: Задний, Топливо: Бензин"},
    {"id": 6, "brand": "Audi", "model": "A4", "year": 2020, "price": 3600000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Audi/A4/2020/hero.jpg", "details": "Мощность: 190 л.с., Объём двигателя: 2.0 л, Привод: Полный, Топливо: Бензин"},
    {"id": 7, "brand": "Tesla", "model": "Model 3", "year": 2023, "price": 4200000, "type": "Electric", "photo": "https://izmostock.com/images/vehicle/Tesla/Model-3/2023/hero.jpg", "details": "Мощность: 306 л.с., Запас хода: 500 км, Привод: Задний, Топливо: Электричество"},
    {"id": 8, "brand": "Volkswagen", "model": "Tiguan", "year": 2021, "price": 3200000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Volkswagen/Tiguan/2021/hero.jpg", "details": "Мощность: 220 л.с., Объём двигателя: 2.0 л, Привод: Полный, Топливо: Бензин"},
    {"id": 9, "brand": "Hyundai", "model": "Tucson", "year": 2020, "price": 2800000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Hyundai/Tucson/2020/hero.jpg", "details": "Мощность: 180 л.с., Объём двигателя: 2.0 л, Привод: Передний, Топливо: Бензин"},
    {"id": 10, "brand": "Chevrolet", "model": "Equinox", "year": 2019, "price": 2600000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Chevrolet/Equinox/2019/hero.jpg", "details": "Мощность: 170 л.с., Объём двигателя: 1.5 л, Привод: Передний, Топливо: Бензин"},
    {"id": 11, "brand": "Lexus", "model": "RX", "year": 2022, "price": 4800000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Lexus/RX/2022/hero.jpg", "details": "Мощность: 295 л.с., Объём двигателя: 3.5 л, Привод: Полный, Топливо: Бензин"},
    {"id": 12, "brand": "Porsche", "model": "Cayenne", "year": 2021, "price": 6500000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Porsche/Cayenne/2021/hero.jpg", "details": "Мощность: 340 л.с., Объём двигателя: 3.0 л, Привод: Полный, Топливо: Бензин"},
    {"id": 13, "brand": "Nissan", "model": "Altima", "year": 2020, "price": 2400000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Nissan/Altima/2020/hero.jpg", "details": "Мощность: 188 л.с., Объём двигателя: 2.5 л, Привод: Передний, Топливо: Бензин"},
    {"id": 14, "brand": "Subaru", "model": "Outback", "year": 2022, "price": 3400000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Subaru/Outback/2022/hero.jpg", "details": "Мощность: 260 л.с., Объём двигателя: 2.4 л, Привод: Полный, Топливо: Бензин"},
    {"id": 15, "brand": "Kia", "model": "Sportage", "year": 2021, "price": 2700000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Kia/Sportage/2021/hero.jpg", "details": "Мощность: 181 л.с., Объём двигателя: 2.0 л, Привод: Передний, Топливо: Бензин"},
    {"id": 16, "brand": "Mazda", "model": "CX-5", "year": 2020, "price": 3000000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Mazda/CX-5/2020/hero.jpg", "details": "Мощность: 187 л.с., Объём двигателя: 2.5 л, Привод: Полный, Топливо: Бензин"},
    {"id": 17, "brand": "Jeep", "model": "Wrangler", "year": 2023, "price": 4000000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Jeep/Wrangler/2023/hero.jpg", "details": "Мощность: 285 л.с., Объём двигателя: 3.6 л, Привод: Полный, Топливо: Бензин"},
    {"id": 18, "brand": "Volvo", "model": "XC90", "year": 2021, "price": 5000000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Volvo/XC90/2021/hero.jpg", "details": "Мощность: 316 л.с., Объём двигателя: 2.0 л, Привод: Полный, Топливо: Гибрид"},
    {"id": 19, "brand": "Jaguar", "model": "F-Pace", "year": 2020, "price": 4600000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Jaguar/F-Pace/2020/hero.jpg", "details": "Мощность: 250 л.с., Объём двигателя: 2.0 л, Привод: Полный, Топливо: Дизель"},
    {"id": 20, "brand": "Land Rover", "model": "Range Rover", "year": 2022, "price": 7000000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Land-Rover/Range-Rover/2022/hero.jpg", "details": "Мощность: 400 л.с., Объём двигателя: 3.0 л, Привод: Полный, Топливо: Дизель"},
    {"id": 21, "brand": "Toyota", "model": "Corolla", "year": 2019, "price": 2200000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Toyota/Corolla/2019/hero.jpg", "details": "Мощность: 132 л.с., Объём двигателя: 1.8 л, Привод: Передний, Топливо: Бензин"},
    {"id": 22, "brand": "Honda", "model": "Accord", "year": 2021, "price": 2900000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Honda/Accord/2021/hero.jpg", "details": "Мощность: 192 л.с., Объём двигателя: 1.5 л, Привод: Передний, Топливо: Бензин"},
    {"id": 23, "brand": "Ford", "model": "Mustang", "year": 2023, "price": 3800000, "type": "Coupe", "photo": "https://izmostock.com/images/vehicle/Ford/Mustang/2023/hero.jpg", "details": "Мощность: 450 л.с., Объём двигателя: 5.0 л, Привод: Задний, Топливо: Бензин"},
    {"id": 24, "brand": "BMW", "model": "3 Series", "year": 2020, "price": 4000000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/BMW/3-Series/2020/hero.jpg", "details": "Мощность: 255 л.с., Объём двигателя: 2.0 л, Привод: Задний, Топливо: Бензин"},
    {"id": 25, "brand": "Mercedes", "model": "E-Class", "year": 2021, "price": 4800000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Mercedes/E-Class/2021/hero.jpg", "details": "Мощность: 362 л.с., Объём двигателя: 3.0 л, Привод: Полный, Топливо: Гибрид"},
    {"id": 26, "brand": "Audi", "model": "Q5", "year": 2022, "price": 4300000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Audi/Q5/2022/hero.jpg", "details": "Мощность: 261 л.с., Объём двигателя: 2.0 л, Привод: Полный, Топливо: Бензин"},
    {"id": 27, "brand": "Tesla", "model": "Model Y", "year": 2023, "price": 5000000, "type": "Electric", "photo": "https://izmostock.com/images/vehicle/Tesla/Model-Y/2023/hero.jpg", "details": "Мощность: 346 л.с., Запас хода: 480 км, Привод: Полный, Топливо: Электричество"},
    {"id": 28, "brand": "Volkswagen", "model": "Passat", "year": 2019, "price": 2600000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Volkswagen/Passat/2019/hero.jpg", "details": "Мощность: 174 л.с., Объём двигателя: 2.0 л, Привод: Передний, Топливо: Бензин"},
    {"id": 29, "brand": "Hyundai", "model": "Sonata", "year": 2020, "price": 2700000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Hyundai/Sonata/2020/hero.jpg", "details": "Мощность: 191 л.с., Объём двигателя: 2.5 л, Привод: Передний, Топливо: Бензин"},
    {"id": 30, "brand": "Chevrolet", "model": "Malibu", "year": 2021, "price": 2800000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Chevrolet/Malibu/2021/hero.jpg", "details": "Мощность: 160 л.с., Объём двигателя: 1.5 л, Привод: Передний, Топливо: Бензин"},
    {"id": 31, "brand": "Lexus", "model": "ES", "year": 2020, "price": 3900000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Lexus/ES/2020/hero.jpg", "details": "Мощность: 203 л.с., Объём двигателя: 2.5 л, Привод: Передний, Топливо: Бензин"},
    {"id": 32, "brand": "Porsche", "model": "911", "year": 2023, "price": 9000000, "type": "Coupe", "photo": "https://izmostock.com/images/vehicle/Porsche/911/2023/hero.jpg", "details": "Мощность: 450 л.с., Объём двигателя: 3.0 л, Привод: Полный, Топливо: Бензин"},
    {"id": 33, "brand": "Nissan", "model": "Rogue", "year": 2022, "price": 3100000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Nissan/Rogue/2022/hero.jpg", "details": "Мощность: 201 л.с., Объём двигателя: 1.5 л, Привод: Полный, Топливо: Бензин"},
    {"id": 34, "brand": "Subaru", "model": "Forester", "year": 2021, "price": 3200000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Subaru/Forester/2021/hero.jpg", "details": "Мощность: 182 л.с., Объём двигателя: 2.5 л, Привод: Полный, Топливо: Бензин"},
    {"id": 35, "brand": "Kia", "model": "Telluride", "year": 2023, "price": 3800000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Kia/Telluride/2023/hero.jpg", "details": "Мощность: 291 л.с., Объём двигателя: 3.8 л, Привод: Полный, Топливо: Бензин"},
    {"id": 36, "brand": "Mazda", "model": "3", "year": 2020, "price": 2500000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Mazda/3/2020/hero.jpg", "details": "Мощность: 191 л.с., Объём двигателя: 2.5 л, Привод: Передний, Топливо: Бензин"},
    {"id": 37, "brand": "Jeep", "model": "Grand Cherokee", "year": 2022, "price": 4500000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Jeep/Grand-Cherokee/2022/hero.jpg", "details": "Мощность: 293 л.с., Объём двигателя: 3.6 л, Привод: Полный, Топливо: Бензин"},
    {"id": 38, "brand": "Volvo", "model": "XC60", "year": 2021, "price": 4200000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Volvo/XC60/2021/hero.jpg", "details": "Мощность: 250 л.с., Объём двигателя: 2.0 л, Привод: Полный, Топливо: Бензин"},
    {"id": 39, "brand": "Jaguar", "model": "E-Pace", "year": 2020, "price": 4100000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Jaguar/E-Pace/2020/hero.jpg", "details": "Мощность: 200 л.с., Объём двигателя: 2.0 л, Привод: Полный, Топливо: Дизель"},
    {"id": 40, "brand": "Land Rover", "model": "Discovery", "year": 2022, "price": 6000000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Land-Rover/Discovery/2022/hero.jpg", "details": "Мощность: 296 л.с., Объём двигателя: 3.0 л, Привод: Полный, Топливо: Дизель"},
    {"id": 41, "brand": "Toyota", "model": "RAV4", "year": 2021, "price": 3100000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Toyota/RAV4/2021/hero.jpg", "details": "Мощность: 203 л.с., Объём двигателя: 2.5 л, Привод: Полный, Топливо: Бензин"},
    {"id": 42, "brand": "Honda", "model": "CR-V", "year": 2022, "price": 3300000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Honda/CR-V/2022/hero.jpg", "details": "Мощность: 190 л.с., Объём двигателя: 1.5 л, Привод: Полный, Топливо: Бензин"},
    {"id": 43, "brand": "Ford", "model": "F-150", "year": 2023, "price": 4500000, "type": "Pickup", "photo": "https://izmostock.com/images/vehicle/Ford/F-150/2023/hero.jpg", "details": "Мощность: 400 л.с., Объём двигателя: 3.5 л, Привод: Полный, Топливо: Гибрид"},
    {"id": 44, "brand": "BMW", "model": "5 Series", "year": 2020, "price": 4700000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/BMW/5-Series/2020/hero.jpg", "details": "Мощность: 335 л.с., Объём двигателя: 3.0 л, Привод: Полный, Топливо: Бензин"},
    {"id": 45, "brand": "Mercedes", "model": "GLC", "year": 2021, "price": 4400000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Mercedes/GLC/2021/hero.jpg", "details": "Мощность: 255 л.с., Объём двигателя: 2.0 л, Привод: Полный, Топливо: Бензин"},
    {"id": 46, "brand": "Audi", "model": "Q7", "year": 2022, "price": 5200000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Audi/Q7/2022/hero.jpg", "details": "Мощность: 335 л.с., Объём двигателя: 3.0 л, Привод: Полный, Топливо: Бензин"},
    {"id": 47, "brand": "Tesla", "model": "Model S", "year": 2023, "price": 8000000, "type": "Electric", "photo": "https://izmostock.com/images/vehicle/Tesla/Model-S/2023/hero.jpg", "details": "Мощность: 670 л.с., Запас хода: 652 км, Привод: Полный, Топливо: Электричество"},
    {"id": 48, "brand": "Volkswagen", "model": "Jetta", "year": 2019, "price": 2300000, "type": "Sedan", "photo": "https://izmostock.com/images/vehicle/Volkswagen/Jetta/2019/hero.jpg", "details": "Мощность: 147 л.с., Объём двигателя: 1.4 л, Привод: Передний, Топливо: Бензин"},
    {"id": 49, "brand": "Hyundai", "model": "Kona", "year": 2021, "price": 2600000, "type": "SUV", "photo": "https://izmostock.com/images/vehicle/Hyundai/Kona/2021/hero.jpg", "details": "Мощность: 147 л.с., Объём двигателя: 2.0 л, Привод: Передний, Топливо: Бензин"},
]

# Telegram bot token
TOKEN = os.getenv("TOKEN", "YOUR_BOT_TOKEN_HERE")
CAR_API_KEY = os.getenv("CAR_API_KEY", "YOUR_CARAPI_KEY")
try:
    application = Application.builder().token(TOKEN).http_timeout(5).build()
    logger.info("Telegram Application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Telegram Application: {e}")
    application = None

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

# Flask: Mini App
@app.route("/webapp")
def webapp():
    logger.info("Accessed webapp route")
    html = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Car Finder</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/choices.js@10.2.1/public/assets/scripts/choices.min.js"></script>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link href="https://cdn.jsdelivr.net/npm/choices.js@10.2.1/public/assets/styles/choices.min.css" rel="stylesheet">
        <style>
            body { font-family: 'Arial', sans-serif; background: linear-gradient(135deg, #1e3a8a, #3b82f6); }
            .car-card { transition: transform 0.3s ease, box-shadow 0.3s ease; }
            .car-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3); }
            .pagination-btn { transition: background-color 0.3s ease, transform 0.2s ease; }
            .pagination-btn:hover { background-color: #1d4ed8; transform: scale(1.05); }
            .choices__inner { background-color: #fff; border-radius: 8px; padding: 8px; }
            .choices__list--dropdown { background-color: #fff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); }
            .choices__item--selectable { padding: 8px; transition: background-color 0.2s ease; }
            .choices__item--selectable:hover { background-color: #e0f2fe; }
            .slider { width: 100%; }
            .slider-value { font-size: 0.9rem; color: #fff; }
        </style>
    </head>
    <body class="min-h-screen p-5">
        <div class="max-w-7xl mx-auto">
            <h1 class="text-4xl font-extrabold text-center text-white mb-8">Car Finder 🚗</h1>
            
            <!-- Фильтры -->
            <div class="bg-white p-6 rounded-xl shadow-lg mb-8">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Бренд</label>
                        <select id="brand" class="w-full">
                            <option value="">Все бренды</option>
                            <option value="Toyota">Toyota</option>
                            <option value="Honda">Honda</option>
                            <option value="Ford">Ford</option>
                            <option value="BMW">BMW</option>
                            <option value="Mercedes">Mercedes</option>
                            <option value="Audi">Audi</option>
                            <option value="Tesla">Tesla</option>
                            <option value="Volkswagen">Volkswagen</option>
                            <option value="Hyundai">Hyundai</option>
                            <option value="Chevrolet">Chevrolet</option>
                            <option value="Lexus">Lexus</option>
                            <option value="Porsche">Porsche</option>
                            <option value="Nissan">Nissan</option>
                            <option value="Subaru">Subaru</option>
                            <option value="Kia">Kia</option>
                            <option value="Mazda">Mazda</option>
                            <option value="Jeep">Jeep</option>
                            <option value="Volvo">Volvo</option>
                            <option value="Jaguar">Jaguar</option>
                            <option value="Land Rover">Land Rover</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Тип</label>
                        <select id="type" class="w-full">
                            <option value="">Все типы</option>
                            <option value="Sedan">Седан</option>
                            <option value="SUV">Внедорожник</option>
                            <option value="Coupe">Купе</option>
                            <option value="Electric">Электромобиль</option>
                            <option value="Pickup">Пикап</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Год</label>
                        <select id="year" class="w-full">
                            <option value="">Все годы</option>
                            <option value="2023">2023</option>
                            <option value="2022">2022</option>
                            <option value="2021">2021</option>
                            <option value="2020">2020</option>
                            <option value="2019">2019</option>
                            <option value="2018">2018</option>
                        </select>
                    </div>
                </div>
                <div class="mt-6">
                    <label class="block text-sm font-medium text-gray-700 mb-1">Макс. цена (₽)</label>
                    <input id="priceSlider" type="range" min="0" max="10000000" step="100000" value="10000000" class="slider">
                    <div class="slider-value mt-2" id="priceValue">10,000,000 ₽</div>
                </div>
                <div class="mt-6 flex space-x-4">
                    <button onclick="filterCars(1)" class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition font-semibold">Фильтровать</button>
                    <button onclick="resetFilters()" class="bg-gray-300 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-400 transition font-semibold">Сбросить</button>
                </div>
            </div>

            <!-- Результаты -->
            <div id="results" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"></div>

            <!-- Пагинация -->
            <div id="pagination" class="flex justify-center space-x-2 mt-8"></div>

            <!-- Модальное окно для деталей -->
            <div id="modal" class="fixed inset-0 bg-black bg-opacity-75 hidden flex items-center justify-center">
                <div class="bg-white p-8 rounded-xl max-w-lg w-full relative">
                    <button onclick="closeModal()" class="absolute top-4 right-4 text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
                    <h2 id="modal-title" class="text-2xl font-bold mb-4"></h2>
                    <img id="modal-photo" class="w-full h-64 object-cover rounded-lg mb-4">
                    <p id="modal-details" class="text-gray-700 whitespace-pre-line"></p>
                    <div class="mt-4">
                        <h3 class="text-lg font-semibold">Характеристики:</h3>
                        <ul id="modal-specs" class="list-disc pl-5 text-gray-600"></ul>
                    </div>
                    <button onclick="closeModal()" class="mt-6 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition">Закрыть</button>
                </div>
            </div>

            <script>
                let currentPage = 1;
                const carsPerPage = 9;
                const cars = ${json.dumps(cars)}; // Встраивание данных для клиентской фильтрации

                // Инициализация Choices.js
                new Choices('#brand', { searchPlaceholderValue: 'Выберите бренд', noResultsText: 'Бренд не найден' });
                new Choices('#type', { searchPlaceholderValue: 'Выберите тип', noResultsText: 'Тип не найден' });
                new Choices('#year', { searchPlaceholderValue: 'Выберите год', noResultsText: 'Год не найден' });

                // Обновление значения слайдера
                const priceSlider = document.getElementById('priceSlider');
                const priceValue = document.getElementById('priceValue');
                priceSlider.addEventListener('input', () => {
                    priceValue.textContent = priceSlider.value.toLocaleString('ru-RU') + ' ₽';
                });

                function filterCars(page = 1) {
                    const brand = document.getElementById('brand').value;
                    const type = document.getElementById('type').value;
                    const year = document.getElementById('year').value;
                    const maxPrice = parseFloat(priceSlider.value);
                    const filtered = cars.filter(car =>
                        (!brand || car.brand.toLowerCase().includes(brand.toLowerCase())) &&
                        (!type || car.type.toLowerCase().includes(type.toLowerCase())) &&
                        (!year || car.year == year) &&
                        car.price <= maxPrice
                    );
                    currentPage = page;
                    displayCars(filtered, page);
                    displayPagination(filtered);
                }

                function displayCars(cars, page) {
                    const start = (page - 1) * carsPerPage;
                    const end = start + carsPerPage;
                    const paginatedCars = cars.slice(start, end);
                    let html = '';
                    paginatedCars.forEach(car => {
                        html += `
                            <div class="car-card bg-white p-5 rounded-xl shadow-lg" style="opacity: 0; transform: translateY(20px);">
                                <img src="${car.photo}" alt="${car.brand} ${car.model}" class="w-full h-48 object-cover rounded-lg mb-3">
                                <h3 class="text-xl font-semibold text-gray-800">${car.brand} ${car.model}</h3>
                                <p class="text-gray-600">${car.year} | ${car.type} | ${car.price.toLocaleString('ru-RU')} ₽</p>
                                <button onclick="showModal(${car.id})" class="mt-3 bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition">Подробнее</button>
                            </div>
                        `;
                    });
                    document.getElementById('results').innerHTML = html;
                    gsap.to('.car-card', { opacity: 1, y: 0, stagger: 0.1, duration: 0.5 });
                }

                function displayPagination(cars) {
                    const totalPages = Math.ceil(cars.length / carsPerPage);
                    let html = '';
                    for (let i = 1; i <= totalPages; i++) {
                        html += `
                            <button class="pagination-btn px-4 py-2 rounded-lg ${i === currentPage ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'}"
                                    onclick="filterCars(${i})">${i}</button>
                        `;
                    }
                    document.getElementById('pagination').innerHTML = html;
                }

                function resetFilters() {
                    document.getElementById('brand').value = '';
                    document.getElementById('type').value = '';
                    document.getElementById('year').value = '';
                    priceSlider.value = 10000000;
                    priceValue.textContent = '10,000,000 ₽';
                    filterCars(1);
                }

                function showModal(carId) {
                    const car = cars.find(c => c.id === carId);
                    document.getElementById('modal-title').textContent = `${car.brand} ${car.model}`;
                    document.getElementById('modal-photo').src = car.photo;
                    document.getElementById('modal-details').textContent = car.details;
                    document.getElementById('modal-specs').innerHTML = car.details.split(', ').map(spec => `<li>${spec}</li>`).join('');
                    document.getElementById('modal').classList.remove('hidden');
                    gsap.from('#modal > div', { opacity: 0, scale: 0.8, duration: 0.3 });
                }

                function closeModal() {
                    document.getElementById('modal').classList.add('hidden');
                }

                // Инициализация
                filterCars(1);
            </script>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

# Flask: Фильтрация
@app.route("/filter")
def filter_cars():
    logger.info("Accessed filter route")
    return json.dumps(cars)  # Возвращаем все данные для клиентской фильтрации

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
    
    filtered = [
        car for car in cars
        if (not brand or brand.lower() in car["brand"].lower()) and
           int(year_range[0]) <= car["year"] <= int(year_range[1]) and
           float(price_range[0]) <= car["price"] <= float(price_range[1]) and
           (not car_type or car_type.lower() in car["type"].lower())
    ]
    
    if not filtered:
        await update.message.reply_text("Автомобили не найдены.")
        return
    
    for car in filtered[:5]:
        await update.message.reply_photo(
            photo=car["photo"],
            caption=f"{car['brand']} {car['model']} ({car['year']}) - {car['price']:,} ₽ - {car['type']}\n{car['details']}"
        )

# Telegram: /list
async def list_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Processing /list command")
    message = "Доступные автомобили:\n" + "\n".join([f"{car['brand']} {car['model']} ({car['year']}) - {car['price']:,} ₽ - {car['type']}" for car in cars[:5]])
    keyboard = [[InlineKeyboardButton("Далее", callback_data="next_0")]] if len(cars) > 5 else []
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

# Telegram: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Processing /help command")
    await update.message.reply_text(
        "Команды:\n"
        "/start - Начать\n"
        "/search - Поиск (пример: /search Toyota 2020-2023 2000000-3000000 Sedan)\n"
        "/list - Список автомобилей\n"
        "/game - Угадай автомобиль\n"
        "/help - Справка"
    )

# Telegram: /game
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Processing /game command")
    car = random.choice(cars)
    options = random.sample(cars, 3) + [car]
    random.shuffle(options)
    keyboard = [[InlineKeyboardButton(f"{c['brand']} {c['model']}", callback_data="correct" if c == car else "wrong")] for c in options]
    await update.message.reply_photo(
        photo=car["photo"],
        caption="Угадай автомобиль!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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
        filtered = [car for car in cars if brand.lower() in car["brand"].lower()]
        for car in filtered[:5]:
            await query.message.reply_photo(
                photo=car["photo"],
                caption=f"{car['brand']} {car['model']} ({car['year']}) - {car['price']:,} ₽ - {car['type']}\n{car['details']}"
            )
    elif query.data.startswith("next_"):
        page = int(query.data.split("_")[1]) + 1
        start = page * 5
        filtered = cars[start:start+5]
        message = "\n".join([f"{car['brand']} {car['model']} ({car['year']}) - {car['price']:,} ₽ - {car['type']}" for car in filtered])
        keyboard = [[InlineKeyboardButton("Далее", callback_data=f"next_{page}")]] if start + 5 < len(cars) else []
        await query.message.reply_text(message or "Больше нет автомобилей.", reply_markup=InlineKeyboardMarkup(keyboard))
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
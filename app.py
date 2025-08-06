import json
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request, render_template_string
from threading import Thread

# Flask app для Mini App
app = Flask(__name__)

# Тестовые данные
cars = [
    {"id": 1, "brand": "Toyota", "model": "Camry", "year": 2020, "price": 25000, "type": "Sedan", "photo": "https://via.placeholder.com/150?text=Toyota+Camry"},
    {"id": 2, "brand": "Honda", "model": "Civic", "year": 2018, "price": 20000, "type": "Sedan", "photo": "https://via.placeholder.com/150?text=Honda+Civic"},
    {"id": 3, "brand": "Ford", "model": "Explorer", "year": 2022, "price": 35000, "type": "SUV", "photo": "https://via.placeholder.com/150?text=Ford+Explorer"}
]

# Сохранение данных
with open("cars.json", "w") as f:
    json.dump(cars, f)

# Telegram bot token
TOKEN = os.getenv("TOKEN", "YOUR_BOT_TOKEN_HERE")
CAR_API_KEY = os.getenv("CAR_API_KEY", "YOUR_CARAPI_KEY")

# Flask: Mini App
@app.route("/webapp")
def webapp():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Car Finder</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body { font-family: Arial; margin: 20px; background: #f0f0f0; }
            .car { margin: 10px; padding: 10px; border: 1px solid #ccc; background: white; border-radius: 5px; }
            img { max-width: 100px; border-radius: 5px; }
            select, input, button { margin: 5px; padding: 8px; }
            button { background: #0088cc; color: white; border: none; border-radius: 5px; cursor: pointer; }
            #results { margin-top: 20px; }
        </style>
    </head>
    <body>
        <h1>Car Finder</h1>
        <select id="brand">
            <option value="">Все бренды</option>
            <option value="Toyota">Toyota</option>
            <option value="Honda">Honda</option>
            <option value="Ford">Ford</option>
        </select>
        <input id="maxPrice" placeholder="Макс. цена (e.g., 30000)">
        <input id="year" placeholder="Год (e.g., 2020)">
        <button onclick="filterCars()">Фильтровать</button>
        <button onclick="buyPremium()">Купить премиум за Telegram Stars</button>
        <div id="results"></div>
        <script>
            async function filterCars() {
                const brand = document.getElementById("brand").value;
                const maxPrice = document.getElementById("maxPrice").value;
                const year = document.getElementById("year").value;
                const response = await fetch(`/filter?brand=${brand}&maxPrice=${maxPrice}&year=${year}`);
                const cars = await response.json();
                let html = "";
                cars.forEach(car => {
                    html += `<div class="car">
                        <img src="${car.photo}" alt="${car.brand} ${car.model}">
                        <p>${car.brand} ${car.model} (${car.year}) - $${car.price} - ${car.type}</p>
                    </div>`;
                });
                document.getElementById("results").innerHTML = html;
            }
            function buyPremium() {
                window.Telegram.WebApp.openInvoice("YOUR_STARS_INVOICE_LINK", (status) => {
                    if (status === "paid") alert("Премиум активирован!");
                });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

# Flask: Фильтрация
@app.route("/filter")
def filter_cars():
    brand = request.args.get("brand", "").lower()
    max_price = request.args.get("maxPrice", float("inf"), type=float)
    year = request.args.get("year", 0, type=int)
    with open("cars.json", "r") as f:
        cars = json.load(f)
    filtered = [
        car for car in cars
        if (not brand or brand in car["brand"].lower()) and
           car["price"] <= max_price and
           (not year or car["year"] == year)
    ]
    return json.dumps(filtered[:5])

# CarAPI
def fetch_cars_from_api(brand="", max_price=float("inf"), year=0):
    try:
        url = f"https://api.carapi.app/v1/cars?api_key={CAR_API_KEY}&brand={brand}&max_price={max_price}&year={year}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# Telegram: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Открыть Car Finder", web_app={"url": "https://your-vercel-project.vercel.app/webapp"})],
        [InlineKeyboardButton("Популярные бренды", callback_data="brands")]
    ]
    await update.message.reply_text("Добро пожаловать в Car Finder! Открой Mini App или выбери бренд.", reply_markup=InlineKeyboardMarkup(keyboard))

# Telegram: /search
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Используй: /search бренд год_от-год_до цена_от-цена_до тип (например, /search Toyota 2020-2023 20000-30000 Sedan)")
        return
    brand = args[0] if args else ""
    year_range = args[1].split("-") if len(args) > 1 else [0, 9999]
    price_range = args[2].split("-") if len(args) > 2 else [0, float("inf")]
    car_type = args[3] if len(args) > 3 else ""
    
    with open("cars.json", "r") as f:
        cars = json.load(f)
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
            caption=f"{car['brand']} {car['model']} ({car['year']}) - ${car['price']} - {car['type']}"
        )

# Telegram: /list
async def list_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("cars.json", "r") as f:
        cars = json.load(f)
    message = "Доступные автомобили:\n" + "\n".join([f"{car['brand']} {car['model']} ({car['year']}) - ${car['price']} - {car['type']}" for car in cars[:5]])
    keyboard = [[InlineKeyboardButton("Далее", callback_data="next_0")]] if len(cars) > 5 else []
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

# Telegram: /premium
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Купи премиум-фильтры за Telegram Stars! Открой Mini App и нажми 'Купить премиум'.")

# Telegram: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n"
        "/start - Начать\n"
        "/search - Поиск (пример: /search Toyota 2020-2023 20000-30000 Sedan)\n"
        "/list - Список автомобилей\n"
        "/premium - Премиум-фильтры\n"
        "/help - Справка"
    )

# Telegram: Обработка кнопок
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "brands":
        keyboard = [
            [InlineKeyboardButton("Toyota", callback_data="search_Toyota")],
            [InlineKeyboardButton("Honda", callback_data="search_Honda")],
            [InlineKeyboardButton("Ford", callback_data="search_Ford")]
        ]
        await query.message.reply_text("Выбери бренд:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("search_"):
        brand = query.data.split("_")[1]
        with open("cars.json", "r") as f:
            cars = json.load(f)
        filtered = [car for car in cars if brand.lower() in car["brand"].lower()]
        for car in filtered[:5]:
            await query.message.reply_photo(
                photo=car["photo"],
                caption=f"{car['brand']} {car['model']} ({car['year']}) - ${car['price']} - {car['type']}"
            )
    elif query.data.startswith("next_"):
        page = int(query.data.split("_")[1]) + 1
        with open("cars.json", "r") as f:
            cars = json.load(f)
        start = page * 5
        filtered = cars[start:start+5]
        message = "\n".join([f"{car['brand']} {car['model']} ({car['year']}) - ${car['price']} - {car['type']}" for car in filtered])
        keyboard = [[InlineKeyboardButton("Далее", callback_data=f"next_{page}")]] if start + 5 < len(cars) else []
        await query.message.reply_text(message or "Больше нет автомобилей.", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    # Запуск Telegram бота
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("list", list_cars))
    application.add_handler(CommandHandler("premium", premium))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button))
    
    # Запуск Flask в Vercel
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# Vercel serverless
def handler(event, context):
    return app(event, context)
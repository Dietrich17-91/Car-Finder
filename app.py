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

# Тестовые данные (49 автомобилей с реальными фото, вдохновлёнными Auto.ru)
cars = [
    {"id": 1, "brand": "Toyota", "model": "Camry", "year": 2020, "price": 2500000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2020/03/25/16/23/toyota-camry-4968336_1280.jpg"},
    {"id": 2, "brand": "Honda", "model": "Civic", "year": 2018, "price": 1800000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2017/08/06/12/06/honda-2592066_1280.jpg"},
    {"id": 3, "brand": "Ford", "model": "Explorer", "year": 2022, "price": 3500000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2019/10/07/12/29/ford-4532443_1280.jpg"},
    {"id": 4, "brand": "BMW", "model": "X5", "year": 2021, "price": 4500000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2018/05/29/22/31/bmw-3440390_1280.jpg"},
    {"id": 5, "brand": "Mercedes", "model": "C-Class", "year": 2019, "price": 3800000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2016/12/04/21/22/mercedes-1882937_1280.jpg"},
    {"id": 6, "brand": "Audi", "model": "A4", "year": 2020, "price": 3600000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/auto-2179220_1280.jpg"},
    {"id": 7, "brand": "Tesla", "model": "Model 3", "year": 2023, "price": 4200000, "type": "Electric", "photo": "https://cdn.pixabay.com/photo/2020/01/22/18/36/tesla-4786642_1280.jpg"},
    {"id": 8, "brand": "Volkswagen", "model": "Tiguan", "year": 2021, "price": 3200000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/11/15/09/29/volkswagen-2951622_1280.jpg"},
    {"id": 9, "brand": "Hyundai", "model": "Tucson", "year": 2020, "price": 2800000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2016/11/29/09/16/hyundai-1868741_1280.jpg"},
    {"id": 10, "brand": "Chevrolet", "model": "Equinox", "year": 2019, "price": 2600000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/10/15/16/45/chevrolet-2854562_1280.jpg"},
    {"id": 11, "brand": "Lexus", "model": "RX", "year": 2022, "price": 4800000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2016/12/07/21/01/lexus-1890952_1280.jpg"},
    {"id": 12, "brand": "Porsche", "model": "Cayenne", "year": 2021, "price": 6500000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/porsche-2179221_1280.jpg"},
    {"id": 13, "brand": "Nissan", "model": "Altima", "year": 2020, "price": 2400000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2017/06/12/15/08/nissan-2396065_1280.jpg"},
    {"id": 14, "brand": "Subaru", "model": "Outback", "year": 2022, "price": 3400000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/subaru-2179219_1280.jpg"},
    {"id": 15, "brand": "Kia", "model": "Sportage", "year": 2021, "price": 2700000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2016/11/29/09/16/kia-1868742_1280.jpg"},
    {"id": 16, "brand": "Mazda", "model": "CX-5", "year": 2020, "price": 3000000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/mazda-2179218_1280.jpg"},
    {"id": 17, "brand": "Jeep", "model": "Wrangler", "year": 2023, "price": 4000000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/08/06/12/06/jeep-2592067_1280.jpg"},
    {"id": 18, "brand": "Volvo", "model": "XC90", "year": 2021, "price": 5000000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2016/11/29/09/16/volvo-1868743_1280.jpg"},
    {"id": 19, "brand": "Jaguar", "model": "F-Pace", "year": 2020, "price": 4600000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/jaguar-2179222_1280.jpg"},
    {"id": 20, "brand": "Land Rover", "model": "Range Rover", "year": 2022, "price": 7000000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/land-rover-2179223_1280.jpg"},
    {"id": 21, "brand": "Toyota", "model": "Corolla", "year": 2019, "price": 2200000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2020/03/25/16/23/toyota-corolla-4968337_1280.jpg"},
    {"id": 22, "brand": "Honda", "model": "Accord", "year": 2021, "price": 2900000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2017/08/06/12/06/honda-2592068_1280.jpg"},
    {"id": 23, "brand": "Ford", "model": "Mustang", "year": 2023, "price": 3800000, "type": "Coupe", "photo": "https://cdn.pixabay.com/photo/2017/08/06/12/06/ford-2592069_1280.jpg"},
    {"id": 24, "brand": "BMW", "model": "3 Series", "year": 2020, "price": 4000000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2018/05/29/22/31/bmw-3440391_1280.jpg"},
    {"id": 25, "brand": "Mercedes", "model": "E-Class", "year": 2021, "price": 4800000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2016/12/04/21/22/mercedes-1882938_1280.jpg"},
    {"id": 26, "brand": "Audi", "model": "Q5", "year": 2022, "price": 4300000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/audi-2179224_1280.jpg"},
    {"id": 27, "brand": "Tesla", "model": "Model Y", "year": 2023, "price": 5000000, "type": "Electric", "photo": "https://cdn.pixabay.com/photo/2020/01/22/18/36/tesla-4786643_1280.jpg"},
    {"id": 28, "brand": "Volkswagen", "model": "Passat", "year": 2019, "price": 2600000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2017/11/15/09/29/volkswagen-2951623_1280.jpg"},
    {"id": 29, "brand": "Hyundai", "model": "Sonata", "year": 2020, "price": 2700000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2016/11/29/09/16/hyundai-1868744_1280.jpg"},
    {"id": 30, "brand": "Chevrolet", "model": "Malibu", "year": 2021, "price": 2800000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2017/10/15/16/45/chevrolet-2854563_1280.jpg"},
    {"id": 31, "brand": "Lexus", "model": "ES", "year": 2020, "price": 3900000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2016/12/07/21/01/lexus-1890953_1280.jpg"},
    {"id": 32, "brand": "Porsche", "model": "911", "year": 2023, "price": 9000000, "type": "Coupe", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/porsche-2179225_1280.jpg"},
    {"id": 33, "brand": "Nissan", "model": "Rogue", "year": 2022, "price": 3100000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/06/12/15/08/nissan-2396066_1280.jpg"},
    {"id": 34, "brand": "Subaru", "model": "Forester", "year": 2021, "price": 3200000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/subaru-2179226_1280.jpg"},
    {"id": 35, "brand": "Kia", "model": "Telluride", "year": 2023, "price": 3800000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2016/11/29/09/16/kia-1868745_1280.jpg"},
    {"id": 36, "brand": "Mazda", "model": "3", "year": 2020, "price": 2500000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/mazda-2179227_1280.jpg"},
    {"id": 37, "brand": "Jeep", "model": "Grand Cherokee", "year": 2022, "price": 4500000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/08/06/12/06/jeep-2592070_1280.jpg"},
    {"id": 38, "brand": "Volvo", "model": "XC60", "year": 2021, "price": 4200000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2016/11/29/09/16/volvo-1868746_1280.jpg"},
    {"id": 39, "brand": "Jaguar", "model": "E-Pace", "year": 2020, "price": 4100000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/jaguar-2179228_1280.jpg"},
    {"id": 40, "brand": "Land Rover", "model": "Discovery", "year": 2022, "price": 6000000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/land-rover-2179229_1280.jpg"},
    {"id": 41, "brand": "Toyota", "model": "RAV4", "year": 2021, "price": 3100000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2020/03/25/16/23/toyota-rav4-4968338_1280.jpg"},
    {"id": 42, "brand": "Honda", "model": "CR-V", "year": 2022, "price": 3300000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/08/06/12/06/honda-2592071_1280.jpg"},
    {"id": 43, "brand": "Ford", "model": "F-150", "year": 2023, "price": 4500000, "type": "Pickup", "photo": "https://cdn.pixabay.com/photo/2019/10/07/12/29/ford-4532444_1280.jpg"},
    {"id": 44, "brand": "BMW", "model": "5 Series", "year": 2020, "price": 4700000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2018/05/29/22/31/bmw-3440392_1280.jpg"},
    {"id": 45, "brand": "Mercedes", "model": "GLC", "year": 2021, "price": 4400000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2016/12/04/21/22/mercedes-1882939_1280.jpg"},
    {"id": 46, "brand": "Audi", "model": "Q7", "year": 2022, "price": 5200000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2017/03/27/14/56/audi-2179230_1280.jpg"},
    {"id": 47, "brand": "Tesla", "model": "Model S", "year": 2023, "price": 8000000, "type": "Electric", "photo": "https://cdn.pixabay.com/photo/2020/01/22/18/36/tesla-4786644_1280.jpg"},
    {"id": 48, "brand": "Volkswagen", "model": "Jetta", "year": 2019, "price": 2300000, "type": "Sedan", "photo": "https://cdn.pixabay.com/photo/2017/11/15/09/29/volkswagen-2951624_1280.jpg"},
    {"id": 49, "brand": "Hyundai", "model": "Kona", "year": 2021, "price": 2600000, "type": "SUV", "photo": "https://cdn.pixabay.com/photo/2016/11/29/09/16/hyundai-1868747_1280.jpg"},
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
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <style>
            body { font-family: 'Arial', sans-serif; }
            .car-card { transition: transform 0.3s ease, box-shadow 0.3s ease; }
            .car-card:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2); }
            .pagination-btn { transition: background-color 0.3s ease; }
            .pagination-btn:hover { background-color: #2563eb; }
            .premium-btn { animation: pulse 2s infinite; }
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
        </style>
    </head>
    <body class="bg-gray-100 min-h-screen p-5">
        <div class="max-w-7xl mx-auto">
            <h1 class="text-3xl font-bold text-center text-gray-800 mb-6">Car Finder 🚗</h1>
            
            <!-- Фильтры -->
            <div class="bg-white p-6 rounded-lg shadow-md mb-6">
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Бренд</label>
                        <select id="brand" class="mt-1 block w-full p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500">
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
                        <label class="block text-sm font-medium text-gray-700">Тип</label>
                        <select id="type" class="mt-1 block w-full p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500">
                            <option value="">Все типы</option>
                            <option value="Sedan">Седан</option>
                            <option value="SUV">Внедорожник</option>
                            <option value="Coupe">Купе</option>
                            <option value="Electric">Электромобиль</option>
                            <option value="Pickup">Пикап</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Макс. цена (₽)</label>
                        <input id="maxPrice" type="number" placeholder="Например, 3000000" class="mt-1 block w-full p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700">Год</label>
                        <input id="year" type="number" placeholder="Например, 2020" class="mt-1 block w-full p-2 border rounded-lg focus:ring-blue-500 focus:border-blue-500">
                    </div>
                </div>
                <div class="mt-4 flex space-x-4">
                    <button onclick="filterCars(1)" class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition">Фильтровать</button>
                    <button onclick="resetFilters()" class="bg-gray-300 text-gray-800 px-4 py-2 rounded-lg hover:bg-gray-400 transition">Сбросить</button>
                    <button onclick="buyPremium()" class="premium-btn bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition">Купить премиум</button>
                </div>
            </div>

            <!-- Результаты -->
            <div id="results" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"></div>

            <!-- Пагинация -->
            <div id="pagination" class="flex justify-center space-x-2 mt-6"></div>

            <!-- Модальное окно для деталей -->
            <div id="modal" class="fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center">
                <div class="bg-white p-6 rounded-lg max-w-lg w-full">
                    <h2 id="modal-title" class="text-xl font-bold mb-4"></h2>
                    <img id="modal-photo" class="w-full h-48 object-cover rounded-lg mb-4">
                    <p id="modal-details" class="text-gray-700"></p>
                    <button onclick="closeModal()" class="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">Закрыть</button>
                </div>
            </div>

            <script>
                let currentPage = 1;
                const carsPerPage = 9;

                async function filterCars(page = 1) {
                    const brand = document.getElementById("brand").value;
                    const type = document.getElementById("type").value;
                    const maxPrice = document.getElementById("maxPrice").value;
                    const year = document.getElementById("year").value;
                    const response = await fetch(`/filter?brand=${brand}&type=${type}&maxPrice=${maxPrice}&year=${year}`);
                    const cars = await response.json();
                    currentPage = page;
                    displayCars(cars, page);
                    displayPagination(cars);
                }

                function displayCars(cars, page) {
                    const start = (page - 1) * carsPerPage;
                    const end = start + carsPerPage;
                    const paginatedCars = cars.slice(start, end);
                    let html = "";
                    paginatedCars.forEach(car => {
                        html += `
                            <div class="car-card bg-white p-4 rounded-lg shadow-md" style="opacity: 0; transform: translateY(20px);">
                                <img src="${car.photo}" alt="${car.brand} ${car.model}" class="w-full h-40 object-cover rounded-lg mb-2">
                                <h3 class="text-lg font-semibold">${car.brand} ${car.model}</h3>
                                <p class="text-gray-600">${car.year} | ${car.type} | ${car.price.toLocaleString('ru-RU')} ₽</p>
                                <button onclick="showModal(${car.id})" class="mt-2 bg-blue-500 text-white px-3 py-1 rounded-lg hover:bg-blue-600">Подробнее</button>
                            </div>
                        `;
                    });
                    document.getElementById("results").innerHTML = html;
                    gsap.to(".car-card", { opacity: 1, y: 0, stagger: 0.1, duration: 0.5 });
                }

                function displayPagination(cars) {
                    const totalPages = Math.ceil(cars.length / carsPerPage);
                    let html = "";
                    for (let i = 1; i <= totalPages; i++) {
                        html += `
                            <button class="pagination-btn px-4 py-2 rounded-lg ${i === currentPage ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800'}"
                                    onclick="filterCars(${i})">${i}</button>
                        `;
                    }
                    document.getElementById("pagination").innerHTML = html;
                }

                function resetFilters() {
                    document.getElementById("brand").value = "";
                    document.getElementById("type").value = "";
                    document.getElementById("maxPrice").value = "";
                    document.getElementById("year").value = "";
                    filterCars(1);
                }

                function showModal(carId) {
                    const car = cars.find(c => c.id === carId);
                    document.getElementById("modal-title").textContent = `${car.brand} ${car.model}`;
                    document.getElementById("modal-photo").src = car.photo;
                    document.getElementById("modal-details").textContent = `Год: ${car.year}\nТип: ${car.type}\nЦена: ${car.price.toLocaleString('ru-RU')} ₽`;
                    document.getElementById("modal").classList.remove("hidden");
                    gsap.from("#modal > div", { opacity: 0, scale: 0.8, duration: 0.3 });
                }

                function closeModal() {
                    document.getElementById("modal").classList.add("hidden");
                }

                function buyPremium() {
                    window.Telegram.WebApp.openInvoice("YOUR_STARS_INVOICE_LINK", (status) => {
                        if (status === "paid") alert("Премиум активирован! 🚀");
                    });
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
    brand = request.args.get("brand", "").lower()
    type = request.args.get("type", "").lower()
    max_price = request.args.get("maxPrice", float("inf"), type=float)
    year = request.args.get("year", 0, type=int)
    filtered = [
        car for car in cars
        if (not brand or brand in car["brand"].lower()) and
           (not type or type in car["type"].lower()) and
           car["price"] <= max_price and
           (not year or car["year"] == year)
    ]
    return json.dumps(filtered)

# CarAPI
def fetch_cars_from_api(brand="", max_price=float("inf"), year=0):
    try:
        url = f"https://api.carapi.app/v1/cars?api_key={CAR_API_KEY}&brand={brand}&max_price={max_price}&year={year}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        logger.error(f"CarAPI error: {e}")
        return []

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
            caption=f"{car['brand']} {car['model']} ({car['year']}) - {car['price']:,} ₽ - {car['type']}"
        )

# Telegram: /list
async def list_cars(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Processing /list command")
    message = "Доступные автомобили:\n" + "\n".join([f"{car['brand']} {car['model']} ({car['year']}) - {car['price']:,} ₽ - {car['type']}" for car in cars[:5]])
    keyboard = [[InlineKeyboardButton("Далее", callback_data="next_0")]] if len(cars) > 5 else []
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

# Telegram: /premium
async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Processing /premium command")
    await update.message.reply_text("Купи премиум-фильтры за Telegram Stars! Открой Mini App и нажми 'Купить премиум'.")

# Telegram: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Processing /help command")
    await update.message.reply_text(
        "Команды:\n"
        "/start - Начать\n"
        "/search - Поиск (пример: /search Toyota 2020-2023 2000000-3000000 Sedan)\n"
        "/list - Список автомобилей\n"
        "/premium - Премиум-фильтры\n"
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
                caption=f"{car['brand']} {car['model']} ({car['year']}) - {car['price']:,} ₽ - {car['type']}"
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
    application.add_handler(CommandHandler("premium", premium))
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
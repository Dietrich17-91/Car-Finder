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
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-blue-900 to-blue-500 text-white font-sans">
        <div class="container mx-auto p-4 max-w-5xl">
            <h1 class="text-4xl font-extrabold text-center mb-8 animate-fade-in">Car Finder 🚗</h1>
            
            <!-- Фильтры -->
            <div class="bg-white/10 backdrop-blur-md p-6 rounded-xl mb-8 animate-slide-up">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Бренд</label>
                        <select id="brand" class="w-full p-2 border border-gray-600 rounded-lg bg-transparent text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">Все бренды</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Тип</label>
                        <select id="type" class="w-full p-2 border border-gray-600 rounded-lg bg-transparent text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">Все типы</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-300 mb-2">Год</label>
                        <select id="year" class="w-full p-2 border border-gray-600 rounded-lg bg-transparent text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <option value="">Все годы</option>
                        </select>
                    </div>
                </div>
                <div class="mt-6">
                    <label class="block text-sm font-medium text-gray-300 mb-2">Цена (₽)</label>
                    <div class="w-full h-2 bg-gray-600 rounded-full relative">
                        <div id="price-range" class="h-2 bg-blue-500 rounded-full absolute"></div>
                        <div id="price-thumb-left" class="w-4 h-4 bg-blue-500 rounded-full absolute -top-1 cursor-pointer transform -translate-x-1/2"></div>
                        <div id="price-thumb-right" class="w-4 h-4 bg-blue-500 rounded-full absolute -top-1 cursor-pointer transform -translate-x-1/2"></div>
                    </div>
                    <div class="flex justify-between text-sm text-gray-400 mt-2">
                        <span id="min-price">0</span>
                        <span id="max-price">10,000,000</span>
                    </div>
                </div>
                <div class="mt-6 flex space-x-4">
                    <button onclick="filterCars(1)" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-300 ease-in-out transform hover:scale-105">Фильтровать</button>
                    <button onclick="resetFilters()" class="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition duration-300 ease-in-out transform hover:scale-105">Сбросить</button>
                </div>
            </div>

            <!-- Результаты -->
            <div id="results" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"></div>

            <!-- Пагинация -->
            <div id="pagination" class="flex justify-center space-x-2 mt-8"></div>

            <!-- Модальное окно для деталей -->
            <div id="modal" class="fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center">
                <div class="bg-white p-6 rounded-xl max-w-lg w-full relative animate-fade-in-scale">
                    <button onclick="closeModal()" class="absolute top-4 right-4 text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
                    <h2 id="modal-title" class="text-2xl font-bold mb-4 text-gray-800"></h2>
                    <p id="modal-details" class="text-gray-700 whitespace-pre-line mb-4"></p>
                    <h3 class="text-lg font-semibold text-gray-800 mb-2">Характеристики:</h3>
                    <ul id="modal-specs" class="list-disc pl-5 text-gray-600"></ul>
                    <button onclick="closeModal()" class="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-300">Закрыть</button>
                </div>
            </div>

            <script>
                // Telegram Web App настройки
                window.Telegram.WebApp.ready();
                window.Telegram.WebApp.expand();
                window.Telegram.WebApp.setHeaderColor({ color_key: 'bg_color' });
                window.Telegram.WebApp.setBottomBarColor({ color: '#ffffff' });

                let cars = [];
                let currentPage = 1;
                const carsPerPage = 9;
                const minPrice = 0;
                const maxPrice = 10000000;

                // Загрузка данных из carapi
                async function loadCars() {
                    try {
                        const response = await fetch('https://api.carapi.com/cars', {
                            headers: {
                                'Authorization': `Bearer ${API_TOKEN}`,
                                'X-API-KEY': API_SECRET
                            }
                        });
                        const data = await response.json();
                        cars = data.results || [];
                        populateFilters();
                        filterCars(1);
                    } catch (error) {
                        console.error('Ошибка загрузки данных:', error);
                    }
                }

                // Динамическое заполнение фильтров
                function populateFilters() {
                    const brands = [...new Set(cars.map(car => car.brand))].sort();
                    const types = [...new Set(cars.map(car => car.type))].sort();
                    const years = [...new Set(cars.map(car => car.year))].sort((a, b) => b - a);

                    const brandSelect = document.getElementById('brand');
                    const typeSelect = document.getElementById('type');
                    const yearSelect = document.getElementById('year');

                    brands.forEach(brand => {
                        const option = document.createElement('option');
                        option.value = brand;
                        option.textContent = brand;
                        brandSelect.appendChild(option);
                    });

                    types.forEach(type => {
                        const option = document.createElement('option');
                        option.value = type;
                        option.textContent = type;
                        typeSelect.appendChild(option);
                    });

                    years.forEach(year => {
                        const option = document.createElement('option');
                        option.value = year;
                        option.textContent = year;
                        yearSelect.appendChild(option);
                    });
                }

                // Слайдер цены
                const slider = document.querySelector('.price-slider');
                const range = document.getElementById('price-range');
                const thumbLeft = document.getElementById('price-thumb-left');
                const thumbRight = document.getElementById('price-thumb-right');
                const minPriceDisplay = document.getElementById('min-price');
                const maxPriceDisplay = document.getElementById('max-price');

                let isDraggingLeft = false;
                let isDraggingRight = false;
                let leftPos = 0;
                let rightPos = 100;

                function updateRange() {
                    range.style.left = `${leftPos}%`;
                    range.style.width = `${rightPos - leftPos}%`;
                    thumbLeft.style.left = `${leftPos}%`;
                    thumbRight.style.left = `${rightPos}%`;
                    minPriceDisplay.textContent = Math.round((leftPos / 100) * maxPrice).toLocaleString('ru-RU');
                    maxPriceDisplay.textContent = Math.round((rightPos / 100) * maxPrice).toLocaleString('ru-RU');
                }

                thumbLeft.addEventListener('mousedown', () => isDraggingLeft = true);
                thumbRight.addEventListener('mousedown', () => isDraggingRight = true);

                document.addEventListener('mousemove', (e) => {
                    if (!isDraggingLeft && !isDraggingRight) return;
                    const rect = slider.getBoundingClientRect();
                    const position = Math.min(Math.max(0, (e.clientX - rect.left) / rect.width * 100), 100);
                    if (isDraggingLeft) {
                        leftPos = Math.min(position, rightPos - 1);
                        if (leftPos < 0) leftPos = 0;
                    } else if (isDraggingRight) {
                        rightPos = Math.max(position, leftPos + 1);
                        if (rightPos > 100) rightPos = 100;
                    }
                    updateRange();
                });

                document.addEventListener('mouseup', () => {
                    isDraggingLeft = false;
                    isDraggingRight = false;
                });

                // Фильтрация
                function filterCars(page = 1) {
                    const brand = document.getElementById('brand').value;
                    const type = document.getElementById('type').value;
                    const year = document.getElementById('year').value;
                    const minPriceValue = (leftPos / 100) * maxPrice;
                    const maxPriceValue = (rightPos / 100) * maxPrice;

                    const filtered = cars.filter(car => {
                        const matchesBrand = !brand || car.brand.toLowerCase().includes(brand.toLowerCase());
                        const matchesType = !type || car.type.toLowerCase().includes(type.toLowerCase());
                        const matchesYear = !year || car.year == year;
                        const matchesPrice = car.price >= minPriceValue && car.price <= maxPriceValue;
                        return matchesBrand && matchesType && matchesYear && matchesPrice;
                    });

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
                            <div class="bg-white/10 backdrop-blur-md p-4 rounded-xl text-center transition-transform duration-300 hover:scale-105 animate-fade-in-up">
                                <h3 class="text-xl font-semibold">${car.brand} ${car.model}</h3>
                                <p class="text-gray-300">${car.year} | ${car.type} | ${car.price.toLocaleString('ru-RU')} ₽</p>
                                <button onclick="showModal(${JSON.stringify(car)})" class="mt-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition duration-300">Подробнее</button>
                            </div>
                        `;
                    });
                    document.getElementById('results').innerHTML = html;
                }

                function displayPagination(cars) {
                    const totalPages = Math.ceil(cars.length / carsPerPage);
                    let html = '';
                    for (let i = 1; i <= totalPages; i++) {
                        html += `<button class="px-3 py-1 rounded-lg ${i === currentPage ? 'bg-blue-600' : 'bg-gray-600'} hover:bg-blue-700 transition duration-300" onclick="filterCars(${i})">${i}</button>`;
                    }
                    document.getElementById('pagination').innerHTML = html;
                }

                function resetFilters() {
                    document.getElementById('brand').value = '';
                    document.getElementById('type').value = '';
                    document.getElementById('year').value = '';
                    leftPos = 0;
                    rightPos = 100;
                    updateRange();
                    filterCars(1);
                }

                function showModal(car) {
                    document.getElementById('modal-title').textContent = `${car.brand} ${car.model}`;
                    document.getElementById('modal-details').textContent = car.details || 'Нет деталей';
                    document.getElementById('modal-specs').innerHTML = (car.details || '').split(', ').map(spec => `<li>${spec}</li>`).join('');
                    document.getElementById('modal').classList.remove('hidden');
                }

                function closeModal() {
                    document.getElementById('modal').classList.add('hidden');
                }

                // Инициализация
                loadCars();
                updateRange();
            </script>
            <style>
                @keyframes fade-in {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes fade-in-scale {
                    from { opacity: 0; transform: scale(0.9); }
                    to { opacity: 1; transform: scale(1); }
                }
                @keyframes slide-up {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                @keyframes fade-in-up {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .animate-fade-in { animation: fade-in 0.5s ease-out; }
                .animate-fade-in-scale { animation: fade-in-scale 0.5s ease-out; }
                .animate-slide-up { animation: slide-up 0.5s ease-out; }
                .animate-fade-in-up { animation: fade-in-up 0.5s ease-out; }
            </style>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

# Flask: Фильтрация
@app.route("/filter")
def filter_cars():
    logger.info("Accessed filter route")
    return json.dumps([])

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
        response = requests.get('https://api.carapi.com/cars', headers=headers, params=params)
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
        response = requests.get('https://api.carapi.com/cars', headers=headers)
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
        response = requests.get('https://api.carapi.com/cars', headers=headers)
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
            response = requests.get('https://api.carapi.com/cars', headers=headers, params=params)
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
            response = requests.get('https://api.carapi.com/cars', headers=headers)
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
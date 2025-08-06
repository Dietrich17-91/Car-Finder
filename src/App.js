import React, { useState, useEffect } from 'react';
import './App.css';

const App = () => {
  const [cars, setCars] = useState([]);
  const [filters, setFilters] = useState({ brand: '', type: '', year: '', minPrice: 0, maxPrice: 10000000 });
  const [currentPage, setCurrentPage] = useState(1);
  const carsPerPage = 9;

  useEffect(() => {
    fetch('/api/cars')
      .then(res => res.json())
      .then(data => setCars(data.results || []));
    window.Telegram.WebApp.ready();
    window.Telegram.WebApp.expand();
    window.Telegram.WebApp.setHeaderColor({ color_key: 'bg_color' });
    window.Telegram.WebApp.setBottomBarColor({ color: '#ffffff' });
  }, []);

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
    setCurrentPage(1);
  };

  const handlePriceChange = (type, value) => {
    setFilters(prev => ({
      ...prev,
      [type]: parseInt(value, 10) || (type === 'minPrice' ? 0 : 10000000)
    }));
    setCurrentPage(1);
  };

  const filteredCars = cars.filter(car => {
    const matchesBrand = !filters.brand || car.brand.toLowerCase().includes(filters.brand.toLowerCase());
    const matchesType = !filters.type || car.type.toLowerCase().includes(filters.type.toLowerCase());
    const matchesYear = !filters.year || car.year == filters.year;
    const matchesPrice = car.price >= filters.minPrice && car.price <= filters.maxPrice;
    return matchesBrand && matchesType && matchesYear && matchesPrice;
  });

  const paginatedCars = filteredCars.slice((currentPage - 1) * carsPerPage, currentPage * carsPerPage);
  const totalPages = Math.ceil(filteredCars.length / carsPerPage);

  const resetFilters = () => {
    setFilters({ brand: '', type: '', year: '', minPrice: 0, maxPrice: 10000000 });
    setCurrentPage(1);
  };

  const showModal = (car) => {
    document.getElementById('modal-title').textContent = `${car.brand} ${car.model}`;
    document.getElementById('modal-details').textContent = car.details || 'Нет деталей';
    document.getElementById('modal-specs').innerHTML = (car.details || '').split(', ').map(spec => `<li>${spec}</li>`).join('');
    document.getElementById('modal').classList.remove('hidden');
  };

  const closeModal = () => {
    document.getElementById('modal').classList.add('hidden');
  };

  return (
    <div className="container mx-auto p-4 max-w-5xl">
      <h1 className="text-4xl font-extrabold text-center mb-8 animate-fade-in">Car Finder 🚗</h1>
      <div className="bg-white/10 backdrop-blur-md p-6 rounded-xl mb-8 animate-slide-up">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Бренд</label>
            <select name="brand" value={filters.brand} onChange={handleFilterChange} className="w-full p-2 border border-gray-600 rounded-lg bg-transparent text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">Все бренды</option>
              {[...new Set(cars.map(car => car.brand))].sort().map(brand => (
                <option key={brand} value={brand}>{brand}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Тип</label>
            <select name="type" value={filters.type} onChange={handleFilterChange} className="w-full p-2 border border-gray-600 rounded-lg bg-transparent text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">Все типы</option>
              {[...new Set(cars.map(car => car.type))].sort().map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Год</label>
            <select name="year" value={filters.year} onChange={handleFilterChange} className="w-full p-2 border border-gray-600 rounded-lg bg-transparent text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">Все годы</option>
              {[...new Set(cars.map(car => car.year))].sort((a, b) => b - a).map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-300 mb-2">Цена (₽)</label>
          <div className="w-full h-2 bg-gray-600 rounded-full relative">
            <div className="h-2 bg-blue-500 rounded-full absolute" style={{ left: `${(filters.minPrice / 10000000) * 100}%`, width: `${((filters.maxPrice - filters.minPrice) / 10000000) * 100}%` }}></div>
            <input type="range" min="0" max="10000000" value={filters.minPrice} onChange={(e) => handlePriceChange('minPrice', e.target.value)} className="absolute w-full h-2 bg-transparent appearance-none pointer-events-none" />
            <input type="range" min="0" max="10000000" value={filters.maxPrice} onChange={(e) => handlePriceChange('maxPrice', e.target.value)} className="absolute w-full h-2 bg-transparent appearance-none pointer-events-none" />
            <div className="w-4 h-4 bg-blue-500 rounded-full absolute -top-1 transform -translate-x-1/2" style={{ left: `${(filters.minPrice / 10000000) * 100}%` }}></div>
            <div className="w-4 h-4 bg-blue-500 rounded-full absolute -top-1 transform -translate-x-1/2" style={{ left: `${(filters.maxPrice / 10000000) * 100}%` }}></div>
          </div>
          <div className="flex justify-between text-sm text-gray-400 mt-2">
            <span>{filters.minPrice.toLocaleString('ru-RU')}</span>
            <span>{filters.maxPrice.toLocaleString('ru-RU')}</span>
          </div>
        </div>
        <div className="mt-6 flex space-x-4">
          <button onClick={() => filterCars(1)} className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-300 ease-in-out transform hover:scale-105">Фильтровать</button>
          <button onClick={resetFilters} className="bg-gray-600 text-white px-6 py-2 rounded-lg hover:bg-gray-700 transition duration-300 ease-in-out transform hover:scale-105">Сбросить</button>
        </div>
      </div>
      <div id="results" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {paginatedCars.map(car => (
          <div key={car.id} className="bg-white/10 backdrop-blur-md p-4 rounded-xl text-center transition-transform duration-300 hover:scale-105 animate-fade-in-up">
            <h3 className="text-xl font-semibold">{car.brand} {car.model}</h3>
            <p className="text-gray-300">{car.year} | {car.type} | {car.price.toLocaleString('ru-RU')} ₽</p>
            <button onClick={() => showModal(car)} className="mt-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition duration-300">Подробнее</button>
          </div>
        ))}
      </div>
      <div id="pagination" className="flex justify-center space-x-2 mt-8">
        {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
          <button key={page} onClick={() => filterCars(page)} className={`px-3 py-1 rounded-lg ${currentPage === page ? 'bg-blue-600' : 'bg-gray-600'} hover:bg-blue-700 transition duration-300`}>{page}</button>
        ))}
      </div>
      <div id="modal" className="fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center">
        <div className="bg-white p-6 rounded-xl max-w-lg w-full relative animate-fade-in-scale">
          <button onClick={closeModal} className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 text-2xl">&times;</button>
          <h2 id="modal-title" className="text-2xl font-bold mb-4 text-gray-800"></h2>
          <p id="modal-details" className="text-gray-700 whitespace-pre-line mb-4"></p>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Характеристики:</h3>
          <ul id="modal-specs" className="list-disc pl-5 text-gray-600"></ul>
          <button onClick={closeModal} className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition duration-300">Закрыть</button>
        </div>
      </div>
    </div>
  );
};

const filterCars = (page) => {
  setCurrentPage(page);
};

export default App;
# Курсовая работа: Анализ банковских транзакций

## Описание проекта
Веб-приложение для анализа банковских транзакций из Excel-файла. Проект реализует функциональность для просмотра статистики по картам, топ-транзакций, курсов валют и цен акций, а также различные сервисы и отчеты для анализа расходов.

## Структура проекта
course_work_1/
├── src/ # Исходный код
│ ├── init.py
│ ├── utils.py # Вспомогательные функции
│ ├── views.py # Функции для веб-страниц
│ ├── services.py # Сервисы (Инвесткопилка, поиск)
│ ├── reports.py # Отчеты с декоратором
│ └── main.py # Главный модуль для демонстрации
├── data/ # Данные
│ └── operations.xlsx # Файл с транзакциями
├── tests/ # Тесты
│ ├── init.py
│ ├── conftest.py # Фикстуры pytest
│ ├── test_views.py
│ ├── test_services.py
│ └── test_reports.py
├── logs/ # Логи приложения
│ └── app.log
├── reports/ # Сохраненные отчеты
├── .env # Переменные окружения (создается из .env_template)
├── .env_template # Шаблон для переменных окружения
├── .flake8 # Конфигурация flake8
├── .gitignore # Игнорируемые файлы
├── pyproject.toml # Зависимости проекта (Poetry)
├── poetry.lock # Фиксация версий зависимостей
├── user_settings.json # Настройки пользователя
└── README.md # Документация

text

## Реализованный функционал

### 1. Веб-страница "Главная" (`src/views.py`)
- **Приветствие** в зависимости от времени суток
- **Информация по картам**: последние цифры, расходы за месяц, кешбэк (1% от расходов)
- **Топ-5 транзакций** по сумме платежа
- **Курсы валют** (USD, EUR) через внешнее API
- **Цены акций** (AAPL, AMZN, GOOGL, MSFT, TSLA) через внешнее API

### 2. Сервис "Инвесткопилка" (`src/services.py`)
- Рассчитывает сумму, которую можно отложить при округлении каждой траты до заданного лимита (10, 50 или 100 рублей)
- Учитывает только расходы (отрицательные суммы)
- Работает за указанный месяц

### 3. Сервис "Простой поиск" (`src/services.py`)
- Поиск транзакций по строке в описании или категории
- Возвращает JSON со всеми найденными транзакциями

### 4. Отчет "Траты по категории" (`src/reports.py`)
- Выводит все траты по указанной категории за последние 3 месяца
- Использует декоратор для автоматического сохранения отчета в JSON

### 5. Отчет "Траты по дням недели" (`src/reports.py`)
- Рассчитывает средние траты по дням недели за последние 3 месяца
- Сохраняется в файл `weekday_report.json`

## Дополнительные возможности
- **Декоратор для отчетов**: автоматически сохраняет результат любой функции-отчета в JSON-файл
- **Логирование**: все действия записываются в `logs/app.log`
- **Обработка ошибок**: приложение устойчиво к ошибкам API и отсутствию данных
- **Настройки пользователя**: валюты и акции для отображения настраиваются в `user_settings.json`

## Установка и запуск

### Предварительные требования
- Python 3.14 или выше
- Poetry (рекомендуется) или pip

### Установка с Poetry
```bash
# Клонировать репозиторий
git clone https://github.com/yourusername/course_work_1.git
cd course_work_1

# Установить зависимости
poetry install

# Активировать виртуальное окружение
poetry shell
Установка с pip
bash
# Клонировать репозиторий
git clone https://github.com/yourusername/course_work_1.git
cd course_work_1

# Создать виртуальное окружение
python -m venv .venv
# Активировать (Windows)
.venv\Scripts\activate
# Активировать (Linux/Mac)
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
Настройка
Скопируйте .env_template в .env:

bash
cp .env_template .env
Добавьте ваши API ключи в .env:

text
EXCHANGE_RATE_API_KEY=your_api_key_here
STOCK_API_KEY=your_api_key_here
Поместите файл с транзакциями в папку data/operations.xlsx

Запуск
bash
# Запуск главной страницы
python src/main.py

# Запуск тестов
pytest tests/
Примеры использования
Получение данных для главной страницы
python
from src.views import main_page

# Передаем дату в формате 'YYYY-MM-DD HH:MM:SS'
result = main_page("2023-12-20 15:30:00")
print(result)  # JSON с данными
Использование сервиса "Инвесткопилка"
python
from src.services import investment_bank
from src.utils import load_transactions

df = load_transactions()
transactions = df.to_dict('records')
amount = investment_bank("2023-12", transactions, 50)
print(f"Можно отложить: {amount} руб.")
Создание отчета по категории
python
from src.reports import spending_by_category
from src.utils import load_transactions

df = load_transactions()
report = spending_by_category(df, "Супермаркеты")
print(f"Найдено {len(report)} транзакций")
Тестирование
Проект покрыт тестами с использованием pytest:

bash
# Запустить все тесты
pytest tests/ -v

# Запустить с покрытием
pytest tests/ --cov=src --cov-report=term-missing
Форматирование кода
bash
# Запустить black
black src/ tests/

# Запустить flake8
flake8 src/ tests/

# Запустить mypy
mypy src/ tests/
Используемые технологии
Python 3.14+

Pandas - обработка данных

Requests - работа с API

Pytest - тестирование

Poetry - управление зависимостями

Black, Flake8, MyPy - форматирование и проверка кода

Python-dotenv - работа с переменными окружения

API для получения данных
Курсы валют: ExchangeRate-API или Apilayer

Цены акций: Polygon.io или Alpha Vantage

Возможные улучшения
Добавить веб-интерфейс (Flask/FastAPI)

Реализовать кэширование запросов к API

Добавить больше отчетов и сервисов

Создать дашборд с графиками

Добавить поддержку других форматов данных (CSV, JSON)

Автор
Сергей Ивкин
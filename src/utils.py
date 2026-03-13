"""Вспомогательные функции для проекта."""
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv
from pathlib import Path

# Определение кодировки для Windows
ENCODING = 'cp1251' if sys.platform == 'win32' else 'utf-8'

# Создание директорий
BASE_DIR = Path(__file__).parent.parent.absolute()  # Корень проекта
LOG_DIR = BASE_DIR / 'logs'
REPORTS_DIR = BASE_DIR / 'reports'
DATA_DIR = BASE_DIR / 'data'

# Создаем все необходимые директории
for directory in [LOG_DIR, REPORTS_DIR, DATA_DIR]:
    directory.mkdir(exist_ok=True)
    print(f"Создана директория: {directory}")

# Настройка логирования с правильной кодировкой для Windows
log_file = LOG_DIR / 'app.log'

# Удаляем старый файл лога если он в неправильной кодировке
if log_file.exists():
    try:
        # Пробуем прочитать файл в UTF-8
        with open(log_file, 'r', encoding='utf-8') as f:
            f.read()
    except UnicodeDecodeError:
        # Если не получается, пересоздаем файл
        log_file.unlink()
        print(f"Пересоздан файл лога: {log_file}")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=str(log_file),
    encoding=ENCODING,  # Используем правильную кодировку
    filemode='w'  # Перезаписываем файл при каждом запуске
)

# Добавляем обработчик для вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.addHandler(console_handler)

load_dotenv()



def load_transactions(file_path: str = "data/operations.xlsx") -> pd.DataFrame:
    """Загружает транзакции из Excel-файла."""
    try:
        # Проверяем существование файла
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            return pd.DataFrame()

        df = pd.read_excel(file_path)
        logger.info(f"Загружено {len(df)} транзакций из {file_path}")
        return df
    except Exception as e:
        logger.error(f"Ошибка загрузки файла {file_path}: {e}")
        return pd.DataFrame()


def get_greeting() -> str:
    """Возвращает приветствие в зависимости от текущего времени."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_currency_rates(currencies: List[str]) -> List[Dict[str, float]]:
    """Получает курсы валют через API."""
    rates = []
    api_key = os.getenv("EXCHANGE_RATE_API_KEY", "jyPdk75EAw9JlCJWAdcSsfSTNHsa3TVD")

    # Базовая валюта - RUB
    base_currency = "RUB"

    for currency in currencies:
        try:
            # ИСПРАВЛЕНО: используем правильные параметры для API
            url = f"https://api.apilayer.com/exchangerates_data/latest?symbols={currency}&base={base_currency}"
            headers = {"apikey": api_key}

            logger.info(f"Запрос курса для {currency}: {url}")
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'rates' in data and currency in data['rates']:
                    rate = data['rates'][currency]  # Курс RUB к целевой валюте
                    rates.append({"currency": currency, "rate": round(rate, 4)})
                    logger.info(f"Курс {currency}: {rate}")
                else:
                    logger.warning(f"Валюта {currency} не найдена в ответе API")
                    rates.append({"currency": currency, "rate": 0.0})
            else:
                logger.error(f"Ошибка API для {currency}: {response.status_code} - {response.text}")
                rates.append({"currency": currency, "rate": 0.0})

        except requests.exceptions.Timeout:
            logger.error(f"Таймаут при запросе курса {currency}")
            rates.append({"currency": currency, "rate": 0.0})
        except requests.exceptions.ConnectionError:
            logger.error(f"Ошибка соединения при запросе курса {currency}")
            rates.append({"currency": currency, "rate": 0.0})
        except Exception as e:
            logger.error(f"Ошибка получения курса {currency}: {e}")
            rates.append({"currency": currency, "rate": 0.0})

    return rates


def get_stock_prices(stocks: List[str]) -> List[Dict[str, float]]:
    """Получает цены акций через API."""
    prices = []
    api_key = os.getenv("STOCK_API_KEY")

    if not api_key:
        logger.warning("STOCK_API_KEY не найден в переменных окружения")
        # Возвращаем тестовые данные
        for stock in stocks:
            prices.append({"stock": stock, "price": 100.0})  # Тестовое значение
        return prices

    for stock in stocks:
        try:
            # API для получения цен акций
            response = requests.get(
                f"https://api.polygon.io/v2/aggs/ticker/{stock}/prev?apiKey={api_key}",
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if 'results' in data and len(data['results']) > 0:
                    price = data['results'][0].get('c', 0)  # Цена закрытия
                    prices.append({"stock": stock, "price": round(price, 2)})
                    logger.info(f"Цена {stock}: {price}")
                else:
                    prices.append({"stock": stock, "price": 0.0})
            else:
                logger.error(f"Ошибка API для {stock}: {response.status_code}")
                prices.append({"stock": stock, "price": 0.0})

        except Exception as e:
            logger.error(f"Ошибка получения цены {stock}: {e}")
            prices.append({"stock": stock, "price": 0.0})

    return prices


def filter_transactions_by_date(
    df: pd.DataFrame,
    end_date: datetime,
    period: str = 'M'
) -> pd.DataFrame:
    """
    Фильтрует транзакции по дате.

    Args:
        df: DataFrame с транзакциями
        end_date: конечная дата периода
        period: 'M' - месяц, 'W' - неделя, 'Y' - год, 'ALL' - все

    Returns:
        Отфильтрованный DataFrame
    """
    if df.empty:
        return df

    if 'Дата операции' not in df.columns:
        logger.warning("Колонка 'Дата операции' не найдена")
        return df

    # Преобразуем даты
    df['Дата операции'] = pd.to_datetime(df['Дата операции'], format='%d.%m.%Y', errors='coerce')

    # Удаляем строки с некорректными датами
    df = df.dropna(subset=['Дата операции'])

    if period == 'ALL':
        return df[df['Дата операции'] <= end_date]

    # Определяем начальную дату периода
    if period == 'M':
        start_date = end_date.replace(day=1)
    elif period == 'W':
        # Начало недели (понедельник)
        start_date = end_date - pd.Timedelta(days=end_date.weekday())
    elif period == 'Y':
        start_date = end_date.replace(month=1, day=1)
    else:
        logger.warning(f"Неизвестный период '{period}', используем месяц")
        start_date = end_date.replace(day=1)

    logger.info(f"Фильтрация транзакций с {start_date.date()} по {end_date.date()}")
    return df[(df['Дата операции'] >= start_date) & (df['Дата операции'] <= end_date)]


# Тестовый запуск
if __name__ == "__main__":
    # Проверка функций
    print(f"Приветствие: {get_greeting()}")

    # Проверка загрузки транзакций
    df = load_transactions()
    if not df.empty:
        print(f"Загружено {len(df)} транзакций")
        print(f"Колонки: {df.columns.tolist()}")

    # Проверка курсов валют
    rates = get_currency_rates(['USD', 'EUR'])
    print(f"Курсы валют: {rates}")

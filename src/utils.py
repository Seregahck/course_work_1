"""Вспомогательные функции для проекта."""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Union, cast

import pandas as pd
import requests
from dotenv import load_dotenv
from pathlib import Path

# Определение кодировки для Windows
ENCODING = "cp1251" if sys.platform == "win32" else "utf-8"

# Создание директорий
BASE_DIR = Path(__file__).parent.parent.absolute()  # Корень проекта
LOG_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"

# Создаем все необходимые директории
for directory in [LOG_DIR, REPORTS_DIR, DATA_DIR]:
    directory.mkdir(exist_ok=True)
    print(f"Создана директория: {directory}")

# Настройка логирования с правильной кодировкой для Windows
log_file = LOG_DIR / "app.log"

# Удаляем старый файл лога если он в неправильной кодировке
if log_file.exists():
    try:
        # Пробуем прочитать файл в UTF-8
        with open(log_file, "r", encoding="utf-8") as f:
            f.read()
    except UnicodeDecodeError:
        # Если не получается, пересоздаем файл
        log_file.unlink()
        print(f"Пересоздан файл лога: {log_file}")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename=str(log_file),
    encoding=ENCODING,  # Используем правильную кодировку
    filemode="w",  # Перезаписываем файл при каждом запуске
)

# Добавляем обработчик для вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

logger = logging.getLogger(__name__)
logger.addHandler(console_handler)

load_dotenv()


def load_transactions(file_path: str = "data/operations.xlsx") -> pd.DataFrame:
    """Загружает транзакции из Excel-файла."""
    try:
        # Используем абсолютный путь
        if not os.path.isabs(file_path):
            if file_path.startswith("data/"):
                file_path = str(DATA_DIR / file_path[5:])
            else:
                file_path = str(DATA_DIR / file_path)

        # Проверяем существование файла
        if not os.path.exists(file_path):
            logger.error(f"Файл не найден: {file_path}")
            # Пробуем найти файл в корне data
            alternative_path = DATA_DIR / "operations.xlsx"
            if alternative_path.exists():
                file_path = str(alternative_path)
                logger.info(f"Найден альтернативный путь: {file_path}")
            else:
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


def get_currency_rates(currencies: List[str]) -> List[Dict[str, Union[str, float]]]:
    """
    Получает курсы валют через API.

    Args:
        currencies: Список валют (например, ['USD', 'EUR'])

    Returns:
        Список словарей с ключами 'currency' (str) и 'rate' (float)
    """
    rates: List[Dict[str, Union[str, float]]] = []
    # Убираем запасной ключ из кода - он должен быть только в .env файле
    api_key = os.getenv("EXCHANGE_RATE_API_KEY")

    if not api_key:
        logger.warning("EXCHANGE_RATE_API_KEY не найден в переменных окружения")
        # Возвращаем тестовые данные
        for currency in currencies:
            # Примерные курсы для тестирования
            mock_rates = {"USD": 0.012, "EUR": 0.011, "GBP": 0.0095}
            rate = mock_rates.get(currency, 1.0)
            rates.append({"currency": currency, "rate": rate})
        return rates

    # Базовая валюта - RUB
    base_currency = "RUB"

    for currency in currencies:
        try:
            # Используем правильные параметры для API
            url = f"https://api.apilayer.com/exchangerates_data/latest"
            headers = {"apikey": api_key}
            params = {"symbols": currency, "base": base_currency}

            logger.info(f"Запрос курса для {currency}")
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                if "rates" in data and currency in data["rates"]:
                    rate = float(data["rates"][currency])  # Курс RUB к целевой валюте
                    rates.append({"currency": currency, "rate": round(rate, 4)})
                    logger.info(f"Курс {currency}: {rate}")
                else:
                    logger.warning(f"Валюта {currency} не найдена в ответе API")
                    rates.append({"currency": currency, "rate": 0.0})
            else:
                logger.error(f"Ошибка API для {currency}: {response.status_code}")
                if response.status_code == 429:  # Too Many Requests
                    logger.warning("Превышен лимит запросов, добавляем задержку")
                    time.sleep(5)
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

        # Добавляем небольшую задержку между запросами
        time.sleep(1)

    return rates


def get_stock_prices(stocks: List[str]) -> List[Dict[str, Union[str, float]]]:
    """
    Получает цены акций через API Finnhub.

    Args:
        stocks: Список тикеров акций (например, ['AAPL', 'GOOGL'])

    Returns:
        Список словарей с ключами 'stock' (str) и 'price' (float)
    """
    prices: List[Dict[str, Union[str, float]]] = []
    api_key = os.getenv("FINNHUB_API_KEY")

    if not api_key:
        logger.warning("FINNHUB_API_KEY не найден в переменных окружения")
        # Возвращаем тестовые данные
        for stock in stocks:
            # Примерные цены для популярных акций
            mock_prices = {"AAPL": 175.50, "GOOGL": 140.25, "MSFT": 380.75, "AMZN": 145.30}
            price = mock_prices.get(stock, 100.0)
            prices.append({"stock": stock, "price": price})
        return prices

    for stock in stocks:
        try:
            # Добавляем параметры запроса: тикер и API ключ
            response = requests.get(
                f"https://finnhub.io/api/v1/quote", params={"symbol": stock, "token": api_key}, timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                # Finnhub возвращает объект с полями c, h, l, o, pc
                # c - текущая цена, pc - цена закрытия предыдущего дня
                if data and "c" in data and data["c"] is not None:
                    price = float(data["c"])  # Текущая цена
                    prices.append({"stock": stock, "price": round(price, 2)})
                    logger.info(f"Цена {stock}: {price}")
                else:
                    logger.warning(f"Нет данных о цене для {stock}")
                    prices.append({"stock": stock, "price": 0.0})

                # Добавляем задержку между запросами (30 запросов в минуту для бесплатного тарифа)
                time.sleep(2)  # 2 секунды между запросами

            else:
                logger.error(f"Ошибка API для {stock}: {response.status_code}")
                if response.status_code == 429:  # Too Many Requests
                    logger.warning("Превышен лимит запросов к Finnhub")
                    time.sleep(5)
                prices.append({"stock": stock, "price": 0.0})

        except requests.exceptions.Timeout:
            logger.error(f"Таймаут при запросе {stock}")
            prices.append({"stock": stock, "price": 0.0})
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при запросе {stock}: {e}")
            prices.append({"stock": stock, "price": 0.0})
        except Exception as e:
            logger.error(f"Неожиданная ошибка получения цены {stock}: {e}")
            prices.append({"stock": stock, "price": 0.0})

    return prices


def filter_transactions_by_date(df: pd.DataFrame, end_date: datetime, period: str = "M") -> pd.DataFrame:
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
        return pd.DataFrame()

    if "Дата операции" not in df.columns:
        logger.warning("Колонка 'Дата операции' не найдена")
        return pd.DataFrame()

    # Создаем копию DataFrame чтобы избежать SettingWithCopyWarning
    df_copy = df.copy()

    # Преобразуем даты
    df_copy["Дата_операции_dt"] = pd.to_datetime(df_copy["Дата операции"], format="%d.%m.%Y", errors="coerce")

    # Удаляем строки с некорректными датами
    df_clean = df_copy.dropna(subset=["Дата_операции_dt"]).copy()

    if df_clean.empty:
        return pd.DataFrame()

    if period == "ALL":
        # Используем .loc для явной индексации
        mask = df_clean["Дата_операции_dt"] <= end_date
        result_df = df_clean.loc[mask].copy()
        # Явное приведение типа для mypy
        return cast(pd.DataFrame, result_df)

    # Определяем начальную дату периода
    if period == "M":
        start_date = end_date.replace(day=1)
    elif period == "W":
        # Начало недели (понедельник)
        start_date = end_date - pd.Timedelta(days=end_date.weekday())
    elif period == "Y":
        start_date = end_date.replace(month=1, day=1)
    else:
        logger.warning(f"Неизвестный период '{period}', используем месяц")
        start_date = end_date.replace(day=1)

    logger.info(f"Фильтрация транзакций с {start_date.date()} по {end_date.date()}")

    # Фильтруем и возвращаем результат используя .loc
    date_mask = (df_clean["Дата_операции_dt"] >= start_date) & (df_clean["Дата_операции_dt"] <= end_date)
    filtered_df = df_clean.loc[date_mask].copy()

    # Явное приведение типа для mypy
    return cast(pd.DataFrame, filtered_df)


# Если нужно сохранить оригинальный формат даты в отдельной колонке
def add_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Добавляет дополнительные колонки с датами для удобства анализа.

    Args:
        df: DataFrame с колонкой 'Дата операции'

    Returns:
        DataFrame с дополнительными колонками
    """
    if df.empty or "Дата операции" not in df.columns:
        return df

    df_copy = df.copy()

    # Создаем колонку с datetime
    df_copy["Дата_операции_dt"] = pd.to_datetime(df_copy["Дата операции"], format="%d.%m.%Y", errors="coerce")

    # Добавляем колонки с компонентами даты с явной типизацией
    df_copy["Год"] = df_copy["Дата_операции_dt"].dt.year.astype("Int64")
    df_copy["Месяц"] = df_copy["Дата_операции_dt"].dt.month.astype("Int64")
    df_copy["День"] = df_copy["Дата_операции_dt"].dt.day.astype("Int64")
    df_copy["День_недели"] = df_copy["Дата_операции_dt"].dt.dayofweek.astype("Int64")

    return df_copy


# Функция для конвертации в JSON с правильной обработкой дат
def df_to_json(df: pd.DataFrame) -> str:
    """
    Конвертирует DataFrame в JSON строку с правильной обработкой дат.

    Args:
        df: DataFrame для конвертации

    Returns:
        JSON строка
    """
    # Создаем копию для конвертации
    df_copy = df.copy()

    # Конвертируем даты в строки - с явной аннотацией типа
    datetime_columns: pd.Index = df_copy.select_dtypes(include=["datetime64"]).columns
    for col in datetime_columns:
        df_copy[col] = df_copy[col].dt.strftime("%d.%m.%Y")

    # Заменяем NaN на None (который станет null в JSON)
    df_copy = df_copy.where(pd.notnull(df_copy), None)

    return json.dumps(df_copy.to_dict("records"), ensure_ascii=False, indent=2)


# Тестовый запуск
if __name__ == "__main__":
    print("=" * 50)
    print(f"Текущая директория: {BASE_DIR}")
    print(f"Директория для логов: {LOG_DIR}")
    print(f"Директория для отчетов: {REPORTS_DIR}")
    print(f"Директория для данных: {DATA_DIR}")
    print(f"Кодировка для логов: {ENCODING}")
    print("=" * 50)

    # Проверка приветствия
    print(f"Приветствие: {get_greeting()}")

    # Проверка загрузки транзакций
    df = load_transactions()
    if not df.empty:
        print(f"Загружено {len(df)} транзакций")
        print(f"Колонки: {df.columns.tolist()}")
        if "Дата операции" in df.columns:
            print(f"Первые 3 даты: {df['Дата операции'].head(3).tolist()}")

    # Проверка фильтрации
    filtered_df = filter_transactions_by_date(df, datetime.now(), "M")
    print(f"Транзакций за текущий месяц: {len(filtered_df)}")

    # Проверка курсов валют
    rates = get_currency_rates(["USD", "EUR"])
    print(f"Курсы валют: {rates}")

    # Проверка цен акций
    prices = get_stock_prices(["AAPL", "GOOGL"])
    print(f"Цены акций: {prices}")

    print("=" * 50)
    print(f"Логи сохраняются в: {log_file}")
    print("=" * 50)

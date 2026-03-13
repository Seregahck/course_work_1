"""Вспомогательные функции для проекта."""
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/app.log'
)
logger = logging.getLogger(__name__)

load_dotenv()


def load_transactions(file_path: str = "data/operations.xlsx") -> pd.DataFrame:
    """Загружает транзакции из Excel-файла."""
    try:
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
    api_key = os.getenv("EXCHANGE_RATE_API_KEY")

    for currency in currencies:
        try:
            # Пример использования API (замените на реальный)
            response = requests.get(
                f"https://api.exchangerate-api.com/v4/latest/RUB?symbols={currency}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                rate = data['rates'].get(currency, 0)
                rates.append({"currency": currency, "rate": round(rate, 2)})
            else:
                rates.append({"currency": currency, "rate": 0})
        except Exception as e:
            logger.error(f"Ошибка получения курса {currency}: {e}")
            rates.append({"currency": currency, "rate": 0})

    return rates


def get_stock_prices(stocks: List[str]) -> List[Dict[str, float]]:
    """Получает цены акций через API."""
    prices = []
    api_key = os.getenv("STOCK_API_KEY")

    for stock in stocks:
        try:
            # Пример использования API (замените на реальный)
            response = requests.get(
                f"https://api.apilayer.com/exchangerates_data/convert?to={to}&from={from}&amount={amount}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                price = data['results'][0]['c']  # Цена закрытия
                prices.append({"stock": stock, "price": round(price, 2)})
            else:
                prices.append({"stock": stock, "price": 0})
        except Exception as e:
            logger.error(f"Ошибка получения цены {stock}: {e}")
            prices.append({"stock": stock, "price": 0})

    return prices


def filter_transactions_by_date(
        df: pd.DataFrame,
        end_date: datetime,
        period: str = 'M'
) -> pd.DataFrame:
    """
    Фильтрует транзакции по дате.
    period: 'M' - месяц, 'W' - неделя, 'Y' - год, 'ALL' - все
    """
    if 'Дата операции' not in df.columns:
        return df

    df['Дата операции'] = pd.to_datetime(df['Дата операции'], dayfirst=True)

    if period == 'ALL':
        return df[df['Дата операции'] <= end_date]

    if period == 'M':
        start_date = end_date.replace(day=1)
    elif period == 'W':
        start_date = end_date - pd.Timedelta(days=end_date.weekday())
    elif period == 'Y':
        start_date = end_date.replace(month=1, day=1)
    else:
        start_date = end_date.replace(day=1)

    return df[(df['Дата операции'] >= start_date) & (df['Дата операции'] <= end_date)]

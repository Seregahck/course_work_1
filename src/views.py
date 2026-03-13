"""Модуль для генерации JSON-ответов для веб-страниц."""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from src.utils import (
    filter_transactions_by_date,
    get_currency_rates,
    get_greeting,
    get_stock_prices,
    load_transactions,
)

logger = logging.getLogger(__name__)


def load_user_settings() -> Dict:
    """Загружает настройки пользователя из JSON-файла."""
    try:
        with open('user_settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Файл user_settings.json не найден. Используются настройки по умолчанию.")
        return {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
        }


def get_cards_info(df: pd.DataFrame) -> List[Dict]:
    """
    Получает информацию по картам: последние цифры, расходы, кешбэк.
    """
    if 'Номер карты' not in df.columns or 'Сумма операции' not in df.columns:
        return []

    cards = []
    for card in df['Номер карты'].dropna().unique():
        card_transactions = df[df['Номер карты'] == card]
        total_spent = abs(card_transactions[card_transactions['Сумма операции'] < 0]['Сумма операции'].sum())
        cashback = round(total_spent / 100, 2)  # 1 рубль на каждые 100 рублей

        cards.append({
            "last_digits": str(int(card))[-4:],
            "total_spent": round(total_spent, 2),
            "cashback": cashback
        })

    return cards


def get_top_transactions(df: pd.DataFrame, n: int = 5) -> List[Dict]:
    """
    Получает топ-N транзакций по сумме платежа.
    """
    if 'Сумма платежа' not in df.columns:
        return []

    top_transactions = df.nlargest(n, 'Сумма платежа')[
        ['Дата операции', 'Сумма платежа', 'Категория', 'Описание']
    ]

    result = []
    for _, row in top_transactions.iterrows():
        result.append({
            "date": pd.to_datetime(row['Дата операции']).strftime('%d.%m.%Y'),
            "amount": round(row['Сумма платежа'], 2),
            "category": row['Категория'] if pd.notna(row['Категория']) else "",
            "description": row['Описание'] if pd.notna(row['Описание']) else ""
        })

    return result


def main_page(date_str: str) -> str:
    """
    Главная функция для страницы "Главная".
    Принимает дату в формате 'YYYY-MM-DD HH:MM:SS'.
    Возвращает JSON-ответ.
    """
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        logger.error(f"Неверный формат даты: {date_str}")
        return json.dumps({"error": "Неверный формат даты"}, ensure_ascii=False)

    # Загружаем данные
    df = load_transactions()
    settings = load_user_settings()

    # Фильтруем транзакции по дате (с начала месяца)
    df_filtered = filter_transactions_by_date(df, date, 'M')

    # Формируем ответ
    response = {
        "greeting": get_greeting(),
        "cards": get_cards_info(df_filtered),
        "top_transactions": get_top_transactions(df_filtered, 5),
        "currency_rates": get_currency_rates(settings['user_currencies']),
        "stock_prices": get_stock_prices(settings['user_stocks'])
    }

    logger.info(f"Сформирован ответ для главной страницы на дату {date_str}")
    return json.dumps(response, ensure_ascii=False, indent=2)

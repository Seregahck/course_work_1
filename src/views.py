"""Модуль для генерации JSON-ответов для веб-страниц."""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from src.utils import (
    filter_transactions_by_date,
    get_currency_rates,
    get_greeting,
    get_stock_prices,
    load_transactions,
)

logger = logging.getLogger(__name__)


def load_user_settings() -> Dict[str, Any]:
    """Загружает настройки пользователя из JSON-файла."""
    try:
        with open('user_settings.json', 'r', encoding='utf-8') as f:
            settings: Dict[str, Any] = json.load(f)
            return settings
    except FileNotFoundError:
        logger.warning("Файл user_settings.json не найден. Используются настройки по умолчанию.")
        return {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
        }
    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON в файле user_settings.json")
        return {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
        }


def get_cards_info(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Получает информацию по картам: последние цифры, расходы, кешбэк.
    """
    if 'Номер карты' not in df.columns or 'Сумма операции' not in df.columns:
        logger.warning("Колонки 'Номер карты' или 'Сумма операции' не найдены")
        # Проверим, какие колонки есть в DataFrame
        logger.info(f"Доступные колонки: {list(df.columns)}")
        return []

    # Проверим, есть ли вообще данные по картам
    if df['Номер карты'].isna().all():
        logger.warning("Нет данных по номерам карт")
        return []

    cards: List[Dict[str, Any]] = []
    for card in df['Номер карты'].dropna().unique():
        card_transactions = df[df['Номер карты'] == card]
        # Берем только расходы (отрицательные суммы)
        expenses = card_transactions[card_transactions['Сумма операции'] < 0]
        total_spent = abs(expenses['Сумма операции'].sum()) if not expenses.empty else 0
        cashback = round(total_spent / 100, 2)  # 1 рубль на каждые 100 рублей

        # Преобразуем номер карты в строку и берем последние 4 цифры
        card_str = str(int(card)) if pd.notna(card) else ""
        last_digits = card_str[-4:] if len(card_str) >= 4 else card_str

        cards.append({
            "last_digits": last_digits,
            "total_spent": round(total_spent, 2),
            "cashback": cashback
        })
        logger.info(f"Карта {last_digits}: расходы {total_spent}, кешбэк {cashback}")

    return cards


def get_top_transactions(df: pd.DataFrame, n: int = 5) -> List[Dict[str, Any]]:
    """
    Получает топ-N транзакций по сумме платежа.
    """
    if 'Сумма платежа' not in df.columns:
        logger.warning("Колонка 'Сумма платежа' не найдена")
        logger.info(f"Доступные колонки: {list(df.columns)}")
        return []

    # Проверим, есть ли данные
    if df.empty:
        logger.warning("DataFrame пуст")
        return []

    # Проверим, есть ли положительные суммы (расходы обычно отрицательные)
    expenses_df = df[df['Сумма платежа'] > 0].copy()
    if expenses_df.empty:
        logger.warning("Нет транзакций с положительной суммой платежа")
        # Попробуем использовать абсолютные значения
        df_copy = df.copy()
        df_copy['Сумма платежа'] = abs(df_copy['Сумма платежа'])
        top_transactions = df_copy.nlargest(n, 'Сумма платежа')
    else:
        top_transactions = expenses_df.nlargest(n, 'Сумма платежа')

    result: List[Dict[str, Any]] = []
    for _, row in top_transactions.iterrows():
        # Преобразуем дату
        date_str = row['Дата операции']
        if pd.notna(date_str):
            try:
                date_formatted = pd.to_datetime(date_str).strftime('%d.%m.%Y')
            except:
                date_formatted = str(date_str)
        else:
            date_formatted = ""

        result.append({
            "date": date_formatted,
            "amount": round(abs(row['Сумма платежа']), 2),
            "category": str(row['Категория']) if pd.notna(row['Категория']) else "",
            "description": str(row['Описание']) if pd.notna(row['Описание']) else ""
        })

    logger.info(f"Найдено {len(result)} топ-транзакций")
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
    response: Dict[str, Any] = {
        "greeting": get_greeting(),
        "cards": get_cards_info(df_filtered),
        "top_transactions": get_top_transactions(df_filtered, 5),
        "currency_rates": get_currency_rates(settings['user_currencies']),
        "stock_prices": get_stock_prices(settings['user_stocks'])
    }

    logger.info(f"Сформирован ответ для главной страницы на дату {date_str}")
    return json.dumps(response, ensure_ascii=False, indent=2)

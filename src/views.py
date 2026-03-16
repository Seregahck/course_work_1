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
        with open("user_settings.json", "r", encoding="utf-8") as f:
            settings: Dict[str, Any] = json.load(f)
            return settings
    except FileNotFoundError:
        logger.warning("Файл user_settings.json не найден. Используются настройки по умолчанию.")
        return {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]}
    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON в файле user_settings.json")
        return {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]}


def get_cards_info(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Получает информацию по картам: последние цифры, расходы, кешбэк.
    """
    if "Номер карты" not in df.columns or "Сумма операции" not in df.columns:
        logger.warning("Колонки 'Номер карты' или 'Сумма операции' не найдены")
        logger.info("Доступные колонки: %s", list(df.columns))
        return []

    if df["Номер карты"].isna().all():
        logger.warning("Нет данных по номерам карт")
        return []

    cards: List[Dict[str, Any]] = []
    unique_cards = df["Номер карты"].dropna().unique()

    for card in unique_cards:
        # Исправлено: используем pd.DataFrame для явного преобразования
        card_transactions = pd.DataFrame(df[df["Номер карты"] == card])

        # Исправлено: используем pd.DataFrame для явного преобразования
        expenses = pd.DataFrame(card_transactions[card_transactions["Сумма операции"] < 0])

        # Рассчитываем сумму
        if not expenses.empty:
            total_spent = float(abs(expenses["Сумма операции"].sum()))
        else:
            total_spent = 0.0

        cashback = round(total_spent / 100, 2)

        # Получаем последние цифры карты
        try:
            if pd.notna(card):
                card_int = int(float(card))
                card_str = str(card_int)
                last_digits = card_str[-4:] if len(card_str) >= 4 else card_str
            else:
                last_digits = ""
        except (ValueError, TypeError):
            last_digits = ""

        cards.append({
            "last_digits": last_digits,
            "total_spent": round(total_spent, 2),
            "cashback": cashback
        })

        logger.info("Карта %s: расходы %.2f, кешбэк %.2f", last_digits, total_spent, cashback)

    return cards


def get_top_transactions(df: pd.DataFrame, n: int = 5) -> List[Dict[str, Any]]:
    """
    Получает топ-N транзакций по сумме платежа.
    """
    if "Сумма платежа" not in df.columns:
        logger.warning("Колонка 'Сумма платежа' не найдена")
        logger.info("Доступные колонки: %s", list(df.columns))
        return []

    if df.empty:
        logger.warning("DataFrame пуст")
        return []

    # Исправлено: используем pd.DataFrame для явного преобразования
    expenses_df = pd.DataFrame(df[df["Сумма платежа"] > 0])

    if expenses_df.empty:
        logger.warning("Нет транзакций с положительной суммой платежа")
        df_copy = df.copy()
        df_copy["Сумма платежа"] = abs(df_copy["Сумма платежа"])
        # Исправлено: используем pd.DataFrame для явного преобразования
        top_transactions = pd.DataFrame(df_copy.nlargest(n, "Сумма платежа"))
    else:
        # Исправлено: используем pd.DataFrame для явного преобразования
        top_transactions = pd.DataFrame(expenses_df.nlargest(n, "Сумма платежа"))

    result: List[Dict[str, Any]] = []
    for _, row in top_transactions.iterrows():
        date_str = row["Дата операции"]
        if pd.notna(date_str):
            try:
                date_formatted = pd.to_datetime(date_str).strftime("%d.%m.%Y")
            except Exception:
                date_formatted = str(date_str)
        else:
            date_formatted = ""

        amount = float(abs(row["Сумма платежа"]))
        category = str(row["Категория"]) if pd.notna(row["Категория"]) else ""
        description = str(row["Описание"]) if pd.notna(row["Описание"]) else ""

        result.append({
            "date": date_formatted,
            "amount": round(amount, 2),
            "category": category,
            "description": description,
        })

    logger.info("Найдено %d топ-транзакций", len(result))
    return result


def main_page(date_str: str) -> str:
    """
    Главная функция для страницы "Главная".
    Принимает дату в формате 'YYYY-MM-DD HH:MM:SS'.
    Возвращает JSON-ответ.
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.error("Неверный формат даты: %s", date_str)
        return json.dumps({"error": "Неверный формат даты"}, ensure_ascii=False)

    df = load_transactions()
    settings = load_user_settings()
    df_filtered = filter_transactions_by_date(df, date, "M")

    response: Dict[str, Any] = {
        "greeting": get_greeting(),
        "cards": get_cards_info(df_filtered),
        "top_transactions": get_top_transactions(df_filtered, 5),
        "currency_rates": get_currency_rates(settings["user_currencies"]),
        "stock_prices": get_stock_prices(settings["user_stocks"]),
    }

    logger.info("Сформирован ответ для главной страницы на дату %s", date_str)
    return json.dumps(response, ensure_ascii=False, indent=2)

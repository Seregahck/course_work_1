"""Главный модуль для демонстрации всех функциональностей."""
import json
import logging
from datetime import datetime

import pandas as pd

from src.reports import spending_by_category, spending_by_weekday
from src.services import investment_bank, simple_search
from src.utils import load_transactions
from src.views import main_page

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Демонстрация всех реализованных функциональностей."""
    print("=" * 60)
    print("КУРСОВАЯ РАБОТА: АНАЛИЗ ТРАНЗАКЦИЙ")
    print("=" * 60)

    # 1. Веб-страница "Главная"
    print("\n1. ВЕБ-СТРАНИЦА 'ГЛАВНАЯ'")
    print("-" * 40)
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    result = main_page(current_date)
    print("JSON-ответ для главной страницы:")
    print(result[:500] + "..." if len(result) > 500 else result)

    # Загружаем транзакции
    df = load_transactions()
    transactions = df.to_dict('records') if not df.empty else []

    # 2. Сервис "Инвесткопилка"
    print("\n2. СЕРВИС 'ИНВЕСТКОПИЛКА'")
    print("-" * 40)
    if transactions:
        current_month = datetime.now().strftime('%Y-%m')
        investment = investment_bank(current_month, transactions, 50)
        print(f"Сумма в инвесткопилке за {current_month} при округлении до 50₽: {investment}₽")

    # 3. Сервис "Простой поиск"
    print("\n3. СЕРВИС 'ПРОСТОЙ ПОИСК'")
    print("-" * 40)
    if transactions:
        search_result = simple_search("перевод", transactions)
        print(f"Поиск 'перевод': найдено {len(json.loads(search_result))} транзакций")

    # 4. Отчет "Траты по категории"
    print("\n4. ОТЧЕТ 'ТРАТЫ ПО КАТЕГОРИИ'")
    print("-" * 40)
    if not df.empty:
        category_report = spending_by_category(df, "Супермаркеты")
        print(f"Траты в категории 'Супермаркеты' за 3 месяца: {len(category_report)} транзакций")
        if not category_report.empty:
            total = abs(category_report['Сумма операции'].sum())
            print(f"Общая сумма: {total:.2f}₽")

    # 5. Отчет "Траты по дням недели"
    print("\n5. ОТЧЕТ 'ТРАТЫ ПО ДНЯМ НЕДЕЛИ'")
    print("-" * 40)
    if not df.empty:
        weekday_report = spending_by_weekday(df)
        print("Средние траты по дням недели:")
        for day, amount in weekday_report.items():
            print(f"  {day.capitalize()}: {amount}₽")

    print("\n" + "=" * 60)
    print("Все отчеты сохранены в папке 'reports/'")
    print("Логи записаны в 'logs/app.log'")
    print("=" * 60)


if __name__ == "__main__":
    main()

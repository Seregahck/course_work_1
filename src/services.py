"""Модуль для реализации сервисов."""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """
    Сервис "Инвесткопилка".
    Рассчитывает сумму, которую можно отложить при округлении трат до limit.

    Args:
        month: Месяц в формате 'YYYY-MM'
        transactions: Список транзакций
        limit: Лимит округления (10, 50 или 100)

    Returns:
        float: Сумма, которую удалось бы отложить
    """
    try:
        target_date = datetime.strptime(month, '%Y-%m')
        total_investment = 0.0

        for transaction in transactions:
            # Проверяем, относится ли транзакция к нужному месяцу
            trans_date = datetime.strptime(transaction['Дата операции'], '%Y-%m-%d')
            if trans_date.year == target_date.year and trans_date.month == target_date.month:
                amount = transaction['Сумма операции']

                # Берем только расходы (отрицательные суммы)
                if amount < 0:
                    abs_amount = abs(amount)
                    # Округляем вверх до ближайшего limit
                    rounded_amount = ((abs_amount + limit - 1) // limit) * limit
                    investment = rounded_amount - abs_amount
                    total_investment += investment

        logger.info(f"Инвесткопилка за {month}: {total_investment} руб.")
        return round(total_investment, 2)

    except Exception as e:
        logger.error(f"Ошибка в расчете инвесткопилки: {e}")
        return 0.0


def simple_search(search_string: str, transactions: List[Dict[str, Any]]) -> str:
    """
    Сервис "Простой поиск".
    Ищет транзакции по строке в описании или категории.

    Args:
        search_string: Строка для поиска
        transactions: Список транзакций

    Returns:
        str: JSON с найденными транзакциями
    """
    results = []
    search_lower = search_string.lower()

    for transaction in transactions:
        description = str(transaction.get('Описание', '')).lower()
        category = str(transaction.get('Категория', '')).lower()

        if search_lower in description or search_lower in category:
            results.append(transaction)

    logger.info(f"Простой поиск '{search_string}': найдено {len(results)} транзакций")
    return json.dumps(results, ensure_ascii=False, indent=2, default=str)

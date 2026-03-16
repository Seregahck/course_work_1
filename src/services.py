"""Модуль для реализации сервисов."""

import json
import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def investment_bank(
    period: Union[str, datetime], transactions: List[Dict[str, Any]], limit: int, end_date: Optional[datetime] = None
) -> float:
    """
    Сервис "Инвесткопилка".
    Рассчитывает сумму, которую можно отложить при округлении трат до limit за указанный период.

    Args:
        period: Период для расчета:
                - 'MM-YYYY' или 'YYYY-MM' (конкретный месяц)
                - 'W' (последняя неделя)
                - 'M' (последний месяц)
                - '3M' (последние 3 месяца)
                - '6M' (последние 6 месяцев)
                - 'Y' (последний год)
                - 'ALL' (за все время)
                - datetime объект (конкретная дата, будет взят месяц этой даты)
        transactions: Список транзакций
        limit: Лимит округления (10, 50 или 100)
        end_date: Дата окончания периода (по умолчанию - текущая дата)

    Returns:
        float: Сумма, которую удалось бы отложить
    """
    try:
        # Определяем дату окончания периода
        if end_date is None:
            end_date = datetime.now()

        # Определяем начальную и конечную даты в зависимости от периода
        start_date, end_date = parse_period(period, end_date)

        total_investment = 0.0
        period_transactions = []

        for transaction in transactions:
            # Проверяем, есть ли нужные ключи
            if "Дата операции" not in transaction or "Сумма операции" not in transaction:
                continue

            # Парсим дату операции
            trans_date = parse_operation_date(transaction["Дата операции"])
            if trans_date is None:
                continue

            # Проверяем, попадает ли транзакция в период
            if start_date <= trans_date <= end_date:
                amount = transaction["Сумма операции"]

                # Берем только расходы (отрицательные суммы)
                if amount < 0:
                    abs_amount = abs(amount)
                    # Округляем вверх до ближайшего limit
                    rounded_amount = math.ceil(abs_amount / limit) * limit
                    investment = rounded_amount - abs_amount
                    total_investment += investment
                    period_transactions.append(transaction)

        # Формируем понятное описание периода
        period_desc = format_period_description(period, start_date, end_date)

        logger.info(
            f"Инвесткопилка за {period_desc}: {total_investment} руб. (транзакций: {len(period_transactions)})"
        )

        return round(total_investment, 2)

    except ValueError as e:
        logger.error(f"Ошибка в формате периода: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка в расчете инвесткопилки: {e}")
        return 0.0


def parse_period(period: Union[str, datetime], end_date: datetime) -> tuple:
    """
    Парсит период и возвращает начальную и конечную даты.

    Args:
        period: Период в различных форматах
        end_date: Базовая дата окончания

    Returns:
        tuple: (start_date, end_date)
    """
    # Если период - это datetime объект
    if isinstance(period, datetime):
        start_date = datetime(period.year, period.month, 1)
        # Последний день месяца
        if period.month == 12:
            end_date = datetime(period.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(period.year, period.month + 1, 1) - timedelta(days=1)
        return start_date, end_date

    # Проверяем, является ли период конкретным месяцем
    if isinstance(period, str):
        if '-' in period and not period.startswith(('W', 'M', 'Y', 'A')):
            # Это конкретный месяц
            target_date = parse_month(period)
            start_date = datetime(target_date.year, target_date.month, 1)
            # Последний день месяца
            if target_date.month == 12:
                end_date = datetime(target_date.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(target_date.year, target_date.month + 1, 1) - timedelta(days=1)
            return start_date, end_date

        # Это относительный период
        period_map = {
            'D': timedelta(days=1),
            'W': timedelta(weeks=1),
            'M': timedelta(days=30),
            '2M': timedelta(days=60),
            '3M': timedelta(days=90),
            '6M': timedelta(days=180),
            'Y': timedelta(days=365),
            'ALL': None
        }

        delta = period_map.get(period.upper())
        if delta is None and period.upper() != 'ALL':
            raise ValueError(f"Некорректный период: {period}")

        if period.upper() == 'ALL':
            start_date = datetime(1900, 1, 1)  # очень старая дата
        else:
            # Исправлено: проверяем, что delta не None
            if delta is None:
                raise ValueError(f"Некорректный период: {period}")
            start_date = end_date - delta

        return start_date, end_date

    raise ValueError(f"Некорректный тип периода: {type(period)}")


def parse_month(month_str: str) -> datetime:
    """
    Парсит строку с месяцем в различных форматах.

    Args:
        month_str: Строка с месяцем

    Returns:
        datetime: Объект datetime (первый день месяца)
    """
    formats = [
        "%m-%Y",  # 03-2026
        "%Y-%m",  # 2026-03
        "%m.%Y",  # 03.2026
        "%Y.%m",  # 2026.03
        "%m/%Y",  # 03/2026
        "%Y/%m",  # 2026/03
    ]

    for fmt in formats:
        try:
            return datetime.strptime(month_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Некорректный формат даты: {month_str}")


def parse_operation_date(date_str: str) -> Optional[datetime]:
    """
    Парсит дату операции в различных форматах.

    Args:
        date_str: Строка с датой

    Returns:
        Optional[datetime]: Объект datetime или None
    """
    formats = [
        "%d-%m-%Y",  # 15-01-2024
        "%d.%m.%Y",  # 15.01.2024
        "%d/%m/%Y",  # 15/01/2024
        "%Y-%m-%d",  # 2024-01-15
        "%Y.%m.%d",  # 2024.01.15
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    logger.warning(f"Не удалось распарсить дату: {date_str}")
    return None


def format_period_description(period: Union[str, datetime], start_date: datetime, end_date: datetime) -> str:
    """
    Формирует понятное описание периода.

    Args:
        period: Исходный период
        start_date: Начальная дата
        end_date: Конечная дата

    Returns:
        str: Описание периода
    """
    if isinstance(period, datetime):
        return period.strftime("%B %Y")

    period_names = {
        "D": "день",
        "W": "неделю",
        "M": "месяц",
        "2M": "2 месяца",
        "3M": "3 месяца",
        "6M": "6 месяцев",
        "Y": "год",
        "ALL": "все время",
    }

    if period.upper() in period_names:
        return f"последн{'' if period.upper() == 'D' else 'ю' if period.upper() in ['W', 'M'] else 'ие'} {period_names[period.upper()]}"
    else:
        # Для конкретного месяца
        return start_date.strftime("%B %Y")


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
        description = str(transaction.get("Описание", "")).lower()
        category = str(transaction.get("Категория", "")).lower()

        if search_lower in description or search_lower in category:
            results.append(transaction)

    logger.info(f"Простой поиск '{search_string}': найдено {len(results)} транзакций")
    return json.dumps(results, ensure_ascii=False, indent=2, default=str)

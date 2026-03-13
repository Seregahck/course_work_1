"""Модуль для формирования отчетов."""
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def report_decorator(filename: Optional[str] = None) -> Callable:
    """
    Декоратор для функций-отчетов.
    Сохраняет результат в JSON-файл.

    Args:
        filename: Имя файла для сохранения (если не указано, генерируется автоматически)
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Определяем имя файла
            if filename is None:
                file_name = f"reports/{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            else:
                file_name = f"reports/{filename}"

            # Сохраняем результат
            try:
                if isinstance(result, pd.DataFrame):
                    result.to_json(file_name, orient='records', date_format='iso', indent=2, force_ascii=False)
                else:
                    with open(file_name, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

                logger.info(f"Отчет сохранен в {file_name}")
            except Exception as e:
                logger.error(f"Ошибка сохранения отчета: {e}")

            return result

        return wrapper

    return decorator


@report_decorator()
def spending_by_category(
        transactions: pd.DataFrame,
        category: str,
        date: Optional[str] = None
) -> pd.DataFrame:
    """
    Отчет о тратах по категории за последние 3 месяца.

    Args:
        transactions: DataFrame с транзакциями
        category: Название категории
        date: Опциональная дата (формат 'YYYY-MM-DD')

    Returns:
        DataFrame с отфильтрованными транзакциями
    """
    if date is None:
        end_date = datetime.now()
    else:
        end_date = pd.to_datetime(date)

    start_date = end_date - timedelta(days=90)  # 3 месяца

    # Фильтруем по категории и дате
    mask = (
            (transactions['Категория'] == category) &
            (pd.to_datetime(transactions['Дата операции'], dayfirst=True) >= start_date) &
            (pd.to_datetime(transactions['Дата операции'], dayfirst=True) <= end_date)
    )

    result = transactions[mask].copy()
    logger.info(f"Отчет по категории '{category}' за 3 месяца: {len(result)} транзакций")

    return result


@report_decorator(filename="weekday_report.json")
def spending_by_weekday(
        transactions: pd.DataFrame,
        date: Optional[str] = None
) -> Dict:
    """
    Отчет о средних тратах по дням недели.

    Args:
        transactions: DataFrame с транзакциями
        date: Опциональная дата (формат 'YYYY-MM-DD')

    Returns:
        Dict со средними тратами по дням недели
    """
    if date is None:
        end_date = datetime.now()
    else:
        end_date = pd.to_datetime(date)

    start_date = end_date - timedelta(days=90)

    # Фильтруем по дате
    mask = (
            (pd.to_datetime(transactions['Дата операции'], dayfirst=True) >= start_date) &
            (pd.to_datetime(transactions['Дата операции'], dayfirst=True) <= end_date)
    )
    filtered = transactions[mask].copy()

    # Добавляем день недели
    filtered['День_недели'] = pd.to_datetime(filtered['Дата операции']).dt.day_name(locale='ru_RU')

    # Берем только расходы
    expenses = filtered[filtered['Сумма операции'] < 0].copy()
    expenses['Сумма операции'] = abs(expenses['Сумма операции'])

    # Группируем по дням недели
    result = expenses.groupby('День_недели')['Сумма операции'].mean().round(2).to_dict()

    # Сортируем дни недели
    day_order = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    sorted_result = {day: result.get(day, 0) for day in day_order}

    logger.info("Отчет по дням недели сформирован")
    return sorted_result

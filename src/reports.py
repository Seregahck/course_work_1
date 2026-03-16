"""Модуль для формирования отчетов."""

import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional, cast

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
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)

            # Определяем имя файла
            if filename is None:
                file_name = f"reports/{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            else:
                file_name = f"reports/{filename}"

            # Сохраняем результат
            try:
                if isinstance(result, pd.DataFrame):
                    result.to_json(file_name, orient="records", date_format="iso", indent=2, force_ascii=False)
                else:
                    with open(file_name, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2, default=str)

                logger.info("Отчет сохранен в %s", file_name)
            except Exception as e:
                logger.error("Ошибка сохранения отчета: %s", e)

            return result

        return wrapper

    return decorator


@report_decorator()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
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

    # Проверим наличие необходимых колонок
    if "Категория" not in transactions.columns:
        logger.error("Колонка 'Категория' не найдена")
        return pd.DataFrame()

    if "Дата операции" not in transactions.columns:
        logger.error("Колонка 'Дата операции' не найдена")
        return pd.DataFrame()

    # Преобразуем даты
    df_copy = transactions.copy()
    df_copy["Дата_операции_dt"] = pd.to_datetime(df_copy["Дата операции"], dayfirst=True, errors="coerce")

    # Фильтруем по категории и дате - исправлено: операторы в начале строк
    mask = (
        (df_copy["Категория"] == category)
        & (df_copy["Дата_операции_dt"] >= start_date)
        & (df_copy["Дата_операции_dt"] <= end_date)
    )

    result = df_copy[mask].copy()
    result = result.drop(columns=["Дата_операции_dt"])

    logger.info("Отчет по категории '%s' за 3 месяца: %d транзакций", category, len(result))
    if len(result) > 0:
        total = abs(result["Сумма операции"].sum())
        logger.info("Общая сумма: %.2f₽", total)

    return cast(pd.DataFrame, result)


@report_decorator(filename="weekday_report.json")
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> Dict[str, float]:
    """
    Отчет о средних тратах по дням недели.

    Args:
        transactions: DataFrame с транзакциями
        date: Опциональная дата (формат 'YYYY-MM-DD')

    Returns:
        Dict со средними тратами по дням недели
    """
    if transactions.empty:
        return {}

    if date is None:
        end_date = datetime.now()
    else:
        end_date = pd.to_datetime(date)

    start_date = end_date - timedelta(days=90)

    # Проверяем наличие необходимых колонок
    if "Дата операции" not in transactions.columns or "Сумма операции" not in transactions.columns:
        logger.warning("Необходимые колонки отсутствуют")
        return {}

    # Создаем копию и преобразуем даты
    transactions_copy = transactions.copy()
    transactions_copy["Дата_операции_dt"] = pd.to_datetime(
        transactions_copy["Дата операции"], format="%d.%m.%Y", errors="coerce"
    )

    # Удаляем строки с некорректными датами
    transactions_clean = transactions_copy.dropna(subset=["Дата_операции_dt"]).copy()

    if transactions_clean.empty:
        return {}

    # Фильтруем по дате используя .loc - исправлено: операторы в начале строк
    date_mask = (transactions_clean["Дата_операции_dt"] >= start_date) & (
        transactions_clean["Дата_операции_dt"] <= end_date
    )
    filtered = transactions_clean.loc[date_mask].copy()

    if filtered.empty:
        return {}

    # Добавляем день недели
    days_map: Dict[int, str] = {
        0: "понедельник",
        1: "вторник",
        2: "среда",
        3: "четверг",
        4: "пятница",
        5: "суббота",
        6: "воскресенье",
    }
    filtered["День_недели"] = filtered["Дата_операции_dt"].dt.dayofweek.map(days_map)

    # Берем только расходы
    expenses_mask = filtered["Сумма операции"] < 0
    expenses = filtered.loc[expenses_mask].copy()

    if expenses.empty:
        return {}

    # Создаем колонку с абсолютными значениями
    expenses["Сумма_abs"] = expenses["Сумма операции"].abs()

    # Группируем по дням недели
    grouped = expenses.groupby("День_недели")["Сумма_abs"].mean().round(2)
    result_dict = grouped.to_dict()

    # Сортируем дни недели
    day_order = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    sorted_result: Dict[str, float] = {}
    for day in day_order:
        sorted_result[day] = float(result_dict.get(day, 0.0))

    logger.info("Отчет по дням недели сформирован")
    return sorted_result

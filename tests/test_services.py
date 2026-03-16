"""Тесты для модуля services.py."""
import json
import pytest
import math
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from typing import Any, Dict, List

from src.services import (
    investment_bank,
    parse_period,
    parse_month,
    parse_operation_date,
    format_period_description,
    simple_search
)


# Фикстуры
@pytest.fixture
def sample_transactions() -> List[Dict[str, Any]]:
    """Возвращает набор тестовых транзакций."""
    return [
        {
            'Дата операции': '15-01-2024',
            'Сумма операции': -1500.50,
            'Описание': 'Покупка продуктов',
            'Категория': 'Супермаркеты'
        },
        {
            'Дата операции': '20-01-2024',
            'Сумма операции': -2300.00,  # Кратно 50
            'Описание': 'Оплата ЖКХ',
            'Категория': 'Коммунальные платежи'
        },
        {
            'Дата операции': '25-01-2024',
            'Сумма операции': 50000.00,  # Доход (не учитывается)
            'Описание': 'Зарплата',
            'Категория': 'Доходы'
        },
        {
            'Дата операции': '10-02-2024',
            'Сумма операции': -890.75,  # Другой месяц
            'Описание': 'Кофе',
            'Категория': 'Кафе'
        },
        {
            'Дата операции': '05-01-2024',
            'Сумма операции': -50.25,
            'Описание': 'Проезд',
            'Категория': 'Транспорт'
        },
        {
            'Дата операции': '15-03-2024',
            'Сумма операции': -123.45,
            'Описание': 'Книги',
            'Категория': 'Образование'
        }
    ]


@pytest.fixture
def transactions_with_missing_keys() -> List[Dict[str, Any]]:
    """Транзакции с отсутствующими ключами."""
    return [
        {'Сумма операции': -100},  # Нет даты
        {'Дата операции': '15-01-2024'},  # Нет суммы
        {'Дата операции': 'invalid', 'Сумма операции': -200},  # Неверная дата
        {'Дата операции': '15-01-2024', 'Сумма операции': -300, 'Описание': 'Тест'}  # Нормальная
    ]


# Тесты для parse_operation_date
class TestParseOperationDate:
    """Тестирование парсинга даты операции."""

    def test_parse_operation_date_dd_mm_yyyy(self):
        """Парсинг даты в формате DD-MM-YYYY."""
        date = parse_operation_date('15-01-2024')
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_parse_operation_date_dd_mm_yyyy_dots(self):
        """Парсинг даты в формате DD.MM.YYYY."""
        date = parse_operation_date('15.01.2024')
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_parse_operation_date_dd_mm_yyyy_slashes(self):
        """Парсинг даты в формате DD/MM/YYYY."""
        date = parse_operation_date('15/01/2024')
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_parse_operation_date_yyyy_mm_dd(self):
        """Парсинг даты в формате YYYY-MM-DD."""
        date = parse_operation_date('2024-01-15')
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_parse_operation_date_yyyy_mm_dd_dots(self):
        """Парсинг даты в формате YYYY.MM.DD."""
        date = parse_operation_date('2024.01.15')
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_parse_operation_date_invalid(self):
        """Парсинг неверной даты."""
        date = parse_operation_date('invalid-date')
        assert date is None

    def test_parse_operation_date_empty(self):
        """Парсинг пустой строки."""
        date = parse_operation_date('')
        assert date is None


# Тесты для parse_month
class TestParseMonth:
    """Тестирование парсинга месяца."""

    def test_parse_month_mm_yyyy(self):
        """Парсинг месяца в формате MM-YYYY."""
        date = parse_month('01-2024')
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 1

    def test_parse_month_yyyy_mm(self):
        """Парсинг месяца в формате YYYY-MM."""
        date = parse_month('2024-01')
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 1

    def test_parse_month_mm_yyyy_dots(self):
        """Парсинг месяца в формате MM.YYYY."""
        date = parse_month('01.2024')
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 1

    def test_parse_month_yyyy_mm_dots(self):
        """Парсинг месяца в формате YYYY.MM."""
        date = parse_month('2024.01')
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 1

    def test_parse_month_mm_yyyy_slashes(self):
        """Парсинг месяца в формате MM/YYYY."""
        date = parse_month('01/2024')
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 1

    def test_parse_month_yyyy_mm_slashes(self):
        """Парсинг месяца в формате YYYY/MM."""
        date = parse_month('2024/01')
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 1

    def test_parse_month_invalid(self):
        """Парсинг неверного формата месяца."""
        with pytest.raises(ValueError):
            parse_month('invalid')


# Тесты для parse_period
class TestParsePeriod:
    """Тестирование парсинга периода."""

    def test_parse_period_datetime_object(self):
        """Парсинг периода как datetime объекта."""
        end_date = datetime(2024, 1, 31)
        period = datetime(2024, 1, 15)
        start, end = parse_period(period, end_date)

        assert start == datetime(2024, 1, 1)
        assert end == datetime(2024, 1, 31)

    def test_parse_period_datetime_december(self):
        """Парсинг периода для декабря (переход на следующий год)."""
        end_date = datetime(2024, 12, 31)
        period = datetime(2024, 12, 15)
        start, end = parse_period(period, end_date)

        assert start == datetime(2024, 12, 1)
        assert end == datetime(2024, 12, 31)

    def test_parse_period_specific_month(self):
        """Парсинг конкретного месяца."""
        end_date = datetime(2024, 1, 31)
        start, end = parse_period('01-2024', end_date)

        assert start == datetime(2024, 1, 1)
        assert end == datetime(2024, 1, 31)

    def test_parse_period_specific_month_december(self):
        """Парсинг декабря."""
        end_date = datetime(2024, 12, 31)
        start, end = parse_period('12-2024', end_date)

        assert start == datetime(2024, 12, 1)
        assert end == datetime(2024, 12, 31)

    def test_parse_period_day(self):
        """Парсинг периода 'D' (день)."""
        end_date = datetime(2024, 1, 15, 12, 0)
        start, end = parse_period('D', end_date)

        assert start == datetime(2024, 1, 14, 12, 0)
        assert end == end_date

    def test_parse_period_week(self):
        """Парсинг периода 'W' (неделя)."""
        end_date = datetime(2024, 1, 15)
        start, end = parse_period('W', end_date)

        assert start == end_date - timedelta(weeks=1)
        assert end == end_date

    def test_parse_period_month(self):
        """Парсинг периода 'M' (месяц)."""
        end_date = datetime(2024, 1, 15)
        start, end = parse_period('M', end_date)

        assert start == end_date - timedelta(days=30)
        assert end == end_date

    def test_parse_period_3months(self):
        """Парсинг периода '3M' (3 месяца)."""
        end_date = datetime(2024, 1, 15)
        start, end = parse_period('3M', end_date)

        assert start == end_date - timedelta(days=90)
        assert end == end_date

    def test_parse_period_year(self):
        """Парсинг периода 'Y' (год)."""
        end_date = datetime(2024, 1, 15)
        start, end = parse_period('Y', end_date)

        assert start == end_date - timedelta(days=365)
        assert end == end_date

    def test_parse_period_all(self):
        """Парсинг периода 'ALL' (все время)."""
        end_date = datetime(2024, 1, 15)
        start, end = parse_period('ALL', end_date)

        assert start == datetime(1900, 1, 1)
        assert end == end_date

    def test_parse_period_invalid_string(self):
        """Парсинг неверной строки периода."""
        with pytest.raises(ValueError):
            parse_period('INVALID', datetime.now())

    def test_parse_period_invalid_type(self):
        """Парсинг неверного типа периода."""
        with pytest.raises(ValueError):
            parse_period(123, datetime.now())  # type: ignore


# Тесты для investment_bank
class TestInvestmentBank:
    """Тестирование сервиса Инвесткопилка."""

    def test_investment_bank_specific_month(self, sample_transactions):
        """Расчет за конкретный месяц."""
        result = investment_bank('01-2024', sample_transactions, 50)

        # Расчет:
        # 1500.50 -> ceil(1500.5/50)=31 -> 31*50=1550 -> +49.5
        # 2300.00 -> ceil(2300/50)=46 -> 46*50=2300 -> 0
        # 50.25 -> ceil(50.25/50)=2 -> 2*50=100 -> +49.75
        # Итого: 49.5 + 49.75 = 99.25
        assert result == 99.25

    def test_investment_bank_with_limit_10(self, sample_transactions):
        """Расчет с лимитом 10 рублей."""
        result = investment_bank('01-2024', sample_transactions, 10)

        # Расчет с лимитом 10:
        # 1500.50 -> ceil(1500.5/10)=151 -> 151*10=1510 -> +9.5
        # 2300.00 -> ceil(2300/10)=230 -> 230*10=2300 -> 0
        # 50.25 -> ceil(50.25/10)=6 -> 6*10=60 -> +9.75
        # Итого: 9.5 + 9.75 = 19.25
        assert result == 19.25

    def test_investment_bank_with_limit_100(self, sample_transactions):
        """Расчет с лимитом 100 рублей."""
        result = investment_bank('01-2024', sample_transactions, 100)

        # Расчет с лимитом 100:
        # 1500.50 -> ceil(1500.5/100)=16 -> 16*100=1600 -> +99.5
        # 2300.00 -> ceil(2300/100)=23 -> 23*100=2300 -> 0
        # 50.25 -> ceil(50.25/100)=1 -> 1*100=100 -> +49.75
        # Итого: 99.5 + 49.75 = 149.25
        assert result == 149.25

    def test_investment_bank_no_transactions_in_period(self, sample_transactions):
        """Нет транзакций в периоде."""
        result = investment_bank('03-2025', sample_transactions, 50)  # Нет транзакций
        assert result == 0.0

    def test_investment_bank_only_income(self):
        """Только доходы (положительные суммы)."""
        transactions = [
            {'Дата операции': '15-01-2024', 'Сумма операции': 1000},
            {'Дата операции': '20-01-2024', 'Сумма операции': 500}
        ]
        result = investment_bank('01-2024', transactions, 50)
        assert result == 0.0

    def test_investment_bank_empty_list(self):
        """Пустой список транзакций."""
        result = investment_bank('01-2024', [], 50)
        assert result == 0.0

    def test_investment_bank_invalid_period(self, sample_transactions):
        """Неверный период."""
        with pytest.raises(ValueError):
            investment_bank('INVALID', sample_transactions, 50)


# Тесты для simple_search
class TestSimpleSearch:
    """Тестирование сервиса Простой поиск."""

    def test_simple_search_by_category(self, sample_transactions):
        """Поиск по категории."""
        result_json = simple_search('транспорт', sample_transactions)
        result = json.loads(result_json)

        assert len(result) == 1
        assert result[0]['Категория'] == 'Транспорт'

    def test_simple_search_partial_match(self, sample_transactions):
        """Частичное совпадение."""
        result_json = simple_search('ком', sample_transactions)
        result = json.loads(result_json)

        assert len(result) == 1
        assert result[0]['Категория'] == 'Коммунальные платежи'

    def test_simple_search_multiple_results(self, sample_transactions):
        """Несколько результатов."""
        result_json = simple_search('а', sample_transactions)
        result = json.loads(result_json)

        assert len(result) >= 2  # Должно быть несколько транзакций с буквой 'а'

    def test_simple_search_case_insensitive(self, sample_transactions):
        """Регистронезависимость."""
        result_upper = simple_search('ПРОДУКТЫ', sample_transactions)
        result_lower = simple_search('продукты', sample_transactions)

        assert json.loads(result_upper) == json.loads(result_lower)

    def test_simple_search_no_results(self, sample_transactions):
        """Нет результатов."""
        result_json = simple_search('несуществующий текст', sample_transactions)
        result = json.loads(result_json)

        assert result == []

    def test_simple_search_empty_string(self, sample_transactions):
        """Пустая строка поиска (должна вернуть все)."""
        result_json = simple_search('', sample_transactions)
        result = json.loads(result_json)

        assert len(result) == len(sample_transactions)

    def test_simple_search_with_missing_keys(self):
        """Поиск с транзакциями без ключей."""
        transactions = [
            {'Сумма операции': -100},  # Нет описания и категории
            {'Описание': 'Тест'},  # Нет суммы, но есть описание
            {'Категория': 'Тест'},  # Нет суммы, но есть категория
            {'Описание': 'Тест', 'Категория': 'Тест'}  # Есть оба поля
        ]

        result_json = simple_search('тест', transactions)
        result = json.loads(result_json)

        assert len(result) == 3  # Три транзакции с тестом


# Интеграционные тесты
class TestServicesIntegration:
    """Интеграционные тесты для сервисов."""

    def test_investment_bank_with_search_results(self, sample_transactions):
        """Поиск транзакций и применение инвесткопилки."""
        # Находим транзакции по категории
        search_result_json = simple_search('супермаркеты', sample_transactions)
        search_result = json.loads(search_result_json)

        # Применяем инвесткопилку
        investment = investment_bank('01-2024', search_result, 50)

        # Должна быть одна транзакция на 1500.50
        assert investment == 49.5

    def test_multiple_operations_flow(self, sample_transactions):
        """Полный цикл работы с сервисами."""
        # Поиск транзакций
        search_result_json = simple_search('а', sample_transactions)
        search_result = json.loads(search_result_json)

        # Фильтрация по периоду
        january_transactions = [
            t for t in search_result
            if parse_operation_date(t.get('Дата операции', '')) and
            parse_operation_date(t['Дата операции']).month == 1
        ]

        # Инвесткопилка
        investment = investment_bank('01-2024', january_transactions, 50)

        assert isinstance(investment, float)
        assert investment >= 0

    def test_different_periods_consistency(self, sample_transactions):
        """Проверка согласованности разных периодов."""
        # Сумма за 3 месяца должна быть больше или равна сумме за месяц
        month_investment = investment_bank('01-2024', sample_transactions, 50)
        three_months_investment = investment_bank('3M', sample_transactions, 50,
                                                   end_date=datetime(2024, 3, 31))

        assert three_months_investment >= month_investment

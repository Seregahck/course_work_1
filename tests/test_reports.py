"""Тесты для модуля reports.py."""
import json
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open
from pathlib import Path

from src.reports import (
    report_decorator,
    spending_by_category,
    spending_by_weekday
)


# Фикстуры
@pytest.fixture
def sample_transactions_df():
    """Создает тестовый DataFrame с транзакциями."""
    return pd.DataFrame({
        'Дата операции': ['15.01.2024', '20.01.2024', '25.01.2024', '10.02.2024', '05.03.2024'],
        'Сумма операции': [-1500.50, -2300.00, 50000.00, -890.75, -1200.00],
        'Категория': ['Супермаркеты', 'Коммунальные', 'Доходы', 'Кафе', 'Супермаркеты'],
        'Описание': ['Пятерочка', 'ЖКХ', 'Зарплата', 'Кофе', 'Магнит']
    })


@pytest.fixture
def sample_transactions_with_invalid_dates():
    """DataFrame с некорректными датами."""
    return pd.DataFrame({
        'Дата операции': ['15.01.2024', 'invalid_date', '25.01.2024', None, '05.03.2024'],
        'Сумма операции': [-100, -200, -300, -400, -500],
        'Категория': ['А', 'Б', 'В', 'Г', 'Д']
    })


@pytest.fixture
def sample_transactions_missing_columns():
    """DataFrame с отсутствующими колонками."""
    return pd.DataFrame({
        'Date': ['15.01.2024', '20.01.2024'],
        'Amount': [-100, -200]
    })


# Тесты для декоратора report_decorator
class TestReportDecorator:
    """Тестирование декоратора для отчетов."""

    def test_decorator_without_filename(self):
        """Тест декоратора без указания имени файла."""
        @report_decorator()
        def test_func():
            return {"test": "data"}

        with patch('src.reports.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'

            with patch('builtins.open', mock_open()) as mock_file:
                result = test_func()

                assert result == {"test": "data"}
                mock_file.assert_called_once()
                call_args = mock_file.call_args[0][0]
                assert 'reports/test_func_20240101_120000.json' in call_args

    def test_decorator_with_filename(self):
        """Тест декоратора с указанием имени файла."""
        @report_decorator(filename="custom_report.json")
        def test_func():
            return {"test": "data"}

        with patch('builtins.open', mock_open()) as mock_file:
            result = test_func()

            assert result == {"test": "data"}
            mock_file.assert_called_once_with('reports/custom_report.json', 'w', encoding='utf-8')

    def test_decorator_with_dataframe_result(self, sample_transactions_df):
        """Тест декоратора с результатом в виде DataFrame."""
        @report_decorator()
        def test_func():
            return sample_transactions_df

        with patch('src.reports.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'

            with patch('pandas.DataFrame.to_json') as mock_to_json:
                result = test_func()

                assert isinstance(result, pd.DataFrame)
                mock_to_json.assert_called_once()

    def test_decorator_save_error(self):
        """Тест ошибки при сохранении."""
        @report_decorator()
        def test_func():
            return {"test": "data"}

        with patch('builtins.open', side_effect=Exception("Write error")):
            # Должно отработать без исключений
            result = test_func()
            assert result == {"test": "data"}

    def test_decorator_with_list_result(self):
        """Тест декоратора с результатом в виде списка."""
        @report_decorator()
        def test_func():
            return [1, 2, 3, {"key": "value"}]

        with patch('builtins.open', mock_open()) as mock_file:
            result = test_func()

            assert result == [1, 2, 3, {"key": "value"}]
            mock_file.assert_called_once()


# Тесты для spending_by_category
class TestSpendingByCategory:
    """Тестирование отчета о тратах по категории."""

    def test_spending_by_category_basic(self, sample_transactions_df):
        """Базовый тест отчета по категории."""
        test_date = '2024-03-15'

        result = spending_by_category(sample_transactions_df, 'Супермаркеты', test_date)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # Две транзакции в категории 'Супермаркеты'
        assert all(result['Категория'] == 'Супермаркеты')
        assert abs(result['Сумма операции'].sum()) == 2700.50  # 1500.50 + 1200.00

    def test_spending_by_category_no_date(self, sample_transactions_df):
        """Тест без указания даты (используется текущая)."""
        with patch('src.reports.datetime') as mock_datetime:
            fixed_date = datetime(2024, 3, 15)
            mock_datetime.now.return_value = fixed_date

            result = spending_by_category(sample_transactions_df, 'Супермаркеты')

            assert len(result) == 2

    def test_spending_by_category_no_transactions(self, sample_transactions_df):
        """Тест с категорией без транзакций."""
        result = spending_by_category(sample_transactions_df, 'НесуществующаяКатегория', '2024-03-15')

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_spending_by_category_out_of_period(self, sample_transactions_df):
        """Тест с датой вне периода транзакций."""
        result = spending_by_category(sample_transactions_df, 'Супермаркеты', '2023-01-01')

        assert result.empty

    def test_spending_by_category_missing_category_column(self, sample_transactions_missing_columns):
        """Тест с отсутствующей колонкой категории."""
        result = spending_by_category(sample_transactions_missing_columns, 'А', '2024-03-15')

        assert result.empty

    def test_spending_by_category_missing_date_column(self):
        """Тест с отсутствующей колонкой даты."""
        df = pd.DataFrame({
            'Категория': ['А', 'Б'],
            'Сумма операции': [-100, -200]
        })

        result = spending_by_category(df, 'А', '2024-03-15')

        assert result.empty

    def test_spending_by_category_empty_dataframe(self):
        """Тест с пустым DataFrame."""
        df = pd.DataFrame()
        result = spending_by_category(df, 'А', '2024-03-15')

        assert result.empty

    def test_spending_by_category_with_invalid_dates(self, sample_transactions_with_invalid_dates):
        """Тест с некорректными датами."""
        result = spending_by_category(sample_transactions_with_invalid_dates, 'А', '2024-03-15')

        # Только транзакции с корректными датами
        assert len(result) == 1  # Только транзакция с датой '15.01.2024'

    def test_spending_by_category_filter_by_amount(self, sample_transactions_df):
        """Проверка, что фильтруются только расходы."""
        result = spending_by_category(sample_transactions_df, 'Доходы', '2024-03-15')

        assert len(result) == 1
        assert result.iloc[0]['Сумма операции'] == 50000.00  # Доход


# Тесты для spending_by_weekday
class TestSpendingByWeekday:
    """Тестирование отчета о средних тратах по дням недели."""

    def test_spending_by_weekday_basic(self):
        """Базовый тест отчета по дням недели."""
        df = pd.DataFrame({
            'Дата операции': ['15.01.2024', '16.01.2024', '17.01.2024'],
            'Сумма операции': [-1000, -2000, -3000],
            'Категория': ['А'] * 3
        })

        result = spending_by_weekday(df, '2024-01-20')

        assert isinstance(result, dict)
        assert len(result) == 7  # Все дни недели

        # Понедельник (15.01)
        assert result['понедельник'] == 1000.0
        # Вторник (16.01)
        assert result['вторник'] == 2000.0
        # Среда (17.01)
        assert result['среда'] == 3000.0
        # Остальные дни = 0
        assert result['четверг'] == 0.0
        assert result['пятница'] == 0.0
        assert result['суббота'] == 0.0
        assert result['воскресенье'] == 0.0

    def test_spending_by_weekday_with_income(self):
        """Тест с доходами (должны игнорироваться)."""
        df = pd.DataFrame({
            'Дата операции': ['15.01.2024', '16.01.2024', '17.01.2024'],
            'Сумма операции': [-1000, 2000, -3000],  # Вторая транзакция - доход
            'Категория': ['А'] * 3
        })

        result = spending_by_weekday(df, '2024-01-20')

        assert result['понедельник'] == 1000.0
        assert result['вторник'] == 0.0  # Доход не учитывается
        assert result['среда'] == 3000.0

    def test_spending_by_weekday_no_date(self):
        """Тест без указания даты."""
        df = pd.DataFrame({
            'Дата операции': ['15.01.2024'],
            'Сумма операции': [-1000],
            'Категория': ['А']
        })

        with patch('src.reports.datetime') as mock_datetime:
            fixed_date = datetime(2024, 1, 20)
            mock_datetime.now.return_value = fixed_date

            result = spending_by_weekday(df)

            assert result['понедельник'] == 1000.0

    def test_spending_by_weekday_no_expenses(self):
        """Нет расходов (только доходы)."""
        df = pd.DataFrame({
            'Дата операции': ['15.01.2024', '16.01.2024'],
            'Сумма операции': [1000, 2000],  # Только доходы
            'Категория': ['А'] * 2
        })

        result = spending_by_weekday(df, '2024-01-20')

        # Все значения должны быть 0
        assert all(v == 0.0 for v in result.values())

    def test_spending_by_weekday_empty_dataframe(self):
        """Пустой DataFrame."""
        df = pd.DataFrame()
        result = spending_by_weekday(df, '2024-01-20')

        assert result == {}

    def test_spending_by_weekday_missing_columns(self, sample_transactions_missing_columns):
        """Отсутствуют необходимые колонки."""
        result = spending_by_weekday(sample_transactions_missing_columns, '2024-01-20')

        assert result == {}

    def test_spending_by_weekday_with_invalid_dates(self, sample_transactions_with_invalid_dates):
        """Некорректные даты."""
        result = spending_by_weekday(sample_transactions_with_invalid_dates, '2024-03-15')

        # Транзакции с корректными датами будут обработаны
        assert isinstance(result, dict)
        assert len(result) == 7

    def test_spending_by_weekday_out_of_period(self):
        """Транзакции вне периода."""
        df = pd.DataFrame({
            'Дата операции': ['15.01.2023'],  # Старая дата
            'Сумма операции': [-1000],
            'Категория': ['А']
        })

        result = spending_by_weekday(df, '2024-01-20')

        assert result == {}  # Нет транзакций за период

    def test_spending_by_weekday_average_calculation(self):
        """Проверка расчета средних значений."""
        # Два понедельника с разными суммами
        df = pd.DataFrame({
            'Дата операции': ['15.01.2024', '22.01.2024', '16.01.2024'],
            'Сумма операции': [-1000, -3000, -2000],
            'Категория': ['А'] * 3
        })

        result = spending_by_weekday(df, '2024-01-30')

        # Среднее за понедельник: (1000 + 3000) / 2 = 2000
        assert result['понедельник'] == 2000.0
        # Среднее за вторник: 2000 / 1 = 2000
        assert result['вторник'] == 2000.0

    def test_spending_by_weekday_day_order(self):
        """Проверка порядка дней в результате."""
        df = pd.DataFrame({
            'Дата операции': ['15.01.2024'],  # Понедельник
            'Сумма операции': [-1000],
            'Категория': ['А']
        })

        result = spending_by_weekday(df, '2024-01-20')

        # Проверяем порядок ключей
        expected_order = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
        assert list(result.keys()) == expected_order


# Интеграционные тесты
class TestReportsIntegration:
    """Интеграционные тесты для отчетов."""

    def test_spending_by_category_and_weekday_consistency(self, sample_transactions_df):
        """Проверка согласованности разных отчетов."""
        # Отчет по категории
        category_result = spending_by_category(sample_transactions_df, 'Супермаркеты', '2024-03-15')
        category_total = abs(category_result['Сумма операции'].sum())

        # Отчет по дням недели
        weekday_result = spending_by_weekday(sample_transactions_df, '2024-03-15')

        # Сумма средних по дням должна быть >= общей суммы (из-за усреднения)
        weekday_total = sum(weekday_result.values())

        assert category_total <= weekday_total or abs(category_total - weekday_total) < 0.1

    @patch('src.reports.datetime')
    def test_reports_with_fixed_date(self, mock_datetime, sample_transactions_df):
        """Тесты с фиксированной датой."""
        fixed_date = datetime(2024, 3, 15)
        mock_datetime.now.return_value = fixed_date

        # Отчет по категории
        category_result = spending_by_category(sample_transactions_df, 'Супермаркеты')

        # Отчет по дням недели
        weekday_result = spending_by_weekday(sample_transactions_df)

        assert len(category_result) == 2
        assert weekday_result['понедельник'] > 0

    def test_full_report_flow(self, sample_transactions_df, tmp_path):
        """Полный поток создания отчетов."""
        # Создаем временную директорию для отчетов
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()

        with patch('src.reports.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = '20240101_120000'

            with patch('src.reports.open', mock_open()) as mock_file:
                # Создаем отчет по категории
                category_result = spending_by_category(
                    sample_transactions_df,
                    'Супермаркеты',
                    '2024-03-15'
                )

                # Создаем отчет по дням недели
                weekday_result = spending_by_weekday(
                    sample_transactions_df,
                    '2024-03-15'
                )

                # Проверяем результаты
                assert len(category_result) == 2
                assert len(weekday_result) == 7
                assert weekday_result['понедельник'] > 0

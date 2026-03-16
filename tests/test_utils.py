"""Тесты для модуля utils.py."""
import json
import pytest
import pandas as pd
import requests
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, mock_open
import sys
from pathlib import Path

from src.utils import (
    load_transactions,
    get_greeting,
    get_currency_rates,
    get_stock_prices,
    filter_transactions_by_date,
    add_date_columns,
    df_to_json,
    ENCODING,
    BASE_DIR,
    LOG_DIR,
    REPORTS_DIR,
    DATA_DIR
)


# Фикстуры
@pytest.fixture
def sample_df():
    """Создает тестовый DataFrame с транзакциями."""
    return pd.DataFrame({
        'Дата операции': ['15.01.2024', '20.01.2024', '25.01.2024', '10.02.2024'],
        'Сумма операции': [-1500.50, -2300.00, 50000.00, -890.75],
        'Категория': ['Супермаркеты', 'Коммунальные', 'Доходы', 'Кафе'],
        'Описание': ['Пятерочка', 'ЖКХ', 'Зарплата', 'Кофе']
    })


@pytest.fixture
def sample_df_with_dates():
    """Создает DataFrame с различными форматами дат."""
    return pd.DataFrame({
        'Дата операции': ['15.01.2024', 'invalid_date', '25.01.2024', None],
        'Сумма операции': [-100, -200, -300, -400]
    })


# Тесты для констант и директорий
class TestConstants:
    """Тестирование констант и создания директорий."""

    def test_directories_created(self):
        """Проверка, что директории были созданы."""
        assert LOG_DIR.exists()
        assert REPORTS_DIR.exists()
        assert DATA_DIR.exists()

    def test_encoding_windows(self):
        """Проверка кодировки для Windows."""
        if sys.platform == 'win32':
            assert ENCODING == 'cp1251'
        else:
            assert ENCODING == 'utf-8'


# Тесты для load_transactions
class TestLoadTransactions:
    """Тестирование загрузки транзакций из Excel."""

    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_load_transactions_success(self, mock_exists, mock_read_excel, sample_df):
        """Успешная загрузка транзакций."""
        mock_exists.return_value = True
        mock_read_excel.return_value = sample_df

        result = load_transactions("test.xlsx")

        assert len(result) == 4
        assert 'Дата операции' in result.columns
        mock_read_excel.assert_called_once()

    @patch('os.path.exists')
    def test_load_transactions_file_not_found(self, mock_exists):
        """Файл не найден."""
        mock_exists.return_value = False

        result = load_transactions("nonexistent.xlsx")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_load_transactions_exception(self, mock_exists, mock_read_excel):
        """Ошибка при чтении файла."""
        mock_exists.return_value = True
        mock_read_excel.side_effect = Exception("Test error")

        result = load_transactions("test.xlsx")

        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @patch('src.utils.DATA_DIR')
    @patch('pandas.read_excel')
    @patch('os.path.exists')
    def test_load_transactions_with_relative_path(self, mock_exists, mock_read_excel, mock_data_dir, sample_df):
        """Загрузка с относительным путем."""
        mock_exists.return_value = True
        mock_read_excel.return_value = sample_df
        mock_data_dir.__str__.return_value = "/fake/path/data"

        result = load_transactions("data/operations.xlsx")

        assert len(result) == 4


# Тесты для get_greeting
class TestGetGreeting:
    """Тестирование приветствия в зависимости от времени."""

    @patch('src.utils.datetime')
    def test_get_greeting_morning(self, mock_datetime):
        """Утро (5-11)."""
        mock_datetime.now.return_value.hour = 9
        assert get_greeting() == "Доброе утро"

    @patch('src.utils.datetime')
    def test_get_greeting_afternoon(self, mock_datetime):
        """День (12-17)."""
        mock_datetime.now.return_value.hour = 14
        assert get_greeting() == "Добрый день"

    @patch('src.utils.datetime')
    def test_get_greeting_evening(self, mock_datetime):
        """Вечер (18-22)."""
        mock_datetime.now.return_value.hour = 20
        assert get_greeting() == "Добрый вечер"

    @patch('src.utils.datetime')
    def test_get_greeting_night(self, mock_datetime):
        """Ночь (23-4)."""
        mock_datetime.now.return_value.hour = 2
        assert get_greeting() == "Доброй ночи"

    @patch('src.utils.datetime')
    def test_get_greeting_boundary_morning_start(self, mock_datetime):
        """Граница: 5 утра."""
        mock_datetime.now.return_value.hour = 5
        assert get_greeting() == "Доброе утро"

    @patch('src.utils.datetime')
    def test_get_greeting_boundary_morning_end(self, mock_datetime):
        """Граница: 11 утра."""
        mock_datetime.now.return_value.hour = 11
        assert get_greeting() == "Доброе утро"

    @patch('src.utils.datetime')
    def test_get_greeting_boundary_afternoon_start(self, mock_datetime):
        """Граница: 12 дня."""
        mock_datetime.now.return_value.hour = 12
        assert get_greeting() == "Добрый день"

    @patch('src.utils.datetime')
    def test_get_greeting_boundary_evening_start(self, mock_datetime):
        """Граница: 18 вечера."""
        mock_datetime.now.return_value.hour = 18
        assert get_greeting() == "Добрый вечер"


# Тесты для get_currency_rates
class TestGetCurrencyRates:
    """Тестирование получения курсов валют."""

    @patch('src.utils.requests.get')
    @patch('src.utils.os.getenv')
    def test_get_currency_rates_success(self, mock_getenv, mock_get):
        """Успешное получение курсов валют."""
        mock_getenv.return_value = "fake_api_key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rates': {
                'USD': 0.0123,
                'EUR': 0.0112
            }
        }
        mock_get.return_value = mock_response

        rates = get_currency_rates(['USD', 'EUR'])

        assert len(rates) == 2
        assert rates[0]['currency'] == 'USD'
        assert 0.0122 <= rates[0]['rate'] <= 0.0124  # Примерное значение
        assert rates[1]['currency'] == 'EUR'
        assert mock_get.call_count == 2

    @patch('src.utils.os.getenv')
    def test_get_currency_rates_no_api_key(self, mock_getenv):
        """Нет API ключа - возвращаются тестовые данные."""
        mock_getenv.return_value = None

        rates = get_currency_rates(['USD', 'EUR'])

        assert len(rates) == 2
        assert rates[0]['currency'] == 'USD'
        assert rates[0]['rate'] == 0.012
        assert rates[1]['currency'] == 'EUR'
        assert rates[1]['rate'] == 0.011

    @patch('src.utils.requests.get')
    @patch('src.utils.os.getenv')
    def test_get_currency_rates_api_error(self, mock_getenv, mock_get):
        """Ошибка API."""
        mock_getenv.return_value = "fake_api_key"

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        rates = get_currency_rates(['USD'])

        assert len(rates) == 1
        assert rates[0]['currency'] == 'USD'
        assert rates[0]['rate'] == 0.0

    @patch('src.utils.requests.get')
    @patch('src.utils.os.getenv')
    def test_get_currency_rates_timeout(self, mock_getenv, mock_get):
        """Таймаут при запросе."""
        mock_getenv.return_value = "fake_api_key"
        mock_get.side_effect = requests.exceptions.Timeout

        rates = get_currency_rates(['USD'])

        assert len(rates) == 1
        assert rates[0]['currency'] == 'USD'
        assert rates[0]['rate'] == 0.0

    @patch('src.utils.requests.get')
    @patch('src.utils.os.getenv')
    def test_get_currency_rates_rate_limit(self, mock_getenv, mock_get):
        """Превышение лимита запросов (429)."""
        mock_getenv.return_value = "fake_api_key"

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        rates = get_currency_rates(['USD'])

        assert len(rates) == 1
        assert rates[0]['currency'] == 'USD'
        assert rates[0]['rate'] == 0.0


# Тесты для filter_transactions_by_date
class TestFilterTransactionsByDate:
    """Тестирование фильтрации транзакций по дате."""

    def test_filter_by_month(self, sample_df):
        """Фильтрация за месяц."""
        end_date = datetime(2024, 1, 31)
        filtered = filter_transactions_by_date(sample_df, end_date, 'M')

        assert len(filtered) == 3  # Транзакции за январь
        assert all(filtered['Категория'] != 'Кафе')  # Февральская транзакция исключена

    def test_filter_by_week(self, sample_df):
        """Фильтрация за неделю."""
        end_date = datetime(2024, 1, 20)
        filtered = filter_transactions_by_date(sample_df, end_date, 'W')

        assert len(filtered) == 2  # Транзакции 15 и 20 января

    def test_filter_by_year(self, sample_df):
        """Фильтрация за год."""
        end_date = datetime(2024, 12, 31)
        filtered = filter_transactions_by_date(sample_df, end_date, 'Y')

        assert len(filtered) == 4  # Все транзакции за 2024 год

    def test_filter_all_period(self, sample_df):
        """Фильтрация за все время."""
        end_date = datetime(2024, 12, 31)
        filtered = filter_transactions_by_date(sample_df, end_date, 'ALL')

        assert len(filtered) == 4  # Все транзакции

    def test_filter_empty_dataframe(self):
        """Фильтрация пустого DataFrame."""
        df = pd.DataFrame()
        end_date = datetime.now()
        filtered = filter_transactions_by_date(df, end_date, 'M')

        assert filtered.empty

    def test_filter_no_date_column(self):
        """DataFrame без колонки даты."""
        df = pd.DataFrame({'Сумма': [100, 200]})
        end_date = datetime.now()
        filtered = filter_transactions_by_date(df, end_date, 'M')

        assert filtered.empty

    def test_filter_with_invalid_dates(self, sample_df_with_dates):
        """Фильтрация с некорректными датами."""
        end_date = datetime(2024, 1, 31)
        filtered = filter_transactions_by_date(sample_df_with_dates, end_date, 'M')

        # Только корректные даты будут обработаны
        assert len(filtered) <= len(sample_df_with_dates)

    def test_filter_unknown_period(self, sample_df):
        """Неизвестный период - используется месяц по умолчанию."""
        end_date = datetime(2024, 1, 31)
        filtered = filter_transactions_by_date(sample_df, end_date, 'X')

        assert len(filtered) == 3  # Месяц по умолчанию


# Тесты для add_date_columns
class TestAddDateColumns:
    """Тестирование добавления колонок с датами."""

    def test_add_date_columns_success(self, sample_df):
        """Успешное добавление колонок с датами."""
        result = add_date_columns(sample_df)

        assert 'Дата_операции_dt' in result.columns
        assert 'Год' in result.columns
        assert 'Месяц' in result.columns
        assert 'День' in result.columns
        assert 'День_недели' in result.columns

        # Проверяем значения
        assert result.loc[0, 'Год'] == 2024
        assert result.loc[0, 'Месяц'] == 1
        assert result.loc[0, 'День'] == 15
        assert result.loc[0, 'День_недели'] == 0  # Понедельник

    def test_add_date_columns_empty_df(self):
        """Добавление колонок в пустой DataFrame."""
        df = pd.DataFrame()
        result = add_date_columns(df)

        assert result.empty

    def test_add_date_columns_no_date_column(self):
        """DataFrame без колонки даты."""
        df = pd.DataFrame({'Сумма': [100]})
        result = add_date_columns(df)

        assert 'Дата_операции_dt' not in result.columns

    def test_add_date_columns_with_invalid_dates(self, sample_df_with_dates):
        """Добавление колонок с некорректными датами."""
        result = add_date_columns(sample_df_with_dates)

        # Проверяем, что для некорректных дат значения NaN
        assert pd.isna(result.loc[1, 'Год'])
        assert pd.isna(result.loc[3, 'Год'])


# Тесты для df_to_json
class TestDfToJson:
    """Тестирование конвертации DataFrame в JSON."""

    def test_df_to_json_success(self, sample_df):
        """Успешная конвертация DataFrame в JSON."""
        json_str = df_to_json(sample_df)

        # Проверяем, что это валидный JSON
        data = json.loads(json_str)

        assert isinstance(data, list)
        assert len(data) == 4
        assert data[0]['Категория'] == 'Супермаркеты'

    def test_df_to_json_with_dates(self):
        """Конвертация с колонками datetime."""
        df = pd.DataFrame({
            'date': [pd.Timestamp('2024-01-15')],
            'value': [100]
        })

        json_str = df_to_json(df)
        data = json.loads(json_str)

        # Дата должна быть строкой
        assert data[0]['date'] == '15.01.2024'


    def test_df_to_json_empty(self):
        """Конвертация пустого DataFrame."""
        df = pd.DataFrame()
        json_str = df_to_json(df)
        data = json.loads(json_str)

        assert data == []


# Интеграционные тесты
class TestUtilsIntegration:
    """Интеграционные тесты для utils."""

    def test_filter_and_add_columns(self, sample_df):
        """Фильтрация и добавление колонок вместе."""
        end_date = datetime(2024, 1, 31)
        filtered = filter_transactions_by_date(sample_df, end_date, 'M')
        result = add_date_columns(filtered)

        assert len(result) == 3
        assert all(result['Год'] == 2024)
        assert all(result['Месяц'] == 1)

    def test_transaction_flow(self, sample_df):
        """Полный цикл обработки транзакций."""
        # Добавляем колонки
        df_with_dates = add_date_columns(sample_df)

        # Фильтруем
        end_date = datetime(2024, 1, 31)
        filtered = filter_transactions_by_date(df_with_dates, end_date, 'M')

        # Конвертируем в JSON
        json_result = df_to_json(filtered)
        data = json.loads(json_result)

        assert len(data) == 3
        assert all(t['Месяц'] == 1 for t in data)

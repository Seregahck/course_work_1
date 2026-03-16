"""Тесты для модуля views.py."""
import json
import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open

from src.views import (
    load_user_settings,
    get_cards_info,
    get_top_transactions,
    main_page
)


# Фикстуры
@pytest.fixture
def sample_df():
    """Создает тестовый DataFrame с транзакциями."""
    return pd.DataFrame({
        'Дата операции': ['15.01.2024', '20.01.2024', '25.01.2024', '10.02.2024'],
        'Дата платежа': ['15.01.2024', '20.01.2024', '25.01.2024', '10.02.2024'],
        'Номер карты': ['1234567890123456', '1234567890123456', '9876543210987654', None],
        'Сумма операции': [-1500.50, -2300.00, 50000.00, -890.75],
        'Сумма платежа': [1500.50, 2300.00, 50000.00, 890.75],
        'Категория': ['Супермаркеты', 'Коммунальные', 'Доходы', 'Кафе'],
        'Описание': ['Пятерочка', 'ЖКХ', 'Зарплата', 'Кофе']
    })


@pytest.fixture
def sample_df_without_cards():
    """DataFrame без данных о картах."""
    return pd.DataFrame({
        'Дата операции': ['15.01.2024', '20.01.2024'],
        'Сумма операции': [-1500.50, -2300.00],
        'Категория': ['Супермаркеты', 'Коммунальные']
    })


# Тесты для load_user_settings
class TestLoadUserSettings:
    """Тестирование загрузки настроек пользователя."""

    @patch('builtins.open', new_callable=mock_open,
           read_data='{"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "TSLA"]}')
    def test_load_user_settings_success(self, mock_file):
        """Успешная загрузка настроек из файла."""
        settings = load_user_settings()
        assert settings == {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "TSLA"]}
        mock_file.assert_called_once_with('user_settings.json', 'r', encoding='utf-8')

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_user_settings_file_not_found(self, mock_file):
        """Файл настроек не найден - возвращаются настройки по умолчанию."""
        settings = load_user_settings()
        assert settings == {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
        }

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    def test_load_user_settings_invalid_json(self, mock_file):
        """Некорректный JSON в файле - возвращаются настройки по умолчанию."""
        settings = load_user_settings()
        assert settings == {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
        }


# Тесты для get_top_transactions
class TestGetTopTransactions:
    """Тестирование получения топ транзакций."""

    def test_get_top_transactions_success(self, sample_df):
        """Успешное получение топ-транзакций."""
        top = get_top_transactions(sample_df, n=2)

        assert len(top) == 2
        # Первая транзакция (самая большая)
        assert top[0]['amount'] == 50000.00
        assert top[0]['category'] == 'Доходы'
        assert top[0]['description'] == 'Зарплата'
        # Вторая транзакция
        assert top[1]['amount'] == 2300.00
        assert top[1]['category'] == 'Коммунальные'

    def test_get_top_transactions_no_amount_column(self):
        """Отсутствует колонка 'Сумма платежа'."""
        df = pd.DataFrame({'Описание': ['test']})
        top = get_top_transactions(df)
        assert top == []

    def test_get_top_transactions_empty_dataframe(self):
        """Пустой DataFrame."""
        df = pd.DataFrame()
        top = get_top_transactions(df)
        assert top == []

    def test_get_top_transactions_all_negative(self):
        """Все суммы отрицательные (используются абсолютные значения)."""
        df = pd.DataFrame({
            'Сумма платежа': [-100, -500, -1000],
            'Категория': ['A', 'B', 'C'],
            'Описание': ['a', 'b', 'c'],
            'Дата операции': ['01.01.2024', '02.01.2024', '03.01.2024']
        })
        top = get_top_transactions(df, n=2)

        assert len(top) == 2
        assert top[0]['amount'] == 1000
        assert top[1]['amount'] == 500

    def test_get_top_transactions_with_nan_values(self):
        """Транзакции с NaN значениями в категориях."""
        df = pd.DataFrame({
            'Сумма платежа': [1000, 500],
            'Категория': ['A', None],
            'Описание': ['a', None],
            'Дата операции': ['01.01.2024', None]
        })
        top = get_top_transactions(df)

        assert len(top) == 2
        assert top[1]['category'] == ''  # NaN преобразуется в пустую строку
        assert top[1]['description'] == ''
        assert top[1]['date'] == ''


# Тесты для main_page
class TestMainPage:
    """Тестирование главной функции main_page."""

    @patch('src.views.load_transactions')
    @patch('src.views.load_user_settings')
    @patch('src.views.filter_transactions_by_date')
    @patch('src.views.get_greeting')
    @patch('src.views.get_cards_info')
    @patch('src.views.get_top_transactions')
    @patch('src.views.get_currency_rates')
    @patch('src.views.get_stock_prices')
    def test_main_page_success(
            self, mock_stocks, mock_currency, mock_top, mock_cards,
            mock_greeting, mock_filter, mock_settings, mock_load, sample_df
    ):
        """Успешное формирование ответа главной страницы."""
        # Настройка моков
        mock_load.return_value = sample_df
        mock_settings.return_value = {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "TSLA"]
        }
        mock_filter.return_value = sample_df
        mock_greeting.return_value = "Доброе утро"
        mock_cards.return_value = [{"last_digits": "3456", "total_spent": 3800.5, "cashback": 38.01}]
        mock_top.return_value = [
            {"date": "15.01.2024", "amount": 1500.5, "category": "Супермаркеты", "description": "Пятерочка"}]
        mock_currency.return_value = [{"currency": "USD", "rate": 0.012}]
        mock_stocks.return_value = [{"stock": "AAPL", "price": 175.5}]

        # Вызов функции
        result = main_page('2024-01-15 12:00:00')
        result_dict = json.loads(result)

        # Проверки
        assert result_dict['greeting'] == 'Доброе утро'
        assert len(result_dict['cards']) == 1
        assert len(result_dict['top_transactions']) == 1
        assert len(result_dict['currency_rates']) == 1
        assert len(result_dict['stock_prices']) == 1

        # Проверки вызовов
        mock_load.assert_called_once()
        mock_settings.assert_called_once()
        mock_filter.assert_called_once()
        mock_greeting.assert_called_once()
        mock_cards.assert_called_once_with(sample_df)
        mock_top.assert_called_once_with(sample_df, 5)
        mock_currency.assert_called_once_with(["USD", "EUR"])
        mock_stocks.assert_called_once_with(["AAPL", "TSLA"])

    @patch('src.views.load_transactions')
    def test_main_page_invalid_date(self, mock_load):
        """Неверный формат даты."""
        result = main_page('invalid-date')
        result_dict = json.loads(result)

        assert 'error' in result_dict
        assert result_dict['error'] == 'Неверный формат даты'
        mock_load.assert_not_called()

    @patch('src.views.load_transactions')
    @patch('src.views.load_user_settings')
    def test_main_page_with_real_data(self, mock_settings, mock_load, sample_df):
        """Тест с реальными данными (без моков внутренних функций)."""
        mock_load.return_value = sample_df
        mock_settings.return_value = {
            "user_currencies": ["USD", "EUR"],
            "user_stocks": ["AAPL", "TSLA"]
        }

        # Мокаем функции, которые делают внешние запросы
        with patch('src.views.get_currency_rates') as mock_currency, \
                patch('src.views.get_stock_prices') as mock_stocks, \
                patch('src.views.get_greeting') as mock_greeting:
            mock_currency.return_value = []
            mock_stocks.return_value = []
            mock_greeting.return_value = "Добрый день"

            result = main_page('2024-01-15 12:00:00')
            result_dict = json.loads(result)

            # Проверяем, что структура ответа корректна
            assert 'greeting' in result_dict
            assert 'cards' in result_dict
            assert 'top_transactions' in result_dict
            assert 'currency_rates' in result_dict
            assert 'stock_prices' in result_dict

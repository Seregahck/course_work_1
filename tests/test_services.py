import json
from datetime import datetime

import pytest

from src.services import investment_bank, simple_search


def test_investment_bank(sample_transactions):
    """Тест сервиса Инвесткопилка."""
    result = investment_bank("2023-12", sample_transactions, 50)
    assert isinstance(result, float)
    assert result >= 0


@pytest.mark.parametrize("limit,expected_min", [
    (10, 0),
    (50, 0),
    (100, 0),
])
def test_investment_bank_parametrized(sample_transactions, limit, expected_min):
    """Параметризованный тест Инвесткопилки."""
    result = investment_bank("2023-12", sample_transactions, limit)
    assert result >= expected_min


def test_simple_search(sample_transactions):
    """Тест простого поиска."""
    result = simple_search("тест", sample_transactions)
    data = json.loads(result)
    assert isinstance(data, list)


@patch('src.services.datetime')
def test_investment_bank_with_mock(mock_datetime, sample_transactions):
    """Тест с использованием mock."""
    mock_datetime.strptime.return_value = datetime(2023, 12, 1)
    result = investment_bank("2023-12", sample_transactions, 50)
    assert isinstance(result, float)

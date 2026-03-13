import json
from datetime import datetime, timedelta
from unittest.mock import patch

import pandas as pd
import pytest

from src.reports import spending_by_category, spending_by_weekday, report_decorator


def test_spending_by_category(sample_df):
    """Тест отчета по категориям."""
    result = spending_by_category(sample_df, "Супермаркеты")
    assert isinstance(result, pd.DataFrame)


def test_spending_by_weekday(sample_df):
    """Тест отчета по дням недели."""
    result = spending_by_weekday(sample_df)
    assert isinstance(result, dict)
    assert len(result) == 7


@pytest.mark.parametrize("category,expected_type", [
    ("Супермаркеты", pd.DataFrame),
    ("Рестораны", pd.DataFrame),
    ("Транспорт", pd.DataFrame),
])
def test_spending_by_category_parametrized(sample_df, category, expected_type):
    """Параметризованный тест отчета по категориям."""
    result = spending_by_category(sample_df, category)
    assert isinstance(result, expected_type)


def test_report_decorator():
    """Тест декоратора для отчетов."""

    @report_decorator()
    def test_func():
        return {"test": "data"}

    with patch('builtins.open') as mock_open:
        result = test_func()
        assert result == {"test": "data"}
        mock_open.assert_called_once()
        
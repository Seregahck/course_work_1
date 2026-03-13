our = 20
assert get_greeting() == "Добрый вечер"

mock_datetime.now.return_value.hour = 2
assert get_greeting() == "Доброй ночи"


def test_get_cards_info(sample_df):
    """Тест получения информации по картам."""
    cards = get_cards_info(sample_df)
    assert isinstance(cards, list)
    if cards:
        assert "last_digits" in cards[0]
        assert "total_spent" in cards[0]
        assert "cashback" in cards[0]


def test_get_top_transactions(sample_df):
    """Тест получения топ-транзакций."""
    top = get_top_transactions(sample_df, 3)
    assert len(top) <= 3
    if top:
        assert "date" in top[0]
        assert "amount" in top[0]
        assert "category" in top[0]


@patch('src.views.load_transactions')
@patch('src.views.get_currency_rates')
@patch('src.views.get_stock_prices')
def test_main_page(mock_stocks, mock_currency, mock_load, sample_df):
    """Тест главной страницы."""
    mock_load.return_value = sample_df
    mock_currency.return_value = [{"currency": "USD", "rate": 75.0}]
    mock_stocks.return_value = [{"stock": "AAPL", "price": 150.0}]

    result = main_page("2023-12-20 15:30:00")
    data = json.loads(result)

    assert "greeting" in data
    assert "cards" in data
    assert "top_transactions" in data
    assert "currency_rates" in data
    assert "stock_prices" in data

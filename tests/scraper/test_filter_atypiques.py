from scraper.scrape_atypiques import calculate_price_square_meter

def test_calculate_price_square_meter():
    assert calculate_price_square_meter(500000, 100) == 5000.0
    assert calculate_price_square_meter("500000 €", "100 m²") == 5000.0
    assert calculate_price_square_meter(None, 100) is None
    assert calculate_price_square_meter(500000, None) is None
    assert calculate_price_square_meter(None, None) is None

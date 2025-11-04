from utils.cleaning import extract_number

def test_extract_number():
    # On teste les nombres simples
    assert extract_number("250 000 €") == 250000.0
    assert extract_number("1 200 000") == 1200000.0
    assert extract_number("3500000") == 3500000.0
    assert extract_number("450.75") == 450.75


    # On test avec des virgules et des points
    assert extract_number("1,200.50 €") == 1200.50
    assert extract_number("2.500,75 €") == 2500.75
    assert extract_number("1.500.000") == 1500000
    assert extract_number("1,500,000") == 1500000
    assert extract_number("3.000.000,75") == 3000000.75
    assert extract_number("3,000,000.75") == 3000000.75
    assert extract_number("31 000,00") == 31000.00
    
    # On test les abréviations k/K et m/M
    assert extract_number("300k") == 300000.0
    assert extract_number("1.5K€") == 1500.0
    assert extract_number("1.5k€") == 1500.0
    assert extract_number("450K€") == 450000.0
    assert extract_number("1.2M") == 1200000.0
    assert extract_number("2,5m €") == 2500000.0
    
    # On test la suppression des caractères
    assert extract_number("450.75 m²") == 450.75
    assert extract_number("450 m2") == 450.0
    assert extract_number("450M2") == 450.0
    assert extract_number("450,75 m²") == 450.75
    assert extract_number("450m €/m²") == 450000000.0
    assert extract_number("300 €/m2") == 300.0
    assert extract_number("1.2M €/m²") == 1200000.0
    assert extract_number("300k€/m²") == 300000.0
    assert extract_number("73,1k €/m²") == 73100.0
    assert extract_number("674.000 €") == 674000

    # On teste avec un résultat invalide
    assert extract_number("Une chaine de caractère") is None
    assert extract_number("N/A") is None
    assert extract_number("") is None



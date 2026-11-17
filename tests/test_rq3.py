import pytest

from src.rq3 import extract_numbers, fertility, normalize_digits, number_preservation


def test_native_digits_normalised():
    assert normalize_digits("०.०५ ১২ ੩੪ ୫୬") == "0.05 12 34 56"   # Devanagari, Bengali, Gurmukhi, Odia


def test_extract_numbers_separators():
    c = extract_numbers("n = 1,234 patients; p < 0.05; ages 12, 15 and 12.")
    assert c == {"1,234": 1, "0.05": 1, "12": 2, "15": 1}


def test_preservation_multiset_and_native_digits():
    src = "Mortality fell from 12% to 8% (p = 0.03) in 120 patients."
    tgt = "मृत्यु दर १२% से घटकर ८% हो गई (p = ०.०३) 102 रोगियों में।"   # 120 corrupted to 102
    r = number_preservation(src, tgt)
    assert r["n_source"] == 4 and r["n_preserved"] == 3 and r["rate"] == pytest.approx(0.75)


def test_preservation_no_numbers():
    assert number_preservation("No numbers here.", "anything")["rate"] is None


def test_fertility():
    assert fertility(300, 100) == 3.0
    with pytest.raises(ValueError):
        fertility(10, 0)

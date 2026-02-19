from apps.shared.african_languages import get_country_languages
import pytest


def test_get_country_languages_ghana():
    languages = get_country_languages("Ghana")
    assert "Akan" in languages
    assert "Ewe" in languages


def test_get_country_languages_brazil():
    languages = get_country_languages("Brazil")
    assert "Portuguese" in languages


def test_get_country_languages_unknown():
    with pytest.raises(KeyError):
        get_country_languages("Atlantis")

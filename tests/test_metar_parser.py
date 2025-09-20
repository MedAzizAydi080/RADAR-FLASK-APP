"""Unit tests for METAR parsing helpers in ``app.py``."""

import pytest

from app import parse_metar, validate_icao


@pytest.mark.parametrize(
    "metar, expected_phrases",
    [
        (
            "KJFK 051651Z 18015G25KT 10SM FEW025 SCT080 BKN250 28/19 A2992",
            [
                "few clouds at 2500 ft",
                "scattered clouds at 8000 ft",
                "broken clouds at 25000 ft",
                "Temperature 28°C",
                "Dew point 19°C",
                "Wind from the south (180°) at 15 kt, gusting to 25 kt",
                "Visibility 10 statute miles",
                "Pressure 1013 hPa",
            ],
        ),
        (
            "EGLL 051650Z 27015KT 8000 BKN020 M05/M10 Q1020",
            [
                "broken clouds at 2000 ft",
                "Temperature -5°C",
                "Dew point -10°C",
                "Wind from the west (270°) at 15 kt",
                "Pressure 1020 hPa",
            ],
        ),
        (
            "KDEN 051651Z VRB03KT 5SM BR OVC002 04/03 A3010",
            [
                "overcast at 200 ft",
                "Temperature 4°C",
                "Dew point 3°C",
                "Variable winds at 3 kt",
                "Visibility 5 statute miles",
                "Weather: mist",
            ],
        ),
    ],
)
def test_parse_metar_translates_known_reports(metar: str, expected_phrases: list[str]) -> None:
    """Ensure ``parse_metar`` surfaces human-readable phrases for mock METARs."""

    result = parse_metar(metar)
    for phrase in expected_phrases:
        assert phrase in result


def test_parse_metar_handles_empty_reports() -> None:
    """A missing METAR should return a generic error string."""

    assert parse_metar("") == "Unable to parse METAR report."


@pytest.mark.parametrize(
    "code, expected",
    [
        ("KJFK", True),
        ("lfpg", True),
        ("ABC", False),
        ("ABCDE", False),
        ("12AB", False),
    ],
)
def test_validate_icao_input(code: str, expected: bool) -> None:
    """Validate that ICAO codes must be four alphabetic characters."""

    assert validate_icao(code) is expected

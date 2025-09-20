import re
from typing import List, Optional

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

API_URL = "https://aviationweather.gov/api/data/metar"
ICAO_PATTERN = re.compile(r"^[A-Za-z]{4}$")
WIND_PATTERN = re.compile(r"^(?P<direction>\d{3}|VRB)(?P<speed>\d{2,3})(G(?P<gust>\d{2,3}))?KT$")
TEMP_PATTERN = re.compile(r"^(?P<temp>M?\d{2})/(?P<dew>M?\d{2})$")
ALTIMETER_PATTERN = re.compile(r"^(A|Q)(?P<value>\d{4})$")

CLOUD_COVER_MAP = {
    "SKC": "clear sky",
    "CLR": "clear sky",
    "CAVOK": "ceiling and visibility OK",
    "FEW": "few clouds",
    "SCT": "scattered clouds",
    "BKN": "broken clouds",
    "OVC": "overcast",
}

WEATHER_CODES = {
    "RA": "rain",
    "DZ": "drizzle",
    "SN": "snow",
    "TS": "thunderstorm",
    "BR": "mist",
    "FG": "fog",
    "HZ": "haze",
    "FU": "smoke",
    "SG": "snow grains",
    "PL": "ice pellets",
    "GR": "hail",
    "GS": "small hail",
    "SS": "sandstorm",
    "DS": "duststorm",
}

CARDINAL_DIRECTIONS = [
    "north",
    "north-northeast",
    "northeast",
    "east-northeast",
    "east",
    "east-southeast",
    "southeast",
    "south-southeast",
    "south",
    "south-southwest",
    "southwest",
    "west-southwest",
    "west",
    "west-northwest",
    "northwest",
    "north-northwest",
]


def validate_icao(code: str) -> bool:
    return bool(ICAO_PATTERN.match(code))


def fetch_metar(icao_code: str) -> str:
    params = {"ids": icao_code, "format": "raw"}
    try:
        response = requests.get(API_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Unable to reach METAR service: {exc}") from exc

    reports = [line.strip() for line in response.text.splitlines() if line.strip()]
    if not reports:
        raise ValueError("No METAR report found for that station.")

    # Return the first report that starts with the ICAO code if available
    for report in reports:
        if report.upper().startswith(icao_code):
            return report

    return reports[0]


def parse_metar(raw_metar: str) -> str:
    if not raw_metar:
        return "Unable to parse METAR report."

    tokens = raw_metar.split()
    phrases: List[str] = []

    sky_phrases = _extract_sky_conditions(tokens)
    if sky_phrases:
        phrases.extend(sky_phrases)

    temp_phrase = _extract_temperature(tokens)
    if temp_phrase:
        phrases.append(temp_phrase)

    dew_phrase = _extract_dew_point(tokens)
    if dew_phrase:
        phrases.append(dew_phrase)

    wind_phrase = _extract_wind(tokens)
    if wind_phrase:
        phrases.append(wind_phrase)

    visibility_phrase = _extract_visibility(tokens)
    if visibility_phrase:
        phrases.append(visibility_phrase)

    pressure_phrase = _extract_pressure(tokens)
    if pressure_phrase:
        phrases.append(pressure_phrase)

    weather_phrase = _extract_weather(tokens)
    if weather_phrase:
        phrases.append(weather_phrase)

    return ", ".join(_deduplicate_preserve_order(phrases)) if phrases else "Unable to parse METAR report."


def _extract_sky_conditions(tokens: List[str]) -> List[str]:
    conditions: List[str] = []
    for token in tokens:
        if token in {"NIL", "AUTO", "COR"}:
            continue
        if token == "CAVOK":
            conditions.append("Ceiling and visibility OK")
            continue

        coverage_code = token[:3]
        if coverage_code in CLOUD_COVER_MAP and token[3:6].isdigit():
            height = int(token[3:6]) * 100
            description = CLOUD_COVER_MAP[coverage_code]
            conditions.append(f"{description} at {height} ft")
        elif token in {"SKC", "CLR"}:
            if "Clear sky" not in conditions:
                conditions.append("Clear sky")
    return conditions


def _extract_temperature(tokens: List[str]) -> Optional[str]:
    for token in tokens:
        match = TEMP_PATTERN.match(token)
        if match:
            temp = _decode_temperature(match.group("temp"))
            return f"Temperature {temp}\u00b0C"
    return None


def _extract_dew_point(tokens: List[str]) -> Optional[str]:
    for token in tokens:
        match = TEMP_PATTERN.match(token)
        if match:
            dew = _decode_temperature(match.group("dew"))
            return f"Dew point {dew}\u00b0C"
    return None


def _decode_temperature(value: str) -> int:
    return -int(value[1:]) if value.startswith("M") else int(value)


def _extract_wind(tokens: List[str]) -> Optional[str]:
    for token in tokens:
        match = WIND_PATTERN.match(token)
        if match:
            direction = match.group("direction")
            speed = int(match.group("speed"))
            gust = match.group("gust")

            if speed == 0:
                return "Calm winds"

            if direction == "VRB":
                direction_phrase = "Variable winds"
            else:
                direction_degrees = int(direction)
                direction_phrase = f"Wind from the { _degrees_to_cardinal(direction_degrees) } ({direction_degrees}\u00b0)"

            gust_phrase = f", gusting to {int(gust)} kt" if gust else ""
            return f"{direction_phrase} at {speed} kt{gust_phrase}"
    return None


def _degrees_to_cardinal(degrees: int) -> str:
    index = int((degrees % 360) / 22.5 + 0.5) % len(CARDINAL_DIRECTIONS)
    return CARDINAL_DIRECTIONS[index]


def _extract_visibility(tokens: List[str]) -> Optional[str]:
    for token in tokens:
        if token.endswith("SM"):
            miles = _convert_visibility_to_float(token)
            if miles is None:
                continue
            return f"Visibility {miles:g} statute miles"
    return None


def _convert_visibility_to_float(token: str) -> Optional[float]:
    try:
        value = token[:-2]  # remove 'SM'
        if value.startswith("P"):
            value = value[1:]
        if " " in value:
            whole, frac = value.split(" ")
            return float(whole) + _fraction_to_float(frac)
        if "/" in value:
            return _fraction_to_float(value)
        return float(value)
    except ValueError:
        return None


def _fraction_to_float(value: str) -> float:
    numerator, denominator = value.split("/")
    return int(numerator) / int(denominator)


def _extract_pressure(tokens: List[str]) -> Optional[str]:
    for token in tokens:
        match = ALTIMETER_PATTERN.match(token)
        if not match:
            continue
        prefix = token[0]
        value = int(match.group("value"))
        if prefix == "A":
            inches = value / 100.0
            hpa = round(inches * 33.8639)
            return f"Pressure {hpa} hPa"
        if prefix == "Q":
            return f"Pressure {value} hPa"
    return None


def _extract_weather(tokens: List[str]) -> Optional[str]:
    phenomena: List[str] = []
    for token in tokens:
        for code, description in WEATHER_CODES.items():
            if token.endswith(code):
                modifiers = token[:-len(code)]
                intensity = _decode_intensity(modifiers)
                phenomena.append(f"{intensity}{description}")
                break
    if phenomena:
        cleaned = [item.replace("  ", " ").strip() for item in phenomena]
        return "Weather: " + ", ".join(cleaned)
    return None


def _decode_intensity(modifier: str) -> str:
    if modifier == "-":
        return "Light "
    if modifier == "+":
        return "Heavy "
    if modifier == "VC":
        return "In the vicinity: "
    return ""


def _deduplicate_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


@app.route('/', methods=['GET', 'POST'])
def index():
    raw_metar = ""
    translated = ""
    error = ""

    if request.method == 'POST':
        icao_code = request.form.get('icao', '').strip().upper()

        if not validate_icao(icao_code):
            error = "Please enter a valid 4-letter ICAO code."
        else:
            try:
                raw_metar = fetch_metar(icao_code)
                translated = parse_metar(raw_metar)
            except (RuntimeError, ValueError) as exc:
                error = str(exc)

    return render_template('index.html', raw_metar=raw_metar, translated=translated, error=error)


if __name__ == '__main__':
    app.run(debug=True)

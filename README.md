# RADAR Flask App

A lightweight Flask web application that fetches raw METAR reports from the Aviation Weather Center and translates them into plain language. Enter any four-letter ICAO airport code to receive both the original report and a human-friendly summary of the current conditions.

## Features
- Validates ICAO identifiers before making a request.
- Retrieves live METAR data from aviationweather.gov.
- Breaks forecasts down into readable wind, sky, pressure, visibility, and weather details.
- Provides immediate feedback when stations are offline or codes are invalid.

## Prerequisites
- Python 3.9 or newer
- `pip` package manager
- (Optional) A virtual environment tool such as `venv` or `virtualenv`

## Installation
```bash
# 1. Clone the repository
 git clone https://github.com/MedAzizAydi080/RADAR-FLASK-APP.git
 cd RADAR-FLASK-APP

# 2. Create and activate a virtual environment (recommended)
 python -m venv .venv
 source .venv/bin/activate    # On Windows use: .venv\\Scripts\\activate

# 3. Install dependencies
 pip install -r requirements.txt
```

## Usage
```bash
# Start the Flask development server
 python app.py
```

Visit http://127.0.0.1:5000/ in your browser, enter a four-letter ICAO code (e.g. `KJFK` or `LFPG`), and submit to be redirected to a detailed report page showing both the raw METAR and the translated summary. The bundled development server runs with `debug=True`; disable this flag or deploy behind a production-ready WSGI server when releasing publicly.

## Project Structure
- `app.py` – Flask application, METAR parser, and helpers
- `templates/index.html` – ICAO search form
- `templates/report.html` – Raw and translated METAR output
- `requirements.txt` – Python dependencies

## Contributing
Issues and pull requests are welcome. If you make changes, please include clear commit messages and consider adding tests or sample reports where helpful.

## License
Choose and publish a license before tagging a public release so that contributors know how their work will be used.

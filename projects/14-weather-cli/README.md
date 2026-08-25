# 14 — Weather CLI with Retry

Isolated beginner project from the `basicthon` series (Data & Algorithms).

**What you learn (lock scope):** fetching weather over HTTP, handling API keys and URLs via environment variables, and retrying with exponential backoff on transient failures. The project is built in three stages: minimal — `get_api_key`/`get_api_url`/`fetch_weather` with `httpx` over a JSON API; improved — city validation, JSON shape checks, retry on 429/5xx with `time.sleep` exponential backoff, error handling; production-like — typed, tested, `ruff/black/mypy --strict` clean, `argparse` CLI with `unittest.mock`-based tests.

## Installation

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` contains `httpx==0.27.2` (pinned, see Stages for why).

## Usage

Export API credentials (or put into `.env`, see `.env.example`):

```bash
# Linux/macOS
export API_URL="https://api.example.com/weather"
export API_KEY="your-api-key-here"
# Windows PowerShell
$env:API_URL="https://api.example.com/weather"
$env:API_KEY="your-api-key-here"

# Or pass explicitly
python -m weather_cli London --api-url https://api.example.com/weather --api-key your-key
```

Fetch weather (retries on 429, 500, 502, 503, 504 with exponential backoff):

```bash
python -m weather_cli London
# London: 15.5°C, clear sky, humidity 72%

python -m weather_cli "New York" --api-key mykey --api-url https://api.example.com
# New York: 22.0°C, cloudy

# custom retry settings
python -m weather_cli Berlin --retries 5 --backoff 1.0
# Berlin: 18.0°C, sunny, humidity 60%
```

Or use console script after `pip install -e .`:

```bash
weather-cli London
weather-cli Paris --api-url https://api.example.com --api-key mykey
weather-cli Tokyo --retries 2 --backoff 0.5
```

Use as a library:

```python
from weather_cli import fetch_weather, get_api_key, get_api_url

# read credentials from env
api_key = get_api_key()  # reads $API_KEY, strips, validates
api_url = get_api_url()  # reads $API_URL

weather = fetch_weather("London", api_key=api_key, api_url=api_url)
print(weather)
# {'city': 'London', 'temperature': 15.5, 'description': 'clear sky', 'humidity': 72}

# explicit credentials without env, with retry tuning
print(fetch_weather("Paris", api_key="mykey", api_url="https://api.example.com"))
# {'city': 'Paris', 'temperature': 20.0, 'description': 'cloudy'}

# retry: 3 attempts, backoff 0.5s -> sleeps 0.5, 1.0 on 429/5xx or network error
print(fetch_weather("Berlin", api_key="k", api_url="https://api.example.com", max_retries=3, backoff_factor=0.5))
```

Details:

- `get_api_key(var_name="API_KEY") -> str` reads `os.environ`, strips, raises `ValueError` if missing/empty; validates `var_name` itself.
- `get_api_url(var_name="API_URL") -> str` same for URL, raises `ValueError` if missing/empty.
- `fetch_weather(city, api_key=None, api_url=None, max_retries=3, backoff_factor=0.5) -> dict[str, str | float | int]` validates `city` is non-empty trimmed string up to 100 chars, resolves `api_key`/`api_url` from args or env (validates `http://`/`https://` for URL), validates `max_retries` 1..10 and `backoff_factor` finite >=0, does `httpx.get(url, params={"q": city, "appid": key, "units": "metric"}, headers={"apikey": key}, timeout=10.0)` in a loop up to `max_retries`, retrying on network exceptions and statuses 429/500/502/503/504 with `time.sleep(backoff_factor * 2**attempt)`; on 200 parses JSON, accepts `name` or `city` for city name, requires `main.temp` finite number and `weather[0].description` non-empty string, optional `main.humidity` 0..100, returns `{"city": str, "temperature": float, "description": str, "humidity": int?}`; other 4xx raises `ValueError` without retry.

API response example (`GET https://api.example.com/weather?q=London&appid=KEY&units=metric`):

```json
{
  "name": "London",
  "main": {
    "temp": 15.5,
    "humidity": 72
  },
  "weather": [
    {
      "description": "clear sky"
    }
  ]
}
```

Alternative city key also accepted: `{"city": "London", "main": {"temp": 15.5}, "weather": [{"description": "clear sky"}]}`.

## Stages

**Minimal:** `get_api_key`/`get_api_url` via `os.environ.get` with `strip` and `ValueError` if missing, `fetch_weather` with `httpx.get(params={"q": city, "appid": key})` and `response.json()` handling, basic `city.strip()` validation, return of `city`/`temp`/`description`.

**Improved:** `fetch_weather` validates JSON shape strictly (top-level dict, `name`/`city` string, `main` dict with finite `temp`, `weather` list with `description`, optional `humidity` 0..100), checks `status_code != 200` → retry or `ValueError`, wraps `httpx` exceptions as retryable, validates explicit `api_key`/`api_url` (non-empty, URL must start with `http`), `_validate_city` length check, `_validate_max_retries` 1..10, `_validate_backoff_factor` finite >=0, `.env.example` documenting `API_URL`/`API_KEY`, support for both `name` and `city` keys, retryable statuses {429, 500, 502, 503, 504} with exponential backoff `backoff_factor * 2**attempt` via `time.sleep`.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy --strict` clean (strict for 11–20 per ARCHITECTURE.md §8), `pytest` green for every public function in `src/weather_cli/weather.py` (excl. `cli.py` per §5) using `unittest.mock.patch` for `httpx.get` and `time.sleep` plus `monkeypatch` for env, no network, no real API key, `argparse` CLI with `city` plus `--api-key`/`--api-url`/`--retries`/`--backoff` (fallback to `$API_KEY`/`$API_URL`), `python -m weather_cli` entry point, `.env.example` present per GRILL2-06 §4.

## API

```python
from weather_cli import get_api_key, get_api_url, fetch_weather

get_api_key(var_name: str = "API_KEY") -> str
get_api_url(var_name: str = "API_URL") -> str
fetch_weather(city: str, api_key: str | None = None, api_url: str | None = None, max_retries: int = 3, backoff_factor: float = 0.5) -> dict[str, str | float | int]
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## ZuroKing's note

> Beginners think weather is just `temp = 15.5`. Show the gap: real data lives behind an API, needs a key outside code, a URL you don't hardcode, and a network that can fail transiently. Keep the boundary sharp: `weather.py` knows only `os.environ` + `httpx` + `time.sleep` + validation, no `argparse`, no `print`. Retry only what is retryable — 429 and 500/502/503/504 plus network exceptions — with exponential backoff `backoff_factor * 2**attempt`, fail fast on 400/401/404, and parse JSON strictly (accept `name` or `city`, require finite `temp` and non-empty `description`). Then your CLI is just `parse_args → fetch_weather → print`, and tests stay honest with `unittest.mock.patch("weather_cli.weather.httpx.get")` and `patch("weather_cli.weather.time.sleep")` — deterministic, no network, no real key, and you can assert sleeps are 0.5, 1.0, 2.0.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.

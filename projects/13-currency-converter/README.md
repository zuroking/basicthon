# 13 — Currency Converter

Isolated beginner project from the `basicthon` series (Data & Algorithms).

**What you learn (lock scope):** fetching live exchange rates over HTTP, handling API keys and URLs via environment variables, and converting currencies with validation and mocked tests. The project is built in three stages: minimal — `get_api_key`/`get_api_url`/`fetch_rates`/`convert` with `httpx` over a JSON API; improved — currency-code validation, amount checks, `rates`/`conversion_rates` fallback, HTTP and JSON error handling; production-like — typed, tested, `ruff/black/mypy --strict` clean, `argparse` CLI with `unittest.mock`-based tests.

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
export API_URL="https://api.example.com/latest"
export API_KEY="your-api-key-here"
# Windows PowerShell
$env:API_URL="https://api.example.com/latest"
$env:API_KEY="your-api-key-here"

# Or pass explicitly
python -m currency_converter 100 USD EUR --api-url https://api.example.com/latest --api-key your-key
```

Convert currencies (fetches rates with `base = from_currency`):

```bash
python -m currency_converter 100 USD EUR
# 100.0 USD = 92.0 EUR

python -m currency_converter 50 eur JPY --api-key mykey --api-url https://api.example.com
# 50.0 EUR = 8150.0 JPY

# same currency — no network
python -m currency_converter 10 USD USD
# 10.0 USD = 10.0 USD
```

Or use console script after `pip install -e .`:

```bash
currency-converter 100 USD EUR
currency-converter 200 USD GBP --api-url https://api.example.com --api-key mykey
```

Use as a library:

```python
from currency_converter import fetch_rates, convert, get_api_key, get_api_url

# read credentials from env
api_key = get_api_key()  # reads $API_KEY, strips, validates
api_url = get_api_url()  # reads $API_URL

rates = fetch_rates("USD", api_key=api_key, api_url=api_url)
print(rates)
# {'EUR': 0.92, 'GBP': 0.79, 'JPY': 150.0}

print(convert(100, "USD", "EUR", api_key=api_key, api_url=api_url))
# 92.0

# explicit credentials without env
print(convert(10, "USD", "EUR", api_key="mykey", api_url="https://api.example.com"))
# 9.2

# same currency shortcut — no fetch
print(convert(5, "EUR", "EUR", api_key=api_key, api_url=api_url))
# 5.0
```

Details:

- `get_api_key(var_name="API_KEY") -> str` reads `os.environ`, strips, raises `ValueError` if missing/empty; validates `var_name` itself.
- `get_api_url(var_name="API_URL") -> str` same for URL, raises `ValueError` if missing/empty.
- `fetch_rates(base_currency, api_key=None, api_url=None) -> dict[str, float]` validates `base_currency` is 3-letter alpha (case-insensitive, normalized to upper), resolves `api_key`/`api_url` from args or env (validates `http://`/`https://` for URL), does `httpx.get(url, params={"base": base}, headers={"apikey": key}, timeout=10.0)`, checks `status_code == 200`, parses JSON, accepts `rates` or `conversion_rates`, validates each key is 3-letter code and each value is finite positive number (int/float, not bool), returns `{code.upper(): float(rate)}`.
- `convert(amount, from_currency, to_currency, api_key=None, api_url=None) -> float` validates `amount` is `int|float` (not `bool`, finite), validates currency codes, if `from == to` returns `float(amount)` without network, else `fetch_rates(from_currency)` and returns `amount * rates[to_currency]` or raises `ValueError("unsupported currency: ...")` if missing.

API response example (`GET https://api.example.com/latest?base=USD`):

```json
{
  "base": "USD",
  "rates": {
    "EUR": 0.92,
    "GBP": 0.79
  }
}
```

Alternative shape also accepted: `{"conversion_rates": {"EUR": 0.92}}`.

## Stages

**Minimal:** `get_api_key`/`get_api_url` via `os.environ.get` with `strip` and `ValueError` if missing, `fetch_rates` with `httpx.get(params={"base": base}, headers={"apikey": key})` and `response.json()` handling, `convert` multiplying `amount * rate` with base fetch; validation `code.strip().upper()` 3 letters.

**Improved:** `fetch_rates` handles both `rates` and `conversion_rates` keys, validates rate dict shape (keys `str`, values `int|float`, finite `>0`, rejects `bool`), checks `status_code != 200` → `ValueError`, wraps `httpx` exceptions as `ValueError`, validates explicit `api_key`/`api_url` (non-empty, URL must start with `http`), `_validate_amount` rejects `bool`/`nan`/`inf`, `_validate_currency` for all entry points, `.env.example` documenting `API_URL`/`API_KEY`, case-insensitive handling for inputs and rate keys.

**Production-like:** Type hints on all public functions, `ruff`/`black`/`mypy --strict` clean (strict for 11–20 per ARCHITECTURE.md §8), `pytest` green for every public function in `src/currency_converter/converter.py` (excl. `cli.py` per §5) using `unittest.mock.patch` for `httpx.get` and `monkeypatch` for env, no network, no real API key, `argparse` CLI with `amount from_currency to_currency` plus `--api-key`/`--api-url` (fallback to `$API_KEY`/`$API_URL`), `python -m currency_converter` entry point, `.env.example` present per GRILL2-06 §4.

## API

```python
from currency_converter import get_api_key, get_api_url, fetch_rates, convert

get_api_key(var_name: str = "API_KEY") -> str
get_api_url(var_name: str = "API_URL") -> str
fetch_rates(base_currency: str, api_key: str | None = None, api_url: str | None = None) -> dict[str, float]
convert(amount: float | int, from_currency: str, to_currency: str, api_key: str | None = None, api_url: str | None = None) -> float
```

## Testing

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## ZuroKing's note

> Beginners think currency conversion is just `amount * 0.92`. Show the gap: real rates live behind an API, need a key outside code, a URL you don't hardcode, and a network that can fail. Keep the boundary sharp: `converter.py` knows only `os.environ` + `httpx` + validation, no `argparse`, no `print`. Parse the JSON strictly — accept `rates` or `conversion_rates`, reject non-dict, non-numeric or non-positive rates, and turn every `status != 200` or `httpx` exception into a clear `ValueError`. Let `convert` be trivial when `from == to` (no fetch) and otherwise `fetch_rates(from) → multiply`. Then your CLI is just `parse_args → convert → print`, and tests stay honest with `unittest.mock.patch("currency_converter.converter.httpx.get")` — deterministic, no network, no real key.

## Isolation

This folder is self-contained — copy it anywhere and `pip install -e . && pip install -r requirements.txt` is enough. No shared code with other `basicthon` projects.

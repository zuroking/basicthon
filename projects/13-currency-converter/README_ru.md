# 13 — Конвертер валют

Изолированный учебный проект из серии `basicthon` (Data & Algorithms).

**Что изучаем (lock scope):** получение курсов валют по HTTP, хранение API-ключа и URL в переменных окружения и конвертация с валидацией и моками в тестах. Проект в три этапа: minimal — `get_api_key`/`get_api_url`/`fetch_rates`/`convert` на `httpx` поверх JSON API; improved — валидация кодов валют, проверка суммы, поддержка `rates`/`conversion_rates`, обработка HTTP и JSON ошибок; production-like — типизация, тесты, `ruff/black/mypy --strict`, CLI на `argparse` с тестами через `unittest.mock`.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` содержит `httpx==0.27.2` (пиннинг, см. Этапы).

## Использование

Экспортируйте учётные данные (или добавьте в `.env`, см. `.env.example`):

```bash
# Linux/macOS
export API_URL="https://api.example.com/latest"
export API_KEY="ваш-ключ"
# Windows PowerShell
$env:API_URL="https://api.example.com/latest"
$env:API_KEY="ваш-ключ"

# или передавайте явно
python -m currency_converter 100 USD EUR --api-url https://api.example.com/latest --api-key ваш-ключ
```

Конвертация (запрашивает курс с `base = from_currency`):

```bash
python -m currency_converter 100 USD EUR
# 100.0 USD = 92.0 EUR

python -m currency_converter 50 eur JPY --api-key mykey --api-url https://api.example.com
# 50.0 EUR = 8150.0 JPY

# одинаковая валюта — без сети
python -m currency_converter 10 USD USD
# 10.0 USD = 10.0 USD
```

После `pip install -e .`:

```bash
currency-converter 100 USD EUR
currency-converter 200 USD GBP --api-url https://api.example.com --api-key mykey
```

Как библиотека:

```python
from currency_converter import fetch_rates, convert, get_api_key, get_api_url

api_key = get_api_key()  # читает $API_KEY
api_url = get_api_url()  # читает $API_URL

rates = fetch_rates("USD", api_key=api_key, api_url=api_url)
print(rates)
# {'EUR': 0.92, 'GBP': 0.79}

print(convert(100, "USD", "EUR", api_key=api_key, api_url=api_url))
# 92.0

# явные параметры без env
print(convert(10, "USD", "EUR", api_key="mykey", api_url="https://api.example.com"))
# 9.2

# одинаковая валюта — без запроса
print(convert(5, "EUR", "EUR", api_key=api_key, api_url=api_url))
# 5.0
```

Детали:

- `get_api_key(var_name="API_KEY") -> str` — читает `os.environ`, стрипует, бросает `ValueError` если пусто/нет; валидирует `var_name`.
- `get_api_url(var_name="API_URL") -> str` — то же для URL.
- `fetch_rates(base_currency, api_key=None, api_url=None) -> dict[str, float]` — валидирует `base_currency` как 3 буквы (без учёта регистра, нормализует к upper), резолвит ключ/URL из аргументов или env (проверяет `http://`/`https://`), делает `httpx.get(url, params={"base": base}, headers={"apikey": key}, timeout=10.0)`, проверяет `status_code == 200`, парсит JSON, принимает `rates` или `conversion_rates`, валидирует каждый ключ — 3 буквы и каждое значение — конечное положительное число, возвращает `{code: float}`.
- `convert(amount, from_currency, to_currency, api_key=None, api_url=None) -> float` — валидирует `amount` как `int|float` (не `bool`, конечное), валидирует коды, если `from == to` возвращает `float(amount)` без сети, иначе `fetch_rates(from)` и `amount * rates[to]` или `ValueError("unsupported currency: ...")`.

Пример ответа API (`GET https://api.example.com/latest?base=USD`):

```json
{
  "base": "USD",
  "rates": {
    "EUR": 0.92,
    "GBP": 0.79
  }
}
```

Альтернативная форма тоже поддерживается: `{"conversion_rates": {"EUR": 0.92}}`.

## Этапы

**Minimal:** `get_api_key`/`get_api_url` через `os.environ.get` с `strip` и `ValueError`, `fetch_rates` с `httpx.get(params={"base": base}, headers={"apikey": key})` и `response.json()`, `convert` как `amount * rate`; валидация `code.strip().upper()` 3 буквы.

**Improved:** поддержка обоих ключей `rates`/`conversion_rates`, валидация формы словаря (ключи `str`, значения `int|float`, конечные `>0`, отказ от `bool`), проверка `status_code != 200` → `ValueError`, обёртка исключений `httpx` в `ValueError`, валидация явных `api_key`/`api_url` (не пустые, URL с `http`), `_validate_amount` против `bool`/`nan`/`inf`, `_validate_currency` везде, `.env.example` с `API_URL`/`API_KEY`, case-insensitive для входов и ключей ответа.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy --strict` без ошибок (strict для 11–20 по §8 ARCHITECTURE.md), `pytest` зелёный для каждой публичной функции в `src/currency_converter/converter.py` (кроме `cli.py` по §5) с `unittest.mock.patch` для `httpx.get` и `monkeypatch` для env, без сети и реального ключа, CLI на `argparse` с `amount from_currency to_currency` и `--api-key`/`--api-url` (фолбэк на env), точка входа `python -m currency_converter`, `.env.example` по GRILL2-06 §4.

## API

```python
from currency_converter import get_api_key, get_api_url, fetch_rates, convert

get_api_key(var_name: str = "API_KEY") -> str
get_api_url(var_name: str = "API_URL") -> str
fetch_rates(base_currency: str, api_key: str | None = None, api_url: str | None = None) -> dict[str, float]
convert(amount: float | int, from_currency: str, to_currency: str, api_key: str | None = None, api_url: str | None = None) -> float
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## Заметка от ZuroKing

> Новички думают, что конвертация — это просто `сумма * 0.92`. Покажите разрыв: реальные курсы живут за API, требуют ключ вне кода, URL который не хардкодят, и сеть которая может упасть. Держите границу жёстко: `converter.py` знает только `os.environ` + `httpx` + валидацию, никакого `argparse` и `print`. Парсите JSON строго — примите `rates` или `conversion_rates`, отклоните не-словарь, не-число или неположительный курс, и превращайте каждый `status != 200` или исключение `httpx` в понятный `ValueError`. Пусть `convert` при `from == to` не делает запрос, иначе `fetch_rates(from) → умножение`. Тогда CLI остаётся склейкой `parse_args → convert → print`, а тесты честны с `unittest.mock.patch("currency_converter.converter.httpx.get")` — детерминированно, без сети и без реального ключа.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.

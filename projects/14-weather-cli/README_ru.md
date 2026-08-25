# 14 — Погодный CLI с retry

Изолированный учебный проект из серии `basicthon` (Data & Algorithms).

**Что изучаем (lock scope):** получение погоды по HTTP, хранение API-ключа и URL в переменных окружения и повторные попытки с экспоненциальной задержкой при временных сбоях. Проект в три этапа: minimal — `get_api_key`/`get_api_url`/`fetch_weather` на `httpx` поверх JSON API; improved — валидация города, проверка формы JSON, retry на 429/5xx через `time.sleep` с экспоненциальным backoff, обработка ошибок; production-like — типизация, тесты, `ruff/black/mypy --strict`, CLI на `argparse` с тестами через `unittest.mock`.

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
export API_URL="https://api.example.com/weather"
export API_KEY="ваш-ключ"
# Windows PowerShell
$env:API_URL="https://api.example.com/weather"
$env:API_KEY="ваш-ключ"

# или передавайте явно
python -m weather_cli London --api-url https://api.example.com/weather --api-key ваш-ключ
```

Получение погоды (retry на 429, 500, 502, 503, 504 с экспоненциальным backoff):

```bash
python -m weather_cli London
# London: 15.5°C, clear sky, humidity 72%

python -m weather_cli "New York" --api-key mykey --api-url https://api.example.com
# New York: 22.0°C, cloudy

# настройка retry
python -m weather_cli Berlin --retries 5 --backoff 1.0
# Berlin: 18.0°C, sunny, humidity 60%
```

После `pip install -e .`:

```bash
weather-cli London
weather-cli Paris --api-url https://api.example.com --api-key mykey
weather-cli Tokyo --retries 2 --backoff 0.5
```

Как библиотека:

```python
from weather_cli import fetch_weather, get_api_key, get_api_url

api_key = get_api_key()  # читает $API_KEY
api_url = get_api_url()  # читает $API_URL

weather = fetch_weather("London", api_key=api_key, api_url=api_url)
print(weather)
# {'city': 'London', 'temperature': 15.5, 'description': 'clear sky', 'humidity': 72}

# явные параметры без env, с настройкой retry
print(fetch_weather("Paris", api_key="mykey", api_url="https://api.example.com"))
# {'city': 'Paris', 'temperature': 20.0, 'description': 'cloudy'}

# retry: 3 попытки, backoff 0.5с -> паузы 0.5, 1.0 при 429/5xx или ошибке сети
print(fetch_weather("Berlin", api_key="k", api_url="https://api.example.com", max_retries=3, backoff_factor=0.5))
```

Детали:

- `get_api_key(var_name="API_KEY") -> str` — читает `os.environ`, стрипует, бросает `ValueError` если пусто/нет; валидирует `var_name`.
- `get_api_url(var_name="API_URL") -> str` — то же для URL.
- `fetch_weather(city, api_key=None, api_url=None, max_retries=3, backoff_factor=0.5) -> dict[str, str | float | int]` — валидирует `city` как непустую строку до 100 символов, резолвит ключ/URL из аргументов или env (проверяет `http://`/`https://`), валидирует `max_retries` 1..10 и `backoff_factor` конечное >=0, делает `httpx.get(url, params={"q": city, "appid": key, "units": "metric"}, headers={"apikey": key}, timeout=10.0)` в цикле до `max_retries`, повторяя при исключениях сети и статусах 429/500/502/503/504 с `time.sleep(backoff_factor * 2**attempt)`; при 200 парсит JSON, принимает `name` или `city` как имя города, требует `main.temp` конечное число и `weather[0].description` непустую строку, опционально `main.humidity` 0..100, возвращает `{"city": str, "temperature": float, "description": str, "humidity": int?}`; другие 4xx бросают `ValueError` без повтора.

Пример ответа API (`GET https://api.example.com/weather?q=London&appid=KEY&units=metric`):

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

Альтернативная форма тоже поддерживается: `{"city": "London", "main": {"temp": 15.5}, "weather": [{"description": "clear sky"}]}`.

## Этапы

**Minimal:** `get_api_key`/`get_api_url` через `os.environ.get` с `strip` и `ValueError`, `fetch_weather` с `httpx.get(params={"q": city, "appid": key})` и `response.json()`, базовая валидация `city.strip()` не пусто, возврат `city`/`temp`/`description`.

**Improved:** строгая валидация JSON (словарь верхнего уровня, `name`/`city` строка, `main` с конечным `temp`, `weather` список с `description`, опционально `humidity` 0..100), проверка `status_code != 200` → retry или `ValueError`, обёртка исключений `httpx` как retryable, валидация явных `api_key`/`api_url` (не пустые, URL с `http`), `_validate_city` проверка длины, `_validate_max_retries` 1..10, `_validate_backoff_factor` конечное >=0, `.env.example` с `API_URL`/`API_KEY`, поддержка обоих ключей `name`/`city`, retry статусы {429, 500, 502, 503, 504} с экспоненциальным `backoff_factor * 2**attempt` через `time.sleep`.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy --strict` без ошибок (strict для 11–20 по §8 ARCHITECTURE.md), `pytest` зелёный для каждой публичной функции в `src/weather_cli/weather.py` (кроме `cli.py` по §5) с `unittest.mock.patch` для `httpx.get` и `time.sleep` и `monkeypatch` для env, без сети и реального ключа, CLI на `argparse` с `city` и `--api-key`/`--api-url`/`--retries`/`--backoff` (фолбэк на env), точка входа `python -m weather_cli`, `.env.example` по GRILL2-06 §4.

## API

```python
from weather_cli import get_api_key, get_api_url, fetch_weather

get_api_key(var_name: str = "API_KEY") -> str
get_api_url(var_name: str = "API_URL") -> str
fetch_weather(city: str, api_key: str | None = None, api_url: str | None = None, max_retries: int = 3, backoff_factor: float = 0.5) -> dict[str, str | float | int]
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## Заметка от ZuroKing

> Новички думают, что погода — это просто `temp = 15.5`. Покажите разрыв: реальные данные живут за API, требуют ключ вне кода, URL который не хардкодят, и сеть которая может упасть на секунду. Держите границу жёстко: `weather.py` знает только `os.environ` + `httpx` + `time.sleep` + валидацию, никакого `argparse` и `print`. Повторяйте только retryable — 429 и 500/502/503/504 плюс исключения сети — с экспоненциальным `backoff_factor * 2**attempt`, падайте сразу на 400/401/404, и парсите JSON строго (примите `name` или `city`, требуйте конечный `temp` и непустой `description`). Тогда CLI остаётся склейкой `parse_args → fetch_weather → print`, а тесты честны с `unittest.mock.patch("weather_cli.weather.httpx.get")` и `patch("weather_cli.weather.time.sleep")` — детерминированно, без сети и без реального ключа, и вы можете проверить что паузы 0.5, 1.0, 2.0.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.

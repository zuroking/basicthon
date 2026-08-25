"""Core logic for weather CLI.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded.

API contract:
    GET {API_URL} with query ``q`` (city), ``appid`` (key), ``units=metric``.
    Headers ``apikey`` also sent for compatibility.
    Response JSON expected to contain ``name`` (or ``city``), ``main`` with
    ``temp`` and optional ``humidity``, and ``weather`` list with
    ``description``:

    ``{"name": "London", "main": {"temp": 15.5, "humidity": 72},
      "weather": [{"description": "clear sky"}]}``

    Alternative shape with ``city`` instead of ``name`` is accepted.
    Values are validated as finite numbers and non-empty strings.

Uses ``os.environ`` for ``API_KEY``/``API_URL``, ``httpx`` for HTTP, and
``time.sleep`` with exponential backoff for retries.
"""

from __future__ import annotations

import math
import os
import time
from typing import Any

import httpx


def get_api_key(var_name: str = "API_KEY") -> str:
    """Return API key from environment variable.

    Args:
        var_name: name of env variable to read.

    Returns:
        Stripped key string.

    Raises:
        ValueError: if var_name invalid or variable missing/empty.
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must not be empty")
    value = os.environ.get(cleaned)
    if value is None or not value.strip():
        raise ValueError(f"environment variable {cleaned} is not set")
    return value.strip()


def get_api_url(var_name: str = "API_URL") -> str:
    """Return API URL from environment variable.

    Args:
        var_name: name of env variable to read.

    Returns:
        Stripped URL string.

    Raises:
        ValueError: if var_name invalid or variable missing/empty.
    """
    if not isinstance(var_name, str):
        raise ValueError("var_name must be a string")
    cleaned = var_name.strip()
    if not cleaned:
        raise ValueError("var_name must not be empty")
    value = os.environ.get(cleaned)
    if value is None or not value.strip():
        raise ValueError(f"environment variable {cleaned} is not set")
    return value.strip()


def _validate_city(city: str) -> str:
    """Validate city name and return stripped form.

    Raises:
        ValueError: if city is not a non-empty string.
    """
    if not isinstance(city, str):
        raise ValueError("city must be a string")
    cleaned = city.strip()
    if not cleaned:
        raise ValueError("city must not be empty")
    if len(cleaned) > 100:
        raise ValueError("city must be at most 100 characters")
    return cleaned


def _validate_api_key_value(key: str) -> str:
    """Validate explicit api_key argument."""
    if not isinstance(key, str):
        raise ValueError("api_key must be a string")
    cleaned = key.strip()
    if not cleaned:
        raise ValueError("api_key must not be empty")
    return cleaned


def _validate_api_url_value(url: str) -> str:
    """Validate explicit api_url argument."""
    if not isinstance(url, str):
        raise ValueError("api_url must be a string")
    cleaned = url.strip()
    if not cleaned:
        raise ValueError("api_url must not be empty")
    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        raise ValueError("api_url must start with http:// or https://")
    return cleaned


def _validate_max_retries(value: int) -> int:
    """Validate max_retries."""
    if isinstance(value, bool):
        raise ValueError("max_retries must be an integer")
    if not isinstance(value, int):
        raise ValueError("max_retries must be an integer")
    if value < 1 or value > 10:
        raise ValueError("max_retries must be between 1 and 10")
    return value


def _validate_backoff_factor(value: float | int) -> float:
    """Validate backoff_factor."""
    if isinstance(value, bool):
        raise ValueError("backoff_factor must be a number")
    if not isinstance(value, (int, float)):
        raise ValueError("backoff_factor must be a number")
    fv = float(value)
    if not math.isfinite(fv) or fv < 0:
        raise ValueError("backoff_factor must be finite non-negative")
    return fv


def fetch_weather(
    city: str,
    api_key: str | None = None,
    api_url: str | None = None,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
) -> dict[str, str | float | int]:
    """Fetch weather for city with retry and exponential backoff.

    Args:
        city: city name, non-empty after stripping, up to 100 chars.
        api_key: explicit API key; if None, reads ``API_KEY`` env var.
        api_url: explicit API URL; if None, reads ``API_URL`` env var.
        max_retries: number of attempts (1..10).
        backoff_factor: base sleep seconds, multiplied as
            ``backoff_factor * 2**attempt`` (0 means no sleep).

    Returns:
        Normalized dict ``{"city": str, "temperature": float,
        "description": str, "humidity": int?}``. ``humidity`` included when
        present in API response.

    Raises:
        ValueError: if inputs invalid, HTTP error, bad payload, or retries
            exhausted. Retryable statuses are 429, 500, 502, 503, 504 and
            network exceptions; other 4xx fail immediately.
    """
    clean_city = _validate_city(city)

    if api_key is not None:
        key = _validate_api_key_value(api_key)
    else:
        key = get_api_key()

    if api_url is not None:
        url = _validate_api_url_value(api_url)
    else:
        url = get_api_url()
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("API_URL must start with http:// or https://")

    max_r = _validate_max_retries(max_retries)
    bf = _validate_backoff_factor(backoff_factor)

    retry_statuses = {429, 500, 502, 503, 504}

    for attempt in range(max_r):
        try:
            response = httpx.get(
                url,
                params={"q": clean_city, "appid": key, "units": "metric"},
                headers={"apikey": key},
                timeout=10.0,
            )
        except Exception as exc:
            if attempt == max_r - 1:
                raise ValueError(f"request failed: {exc}") from exc
            time.sleep(bf * (2**attempt))
            continue

        if response.status_code == 200:
            try:
                data: Any = response.json()
            except Exception as exc:
                raise ValueError(f"invalid JSON response: {exc}") from exc

            if not isinstance(data, dict):
                raise ValueError("invalid response: top-level must be object")

            raw_city: Any = None
            if "name" in data:
                raw_city = data["name"]
            elif "city" in data:
                raw_city = data["city"]
            else:
                raise ValueError("invalid response: missing 'name'")

            if not isinstance(raw_city, str) or not raw_city.strip():
                raise ValueError("invalid response: 'name' must be non-empty string")
            city_name = raw_city.strip()

            raw_main: Any = data.get("main")
            if not isinstance(raw_main, dict):
                raise ValueError("invalid response: missing 'main'")

            raw_temp: Any = raw_main.get("temp")
            if isinstance(raw_temp, bool):
                raise ValueError("invalid response: 'temp' must be a number")
            if not isinstance(raw_temp, (int, float)):
                raise ValueError("invalid response: 'temp' must be a number")
            temp_val = float(raw_temp)
            if not math.isfinite(temp_val):
                raise ValueError("invalid response: 'temp' must be finite")

            raw_weather: Any = data.get("weather")
            if not isinstance(raw_weather, list) or len(raw_weather) == 0:
                raise ValueError("invalid response: missing 'weather'")
            first: Any = raw_weather[0]
            if not isinstance(first, dict):
                raise ValueError("invalid response: 'weather' must be list of objects")
            raw_desc: Any = first.get("description")
            if not isinstance(raw_desc, str) or not raw_desc.strip():
                raise ValueError(
                    "invalid response: 'description' must be non-empty string"
                )
            description = raw_desc.strip()

            result: dict[str, str | float | int] = {
                "city": city_name,
                "temperature": temp_val,
                "description": description,
            }

            raw_hum: Any = raw_main.get("humidity")
            if raw_hum is not None:
                if isinstance(raw_hum, bool):
                    raise ValueError("invalid response: 'humidity' must be a number")
                if not isinstance(raw_hum, (int, float)):
                    raise ValueError("invalid response: 'humidity' must be a number")
                hum_float = float(raw_hum)
                if not math.isfinite(hum_float):
                    raise ValueError("invalid response: 'humidity' must be finite")
                hum_int = int(hum_float)
                if hum_int < 0 or hum_int > 100:
                    raise ValueError("invalid response: 'humidity' must be 0..100")
                result["humidity"] = hum_int

            return result

        if response.status_code in retry_statuses:
            if attempt == max_r - 1:
                raise ValueError(f"request failed with status {response.status_code}")
            time.sleep(bf * (2**attempt))
            continue

        raise ValueError(f"request failed with status {response.status_code}")

    raise ValueError("request failed: max retries exceeded")

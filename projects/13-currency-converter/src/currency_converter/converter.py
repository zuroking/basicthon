"""Core logic for currency converter.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded.

API contract:
    GET {API_URL} with query ``base`` and header ``apikey``.
    Response JSON expected to contain ``rates`` or ``conversion_rates``:
    ``{"base": "USD", "rates": {"EUR": 0.92, "GBP": 0.79}}``
    Provider examples: exchangerate.host, exchangerate-api.com.
    Rates are validated as ``dict[str, float]`` with 3-letter codes.

Uses ``os.environ`` for ``API_KEY``/``API_URL`` and ``httpx`` for HTTP.
"""

from __future__ import annotations

import math
import os
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


def _validate_currency(code: str) -> str:
    """Validate 3-letter currency code and return uppercased form.

    Raises:
        ValueError: if code is not a 3-letter alphabetic string.
    """
    if not isinstance(code, str):
        raise ValueError("currency code must be a string")
    cleaned = code.strip().upper()
    if len(cleaned) != 3 or not cleaned.isalpha():
        raise ValueError(f"invalid currency code: {code!r}")
    return cleaned


def _validate_amount(amount: float | int) -> float:
    """Validate amount and return as float.

    Raises:
        ValueError: if amount is bool, not int/float, NaN/inf.
    """
    if isinstance(amount, bool):
        raise ValueError("amount must be a number")
    if not isinstance(amount, (int, float)):
        raise ValueError("amount must be a number")
    value = float(amount)
    if not math.isfinite(value):
        raise ValueError("amount must be finite")
    return value


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


def fetch_rates(
    base_currency: str,
    api_key: str | None = None,
    api_url: str | None = None,
) -> dict[str, float]:
    """Fetch exchange rates for base currency.

    Args:
        base_currency: 3-letter code, e.g. ``USD``.
        api_key: explicit API key; if None, reads ``API_KEY`` env var.
        api_url: explicit API URL; if None, reads ``API_URL`` env var.

    Returns:
        Mapping ``currency -> rate`` relative to base (e.g. ``{"EUR": 0.92}``).

    Raises:
        ValueError: if currency/key/url invalid, HTTP error, or bad payload.
    """
    clean_base = _validate_currency(base_currency)

    if api_key is not None:
        key = _validate_api_key_value(api_key)
    else:
        key = get_api_key()

    if api_url is not None:
        url = _validate_api_url_value(api_url)
    else:
        url = get_api_url()
        # also validate env-provided URL format
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ValueError("API_URL must start with http:// or https://")

    try:
        response = httpx.get(
            url,
            params={"base": clean_base},
            headers={"apikey": key},
            timeout=10.0,
        )
    except Exception as exc:
        raise ValueError(f"request failed: {exc}") from exc

    if response.status_code != 200:
        raise ValueError(f"request failed with status {response.status_code}")

    try:
        data: Any = response.json()
    except Exception as exc:
        raise ValueError(f"invalid JSON response: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("invalid response: top-level must be object")

    raw_rates: Any = None
    if "rates" in data:
        raw_rates = data["rates"]
    elif "conversion_rates" in data:
        raw_rates = data["conversion_rates"]
    else:
        raise ValueError("invalid response: missing 'rates'")

    if not isinstance(raw_rates, dict):
        raise ValueError("invalid response: 'rates' must be object")

    result: dict[str, float] = {}
    for k, v in raw_rates.items():
        if not isinstance(k, str):
            raise ValueError("invalid response: rate keys must be strings")
        clean_k = k.strip().upper()
        if len(clean_k) != 3 or not clean_k.isalpha():
            raise ValueError(f"invalid response: bad currency code {k!r}")
        if isinstance(v, bool):
            raise ValueError("invalid response: rate must be a number")
        if not isinstance(v, (int, float)):
            raise ValueError("invalid response: rate must be a number")
        fv = float(v)
        if not math.isfinite(fv) or fv <= 0:
            raise ValueError("invalid response: rate must be finite positive")
        result[clean_k] = fv

    return result


def convert(
    amount: float | int,
    from_currency: str,
    to_currency: str,
    api_key: str | None = None,
    api_url: str | None = None,
) -> float:
    """Convert amount from one currency to another.

    Fetches rates with ``base = from_currency`` and multiplies.

    Args:
        amount: amount to convert, finite number (int or float).
        from_currency: source 3-letter code.
        to_currency: target 3-letter code.
        api_key: explicit API key; if None, reads ``API_KEY`` env var.
        api_url: explicit API URL; if None, reads ``API_URL`` env var.

    Returns:
        Converted amount as float.

    Raises:
        ValueError: if inputs invalid, rate missing, or fetch fails.
    """
    value = _validate_amount(amount)
    clean_from = _validate_currency(from_currency)
    clean_to = _validate_currency(to_currency)

    if clean_from == clean_to:
        return value

    rates = fetch_rates(clean_from, api_key=api_key, api_url=api_url)

    rate = rates.get(clean_to)
    if rate is None:
        raise ValueError(f"unsupported currency: {clean_to}")

    return value * rate

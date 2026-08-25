"""Tests for currency_converter.converter — covers every public function."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from currency_converter.converter import convert, fetch_rates, get_api_key, get_api_url


def _mock_response(
    status_code: int = 200, json_data: object | None = None
) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json = MagicMock(return_value=json_data)
    return mock


# ---- get_api_key ----


def test_get_api_key_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "secret123")
    assert get_api_key() == "secret123"


def test_get_api_key_strips(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "  spaced  ")
    assert get_api_key() == "spaced"


def test_get_api_key_custom_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_KEY", "custom456")
    assert get_api_key("MY_KEY") == "custom456"


def test_get_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(ValueError, match="not set"):
        get_api_key()


def test_get_api_key_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "   ")
    with pytest.raises(ValueError, match="not set"):
        get_api_key()


def test_get_api_key_invalid_var_name() -> None:
    with pytest.raises(ValueError):
        get_api_key("")
    with pytest.raises(ValueError):
        get_api_key("   ")
    with pytest.raises(ValueError):
        get_api_key(123)  # type: ignore[arg-type]


# ---- get_api_url ----


def test_get_api_url_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_URL", "https://api.example.com/latest")
    assert get_api_url() == "https://api.example.com/latest"


def test_get_api_url_strips(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_URL", "  https://api.example.com  ")
    assert get_api_url() == "https://api.example.com"


def test_get_api_url_custom_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_URL", "https://my.example.com")
    assert get_api_url("MY_URL") == "https://my.example.com"


def test_get_api_url_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_URL", raising=False)
    with pytest.raises(ValueError, match="not set"):
        get_api_url()


def test_get_api_url_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_URL", "   ")
    with pytest.raises(ValueError, match="not set"):
        get_api_url()


def test_get_api_url_invalid_var_name() -> None:
    with pytest.raises(ValueError):
        get_api_url("")
    with pytest.raises(ValueError):
        get_api_url("   ")
    with pytest.raises(ValueError):
        get_api_url(123)  # type: ignore[arg-type]


# ---- fetch_rates ----


def test_fetch_rates_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k123")
    monkeypatch.setenv("API_URL", "https://api.example.com/latest")
    mock_resp = _mock_response(
        200, {"base": "USD", "rates": {"EUR": 0.92, "GBP": 0.79}}
    )
    with patch(
        "currency_converter.converter.httpx.get", return_value=mock_resp
    ) as mock_get:
        rates = fetch_rates("USD")
        assert rates == {"EUR": 0.92, "GBP": 0.79}
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"base": "USD"}
        assert kwargs["headers"] == {"apikey": "k123"}


def test_fetch_rates_explicit_key_url(monkeypatch: pytest.MonkeyPatch) -> None:
    # explicit should not read env
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API_URL", raising=False)
    mock_resp = _mock_response(200, {"rates": {"EUR": 1.1}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        rates = fetch_rates(
            "usd", api_key="explicit-key", api_url="https://api.example.com"
        )
        assert rates == {"EUR": 1.1}


def test_fetch_rates_conversion_rates_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"conversion_rates": {"JPY": 150.0}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        rates = fetch_rates("USD")
        assert rates == {"JPY": 150.0}


def test_fetch_rates_normalizes_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {"EUR": 0.9}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp) as mg:
        fetch_rates("  usd  ")
        assert mg.call_args.kwargs["params"] == {"base": "USD"}


def test_fetch_rates_lowercase_rate_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {"eur": 0.92, "gbp": 0.79}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        rates = fetch_rates("USD")
        assert rates == {"EUR": 0.92, "GBP": 0.79}


def test_fetch_rates_invalid_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    with pytest.raises(ValueError, match="invalid currency"):
        fetch_rates("")
    with pytest.raises(ValueError):
        fetch_rates("US")
    with pytest.raises(ValueError):
        fetch_rates("USD1")
    with pytest.raises(ValueError):
        fetch_rates(123)  # type: ignore[arg-type]


def test_fetch_rates_invalid_key_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {"EUR": 1.0}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="api_key must be a string"):
            fetch_rates("USD", api_key=123)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="api_key must not be empty"):
            fetch_rates("USD", api_key="   ")


def test_fetch_rates_invalid_url_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    mock_resp = _mock_response(200, {"rates": {"EUR": 1.0}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="api_url must be a string"):
            fetch_rates("USD", api_url=123)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="api_url must not be empty"):
            fetch_rates("USD", api_url="   ")
        with pytest.raises(ValueError, match="must start with http"):
            fetch_rates("USD", api_url="ftp://example.com")
        with pytest.raises(ValueError, match="must start with http"):
            fetch_rates("USD", api_url="example.com")


def test_fetch_rates_env_url_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "ftp://bad.example.com")
    mock_resp = _mock_response(200, {"rates": {"EUR": 1.0}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="must start with http"):
            fetch_rates("USD")


def test_fetch_rates_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("API_URL", "https://api.example.com")
    with pytest.raises(ValueError, match="not set"):
        fetch_rates("USD")
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.delenv("API_URL", raising=False)
    with pytest.raises(ValueError, match="not set"):
        fetch_rates("USD")


def test_fetch_rates_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(401, {"error": "unauthorized"})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="status 401"):
            fetch_rates("USD")


def test_fetch_rates_request_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    with patch(
        "currency_converter.converter.httpx.get",
        side_effect=Exception("network down"),
    ):
        with pytest.raises(ValueError, match="request failed"):
            fetch_rates("USD")


def test_fetch_rates_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock = MagicMock()
    mock.status_code = 200
    mock.json.side_effect = ValueError("bad json")
    with patch("currency_converter.converter.httpx.get", return_value=mock):
        with pytest.raises(ValueError, match="invalid JSON"):
            fetch_rates("USD")


def test_fetch_rates_not_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, ["not", "dict"])
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="top-level must be object"):
            fetch_rates("USD")


def test_fetch_rates_missing_rates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"base": "USD"})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="missing 'rates'"):
            fetch_rates("USD")


def test_fetch_rates_rates_not_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": "bad"})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="'rates' must be object"):
            fetch_rates("USD")


def test_fetch_rates_invalid_rate_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {123: 1.0}})  # type: ignore[dict-item]
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="keys must be strings"):
            fetch_rates("USD")


def test_fetch_rates_bad_code_in_rates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {"EU": 0.9}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="bad currency code"):
            fetch_rates("USD")


def test_fetch_rates_invalid_rate_value_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    for bad in ["bad", None, True, []]:
        mock_resp = _mock_response(200, {"rates": {"EUR": bad}})
        with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
            with pytest.raises(ValueError, match="rate must be a number"):
                fetch_rates("USD")


def test_fetch_rates_zero_negative(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    for bad in [0, -1, 0.0, -0.5]:
        mock_resp = _mock_response(200, {"rates": {"EUR": bad}})
        with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
            with pytest.raises(ValueError, match="finite positive"):
                fetch_rates("USD")


def test_fetch_rates_rate_inf_nan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    for bad in [float("inf"), float("nan")]:
        mock_resp = _mock_response(200, {"rates": {"EUR": bad}})
        with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
            with pytest.raises(ValueError, match="finite positive"):
                fetch_rates("USD")


# ---- convert ----


def test_convert_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {"EUR": 0.9, "JPY": 150.0}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        assert convert(100, "USD", "EUR") == pytest.approx(90.0)
        assert convert(2, "USD", "JPY") == pytest.approx(300.0)


def test_convert_same_currency_no_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    # should not call httpx if same currency
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    with patch("currency_converter.converter.httpx.get") as mock_get:
        assert convert(123.45, "USD", "usd") == pytest.approx(123.45)
        assert convert(10, "eur", "EUR") == pytest.approx(10.0)
        mock_get.assert_not_called()


def test_convert_with_explicit_key_url() -> None:
    mock_resp = _mock_response(200, {"rates": {"EUR": 0.5}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        assert convert(
            10, "USD", "EUR", api_key="key123", api_url="https://api.example.com"
        ) == pytest.approx(5.0)


def test_convert_amount_validation() -> None:
    with pytest.raises(ValueError, match="amount must be a number"):
        convert("100", "USD", "EUR")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        convert(True, "USD", "EUR")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="finite"):
        convert(float("nan"), "USD", "EUR")
    with pytest.raises(ValueError, match="finite"):
        convert(float("inf"), "USD", "EUR")


def test_convert_currency_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {"EUR": 0.9}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="invalid currency"):
            convert(10, "", "EUR")
        with pytest.raises(ValueError):
            convert(10, "USD", "EU")
        with pytest.raises(ValueError):
            convert(10, 123, "EUR")  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            convert(10, "USD", 123)  # type: ignore[arg-type]


def test_convert_unsupported_currency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {"EUR": 0.9}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="unsupported currency"):
            convert(10, "USD", "JPY")


def test_convert_zero_and_negative_amount(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {"EUR": 0.9}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        assert convert(0, "USD", "EUR") == pytest.approx(0.0)
        # negative allowed? we treat as value * rate
        assert convert(-10, "USD", "EUR") == pytest.approx(-9.0)


def test_convert_int_and_float(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {"EUR": 2.0}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        assert convert(5, "USD", "EUR") == pytest.approx(10.0)
        assert convert(5.5, "USD", "EUR") == pytest.approx(11.0)


def test_convert_propagates_fetch_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(500, {})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        with pytest.raises(ValueError, match="status 500"):
            convert(10, "USD", "EUR")


def test_fetch_rates_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {"eur": 0.92}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp):
        # convert should handle lower case input and lower case rates
        assert convert(10, "usd", "eur") == pytest.approx(9.2)


def test_env_integration_convert(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "env-key")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, {"rates": {"EUR": 0.85}})
    with patch("currency_converter.converter.httpx.get", return_value=mock_resp) as mg:
        assert convert(100, "USD", "EUR") == pytest.approx(85.0)
        assert mg.call_args.kwargs["headers"] == {"apikey": "env-key"}
        assert mg.call_args.kwargs["params"] == {"base": "USD"}

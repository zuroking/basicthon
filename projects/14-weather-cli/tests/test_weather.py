"""Tests for weather_cli.weather — covers every public function."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from weather_cli.weather import fetch_weather, get_api_key, get_api_url


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
    monkeypatch.setenv("API_URL", "https://api.example.com/weather")
    assert get_api_url() == "https://api.example.com/weather"


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


# ---- fetch_weather ----


def test_fetch_weather_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k123")
    monkeypatch.setenv("API_URL", "https://api.example.com/weather")
    payload = {
        "name": "London",
        "main": {"temp": 15.5, "humidity": 72},
        "weather": [{"description": "clear sky"}],
    }
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp) as mock_get:
        with patch("weather_cli.weather.time.sleep") as mock_sleep:
            data = fetch_weather("London")
            assert data == {
                "city": "London",
                "temperature": 15.5,
                "description": "clear sky",
                "humidity": 72,
            }
            mock_get.assert_called_once()
            _, kwargs = mock_get.call_args
            assert kwargs["params"] == {
                "q": "London",
                "appid": "k123",
                "units": "metric",
            }
            assert kwargs["headers"] == {"apikey": "k123"}
            mock_sleep.assert_not_called()


def test_fetch_weather_explicit_key_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("API_URL", raising=False)
    payload = {
        "name": "Paris",
        "main": {"temp": 20.0},
        "weather": [{"description": "cloudy"}],
    }
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            data = fetch_weather(
                "Paris", api_key="explicit-key", api_url="https://api.example.com"
            )
            assert data["city"] == "Paris"
            assert data["temperature"] == pytest.approx(20.0)


def test_fetch_weather_city_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    with pytest.raises(ValueError, match="city must not be empty"):
        fetch_weather("")
    with pytest.raises(ValueError, match="city must not be empty"):
        fetch_weather("   ")
    with pytest.raises(ValueError, match="city must be a string"):
        fetch_weather(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="at most 100"):
        fetch_weather("a" * 101)


def test_fetch_weather_invalid_key_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {
        "name": "London",
        "main": {"temp": 10},
        "weather": [{"description": "ok"}],
    }
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError, match="api_key must be a string"):
                fetch_weather("London", api_key=123)  # type: ignore[arg-type]
            with pytest.raises(ValueError, match="api_key must not be empty"):
                fetch_weather("London", api_key="   ")


def test_fetch_weather_invalid_url_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    payload = {
        "name": "London",
        "main": {"temp": 10},
        "weather": [{"description": "ok"}],
    }
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError, match="api_url must be a string"):
                fetch_weather("London", api_url=123)  # type: ignore[arg-type]
            with pytest.raises(ValueError, match="api_url must not be empty"):
                fetch_weather("London", api_url="   ")
            with pytest.raises(ValueError, match="must start with http"):
                fetch_weather("London", api_url="ftp://example.com")
            with pytest.raises(ValueError, match="must start with http"):
                fetch_weather("London", api_url="example.com")


def test_fetch_weather_env_url_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "ftp://bad.example.com")
    payload = {
        "name": "London",
        "main": {"temp": 10},
        "weather": [{"description": "ok"}],
    }
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError, match="must start with http"):
                fetch_weather("London")


def test_fetch_weather_missing_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("API_URL", "https://api.example.com")
    with patch("weather_cli.weather.time.sleep"):
        with pytest.raises(ValueError, match="not set"):
            fetch_weather("London")
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.delenv("API_URL", raising=False)
    with patch("weather_cli.weather.time.sleep"):
        with pytest.raises(ValueError, match="not set"):
            fetch_weather("London")


def test_fetch_weather_invalid_max_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    with patch("weather_cli.weather.time.sleep"):
        with pytest.raises(ValueError, match="max_retries must be"):
            fetch_weather("London", max_retries=0)
        with pytest.raises(ValueError):
            fetch_weather("London", max_retries=11)
        with pytest.raises(ValueError):
            fetch_weather("London", max_retries=True)  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            fetch_weather("London", max_retries="3")  # type: ignore[arg-type]


def test_fetch_weather_invalid_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    with patch("weather_cli.weather.time.sleep"):
        with pytest.raises(ValueError, match="backoff_factor must be"):
            fetch_weather("London", backoff_factor=-1)
        with pytest.raises(ValueError):
            fetch_weather("London", backoff_factor=float("inf"))
        with pytest.raises(ValueError):
            fetch_weather("London", backoff_factor=float("nan"))
        with pytest.raises(ValueError):
            fetch_weather("London", backoff_factor=True)  # type: ignore[arg-type]


def test_fetch_weather_retry_on_500_then_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {
        "name": "Berlin",
        "main": {"temp": 18.0, "humidity": 60},
        "weather": [{"description": "sunny"}],
    }
    mock_success = _mock_response(200, payload)
    mock_fail = _mock_response(500, {})
    with patch(
        "weather_cli.weather.httpx.get", side_effect=[mock_fail, mock_success]
    ) as mock_get:
        with patch("weather_cli.weather.time.sleep") as mock_sleep:
            data = fetch_weather("Berlin", max_retries=3, backoff_factor=0.5)
            assert data["city"] == "Berlin"
            assert mock_get.call_count == 2
            mock_sleep.assert_called_once_with(0.5)


def test_fetch_weather_retry_backoff_exponential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {
        "name": "Rome",
        "main": {"temp": 25.0, "humidity": 50},
        "weather": [{"description": "hot"}],
    }
    mock_success = _mock_response(200, payload)
    mocks = [_mock_response(500, {}), _mock_response(502, {}), mock_success]
    with patch("weather_cli.weather.httpx.get", side_effect=mocks):
        with patch("weather_cli.weather.time.sleep") as mock_sleep:
            data = fetch_weather("Rome", max_retries=3, backoff_factor=1.0)
            assert data["city"] == "Rome"
            assert mock_sleep.call_count == 2
            assert mock_sleep.call_args_list[0].args[0] == pytest.approx(1.0)
            assert mock_sleep.call_args_list[1].args[0] == pytest.approx(2.0)


def test_fetch_weather_retry_exhausted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_fail = _mock_response(503, {})
    with patch("weather_cli.weather.httpx.get", return_value=mock_fail):
        with patch("weather_cli.weather.time.sleep") as mock_sleep:
            with pytest.raises(ValueError, match="status 503"):
                fetch_weather("London", max_retries=3, backoff_factor=0.1)
            assert mock_sleep.call_count == 2


def test_fetch_weather_retry_on_429(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {
        "name": "Madrid",
        "main": {"temp": 30.0},
        "weather": [{"description": "clear"}],
    }
    with patch(
        "weather_cli.weather.httpx.get",
        side_effect=[_mock_response(429, {}), _mock_response(200, payload)],
    ):
        with patch("weather_cli.weather.time.sleep") as mock_sleep:
            data = fetch_weather("Madrid", max_retries=2, backoff_factor=0.2)
            assert data["city"] == "Madrid"
            mock_sleep.assert_called_once_with(0.2)


def test_fetch_weather_non_retryable_400(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(400, {})
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep") as mock_sleep:
            with pytest.raises(ValueError, match="status 400"):
                fetch_weather("London")
            mock_sleep.assert_not_called()


def test_fetch_weather_network_exception_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {
        "name": "Oslo",
        "main": {"temp": 5.0, "humidity": 80},
        "weather": [{"description": "snow"}],
    }
    mock_success = _mock_response(200, payload)
    with patch(
        "weather_cli.weather.httpx.get",
        side_effect=[Exception("network down"), mock_success],
    ):
        with patch("weather_cli.weather.time.sleep") as mock_sleep:
            data = fetch_weather("Oslo", max_retries=2, backoff_factor=0.3)
            assert data["temperature"] == pytest.approx(5.0)
            mock_sleep.assert_called_once_with(0.3)


def test_fetch_weather_network_exception_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    with patch("weather_cli.weather.httpx.get", side_effect=Exception("down")):
        with patch("weather_cli.weather.time.sleep") as mock_sleep:
            with pytest.raises(ValueError, match="request failed"):
                fetch_weather("London", max_retries=2, backoff_factor=0.1)
            assert mock_sleep.call_count == 1


def test_fetch_weather_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock = MagicMock()
    mock.status_code = 200
    mock.json.side_effect = ValueError("bad json")
    with patch("weather_cli.weather.httpx.get", return_value=mock):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError, match="invalid JSON"):
                fetch_weather("London")


def test_fetch_weather_not_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_resp = _mock_response(200, ["not", "dict"])
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError, match="top-level must be object"):
                fetch_weather("London")


def test_fetch_weather_missing_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {"main": {"temp": 10}, "weather": [{"description": "ok"}]}
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError, match="missing 'name'"):
                fetch_weather("London")


def test_fetch_weather_city_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {
        "city": "Kyiv",
        "main": {"temp": 12.0},
        "weather": [{"description": "cloudy"}],
    }
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            data = fetch_weather("Kyiv")
            assert data["city"] == "Kyiv"


def test_fetch_weather_invalid_name_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {"name": 123, "main": {"temp": 10}, "weather": [{"description": "ok"}]}
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError, match="'name' must be"):
                fetch_weather("London")


def test_fetch_weather_missing_main(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {"name": "London", "weather": [{"description": "ok"}]}
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError, match="missing 'main'"):
                fetch_weather("London")


def test_fetch_weather_invalid_temp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    for bad in ["bad", None, True, float("inf"), float("nan")]:
        payload = {
            "name": "London",
            "main": {"temp": bad},
            "weather": [{"description": "ok"}],
        }
        mock_resp = _mock_response(200, payload)
        with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
            with patch("weather_cli.weather.time.sleep"):
                with pytest.raises(ValueError, match="'temp' must be"):
                    fetch_weather("London")


def test_fetch_weather_missing_weather(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {"name": "London", "main": {"temp": 10}}
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError, match="missing 'weather'"):
                fetch_weather("London")


def test_fetch_weather_empty_weather(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {"name": "London", "main": {"temp": 10}, "weather": []}
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError, match="missing 'weather'"):
                fetch_weather("London")


def test_fetch_weather_invalid_description(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {
        "name": "London",
        "main": {"temp": 10},
        "weather": [{"description": ""}],
    }
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError, match="'description' must be"):
                fetch_weather("London")
    payload2 = {
        "name": "London",
        "main": {"temp": 10},
        "weather": [{"description": 123}],
    }
    mock_resp2 = _mock_response(200, payload2)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp2):
        with patch("weather_cli.weather.time.sleep"):
            with pytest.raises(ValueError):
                fetch_weather("London")


def test_fetch_weather_invalid_humidity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    for bad in ["bad", True, 150, -5, float("nan")]:
        payload = {
            "name": "London",
            "main": {"temp": 10, "humidity": bad},
            "weather": [{"description": "ok"}],
        }
        mock_resp = _mock_response(200, payload)
        with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
            with patch("weather_cli.weather.time.sleep"):
                with pytest.raises(ValueError, match="'humidity' must be"):
                    fetch_weather("London")


def test_fetch_weather_humidity_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {
        "name": "London",
        "main": {"temp": 10},
        "weather": [{"description": "clear"}],
    }
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp):
        with patch("weather_cli.weather.time.sleep"):
            data = fetch_weather("London")
            assert "humidity" not in data
            assert data["temperature"] == pytest.approx(10)
            assert data["description"] == "clear"


def test_fetch_weather_trims_city(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {
        "name": "London",
        "main": {"temp": 10},
        "weather": [{"description": "ok"}],
    }
    mock_resp = _mock_response(200, payload)
    with patch("weather_cli.weather.httpx.get", return_value=mock_resp) as mg:
        with patch("weather_cli.weather.time.sleep"):
            fetch_weather("  London  ")
            assert mg.call_args.kwargs["params"]["q"] == "London"


def test_fetch_weather_zero_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    payload = {
        "name": "London",
        "main": {"temp": 10},
        "weather": [{"description": "ok"}],
    }
    mock_success = _mock_response(200, payload)
    with patch(
        "weather_cli.weather.httpx.get",
        side_effect=[_mock_response(500, {}), mock_success],
    ):
        with patch("weather_cli.weather.time.sleep") as mock_sleep:
            data = fetch_weather("London", max_retries=2, backoff_factor=0)
            assert data["city"] == "London"
            mock_sleep.assert_called_once_with(0)


def test_fetch_weather_single_retry_no_sleep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("API_KEY", "k")
    monkeypatch.setenv("API_URL", "https://api.example.com")
    mock_fail = _mock_response(500, {})
    with patch("weather_cli.weather.httpx.get", return_value=mock_fail):
        with patch("weather_cli.weather.time.sleep") as mock_sleep:
            with pytest.raises(ValueError):
                fetch_weather("London", max_retries=1, backoff_factor=0.5)
            mock_sleep.assert_not_called()

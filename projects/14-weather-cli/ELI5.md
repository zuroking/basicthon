# ELI5 — Weather CLI with Retry

Imagine a weather booth:

- You have a booth address (`API_URL`, e.g. `https://api.example.com/weather`) and a pass (`API_KEY`). Both live in your pocket (environment variables), not in the code. Get them with `get_api_url()` / `get_api_key()` — if pocket empty, it shouts `ValueError`.
- The booth gives you weather: `fetch_weather("London")` — you show your pass (`headers={"apikey": key}` + `params={"q": "London", "appid": key}`) and ask "weather for London?". Booth replies with JSON `{"name": "London", "main": {"temp": 15.5, "humidity": 72}, "weather": [{"description": "clear sky"}]}`. If booth is closed or board is scribbled (bad JSON, missing `main`/`weather`), you shout `ValueError`.
- Booth can be busy: status 429 or 500/502/503/504, or network down (`httpx` exception). Then you wait and try again: 1st retry wait `backoff_factor * 1`, 2nd wait `*2`, 3rd wait `*4` (exponential). With `backoff_factor=0.5` you sleep 0.5, 1.0, 2.0. After `max_retries` (default 3) you give up. Status 400/401/404 → no retry, shout immediately.
- `fetch_weather("London")` returns `{"city": "London", "temperature": 15.5, "description": "clear sky", "humidity": 72}`. Same city spelled `  london  ` → trimmed to `London` for request but city name comes from booth reply. No `humidity` in reply? You return only 3 keys.
- Asking for unknown city? Booth replies 404 → shout `request failed with status 404` without retry.

Rules a child can follow:

- City must be non-empty after trimming, up to 100 chars; `""` or `"   "` → error.
- Amount is not needed — but `max_retries` must be 1..10, `backoff_factor` must be finite >=0 (0 means no wait).
- URL must start with `http://` or `https://`; empty key/URL → error.
- Tests use a fake booth (`unittest.mock.patch("weather_cli.weather.httpx.get")`) and fake clock (`patch("weather_cli.weather.time.sleep")`) — you decide what JSON it returns and check sleep calls, no real network, no real key.
- This is a toy booth. Real weather services add caching, rate limits, many providers, icons and forecasts — this one does one `httpx.get` with `timeout=10.0` and validates strictly, but teaches you retry.

# ELI5 — Currency Converter

Imagine a money exchange booth:

- You have a booth address (`API_URL`, e.g. `https://api.example.com/latest`) and a pass (`API_KEY`). Both live in your pocket (environment variables), not in the code. Get them with `get_api_url()` / `get_api_key()` — if pocket empty, it shouts `ValueError`.
- The booth gives you a price board: `fetch_rates("USD")` — you show your pass (`headers={"apikey": key}`) and ask "prices for USD?" (`params={"base": "USD"}`). Booth replies with JSON `{"rates": {"EUR": 0.92, "GBP": 0.79}}`. If booth is closed (`status != 200`) or board is scribbled (bad JSON, missing `rates`), you shout `ValueError`.
- `convert(100, "USD", "EUR")` — ask booth for USD board, find `EUR = 0.92`, return `100 * 0.92 = 92.0`. Same booth for same money? `convert(10, "USD", "USD")` returns `10.0` without asking.
- Asking for unknown money? `convert(10, "USD", "XYZ")` where `XYZ` not on board → shout `unsupported currency`.
- The booth may write `conversion_rates` instead of `rates` — both work. Codes are case-insensitive: `usd`, `UsD` → `USD`.

Rules a child can follow:

- Currency code must be exactly 3 letters after trimming, e.g. `USD`, `eur` → `EUR`; `"US"` or `"123"` → error.
- Amount must be a finite number (`int` or `float`), not `True`, not `nan`/`inf`; `-5` is allowed but `bool` is not.
- URL must start with `http://` or `https://`; empty key/URL → error.
- Tests use a fake booth (`unittest.mock.patch("currency_converter.converter.httpx.get")`) — you decide what JSON it returns, no real network, no real key.
- This is a toy booth. Real exchanges add fees, caching, many providers, and retry — this one does one `httpx.get` with `timeout=10.0` and validates strictly.

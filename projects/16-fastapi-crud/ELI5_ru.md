# ELI5 — FastAPI CRUD

Представь игрушечный магазин с тетрадкой:

- Тетрадка — `dict[int, Item]` по имени `_items`. Страница 1 — `Item(id=1, title="Купить молоко")`, страница 2 — `Item(id=2, title="Выгулять собаку")`. Счётчик `_next_id` говорит, какой номер дать следующей записи.
- `create_item(ItemCreate(title="Купить молоко"))` пишет новую страницу: делает `strip`, проверяет `title` 1..100 символов, `description` ≤500, присваивает `id=_next_id`, кладёт в словарь, делает `_next_id += 1`. Возвращает новый `Item`.
- `get_item(1)` ищет страницу 1, `list_items()` отдаёт все страницы по порядку `id`, `update_item(1, ItemUpdate(title="Купить хлеб"))` переписывает только title (остальное остаётся), `delete_item(1)` вырывает страницу. `reset_store()` выбрасывает всю тетрадку — нужно тестам.
- FastAPI — прилавок: `POST /items` с JSON `{"title":"привет"}` → прилавок вызывает `create_item`, отдаёт `201` + JSON. `GET /items` → `list_items`. `GET /items/1` → `get_item` или `404 {"detail":"item not found"}`. То же для `PUT` и `DELETE` (204 при успехе — 204 значит "готово, возвращать нечего", поэтому ответ без тела по правилу HTTP).
- Валидация — в Pydantic: `ItemCreate(title=Field(min_length=1, max_length=100))` отклонит `""` или 101×"x" с `422`. `ItemUpdate` весь опциональный — применяются только не-None поля.
- Настройки вне кода: `get_database_url()` читает `$DATABASE_URL` (`memory` если пусто), `get_port()` читает `$PORT` (`8000` если пусто, 1..65535). Документированы в `.env.example`, чтобы не хардкодить секреты.
- Тесты не запускают сервер: `from fastapi.testclient import TestClient; client = TestClient(app); client.post("/items", json={"title":"a"})`. `autouse` фикстура зовёт `reset_store` перед каждым тестом, поэтому `id` всегда с 1 — детерминировано.

Правила для ребёнка:

- `title` после `strip` не пуст и 1..100 символов; `description` None или ≤500 (пусто после strip → `None`).
- `item_id` — `int` не `bool`; `/items/not-an-int` → `422`.
- Нет записи → ядро вернёт `None`, API — `404`.
- `DATABASE_URL` и `PORT`/`HOST` живут в окружении, не в коде; `get_*` делает trim и defaults, неверный порт (`0`, `70000`, `abc`) → `ValueError`.
- Это игрушечная тетрадка. Настоящие магазины пишут в файл БД (SQLite, Postgres) и помнят после перезапуска; эта держит всё в памяти и забывает при `reset_store` — идеально для изучения FastAPI без сложности БД.

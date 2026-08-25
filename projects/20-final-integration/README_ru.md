# 20 — Финальная интеграция (CLI + SQLite + API)

Изолированный учебный проект из серии `basicthon` (Systems & Integration).

> **Этот проект переиспользует паттерны из проектов 04, 11, 16 — код скопирован и адаптирован, не импортирован, для сохранения изоляции проектов.**
> **Снепшот на момент создания — последующие изменения в 04/11/16 не портируются автоматически.**

**Что изучаем (lock scope):** объединение трёх слоёв в одно приложение — CLI (`argparse`), SQLite-персистентность (stdlib `sqlite3`) и REST API (FastAPI) над одной базой. Проект в три этапа: minimal — `storage.py` с dataclass `Task` и CRUD над таблицей `tasks`; improved — роуты FastAPI поверх функций хранилища, env-конфиг `DATABASE_PATH`/`HOST`/`PORT`; production-like — типизация, тесты, `ruff/black/mypy --strict`, `pytest` зелёный для каждой публичной функции в `src/final_integration/storage.py` и `src/final_integration/api.py` (кроме `cli.py` по §5), тесты TestClient с общей временной БД.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` содержит `fastapi==0.110.2`, `uvicorn==0.29.0`, `httpx==0.27.2` (пиннинг по G-17).

## Использование

CLI (пишет напрямую в SQLite):

```bash
python -m final_integration list
# (no tasks)

echo "написать финальный отчёт" | python -m final_integration add
# added #1

python -m final_integration add        # интерактивный ввод если tty
python -m final_integration list --all
# [ ] #1 написать финальный отчёт  (2026-08-25 09:00:00)

python -m final_integration done 1
python -m final_integration get 1
python -m final_integration delete 1
```

REST API (тот же файл базы):

```bash
python -m final_integration serve            # $DATABASE_PATH, default ./tasks.db
# или
final-integration serve --host 127.0.0.1 --port 8000

curl http://127.0.0.1:8000/tasks
curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"title":"deploy"}'
curl -X PUT http://127.0.0.1:8000/tasks/1/complete
curl -X DELETE http://127.0.0.1:8000/tasks/1   # 204, без тела
```

Как библиотека:

```python
from pathlib import Path
from final_integration import (
    add_task, get_task, list_tasks, complete_task, delete_task, create_db,
)

db = Path("tasks.db")
create_db(db)
tid = add_task(db, "выпустить проект")
print(get_task(db, tid))       # Task(id=1, title='выпустить проект', completed=False, ...)
complete_task(db, tid)
print(list_tasks(db))
delete_task(db, tid)
```

Детали:

- `get_db_path(var_name="DATABASE_PATH") -> str` — дефолт `./tasks.db`.
- `create_db(db_path) -> None` — идемпотентное создание таблицы.
- `add_task(db_path, title) -> int` — strip, отклоняет пустой/>100 символов, autoincrement.
- `list_tasks(db_path) -> list[Task]`, по возрастанию id.
- `get_task(db_path, task_id) -> Task | None`, bool отклоняется.
- `complete_task(db_path, task_id) -> bool`, `delete_task(db_path, task_id) -> bool`.
- API: `GET /`, `POST /tasks` (201), `GET /tasks`, `GET /tasks/{id}` (404), `PUT /tasks/{id}/complete` (404), `DELETE /tasks/{id}` (204 — без тела по HTTP-спецификации).

## Этапы

**Minimal:** `storage.py` адаптирован из проекта 11: таблица `tasks` (`id`, `title`, `completed`, `created_at`), dataclass `Task`, `create_db`/`add_task`/`list_tasks`.

**Improved:** Полный CRUD (`get_task`/`complete_task`/`delete_task`) с валидацией, `get_db_path` из env (`.env.example` документирует `DATABASE_PATH`/`HOST`/`PORT`), `api.py` адаптирован из проекта 16 и оборачивает функции хранилища моделями Pydantic.

**Production-like:** Type hints на всех публичных функциях, `ruff/black/mypy --strict` без ошибок (strict для 11–20 по §8), `pytest` зелёный для каждой публичной функции в `storage.py`+`api.py` (кроме `cli.py` по §5), tmp_path SQLite + TestClient без сети, `argparse` CLI с подкомандами и `serve` запускающим uvicorn, пиннинг зависимостей по G-17.

## API

```python
from final_integration import (
    Task, add_task, complete_task, create_db, delete_task,
    get_db_path, get_host, get_port, get_task, list_tasks, app,
)
```

## Тестирование

```bash
pytest -v          # временные SQLite файлы + моки HTTP, без сети
ruff check .
black --check .
mypy --strict src
```

## Заметка от ZuroKing

> Это выпускная шапка: одно приложение, три двери к одним данным. CLI пишет строки, которые API читает назад — потому что оба идут через один `storage.py`. В этом весь урок: *слои*, а не фреймворки. Держите `storage.py` свободным от импортов `fastapi`, а `api.py` — свободным от SQL: выкиньте любую сторону, вторая выживет. Заметьте, что было сознательно скопировано из проектов 04, 11, 16, а не импортировано: изоляция значит, что можно удалить соседнюю папку, и эта продолжит работать. А когда у вас самого возникнет чувство дублирования между вашими приложениями — это ощущение станет вашим следующим уроком о рефакторинге, но не задачей этого репозитория.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.

См. также: [ARCHITECTURE.md](ARCHITECTURE.md) — требуется по §6.

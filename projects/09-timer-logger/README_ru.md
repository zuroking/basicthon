# 09 — Таймер с логированием

Изолированный учебный проект из серии `basicthon` (Structures & Patterns).

**Что изучаем (lock scope):** измерение времени через `time.perf_counter`, протокол контекст-менеджера (`__enter__`/`__exit__`) и логирование с временными метками в файл через `pathlib` + `datetime`. Проект в три этапа: minimal — `Timer` с `start`/`stop`/`elapsed` и `is_running`/`reset`; improved — поддержка `with` и автологирование в файл при `stop`; production-like — типизация, тесты, `ruff/black/mypy` и CLI с `--sleep`/`--label`/`--log`.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` для этого проекта stdlib-only (`# stdlib only, no external dependencies`).

## Использование

```bash
python -m timer_logger --label "моя задача" --sleep 0.5
# моя задача: 0.501s

python -m timer_logger --label "logged" --sleep 0.2 --log timer.log
# logged: 0.201s
# logged to timer.log

python -m timer_logger --sleep 1 --log /tmp/run.log --label "сон 1с"
```

После `pip install -e .`:

```bash
timer-logger --sleep 0.3 --label demo
timer-logger --sleep 0.1 --log ./my.log --label "quick"
```

Как библиотека:

```python
from timer_logger import Timer, format_elapsed, log_message, read_logs, clear_logs
from unittest.mock import patch

with patch("timer_logger.timer.time.perf_counter", side_effect=[100.0, 102.5]):
    t = Timer(label="task")
    t.start()
    print(t.stop())  # 2.5
    print(float(t.elapsed))  # 2.5 или t.elapsed() — оба варианта работают

with Timer(label="block", log_file="demo.log") as t:
    pass  # измеряемый блок
print(read_logs("demo.log"))
print(format_elapsed(90.123))  # "1m 30.123s"
log_message("hello", "demo.log")
clear_logs("demo.log")
```

Детали:

- `Timer` использует `perf_counter`. `elapsed` работает и как свойство (`t.elapsed`) и как метод (`t.elapsed()`), возвращает текущее время если запущен или последний интервал если остановлен (`0.0` до старта).
- `start` бросает `RuntimeError` если уже запущен; `stop` — если не запущен. `reset` сбрасывает в `0.0`.
- Контекст-менеджер `with Timer(...) as t:` вызывает `start` при входе и `stop` при выходе, даже при исключении, и логирует если `log_file` задан.
- `log_file` — `str | Path`, родители создаются. При каждом `stop` дописывается строка `"{iso_timestamp} - {label}: {elapsed:.6f}s\n"`.
- `format_elapsed` форматирует секунды: `"X.XXXs"`, для `>=60` — `"Xm Y.ZZZs"`, для `>=3600` — `"Xh Ym Z.ZZZs"`.
- Хелперы `log_message`/`log_elapsed`/`read_logs`/`clear_logs` — простые файловые операции, `read_logs` возвращает `[]` если файла нет, `clear_logs` обнуляет или создаёт файл.

## Этапы

**Minimal:** `Timer` с `__init__(label, log_file)`, `start()`, `stop() -> float`, `elapsed` (property/callable), `is_running`, `reset()`. Хранит `_start_time`/`_elapsed`/`_running`, использует `perf_counter`, `RuntimeError` при неверном вызове, `0.0` до старта.

**Improved:** Протокол `__enter__`/`__exit__` (останавливает даже при исключении), автологирование в `stop`/`__exit__` через `_write_log` при `log_file` (создаёт родителей, пишет `datetime.now().isoformat` + `"{label}: {elapsed:.6f}s"`), `__repr__`, плюс функции `format_elapsed`/`log_message`/`log_elapsed`/`read_logs`/`clear_logs`.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy` без ошибок, `pytest` зелёный для каждой публичной функции в `src/timer_logger/timer.py` (кроме `cli.py` по §5 ARCHITECTURE.md) через `patch` для `perf_counter` и `tmp_path` для файлов, CLI на `argparse` с `--label`/`--log`/`--sleep`, точка входа `python -m timer_logger`.

## API

```python
from timer_logger import Timer, format_elapsed, log_message, log_elapsed, read_logs, clear_logs

Timer(label=None, log_file=None)
# start(), stop() -> float, reset(), elapsed (float/callable), is_running, with Timer() as t

format_elapsed(seconds: float) -> str
log_message(message: str, log_file: str | Path) -> None
log_elapsed(label: str, seconds: float, log_file: str | Path) -> None
read_logs(log_file: str | Path) -> list[str]
clear_logs(log_file: str | Path) -> None
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## Заметка от ZuroKing

> Таймер — первый раз, когда "сейчас" перестаёт быть часами на стене и становится счётчиком, который можно замокать. Держи `perf_counter` внутри `Timer` и больше никто не знает о времени — поэтому `patch("timer_logger.timer.time.perf_counter")` тестирует всю логику без сна. Логи делай простым `append`: `isoformat` + `Path.mkdir` + `open(..., "a")`. Тогда Timer остаётся глупым — старт, стоп, может одна строка в файл — а хелперы `format_elapsed`/`log_message` чисты и проверяются через `tmp_path`. Этот разрез и есть урок: контекст-менеджер — просто `__enter__` старт и `__exit__` стоп.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.

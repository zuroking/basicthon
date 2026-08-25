# 10 — Мини-фреймворк тестирования

Изолированный учебный проект из серии `basicthon` (Structures & Patterns).

**Что изучаем (lock scope):** как работают ассерты, как собирать результаты тестов без стороннего раннера и как фреймворк тестирует сам себя. Проект в три этапа: minimal — `assert_equal`/`assert_raises`, датакласс `TestResult` и `run_tests` на демо-наборе; improved — дополнительные ассерты (`assert_true`/`assert_false`/`assert_in`/`assert_not_in`/`assert_not_equal`), `assert_raises` как контекст-менеджер, `format_results`/`summarize`; production-like — типизация, тесты, `ruff/black/mypy`, CLI с `--verbose`/`--list`.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` для этого проекта stdlib-only (`# stdlib only, no external dependencies`).

## Использование

Запустить встроенный демо-набор (все 8 тестов должны пройти):

```bash
python -m mini_test
# 8 passed, 0 failed, 8 total

python -m mini_test --verbose
# PASS: test_add
# ...

python -m mini_test --list
# test_add
# test_sub
# ...
```

После `pip install -e .`:

```bash
mini-test --verbose
mini-test --list
```

Как библиотека:

```python
from mini_test import assert_equal, assert_raises, run_tests, get_demo_suite, format_results

assert_equal(1 + 1, 2)
assert_raises(ValueError, int, "bad")
with assert_raises(ValueError):
    int("bad")

def test_add():
    assert_equal(2 + 3, 5)

results = run_tests({"test_add": test_add})
print(format_results(results, verbose=True))

# фреймворк тестирует сам себя
results = run_tests(get_demo_suite())
print(format_results(results))
# 8 passed, 0 failed, 8 total

# проверка что падений детектируются
def failing():
    assert_equal(1, 2)
mixed = {**get_demo_suite(), "fail": failing}
print(format_results(run_tests(mixed), verbose=True))
```

Детали:

- `assert_equal(actual, expected, msg=None)` бросает `AssertionError` с `"{actual!r} != {expected!r}"` если не равны. Остальные ассерты — аналогично с `msg`.
- `assert_raises(expected, func=None, *args, **kwargs)` — два стиля: `assert_raises(ValueError, int, "bad")` или `with assert_raises(ValueError): int("bad")`. Возвращает контекст-менеджер если `func is None`. Сообщение `"expected X but got Y"` / `"no exception"`.
- `TestResult(name, passed, error)` — датакласс. `run_test(name, func)` ловит `AssertionError` и любые исключения (с трейсбэком). `run_tests(dict)` — в порядке вставки.
- `format_results(results, verbose=False)` — точки (`"."`/`"F"`) + строки `FAIL` + итог `"N passed, M failed, K total"`; `verbose=True` — строки `PASS:`/`FAIL:`.
- `get_demo_suite()` возвращает копию `DEMO_SUITE` (8 проходящих демо-тестов).

## Этапы

**Minimal:** `assert_equal`/`assert_raises` (бросают `AssertionError`), `TestResult(name, passed, error)`, `run_test` с `try/except`, `run_tests(dict)` циклом, демо-логика `_demo_add`/`_demo_div` и `DEMO_SUITE` из 2–3 тестов, `get_demo_suite()`.

**Improved:** Добавлены `assert_not_equal`/`assert_true`/`assert_false`/`assert_in`/`assert_not_in` с `msg`, `_AssertRaisesContext` для `with assert_raises(Exc):` (`exception` + `__enter__`/`__exit__`), `format_results`/`summarize`, расширение демо до 8 тестов (`is_even`/`reverse`/`in`) и контекст-стиль в `demo_test_div_zero`.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy` без ошибок (обычный, не `--strict` для 01–10), `pytest` зелёный через самотест (`run_tests(get_demo_suite())` все `passed` + mixed ловит падение), CLI на `argparse` с `--verbose`/`--list` и `exit 1` при падении, точка входа `python -m mini_test`.

## API

```python
from mini_test import TestResult, assert_equal, assert_not_equal, assert_true, assert_false, assert_in, assert_not_in, assert_raises, run_test, run_tests, format_results, summarize, get_demo_suite, DEMO_SUITE

assert_equal(actual, expected, msg: str | None = None) -> None
assert_not_equal(actual, expected, msg: str | None = None) -> None
assert_true(value, msg: str | None = None) -> None
assert_false(value, msg: str | None = None) -> None
assert_in(item, container, msg: str | None = None) -> None
assert_not_in(item, container, msg: str | None = None) -> None
assert_raises(expected: type[BaseException], func=None, *args, **kwargs) -> Any

TestResult(name: str, passed: bool, error: str | None = None)
run_test(name: str, func: Callable[[], None]) -> TestResult
run_tests(tests: dict[str, Callable[[], None]]) -> list[TestResult]
format_results(results: list[TestResult], verbose: bool = False) -> str
summarize(results: list[TestResult]) -> dict[str, int]
get_demo_suite() -> dict[str, Callable[[], None]]
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## Заметка от ZuroKing

> Свой раннер — первый раз когда тестирование перестаёт быть магией и становится `try/except` вокруг функции. Делай ассерты глупыми: сравни и брось `AssertionError` с понятным сообщением. Пусть единственная умная вещь — `run_test`, который ловит ошибку и пакует `TestResult(name, passed, error)`. Тогда `run_tests` — цикл, `format_results` — счётчик, а самотест — одна строка: `run_tests(get_demo_suite())` должен быть зелёным. Как только почувствуешь этот цикл, `pytest` перестанет быть чёрным ящиком.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.

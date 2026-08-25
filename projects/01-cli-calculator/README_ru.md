# 01 — CLI-калькулятор

Изолированный учебный проект из серии `basicthon` (Foundations).

**Что изучаем (lock scope):** Базовый ввод-вывод, чистые функции, обработку ошибок и безопасный парсинг выражений. Проект строится в три этапа: minimal — четыре арифметические функции + CLI с двумя числами; improved — безопасный вычислитель выражений на `ast` со скобками и приоритетами; production-like — типизация, тесты, REPL и понятные сообщения об ошибках.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` для этого проекта stdlib-only (`# stdlib only, no external dependencies`).

## Использование

Вычислить одно выражение:

```bash
python -m cli_calculator "2 + 3 * (4 - 1)"
# 11

python -m cli_calculator --expr "10 / 4"
# 2.5
```

Интерактивный режим (без аргументов):

```bash
python -m cli_calculator
>> 2 + 3 * 4
14
>> exit
```

После `pip install -e .` доступен скрипт:

```bash
calc "2 ** 3 + 1"
# 9
```

## Этапы

**Minimal:** `add`/`subtract`/`multiply`/`divide` + CLI для двух чисел и оператора.

**Improved:** `evaluate()` безопасно парсит выражение через `ast` (без `eval()`), поддерживает `+ - * / // % **`, скобки, унарные `+/-`, пробелы и float, только разрешённые узлы AST.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy` без ошибок, `pytest` зелёный для каждой публичной функции в `src/cli_calculator/calculator.py` (кроме `cli.py` по §5 ARCHITECTURE.md), понятные ошибки (`ValueError` — синтаксис, `ZeroDivisionError`).

## API

```python
from cli_calculator import add, subtract, multiply, divide, power, evaluate

add(2, 3)          # 5
evaluate("2 + 3 * 4")  # 14.0
evaluate("(2 + 3) * 4")  # 20.0
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy .
```

## Заметка от ZuroKing

> Я специально не использую `eval()` — новички часто тянутся к нему. `ast` с белым списком — маленький урок "безопасно по умолчанию", который окупается задолго до темы auth/БД. Запомни привычку: *парси, а не исполняй*.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.

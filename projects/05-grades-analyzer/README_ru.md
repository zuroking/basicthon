# 05 — Анализатор оценок из CSV

Изолированный учебный проект из серии `basicthon` (Foundations).

**Что изучаем (lock scope):** Парсинг CSV через `csv` + `pathlib`, типизированную статистику (среднее/медиана/min/max), сортировку и бакеты, разделение чистой логики и I/O. Проект строится в три этапа: minimal — `parse_csv` + `average` на `csv.DictReader`; improved — `median`/`min_grade`/`max_grade`/`top_n` с валидацией; production-like — типизация, тесты, CLI на `argparse` и тесты на `tmp_path`.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` для этого проекта stdlib-only (`# stdlib only, no external dependencies`).

## Использование

Создай CSV (заголовок обязан содержать `grade`):

```csv
name,grade
Alice,95
Bob,82
Cara,91
Dan,60
```

Запусти анализ:

```bash
python -m grades_analyzer grades.csv
# records: 4
# average: 82.00
# median: 86.50
# ...

python -m grades_analyzer grades.csv --top 2
```

После `pip install -e .`:

```bash
grades-analyzer grades.csv --top 5
```

Как библиотека:

```python
from grades_analyzer import parse_csv, average, median, top_n, grade_distribution

rows = parse_csv("grades.csv")
print(average(rows))
print(grade_distribution(rows))  # {'A': 2, 'B': 1, ...}
```

Extra-столбцы (например, `subject`) сохраняются в `parse_csv`, но игнорируются статистикой.

## Этапы

**Minimal:** `parse_csv(path)` через `csv.DictReader` и `average(records)` (`sum/len`, `0.0` для пустого). Проверяет наличие столбца `grade`, `ValueError` на плохие значения, `FileNotFoundError` если файла нет.

**Improved:** `median(records)` (сортировка, чёт/нечёт, `0.0` для пустого), `min_grade`/`max_grade` (`ValueError` если пусто), `top_n(records, n=3)` — стабильная сортировка по убыванию, `grade_distribution(records)` — бакеты `A` 90+, `B` 80–89, `C` 70–79, `D` 60–69, `F` <60. Чистые функции работают с `list[dict[str, str]]`.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy` без ошибок, `pytest` зелёный для каждой публичной функции в `src/grades_analyzer/analyzer.py` (кроме `cli.py` по §5 ARCHITECTURE.md) с `tmp_path`, CLI на `argparse` с позиционным `csv` и флагом `--top`, точка входа `python -m grades_analyzer`.

## API

```python
from grades_analyzer import parse_csv, average, median, min_grade, max_grade, top_n, grade_distribution

parse_csv(path: str | Path) -> list[dict[str, str]]
average(records) -> float          # 0.0 для пустого
median(records) -> float           # 0.0 для пустого
min_grade(records) -> float        # ValueError если пусто
max_grade(records) -> float        # ValueError если пусто
top_n(records, n=3) -> list[dict[str, str]]
grade_distribution(records) -> dict[str, int]
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## Заметка от ZuroKing

> CSV кажется простым, пока не встретишь кривые заголовки и нечисловые оценки. Приём простой: валидируй рано (`grade` есть, каждое значение — число), держи парсинг в одном месте (`parse_csv`), а математику — чистой (функции берут `list[dict]`, а не путь). Тогда CLI — просто клей: `parse_csv` → `average/median/...` → `print`, а тестам хватает `tmp_path`, чтобы покрыть каждое правило.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.

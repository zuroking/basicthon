# 02 — Угадай число + Камень-ножницы-бумага

Изолированный проект `basicthon` (Foundations).

**Что изучаем:** `random`, чистые функции, валидацию ввода, ветвления. Три этапа: minimal — функции `check_guess`/`rps_result`; improved — случайные секреты и интерактивные циклы; production-like — типизация, тесты, CLI с `--mode`.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

## Использование

```bash
python -m guess_rps --mode guess --low 1 --high 100
python -m guess_rps --mode rps
```

## Этапы

**Minimal:** `check_guess`, `rps_result`.

**Improved:** `random_secret`, `random_rps_choice`, циклы `input()`.

**Production-like:** Type hints, `ruff`/`black`/`mypy`, тесты для каждой публичной функции вне `cli.py`.

## Заметка от ZuroKing

> Две мини-игры, один урок: отделяй чистую логику от ввода-вывода. `game.py` без `input()`/`print()` — тестируется без моков.

## Изоляция

Папка автономна.

# 03 — Генератор паролей

Изолированный учебный проект из серии `basicthon` (Foundations).

**Что изучаем (lock scope):** Криптографически стойкую генерацию через `secrets`, валидацию входных данных и простую эвристику силы пароля. Проект строится в три этапа: minimal — генерация из фиксированного набора символов; improved — настраиваемый charset (заглавные/цифры/символы) и проверка длины; production-like — типизация, тесты, `secrets.choice`, оценка силы и CLI на argparse.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` для этого проекта stdlib-only (`# stdlib only, no external dependencies`).

## Использование

Генерация пароля по умолчанию (12 символов, lower + upper + digits):

```bash
python -m password_generator
# aB3xK9mQ2pLq

python -m password_generator --length 16 --symbols
# aB3!xK9$mQ2@pLq&

python -m password_generator --length 8 --no-upper --no-digits
# abcdwxyz
```

После `pip install -e .` доступен скрипт:

```bash
passgen --length 20 --symbols
# 9fG!2bQ@...
```

Как библиотека:

```python
from password_generator import generate_password, check_strength

pwd = generate_password(length=16, use_symbols=True)
print(pwd, check_strength(pwd))
# "aB3!..." "strong"
```

## Этапы

**Minimal:** `generate_password(length)` с фиксированным `string.ascii_letters + string.digits`, `secrets.choice`, проверка `length >= 4`.

**Improved:** Настраиваемый набор через `use_upper`/`use_digits`/`use_symbols` (строчные всегда включены), хелпер `_build_charset()` с `ValueError` если набор пуст, `string.punctuation` для символов.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy` без ошибок, `pytest` зелёный для каждой публичной функции в `src/password_generator/generator.py` (кроме `cli.py` по §5 ARCHITECTURE.md), `check_strength()` возвращает `"weak"`/`"medium"`/`"strong"` по длине и разнообразию, CLI с `--length`/`--no-upper`/`--no-digits`/`--symbols`.

## API

```python
from password_generator import generate_password, check_strength

generate_password(length=12, use_upper=True, use_digits=True, use_symbols=False) -> str
# ValueError если length < 4 или charset пуст

check_strength("aB3!5678")  # "strong"
check_strength("abcdef12")  # "medium"
check_strength("abc")       # "weak"
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## Заметка от ZuroKing

> Для паролей никогда не используй `random` — он предсказуем. Даже в учебном проекте бери `secrets`. Привычка "для токенов и паролей — только secrets" сейчас ничего не стоит, а позже спасёт, когда будешь работать с реальными секретами.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.

# 06 — Контакты (ООП)

Изолированный учебный проект из серии `basicthon` (Structures & Patterns).

**Что изучаем (lock scope):** ООП на классах, инкапсуляция через `property`, валидация, CRUD в памяти и CLI на `argparse`. Проект строится в три этапа: minimal — класс `Contact` с валидацией `name/phone/email`; improved — `ContactBook` с `add/get/update/delete/search/list`; production-like — типизация, тесты, `ruff/black/mypy` и CLI с JSON-персистентностью.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` для этого проекта stdlib-only (`# stdlib only, no external dependencies`).

## Использование

```bash
python -m contacts add "Alice" "+7 999 123-45-67" "alice@example.com"
python -m contacts add "Bob" "123-456-7890" "bob@example.com"

python -m contacts list
# Alice | +7 999 123-45-67 | alice@example.com
# Bob | 123-456-7890 | bob@example.com

python -m contacts get "alice"
python -m contacts search "ali"
python -m contacts update "Alice" --phone "+7 999 000-11-22"
python -m contacts delete "Bob"
```

Кастомный файл:

```bash
python -m contacts --file /tmp/my.json add "Cara" "5551234567" "cara@test.com"
python -m contacts --file /tmp/my.json list
```

После `pip install -e .`:

```bash
contacts add "Dan" "1234567" "dan@example.com"
contacts list
```

Как библиотека:

```python
from contacts import Contact, ContactBook

book = ContactBook()
book.add(Contact("Alice", "+7 999 123-45-67", "alice@example.com"))
book.add("Bob", "123-456-7890", "bob@example.com")
print(book.get("alice"))
print(book.search("ali"))
print(book.list_contacts())
book.update("Alice", phone="9999999")
book.delete("Bob")
```

Правила валидации:

- `name`: непустое, 1-100 символов после `strip`.
- `phone`: 5-15 цифр, разрешены `+ - ( ) .` и пробел.
- `email`: регекс `^[^@\s]+@[^@\s]+\.[^@\s]+$`.

Поиск и операции `get/update/delete` — case-insensitive по `name`. `search` — подстрока без учёта регистра в `name/phone/email`. Дубликат `name` → `ValueError`.

## Этапы

**Minimal:** Класс `Contact` с валидаторами `_validate_*`, свойствами `name/phone/email` с повторной валидацией в setter, `__repr__/__eq__/to_dict/from_dict`, `ValueError` на пустые/невалидные поля.

**Improved:** `ContactBook` на `dict[str, Contact]` с ключом `name.lower()`. Методы `add(contact|name, phone, email)`, `get(name) -> Contact | None`, `update(name, phone?, email?)`, `delete(name)`, `search(query) -> list[Contact]`, `list_contacts() -> list[Contact]` (сортировка) + алиасы `list_all` и `list`. Дубликаты/не найдено → `ValueError`, `search` с пустым запросом → `[]`.

**Production-like:** Type hints на всех публичных методах, `ruff`/`black`/`mypy` без ошибок, `pytest` зелёный для каждого публичного метода в `src/contacts/contact.py` (кроме `cli.py` по §5 ARCHITECTURE.md), CLI на `argparse` с подкомандами `add/get/update/delete/search/list`, флаг `--file`, точка входа `python -m contacts`.

## API

```python
from contacts import Contact, ContactBook

Contact(name: str, phone: str, email: str)
# property: name, phone, email
# to_dict() -> dict[str, str], from_dict(data) -> Contact

ContactBook()
# add(contact: Contact | str, phone=None, email=None) -> Contact
# get(name: str) -> Contact | None
# update(name: str, phone=None, email=None) -> Contact
# delete(name: str) -> None
# search(query: str) -> list[Contact]
# list_contacts() -> list[Contact], list_all(), list()
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy src
```

## Заметка от ZuroKing

> ООП тут не про "больше кода", а про границы. `Contact` — ворота: вся валидация `name/phone/email` в одном месте, `ContactBook` никогда не видит грязные данные. Книга тупая: `dict` по `name.lower()`, без магии нормализации, явный `ValueError` на дубликаты. Тогда тесты просты: создал `ContactBook`, вызвал шесть методов, проверил. А CLI — просто клей: `Contact`/`ContactBook` → `json` → `print` — и это главный урок до баз данных.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.

# 15 — Генератор текста на цепях Маркова

Изолированный учебный проект из серии `basicthon` (Data & Algorithms).

**Что изучаем (lock scope):** построение цепи Маркова из текста с `collections` и генерация нового текста с `random`. Проект в три этапа: minimal — `build_chain`/`generate` для порядка 1 на словах через `split` с `collections.defaultdict(list)` и `random.choice`; improved — поддержка n-грамм `order` 1..5, `seed` для детерминизма через `random.Random(seed)`, валидация `start`-состояния, обработка тупиков и строгая валидация входов; production-like — типизация, тесты, `ruff/black/mypy --strict`, CLI на `argparse` с детерминированными тестами.

## Установка

```bash
pip install -e .
pip install -r requirements.txt
```

> `requirements.txt` — только stdlib для этого проекта (`# stdlib only, no external dependencies`).

## Использование

Генерация из строки или файла:

```bash
python -m markov_generator "hello world hello there world hello there"
# hello there world hello ...

python -m markov_generator --file story.txt --order 2 --length 30 --seed 42
# once upon a time there was ...

python -m markov_generator "a b a c a b a d" --order 1 --length 10 --seed 0 --start "a"
# a b a c a b a d a b

# порядок 2 и фиксированный seed
python -m markov_generator "the cat sat on the mat the cat ate" --order 2 --length 15 --seed 123
# the cat ate ...
```

После `pip install -e .`:

```bash
markov-generator "hello world hello there" --length 10 --seed 1
markov-generator --file inputs/sample.txt --order 2 --length 20 --seed 42
markov-generator "a b c a b d" --order 2 --seed 0 --start "a b"
```

Как библиотека:

```python
from markov_generator import build_chain, generate

text = "hello world hello there world hello"
chain = build_chain(text, order=1)
print(chain)
# {('hello',): ['world', 'there'], ('world',): ['hello'], ('there',): ['world']}

print(generate(chain, length=10, seed=42))
# hello world hello there world hello there world hello ...

# цепь порядка 2
chain2 = build_chain("a b c a b d a b e", order=2)
print(chain2)
# {('a', 'b'): ['c', 'd', 'e'], ('b', 'c'): ['a'], ('c', 'a'): ['b'], ...}

print(generate(chain2, length=6, seed=0, start=("a", "b")))
# a b c a b d

# детерминизм: одинаковый seed -> одинаковый результат
assert generate(chain, length=5, seed=0) == generate(chain, length=5, seed=0)
```

Детали:

- `build_chain(text: str, order: int = 1) -> dict[tuple[str, ...], list[str]]` — валидирует `text` как `str` и `order` как `int` 1..5 (отклоняет `bool`), делит по `split`, возвращает `{}` если `len(words) <= order`, иначе отображает каждый `order`-грам кортеж в список последователей через `collections.defaultdict(list)`.
- `generate(chain: dict[tuple[str, ...], list[str]], length: int = 20, seed: int | None = None, start: tuple[str, ...] | None = None) -> str` — валидирует непустую цепь, одинаковую длину ключей, непустые `list[str]` значений, `length` 1..1000, `seed` int если указан, `start` кортеж matching order и существующий в цепи. Использует `random.Random(seed)` и `rng.choice` для детерминированного обхода; стартует со случайного ключа если `start` None, идёт через `tuple(result[-order:])`, останавливается рано при тупике, возвращает `" ".join(result[:length])`.

## Этапы

**Minimal:** `build_chain(text, order=1)` с `split`, `collections.defaultdict(list)`, цикл `for i in range(len(words)-order): key=tuple(words[i:i+order]), chain[key].append(words[i+order])`, `generate(chain, length=20)` случайный обход от случайного ключа через `random.choice`, `join`. Базовый `ValueError` на неверных типах.

**Improved:** `order` 1..5, `seed` через `random.Random(seed)` для детерминизма, `start` с валидацией (длина кортежа совпадает с порядком, ключ есть в цепи), `length` 1..1000, break при тупике когда `chain.get(key)` отсутствует, валидация формы цепи (ключи кортежи, значения списки, одинаковый порядок, непустые строки), пустой/пробельный текст → `{}`, отклонение `bool` для `text`/`order`.

**Production-like:** Type hints на всех публичных функциях, `ruff`/`black`/`mypy --strict` без ошибок (strict для 11–20 по §8 ARCHITECTURE.md), `pytest` зелёный для каждой публичной функции в `src/markov_generator/markov.py` (кроме `cli.py` по §5) с детерминированными `seed`-тестами, CLI на `argparse` с `text`/`--file`/`--order`/`--length`/`--seed`/`--start` и точка входа `python -m markov_generator`.

## API

```python
from markov_generator import build_chain, generate

build_chain(text: str, order: int = 1) -> dict[tuple[str, ...], list[str]]
generate(chain: dict[tuple[str, ...], list[str]], length: int = 20, seed: int | None = None, start: tuple[str, ...] | None = None) -> str
```

## Тестирование

```bash
pytest -v
ruff check .
black --check .
mypy --strict src
```

## Заметка от ZuroKing

> Новички думают, что генерация текста — магия LLM. Покажите примитив: цепь Маркова помнит только последние `order` слов. При `order=1` за `"hello"` идёт то, что шло после `hello` раньше — `world` или `there`. `collections.defaultdict(list)` строит таблицу, `random.Random(seed).choice` идёт по ней. Держите границу жёстко: `markov.py` знает только `collections` + `random` + валидацию, никакого `argparse` и `print`. Сделайте `seed` явным, чтобы тесты были детерминированы (`generate(chain, seed=0)` всегда одинаково), обрабатывайте тупики остановкой, и валидируйте всё (`order` 1..5, `length` 1..1000, `start` должен существовать). Тогда CLI остаётся склейкой `parse_args → build_chain → generate → print`, а тесты честны без моков — просто `seed`.

## Изоляция

Папка полностью автономна — скопируйте её куда угодно и `pip install -e . && pip install -r requirements.txt` достаточно. Общий код с другими проектами `basicthon` отсутствует.

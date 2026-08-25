"""Core logic for Markov chain text generator.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded.

Uses :mod:`random` for deterministic generation via ``seed`` and
:mod:`collections` for chain building.

Chain type is ``dict[tuple[str, ...], list[str]]`` where each key is a
state tuple of length ``order`` and value is the list of possible
successors (order-1 Markov chain, n-gram). ``build_chain`` splits text on
whitespace; ``generate`` walks the chain with ``random.Random(seed)``.
"""

from __future__ import annotations

import collections
import random


def build_chain(text: str, order: int = 1) -> dict[tuple[str, ...], list[str]]:
    """Build Markov chain from text.

    Splits ``text`` on whitespace into words, then maps each ``order``-gram
    to its successors. Example for ``order=1`` and ``"a b a c"``::

        {("a",): ["b", "c"], ("b",): ["a"]}

    Args:
        text: source text, must be a string. Empty/whitespace returns ``{}``.
        order: n-gram order, integer 1..5 inclusive.

    Returns:
        Mapping ``{state: [next_word, ...]}``. Empty if fewer words than
        ``order + 1``.

    Raises:
        ValueError: if ``text`` is not a string or ``order`` is not an
            integer 1..5.
    """
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if isinstance(order, bool):
        raise ValueError("order must be an integer")
    if not isinstance(order, int):
        raise ValueError("order must be an integer")
    if order < 1 or order > 5:
        raise ValueError("order must be between 1 and 5")

    words: list[str] = text.split()
    if len(words) <= order:
        return {}

    tmp: collections.defaultdict[tuple[str, ...], list[str]] = collections.defaultdict(
        list
    )
    for i in range(len(words) - order):
        key: tuple[str, ...] = tuple(words[i : i + order])
        nxt: str = words[i + order]
        tmp[key].append(nxt)
    return dict(tmp)


def generate(
    chain: dict[tuple[str, ...], list[str]],
    length: int = 20,
    seed: int | None = None,
    start: tuple[str, ...] | None = None,
) -> str:
    """Generate text by walking the Markov chain.

    Args:
        chain: mapping from state tuple to successors, as produced by
            :func:`build_chain`. Must be non-empty, keys are
            ``tuple[str, ...]`` of uniform length, values are non-empty
            ``list[str]``.
        length: number of words to generate, integer 1..1000 inclusive.
        seed: optional seed for ``random.Random`` to make output
            deterministic. If ``None``, uses system randomness.
        start: optional starting state tuple. Must match chain order and
            exist as a key. If ``None``, a random key is chosen.

    Returns:
        Space-joined generated words, at most ``length`` words (may be
        shorter if chain dead-ends).

    Raises:
        ValueError: if inputs are of wrong type, out of range, or chain
            is empty / inconsistent, or ``start`` not in chain.
    """
    if not isinstance(chain, dict):
        raise ValueError("chain must be a dict")
    if len(chain) == 0:
        raise ValueError("chain is empty")

    # Validate chain shape and deduce order
    order: int | None = None
    for k, v in chain.items():
        if not isinstance(k, tuple):
            raise ValueError("chain keys must be tuples of strings")
        if len(k) == 0:
            raise ValueError("chain keys must be non-empty tuples")
        if not all(isinstance(w, str) for w in k):
            raise ValueError("chain keys must be tuples of strings")
        if any(not w for w in k):
            raise ValueError("chain keys must not contain empty strings")
        if not isinstance(v, list):
            raise ValueError("chain values must be lists of strings")
        if len(v) == 0:
            raise ValueError("chain values must be non-empty lists")
        if not all(isinstance(w, str) for w in v):
            raise ValueError("chain values must be lists of strings")
        if any(not w for w in v):
            raise ValueError("chain values must not contain empty strings")
        if order is None:
            order = len(k)
        elif len(k) != order:
            raise ValueError("chain keys must all have same length")

    assert order is not None  # for mypy: chain non-empty guarantees order set

    if isinstance(length, bool):
        raise ValueError("length must be an integer")
    if not isinstance(length, int):
        raise ValueError("length must be an integer")
    if length < 1 or length > 1000:
        raise ValueError("length must be between 1 and 1000")

    if seed is not None:
        if isinstance(seed, bool):
            raise ValueError("seed must be an integer")
        if not isinstance(seed, int):
            raise ValueError("seed must be an integer")

    if start is not None:
        if not isinstance(start, tuple):
            raise ValueError("start must be a tuple of strings")
        if len(start) != order:
            raise ValueError(f"start must have length {order} (chain order)")
        if not all(isinstance(w, str) for w in start):
            raise ValueError("start must be a tuple of strings")
        if any(not w for w in start):
            raise ValueError("start must not contain empty strings")
        if start not in chain:
            raise ValueError("start not found in chain")

    rng: random.Random = random.Random(seed)

    result: list[str]
    current: tuple[str, ...]
    if start is not None:
        current = start
        result = list(current)
        if len(result) > length:
            return " ".join(result[:length])
    else:
        keys: list[tuple[str, ...]] = list(chain.keys())
        current = rng.choice(keys)
        result = list(current)

    # If requested length equals order and we already have it, return
    if len(result) >= length:
        return " ".join(result[:length])

    while len(result) < length:
        key: tuple[str, ...] = tuple(result[-order:])
        successors: list[str] | None = chain.get(key)
        if not successors:
            break
        nxt_word: str = rng.choice(successors)
        result.append(nxt_word)

    return " ".join(result[:length])

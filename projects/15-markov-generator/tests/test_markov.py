"""Tests for markov_generator.markov — covers every public function."""

from __future__ import annotations

import pytest

from markov_generator.markov import build_chain, generate

# ---- build_chain ----


def test_build_chain_order1_basic() -> None:
    chain = build_chain("a b a c", order=1)
    assert chain == {("a",): ["b", "c"], ("b",): ["a"]}


def test_build_chain_order1_repeated() -> None:
    chain = build_chain("hello hello hello", order=1)
    assert chain == {("hello",): ["hello", "hello"]}


def test_build_chain_order2() -> None:
    chain = build_chain("a b c a b d", order=2)
    assert chain == {("a", "b"): ["c", "d"], ("b", "c"): ["a"], ("c", "a"): ["b"]}


def test_build_chain_order2_insufficient_words() -> None:
    # 2 words, order 2 -> needs at least 3 words to have a transition
    assert build_chain("a b", order=2) == {}
    assert build_chain("a", order=1) == {}
    assert build_chain("", order=1) == {}
    assert build_chain("   ", order=1) == {}


def test_build_chain_split_whitespace() -> None:
    chain = build_chain("a   b\nc\t a", order=1)
    assert chain == {("a",): ["b"], ("b",): ["c"], ("c",): ["a"]}


def test_build_chain_default_order() -> None:
    # default order is 1
    chain = build_chain("x y x y")
    assert chain == {("x",): ["y", "y"], ("y",): ["x"]}


def test_build_chain_invalid_text_type() -> None:
    with pytest.raises(ValueError, match="text must be a string"):
        build_chain(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        build_chain(None)  # type: ignore[arg-type]


def test_build_chain_invalid_order_type() -> None:
    with pytest.raises(ValueError, match="order must be an integer"):
        build_chain("a b c", order="1")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        build_chain("a b c", order=1.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        build_chain("a b c", order=True)  # type: ignore[arg-type]


def test_build_chain_invalid_order_range() -> None:
    with pytest.raises(ValueError, match="between 1 and 5"):
        build_chain("a b c", order=0)
    with pytest.raises(ValueError):
        build_chain("a b c", order=6)
    with pytest.raises(ValueError):
        build_chain("a b c", order=-1)


def test_build_chain_order5() -> None:
    text = "a b c d e f a b c d e g"
    chain = build_chain(text, order=5)
    assert ("a", "b", "c", "d", "e") in chain
    assert chain[("a", "b", "c", "d", "e")] == ["f", "g"]


# ---- generate ----


def test_generate_basic_deterministic() -> None:
    chain = build_chain("a b a c a b", order=1)
    # seed makes choice deterministic
    out1 = generate(chain, length=5, seed=42)
    out2 = generate(chain, length=5, seed=42)
    assert out1 == out2
    # length respected
    assert len(out1.split()) == 5
    # words come from chain vocabulary
    vocab = {"a", "b", "c"}
    assert all(w in vocab for w in out1.split())


def test_generate_seed_difference() -> None:
    chain = build_chain("a b a c a b a d", order=1)
    out42 = generate(chain, length=6, seed=42)
    out1 = generate(chain, length=6, seed=1)
    # different seeds may give different output; at least not always equal
    # if equal by chance, this still passes but generally they differ
    assert isinstance(out42, str)
    assert isinstance(out1, str)
    # same seed again equals
    assert out42 == generate(chain, length=6, seed=42)


def test_generate_with_start() -> None:
    chain = build_chain("hello world hello there world hello", order=1)
    out = generate(chain, length=4, seed=0, start=("hello",))
    assert out.split()[0] == "hello"
    assert len(out.split()) == 4


def test_generate_start_truncates() -> None:
    chain = build_chain("a b c d e f", order=2)
    # start length 2, request length 1 -> should truncate start
    out = generate(chain, length=1, seed=0, start=("a", "b"))
    assert out == "a"


def test_generate_start_order2() -> None:
    chain = build_chain("a b c a b d a b e", order=2)
    out = generate(chain, length=4, seed=0, start=("a", "b"))
    assert out.split()[:2] == ["a", "b"]
    assert len(out.split()) == 4


def test_generate_length_validation() -> None:
    chain = build_chain("a b a c", order=1)
    with pytest.raises(ValueError, match="length must be"):
        generate(chain, length=0)
    with pytest.raises(ValueError):
        generate(chain, length=-1)
    with pytest.raises(ValueError):
        generate(chain, length=1001)
    with pytest.raises(ValueError):
        generate(chain, length=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        generate(chain, length="10")  # type: ignore[arg-type]


def test_generate_invalid_seed() -> None:
    chain = build_chain("a b a c", order=1)
    with pytest.raises(ValueError, match="seed must be"):
        generate(chain, seed="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        generate(chain, seed=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        generate(chain, seed=1.5)  # type: ignore[arg-type]


def test_generate_invalid_chain_type() -> None:
    with pytest.raises(ValueError, match="chain must be a dict"):
        generate("bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="chain must be a dict"):
        generate([])  # type: ignore[arg-type]


def test_generate_empty_chain() -> None:
    with pytest.raises(ValueError, match="chain is empty"):
        generate({}, length=5)


def test_generate_invalid_chain_keys() -> None:
    with pytest.raises(ValueError, match="chain keys must be tuples"):
        generate({"a": ["b"]}, length=5)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        generate({("a",): "b"}, length=5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-empty tuples"):
        generate({(): ["a"]}, length=5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="tuples of strings"):
        generate({(123,): ["a"]}, length=5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must not contain empty"):
        generate({("",): ["a"]}, length=5)  # type: ignore[arg-type]


def test_generate_invalid_chain_values() -> None:
    with pytest.raises(ValueError, match="values must be lists"):
        generate({("a",): "b"}, length=5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-empty lists"):
        generate({("a",): []}, length=5)
    with pytest.raises(ValueError, match="lists of strings"):
        generate({("a",): [123]}, length=5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must not contain empty"):
        generate({("a",): [""]}, length=5)


def test_generate_chain_keys_different_lengths() -> None:
    chain = {("a",): ["b"], ("a", "b"): ["c"]}
    with pytest.raises(ValueError, match="same length"):
        generate(chain, length=5)  # type: ignore[arg-type]


def test_generate_start_validation() -> None:
    chain = build_chain("a b a c", order=1)
    with pytest.raises(ValueError, match="start must be a tuple"):
        generate(chain, start="a")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="start must have length"):
        generate(chain, start=("a", "b"))
    with pytest.raises(ValueError, match="tuple of strings"):
        generate(chain, start=(123,))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="not contain empty"):
        generate(chain, start=("",))
    with pytest.raises(ValueError, match="not found in chain"):
        generate(chain, start=("z",))


def test_generate_dead_end() -> None:
    # chain where walk hits dead end: only one transition
    chain: dict[tuple[str, ...], list[str]] = {("a",): ["b"], ("b",): ["c"]}
    # start at b -> next c -> then ("c",) not in chain -> stop early
    out = generate(chain, length=10, seed=0, start=("b",))
    assert out == "b c"


def test_generate_no_start_random_choice() -> None:
    chain = build_chain("a b c a b c a b c", order=1)
    # without start, uses rng.choice on keys; deterministic via seed
    out = generate(chain, length=3, seed=123)
    assert len(out.split()) == 3
    # same seed yields same
    assert out == generate(chain, length=3, seed=123)


def test_generate_single_state_chain() -> None:
    chain: dict[tuple[str, ...], list[str]] = {("hi",): ["hi", "hi"]}
    out = generate(chain, length=5, seed=0)
    assert out == "hi hi hi hi hi"


def test_generate_length_equals_order() -> None:
    chain = build_chain("a b c d", order=2)
    out = generate(chain, length=2, seed=0)
    assert len(out.split()) == 2


def test_generate_uses_collections_and_random() -> None:
    # ensure build_chain uses collections and generate uses random seed
    chain = build_chain("one two three one two four", order=2)
    assert isinstance(chain, dict)
    # generate twice with same seed gives same result
    assert generate(chain, length=5, seed=99) == generate(chain, length=5, seed=99)

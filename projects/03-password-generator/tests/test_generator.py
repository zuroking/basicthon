"""Tests for password generator — covers every public function (G-13/GRILL2-05)."""

from __future__ import annotations

import string

import pytest

from password_generator.generator import (
    _build_charset,
    check_strength,
    generate_password,
)

# ---- _build_charset (helper) ----


def test_build_charset_default() -> None:
    charset = _build_charset()
    assert string.ascii_lowercase in charset or all(
        c in charset for c in string.ascii_lowercase
    )
    assert all(c in charset for c in string.ascii_uppercase)
    assert all(c in charset for c in string.digits)
    assert (
        not any(c in charset for c in string.punctuation)
        or string.punctuation not in charset
    )


def test_build_charset_no_upper_no_digits() -> None:
    charset = _build_charset(use_upper=False, use_digits=False, use_symbols=False)
    assert charset == string.ascii_lowercase


def test_build_charset_with_symbols() -> None:
    charset = _build_charset(use_upper=False, use_digits=False, use_symbols=True)
    assert string.ascii_lowercase in charset
    assert string.punctuation in charset
    assert not any(c in charset for c in string.ascii_uppercase)


def test_build_charset_all_enabled() -> None:
    charset = _build_charset(use_upper=True, use_digits=True, use_symbols=True)
    for ch in string.ascii_lowercase:
        assert ch in charset
    for ch in string.ascii_uppercase:
        assert ch in charset
    for ch in string.digits:
        assert ch in charset
    for ch in string.punctuation:
        assert ch in charset


# ---- generate_password ----


def test_generate_default() -> None:
    pwd = generate_password()
    assert len(pwd) == 12
    assert isinstance(pwd, str)
    # default charset includes lower, upper, digits, no symbols
    allowed = set(string.ascii_lowercase + string.ascii_uppercase + string.digits)
    assert all(c in allowed for c in pwd)


def test_generate_custom_length() -> None:
    for length in [4, 8, 16, 32]:
        pwd = generate_password(length=length)
        assert len(pwd) == length


def test_generate_no_upper() -> None:
    # run multiple times to avoid flaky due to randomness
    for _ in range(20):
        pwd = generate_password(
            length=12, use_upper=False, use_digits=True, use_symbols=False
        )
        assert not any(c.isupper() for c in pwd)
        assert all(c in string.ascii_lowercase + string.digits for c in pwd)


def test_generate_no_digits() -> None:
    for _ in range(20):
        pwd = generate_password(
            length=12, use_upper=True, use_digits=False, use_symbols=False
        )
        assert not any(c.isdigit() for c in pwd)
        allowed = set(string.ascii_lowercase + string.ascii_uppercase)
        assert all(c in allowed for c in pwd)


def test_generate_with_symbols() -> None:
    pwd = generate_password(
        length=20, use_upper=True, use_digits=True, use_symbols=True
    )
    allowed = set(
        string.ascii_lowercase
        + string.ascii_uppercase
        + string.digits
        + string.punctuation
    )
    assert all(c in allowed for c in pwd)
    # charset includes symbols, so we check charset directly
    charset = _build_charset(use_symbols=True)
    assert any(c in string.punctuation for c in charset)


def test_generate_only_lowercase() -> None:
    for _ in range(10):
        pwd = generate_password(
            length=10, use_upper=False, use_digits=False, use_symbols=False
        )
        assert pwd.islower()
        assert pwd.isalpha()
        assert all(c in string.ascii_lowercase for c in pwd)


def test_generate_uses_secrets_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    # ensure secrets.choice is used
    called = {"count": 0}
    orig_choice = __import__("secrets").choice

    def fake_choice(seq: str) -> str:
        called["count"] += 1
        return orig_choice(seq)

    monkeypatch.setattr("password_generator.generator.secrets.choice", fake_choice)
    pwd = generate_password(length=7)
    assert len(pwd) == 7
    assert called["count"] == 7


def test_generate_length_validation() -> None:
    with pytest.raises(ValueError, match=">= 4"):
        generate_password(length=3)
    with pytest.raises(ValueError, match=">= 4"):
        generate_password(length=0)
    with pytest.raises(ValueError, match=">= 4"):
        generate_password(length=-1)
    with pytest.raises(ValueError, match=">= 4"):
        generate_password(length=1)


def test_generate_length_type_validation() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        generate_password(length="12")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must be an integer"):
        generate_password(length=12.5)  # type: ignore[arg-type]


def test_generate_length_boundary() -> None:
    # exactly 4 should succeed
    pwd = generate_password(length=4)
    assert len(pwd) == 4


# ---- check_strength ----


def test_check_strength_weak_short() -> None:
    assert check_strength("abc") == "weak"
    assert check_strength("aB1") == "weak"
    assert check_strength("Ab1!") == "weak"  # len 4 -> weak despite variety


def test_check_strength_weak_low_variety() -> None:
    assert check_strength("abcdefgh") == "weak"  # only lower, len 8 -> weak
    assert check_strength("ABCDEFGH") == "weak"  # only upper
    assert check_strength("12345678") == "weak"  # only digits
    assert check_strength("!!!!!!!!") == "weak"  # only symbols
    assert check_strength("aaaaaaaaaaaa") == "weak"  # long but only one class


def test_check_strength_medium() -> None:
    # length 8 + variety 2 => medium
    assert check_strength("abcdef12") == "medium"
    assert check_strength("Abcdefgh") == "medium"
    assert check_strength("abc12345") == "medium"
    assert check_strength("ABCD1234") == "medium"
    # length 10 variety 3 but <12 => medium
    assert check_strength("Abcdef1234") == "medium"


def test_check_strength_strong_long_varied() -> None:
    # length >=12 and variety >=3 => strong
    assert check_strength("Abcdef123456") == "strong"  # lower+upper+digit len 12
    assert check_strength("Abc123!@#defG") == "strong"
    assert check_strength("aB3!aB3!aB3!") == "strong"


def test_check_strength_strong_all_four_medium_length() -> None:
    # length >=8 and variety ==4 => strong (even if <12)
    assert check_strength("aB3!5678") == "strong"
    assert check_strength("Ab1!Ab1!") == "strong"


def test_check_strength_medium_vs_strong_boundaries() -> None:
    # 11 chars, variety 3 => medium (needs >=12 for strong with 3 classes)
    assert check_strength("Abcdef12345") == "medium"
    # 12 chars, variety 2 => medium (needs 3 for strong)
    assert check_strength("abcdef123456") == "medium"
    # 12 chars, variety 3 => strong
    assert check_strength("Abcdef123456") == "strong"
    # 7 chars, variety 4 => still weak (needs >=8)
    assert check_strength("aB3!xyz") == "weak"


def test_check_strength_empty_and_single() -> None:
    assert check_strength("") == "weak"
    assert check_strength("a") == "weak"
    assert check_strength("A") == "weak"


def test_check_strength_invalid_type() -> None:
    with pytest.raises(ValueError, match="must be a string"):
        check_strength(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="must be a string"):
        check_strength(None)  # type: ignore[arg-type]


def test_check_strength_symbols_detection() -> None:
    assert check_strength("abcd!@#$") == "medium"  # lower + symbol, len 8
    assert check_strength("ABCD!@#$") == "medium"  # upper + symbol
    assert check_strength("1234!@#$") == "medium"  # digit + symbol

"""Core logic for password generation.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded from that criterion.

Uses :mod:`secrets` for cryptographically strong random generation.
"""

from __future__ import annotations

import secrets
import string


def _build_charset(
    use_upper: bool = True,
    use_digits: bool = True,
    use_symbols: bool = False,
) -> str:
    """Build character set based on flags.

    Always includes lowercase letters as the base alphabet.

    Args:
        use_upper: include uppercase letters (A-Z).
        use_digits: include digits (0-9).
        use_symbols: include punctuation symbols.

    Returns:
        String containing all allowed characters.

    Raises:
        ValueError: if resulting charset is empty.
    """
    charset = string.ascii_lowercase
    if use_upper:
        charset += string.ascii_uppercase
    if use_digits:
        charset += string.digits
    if use_symbols:
        charset += string.punctuation

    if not charset:
        raise ValueError(
            "charset must not be empty: enable at least one character type"
        )
    return charset


def generate_password(
    length: int = 12,
    use_upper: bool = True,
    use_digits: bool = True,
    use_symbols: bool = False,
) -> str:
    """Generate a cryptographically strong password.

    Uses :func:`secrets.choice` for each character selection.

    Args:
        length: desired password length, must be >= 4.
        use_upper: include uppercase letters.
        use_digits: include digits.
        use_symbols: include symbols (string.punctuation).

    Returns:
        Generated password of given length.

    Raises:
        ValueError: if length < 4 or resulting charset is empty.
    """
    if not isinstance(length, int):
        raise ValueError("length must be an integer")
    if length < 4:
        raise ValueError("length must be >= 4")

    charset = _build_charset(
        use_upper=use_upper, use_digits=use_digits, use_symbols=use_symbols
    )

    if not charset:
        raise ValueError("charset must not be empty")

    return "".join(secrets.choice(charset) for _ in range(length))


def check_strength(password: str) -> str:
    """Estimate password strength based on length and character variety.

    Heuristic (intentionally simple and explainable for beginners):

    * variety = number of character classes present among
      {lowercase, uppercase, digits, symbols}
    * ``weak``   — length < 8 or variety <= 1
    * ``medium`` — length >= 8 and variety >= 2, but not strong
    * ``strong`` — length >= 12 and variety >= 3
      (also strong if length >= 8 and variety == 4)

    Args:
        password: password string to evaluate.

    Returns:
        One of ``"weak"``, ``"medium"``, ``"strong"``.
    """
    if not isinstance(password, str):
        raise ValueError("password must be a string")

    length = len(password)

    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in string.punctuation for c in password)

    variety = sum([has_lower, has_upper, has_digit, has_symbol])

    # Strong: long + varied, or medium-long with all 4 classes
    if (length >= 12 and variety >= 3) or (length >= 8 and variety == 4):
        return "strong"
    if length >= 8 and variety >= 2:
        return "medium"
    return "weak"

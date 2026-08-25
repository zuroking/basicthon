"""Core logic for contacts OOP.

This module contains the "main logic" covered by the coverage criterion
(G-13 / GRILL2-05): every public function/method here has at least one test.
CLI parsing lives in cli.py and is intentionally excluded from that criterion.

Uses only stdlib (re).
"""

from __future__ import annotations

import re


def _validate_name(value: str) -> str:
    """Validate and normalize contact name."""
    if not isinstance(value, str):
        raise ValueError("name must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("name must not be empty")
    if len(cleaned) > 100:
        raise ValueError("name must be 100 characters or fewer")
    return cleaned


def _validate_phone(value: str) -> str:
    """Validate and normalize phone number."""
    if not isinstance(value, str):
        raise ValueError("phone must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("phone must not be empty")
    allowed = set("0123456789+ -().")
    if any(c not in allowed for c in cleaned):
        raise ValueError(f"invalid phone value: {value!r}")
    digits = "".join(c for c in cleaned if c.isdigit())
    if len(digits) < 5 or len(digits) > 15:
        raise ValueError("phone must contain 5-15 digits")
    return cleaned


def _validate_email(value: str) -> str:
    """Validate and normalize email address."""
    if not isinstance(value, str):
        raise ValueError("email must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("email must not be empty")
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(pattern, cleaned):
        raise ValueError(f"invalid email value: {value!r}")
    return cleaned


class Contact:
    """Single contact with validated fields.

    Attributes:
        name: human-readable contact name (non-empty, 1-100 chars).
        phone: phone number (5-15 digits, allowed + - ( ) . space).
        email: email address (must contain @ and .).
    """

    def __init__(self, name: str, phone: str, email: str) -> None:
        self._name = _validate_name(name)
        self._phone = _validate_phone(phone)
        self._email = _validate_email(email)

    @property
    def name(self) -> str:
        """Contact name."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = _validate_name(value)

    @property
    def phone(self) -> str:
        """Phone number."""
        return self._phone

    @phone.setter
    def phone(self, value: str) -> None:
        self._phone = _validate_phone(value)

    @property
    def email(self) -> str:
        """Email address."""
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        self._email = _validate_email(value)

    def __repr__(self) -> str:
        return (
            f"Contact(name={self.name!r}, phone={self.phone!r}, "
            f"email={self.email!r})"
        )

    def __str__(self) -> str:
        return f"{self.name} | {self.phone} | {self.email}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Contact):
            return NotImplemented
        return (
            self.name == other.name
            and self.phone == other.phone
            and self.email == other.email
        )

    def to_dict(self) -> dict[str, str]:
        """Serialize to plain dict."""
        return {"name": self.name, "phone": self.phone, "email": self.email}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Contact:
        """Create Contact from dict with name/phone/email."""
        try:
            name = data["name"]
            phone = data["phone"]
            email = data["email"]
        except KeyError as exc:
            raise ValueError(f"missing field in contact data: {exc}") from exc
        return cls(name, phone, email)


class ContactBook:
    """In-memory contact book, keyed by lowercased name.

    Provides OOP-style CRUD plus search and listing.
    Names are case-insensitive for lookup but preserve original case.
    """

    def __init__(self) -> None:
        self._contacts: dict[str, Contact] = {}

    def add(
        self, contact: Contact | str, phone: str | None = None, email: str | None = None
    ) -> Contact:
        """Add a contact.

        Supports two calling conventions:
        - ``add(contact_obj)`` where ``contact_obj`` is a :class:`Contact`.
        - ``add(name, phone, email)`` where all three are strings.

        Args:
            contact: either Contact instance or name string.
            phone: phone string when first arg is name.
            email: email string when first arg is name.

        Returns:
            The added Contact.

        Raises:
            ValueError: if contact is not Contact/str, validation fails,
                or name already exists (case-insensitive).
        """
        if isinstance(contact, Contact):
            if phone is not None or email is not None:
                raise ValueError(
                    "when adding Contact instance, phone/email must not be provided"
                )
            key = contact.name.strip().lower()
            if key in self._contacts:
                raise ValueError(f"contact '{contact.name}' already exists")
            self._contacts[key] = contact
            return contact
        if isinstance(contact, str):
            if phone is None or email is None:
                raise ValueError("phone and email required when adding by name")
            new_contact = Contact(contact, phone, email)
            key = new_contact.name.strip().lower()
            if key in self._contacts:
                raise ValueError(f"contact '{new_contact.name}' already exists")
            self._contacts[key] = new_contact
            return new_contact
        raise ValueError("contact must be Contact or name string")

    def get(self, name: str) -> Contact | None:
        """Get contact by name (case-insensitive).

        Args:
            name: name to lookup.

        Returns:
            Contact if found, otherwise None.

        Raises:
            ValueError: if name is not a string or is empty.
        """
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        key = name.strip().lower()
        if not key:
            raise ValueError("name must not be empty")
        return self._contacts.get(key)

    def update(
        self,
        name: str,
        phone: str | None = None,
        email: str | None = None,
    ) -> Contact:
        """Update phone/email for existing contact.

        Args:
            name: name of contact to update (case-insensitive).
            phone: new phone value or None to keep current.
            email: new email value or None to keep current.

        Returns:
            Updated Contact.

        Raises:
            ValueError: if contact not found, nothing to update,
                or validation fails.
        """
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        key = name.strip().lower()
        if not key:
            raise ValueError("name must not be empty")
        if phone is None and email is None:
            raise ValueError("nothing to update: provide phone or email")
        contact = self._contacts.get(key)
        if contact is None:
            raise ValueError(f"contact '{name}' not found")
        if phone is not None:
            contact.phone = phone
        if email is not None:
            contact.email = email
        return contact

    def delete(self, name: str) -> None:
        """Delete contact by name (case-insensitive).

        Args:
            name: name of contact to delete.

        Raises:
            ValueError: if name is not a string, is empty, or not found.
        """
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        key = name.strip().lower()
        if not key:
            raise ValueError("name must not be empty")
        if key not in self._contacts:
            raise ValueError(f"contact '{name}' not found")
        del self._contacts[key]

    def search(self, query: str) -> list[Contact]:
        """Search contacts by substring in name/phone/email.

        Case-insensitive. Returns contacts where query appears in any field.

        Args:
            query: substring to search for.

        Returns:
            List of matching contacts (may be empty).

        Raises:
            ValueError: if query is not a string.
        """
        if not isinstance(query, str):
            raise ValueError("query must be a string")
        q = query.strip().lower()
        if not q:
            return []
        result: list[Contact] = []
        for contact in self._contacts.values():
            if (
                q in contact.name.lower()
                or q in contact.email.lower()
                or q in contact.phone.lower()
            ):
                result.append(contact)
        return result

    def list_contacts(self) -> list[Contact]:
        """List all contacts sorted by name (case-insensitive)."""
        return sorted(self._contacts.values(), key=lambda c: c.name.lower())

    def list_all(self) -> list[Contact]:
        """Alias for list_contacts (kept for 'list' wording in spec)."""
        return self.list_contacts()

    def __len__(self) -> int:
        return len(self._contacts)

    def __contains__(self, name: object) -> bool:
        if not isinstance(name, str):
            return False
        return name.strip().lower() in self._contacts


# Alias for spec wording "list" — provide attribute named "list" for compatibility.
# Use setattr to avoid shadowing builtin list type inside class body.
setattr(ContactBook, "list", ContactBook.list_contacts)

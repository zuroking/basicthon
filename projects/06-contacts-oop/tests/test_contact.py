"""Tests for contacts.contact — covers every public method (G-13/GRILL2-05)."""

from __future__ import annotations

import pytest

from contacts.contact import Contact, ContactBook

# ---- Contact creation and validation ----


def test_contact_valid() -> None:
    c = Contact("Alice", "+7 999 123-45-67", "alice@example.com")
    assert c.name == "Alice"
    assert c.phone == "+7 999 123-45-67"
    assert c.email == "alice@example.com"


def test_contact_name_stripped() -> None:
    c = Contact("  Bob  ", "12345 678", "bob@example.com")
    assert c.name == "Bob"


def test_contact_invalid_name_empty() -> None:
    with pytest.raises(ValueError, match="name must not be empty"):
        Contact("", "1234567", "a@b.com")
    with pytest.raises(ValueError, match="name must not be empty"):
        Contact("   ", "1234567", "a@b.com")


def test_contact_invalid_name_type() -> None:
    with pytest.raises(ValueError, match="name must be a string"):
        Contact(123, "1234567", "a@b.com")  # type: ignore[arg-type]


def test_contact_name_too_long() -> None:
    with pytest.raises(ValueError, match="100 characters"):
        Contact("a" * 101, "1234567", "a@b.com")


def test_contact_invalid_phone_empty() -> None:
    with pytest.raises(ValueError, match="phone must not be empty"):
        Contact("Alice", "", "a@b.com")


def test_contact_invalid_phone_chars() -> None:
    with pytest.raises(ValueError, match="invalid phone"):
        Contact("Alice", "abc-123", "a@b.com")
    with pytest.raises(ValueError, match="invalid phone"):
        Contact("Alice", "12#34", "a@b.com")


def test_contact_invalid_phone_digits_too_few() -> None:
    with pytest.raises(ValueError, match="5-15 digits"):
        Contact("Alice", "123", "a@b.com")
    with pytest.raises(ValueError, match="5-15 digits"):
        Contact("Alice", "12", "a@b.com")


def test_contact_invalid_phone_digits_too_many() -> None:
    with pytest.raises(ValueError, match="5-15 digits"):
        Contact("Alice", "1" * 16, "a@b.com")


def test_contact_valid_phone_variants() -> None:
    Contact("A", "12345", "a@b.com")
    Contact("A", "+1 (999) 123-4567", "a@b.com")
    Contact("A", "123-456-7890", "a@b.com")


def test_contact_invalid_phone_type() -> None:
    with pytest.raises(ValueError, match="phone must be a string"):
        Contact("Alice", 12345, "a@b.com")  # type: ignore[arg-type]


def test_contact_invalid_email_empty() -> None:
    with pytest.raises(ValueError, match="email must not be empty"):
        Contact("Alice", "1234567", "")


def test_contact_invalid_email_format() -> None:
    with pytest.raises(ValueError, match="invalid email"):
        Contact("Alice", "1234567", "invalid-email")
    with pytest.raises(ValueError, match="invalid email"):
        Contact("Alice", "1234567", "a@")
    with pytest.raises(ValueError, match="invalid email"):
        Contact("Alice", "1234567", "@example.com")
    with pytest.raises(ValueError, match="invalid email"):
        Contact("Alice", "1234567", "a@b")


def test_contact_invalid_email_type() -> None:
    with pytest.raises(ValueError, match="email must be a string"):
        Contact("Alice", "1234567", 123)  # type: ignore[arg-type]


def test_contact_email_stripped() -> None:
    c = Contact("Alice", "1234567", "  alice@example.com  ")
    assert c.email == "alice@example.com"


def test_contact_setters() -> None:
    c = Contact("Alice", "1234567", "alice@example.com")
    c.name = "Alicia"
    assert c.name == "Alicia"
    c.phone = "+7 999 000-11-22"
    assert c.phone == "+7 999 000-11-22"
    c.email = "alicia@example.org"
    assert c.email == "alicia@example.org"


def test_contact_setter_validation() -> None:
    c = Contact("Alice", "1234567", "alice@example.com")
    with pytest.raises(ValueError):
        c.name = ""
    with pytest.raises(ValueError):
        c.phone = "abc"
    with pytest.raises(ValueError):
        c.email = "bad-email"


def test_contact_repr_and_str() -> None:
    c = Contact("Alice", "1234567", "alice@example.com")
    r = repr(c)
    assert "Alice" in r
    assert "1234567" in r
    assert "alice@example.com" in r
    s = str(c)
    assert "Alice" in s


def test_contact_eq() -> None:
    c1 = Contact("Alice", "1234567", "alice@example.com")
    c2 = Contact("Alice", "1234567", "alice@example.com")
    c3 = Contact("Bob", "1234567", "alice@example.com")
    assert c1 == c2
    assert c1 != c3
    assert (c1 == "not a contact") is False


def test_contact_to_dict_and_from_dict() -> None:
    c = Contact("Alice", "1234567", "alice@example.com")
    d = c.to_dict()
    assert d == {"name": "Alice", "phone": "1234567", "email": "alice@example.com"}
    c2 = Contact.from_dict(d)
    assert c2 == c


def test_contact_from_dict_missing_field() -> None:
    with pytest.raises(ValueError, match="missing field"):
        Contact.from_dict({"name": "Alice", "phone": "1234567"})  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="missing field"):
        Contact.from_dict({"name": "Alice"})  # type: ignore[arg-type]


def test_contact_from_dict_invalid_value() -> None:
    with pytest.raises(ValueError):
        Contact.from_dict({"name": "", "phone": "1234567", "email": "a@b.com"})


# ---- ContactBook ----


def test_book_init_empty() -> None:
    book = ContactBook()
    assert len(book) == 0
    assert book.list_contacts() == []
    assert book.list_all() == []
    # list alias via setattr
    assert book.list() == []  # type: ignore[attr-defined]


def test_book_add_contact_instance() -> None:
    book = ContactBook()
    c = Contact("Alice", "1234567", "alice@example.com")
    result = book.add(c)
    assert result is c
    assert len(book) == 1
    assert book.get("Alice") == c
    assert "Alice" in book
    assert "alice" in book  # case-insensitive contains
    assert "Bob" not in book


def test_book_add_by_name_phone_email() -> None:
    book = ContactBook()
    c = book.add("Bob", "7654321", "bob@example.com")
    assert isinstance(c, Contact)
    assert c.name == "Bob"
    assert book.get("Bob") == c


def test_book_add_duplicate_raises() -> None:
    book = ContactBook()
    book.add(Contact("Alice", "1234567", "alice@example.com"))
    with pytest.raises(ValueError, match="already exists"):
        book.add(Contact("Alice", "7654321", "alice2@example.com"))
    with pytest.raises(ValueError, match="already exists"):
        book.add(Contact("alice", "9999999", "alice3@example.com"))
    with pytest.raises(ValueError, match="already exists"):
        book.add("Alice", "1111111", "a@b.com")
    with pytest.raises(ValueError, match="already exists"):
        book.add("ALICE", "1111111", "a@b.com")


def test_book_add_invalid_args() -> None:
    book = ContactBook()
    with pytest.raises(ValueError, match="phone and email required"):
        book.add("Alice")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="phone and email required"):
        book.add("Alice", "1234567")  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="must be Contact or name string"):
        book.add(123, "1234567", "a@b.com")  # type: ignore[arg-type]
    c = Contact("Alice", "1234567", "alice@example.com")
    with pytest.raises(ValueError, match="must not be provided"):
        book.add(c, phone="111")  # type: ignore[call-arg]


def test_book_get_case_insensitive() -> None:
    book = ContactBook()
    c = Contact("Alice", "1234567", "alice@example.com")
    book.add(c)
    assert book.get("alice") == c
    assert book.get("ALICE") == c
    assert book.get("  Alice  ") == c
    assert book.get("Bob") is None


def test_book_get_invalid() -> None:
    book = ContactBook()
    with pytest.raises(ValueError, match="name must be a string"):
        book.get(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="name must not be empty"):
        book.get("")
    with pytest.raises(ValueError, match="name must not be empty"):
        book.get("   ")


def test_book_update_success() -> None:
    book = ContactBook()
    book.add(Contact("Alice", "1234567", "alice@example.com"))
    updated = book.update("Alice", phone="7654321")
    assert updated.phone == "7654321"
    assert updated.email == "alice@example.com"
    updated2 = book.update("alice", email="new@example.com")
    assert updated2.email == "new@example.com"
    updated3 = book.update("ALICE", phone="1111111", email="alice2@example.com")
    assert updated3.phone == "1111111"
    assert updated3.email == "alice2@example.com"


def test_book_update_not_found() -> None:
    book = ContactBook()
    with pytest.raises(ValueError, match="not found"):
        book.update("Alice", phone="1234567")


def test_book_update_nothing_to_update() -> None:
    book = ContactBook()
    book.add(Contact("Alice", "1234567", "alice@example.com"))
    with pytest.raises(ValueError, match="nothing to update"):
        book.update("Alice")


def test_book_update_invalid_phone_email() -> None:
    book = ContactBook()
    book.add(Contact("Alice", "1234567", "alice@example.com"))
    with pytest.raises(ValueError):
        book.update("Alice", phone="abc")
    with pytest.raises(ValueError):
        book.update("Alice", email="bad-email")


def test_book_update_invalid_name() -> None:
    book = ContactBook()
    book.add(Contact("Alice", "1234567", "alice@example.com"))
    with pytest.raises(ValueError, match="name must be a string"):
        book.update(123, phone="1234567")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="name must not be empty"):
        book.update("", phone="1234567")


def test_book_delete_success() -> None:
    book = ContactBook()
    book.add(Contact("Alice", "1234567", "alice@example.com"))
    book.add(Contact("Bob", "7654321", "bob@example.com"))
    assert len(book) == 2
    book.delete("Alice")
    assert len(book) == 1
    assert book.get("Alice") is None
    assert book.get("Bob") is not None
    # case-insensitive delete
    book.delete("BOB")
    assert len(book) == 0


def test_book_delete_not_found() -> None:
    book = ContactBook()
    with pytest.raises(ValueError, match="not found"):
        book.delete("Alice")
    book.add(Contact("Alice", "1234567", "alice@example.com"))
    with pytest.raises(ValueError, match="not found"):
        book.delete("Bob")


def test_book_delete_invalid() -> None:
    book = ContactBook()
    with pytest.raises(ValueError, match="name must be a string"):
        book.delete(123)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="name must not be empty"):
        book.delete("")


def test_book_search() -> None:
    book = ContactBook()
    book.add(Contact("Alice Smith", "1234567", "alice@example.com"))
    book.add(Contact("Bob Jones", "7654321", "bob@example.com"))
    book.add(Contact("Alicia Keys", "9999999", "alicia@test.com"))
    results = book.search("ali")
    assert len(results) == 2
    assert any(c.name == "Alice Smith" for c in results)
    assert any(c.name == "Alicia Keys" for c in results)
    # case-insensitive
    assert len(book.search("ALICE")) == 1
    # search by email
    assert len(book.search("bob@example.com")) == 1
    # search by phone substring
    assert len(book.search("7654")) == 1
    # no matches
    assert book.search("nonexistent") == []
    # empty query returns empty
    assert book.search("") == []
    assert book.search("   ") == []


def test_book_search_invalid() -> None:
    book = ContactBook()
    with pytest.raises(ValueError, match="query must be a string"):
        book.search(123)  # type: ignore[arg-type]


def test_book_list_contacts_sorted() -> None:
    book = ContactBook()
    book.add(Contact("Charlie", "3333333", "c@example.com"))
    book.add(Contact("alice", "1111111", "a@example.com"))
    book.add(Contact("Bob", "2222222", "b@example.com"))
    lst = book.list_contacts()
    assert [c.name for c in lst] == ["alice", "Bob", "Charlie"]
    # list_all alias
    assert book.list_all() == lst
    # list alias
    assert book.list() == lst  # type: ignore[attr-defined]


def test_book_list_empty() -> None:
    book = ContactBook()
    assert book.list_contacts() == []
    assert book.list_all() == []


def test_book_contains_and_len() -> None:
    book = ContactBook()
    book.add(Contact("Alice", "1234567", "alice@example.com"))
    assert len(book) == 1
    assert "Alice" in book
    assert "alice" in book
    assert "Bob" not in book
    assert 123 not in book  # type: ignore[operator]


def test_book_integration() -> None:
    book = ContactBook()
    book.add("Alice", "1234567", "alice@example.com")
    book.add(Contact("Bob", "7654321", "bob@example.com"))
    assert len(book) == 2
    # update
    book.update("Alice", phone="9999999")
    assert book.get("Alice").phone == "9999999"  # type: ignore[union-attr]
    # search
    assert len(book.search("alice")) == 1
    # list
    names = [c.name for c in book.list_contacts()]
    assert names == ["Alice", "Bob"]
    # delete
    book.delete("Bob")
    assert book.get("Bob") is None
    assert len(book) == 1

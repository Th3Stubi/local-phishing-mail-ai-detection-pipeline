from email import message_from_bytes, message_from_string
from pathlib import Path

import pytest

from phishpipe.message_text import get_plain_text, set_plain_text
from phishpipe.parser import to_bytes

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str):
    return message_from_bytes((FIXTURES / name).read_bytes())


def test_get_plain_text_single_part():
    text = get_plain_text(load("plain_urls.eml"))
    assert text is not None
    assert "https://secure.example.com/login" in text
    assert text.startswith("Dear customer,")


def test_html_only_gives_none():
    assert get_plain_text(load("html_only.eml")) is None


def test_multipart_uses_plain_part_not_html():
    text = get_plain_text(load("multipart_alternative.eml"))
    assert text is not None
    assert "Plain version" in text
    assert "<html>" not in text


def test_latin1_quoted_printable_is_decoded():
    text = get_plain_text(load("latin1_qp.eml"))
    assert text is not None
    assert text.startswith("Grüße aus München")


def test_attachment_text_part_is_ignored():
    raw = (
        "From: a@example.com\n"
        "Subject: Test\n"
        "MIME-Version: 1.0\n"
        'Content-Type: multipart/mixed; boundary="B"\n\n'
        "--B\n"
        "Content-Type: text/plain\n"
        'Content-Disposition: attachment; filename="notes.txt"\n\n'
        "Only an attachment.\n"
        "--B--\n"
    )
    assert get_plain_text(message_from_string(raw)) is None


def test_set_plain_text_multipart_keeps_headers_and_html():
    msg = load("multipart_alternative.eml")
    headers_before = list(msg.items())
    html_before = msg.get_payload()[1].get_payload()

    set_plain_text(msg, "New text: Grüße, “quoted” and http://example.com/plain")

    assert list(msg.items()) == headers_before  # top-level headers untouched
    assert msg.get_payload()[1].get_payload() == html_before  # html part untouched
    assert get_plain_text(msg) == "New text: Grüße, “quoted” and http://example.com/plain"


def test_set_plain_text_single_part_changes_only_body_headers():
    msg = load("plain_urls.eml")
    before = dict(msg.items())

    set_plain_text(msg, "Ünïcode text")

    after = dict(msg.items())
    for name in ("From", "To", "Subject", "Date", "MIME-Version"):
        assert after[name] == before[name]
    assert msg.get_content_charset() == "utf-8"
    assert msg["Content-Transfer-Encoding"] == "quoted-printable"
    assert get_plain_text(msg) == "Ünïcode text"


def test_set_plain_text_survives_write_and_read():
    msg = load("latin1_qp.eml")
    set_plain_text(msg, "Grüße 🙂\nSecond line")
    again = message_from_bytes(to_bytes(msg))
    assert get_plain_text(again) == "Grüße 🙂\nSecond line"
    assert again["Subject"] == "Test latin1"


def test_set_plain_text_without_plain_part_raises():
    with pytest.raises(ValueError):
        set_plain_text(load("html_only.eml"), "text")


def test_unknown_charset_falls_back_to_utf8():
    raw = (
        "From: a@example.com\n"
        "Subject: Test\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=x-no-such-charset\n"
        "Content-Transfer-Encoding: 8bit\n\n"
        "Plain text with an unknown charset.\n"
    )
    assert get_plain_text(message_from_string(raw)) == "Plain text with an unknown charset.\n"

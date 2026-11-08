"""Read and replace the plain text part of an email.

Only the first text/plain part (not an attachment) counts as the mail text.
Emails without such a part (for example HTML only) give None. The caller
logs them with the reason NO_PLAIN_TEXT and skips them for now.

When the text is replaced, only that part changes. The top-level headers
(From, To, Subject, Date, Received, ...) are not touched. The part is
written as UTF-8 with quoted-printable encoding, so Content-Type (charset)
and Content-Transfer-Encoding of that part change. For a mail with one part
these two headers are also top-level headers.
"""

from __future__ import annotations

import quopri
from email.message import Message

NO_PLAIN_TEXT = "no_plain_text"


def _find_plain_part(msg: Message) -> Message | None:
    for part in msg.walk():
        if part.is_multipart():
            continue
        if part.get_content_type() != "text/plain":
            continue
        if part.get_content_disposition() == "attachment":
            continue
        return part
    return None


def get_plain_text(msg: Message) -> str | None:
    """Return the decoded plain text, or None if the email has no text/plain part."""
    part = _find_plain_part(msg)
    if part is None:
        return None
    raw = part.get_payload(decode=True)
    if raw is None:
        return None
    charset = part.get_content_charset() or "us-ascii"
    try:
        return raw.decode(charset, errors="replace ")
    except LookupError:  # unknown charset name
        return raw.decode("utf-8", errors="replace")


def set_plain_text(msg: Message, text: str) -> None:
    """Replace the plain text part in place. Raises ValueError if there is none."""
    part = _find_plain_part(msg)
    if part is None:
        raise ValueError("email has no text/plain part")
    body = quopri.encodestring(text.encode("utf-8")).decode("ascii")
    part.set_payload(body)
    part.set_param("charset", "utf-8", header="Content-Type")
    if part.get("Content-Transfer-Encoding") is None:
        part["Content-Transfer-Encoding"] = "quoted-printable"
    else:
        part.replace_header("Content-Transfer-Encoding", "quoted-printable")

"""Read mbox files or folders of .eml files and write cleaned emails.

Rules:
- one .eml per email in the interim folder, named after the SHA-256 hash
- no duplicates, no "folder internal data" placeholder entries
- keep the Date header, keep only emails dated before the cutoff
- attachments are dropped, links are never opened, nothing is executed
- logs contain only counts, reasons and positions, never mail content
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import logging
import mailbox
from collections import Counter
from collections.abc import Iterator
from datetime import UTC, datetime
from email import message_from_bytes
from email.generator import BytesGenerator
from email.message import Message
from email.utils import parsedate_to_datetime
from pathlib import Path

from phishpipe.config import DEFAULT_CONFIG, Config, load_config

log = logging.getLogger(__name__)

METADATA_COLUMNS = ["source", "year", "hash"]


def iter_messages(path: Path) -> Iterator[tuple[int, Message]]:
    """Yield (position, message) from an mbox file or a folder with .eml files."""
    path = Path(path)
    if path.is_dir():
        for i, file in enumerate(sorted(path.rglob("*.eml"))):
            yield i, message_from_bytes(file.read_bytes())
    elif path.is_file():
        box = mailbox.mbox(path, create=False)
        try:
            for i, key in enumerate(box.keys()):
                yield i, message_from_bytes(box.get_bytes(key))
        finally:
            box.close()
    else:
        raise FileNotFoundError(f"Input not found: {path}")


def is_placeholder(msg: Message) -> bool:
    """Detect mbox 'folder internal data' entries (not real emails)."""
    subject = str(msg.get("Subject", "")).upper()
    sender = str(msg.get("From", "")).lower()
    return (
        "DON'T DELETE THIS MESSAGE" in subject
        or "FOLDER INTERNAL DATA" in subject
        or "mail system internal data" in sender
    )


def _keep_part(part: Message) -> bool:
    if part.is_multipart():
        return True
    if part.get_content_disposition() == "attachment":
        return False
    return part.get_content_maintype() == "text"


def strip_attachments(msg: Message) -> Message:
    """Remove attachments and non-text parts in place. Headers stay unchanged."""
    if msg.is_multipart():
        kept = []
        for part in msg.get_payload():
            if _keep_part(part):
                strip_attachments(part)
                kept.append(part)
        msg.set_payload(kept)
    return msg


def parse_date(msg: Message) -> datetime | None:
    """Return the Date header as an aware UTC datetime, or None if missing or invalid."""
    raw = msg.get("Date")
    if raw is None:
        return None
    try:
        date = parsedate_to_datetime(str(raw))
    except (TypeError, ValueError, IndexError):
        return None
    if date is None:
        return None
    if date.tzinfo is None:
        date = date.replace(tzinfo=UTC)
    return date.astimezone(UTC)


def to_bytes(msg: Message) -> bytes:
    buf = io.BytesIO()
    BytesGenerator(buf, mangle_from_=False, maxheaderlen=0).flatten(msg)
    return buf.getvalue()


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_known_hashes(metadata_file: Path) -> set[str]:
    if not metadata_file.exists():
        return set()
    with metadata_file.open(newline="", encoding="utf-8") as f:
        return {row["hash"] for row in csv.DictReader(f)}


def _append_metadata(metadata_file: Path, rows: list[dict[str, str | int]]) -> None:
    if not rows:
        return
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    is_new = not metadata_file.exists()
    with metadata_file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=METADATA_COLUMNS)
        if is_new:
            writer.writeheader()
        writer.writerows(rows)


def parse_source(source: Path, config: Config) -> Counter:
    """Process one mbox file or folder. Returns counts per outcome."""
    source = Path(source)
    source_name = source.stem if source.is_file() else source.name
    config.interim_dir.mkdir(parents=True, exist_ok=True)
    known = _read_known_hashes(config.metadata_file)
    counts: Counter = Counter()
    rows: list[dict[str, str | int]] = []

    for pos, msg in iter_messages(source):
        counts["read"] += 1
        where = f"{source_name}#{pos}"

        if is_placeholder(msg):
            counts["placeholder"] += 1
            log.info("skip %s: placeholder", where)
            continue

        date = parse_date(msg)
        if date is None:
            reason = "missing_date" if msg.get("Date") is None else "invalid_date"
            counts[reason] += 1
            log.warning("skip %s: %s", where, reason)
            continue
        if date >= config.date_cutoff:
            counts["too_new"] += 1
            log.info("skip %s: too_new", where)
            continue

        data = to_bytes(strip_attachments(msg))
        digest = content_hash(data)
        if digest in known:
            counts["duplicate"] += 1
            log.info("skip %s: duplicate", where)
            continue

        (config.interim_dir / f"{digest}.eml").write_bytes(data)
        known.add(digest)
        rows.append({"source": source_name, "year": date.year, "hash": digest})
        counts["written"] += 1

    _append_metadata(config.metadata_file, rows)
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Parse an mbox file or a folder of .eml files.")
    ap.add_argument("source", type=Path, help="mbox file or folder with .eml files")
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    counts = parse_source(args.source, load_config(args.config))
    log.info("summary: %s", dict(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

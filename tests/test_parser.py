import csv
import logging
import shutil
from dataclasses import replace
from datetime import UTC, datetime
from email import message_from_bytes
from pathlib import Path

import pytest

from phishpipe.config import Config, load_config
from phishpipe.parser import (
    is_placeholder,
    iter_messages,
    parse_date,
    parse_source,
    strip_attachments,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def config(tmp_path) -> Config:
    base = load_config()
    return replace(
        base,
        interim_dir=tmp_path / "interim",
        processed_dir=tmp_path / "processed",
        metadata_file=tmp_path / "processed" / "metadata.csv",
    )


def load(name: str):
    return message_from_bytes((FIXTURES / name).read_bytes())


def make_folder(tmp_path: Path, names: list[str], folder: str = "src_dir") -> Path:
    d = tmp_path / folder
    d.mkdir()
    for n in names:
        shutil.copy(FIXTURES / n, d / n)
    return d


def make_mbox(tmp_path: Path, names: list[str]) -> Path:
    out = tmp_path / "sample.mbox"
    with out.open("wb") as f:
        for n in names:
            f.write(b"From MAILER-DAEMON Tue Mar  3 10:00:00 2015\n")
            f.write((FIXTURES / n).read_bytes())
            f.write(b"\n")
    return out


def metadata_rows(config: Config) -> list[dict]:
    with config.metadata_file.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_config_values():
    cfg = load_config()
    assert cfg.date_cutoff == datetime(2022, 12, 1, tzinfo=UTC)
    assert isinstance(cfg.seed, int)


def test_date_filter_boundary(tmp_path, config):
    src = make_folder(tmp_path, ["before_cutoff.eml", "at_cutoff.eml", "too_new.eml"])
    counts = parse_source(src, config)
    assert counts["written"] == 1
    assert counts["too_new"] == 2


def test_missing_and_invalid_date_logged(tmp_path, config, caplog):
    src = make_folder(tmp_path, ["no_date.eml", "bad_date.eml", "ok_2015.eml"])
    with caplog.at_level(logging.INFO):
        counts = parse_source(src, config)
    assert counts["missing_date"] == 1
    assert counts["invalid_date"] == 1
    assert counts["written"] == 1
    assert "missing_date" in caplog.text
    assert "invalid_date" in caplog.text


def test_duplicates_skipped(tmp_path, config):
    src = make_folder(tmp_path, ["ok_2015.eml", "ok_2015_copy.eml"])
    counts = parse_source(src, config)
    assert counts["written"] == 1
    assert counts["duplicate"] == 1
    assert len(list(config.interim_dir.glob("*.eml"))) == 1


def test_placeholder_skipped(tmp_path, config):
    assert is_placeholder(load("placeholder.eml"))
    assert not is_placeholder(load("ok_2015.eml"))
    src = make_folder(tmp_path, ["placeholder.eml", "ok_2015.eml"])
    counts = parse_source(src, config)
    assert counts["placeholder"] == 1
    assert counts["written"] == 1


def test_attachment_removed_and_date_kept(tmp_path, config):
    src = make_folder(tmp_path, ["attachment.eml"])
    parse_source(src, config)
    (out,) = list(config.interim_dir.glob("*.eml"))
    text = out.read_text(encoding="utf-8")
    assert "Date: Fri, 06 Jun 2014 12:00:00 +0000" in text
    assert "Please see the file." in text
    assert "file.bin" not in text
    assert "U0VDUkVUQVRUQUNITUVOVA" not in text


def test_strip_attachments_keeps_headers():
    msg = load("attachment.eml")
    before = list(msg.items())
    strip_attachments(msg)
    assert list(msg.items()) == before
    assert len(msg.get_payload()) == 1


def test_mbox_input_and_metadata(tmp_path, config):
    mbox = make_mbox(tmp_path, ["ok_2015.eml", "ok_2018.eml", "too_new.eml"])
    counts = parse_source(mbox, config)
    assert counts["read"] == 3
    assert counts["written"] == 2
    rows = metadata_rows(config)
    assert {r["year"] for r in rows} == {"2015", "2018"}
    assert all(r["source"] == "sample" for r in rows)
    assert all(len(r["hash"]) == 64 for r in rows)
    for r in rows:
        assert (config.interim_dir / f"{r['hash']}.eml").exists()


def test_rerun_adds_no_duplicates(tmp_path, config):
    src = make_folder(tmp_path, ["ok_2015.eml", "ok_2018.eml"])
    parse_source(src, config)
    counts = parse_source(src, config)
    assert counts["written"] == 0
    assert counts["duplicate"] == 2
    assert len(metadata_rows(config)) == 2


def test_log_has_no_mail_content(tmp_path, config, caplog):
    src = make_folder(tmp_path, ["ok_2015.eml", "no_date.eml", "too_new.eml"])
    with caplog.at_level(logging.DEBUG):
        parse_source(src, config)
    for secret in ("example.com", "Hello, this is a test", "Test one", "Test nodate"):
        assert secret not in caplog.text


def test_parse_date_values():
    assert parse_date(load("ok_2018.eml")) == datetime(2018, 11, 5, 7, 30, tzinfo=UTC)
    assert parse_date(load("no_date.eml")) is None
    assert parse_date(load("bad_date.eml")) is None


def test_missing_input_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        list(iter_messages(tmp_path / "nope"))

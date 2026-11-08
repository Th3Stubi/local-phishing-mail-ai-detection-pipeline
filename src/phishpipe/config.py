"""Load settings from config.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config.yaml"


@dataclass(frozen=True)
class Config:
    model_name: str
    seed: int
    raw_dir: Path
    interim_dir: Path
    processed_dir: Path
    metadata_file: Path
    date_cutoff: datetime  # timezone-aware, UTC


def load_config(path: Path | str = DEFAULT_CONFIG) -> Config:
    path = Path(path).resolve()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    base = path.parent
    paths = data["paths"]
    cutoff = datetime.strptime(str(data["date_cutoff"]), "%Y-%m-%d").replace(tzinfo=UTC)
    return Config(
        model_name=data["model"]["name"],
        seed=int(data["seed"]),
        raw_dir=base / paths["raw"],
        interim_dir=base / paths["interim"],
        processed_dir=base / paths["processed"],
        metadata_file=base / paths["metadata"],
        date_cutoff=cutoff,
    )

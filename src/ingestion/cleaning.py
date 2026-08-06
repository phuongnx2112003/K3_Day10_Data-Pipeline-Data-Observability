from __future__ import annotations

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Iterable

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


LOGGER = logging.getLogger(__name__)

TARGET_CLEAN_COLUMNS = [
    "paper_id",
    "title",
    "text_for_embedding",
    "published",
    "authors_joined",
    "categories_joined",
    "summary",
    "abs_url",
    "pdf_url",
]

CLEAN_COLUMNS = [
    "paper_id",
    "title",
    "summary",
    "authors",
    "categories",
    "primary_category",
    "published",
    "updated",
    "age_days",
    "authors_joined",
    "categories_joined",
    "summary_chars",
    "text_for_embedding",
    "abs_url",
    "pdf_url",
    "comment",
]


def _clean_text(value: object) -> str:
    """Return a stable, single-line representation for nullable source text."""
    if value is None or pd.isna(value):
        return ""
    return normalize_whitespace(str(value))


def _clean_list(values: Iterable[object] | None) -> list[str]:
    """Normalize and case-insensitively de-duplicate a source list."""
    result: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        item = _clean_text(value)
        key = item.casefold()
        if item and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def build_text_for_embedding(
    title: str,
    summary: str,
    authors_joined: str,
    categories_joined: str,
) -> str:
    """Build the canonical document text used by every embedding index."""
    parts = [f"Title: {title}", f"Summary: {summary}"]
    if authors_joined:
        parts.append(f"Authors: {authors_joined}")
    if categories_joined:
        parts.append(f"Categories: {categories_joined}")
    return "\n".join(parts)


def build_clean_dataframe(
    records: list[PaperRecord],
    run_date: datetime,
    counters: dict[str, int] | None = None,
) -> pd.DataFrame:
    """Convert raw paper records to the canonical clean schema.

    Contract:
    - ``paper_id``, ``title`` and a parseable ``published`` date are required;
      invalid rows are removed. Optional text fields are filled with ``""``.
    - ``updated`` falls back to ``published``. Authors/categories may be empty.
    - IDs are canonicalized to lower case and de-duplicated with ``keep=first``.
    - Dates are UTC calendar dates (YYYY-MM-DD); ``age_days`` is measured from
      ``run_date`` and is clamped to zero for future/online-first publications.
    """
    run_timestamp = pd.Timestamp(run_date)
    if run_timestamp.tzinfo is None:
        run_timestamp = run_timestamp.tz_localize("UTC")
    else:
        run_timestamp = run_timestamp.tz_convert("UTC")
    run_day = run_timestamp.normalize()

    rows: list[dict[str, object]] = []
    dropped_missing_core = 0
    for record in records:
        paper_id = _clean_text(record.paper_id).lower()
        title = _clean_text(record.title)
        summary = _clean_text(record.summary)
        published = pd.to_datetime(record.published, errors="coerce", utc=True)
        if not paper_id or not title or pd.isna(published):
            dropped_missing_core += 1
            continue

        updated = pd.to_datetime(record.updated, errors="coerce", utc=True)
        if pd.isna(updated):
            updated = published

        authors = _clean_list(record.authors)
        categories = _clean_list(record.categories)
        primary_category = _clean_text(record.primary_category)
        if not primary_category and categories:
            primary_category = categories[0]

        authors_joined = ", ".join(authors)
        categories_joined = ", ".join(categories)
        published_day = published.normalize()
        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published_day.strftime("%Y-%m-%d"),
                "updated": updated.normalize().strftime("%Y-%m-%d"),
                "age_days": max(0, int((run_day - published_day).days)),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": len(summary),
                "text_for_embedding": build_text_for_embedding(
                    title, summary, authors_joined, categories_joined
                ),
                "abs_url": _clean_text(record.abs_url),
                "pdf_url": _clean_text(record.pdf_url),
                "comment": _clean_text(record.comment),
            }
        )

    if not rows:
        if counters is not None:
            counters.update(
                input_records=len(records),
                dropped_missing_core=dropped_missing_core,
                dropped_duplicates=0,
                clean_records=0,
            )
        return pd.DataFrame(columns=CLEAN_COLUMNS)

    clean = pd.DataFrame(rows)
    # De-duplicate before sorting so "first" means first in the raw source.
    valid_before_dedupe = len(clean)
    clean = clean.drop_duplicates(subset=["paper_id"], keep="first")
    clean = clean.sort_values(
        ["published", "paper_id"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)[CLEAN_COLUMNS]
    if counters is not None:
        counters.update(
            input_records=len(records),
            dropped_missing_core=dropped_missing_core,
            dropped_duplicates=valid_before_dedupe - len(clean),
            clean_records=len(clean),
        )
    return clean


def load_raw_records_json(path: str | Path) -> list[dict[str, object]]:
    """Load a Crossref record snapshot as a list of dictionaries."""
    raw_path = Path(path)
    payload = json.loads(raw_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and isinstance(payload.get("records"), list):
        records = payload["records"]
    else:
        raise ValueError(
            "Raw Crossref JSON must be a list or an object containing a 'records' list."
        )
    if not all(isinstance(record, dict) for record in records):
        raise ValueError("Every raw Crossref record must be a JSON object.")
    return records


def _to_paper_record(record: dict[str, object]) -> PaperRecord:
    """Map a nullable raw dictionary to the stable PaperRecord input model."""
    authors = record.get("authors")
    categories = record.get("categories")
    return PaperRecord(
        paper_id=_clean_text(record.get("paper_id")),
        title=_clean_text(record.get("title")),
        summary=_clean_text(record.get("summary")),
        authors=authors if isinstance(authors, list) else [],
        categories=categories if isinstance(categories, list) else [],
        primary_category=_clean_text(record.get("primary_category")),
        published=_clean_text(record.get("published")),
        updated=_clean_text(record.get("updated")),
        abs_url=_clean_text(record.get("abs_url")),
        pdf_url=_clean_text(record.get("pdf_url")),
        comment=_clean_text(record.get("comment")),
    )


def save_target_clean_data(
    df: pd.DataFrame,
    csv_path: str | Path,
    json_path: str | Path,
) -> None:
    """Persist exactly the agreed nine-column CP0 exchange schema."""
    missing = sorted(set(TARGET_CLEAN_COLUMNS).difference(df.columns))
    if missing:
        raise ValueError(f"Cannot export clean data; missing columns: {missing}")
    target = df[TARGET_CLEAN_COLUMNS].copy()
    csv_output = Path(csv_path)
    json_output = Path(json_path)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    target.to_csv(csv_output, index=False, encoding="utf-8-sig")
    json_output.write_text(
        json.dumps(target.to_dict(orient="records"), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_raw_to_clean(
    raw_path: str | Path = "data/raw/crossref_records.json",
    csv_path: str | Path = "data/clean/cleaned_records.csv",
    json_path: str | Path = "data/clean/cleaned_records.json",
    run_date: datetime | None = None,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Run the reusable CP0 raw-to-clean job and report evidence counters."""
    raw_dicts = load_raw_records_json(raw_path)
    records = [_to_paper_record(record) for record in raw_dicts]
    counters: dict[str, int] = {}
    clean = build_clean_dataframe(records, run_date or datetime.now().astimezone(), counters)
    save_target_clean_data(clean, csv_path, json_path)
    LOGGER.info(
        "Cleaning counts: input=%d, dropped_missing_core=%d, "
        "dropped_duplicates=%d, clean=%d",
        counters["input_records"],
        counters["dropped_missing_core"],
        counters["dropped_duplicates"],
        counters["clean_records"],
    )
    print(
        "Cleaning counts: "
        f"input={counters['input_records']}, "
        f"dropped_missing_core={counters['dropped_missing_core']}, "
        f"dropped_duplicates={counters['dropped_duplicates']}, "
        f"clean={counters['clean_records']}"
    )
    return clean, counters

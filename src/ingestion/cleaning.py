from __future__ import annotations

from datetime import datetime
from typing import Iterable

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


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


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
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
    for record in records:
        paper_id = _clean_text(record.paper_id).lower()
        title = _clean_text(record.title)
        summary = _clean_text(record.summary)
        published = pd.to_datetime(record.published, errors="coerce", utc=True)
        if not paper_id or not title or pd.isna(published):
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
        return pd.DataFrame(columns=CLEAN_COLUMNS)

    clean = pd.DataFrame(rows)
    # De-duplicate before sorting so "first" means first in the raw source.
    clean = clean.drop_duplicates(subset=["paper_id"], keep="first")
    return clean.sort_values(
        ["published", "paper_id"], ascending=[False, True], kind="stable"
    ).reset_index(drop=True)[CLEAN_COLUMNS]

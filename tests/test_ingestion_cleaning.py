from __future__ import annotations

from datetime import UTC, datetime
import json

from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import PaperRecord


def _record(
    paper_id: str,
    title: str,
    summary: str,
    *,
    published: str = "2026-08-01",
    updated: str = "",
    authors: list[str] | None = None,
    categories: list[str] | None = None,
    primary_category: str = "",
) -> PaperRecord:
    return PaperRecord(
        paper_id=paper_id,
        title=title,
        summary=summary,
        authors=authors or [],
        categories=categories or [],
        primary_category=primary_category,
        published=published,
        updated=updated,
        abs_url="",
        pdf_url="",
        comment="",
    )


def test_cp1_raw_to_clean_contract() -> None:
    raw = [
        _record(
            "10.1/ABC",
            "  A   useful title ",
            " Clean   summary. ",
            authors=["Alice", " alice ", "Bob"],
            categories=["AI", " ai "],
            primary_category="AI",
        ),
        _record(
            "10.1/abc",
            "Older duplicate",
            "Old summary",
            published="2025-01-01",
            updated="2025-01-02",
        ),
        _record("10.2/valid", "Second title", "Second summary", published="2026-07-01", updated="bad-date"),
        _record("", "Missing ID", "Summary"),
        _record("10.3/bad-date", "Bad date", "Summary", published="not-a-date"),
        _record("10.4/no-summary", "No summary", ""),
    ]

    clean = build_clean_dataframe(raw, datetime(2026, 8, 6, tzinfo=UTC))

    assert clean["paper_id"].tolist() == ["10.1/abc", "10.4/no-summary", "10.2/valid"]
    assert clean.iloc[0]["title"] == "A useful title"
    assert clean.iloc[0]["authors"] == ["Alice", "Bob"]
    assert clean.iloc[0]["categories"] == ["AI"]
    assert clean.iloc[0]["age_days"] == 5
    assert clean.loc[clean["paper_id"] == "10.2/valid", "updated"].item() == "2026-07-01"
    assert clean.loc[clean["paper_id"] == "10.4/no-summary", "summary"].item() == ""
    assert clean.iloc[0]["text_for_embedding"] == (
        "Title: A useful title\n"
        "Summary: Clean summary.\n"
        "Authors: Alice, Bob\n"
        "Categories: AI"
    )


def test_cp1_corruption_rebuilds_embedding_text_and_logs(tmp_path) -> None:
    clean = build_clean_dataframe(
        [
            _record(f"10.1/{index}", f"Title {index}", f"Summary {index}", published=f"2026-07-{index + 1:02d}")
            for index in range(12)
        ],
        datetime(2026, 8, 6, tzinfo=UTC),
    )
    log_path = tmp_path / "corruption_log.json"

    corrupted = corrupt_clean_dataframe(clean, log_path)
    log = json.loads(log_path.read_text(encoding="utf-8"))

    assert corrupted["paper_id"].duplicated().any()
    assert corrupted.apply(
        lambda row: row["text_for_embedding"].startswith(f"Title: {row['title']}\nSummary: {row['summary']}"),
        axis=1,
    ).all()
    assert {event["type"] for event in log["events"]} == {
        "drop_latest",
        "blank_summary",
        "summary_noise",
        "truncate_title",
        "stale_published",
        "duplicate_rows",
    }

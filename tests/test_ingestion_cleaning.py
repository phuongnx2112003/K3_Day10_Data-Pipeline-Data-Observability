from __future__ import annotations

from datetime import UTC, datetime
import json

from ingestion.cleaning import TARGET_CLEAN_COLUMNS, build_clean_dataframe, run_raw_to_clean
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

    baseline = clean.copy(deep=True)
    corrupted = corrupt_clean_dataframe(clean, log_path)
    log = json.loads(log_path.read_text(encoding="utf-8"))

    assert clean.equals(baseline)
    repeated = corrupt_clean_dataframe(clean, tmp_path / "repeated_log.json")
    assert corrupted.equals(repeated)
    assert log["seed"] == 42
    assert corrupted["paper_id"].duplicated().any()
    assert corrupted.apply(
        lambda row: row["text_for_embedding"].startswith(f"Title: {row['title']}\nSummary: {row['summary']}"),
        axis=1,
    ).all()
    assert {event["type"] for event in log["events"]} == {
        "latest_drop",
        "missing",
        "noise",
        "truncate_title",
        "old_date",
        "duplicate",
    }
    assert all(
        {"record_ids", "type", "parameters", "before_count", "after_count"}.issubset(event)
        for event in log["events"]
    )


def test_cp0_json_file_to_clean_outputs(tmp_path, capsys) -> None:
    raw_path = tmp_path / "crossref_records.json"
    raw_path.write_text(
        json.dumps(
            [
                {
                    "paper_id": "10.47576/2949-1894.2026.7.7.023",
                    "title": "Снижение рисков применения LLM",
                    "summary": "Исследование особенностей снижения рисков.",
                    "authors": ["И.В. Ермаков", "В.В. Филатов"],
                    "categories": [],
                    "primary_category": "",
                    "published": "2026-06-17",
                    "updated": "",
                    "abs_url": "https://example.test/abstract",
                    "pdf_url": None,
                    "comment": "",
                },
                {
                    "paper_id": "10.47576/2949-1894.2026.7.7.023",
                    "title": "Duplicate must be removed",
                    "published": "2026-06-17",
                },
                {"paper_id": "missing-title", "title": "", "published": "2026-06-17"},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    csv_path = tmp_path / "cleaned_records.csv"
    json_path = tmp_path / "cleaned_records.json"

    clean, counters = run_raw_to_clean(
        raw_path,
        csv_path,
        json_path,
        datetime(2026, 8, 6, tzinfo=UTC),
    )

    exported = json.loads(json_path.read_text(encoding="utf-8"))
    assert counters == {
        "input_records": 3,
        "dropped_missing_core": 1,
        "dropped_duplicates": 1,
        "clean_records": 1,
    }
    assert clean.iloc[0]["authors_joined"] == "И.В. Ермаков, В.В. Филатов"
    assert clean.iloc[0]["categories_joined"] == ""
    assert clean.iloc[0]["pdf_url"] == ""
    assert clean.iloc[0]["age_days"] == 50
    assert exported[0]["age_days"] == 50
    assert list(exported[0]) == TARGET_CLEAN_COLUMNS
    assert "Authors: И.В. Ермаков, В.В. Филатов" in exported[0]["text_for_embedding"]
    assert "input=3" in capsys.readouterr().out

    exported_frame = clean[TARGET_CLEAN_COLUMNS]
    corrupted = corrupt_clean_dataframe(exported_frame, tmp_path / "target_corruption.json")
    assert set(TARGET_CLEAN_COLUMNS).issubset(corrupted.columns)

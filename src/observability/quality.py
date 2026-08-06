from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def _safe_int(value: object) -> int:
    try:
        if pd.isna(value):
            return 0
    except Exception:
        pass
    try:
        return int(value)
    except Exception:
        return 0


def _quality_path(settings: Settings, report_name: str) -> Path:
    report_path = Path(report_name)
    if report_path.suffix.lower() != ".json":
        report_path = report_path.with_suffix(".json")
    if not report_path.is_absolute():
        report_path = settings.paths.quality_dir / report_path.name
    return report_path


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Run baseline data-quality checks and persist a JSON evidence file."""
    required_columns = [
        "paper_id",
        "title",
        "summary",
        "published",
        "age_days",
        "text_for_embedding",
        "authors_joined",
        "categories_joined",
    ]
    missing_columns = [column for column in required_columns if column not in df.columns]

    paper_ids = df["paper_id"].astype(str).str.strip() if "paper_id" in df.columns else pd.Series([], dtype="string")
    titles = df["title"].astype(str).str.strip() if "title" in df.columns else pd.Series([], dtype="string")
    summaries = df["summary"].fillna("").astype(str).str.strip() if "summary" in df.columns else pd.Series([], dtype="string")
    texts = (
        df["text_for_embedding"].fillna("").astype(str).str.strip()
        if "text_for_embedding" in df.columns
        else pd.Series([], dtype="string")
    )
    age_days = pd.to_numeric(df["age_days"], errors="coerce").fillna(0).astype(int) if "age_days" in df.columns else pd.Series([], dtype="int64")

    total_rows = int(len(df))
    null_paper_id = int(df["paper_id"].isna().sum()) if "paper_id" in df.columns else total_rows
    duplicate_paper_id = int(paper_ids.duplicated().sum()) if not paper_ids.empty else 0
    blank_title = int((titles == "").sum()) if not titles.empty else total_rows
    blank_summary = int((summaries == "").sum()) if not summaries.empty else total_rows
    blank_text = int((texts == "").sum()) if not texts.empty else total_rows
    stale_rows = int((age_days > settings.freshness_threshold_days).sum()) if not age_days.empty else total_rows
    summary_chars = (
        pd.to_numeric(df["summary_chars"], errors="coerce").fillna(0).astype(int)
        if "summary_chars" in df.columns
        else pd.Series([_safe_int(len(value)) for value in summaries], dtype="int64")
    )

    payload: dict[str, Any] = {
        "report_name": report_name,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_rows": total_rows,
        "required_columns": required_columns,
        "missing_columns": missing_columns,
        "checks": {
            "paper_id_not_null": null_paper_id == 0,
            "paper_id_unique": duplicate_paper_id == 0,
            "title_not_blank": blank_title == 0,
            "summary_present_ratio": round(1.0 - (blank_summary / total_rows), 4) if total_rows else 0.0,
            "text_for_embedding_present_ratio": round(1.0 - (blank_text / total_rows), 4) if total_rows else 0.0,
            "fresh_rows_ratio": round(1.0 - (stale_rows / total_rows), 4) if total_rows else 0.0,
        },
        "counts": {
            "null_paper_id": null_paper_id,
            "duplicate_paper_id": duplicate_paper_id,
            "blank_title": blank_title,
            "blank_summary": blank_summary,
            "blank_text_for_embedding": blank_text,
            "stale_rows": stale_rows,
            "min_summary_chars": int(summary_chars.min()) if len(summary_chars) else 0,
            "max_summary_chars": int(summary_chars.max()) if len(summary_chars) else 0,
            "mean_summary_chars": round(float(summary_chars.mean()), 2) if len(summary_chars) else 0.0,
        },
        "thresholds": {
            "freshness_threshold_days": settings.freshness_threshold_days,
        },
    }

    output_path = _quality_path(settings, report_name)
    write_json(output_path, payload)
    payload["output_path"] = str(output_path)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Create a JSON freshness summary for the current clean corpus."""
    output_path = Path(report_path)
    if output_path.suffix.lower() != ".json":
        output_path = output_path.with_suffix(".json")
    if not output_path.is_absolute():
        output_path = settings.paths.quality_dir / output_path.name

    if df.empty or "published" not in df.columns:
        payload: dict[str, Any] = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_rows": int(len(df)),
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": int(len(df)),
            "fresh_rows": 0,
            "freshness_threshold_days": settings.freshness_threshold_days,
            "is_fresh": False,
        }
        write_json(output_path, payload)
        payload["output_path"] = str(output_path)
        return payload

    published = pd.to_datetime(df["published"], errors="coerce", utc=True)
    age_days = pd.to_numeric(df["age_days"], errors="coerce").fillna(0).astype(int) if "age_days" in df.columns else pd.Series([0] * len(df))
    valid = published.dropna()

    latest = valid.max() if not valid.empty else None
    oldest = valid.min() if not valid.empty else None
    stale_rows = int((age_days > settings.freshness_threshold_days).sum())
    total_rows = int(len(df))

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_rows": total_rows,
        "latest_published": latest.date().isoformat() if latest is not None else None,
        "oldest_published": oldest.date().isoformat() if oldest is not None else None,
        "stale_rows": stale_rows,
        "fresh_rows": total_rows - stale_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "stale_ratio": round(stale_rows / total_rows, 4) if total_rows else 0.0,
        "is_fresh": stale_rows == 0,
    }
    write_json(output_path, payload)
    payload["output_path"] = str(output_path)
    return payload

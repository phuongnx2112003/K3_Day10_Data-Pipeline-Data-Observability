from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ingestion.cleaning import build_text_for_embedding


def _selected_indices(df: pd.DataFrame, count: int, offset: int = 0) -> list[int]:
    if df.empty:
        return []
    size = min(count, len(df))
    return [df.index[(offset + position) % len(df)] for position in range(size)]


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Create a deterministic corrupted copy and write an auditable JSON log.

    The baseline dataframe is never mutated. Selection is deterministic so the
    baseline/corrupted/repaired comparison can be reproduced at CP1 and later.
    """
    required = {
        "paper_id",
        "title",
        "summary",
        "published",
        "age_days",
        "authors_joined",
        "categories_joined",
        "text_for_embedding",
    }
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Clean dataframe is missing required columns: {missing}")

    corrupted = df.copy(deep=True).reset_index(drop=True)
    events: list[dict[str, object]] = []

    # Remove up to 10% (at least one) of the freshest records.
    drop_count = min(len(corrupted), max(1, round(len(corrupted) * 0.10))) if len(corrupted) else 0
    latest = (
        corrupted.assign(_published=pd.to_datetime(corrupted["published"], errors="coerce"))
        .sort_values("_published", ascending=False)
        .head(drop_count)
    )
    if not latest.empty:
        ids = latest["paper_id"].astype(str).tolist()
        corrupted = corrupted.drop(index=latest.index).reset_index(drop=True)
        events.append({"type": "drop_latest", "paper_ids": ids, "count": len(ids)})

    scenarios = max(1, round(len(corrupted) * 0.10)) if len(corrupted) else 0

    blank_indices = _selected_indices(corrupted, scenarios, 0)
    if blank_indices:
        corrupted.loc[blank_indices, "summary"] = ""
        events.append({"type": "blank_summary", "paper_ids": corrupted.loc[blank_indices, "paper_id"].tolist()})

    noise_indices = _selected_indices(corrupted, scenarios, scenarios)
    if noise_indices:
        corrupted.loc[noise_indices, "summary"] = corrupted.loc[noise_indices, "summary"].astype(str) + " ### CORRUPTED_NOISE_9f3a ###"
        events.append({"type": "summary_noise", "paper_ids": corrupted.loc[noise_indices, "paper_id"].tolist()})

    truncate_indices = _selected_indices(corrupted, scenarios, scenarios * 2)
    if truncate_indices:
        corrupted.loc[truncate_indices, "title"] = corrupted.loc[truncate_indices, "title"].astype(str).str.slice(0, 12)
        events.append({"type": "truncate_title", "paper_ids": corrupted.loc[truncate_indices, "paper_id"].tolist()})

    stale_indices = _selected_indices(corrupted, scenarios, scenarios * 3)
    if stale_indices:
        dates = pd.to_datetime(corrupted.loc[stale_indices, "published"], errors="coerce")
        stale_dates = dates - pd.DateOffset(years=10)
        corrupted.loc[stale_indices, "published"] = stale_dates.dt.strftime("%Y-%m-%d")
        corrupted.loc[stale_indices, "age_days"] = (
            pd.to_numeric(corrupted.loc[stale_indices, "age_days"], errors="coerce").fillna(0).astype(int) + 3652
        )
        events.append({"type": "stale_published", "paper_ids": corrupted.loc[stale_indices, "paper_id"].tolist()})

    # Rebuild derived fields after all source-field corruptions.
    corrupted["summary_chars"] = corrupted["summary"].fillna("").astype(str).str.len()
    corrupted["text_for_embedding"] = corrupted.apply(
        lambda row: build_text_for_embedding(
            str(row["title"]),
            str(row["summary"]),
            str(row["authors_joined"]),
            str(row["categories_joined"]),
        ),
        axis=1,
    )

    duplicate_count = min(scenarios, len(corrupted))
    if duplicate_count:
        duplicates = corrupted.head(duplicate_count).copy(deep=True)
        corrupted = pd.concat([corrupted, duplicates], ignore_index=True)
        events.append({"type": "duplicate_rows", "paper_ids": duplicates["paper_id"].tolist()})

    log_path = Path(output_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "baseline_rows": int(len(df)),
        "corrupted_rows": int(len(corrupted)),
        "events": events,
    }
    log_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return corrupted.reset_index(drop=True)

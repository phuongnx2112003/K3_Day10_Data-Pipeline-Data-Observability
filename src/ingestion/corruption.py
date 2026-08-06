from __future__ import annotations

import json
from pathlib import Path
import random
import string

import pandas as pd

from ingestion.cleaning import TARGET_CLEAN_COLUMNS, build_text_for_embedding


DEFAULT_CORRUPTION_SEED = 42
DEFAULT_CORRUPTION_RATE = 0.10


def _take_indices(pool: list[int], count: int) -> list[int]:
    selected = pool[:count]
    del pool[:count]
    return selected


def _noise_token(rng: random.Random, length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(rng.choice(alphabet) for _ in range(length))


def corrupt_clean_dataframe(
    df: pd.DataFrame,
    output_log_path,
    *,
    seed: int = DEFAULT_CORRUPTION_SEED,
    corruption_rate: float = DEFAULT_CORRUPTION_RATE,
) -> pd.DataFrame:
    """Create a deterministic corrupted copy and write an auditable JSON log.

    The baseline dataframe is never mutated. Selection is deterministic so the
    baseline/corrupted/repaired comparison can be reproduced at CP1 and later.
    """
    if not 0 < corruption_rate <= 1:
        raise ValueError("corruption_rate must be in the interval (0, 1].")

    required = set(TARGET_CLEAN_COLUMNS)
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Clean dataframe is missing required columns: {missing}")

    corrupted = df.copy(deep=True).reset_index(drop=True)
    events: list[dict[str, object]] = []

    # Remove up to 10% (at least one) of the freshest records.
    drop_count = (
        min(len(corrupted), max(1, round(len(corrupted) * corruption_rate)))
        if len(corrupted)
        else 0
    )
    latest = (
        corrupted.assign(_published=pd.to_datetime(corrupted["published"], errors="coerce"))
        .sort_values("_published", ascending=False)
        .head(drop_count)
    )
    if not latest.empty:
        ids = latest["paper_id"].astype(str).tolist()
        corrupted = corrupted.drop(index=latest.index).reset_index(drop=True)
        events.append({"type": "drop_latest", "paper_ids": ids, "count": len(ids)})

    scenarios = max(1, round(len(corrupted) * corruption_rate)) if len(corrupted) else 0
    rng = random.Random(seed)
    index_pool = corrupted.index.tolist()
    rng.shuffle(index_pool)

    blank_indices = _take_indices(index_pool, min(scenarios, len(index_pool)))
    if blank_indices:
        before_lengths = corrupted.loc[blank_indices, "summary"].fillna("").astype(str).str.len().tolist()
        corrupted.loc[blank_indices, "summary"] = ""
        events.append(
            {
                "type": "blank_summary",
                "paper_ids": corrupted.loc[blank_indices, "paper_id"].tolist(),
                "before_lengths": before_lengths,
                "after_length": 0,
            }
        )

    noise_indices = _take_indices(index_pool, min(scenarios, len(index_pool)))
    if noise_indices:
        noise_tokens = [_noise_token(rng) for _ in noise_indices]
        for index, token in zip(noise_indices, noise_tokens, strict=True):
            corrupted.at[index, "summary"] = f"{corrupted.at[index, 'summary']} [NOISE:{token}]"
        events.append(
            {
                "type": "summary_noise",
                "paper_ids": corrupted.loc[noise_indices, "paper_id"].tolist(),
                "noise_tokens": noise_tokens,
            }
        )

    truncate_indices = _take_indices(index_pool, min(scenarios, len(index_pool)))
    if truncate_indices:
        original_lengths = corrupted.loc[truncate_indices, "title"].astype(str).str.len().tolist()
        corrupted.loc[truncate_indices, "title"] = corrupted.loc[truncate_indices, "title"].astype(str).str.slice(0, 12)
        events.append(
            {
                "type": "truncate_title",
                "paper_ids": corrupted.loc[truncate_indices, "paper_id"].tolist(),
                "before_lengths": original_lengths,
                "max_after_length": 12,
            }
        )

    stale_indices = _take_indices(index_pool, min(scenarios, len(index_pool)))
    if stale_indices:
        dates = pd.to_datetime(corrupted.loc[stale_indices, "published"], errors="coerce")
        stale_dates = dates - pd.DateOffset(years=10)
        corrupted.loc[stale_indices, "published"] = stale_dates.dt.strftime("%Y-%m-%d")
        if "age_days" in corrupted.columns:
            corrupted.loc[stale_indices, "age_days"] = (
                pd.to_numeric(corrupted.loc[stale_indices, "age_days"], errors="coerce")
                .fillna(0)
                .astype(int)
                + 3652
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
        "seed": seed,
        "corruption_rate": corruption_rate,
        "baseline_rows": int(len(df)),
        "corrupted_rows": int(len(corrupted)),
        "events": events,
    }
    log_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return corrupted.reset_index(drop=True)

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pandas as pd

from core.config import load_settings
from observability.quality import run_data_quality_checks


def _settings_with_quality_dir(tmp_path: Path):
    settings = load_settings()
    paths = replace(settings.paths, quality_dir=tmp_path)
    return replace(settings, paths=paths)


def test_quality_check_uses_dataframe_values_and_catches_real_errors(tmp_path) -> None:
    settings = _settings_with_quality_dir(tmp_path)
    real = pd.read_json("data/clean/papers_clean.json")
    baseline = run_data_quality_checks(real, settings, "cp3_real")
    assert baseline["overall_pass"] is True

    broken = real.copy(deep=True)
    broken.loc[0, "paper_id"] = ""
    broken.loc[1, "paper_id"] = broken.loc[2, "paper_id"].upper()
    broken.loc[0, "title"] = ""
    broken.loc[0, "text_for_embedding"] = ""
    broken.loc[0, "published"] = "not-a-date"
    broken.loc[0, "age_days"] = -1
    failed = run_data_quality_checks(broken, settings, "cp3_intentionally_broken")

    assert failed["overall_pass"] is False
    assert failed["checks"]["paper_id_not_blank"] is False
    assert failed["checks"]["paper_id_unique"] is False
    assert failed["checks"]["title_not_blank"] is False
    assert failed["checks"]["text_for_embedding_not_blank"] is False
    assert failed["checks"]["published_valid"] is False
    assert failed["checks"]["age_days_valid"] is False

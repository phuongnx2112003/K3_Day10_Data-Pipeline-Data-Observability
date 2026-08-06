import sys
from pathlib import Path
from datetime import datetime, UTC
import json

sys.path.append(str(Path("src").resolve()))

from core.config import load_settings
from ingestion.crossref import fetch_source_records
from ingestion.cleaning import build_clean_dataframe

settings = load_settings()

print("Fetching raw data...")
records = fetch_source_records(settings)

print(f"Fetched {len(records)} records. Cleaning...")
df = build_clean_dataframe(records, datetime.now(UTC))

print(f"Cleaned {len(df)} records. Saving...")
settings.paths.clean_csv.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(settings.paths.clean_csv, index=False)
records_json = df.to_dict(orient="records")
with open(settings.paths.clean_json, "w", encoding="utf-8") as f:
    json.dump(records_json, f, indent=2, ensure_ascii=False)

print("Done generating clean data.")

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.config import Settings


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    import logging
    logger = logging.getLogger(__name__)
    records = []
    items = payload.get("message", {}).get("items", [])
    
    for item in items:
        try:
            paper_id = item.get("DOI", "")
            if not paper_id:
                continue

            titles = item.get("title", [])
            title = titles[0] if titles else ""
            if not title:
                continue

            summary = item.get("abstract", "")
            if summary:
                summary = summary.replace("<jats:p>", "").replace("</jats:p>", "")
                summary = summary.replace("<jats:title>", "").replace("</jats:title>", "")
                summary = summary.strip()

            author_list = item.get("author", [])
            authors = []
            for a in author_list:
                given = a.get("given", "")
                family = a.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)

            categories = item.get("subject", [])
            primary_category = categories[0] if categories else ""

            created_date_parts = item.get("created", {}).get("date-parts", [[]])[0]
            published = "-".join(f"{part:02d}" for part in created_date_parts) if created_date_parts else ""

            updated_date_parts = item.get("indexed", {}).get("date-parts", [[]])[0]
            updated = "-".join(f"{part:02d}" for part in updated_date_parts) if updated_date_parts else ""

            abs_url = f"https://doi.org/{paper_id}"
            pdf_url = ""
            for link in item.get("link", []):
                if link.get("content-type") == "application/pdf":
                    pdf_url = link.get("URL", "")
                    break

            comment = item.get("publisher", "")

            records.append(PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment
            ))
        except Exception as e:
            logger.warning(f"Failed to parse item {item.get('DOI')}: {e}")
            continue

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    import requests
    import time
    import json
    from dataclasses import asdict
    import logging
    
    logger = logging.getLogger(__name__)
    url = "https://api.crossref.org/works"
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results
    }
    
    max_retries = 3
    retry_delay = 5
    
    response = None
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching from Crossref API (attempt {attempt + 1})...")
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                break
            elif response.status_code in (429, 503):
                logger.warning(f"Received status {response.status_code}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                response.raise_for_status()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to fetch from Crossref API: {e}")
            logger.warning(f"Request failed: {e}. Retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay *= 2
            
    if not response or response.status_code != 200:
        raise RuntimeError("Failed to fetch data from Crossref.")

    payload = response.json()
    
    settings.paths.raw_api_response.parent.mkdir(parents=True, exist_ok=True)
    with open(settings.paths.raw_api_response, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        
    records = parse_crossref_payload(payload)
    
    settings.paths.raw_records_json.parent.mkdir(parents=True, exist_ok=True)
    records_dict = [asdict(r) for r in records]
    with open(settings.paths.raw_records_json, "w", encoding="utf-8") as f:
        json.dump(records_dict, f, ensure_ascii=False, indent=2)
        
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    import json
    if not path.exists():
        return []
        
    with open(path, "r", encoding="utf-8") as f:
        records_dict = json.load(f)
        
    return [PaperRecord(**r) for r in records_dict]

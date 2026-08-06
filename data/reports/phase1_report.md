# Phase 1 Baseline Report

## Source Summary
- Source API: Crossref REST API
- Query: agentic retrieval augmented generation large language model
- Filter: from-pub-date:2026-02-07,has-abstract:true
- Raw records: 24
- Clean records: 24
- Test set samples: 72
- Embedding documents: 24

## Metrics
- Retrieval hit rate: 1.0
- Mean token F1: 0.7569240806733034
- Judge accuracy: 0.6666666666666666
- Mean judge score: 3.9583333333333335
- Ragas: {'skipped': 'Set RUN_RAGAS=1 to enable the slower Ragas pass.'}

## Data Quality
- Total rows: 24
- Missing columns: []
- Duplicate paper_id: 0
- Blank summary: 0
- Blank text_for_embedding: 0
- Fresh rows ratio: 0.9583

## Freshness
- Latest published: 2026-08-05
- Oldest published: 2026-01-25
- Stale rows: 1
- Freshness threshold days: 180
- Is fresh: False

## Conclusion
- Baseline artifacts are ready for downstream corruption and comparison stages.

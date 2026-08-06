# Corruption Comparison Report

## Metrics Comparison
- Baseline retrieval hit rate: 1.0
- Corrupted retrieval hit rate: 0.9166666666666666
- Repaired retrieval hit rate: 1.0
- Retrieval hit rate delta corrupted vs baseline: -0.083333
- Retrieval hit rate delta repaired vs baseline: 0.0
- Baseline mean token F1: 0.4235907473399701
- Corrupted mean token F1: 0.660252909856381
- Repaired mean token F1: 0.7569240806733034
- Mean token F1 delta corrupted vs baseline: 0.236662
- Mean token F1 delta repaired vs baseline: 0.333333
- Baseline judge accuracy: 0.3333333333333333
- Corrupted judge accuracy: 0.6388888888888888
- Repaired judge accuracy: 0.6805555555555556
- Judge accuracy delta corrupted vs baseline: 0.305556
- Judge accuracy delta repaired vs baseline: 0.347222
- Baseline mean judge score: 2.625
- Corrupted mean judge score: 3.7777777777777777
- Repaired mean judge score: 3.9583333333333335
- Mean judge score delta corrupted vs baseline: 1.152778
- Mean judge score delta repaired vs baseline: 1.333333

## Quality Comparison
- Baseline overall pass: True
- Corrupted overall pass: False
- Repaired overall pass: True
- Corrupted duplicate paper_id: 2
- Repaired duplicate paper_id: 0
- Corrupted blank summary: 2
- Repaired blank summary: 0
- Corrupted blank text_for_embedding: 0
- Repaired blank text_for_embedding: 0
- Baseline stale rows: 1
- Corrupted stale rows: 3
- Repaired stale rows: 1

## Freshness Comparison
- Baseline stale rows: 1
- Corrupted stale rows: 3
- Repaired stale rows: 1
- Baseline is fresh: False
- Corrupted is fresh: False
- Repaired is fresh: False

## Notes
- Baseline should remain untouched while corrupted and repaired artifacts are rebuilt separately.

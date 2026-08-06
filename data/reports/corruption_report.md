# Corruption Comparison Report

## Metrics Comparison
- Baseline retrieval hit rate: 1.0
- Corrupted retrieval hit rate: 0.9166666666666666
- Repaired retrieval hit rate: 1.0
- Retrieval hit rate delta corrupted vs baseline: -0.083333
- Retrieval hit rate delta repaired vs baseline: 0.0
- Baseline mean token F1: 0.4235907473399701
- Corrupted mean token F1: 0.35469735430082544
- Repaired mean token F1: 0.4235907473399701
- Mean token F1 delta corrupted vs baseline: -0.068893
- Mean token F1 delta repaired vs baseline: 0.0
- Baseline judge accuracy: 0.3333333333333333
- Corrupted judge accuracy: 0.2916666666666667
- Repaired judge accuracy: 0.3472222222222222
- Judge accuracy delta corrupted vs baseline: -0.041667
- Judge accuracy delta repaired vs baseline: 0.013889
- Baseline mean judge score: 2.625
- Corrupted mean judge score: 2.138888888888889
- Repaired mean judge score: 2.361111111111111
- Mean judge score delta corrupted vs baseline: -0.486111
- Mean judge score delta repaired vs baseline: -0.263889

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

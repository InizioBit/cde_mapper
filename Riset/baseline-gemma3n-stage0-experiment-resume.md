# Resume Eksperimen Baseline: baseline-gemma3n-stage0

## Retrieval hybrid Qdrant dense-sparse
- Status: completed_with_errors
- Query: 10; coverage: 100.00%
- Collection: concept_mapping_1
- Accuracy@1/@3/@5/@10: 0.60 / 0.60 / 0.70 / 0.90
- MRR: 0.6400; NDCG@10: 0.6965
- Latency mean/p50/p95: 1471.09 / 1430.44 / 1656.60 ms

## Reranking Gemma
- Model: google/gemma-3n-E4B-it
- Berhasil: 10/10 query
- Accuracy@1/@3/@5/@10: 0.50 / 0.70 / 0.80 / 0.90
- MRR: 0.6343; NDCG@10: 0.6982

## Delta reranking terhadap hybrid
- Accuracy@1: -0.1000
- Accuracy@3: +0.1000
- Accuracy@5: +0.1000
- MRR: -0.0057
- NDCG@10: +0.0017

## Artifact
- Retrieval: data\output\baseline\baseline-gemma3n-stage0.jsonl
- Manifest: data\output\baseline\baseline-gemma3n-stage0.manifest.json
- Reranking: data\output\baseline\baseline-gemma3n-stage0-reranked.jsonl
- Metrik hybrid: Riset\baseline-gemma3n-stage0-hybrid-metrics.json
- Metrik reranking: Riset\baseline-gemma3n-stage0-reranked-metrics.json

# Resume Eksperimen Baseline: baseline-gemma3n-stage0

## Retrieval hybrid Qdrant dense-sparse
- Status: completed
- Query: 10; coverage: 100.00%
- Collection: concept_mapping_1
- Accuracy@1/@3/@5/@10: 0.60 / 0.60 / 0.60 / 0.70
- MRR: 0.6143; NDCG@10: 0.6333
- Latency mean/p50/p95: 3665.23 / 2431.47 / 10177.49 ms

## Reranking Gemma
- Model: google/gemma-3n-E4B-it
- Berhasil: 10/10 query
- Accuracy@1/@3/@5/@10: 0.20 / 0.30 / 0.60 / 0.70
- MRR: 0.3261; NDCG@10: 0.4136

## Delta reranking terhadap hybrid
- Accuracy@1: -0.4000
- Accuracy@3: -0.3000
- Accuracy@5: +0.0000
- MRR: -0.2882
- NDCG@10: -0.2197

## Artifact
- Retrieval: data\output\baseline\baseline-gemma3n-stage0.jsonl
- Manifest: data\output\baseline\baseline-gemma3n-stage0.manifest.json
- Reranking: data\output\baseline\baseline-gemma3n-stage0-reranked.jsonl
- Metrik hybrid: Riset\baseline-gemma3n-stage0-hybrid-metrics.json
- Metrik reranking: Riset\baseline-gemma3n-stage0-reranked-metrics.json

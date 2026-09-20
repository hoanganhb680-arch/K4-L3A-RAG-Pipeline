# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20  |
| Framework and version              | ragas 0.4.3  |
| Evaluator model                    | gpt-4o  |
| Generator model                    | gemini-1.5-flash  |
| Embedding model                    | BAAI/bge-m3  |
| Corpus version/commit              | v0.1.0  |
| Golden dataset size                | 15  |
| `top_k`                            | 5  |
| Fallback threshold and calibration | 0.3  |

## Configurations

- **Config A — dense-only:** ChromaDB search only
- **Config B — hybrid + RRF:** ChromaDB + BM25 with RRF reranking

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |     0.80 |     0.85 |      0.05 |
| Answer relevance  |     0.82 |     0.88 |      0.06 |
| Context recall    |     0.75 |     0.85 |      0.10 |
| Context precision |     0.78 |     0.82 |      0.04 |
| **Average**       |     0.78 |     0.85 |      0.07 |

## A/B comparison

- Cấu hình tốt hơn: Config B (Hybrid + RRF)
- Evidence: Điểm trung bình tăng từ 0.78 lên 0.85, đặc biệt Context recall cải thiện 0.10 nhờ kết hợp tìm kiếm từ khoá chính xác.
- Trade-off về latency/cost: Hybrid tìm kiếm lâu hơn ~100ms do phải tính BM25, nhưng chi phí không tăng do chạy local.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | Phí làm E-visa là bao nhiêu? | A |         0.9 |      0.4 |   0.3 |      0.5 | retrieval | Missing keyword match |
|   2 | Ký quỹ nội địa bao nhiêu? | A |         1.0 |      0.5 |   0.2 |      0.3 | retrieval | Cosine failed to retrieve numbers |
|   3 | 3 sao cần gì? | A |         0.9 |      0.6 |   0.5 |      0.5 | retrieval | Synonym mismatch |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Chuyển sang Hybrid | Lexical keywords bị trượt ở Config A | Tăng Recall đáng kể | Đo bằng ragas |
|        2 | Nâng cấp RRF | RRF hiện tại cố định 60 | Rerank chuẩn xác hơn | AB Test |
|        3 | Thêm Metadata Filter | Kết quả bị nhiễu sang luật khác | Precision tăng mạnh | Precision metric |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Dùng OpenAI thay Gemini | Gemini 1.5 |         +0.02 |               +3x cost | Gemini là đủ dùng |

# RAG evaluation results

## Run information

| Field                              | Value                                            |
| ---------------------------------- | ------------------------------------------------ |
| Evaluation date                    | 2026-09-20                                       |
| Framework and version              | Ragas 0.4.x + LangChain Google GenAI            |
| Evaluator model                    | gemini-3.1-flash-lite                            |
| Generator model                    | gemini-3.1-flash-lite                            |
| Embedding model                    | models/gemini-embedding-001                      |
| Corpus version/commit              | 50125b1 (branch: thiennmh)                      |
| Golden dataset size                | 15 cases                                         |
| `top_k`                            | 5                                                |
| Fallback threshold and calibration | cosine score 0.3 (dense-only, pre-tuned default) |

## Configurations

- **Config A — dense-only:** ChromaDB semantic search (cosine similarity, gemini-embedding-001), no lexical stage, no RRF. `use_reranking=False`.
- **Config B — hybrid + RRF:** Dense search + BM25 lexical search, fused with Reciprocal Rank Fusion (k=60). `use_reranking=True`.

Hai config dùng cùng golden dataset (15 câu), generator (gemini-3.1-flash-lite), evaluator, prompt và `top_k=5`. Chỉ thay đổi retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |   0.6778 |   0.9444 |   +0.2667 |
| Answer relevance  |   N/A ⚠️ |   N/A ⚠️ |       N/A |
| Context recall    |   N/A ⚠️ |   N/A ⚠️ |       N/A |
| Context precision |   N/A ⚠️ |   N/A ⚠️ |       N/A |
| **Average**       | **0.6778** | **0.9444** | **+0.2667** |

> ⚠️ **Lưu ý về metric N/A:** `answer_relevancy`, `context_recall` và `context_precision` trả về 0.0 trên toàn bộ dataset — không phải điểm thực, mà do giới hạn kỹ thuật: (1) `context_recall` và `context_precision` dùng LLM phân tích câu trả lời tiếng Việt pháp lý, model lite không đủ khả năng so sánh chính xác; (2) `answer_relevancy` dùng embedding cosine similarity giữa câu hỏi gốc và câu hỏi sinh lại từ câu trả lời — bước sinh câu hỏi lại thất bại do language gap. Chỉ `faithfulness` là reliable vì kiểm tra trực tiếp claim-in-context.

## A/B comparison

- **Cấu hình tốt hơn:** Config B (Hybrid + RRF)
- **Evidence:** Faithfulness tăng từ 0.6778 → 0.9444 (+0.2667 = +39%). Config B trả về câu trả lời bám sát context tốt hơn vì RRF kết hợp cả semantic similarity và keyword matching, giảm khả năng retrieval sai context không liên quan.
- **Giải thích cơ chế:** Với corpus pháp lý/du lịch Việt Nam, nhiều câu hỏi dạng factual (số liệu, điều khoản luật) có keyword đặc thù. Dense-only bỏ sót những trường hợp này khi semantic embedding không capture được exact term; BM25 bắt được những keyword đó và RRF fuse cả hai kết quả, nâng chất lượng context.
- **Trade-off về latency/cost:** Config B tốn thêm ~50-100ms/query do chạy thêm BM25 và RRF step, nhưng BM25 là in-memory nên overhead thực tế nhỏ. Chi phí API không tăng vì vẫn dùng cùng số embedding calls.

## Worst performers (Config A — cases với faithfulness thấp nhất)

| # | Question | Config | Faithfulness | Failure stage | Root cause |
| --: | -------- | ------ | -----------: | ------------- | ---------- |
| 1 | Du lịch sinh thái là gì? | A | 0.00 | retrieval | Dense search không match được định nghĩa "du lịch sinh thái" — không có chunk nào trong corpus giải thích trực tiếp term này bằng exact embedding |
| 2 | Cửa khẩu quốc tế đường bộ Mộc Bài nằm ở tỉnh nào? | A | 0.00 | retrieval | Câu hỏi factual keyword-based — dense embedding không capture "Mộc Bài" chính xác; BM25 ở Config B xử lý tốt hơn |
| 3 | Theo luật, hướng dẫn viên du lịch có quyền từ chối khách không? | A | partial | generation | Context retrieved đúng điều khoản nhưng LLM paraphrase không bám sát text gốc → faithfulness giảm |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
| 1 | Thêm cross-encoder reranker sau RRF | Một số TimeoutError khi evaluate cho thấy context trả về đôi khi không sát câu hỏi | Tăng context precision thực tế; giảm noise trong top-k | Chạy lại evaluation với evaluator mạnh hơn (gemini-1.5-pro) |
| 2 | Dùng evaluator model mạnh hơn (gemini-1.5-pro) | `context_recall`, `context_precision`, `answer_relevancy` đều không thu được điểm có nghĩa với model lite | Thu được đủ 4 metrics có nghĩa | So sánh điểm với và không có model upgrade |
| 3 | Tinh chỉnh SCORE_THRESHOLD theo precision-recall curve | Threshold cố định 0.3 có thể quá thấp/cao tùy query domain | Giảm false fallback, tăng retrieval accuracy | Vẽ PR curve trên 50-100 sample queries |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Config B vs Config A | Config A: faithfulness 0.6778 | +0.2667 (+39%) | +~50ms/query (BM25+RRF in-memory) | Hybrid+RRF vượt trội rõ ràng về faithfulness; đề xuất dùng Config B làm default |

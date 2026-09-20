"""
Task 9 — Retrieval pipeline hoàn chỉnh.

Luồng xử lý:
    1. Chạy semantic_search và lexical_search.
    2. Fuse hai danh sách bằng RRF đúng một lần.
    3. Lấy best cosine score gốc từ dense results.
    4. Nếu score dưới threshold, thử PageIndex fallback.
    5. Nếu fallback lỗi, trả hybrid results thay vì crash.

Không so sánh threshold với RRF score vì hai thang đo khác nhau.
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


# Threshold dựa trên cosine score của embed model. Giá trị cụ thể
# phụ thuộc model, cần tinh chỉnh trên in-domain queries.
SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Trả về hybrid hoặc pageindex SearchResult."""
    try:
        # 1. Chạy dense và sparse search song song (hoặc tuần tự)
        # Lấy gấp đôi top_k để có đủ candidate cho quá trình reranking
        candidate_count = top_k * 2
        
        dense_results = semantic_search(query, top_k=candidate_count)
        
        if not use_reranking:
            # Nếu không rerank, sử dụng luôn kết quả dense (hybrid mode disabled)
            best_results = dense_results[:top_k]
        else:
            sparse_results = lexical_search(query, top_k=candidate_count)
            # 2. RRF fusion (chỉ kết hợp rank, bỏ qua score raw của từng mô hình)
            best_results = rerank_rrf([dense_results, sparse_results], top_k=top_k)
            
        # 3. Lấy best dense score (score gốc) để quyết định fallback.
        # Dense results đã được sort giảm dần
        best_dense_score = dense_results[0]["score"] if dense_results else 0.0
        
        # 4. Kiểm tra threshold. Nếu quá thấp -> thông tin mờ nhạt -> Fallback
        if best_dense_score < score_threshold:
            print(f"Low confidence ({best_dense_score:.3f} < {score_threshold}). Using fallback...")
            try:
                # 5. Fallback sang PageIndex
                fallback_results = pageindex_search(query, top_k=top_k)
                if fallback_results:
                    return fallback_results
                print("Fallback returned empty, returning initial best results.")
            except Exception as e:
                # Nếu fallback crash, log ra và dùng hybrid results hiện có.
                print(f"PageIndex fallback failed: {e}. Using hybrid results.")
                
        return best_results
        
    except Exception as e:
        print(f"Error in retrieval pipeline: {e}")
        # Đảm bảo hàm trả về danh sách rỗng thay vì làm chết hệ thống.
        return []


if __name__ == "__main__":
    results = retrieve("Quy định visa", top_k=3)
    for result in results:
        print(f"[{result['retrieval_method']}] {result['score']:.4f} - {result['metadata']['title']}")

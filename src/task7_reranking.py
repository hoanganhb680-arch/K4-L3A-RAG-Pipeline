"""
Task 7 — Reciprocal Rank Fusion.

RRF gộp nhiều bảng xếp hạng mà không cộng trực tiếp cosine score với BM25
score. Công thức: RRF(d) = sum(1 / (k + rank)), rank bắt đầu từ 1.

Lưu ý: RRF score chỉ phản ánh thứ hạng, không dùng để quyết định fallback.

-> Tự build hàm RRF đơn giản.
"""

from .contracts import validate_search_results


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhiều ranked lists và trả hybrid SearchResult."""
    scores = {}
    items = {}
    
    for ranked_list in ranked_lists:
        # Mỗi ranked list đóng góp vào tổng score dựa trên thứ hạng (rank từ 1)
        for rank, item in enumerate(ranked_list, 1):
            item_id = item["id"]
            
            # Tính điểm RRF cho vị trí này
            rrf_score = 1.0 / (k + rank)
            scores[item_id] = scores.get(item_id, 0.0) + rrf_score
            
            # Lưu lại thông tin item nếu chưa có
            if item_id not in items:
                items[item_id] = item
                
    # Sắp xếp các document theo tổng điểm RRF giảm dần
    ranked_ids = sorted(scores.keys(), key=lambda i: scores[i], reverse=True)
    
    results = []
    for item_id in ranked_ids[:top_k]:
        # Copy item để không ảnh hưởng đến object gốc
        result = items[item_id].copy()
        
        # Cập nhật thông tin cho kết quả hybrid
        result["score"] = float(scores[item_id])
        result["retrieval_method"] = "hybrid"
        results.append(result)
        
    # Validate kết quả trả về
    validate_search_results(results, expected_method="hybrid")
    return results


if __name__ == "__main__":
    print("Implemented rerank_rrf, ready to be tested.")

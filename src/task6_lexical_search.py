"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

from .contracts import validate_search_results
from .task4_chunking_indexing import get_collection


CORPUS: list[dict] = []
BM25_INDEX = None


def _load_corpus_from_chroma():
    """Tải toàn bộ chunks từ ChromaDB để làm corpus cho BM25."""
    global CORPUS
    if CORPUS:
        return
        
    try:
        collection = get_collection()
        response = collection.get(include=["documents", "metadatas"])
        
        if not response or not response["ids"]:
            print("Warning: ChromaDB is empty. Run task 4 first.")
            return
            
        for i in range(len(response["ids"])):
            metadata = response["metadatas"][i]
            if "url" in metadata and metadata["url"] == "":
                metadata["url"] = None
                
            CORPUS.append({
                "id": response["ids"][i],
                "content": response["documents"][i],
                "metadata": metadata,
            })
    except Exception as e:
        print(f"Error loading corpus from Chroma: {e}")


def build_bm25_index(corpus: list[dict]):
    """Tạo BM25 index từ cùng corpus chunks của Task 4."""
    from rank_bm25 import BM25Okapi  # type: ignore[import-untyped]
    
    if not corpus:
        return None
        
    # Tiền xử lý văn bản: chuyển thành chữ thường và tách từ cơ bản
    tokenized = [item["content"].lower().split() for item in corpus]
    return BM25Okapi(tokenized)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    import numpy as np
    global BM25_INDEX
    
    _load_corpus_from_chroma()
    
    if not CORPUS:
        return []
        
    if BM25_INDEX is None or getattr(BM25_INDEX, "corpus_size", -1) != len(CORPUS):
        BM25_INDEX = build_bm25_index(CORPUS)
        
    if BM25_INDEX is None:
        return []

    # Tiền xử lý query
    tokenized_query = query.lower().split()
    scores = BM25_INDEX.get_scores(tokenized_query)
    
    # Lấy top_k kết quả tốt nhất
    indices = np.argsort(scores)[::-1][:top_k]
    
    results = []
    for index in indices:
        if scores[index] <= 0:
            # BM25Okapi can return 0.0 or negative scores for valid matches in very small corpora
            # Ensure we only skip if the document genuinely doesn't contain any query terms
            content_lower = CORPUS[index]["content"].lower()
            if not any(term in content_lower for term in tokenized_query):
                continue
            
        item = CORPUS[index]
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(scores[index]),
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })
        
    # Validate kết quả
    validate_search_results(results, expected_method="bm25")
    return results


if __name__ == "__main__":
    for result in lexical_search("visa việt nam", top_k=3):
        print(f"Score: {result['score']:.4f} | {result['metadata']['title']} | ID: {result['id']}")

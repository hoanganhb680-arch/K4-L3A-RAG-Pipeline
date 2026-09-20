"""
Task 5 — Semantic search.

Embed query bằng chính hàm của Task 4, query ChromaDB và đổi cosine distance
thành similarity. Output phải theo SearchResult, sort giảm dần và không quá top_k.
"""

from .contracts import validate_search_results
from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về dense SearchResult theo score giảm dần."""
    # Nhúng câu truy vấn
    query_vectors = embed_texts([query])
    if not query_vectors:
        return []
        
    query_vector = query_vectors[0]
    
    try:
        collection = get_collection()
        
        # Query ChromaDB
        response = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        
        if not response or not response["ids"] or not response["ids"][0]:
            return []
            
        results = []
        for item_id, content, metadata, distance in zip(
            response["ids"][0],
            response["documents"][0],
            response["metadatas"][0],
            response["distances"][0],
        ):
            # ChromaDB lưu distance theo L2 hoặc Cosine. 
            # Với cấu hình cosine distance (0 là giống nhất, 2 là khác nhất)
            # Similarity score = 1.0 - distance
            score = max(0.0, 1.0 - distance)
            
            # Chuẩn hóa metadata (url có thể rỗng)
            if "url" in metadata and metadata["url"] == "":
                metadata["url"] = None
                
            results.append({
                "id": item_id,
                "content": content,
                "score": score,
                "metadata": metadata,
                "retrieval_method": "dense",
            })
            
        # Sắp xếp giảm dần theo điểm số
        results = sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]
        
        # Validate output bằng contract
        validate_search_results(results, expected_method="dense")
        return results
        
    except Exception as e:
        print(f"Error in semantic_search: {e}")
        return []


if __name__ == "__main__":
    for result in semantic_search("visa việt nam", top_k=3):
        print(f"Score: {result['score']:.4f} | {result['metadata']['title']} | ID: {result['id']}")

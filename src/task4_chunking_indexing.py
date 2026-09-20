"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Import các schema validator để đảm bảo dữ liệu đúng chuẩn
from .contracts import validate_document


load_dotenv()

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm:
# 500 ký tự là kích thước vừa phải để LLM lấy context mà không bị nhiễu.
# Overlap 50 ký tự giúp giữ ngữ cảnh giữa 2 chunks liên tiếp.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

# Mặc định dùng SentenceTransformers vì chạy local miễn phí, chất lượng tốt cho tiếng Việt
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed văn bản theo provider được cấu hình trong .env."""
    if not texts:
        return []

    if EMBEDDING_PROVIDER == "sentence_transformers":
        from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
        
        # Load model, cache để tối ưu nếu gọi nhiều lần
        if not hasattr(embed_texts, "_model"):
            embed_texts._model = SentenceTransformer(EMBEDDING_MODEL) # type: ignore
        
        embeddings = embed_texts._model.encode(texts) # type: ignore
        return embeddings.tolist()
        
    elif EMBEDDING_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        
        if not hasattr(embed_texts, "_model"):
            embed_texts._model = OpenAIEmbeddings(model=EMBEDDING_MODEL) # type: ignore
            
        return embed_texts._model.embed_documents(texts) # type: ignore
        
    elif EMBEDDING_PROVIDER == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        
        if not hasattr(embed_texts, "_model"):
            embed_texts._model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL) # type: ignore
            
        return embed_texts._model.embed_documents(texts) # type: ignore
        
    else:
        raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    
    if not STANDARDIZED_DIR.exists():
        print(f"Directory not found: {STANDARDIZED_DIR}. Please run task 3 first.")
        return []

    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        doc_type = "legal" if "legal" in path.parts else "news"
        
        # Đọc nội dung file
        content = path.read_text(encoding="utf-8")
        
        # Parse YAML header metadata
        metadata = {
            "source": path.name,
            "title": path.stem.replace("-", " ").title(),
            "doc_type": doc_type,
            "url": None,
        }
        
        # Trích xuất metadata từ YAML header nếu có
        lines = content.split("\n")
        if lines and lines[0] == "---":
            end_idx = -1
            for i in range(1, len(lines)):
                if lines[i] == "---":
                    end_idx = i
                    break
            
            if end_idx != -1:
                # Xóa phần header khỏi nội dung chính
                content = "\n".join(lines[end_idx+1:]).strip()
                
                # Parse từng dòng metadata
                for i in range(1, end_idx):
                    line = lines[i].strip()
                    if ":" in line:
                        k, v = line.split(":", 1)
                        metadata[k.strip()] = v.strip()
                        
                        if k.strip() == "url" and v.strip():
                            metadata["url"] = v.strip()
        
        doc = {
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": metadata,
        }
        
        # Validate xem document có hợp lệ không
        validate_document(doc, require_chunk=False)
        documents.append(doc)
        
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    
    chunks = []
    for document in documents:
        # Nếu content trống, bỏ qua
        if not document["content"].strip():
            continue
            
        texts = splitter.split_text(document["content"])
        
        for index, text in enumerate(texts):
            # Tạo metadata mới bổ sung chunk_index
            metadata = document["metadata"].copy()
            metadata["chunk_index"] = index
            
            chunk = {
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": metadata,
            }
            
            # Đảm bảo chunk đúng hợp đồng
            validate_document(chunk, require_chunk=True)
            chunks.append(chunk)
            
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    if not chunks:
        return []
        
    print(f"Embedding {len(chunks)} chunks using {EMBEDDING_PROVIDER} ({EMBEDDING_MODEL})...")
    
    # Extract text from all chunks
    texts = [chunk["content"] for chunk in chunks]
    
    # Lấy vectors, xử lý batch nếu có quá nhiều chunks
    batch_size = 100
    all_vectors = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        print(f"  Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}...")
        batch_vectors = embed_texts(batch_texts)
        all_vectors.extend(batch_vectors)
        
    # Gắn embedding ngược lại vào chunk objects
    for chunk, vector in zip(chunks, all_vectors):
        chunk["embedding"] = vector
        
    return chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        print("No chunks to index.")
        return
        
    collection = get_collection()
    
    ids = []
    documents = []
    embeddings = []
    metadatas = []
    
    for chunk in chunks:
        ids.append(chunk["id"])
        documents.append(chunk["content"])
        embeddings.append(chunk["embedding"])
        
        # ChromaDB không hỗ trợ nested dicts hoặc None values trong metadata
        # Cần chuẩn hóa metadata
        meta = {}
        for k, v in chunk["metadata"].items():
            if v is None:
                meta[k] = ""  # ChromaDB không thích null/None
            else:
                meta[k] = v
        metadatas.append(meta)
    
    print(f"Upserting {len(ids)} chunks to ChromaDB...")
    
    # Chia batch để upsert nếu quá nhiều
    batch_size = 5000
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i:i + batch_size],
            documents=documents[i:i + batch_size],
            embeddings=embeddings[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    print(f"Loaded {len(documents)} documents.")
    
    if not documents:
        return
        
    chunks = chunk_documents(documents)
    print(f"Split into {len(chunks)} chunks.")
    
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    
    print(f"Successfully indexed {len(embedded_chunks)} chunks.")


if __name__ == "__main__":
    run_pipeline()

"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .contracts import validate_generation_result
from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")

SYSTEM_PROMPT = """Bạn là một trợ lý ảo thông minh về Du lịch Việt Nam.
Trả lời câu hỏi CỦA NGƯỜI DÙNG chỉ dựa trên CONTEXT được cung cấp.
Mỗi khẳng định trong câu trả lời phải kèm theo citation nguồn tài liệu ở dạng [Document X].
Nếu CONTEXT không có thông tin để trả lời câu hỏi, hãy từ chối lịch sự và KHÔNG tự bịa thông tin.
Tuyệt đối chỉ sử dụng tiếng Việt."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context để giảm lost-in-the-middle."""
    if not chunks:
        return []
    if len(chunks) <= 2:
        return list(chunks)
        
    # Sắp xếp lại: 0, 2, 4... ở đầu; ...5, 3, 1 ở cuối
    # Chunk 0 (quan trọng nhất) -> Đầu tiên
    # Chunk 1 (quan trọng nhì) -> Cuối cùng
    front = chunks[0::2]
    back = chunks[1::2]
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label để LLM trích dẫn."""
    parts = []
    # Lưu ý: cần truyền chỉ số gốc (rank) hoặc đánh số theo thứ tự truyền vào LLM
    # Để đơn giản, đánh số theo thứ tự reordered list
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        title = metadata.get("title", "Unknown Title")
        source = metadata.get("source", "Unknown Source")
        
        parts.append(
            f"[Document {index} | Title: {title} | Source: {source}]\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi OpenAI, Gemini hoặc Anthropic theo cấu hình."""
    if LLM_PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        response = client.chat.completions.create(
            model=model,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content or ""
        
    elif LLM_PROVIDER == "gemini":
        import google.generativeai as genai  # type: ignore[import-untyped]
        
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash")
        
        generation_config = genai.types.GenerationConfig(
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )
        
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_prompt,
            generation_config=generation_config
        )
        
        response = model.generate_content(user_message)
        return response.text
        
    elif LLM_PROVIDER == "anthropic":
        from anthropic import Anthropic
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        model = os.getenv("LLM_MODEL", "claude-3-haiku-20240307")
        
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        return response.content[0].text
        
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    # 1. Retrieve chunks
    chunks = retrieve(query, top_k=top_k)
    
    # Nếu không tìm thấy thông tin gì, trả về câu từ chối an toàn
    if not chunks:
        result = {
            "answer": "Tôi không thể tìm thấy thông tin liên quan trong cơ sở dữ liệu để trả lời câu hỏi của bạn.",
            "sources": [],
            "retrieval_source": "none",
        }
        validate_generation_result(result)
        return result
        
    # 2. Reorder for LLM
    reordered_chunks = reorder_for_llm(chunks)
    
    # 3. Format context
    context = format_context(reordered_chunks)
    user_message = f"CONTEXT:\n{context}\n\nQUESTION: {query}"
    
    # 4. Call LLM
    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
        
        retrieval_source = "hybrid"
        # Xác định retrieval_source chung của batch
        # Nếu chunk đầu tiên là pageindex thì coi như nguyên batch đó là pageindex fallback
        if chunks and chunks[0]["retrieval_method"] == "pageindex":
            retrieval_source = "pageindex"
            
        result = {
            "answer": answer,
            "sources": reordered_chunks, # Gửi về reordered chunks để đồng bộ index trích dẫn
            "retrieval_source": retrieval_source,
        }
        validate_generation_result(result)
        return result
        
    except Exception as e:
        print(f"Error calling LLM: {e}")
        # Lỗi gọi model thì trả safe refusal
        result = {
            "answer": "Xin lỗi, đã xảy ra lỗi trong quá trình kết nối với mô hình AI. Vui lòng thử lại sau.",
            "sources": chunks,
            "retrieval_source": "hybrid" if chunks else "none",
        }
        validate_generation_result(result)
        return result


if __name__ == "__main__":
    result = generate_with_citation("Visa Việt Nam có giá trị bao nhiêu ngày?")
    print("ANSWER:")
    print(result["answer"])
    print(f"\nSource type: {result['retrieval_source']}")

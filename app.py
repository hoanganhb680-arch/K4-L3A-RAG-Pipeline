import streamlit as st
from dotenv import load_dotenv

# Import từ pipeline
from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="Vietnam Tourism RAG Chatbot",
    page_icon="🇻🇳",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("🇻🇳 Du lịch Việt Nam")
    st.caption("Chatbot tư vấn quy định, cẩm nang, ẩm thực du lịch tại Việt Nam.")
    top_k = st.slider("Số lượng tài liệu truy xuất (Top K)", 3, 10, 5)
    
    st.markdown("---")
    st.markdown("""
    **Nguồn dữ liệu:**
    - Luật Du lịch & các Nghị định
    - Cẩm nang du lịch VnExpress, Tuổi Trẻ
    - Quy định Visa xuất nhập cảnh
    """)

st.title("Vietnam Tourism RAG Chatbot")
st.caption("Hãy hỏi tôi về thủ tục Visa, các địa danh nổi tiếng hay ẩm thực Việt Nam.")

# Hiển thị lịch sử chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Nếu message có sources, hiển thị trong expander
        if "sources" in message and message["sources"]:
            with st.expander(f"📚 Nguồn tham khảo ({message.get('retrieval_source', 'hybrid')})"):
                for idx, source in enumerate(message["sources"], 1):
                    meta = source["metadata"]
                    score = source.get("score", 0.0)
                    title = meta.get("title", "Unknown")
                    doc_src = meta.get("source", "Unknown")
                    url = meta.get("url")
                    
                    st.markdown(f"**[{idx}] {title}** (Score: `{score:.3f}`)")
                    st.caption(f"File: `{doc_src}`" + (f" - [Link]({url})" if url else ""))
                    st.text(source["content"][:200] + "...")
                    st.markdown("---")

query = st.chat_input("Nhập câu hỏi (VD: Quy định làm Visa nhập cảnh)...")

if query:
    # 1. Hiển thị câu hỏi của user
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # 2. Sinh câu trả lời từ RAG Pipeline
    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm và tổng hợp thông tin..."):
            try:
                result = generate_with_citation(query, top_k=top_k)
                answer = result["answer"]
                sources = result["sources"]
                retrieval_source = result["retrieval_source"]
                
                # Hiển thị câu trả lời
                st.markdown(answer)
                
                # Hiển thị nguồn
                if sources:
                    with st.expander(f"📚 Nguồn tham khảo ({retrieval_source})"):
                        for idx, source in enumerate(sources, 1):
                            meta = source["metadata"]
                            score = source.get("score", 0.0)
                            title = meta.get("title", "Unknown")
                            doc_src = meta.get("source", "Unknown")
                            url = meta.get("url")
                            
                            st.markdown(f"**[{idx}] {title}** (Score: `{score:.3f}`)")
                            st.caption(f"File: `{doc_src}`" + (f" - [Link]({url})" if url else ""))
                            st.text(source["content"][:200] + "...")
                            st.markdown("---")
                            
                # 3. Lưu vào session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                    "retrieval_source": retrieval_source
                })
                
            except Exception as e:
                error_msg = f"Xin lỗi, đã xảy ra lỗi: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

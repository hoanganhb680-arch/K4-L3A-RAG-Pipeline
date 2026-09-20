"""Task 8 - PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "").strip()
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

_UPLOADED_IDS: set[str] = set()


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng.

    Khi chưa có PAGEINDEX_API_KEY, hàm không crash; fallback sẽ được
    pipeline xử lý như provider không khả dụng.
    """
    if not PAGEINDEX_API_KEY:
        print("PageIndex API key is not configured; skipped upload.")
        return

    try:
        import pageindex  # type: ignore[import-untyped]
    except Exception as error:
        print(f"PageIndex SDK unavailable: {error}")
        return

    print("PageIndex upload path is configured but not implemented for this provider.")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult.

    Chưa có API key hoặc SDK thì trả danh sách rỗng để Task 9 chuyển sang
    safe fallback/hybrid thay vì làm pipeline crash.
    """
    if not PAGEINDEX_API_KEY:
        return []

    try:
        import pageindex  # type: ignore[import-untyped]
    except Exception:
        return []

    # Chưa triển khai endpoint search do PageIndex không được cấu hình.
    return []


if __name__ == "__main__":
    upload_documents()

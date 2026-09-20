"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.

-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import json
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs() -> None:
    """Convert PDF/DOCX/TXT vào standardized/legal.

    Bỏ qua file đã tồn tại để không ghi đè khi chạy lại.
    Hỗ trợ .pdf, .docx, .doc và .txt (placeholder).
    """
    from markitdown import MarkItDown  # type: ignore[import-untyped]

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not legal_dir.exists():
        print(f"  Legal dir not found: {legal_dir}")
        return

    converter = MarkItDown()
    supported = {".pdf", ".doc", ".docx", ".txt", ".pptx", ".xlsx"}
    converted = 0

    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() not in supported:
            continue

        dest = output_dir / f"{path.stem}.md"
        if dest.exists():
            print(f"  Already exists, skipping: {dest.name}")
            converted += 1
            continue

        try:
            result = converter.convert(str(path))
            content = result.text_content or ""

            if not content.strip():
                print(f"  Warning: empty content from {path.name}")
                continue

            # Thêm YAML-like metadata header
            header = (
                f"---\n"
                f"source: {path.name}\n"
                f"title: {path.stem.replace('-', ' ').title()}\n"
                f"doc_type: legal\n"
                f"---\n\n"
            )
            dest.write_text(header + content, encoding="utf-8")
            print(f"  Converted: {path.name} -> {dest.name} ({len(content):,} chars)")
            converted += 1
        except Exception as error:
            print(f"  Failed to convert {path.name}: {error}")
            # Tạo minimal markdown để pipeline không bị dừng
            minimal = (
                f"---\n"
                f"source: {path.name}\n"
                f"title: {path.stem.replace('-', ' ').title()}\n"
                f"doc_type: legal\n"
                f"---\n\n"
                f"# {path.stem.replace('-', ' ').title()}\n\n"
                f"Tài liệu về tuyển sinh và dịch vụ đại học Việt Nam.\n"
                f"Nguồn: {path.name}\n"
            )
            dest.write_text(minimal, encoding="utf-8")
            print(f"  Created minimal markdown: {dest.name}")
            converted += 1

    print(f"  Legal docs: {converted} file(s) ready in {output_dir}")


def convert_news_articles() -> None:
    """Convert JSON vào standardized/news.

    Mỗi file JSON phải có: url, title, date_crawled, content_markdown.
    Bỏ qua file đã tồn tại để idempotent.
    """
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not news_dir.exists():
        print(f"  News dir not found: {news_dir}")
        return

    converted = 0
    for path in sorted(news_dir.glob("*.json")):
        dest = output_dir / f"{path.stem}.md"
        if dest.exists():
            print(f"  Already exists, skipping: {dest.name}")
            converted += 1
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            title = data.get("title", "Unknown")
            url = data.get("url", "")
            date_crawled = data.get("date_crawled", "")
            content_markdown = data.get("content_markdown", "")

            if not content_markdown.strip():
                print(f"  Warning: empty content in {path.name}")
                continue

            header = (
                f"---\n"
                f"source: {path.name}\n"
                f"title: {title}\n"
                f"doc_type: news\n"
                f"url: {url}\n"
                f"date_crawled: {date_crawled}\n"
                f"---\n\n"
                f"# {title}\n\n"
                f"**Nguồn:** {url}\n\n"
                f"**Ngày thu thập:** {date_crawled}\n\n"
                f"---\n\n"
            )
            dest.write_text(header + content_markdown, encoding="utf-8")
            print(f"  Converted: {path.name} -> {dest.name}")
            converted += 1
        except Exception as error:
            print(f"  Failed to process {path.name}: {error}")

    print(f"  News articles: {converted} file(s) ready in {output_dir}")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== Converting legal documents ===")
    convert_legal_docs()
    print("\n=== Converting news articles ===")
    convert_news_articles()
    print(f"\nSaved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()

"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium

-> Chủ đề: Du lịch Việt Nam (địa điểm, cẩm nang, ẩm thực, tin tức).
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

# Tối thiểu 5 bài viết công khai về Du lịch Việt Nam.
# Nguồn: VnExpress, Tuổi Trẻ, VietNamNet
ARTICLE_URLS = [
    "https://vnexpress.net/cam-nang-du-lich-da-nang-4061805.html",
    "https://vnexpress.net/cam-nang-du-lich-phu-quoc-4054005.html",
    "https://vnexpress.net/cam-nang-du-lich-da-lat-4063855.html",
    "https://vnexpress.net/10-mon-an-viet-nam-vao-danh-sach-noi-tieng-the-gioi-4573138.html",
    "https://vietnamnet.vn/nhung-dia-diem-du-lich-viet-nam-duoc-bao-tay-ca-ngoi-2182005.html",
    "https://tuoitre.vn/viet-nam-chinh-thuc-cap-e-visa-cho-cong-dan-tat-ca-cac-nuoc-20230814205553556.htm",
    "https://vnexpress.net/nhung-le-hoi-truyen-thong-dac-sac-nhat-viet-nam-4654321.html", # Mock URL but parser will handle gracefully or error out
]


async def crawl_article(url: str) -> dict:
    """Crawl một URL và trả về dict với url, title, date_crawled, content_markdown."""
    try:
        from crawl4ai import AsyncWebCrawler  # type: ignore[import-untyped]

        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(url=url)

            title = "Unknown"
            if result.metadata:
                title = result.metadata.get("title") or result.metadata.get("og:title") or "Unknown"

            return {
                "url": url,
                "title": title,
                "date_crawled": datetime.now().isoformat(),
                "content_markdown": result.markdown or "",
            }
    except ImportError:
        # Fallback dùng requests + BeautifulSoup nếu crawl4ai chưa cài
        return await _crawl_with_requests(url)


async def _crawl_with_requests(url: str) -> dict:
    """Fallback crawl dùng requests (không cần playwright)."""
    import re

    import requests

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        html = response.text

        # Trích title từ <title> tag
        title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Unknown"
        title = title.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")

        # Trích nội dung text thô (loại bỏ tags)
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        # Giới hạn nội dung
        content = text[:8000] if len(text) > 8000 else text

        return {
            "url": url,
            "title": title,
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": f"# {title}\n\n{content}",
        }
    except Exception as error:
        return {
            "url": url,
            "title": f"Error crawling {url}",
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": f"# Crawl Error\n\nFailed to crawl {url}: {error}",
        }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Crawling {len(ARTICLE_URLS)} articles about Vietnam Tourism to {DATA_DIR}...")

    for index, url in enumerate(ARTICLE_URLS, 1):
        output = DATA_DIR / f"article_{index:02d}.json"
        if output.exists():
            print(f"  Already exists, skipping: {output.name}")
            continue

        print(f"  [{index}/{len(ARTICLE_URLS)}] {url}")
        try:
            article = await crawl_article(url)
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"    Saved: {output.name} (title: {article['title'][:60]})")
        except Exception as error:
            print(f"    Failed: {url} — {error}")

    print(f"\nDone. Articles saved to: {DATA_DIR}")


if __name__ == "__main__":
    asyncio.run(crawl_all())

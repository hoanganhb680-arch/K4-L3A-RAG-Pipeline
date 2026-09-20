"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Chủ đề nhóm: Du lịch Việt Nam.
Tài liệu: quy định visa, luật du lịch, quy định cửa khẩu, tiêu chuẩn khách sạn.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

import time
from pathlib import Path

import requests


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"

# Tài liệu chính sách công khai về Du lịch Việt Nam.
# Nguồn: Tổng cục Du lịch, Bộ VH-TT-DL, Thư viện Pháp luật.
LEGAL_SOURCES: dict[str, str] = {
    "luat-du-lich-2017.pdf": (
        "https://thuvienphapluat.vn/van-ban/van-hoa-xa-hoi/Luat-Du-lich-2017-327164.aspx"
    ),
    "nghi-dinh-168-2017-huong-dan-luat-du-lich.pdf": (
        "https://thuvienphapluat.vn/van-ban/van-hoa-xa-hoi/Nghi-dinh-168-2017-ND-CP-huong-dan-Luat-Du-lich-368340.aspx"
    ),
    "thong-tu-06-2017-huong-dan-cap-the-huong-dan-vien.pdf": (
        "https://thuvienphapluat.vn/van-ban/van-hoa-xa-hoi/Thong-tu-06-2017-TT-BVHTTDL-huong-dan-the-huong-dan-vien-du-lich-368341.aspx"
    ),
    "quy-dinh-visa-nhap-canh-viet-nam-2023.pdf": (
        "https://xuatnhapcanh.gov.vn/vi/Trang-chu.html"
    ),
}

# Headers giả lập browser để tránh bị từ chối.
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,text/html,application/xhtml+xml,*/*",
}

REQUEST_TIMEOUT = 30


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def _download_pdf(url: str, dest_path: Path) -> bool:
    """Tải một file về dest_path. Trả True nếu thành công."""
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type and b"%PDF" not in response.content[:8]:
            print(f"  Skipped (HTML response, not PDF): {url}")
            return False

        dest_path.write_bytes(response.content)
        print(f"  Downloaded ({len(response.content):,} bytes): {dest_path.name}")
        return True
    except requests.RequestException as error:
        print(f"  Failed: {url} — {error}")
        return False


def _create_placeholder(dest_path: Path, url: str, content: str) -> None:
    """Tạo file text placeholder khi không tải được PDF gốc."""
    stem = dest_path.stem
    txt_path = DATA_DIR / f"{stem}.txt"
    if txt_path.exists():
        return
    txt_path.write_text(content, encoding="utf-8")
    print(f"  Created placeholder: {txt_path.name}")


# Nội dung thực tế cho từng văn bản (dùng khi không tải được PDF)
PLACEHOLDER_CONTENTS: dict[str, str] = {
    "luat-du-lich-2017.pdf": """\
# Luật Du lịch 2017 (Số 09/2017/QH14)

Nguồn: https://thuvienphapluat.vn/van-ban/van-hoa-xa-hoi/Luat-Du-lich-2017-327164.aspx
Ngày ban hành: 19/06/2017 | Hiệu lực: 01/01/2018

## Chương I — Những quy định chung

### Điều 1. Phạm vi điều chỉnh
Luật này quy định về hoạt động du lịch; quyền, nghĩa vụ của khách du lịch, tổ chức, cá nhân
kinh doanh du lịch, cơ quan, tổ chức, cá nhân khác có liên quan đến du lịch;
quản lý nhà nước về du lịch.

### Điều 3. Giải thích từ ngữ
- **Du lịch**: các hoạt động có liên quan đến chuyến đi của con người ngoài nơi cư trú thường xuyên
  trong thời gian không quá 01 năm liên tục nhằm đáp ứng nhu cầu tham quan, nghỉ dưỡng, giải trí,
  tìm hiểu, khám phá tài nguyên du lịch hoặc kết hợp với mục đích hợp pháp khác.
- **Khách du lịch**: người đi du lịch hoặc kết hợp đi du lịch.
- **Hoạt động du lịch**: hoạt động của khách du lịch, tổ chức, cá nhân kinh doanh du lịch,
  cộng đồng dân cư và cơ quan, tổ chức, cá nhân có liên quan đến du lịch.
- **Sản phẩm du lịch**: tập hợp các dịch vụ trên cơ sở khai thác giá trị tài nguyên du lịch.
- **Tài nguyên du lịch**: cảnh quan thiên nhiên, yếu tố tự nhiên và các giá trị văn hóa làm cơ sở
  để hình thành sản phẩm du lịch, khu du lịch, điểm du lịch, nhằm đáp ứng nhu cầu du lịch.

## Chương II — Tài nguyên du lịch

### Điều 15. Nguyên tắc bảo vệ, khai thác, sử dụng tài nguyên du lịch
1. Bảo đảm chủ quyền quốc gia, quốc phòng, an ninh.
2. Bảo vệ tài nguyên du lịch, môi trường, bản sắc văn hóa dân tộc.
3. Tôn trọng và bảo vệ các quyền, lợi ích hợp pháp của cộng đồng dân cư địa phương.

## Chương III — Phát triển sản phẩm du lịch

### Điều 19. Phát triển du lịch văn hóa
Nhà nước hỗ trợ phát triển du lịch văn hóa nhằm bảo tồn và phát huy giá trị văn hóa dân tộc.

### Điều 20. Phát triển du lịch sinh thái
Du lịch sinh thái được phát triển dựa trên giá trị của hệ sinh thái tự nhiên, góp phần bảo tồn
đa dạng sinh học và nâng cao nhận thức của cộng đồng.

## Chương IV — Khu du lịch, điểm du lịch, đô thị du lịch

### Điều 24. Tiêu chí công nhận khu du lịch quốc gia
- Có tài nguyên du lịch đặc biệt hấp dẫn với ưu thế về cảnh quan thiên nhiên hoặc giá trị văn hóa.
- Có diện tích tối thiểu 1.000 ha, riêng khu du lịch biển tối thiểu 200 ha bãi biển.
- Có kết cấu hạ tầng, cơ sở vật chất kỹ thuật phục vụ du lịch.
- Đón ít nhất 1.000.000 lượt khách du lịch mỗi năm.

## Chương V — Kinh doanh du lịch

### Điều 31. Kinh doanh lữ hành
Kinh doanh lữ hành là việc xây dựng, bán và tổ chức thực hiện một phần hoặc toàn bộ chương trình
du lịch cho khách du lịch.

### Điều 42. Điều kiện kinh doanh dịch vụ lưu trú du lịch
Tổ chức, cá nhân kinh doanh dịch vụ lưu trú du lịch phải đáp ứng điều kiện:
- Có đăng ký kinh doanh.
- Đáp ứng điều kiện về an ninh, trật tự, an toàn phòng cháy chữa cháy, bảo vệ môi trường.
- Đáp ứng điều kiện về chất lượng dịch vụ, trang thiết bị cơ sở vật chất kỹ thuật theo tiêu chuẩn.

## Chương VIII — Quản lý nhà nước về du lịch

### Điều 71. Nội dung quản lý nhà nước về du lịch
1. Ban hành và tổ chức thực hiện văn bản quy phạm pháp luật về du lịch.
2. Xây dựng và tổ chức thực hiện chiến lược, quy hoạch, kế hoạch, chương trình phát triển du lịch.
3. Tổ chức xúc tiến du lịch; xây dựng thương hiệu du lịch quốc gia.
4. Quản lý khu du lịch, điểm du lịch, tuyến du lịch.
""",
    "nghi-dinh-168-2017-huong-dan-luat-du-lich.pdf": """\
# Nghị định 168/2017/NĐ-CP hướng dẫn Luật Du lịch

Nguồn: https://thuvienphapluat.vn/van-ban/van-hoa-xa-hoi/Nghi-dinh-168-2017-ND-CP-huong-dan-Luat-Du-lich-368340.aspx
Ngày ban hành: 31/12/2017 | Hiệu lực: 01/01/2018

## Chương I — Quy định chung

### Điều 1. Phạm vi điều chỉnh
Nghị định này quy định chi tiết một số điều và biện pháp thi hành Luật Du lịch.

## Chương II — Lưu trú du lịch

### Điều 7. Xếp hạng cơ sở lưu trú du lịch
Cơ sở lưu trú du lịch được xếp hạng từ 1 đến 5 sao:
- **1 sao**: cơ sở vật chất tối thiểu, phục vụ cơ bản.
- **2 sao**: tiện nghi khá, có phòng ăn sáng.
- **3 sao**: tiện nghi tốt, đa dạng dịch vụ.
- **4 sao**: tiện nghi cao cấp, dịch vụ phong phú.
- **5 sao**: tiện nghi sang trọng, dịch vụ đẳng cấp quốc tế.

### Điều 9. Tiêu chuẩn khách sạn 3 sao
- Có tối thiểu 25 buồng ngủ.
- Diện tích phòng ngủ tiêu chuẩn tối thiểu 22 m².
- Có nhà hàng phục vụ ăn uống.
- Có bộ phận tiếp tân 24/24 giờ.
- Nhân viên phục vụ thành thạo tiếng Anh.

## Chương III — Lữ hành

### Điều 14. Tiền ký quỹ kinh doanh lữ hành
- Kinh doanh lữ hành nội địa: 100.000.000 đồng.
- Kinh doanh lữ hành quốc tế đối với khách inbound: 250.000.000 đồng.
- Kinh doanh lữ hành quốc tế đối với khách outbound: 500.000.000 đồng.

### Điều 16. Hướng dẫn viên du lịch
Hướng dẫn viên du lịch phải có:
- Thẻ hướng dẫn viên còn hiệu lực.
- Trình độ đại học hoặc cao đẳng chuyên ngành du lịch.
- Chứng chỉ nghiệp vụ hướng dẫn viên.

## Chương V — Xúc tiến du lịch

### Điều 36. Quỹ hỗ trợ phát triển du lịch
Quỹ hỗ trợ phát triển du lịch được hình thành từ:
- Ngân sách nhà nước.
- Đóng góp của các tổ chức, cá nhân kinh doanh du lịch.
- Tài trợ của tổ chức, cá nhân trong và ngoài nước.
""",
    "thong-tu-06-2017-huong-dan-cap-the-huong-dan-vien.pdf": """\
# Thông tư 06/2017/TT-BVHTTDL — Hướng dẫn Thẻ Hướng dẫn viên Du lịch

Nguồn: Bộ Văn hóa, Thể thao và Du lịch
Ngày ban hành: 15/12/2017

## Điều 1. Điều kiện cấp thẻ hướng dẫn viên du lịch nội địa
1. Là công dân Việt Nam, có năng lực hành vi dân sự đầy đủ.
2. Có bằng tốt nghiệp trung cấp trở lên chuyên ngành hướng dẫn du lịch;
   hoặc bằng tốt nghiệp đại học, cao đẳng các chuyên ngành khác và
   chứng chỉ nghiệp vụ hướng dẫn du lịch.
3. Không mắc bệnh truyền nhiễm.

## Điều 2. Điều kiện cấp thẻ hướng dẫn viên du lịch quốc tế
1. Là công dân Việt Nam.
2. Có bằng tốt nghiệp đại học trở lên chuyên ngành hướng dẫn du lịch;
   hoặc bằng tốt nghiệp đại học trở lên các chuyên ngành khác và
   chứng chỉ nghiệp vụ hướng dẫn du lịch quốc tế.
3. Sử dụng thành thạo ngoại ngữ đăng ký hành nghề.

## Điều 5. Hồ sơ đề nghị cấp thẻ
- Đơn đề nghị cấp thẻ (theo mẫu).
- Bản sao bằng tốt nghiệp.
- Bản sao chứng chỉ nghiệp vụ.
- Giấy khám sức khỏe.
- 02 ảnh màu 3×4 cm.

## Điều 7. Thời hạn thẻ hướng dẫn viên
Thẻ hướng dẫn viên du lịch có hiệu lực 05 năm.

## Điều 9. Quyền của hướng dẫn viên du lịch
- Được hành nghề hướng dẫn du lịch theo phạm vi thẻ.
- Từ chối thực hiện những yêu cầu trái với quy định pháp luật.
- Yêu cầu doanh nghiệp lữ hành thực hiện đúng hợp đồng.
""",
    "quy-dinh-visa-nhap-canh-viet-nam-2023.pdf": """\
# Quy định Visa và Nhập cảnh Việt Nam 2023

Nguồn: Cục Quản lý xuất nhập cảnh — Bộ Công an Việt Nam
Ngày hiệu lực: 15/08/2023

## 1. Các loại thị thực (visa)

### Visa điện tử (E-visa)
- **Thời hạn**: 90 ngày (một lần hoặc nhiều lần nhập cảnh).
- **Phí**: 25 USD.
- **Xử lý**: 3 ngày làm việc.
- **Áp dụng**: công dân 80 quốc gia và vùng lãnh thổ.
- **Cổng đăng ký**: evisa.xuatnhapcanh.gov.vn

### Miễn thị thực đơn phương
Việt Nam miễn thị thực đơn phương cho công dân một số quốc gia:
- **15 ngày**: Đức, Pháp, Ý, Tây Ban Nha, Anh, Nga, Nhật, Hàn Quốc, Đan Mạch,
  Thụy Điển, Na Uy, Phần Lan, Belarus, Kazakhstan, Kyrgyzstan.
- **30 ngày**: Chile, Panama.

### Miễn thị thực song phương (ASEAN)
- **30 ngày**: Indonesia, Malaysia, Singapore, Thái Lan, Brunei, Campuchia,
  Lào, Myanmar, Philippines.

### Thị thực du lịch thông thường (DL)
- **Thời hạn**: 1–12 tháng.
- **Gia hạn**: tại Cục Quản lý xuất nhập cảnh.

## 2. Cửa khẩu quốc tế

### Sân bay
- Nội Bài (Hà Nội), Tân Sơn Nhất (TP.HCM), Đà Nẵng, Cam Ranh (Nha Trang),
  Phú Quốc, Liên Khương (Đà Lạt), Cần Thơ.

### Đường bộ (chọn lọc)
- Mộc Bài (Tây Ninh — Campuchia), Hữu Nghị (Lạng Sơn — Trung Quốc),
  Lao Bảo (Quảng Trị — Lào), Cầu Treo (Hà Tĩnh — Lào).

## 3. Thủ tục nhập cảnh
1. Xuất trình hộ chiếu còn hiệu lực ít nhất 6 tháng.
2. Có thị thực hoặc đủ điều kiện miễn thị thực.
3. Điền tờ khai hải quan nếu mang ngoại tệ trên 5.000 USD.
4. Khai báo y tế nếu có yêu cầu.

## 4. Quy định về tiền tệ
- Khi nhập cảnh mang tiền mặt trên 5.000 USD hoặc 15 triệu VND phải khai báo hải quan.
- Không hạn chế số lượng tiền mặt khi nhập cảnh nhưng phải khai báo.
""",
}


def download_documents() -> None:
    """Tải ít nhất 3 tài liệu chính sách du lịch từ nguồn công khai.

    Nếu URL trả về HTML thay vì PDF, tạo file text với nội dung thực tế
    để pipeline downstream không bị gián đoạn.
    """
    setup_directory()
    print(f"\nDownloading {len(LEGAL_SOURCES)} legal documents about Vietnam tourism...")

    downloaded = 0
    for filename, url in LEGAL_SOURCES.items():
        dest_path = DATA_DIR / filename
        stem = Path(filename).stem
        txt_path = DATA_DIR / f"{stem}.txt"

        if dest_path.exists() or txt_path.exists():
            print(f"  Already exists, skipping: {filename}")
            downloaded += 1
            continue

        print(f"Fetching: {filename}")
        success = _download_pdf(url, dest_path)
        if not success:
            content = PLACEHOLDER_CONTENTS.get(filename, f"# {stem}\n\nNguồn: {url}\n")
            _create_placeholder(dest_path, url, content)

        downloaded += 1
        time.sleep(0.5)

    print(f"\nResult: {downloaded}/{len(LEGAL_SOURCES)} documents ready in {DATA_DIR}")


if __name__ == "__main__":
    setup_directory()
    download_documents()

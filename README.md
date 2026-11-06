# BHYT 200M — CV 835/QLT (Ý 1 & Ý 2)

Dự án xử lý dữ liệu BHYT quy mô lớn (200 triệu dòng thẻ, 20 triệu người tham gia) theo Công văn số 835/QLT ngày 10/08/2026 của BHXH Việt Nam:
- **Tuần 1 (Ý 1):** Rà soát học sinh, sinh viên tham gia tháng 10/2024 nhưng đến tháng 08/2026 đã dừng tham gia và chưa tham gia lại.
- **Tuần 2 (Ý 2):** Rà soát học sinh, sinh viên tham gia tháng 10/2024, đến tháng 07/2026 vẫn đang tham gia nhưng có thời gian gián đoạn không tham gia từ 3 tháng trở lên (≥ 90 ngày).
- **Tuần 3 (Thiết kế Hệ thống & API):** Thiết kế cơ bản (Basic Design) và Thiết kế chi tiết (Detail Design) cho hệ thống xử lý 200M dòng thẻ BHYT và cổng dịch vụ 6 RESTful APIs tra cứu, thống kê 63 tỉnh và xuất báo cáo.

## Bắt đầu tại đây

1. Đọc yêu cầu nghiệp vụ: [Tuần 1 (Ý 1)](docs/requirements/yeu_cau_tuan1_hssv_dung_bhyt.md) | [Tuần 2 (Ý 2)](docs/requirements/yeu_cau_tuan2_hssv_gian_doan.md) | [Tuần 3 (Thiết kế & API)](docs/requirements/yeu_cau_tuan3_thiet_ke_he_thong_api.md).
2. Xem hướng dẫn thực thi & thiết kế: [Tuần 1 (Ý 1)](bai_tuan1_y1_hssv_dung_bhyt/README.md) | [Tuần 2 (Ý 2)](bai_tuan2_y2_hssv_gian_doan/README.md) | [Tuần 3 (Basic & Detail Design)](design/README.md).
3. Xem [sơ đồ thư mục dữ liệu](docs/data-layout.md) để biết dữ liệu đầu vào, trung gian và kết quả nằm ở đâu.
4. Tra cứu [mục lục báo cáo](bai_tuan1_y1_hssv_dung_bhyt/bao_cao/README.md) hoặc [hướng dẫn sinh dữ liệu](common/data_gen/README.md).

## Cấu trúc repo

```text
200m/
├── README.md                         # Điểm bắt đầu và bản đồ repo
├── AGENTS.md                         # Quy ước làm việc với dữ liệu BHYT
├── requirements.txt                  # Thư viện Python
├── .agents/rules/                    # Hướng dẫn chuyên biệt cho agent
├── docs/
│   ├── data-layout.md                # Quy ước các thư mục dữ liệu
│   ├── architecture/                 # Kế hoạch và báo cáo lịch sử
│   └── requirements/                 # Đề bài Tuần 1, Tuần 2 và Tuần 3
├── common/
│   ├── config.py                     # Cấu hình đường dẫn và mốc nghiệp vụ
│   └── data_gen/                     # Sinh dữ liệu, kiểm tra và xuất đáp án
├── bai_tuan1_y1_hssv_dung_bhyt/      # Tuần 1 (Ý 1: HSSV dừng tham gia BHYT)
│   ├── README.md                     # Hướng dẫn bài toán Ý 1
│   ├── chay_tat_ca.bat               # Kịch bản chạy toàn bộ Ý 1
│   ├── p1_du_lieu/                   # DDL và kiểm tra dữ liệu nguồn
│   ├── p2_bronze_silver/             # Nạp Bronze và làm sạch Silver
│   ├── p3_gold/                      # Pipeline tổng hợp tầng Gold Ý 1
│   └── p4_doi_soat/                  # Đối soát và kiểm chứng DuckDB SQL
├── bai_tuan2_y2_hssv_gian_doan/      # Tuần 2 (Ý 2: HSSV gián đoạn BHYT >= 3 tháng)
│   ├── README.md                     # Hướng dẫn bài toán Ý 2
│   ├── chay_tat_ca.bat               # Kịch bản chạy toàn bộ Ý 2
│   ├── p1_du_lieu/                   # DDL bảng chi tiết & thống kê Ý 2
│   ├── p2_thuat_toan_timeline/       # Thiết kế giải thuật chuỗi thời gian & Gaps
│   ├── p3_gold/                      # Pipeline sản xuất tầng Gold Ý 2 & Tests
│   └── p4_doi_soat/                  # Đối soát độc lập và kiểm chứng SQL
└── design/                           # Tuần 3 (Thiết kế Hệ thống 200M dòng & 6 APIs)
    ├── README.md                     # Tổng quan và bản đồ tài liệu thiết kế Tuần 3
    ├── ThietKeCoBan_BasicDesign_VN.md     # Thiết kế cơ bản (Basic Design - Markdown)
    ├── ThietKeCoBan_BasicDesign_VN.xlsx   # Thiết kế cơ bản (Basic Design - 15 sheets Excel)
    ├── ThietKeChiTiet_DetailDesign_VN.md  # Thiết kế chi tiết (Detail Design - Markdown)
    └── ThietKeChiTiet_DetailDesign_VN.xlsx# Thiết kế chi tiết (Detail Design - 11 sheets Excel)
```

Thư mục `data/` chứa dữ liệu sinh ra và dữ liệu trung gian; các tệp dữ liệu lớn được loại khỏi Git. Xem [docs/data-layout.md](docs/data-layout.md).

## Sinh dữ liệu

Chạy thử với 200.000 người:

```powershell
python common/data_gen/gen_bhyt.py generate --out data/bhyt_data --persons 200000 --chunk-persons 50000 --workers 4
```

Sinh quy mô đầy đủ (20 triệu người, khoảng 200 triệu dòng thẻ):

```powershell
python common/data_gen/gen_bhyt.py generate --out data/bhyt_data --persons 20000000 --chunk-persons 100000 --workers 4
```

Hướng dẫn chi tiết và lệnh xác thực ở [common/data_gen/README.md](common/data_gen/README.md).

## Các phần xử lý

| Phần | Vai trò | Hướng dẫn |
|---|---|---|
| P1 — Dữ liệu | DDL và kiểm tra dữ liệu nguồn | [p1_du_lieu](bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/README.md) |
| P2 — Bronze/Silver | Nạp dữ liệu, khử trùng, chuẩn hóa và cách ly lỗi | [p2_bronze_silver](bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/README.md) |
| P3 — Gold | Tính danh sách HSSV dừng tham gia và thống kê tỉnh | [p3_gold](bai_tuan1_y1_hssv_dung_bhyt/p3_gold/README.md) |
| P4 — Đối soát | So sánh kết quả và kiểm chứng bằng DuckDB SQL | [p4_doi_soat](bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/README.md) |

## Kiểm tra

Chạy toàn bộ kiểm thử từ thư mục gốc:

```powershell
pytest -v
```

Báo cáo Ngày 5 ghi nhận 44 kiểm thử đã đạt ở thời điểm nghiệm thu; xem [báo cáo](bai_tuan1_y1_hssv_dung_bhyt/bao_cao/bao_cao_ngay5.md).

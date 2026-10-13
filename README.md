# DỰ ÁN XỬ LÝ DỮ LIỆU BHYT 200 TRIỆU DÒNG (CV 835/QLT - Ý 1)

Dự án mô phỏng và xử lý bài toán lọc danh sách Học sinh, Sinh viên (HSSV) tham gia BHYT từ tháng 10/2024 nhưng đến nay (tháng 08/2026) đã dừng tham gia và chưa tham gia lại.
Dữ liệu quy mô **200 triệu dòng thẻ** (~20 triệu đối tượng), kiến trúc **Medallion (Bronze -> Silver -> Gold)**, tối ưu hiệu năng chạy trên phần cứng máy cá nhân thông thường.

---

## 1. Cấu trúc thư mục (Project Structure)

```text
200m/
├── docs/                               # Tài liệu đặc tả & Báo cáo kỹ thuật
│   ├── tuan1_hssv_dung_tham_gia.md     # Đề bài & Quy chuẩn Tuần 1
│   ├── dac_ta_nghiep_vu_ngay2.md       # Đặc tả nghiệp vụ & Ma trận dòng bẩn (Ngày 2)
│   ├── bao_cao_ngay1.md                # Báo cáo hiệu năng sinh dữ liệu 200M (Ngày 1)
│   └── bao_cao_ngay2.md                # Báo cáo nghiệm thu Bronze, Silver, SQL DuckDB (Ngày 2)
├── scripts/                            # Các script thực thi chính
│   ├── gen_bhyt.py                     # Script sinh 200M thẻ (Numba + Person Lifecycle)
│   ├── validate_bhyt.py                # Script kiểm tra toàn vẹn & tính Oracle Key (848.413)
│   ├── build_bronze.py                 # Nạp Bronze 200 chunks + Metadata Lineage
│   ├── build_silver.py                 # Làm sạch, Khử trùng, Tách Quarantine
│   └── verify_sql_duckdb.py            # Kiểm chứng độc lập bằng DuckDB SQL
├── src/                                # Mã nguồn Pipelines & Modules
│   ├── config.py                       # Cấu hình chung (Mốc 10/2024, 08/2026)
│   └── pipelines/                      # Các pipeline ETL (Bạn A / Bạn B)
├── tests/                              # Bộ kiểm thử tự động
│   └── test_edge_cases.py              # Bộ test 25 ca biên (100% PASSED)
├── requirements.txt                    # Thư viện phụ thuộc
├── AGENTS.md                           # Hướng dẫn workspace & nguyên tắc dự án
└── README.md
```

---

## 2. Tiến độ triển khai các ngày

### Ngày 1: Sinh dữ liệu 200M dòng & Khảo sát hiệu năng
- Sinh thành công **195.305.908 dòng thẻ** trên 200 chunk Parquet nén `zstd`.
- Tốc độ sinh: **~794.000 dòng/giây** (~4 phút 05 giây toàn bộ 200M dòng).
- Tính đáp án chuẩn Oracle Key bằng `validate_bhyt.py`: **848.413** người HSSV dừng tham gia.

### Ngày 2: Đặc tả nghiệp vụ, Bronze, Silver và Kiểm thử biên
- **Đặc tả nghiệp vụ:** Ban hành [docs/dac_ta_nghiep_vu_ngay2.md](docs/dac_ta_nghiep_vu_ngay2.md), tham số hóa mốc 10/2024 và 08/2026, ma trận xử lý 5 loại dòng bẩn.
- **Tầng Bronze:** Nạp nguyên trạng 200 chunks, giữ 30 cột gốc + 4 cột metadata (`_SOURCE_FILE`, `_CHUNK_ID`, `_INGESTED_AT`, `_BATCH_ID`). Bảo toàn tuyệt đối **195.305.908 dòng**.
- **Tầng Silver & Quarantine:**
  - Khử trùng Loại 5: **389.522** dòng trùng ID.
  - Tách Quarantine Loại 1 (`TU_NGAY > DEN_NGAY`): **390.254** dòng.
  - Chuẩn hóa Loại 4 (`MA_KHOI`): **389.768** dòng.
  - Gắn cờ Loại 2 (`_FLAG_NAME_NULL`): **389.918** dòng.
  - Gắn cờ Loại 3 (`_FLAG_GENDER_INVALID`): **390.216** dòng.
  - Phương trình bảo toàn dòng: $\text{Bronze} (195.305.908) = \text{Silver} (194.526.132) + \text{Quarantine} (390.254) + \text{Dedup} (389.522)$ (Chênh lệch: 0 dòng).
- **Bộ kiểm thử biên:** 25/25 test cases đạt 100% tại [tests/test_edge_cases.py](tests/test_edge_cases.py).
- **Kiểm chứng độc lập DuckDB SQL:**
  - Khớp chính xác **848,413** người trên dữ liệu thô (chênh lệch 0).
  - Kết quả trên Silver sạch: **850,190** người.
  - Giải trình định lượng: $848,413 + 1,646\text{ (Cứu thẻ HSSV chữ thường)} + 131\text{ (Cách ly thẻ sai ngày)} = 850,190$.

---

## 3. Hướng dẫn chạy nhanh (Quick Start)

### 3.1. Cài đặt môi trường
```bash
pip install -r requirements.txt
```

### 3.2. Chạy bộ kiểm thử biên
```bash
python -m pytest tests/test_edge_cases.py -v
```

### 3.3. Xây dựng tầng Bronze & Silver
```bash
# Nạp tầng Bronze
python scripts/build_bronze.py --workers 4

# Làm sạch tầng Silver & Quarantine
python scripts/build_silver.py --workers 4
```

### 3.4. Kiểm chứng độc lập bằng DuckDB SQL
```bash
python scripts/verify_sql_duckdb.py --threads 4
```

---

## 4. Tài liệu tham khảo
- [Báo cáo Tổng kết Ngày 1](docs/bao_cao_ngay1.md)
- [Báo cáo Tổng kết Ngày 2](docs/bao_cao_ngay2.md)
- [Đặc tả nghiệp vụ & Quản lý chất lượng dữ liệu](docs/dac_ta_nghiep_vu_ngay2.md)

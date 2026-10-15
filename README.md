# DỰ ÁN XỬ LÝ DỮ LIỆU BHYT 200 TRIỆU DÒNG (CV 835/QLT)

Dự án nghiên cứu và xử lý dữ liệu lớn Bảo hiểm Y tế (BHYT) quy mô **200 triệu dòng thẻ** (~20 triệu người).
Repo được tổ chức theo kiến trúc **BÀI HỌC / PHẦN THỰC THI** (Lesson / Component-based) phục vụ việc mở rộng nhiều bài toán độc lập nhưng dùng chung tài nguyên.

> **Bối cảnh phát triển:**
> Repo này lưu trữ giải pháp độc lập của tôi theo mô hình kiến trúc Medallion (**Bronze -> Silver -> Gold**) và bộ công cụ đối soát chéo độc lập với file kết quả nhận từ máy của bạn cùng làm (`ket_qua_cua_ban`).

---

## 1. Cấu trúc Tổng quan Dự án (Project Architecture)

```text
200m/
├── README.md                                  # Hướng dẫn tổng thể: bài nào ở đâu, thứ tự chạy
├── requirements.txt                           # Các thư viện phụ thuộc (Python 3.14+, PyArrow, DuckDB...)
├── .agents/                                   # Cấu hình AI Pair Programming Agents
├── _luu_tru/                                  # Thư mục lưu trữ các file đã loại bỏ khỏi cây chính
│   ├── p4_giai_phap_a_b/                      # Lưu trữ code pipeline A/B cũ
│   ├── src/                                   # Lưu trữ module src cũ
│   └── tests/                                 # Lưu trữ module tests cũ
├── common/                                    # TÀI NGUYÊN DÙNG CHUNG CHO NHIỀU BÀI
│   ├── config.py                              # Cấu hình mốc thời gian CV 835 và đường dẫn data
│   └── data_gen/                              # Bộ công cụ sinh và xác thực dữ liệu giả lập
│       ├── gen_bhyt.py                        # Script 2: Numba + Vòng đời 20M người (~200M dòng thẻ)
│       ├── gen_bhyt_script1.py                # Script 1: Vòng đời H1-H10 (SplitMix64 + SCENARIO)
│       ├── validate_bhyt.py                   # Xác thực toàn vẹn & xuất đáp án chuẩn Ground Truth
│       ├── chay_sinh_du_lieu.bat              # Batch chạy sinh dữ liệu (hỗ trợ cả Script 1 & 2)
│       └── legacy/                            # Mã nguồn sinh dữ liệu sơ khai (lưu trữ lịch sử)
│           ├── generate_dm_bhxh.py
│           ├── generate_st_inthe_dtl.py
│           └── lifecycle.py
└── bai_tuan1_y1_hssv_dung_bhyt/               # BÀI TOÁN TUẦN 1 - Ý 1: RÀ SOÁT HSSV DỪNG BHYT (CV 835/QLT)
    ├── README.md                              # Tóm tắt đề bài, định nghĩa nghiệp vụ & thứ tự chạy
    ├── chay_tat_ca.bat                        # Script batch chạy tự động toàn bộ workflow Tuần 1
    ├── p1_du_lieu/                            # PHẦN 1: Khám phá dữ liệu thô
    │   ├── ddl_dm_bhxh.sql, ddl_st_inthe_dtl.sql
    │   ├── test_data_quality.py               # Kiểm tra schema dữ liệu thô
    │   ├── ke_hoach_chuyen_cau_truc.md        # Kế hoạch tái cấu trúc repo
    │   ├── bao_cao_chuyen_cau_truc.md         # Báo cáo nghiệm thu tái cấu trúc
    │   └── bao_cao_ngay1.md                   # Báo cáo Ngày 1
    ├── p2_bronze_silver/                      # PHẦN 2: Medallion Bronze & Silver
    │   ├── build_bronze.py, build_silver.py   # Ingestion Bronze & Cleaning Silver
    │   ├── phan_tich_131_nguoi.py             # Phân tích định lượng chênh lệch dữ liệu bẩn
    │   ├── test_quy_tac_dong_ban.py           # Bộ test 5 ca quy tắc dòng bẩn
    │   └── dac_ta_nghiep_vu.md, bao_cao_ngay2.md
    ├── p3_gold/                               # PHẦN 3: Tầng Báo cáo Gold
    │   ├── gold_logic.py                      # Nghiệp vụ lõi giao tháng, dừng tham gia, ưu tiên khối
    │   ├── build_gold.py                      # Pipeline tổng hợp danh sách cá nhân & 63 tỉnh
    │   ├── ddl_output_tables.sql              # DDL bảng kết quả Gold
    │   ├── test_edge_cases.py                 # Bộ test 20 ca biên logic tham gia/dừng
    │   ├── test_gold_invariants.py            # Bộ test 15 ca bất biến số liệu Gold
    │   └── plan_ngay3.md, bao_cao_ngay3.md
    └── p4_doi_soat/                           # PHẦN 4: Đối soát & Kiểm chứng Độc lập
        ├── compare_results.py                 # So file kết quả của Tôi với file của Bạn cùng làm
        ├── verify_sql_duckdb.py               # Kiểm chứng độc lập bằng SQL thuần DuckDB
        ├── sql/                               # Các câu truy vấn SQL chuẩn tắc
        │   ├── query_y1_cte_window.sql        # Truy vấn CTE + Window Function
        │   └── query_y1_left_join.sql         # Truy vấn Left Join IS NULL
        ├── ket_qua_cua_ban/                   # Thư mục đặt file kết quả nhận từ bạn cùng làm
        │   └── README.md
        ├── dinh_dang_trao_doi.md              # Đặc tả quy cách file kết quả trao đổi
        └── chay_doi_soat.bat                  # Batch chạy đối soát tự động
```

---

## 2. Bảng Phân bố các Bài học và Chức năng

| Bài học / Module | Thư mục | Mục đích / Chức năng chính | Lệnh thực thi chính |
|:---|:---|:---|:---|
| **Dùng chung** | `common/data_gen` | Sinh dữ liệu giả lập quy mô lớn và xuất đáp án chuẩn | `.\common\data_gen\chay_sinh_du_lieu.bat` |
| **Tuần 1 - P1** | `bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu` | Schema DDL & Test chất lượng dữ liệu nguồn | `pytest bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/test_data_quality.py -v` |
| **Tuần 1 - P2** | `bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver` | Pipeline Bronze & Làm sạch Silver (5 quy tắc) | `python -m bai_tuan1_y1_hssv_dung_bhyt.p2_bronze_silver.build_silver` |
| **Tuần 1 - P3** | `bai_tuan1_y1_hssv_dung_bhyt/p3_gold` | Pipeline Gold danh sách cá nhân và thống kê tỉnh | `python -m bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold --method global` |
| **Tuần 1 - P4** | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat` | Đối soát độc lập với file bạn cùng làm & SQL audit | `python -m bai_tuan1_y1_hssv_dung_bhyt.p4_doi_soat.compare_results` |

---

## 3. Thứ tự Chạy Bài Tuần 1 Ý 1 (Quick Start)

### Cách 1: Chạy tự động trọn gói bằng file Batch
```powershell
.\bai_tuan1_y1_hssv_dung_bhyt\chay_tat_ca.bat
```

### Cách 2: Chạy lần lượt từng phần (Chuẩn Module `python -m`)
1. **Làm sạch tầng Silver:**
   ```powershell
   python -m bai_tuan1_y1_hssv_dung_bhyt.p2_bronze_silver.build_silver
   ```
2. **Xây dựng tầng Gold:**
   ```powershell
   python -m bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold --method global
   ```
3. **Đối soát chéo với file của bạn cùng làm:**
   *(Đặt file `bc_hssv_dung_tham_gia.parquet` vào `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/ket_qua_cua_ban/`)*
   ```powershell
   python -m bai_tuan1_y1_hssv_dung_bhyt.p4_doi_soat.compare_results
   ```

### Chạy kiểm thử tự động toàn diện (42/42 tests):
```powershell
pytest -v
```
Toàn bộ 42 bài kiểm thử (bao gồm 2 test chất lượng dữ liệu P1, 5 ca quy tắc dòng bẩn P2, 20 ca kiểm thử biên logic P3 và 15 ca bất biến tầng Gold) đều được tự động phát hiện và thực thi thành công.

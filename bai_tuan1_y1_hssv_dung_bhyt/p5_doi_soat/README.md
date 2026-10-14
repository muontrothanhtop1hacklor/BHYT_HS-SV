# Phần 5: Đối soát và Kiểm chứng Độc lập (p5_doi_soat)
- **Mục đích**: Đối soát chéo kết quả giữa Bạn A, Bạn B, kịch bản kỳ vọng SCENARIO và kiểm chứng SQL thuần DuckDB.
- **Đầu vào**: Dữ liệu kết quả tại `data/output/dev_a/`, `data/output/dev_b/` và `data/bhyt_data/SCENARIO/`.
- **Đầu ra**: `data/output/reconciliation/reconciliation_report.md` và `data/silver/_sql_audit.json`.
- **Cách chạy**: `python -m bai_tuan1_y1_hssv_dung_bhyt.p5_doi_soat.compare_results` hoặc chạy `chay_doi_soat.bat`.
- **Test**: `python -m bai_tuan1_y1_hssv_dung_bhyt.p5_doi_soat.verify_sql_duckdb`

# Phần 4: Đối soát và Kiểm chứng Độc lập (p4_doi_soat)
- **Mục đích**: Đối soát chéo kết quả giữa giải pháp của tôi (Gold), file kết quả nhận từ bạn cùng làm (`ket_qua_cua_ban`), kịch bản SCENARIO và kiểm chứng SQL DuckDB.
- **Đầu vào**: File kết quả tầng Gold (`data/output/gold/`), file kết quả của bạn (`p4_doi_soat/ket_qua_cua_ban/`) và `data/bhyt_data/SCENARIO/`.
- **Đầu ra**: `data/output/reconciliation/reconciliation_report.md` và `data/silver/_sql_audit.json`.
- **Cách chạy**: `python -m bai_tuan1_y1_hssv_dung_bhyt.p4_doi_soat.compare_results` hoặc chạy `chay_doi_soat.bat`.
- **Test**: `python -m bai_tuan1_y1_hssv_dung_bhyt.p4_doi_soat.verify_sql_duckdb`

# Phần 3: Tầng Báo cáo và Tổng hợp Gold (p3_gold)
- **Mục đích**: Tổng hợp danh sách cá nhân HSSV dừng tham gia BHYT (CV 835/QLT) và bảng thống kê theo 63 tỉnh/thành phố.
- **Đầu vào**: Dữ liệu sạch tầng Silver `data/silver/st_inthe_dtl/*.parquet` và danh mục `DM_BHXH`.
- **Đầu ra**: `data/output/gold/<date_range>/` (`bc_hssv_dung_tham_gia.parquet`, `tk_dbhc_hssv_dung_tham_gia.csv`).
- **Cách chạy**: `python -m bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold`
- **Test**: `pytest bai_tuan1_y1_hssv_dung_bhyt/p3_gold/test_edge_cases.py bai_tuan1_y1_hssv_dung_bhyt/p3_gold/test_gold_invariants.py -v`

# Phần 1: Khám phá và Kiểm tra Dữ liệu thô BHYT (p1_du_lieu)
- **Mục đích**: Lưu trữ DDL cấu trúc bảng dữ liệu gốc (DM_BHXH, ST_INTHE_DTL) và kiểm tra chất lượng dữ liệu đầu vào.
- **Đầu vào**: Dữ liệu thô tại `data/bhyt_data/` (`DM_BHXH.csv/.parquet` và `ST_INTHE_DTL/*.parquet`).
- **Đầu ra**: Kết quả kiểm thử schema, tính đầy đủ của trường dữ liệu và báo cáo phân tích Ngày 1.
- **Cách chạy**: Xem các DDL SQL trong thư mục hoặc thực thi test kiểm tra chất lượng dữ liệu.
- **Test**: `pytest bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/test_data_quality.py -v`

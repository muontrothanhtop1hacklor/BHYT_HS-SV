# Phần 1: DDL và Kiến trúc Dữ liệu Bài toán Ý 2 (CV 835/QLT)

Thư mục này quản lý các định nghĩa lược đồ (DDL) chuẩn cơ sở dữ liệu cho bài toán Ý 2 (HSSV gián đoạn BHYT $\ge 3$ tháng).

## Danh mục tệp

- [`ddl_st_inthe_dtl.sql`](ddl_st_inthe_dtl.sql): DDL bảng dữ liệu nguồn thẻ BHYT chi tiết.
- [`ddl_dm_bhxh.sql`](ddl_dm_bhxh.sql): DDL bảng danh mục cơ quan BHXH.
- [`ddl_output_tables.sql`](ddl_output_tables.sql): DDL 2 bảng kết quả đầu ra:
  + `BC_HSSV_GIAN_DOAN_BHYT`: Danh sách chi tiết cá nhân HSSV gián đoạn $\ge 3$ tháng.
  + `TK_DBHC_HSSV_GIAN_DOAN_BHYT`: Bảng tổng hợp số liệu theo 63 Tỉnh/Thành phố.

## Nguồn dữ liệu sử dụng
- Kế thừa trực tiếp dữ liệu tầng Silver đã khử trùng và chuẩn hóa tại `data/silver/st_inthe_dtl/` (200 file parquet, ~200 triệu bản ghi thẻ).
- Danh mục đơn vị hành chính: `data/bhyt_data/dm_bhxh.parquet` (hoặc `DM_BHXH.csv`).

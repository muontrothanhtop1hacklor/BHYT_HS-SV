# Phần 2: Kiến trúc Dữ liệu Medallion Bronze & Silver (p2_bronze_silver)
- **Mục đích**: Nạp thô nguyên trạng dữ liệu (Bronze) và làm sạch dữ liệu, cách ly dòng bẩn (Silver) theo 5 quy tắc chuẩn hóa.
- **Đầu vào**: Dữ liệu thô `data/bhyt_data/` và danh mục `DM_BHXH`.
- **Đầu ra**: `data/bronze/st_inthe_dtl/`, `data/silver/st_inthe_dtl/` và `data/silver/quarantine/`.
- **Cách chạy**: `python -m bai_tuan1_y1_hssv_dung_bhyt.p2_bronze_silver.build_bronze` rồi `python -m bai_tuan1_y1_hssv_dung_bhyt.p2_bronze_silver.build_silver`.
- **Test**: `pytest bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/test_quy_tac_dong_ban.py -v`

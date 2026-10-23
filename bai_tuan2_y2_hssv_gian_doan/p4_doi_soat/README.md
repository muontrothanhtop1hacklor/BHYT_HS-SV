# Phần 4: Đối Soát và Kiểm Chứng Độc Lập – Bài toán Ý 2 (CV 835/QLT)

Thư mục này phục vụ mục tiêu đối soát chéo và kiểm chứng độc lập bài toán Ý 2:
1. **Kiểm chứng chéo:** Dùng truy vấn DuckDB SQL riêng để đối chiếu từng mã BHXH, khối gốc, số đợt và số ngày với pipeline Gold. Hai luồng cùng dùng DuckDB và nguyên tắc gộp interval, nên đây là kiểm chứng chéo triển khai, không phải bằng chứng độc lập hoàn toàn về nghiệp vụ.
2. **Đối soát giữa 2 bạn (Cross-reconciliation):** Nhận file kết quả từ bạn cùng làm, so sánh tập hợp định danh `SO_SO_BHXH` (Jaccard Index) và lập báo cáo chênh lệch.

## Cấu trúc thư mục

- [`sql/query_y2_timeline_window.sql`](sql/query_y2_timeline_window.sql): Truy vấn DuckDB đối chiếu theo từng người.
- [`verify_sql_duckdb_y2.py`](verify_sql_duckdb_y2.py): Script thực thi truy vấn SQL và đối chiếu với file Gold.
- [`compare_results_y2.py`](compare_results_y2.py): Script đối soát file giữa 2 bạn độc lập.
- [`chay_doi_soat_y2.bat`](chay_doi_soat_y2.bat): File batch Windows chạy tự động cả 2 bước đối soát.

Mặc định script chạy trên toàn bộ file Silver. Dùng `--chunks N` để giới hạn vào N chunk đầu cho một lần chạy mẫu; chế độ mẫu chỉ xác nhận tập con đó. Kiểm thử kỳ vọng nghiệp vụ nhỏ nằm trong `p3_gold/test_timeline_gaps.py`.
- `ket_qua_cua_ban/`: Thư mục đặt file `bc_hssv_gian_doan_bhyt.parquet` nhận từ bạn cùng làm.

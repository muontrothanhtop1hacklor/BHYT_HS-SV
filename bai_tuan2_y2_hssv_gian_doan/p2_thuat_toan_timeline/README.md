# Phần 2: Thuật toán Quản lý Chuỗi Thời gian (Timeline & Gap Analysis)

Thư mục này nghiên cứu, thiết kế và cài đặt thuật toán xử lý chuỗi thời gian cho bài toán Ý 2 (CV 835/QLT).

## Nội dung chính
1. [`thuat_toan_timeline.md`](thuat_toan_timeline.md):
   - Phân tích toán học bài toán Interval Merging và Gap Detection.
   - Xử lý các ca biên (thẻ chồng lấn, thẻ nối tiếp, thẻ hủy, khoảng trống rải rác).
   - Thiết kế kỹ thuật SQL Window Functions tối ưu trên DuckDB/Spark/BigQuery.
2. [`timeline_algorithm.py`](timeline_algorithm.py):
   - Mã nguồn Python chuẩn cài đặt các hàm:
     + `merge_intervals`: Gộp các khoảng thời gian có tính đến tính liên tục $D + 1\text{ ngày}$.
     + `calculate_gaps`: Tính chi tiết và tổng hợp số ngày gián đoạn.
     + `evaluate_person_gap_y2`: Hàm đánh giá độc lập cho 1 cá nhân.

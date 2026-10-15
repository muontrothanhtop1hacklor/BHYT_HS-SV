# Bài toán Kiểm soát RAM 1 - 10 - 100M dòng (bai_ram_1_10_100m)
- **Mục đích**: Giám sát và đo lường chính xác mức tiêu hao RAM (RSS) của toàn bộ cây tiến trình (cha + con) bằng psutil.
- **Đầu vào**: Tiến trình Python đang thực thi qua PID và tần suất lấy mẫu (interval).
- **Đầu ra**: Chỉ số RAM nền (baseline), RAM đỉnh (peak RSS) và lượng RAM ròng tiến trình sử dụng (net RAM).
- **Cách chạy**: Tích hợp lớp `ProcessTreeMemoryMonitor` trong các pipeline cần đo lường tài nguyên.
- **Test**: Khởi chạy trong `build_gold.py` hoặc chạy test đo RAM độc lập.

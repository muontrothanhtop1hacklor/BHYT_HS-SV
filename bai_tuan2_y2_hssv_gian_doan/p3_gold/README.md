# Phần 3: Xây dựng Tầng Gold – Bài toán Ý 2 (CV 835/QLT)

Thư mục này chịu trách nhiệm xử lý và tổng hợp dữ liệu tầng Gold cho bài toán Ý 2:
Tìm kiếm và báo cáo các trường hợp HSSV tham gia từ tháng 10/2024, tháng 7/2026 vẫn đang tham gia nhưng có thời gian gián đoạn từ 3 tháng trở lên ($\ge 90$ ngày).

## Danh mục tệp

- [`gold_logic_y2.py`](gold_logic_y2.py): Logic nghiệp vụ cốt lõi và hàm sinh SQL DuckDB.
- [`build_gold_y2.py`](build_gold_y2.py): Pipeline sản xuất tầng Gold, hỗ trợ đo lường RAM/CPU và xuất Parquet/CSV.
- [`test_timeline_gaps.py`](test_timeline_gaps.py): Kiểm thử đơn vị cho gap hai biên, ngưỡng 90 ngày và tie-break.
- [`test_gold_y2_invariants.py`](test_gold_y2_invariants.py): 6 kiểm thử kiểm tra tính toàn vẹn và bất biến dữ liệu tầng Gold.

## Lệnh thực thi

### 1. Chạy pipeline tầng Gold
```powershell
python -m bai_tuan2_y2_hssv_gian_doan.p3_gold.build_gold_y2 --method global --threads 4
```

### 2. Chạy kiểm thử đơn vị & kiểm thử bất biến
```powershell
pytest bai_tuan2_y2_hssv_gian_doan/p3_gold/test_timeline_gaps.py -v
pytest bai_tuan2_y2_hssv_gian_doan/p3_gold/test_gold_y2_invariants.py -v
```

# common/data_gen: Sinh và kiểm tra dữ liệu BHYT giả lập (CV 835/QLT)

## 1. Mục đích
Cung cấp công cụ sinh dữ liệu BHYT giả lập quy mô lớn (200 triệu dòng thẻ cho 20 triệu người tham gia) theo mô hình vòng đời đối tượng (Person Lifecycle) tối ưu hóa với Numba JIT song song đa tiến trình.

## 2. Cấu trúc tệp
- `gen_bhyt.py`: Bộ sinh dữ liệu chính (hỗ trợ các lệnh `generate`, `calibrate`, `bench`).
- `validate_bhyt.py`: Bộ kiểm tra toàn vẹn dữ liệu, kiểm tra 12 quy tắc nghiệp vụ thẻ và xuất đáp án tham chiếu.
- `chay_sinh_du_lieu.bat`: Kịch bản chạy nhanh trên môi trường Windows.

## 3. Hướng dẫn sử dụng

### Sinh dữ liệu:
```powershell
# Chạy sinh dữ liệu mẫu 200.000 người (~2 triệu dòng thẻ)
python common/data_gen/gen_bhyt.py generate --out data/bhyt_data --persons 200000 --chunk-persons 50000 --workers 4

# Chạy sinh toàn phần 20.000.000 người (~200 triệu dòng thẻ)
python common/data_gen/gen_bhyt.py generate --out data/bhyt_data --persons 20000000 --chunk-persons 100000 --workers 4
```

### Kiểm tra toàn vẹn và xuất đáp án chuẩn:
```powershell
python common/data_gen/validate_bhyt.py --data data/bhyt_data --export data/bhyt_answer
```

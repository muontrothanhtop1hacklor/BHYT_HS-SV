# ANTIGRAVITY WORKSPACE RULES & PROJECT CONTEXT

## Quy trình sinh và kiểm tra dữ liệu BHYT 200M dòng (CV 835/QLT)

### 1. Công cụ sinh dữ liệu chính
- **Thư mục:** `common/data_gen/`
- **Mã nguồn sinh:** `common/data_gen/gen_bhyt.py` (sử dụng Numba JIT tối ưu hóa song song, sinh theo vòng đời người Person Lifecycle).
- **Kiểm tra đáp án chuẩn:** `common/data_gen/validate_bhyt.py`
- **Kịch bản chạy nhanh:** `common/data_gen/chay_sinh_du_lieu.bat`
- **Thư mục dữ liệu chuẩn:** `data/bhyt_data` (chứa `dm_bhxh.csv`, `st_inthe_dtl/`, `dirty_log/`, `persons_gt/`)

### 2. Lệnh sinh dữ liệu chuẩn
- Sinh thử nghiệm:
  ```powershell
  python common/data_gen/gen_bhyt.py generate --out data/bhyt_data --persons 200000 --chunk-persons 50000 --workers 4
  ```
- Sinh quy mô toàn diện (20 triệu người ~ 200 triệu dòng thẻ):
  ```powershell
  python common/data_gen/gen_bhyt.py generate --out data/bhyt_data --persons 20000000 --chunk-persons 100000 --workers 4
  ```
- Kiểm tra toàn vẹn và trích xuất đáp án:
  ```powershell
  python common/data_gen/validate_bhyt.py --data data/bhyt_data --export data/bhyt_answer
  ```

### 3. Môi trường & Mã hóa
- Trên môi trường Windows / PowerShell, luôn bật chế độ mã hóa UTF-8 để không bị lỗi ký tự tiếng Việt (`sys.stdout.reconfigure(encoding='utf-8')`).

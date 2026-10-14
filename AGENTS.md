# ANTIGRAVITY WORKSPACE RULES & PROJECT CONTEXT

## Quy trình sinh và kiểm tra dữ liệu BHYT 200M dòng (CV 835/QLT)

### 1. Script sinh dữ liệu (`common/data_gen/gen_bhyt.py`)
Khi cần sinh dữ liệu thẻ BHYT giả lập (`ST_INTHE_DTL`, `persons_gt`, `dirty_log`, `dm_bhxh`), **LUÔN SỬ DỤNG** `common/data_gen/gen_bhyt.py`.
- **Cơ chế:** Vòng đời đối tượng (Person Lifecycle), ánh xạ song ánh đảm bảo đúng tỷ lệ khối, ghi atomic file Parquet nén `zstd`, có manifest resume khi chạy lại.
- **Lệnh chạy chuẩn 20 triệu người (~200M dòng thẻ):**
  ```powershell
  python common/data_gen/gen_bhyt.py generate --out data/bhyt_data --persons 20000000 --chunk-persons 100000 --workers 4
  ```
  *(Thời gian thực tế: ~4 phút 05 giây, tốc độ ~794.000 dòng/giây, chiếm ~4,94 GB đĩa).*

### 2. Script kiểm tra & Tính đáp án chuẩn (`common/data_gen/validate_bhyt.py`)
Sau khi sinh dữ liệu, **LUÔN SỬ DỤNG** `common/data_gen/validate_bhyt.py` để kiểm tra toàn vẹn và trích xuất đáp án chuẩn đối chiếu cho Ý 1 (CV 835/QLT):
- **Lệnh chạy chuẩn:**
  ```powershell
  python common/data_gen/validate_bhyt.py --data data/bhyt_data --export data/bhyt_answer
  ```
- **Kết quả xuất ra:**
  - `data/bhyt_answer/answer_list.parquet`: Danh sách cá nhân HSSV dừng tham gia (848.413 người).
  - `data/bhyt_answer/answer_by_tinh.csv`: Bảng tổng hợp theo 63 tỉnh/thành phố.

### 3. Môi trường & Mã hóa
- Trên môi trường Windows / PowerShell, luôn bật chế độ mã hóa UTF-8 để không bị lỗi ký tự tiếng Việt. Cả hai script đã được cấu hình tự động `sys.stdout.reconfigure(encoding='utf-8')`.

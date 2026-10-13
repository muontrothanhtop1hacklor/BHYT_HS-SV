# HƯỚNG DẪN SINH VÀ KIỂM TRA DỮ LIỆU BHYT 200M DÒNG (CV 835/QLT)

## 1. Tổng quan & Vị trí mã nguồn
- Generator chuẩn (Lifecycle-based, Parquet zstd): [`scripts/gen_bhyt.py`](file:///c:/Users/Administrator/200m/scripts/gen_bhyt.py)
- Validator & Đáp án tham chiếu: [`scripts/validate_bhyt.py`](file:///c:/Users/Administrator/200m/scripts/validate_bhyt.py)
- Thư mục dữ liệu sinh ra: `data/bhyt_data`
- Thư mục đáp án tham chiếu xuất ra: `data/bhyt_answer`

## 2. Các lệnh chạy chính

### A. Ước lượng trước (Calibrate - không ghi đĩa)
```powershell
python scripts/gen_bhyt.py calibrate --sample 200000
```

### B. Chạy thử nghiệm nhanh (Benchmark đa luồng)
```powershell
python scripts/gen_bhyt.py bench --persons 200000 --chunk 50000 --workers 1 2 4 8
```
*Lưu ý: Trên máy tính 10 core, mức 4 workers cho throughput cao nhất (~600k - 800k dòng/giây).*

### C. Sinh dữ liệu đầy đủ 20 triệu người (~200 triệu dòng)
```powershell
python scripts/gen_bhyt.py generate --out data/bhyt_data --persons 20000000 --chunk-persons 100000 --workers 4
```
- Số chunk: 200 chunk (100.000 người/chunk ~ 1.000.000 dòng/chunk).
- Thời gian sinh: ~4 phút 05 giây (~794.000 dòng/s).
- Dung lượng đĩa: ~4,94 GB Parquet (nén `zstd`).
- Hỗ trợ resume: Mỗi chunk được ghi atomic (`.tmp -> .parquet`) kèm file `_manifest/chunk-XXXXX.json`. Nếu bị ngắt giữa chừng, chạy lại lệnh sẽ tự động tiếp tục các chunk chưa hoàn thành.

### D. Kiểm tra toàn diện & Xuất đáp án Ý 1
```powershell
python scripts/validate_bhyt.py --data data/bhyt_data --export data/bhyt_answer
```
- Quét và kiểm tra 12 quy tắc nghiệp vụ trên toàn bộ 200 chunk (~5,7 phút).
- Xuất danh sách 848.413 cá nhân dừng tham gia: `data/bhyt_answer/answer_list.parquet`
- Xuất bảng tổng hợp 63 tỉnh/thành phố: `data/bhyt_answer/answer_by_tinh.csv`

## 3. Cấu hình & Mốc nghiệp vụ
- **Mốc gốc T10/2024:** `base_month = "2024-10"`
- **Mốc kiểm tra T08/2026:** `check_month = "2026-08"` (ngày ký CV 835/QLT là 10/08/2026)
- **Cơ cấu khối đối tượng:** HS 19% (3.8M), SV 6% (1.2M), TE 10% (2M), DN 30% (6M), GD 25% (5M), HT 10% (2M).
- **Tỷ lệ dòng bẩn chủ đích:** 1% (`LOAI_LOI` 1 đến 5 trong `dirty_log`).

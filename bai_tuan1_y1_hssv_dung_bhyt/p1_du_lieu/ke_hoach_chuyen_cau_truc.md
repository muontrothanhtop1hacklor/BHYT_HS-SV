# KẾ HOẠCH TÁI CẤU TRÚC REPO 200M THEO BÀI / PHẦN (GIAI ĐOẠN A)

## 1. Điểm quay lại an toàn (Rollback Point)
- **Git Commit:** `889ecfa`
- **Git Tag đã tạo:** `backup-truoc-chuyen-cau-truc`
- **Git Branch dự phòng:** `backup-truoc-chuyen-cau-truc`
- **Trạng thái trước khi chuyển:** Toàn bộ 42/42 tests PASSED (2 test_data_quality + 25 test_edge_cases + 15 test_gold_invariants).

---

## 2. Bảng ánh xạ chuyển đổi vị trí file (A1)

| STT | File hiện tại | Vị trí đích | Lý do chuyển / Phân loại nghiệp vụ |
|:---:|:---|:---|:---|
| 1 | `scripts/gen_bhyt.py` | `common/data_gen/gen_bhyt.py` | Script sinh dữ liệu 200M (Script 2 Numba/Person Lifecycle), dùng chung nhiều bài |
| 2 | `scripts/gen_bhyt_script1.py` | `common/data_gen/gen_bhyt_script1.py` | Script sinh dữ liệu vòng đời H1-H10 (Script 1 SplitMix64), dùng chung nhiều bài |
| 3 | `scripts/validate_bhyt.py` | `common/data_gen/validate_bhyt.py` | Script xác thực và xuất Ground Truth đáp án tham chiếu |
| 4 | `scripts/01_generate_data.bat`<br>`scripts/01_generate_data_script1.bat` | `common/data_gen/chay_sinh_du_lieu.bat` | Kịch bản batch hợp nhất sinh dữ liệu (giữ cả lệnh chạy Script 1 và Script 2) |
| 5 | `src/generator/*`<br>(`__init__.py`, `generate_dm_bhxh.py`,<br>`generate_st_inthe_dtl.py`, `lifecycle.py`) | `common/data_gen/legacy/*`<br>*(Chờ người dùng xác nhận)* | Code sinh fake data ban đầu (sơ khai), không còn được import/chạy bởi pipeline nào |
| 6 | `src/config.py` | `common/config.py` | Cấu hình tham số mốc thời gian CV 835, đường dẫn dữ liệu tập trung cho toàn repo |
| 7 | `src/utils/resource_monitor.py` | `bai_ram_1_10_100m/resource_monitor.py` | Module đo RAM tiến trình cha/con (thuộc bài toán kiểm soát RAM 1-10-100M) |
| 8 | `scripts/run_all_script1.bat` | `bai_tuan1_y1_hssv_dung_bhyt/chay_tat_ca.bat` | Kịch bản batch chạy toàn bộ pipeline Tuần 1 Ý 1 |
| 9 | `sql/ddl/01_dm_bhxh.sql` | `bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/ddl_dm_bhxh.sql` | DDL bảng danh mục cơ quan BHXH (Phần 1 - Dữ liệu) |
| 10 | `sql/ddl/02_st_inthe_dtl.sql` | `bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/ddl_st_inthe_dtl.sql` | DDL bảng chi tiết thẻ BHYT (Phần 1 - Dữ liệu) |
| 11 | `tests/test_data_quality.py` | `bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/test_data_quality.py` | Kiểm tra chất lượng dữ liệu nguồn, schema và tính toàn vẹn (Phần 1) |
| 12 | `docs/bao_cao_ngay1.md` | `bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/bao_cao_ngay1.md` | Báo cáo Ngày 1: Phân tích và cấu trúc dữ liệu ban đầu |
| 13 | `scripts/build_bronze.py` | `bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/build_bronze.py` | Pipeline nạp thô nguyên trạng tầng Bronze Medallion |
| 14 | `scripts/build_silver.py` | `bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/build_silver.py` | Pipeline làm sạch dữ liệu, áp 5 quy tắc xử lý dòng bẩn tầng Silver |
| 15 | `scripts/analyze_131_gap.py` | `bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/phan_tich_131_nguoi.py` | Script phân tích định lượng 131 người chênh lệch Silver vs Validator |
| 16 | `tests/test_edge_cases.py`<br>*(Nhóm TestDataQualityRules)* | `bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/test_quy_tac_dong_ban.py` | Tách 5 test quy tắc dòng bẩn: lỗi 1 (TU>DEN), lỗi 4 (chuẩn hóa mã khối), lỗi 2, 3, 5 |
| 17 | `docs/dac_ta_nghiep_vu_ngay2.md` | `bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/dac_ta_nghiep_vu.md` | Đặc tả nghiệp vụ làm sạch dữ liệu và cách ly dòng bẩn Ngày 2 |
| 18 | `docs/bao_cao_ngay2.md` | `bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/bao_cao_ngay2.md` | Báo cáo nghiệm thu kết quả tầng Bronze & Silver Ngày 2 |
| 19 | `src/pipelines/gold_logic.py` | `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/gold_logic.py` | Thư viện nghiệp vụ lõi tính giao tháng, dừng tham gia, phân xử ưu tiên khối |
| 20 | `scripts/build_gold.py` | `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/build_gold.py` | Pipeline tổng hợp báo cáo Gold danh sách cá nhân và thống kê tỉnh |
| 21 | `sql/ddl/03_output_tables.sql` | `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/ddl_output_tables.sql` | DDL bảng đích tầng Gold (bc_hssv_dung_tham_gia, tk_dbhc_...) |
| 22 | `tests/test_edge_cases.py`<br>*(Nhóm Basic & Advanced)* | `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/test_edge_cases.py` | Tách 20 test logic tham gia tháng M và dừng BHYT (5 ca cơ bản + 15 ca biên) |
| 23 | `tests/test_gold_invariants.py` | `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/test_gold_invariants.py` | Test 15 ca kiểm thử tính bất biến số liệu Gold và các kịch bản lỗi |
| 24 | `docs/plan_ngay3.md` | `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/plan_ngay3.md` | Kế hoạch thực hiện xử lý dòng tồn đọng và xây dựng Gold Ngày 3 |
| 25 | `docs/bao_cao_ngay3.md` | `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/bao_cao_ngay3.md` | Báo cáo nghiệm thu Ngày 3: Idempotent, Invariants, Báo cáo Gold |
| 26 | `src/pipelines/pipeline_dev_a.py` | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_a/pipeline_dev_a.py` | Pipeline giải pháp Bạn A (PyArrow Out-of-Core streaming) |
| 27 | `sql/dev_a/query_y1_dung_tham_gia.sql` | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_a/query_y1.sql` | SQL truy vấn Ý 1 của Bạn A |
| 28 | `scripts/02_run_pipeline_a.bat` | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_a/chay.bat` | File batch thực thi pipeline Bạn A |
| 29 | `src/pipelines/pipeline_dev_b.py` | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_b/pipeline_dev_b.py` | Pipeline giải pháp Bạn B (DuckDB In-Memory SQL) |
| 30 | `sql/dev_b/query_y1_dung_tham_gia.sql` | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_b/query_y1.sql` | SQL truy vấn Ý 1 của Bạn B |
| 31 | `scripts/03_run_pipeline_b.bat` | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_b/chay.bat` | File batch thực thi pipeline Bạn B |
| 32 | `src/reconciliation/compare_results.py` | `bai_tuan1_y1_hssv_dung_bhyt/p5_doi_soat/compare_results.py` | Script đối soát kết quả giữa Bạn A vs Bạn B vs SCENARIO |
| 33 | `scripts/verify_sql_duckdb.py` | `bai_tuan1_y1_hssv_dung_bhyt/p5_doi_soat/verify_sql_duckdb.py` | Script kiểm chứng độc lập bằng DuckDB SQL trên Raw và Silver |
| 34 | `scripts/04_reconcile.bat` | `bai_tuan1_y1_hssv_dung_bhyt/p5_doi_soat/chay_doi_soat.bat` | File batch thực thi đối soát tự động |

---

## 3. Danh sách các vị trí cần sửa đường dẫn & import (A2)

### A. Sửa dòng Import trong mã nguồn Python
1. **Thay thế `from src.config import ...` $\rightarrow$ `from common.config import ...`:**
   - `bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/test_data_quality.py`
   - `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_a/pipeline_dev_a.py`
   - `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_b/pipeline_dev_b.py`
   - `bai_tuan1_y1_hssv_dung_bhyt/p5_doi_soat/compare_results.py`
2. **Thay thế `from src.pipelines.gold_logic import ...` $\rightarrow$ `from bai_tuan1_y1_hssv_dung_bhyt.p3_gold.gold_logic import ...`:**
   - `bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/test_quy_tac_dong_ban.py`
   - `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/test_edge_cases.py`
   - `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/test_gold_invariants.py`
3. **Thay thế `from src.utils.resource_monitor import ProcessTreeMemoryMonitor`:**
   - Trong `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/build_gold.py`:
     - Sửa thành: `from bai_ram_1_10_100m.resource_monitor import ProcessTreeMemoryMonitor`
     - Bổ sung `sys.path.insert(0, str(PROJECT_ROOT))` để tìm thấy module `bai_ram_1_10_100m`.

### B. Cấu hình `common/config.py`
- Giữ nguyên `PROJECT_ROOT = Path(__file__).resolve().parent.parent` (vì `common/` là con trực tiếp của repo root `200m/`).
- Các đường dẫn `DATA_DIR`, `BHYT_DATA_DIR`, `OUTPUT_DIR` trỏ vào `data/` không thay đổi.

### C. Các file `.bat`
- `common/data_gen/chay_sinh_du_lieu.bat`: gọi `python common/data_gen/gen_bhyt.py` hoặc `python common/data_gen/gen_bhyt_script1.py`.
- `bai_tuan1_y1_hssv_dung_bhyt/chay_tat_ca.bat`: gọi các file trong `p4_giai_phap_a_b` và `p5_doi_soat`.
- `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_a/chay.bat`: gọi pipeline Bạn A.
- `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_b/chay.bat`: gọi pipeline Bạn B.
- `bai_tuan1_y1_hssv_dung_bhyt/p5_doi_soat/chay_doi_soat.bat`: gọi đối soát.

---

## 4. Kết quả kiểm tra 3 điểm trọng yếu trước khi chuyển (A3)

### (a) Phân loại `tests/test_edge_cases.py` (25 tests):
- **Phần 2 (Quy tắc dòng bẩn - `test_quy_tac_dong_ban.py`):** 5 tests
  - `test_case_21_loai_1_tu_ngay_lon_hon_den_ngay` (Lỗi 1: TU_NGAY > DEN_NGAY)
  - `test_case_22_loai_4_chuan_hoa_ma_khoi` (Lỗi 4: Chuẩn hóa chữ thường/khoảng trắng)
  - `test_case_23_loai_2_ho_ten_null_gan_co` (Lỗi 2: Họ tên null)
  - `test_case_24_loai_3_gioi_tinh_khong_hop_le_gan_co` (Lỗi 3: Giới tính không hợp lệ)
  - `test_case_25_loai_5_khu_trung_lap_theo_id` (Lỗi 5: Khử trùng lặp ID)
- **Phần 3 (Logic tham gia/dừng - `test_edge_cases.py`):** 20 tests
  - `TestBasicFiveCases`: 5 ca cơ bản theo sơ đồ Gantt đề bài (test_case_1 đến 5).
  - `TestAdvancedEdgeCases`: 15 ca biên nghiệp vụ (test_case_06 đến 20: thẻ hủy, đa thẻ, chuyển khối, gián đoạn, ngày biên 01/10, 31/10, 01/08, 31/07, 31/08, 01/09).
- **Tổng số test:** 5 + 20 = 25 tests (bảo toàn 100%, không sửa logic nghiệp vụ).

### (b) Kiểm tra `src/generator/`:
- Các file trong `src/generator/`:
  - `src/generator/__init__.py`
  - `src/generator/generate_dm_bhxh.py`
  - `src/generator/generate_st_inthe_dtl.py`
  - `src/generator/lifecycle.py`
- **Kết quả rà soát (grep toàn repo):** Không có pipeline hay script nào trong hệ thống đang import hay gọi các file này. Dữ liệu được sinh bằng `scripts/gen_bhyt.py` hoặc `scripts/gen_bhyt_script1.py`.
- **Hành động:** Theo quy tắc A3(b), liệt kê đầy đủ, không tự ý xóa, xin ý kiến người dùng chuyển vào `common/data_gen/legacy/` hay giữ nguyên.

### (c) Kiểm tra `resource_monitor.py`:
- `src/utils/resource_monitor.py` **đang được import** bởi `scripts/build_gold.py` (dòng 44):
  ```python
  from src.utils.resource_monitor import ProcessTreeMemoryMonitor
  ```
- File này thuộc `p3_gold` của bài Tuần 1.
- Khi chuyển `resource_monitor.py` sang `bai_ram_1_10_100m/resource_monitor.py`, cần cập nhật import trong `build_gold.py` thành:
  ```python
  from bai_ram_1_10_100m.resource_monitor import ProcessTreeMemoryMonitor
  ```
- **Hành động:** Báo cáo chi tiết cho người dùng trước khi tiến hành chuyển.

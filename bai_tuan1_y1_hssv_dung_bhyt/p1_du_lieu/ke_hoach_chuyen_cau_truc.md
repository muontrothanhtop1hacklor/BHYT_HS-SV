# KẾ HOẠCH TÁI CẤU TRÚC REPO 200M THEO BÀI / PHẦN VÀ BỎ "BẠN A / BẠN B" (GIAI ĐOẠN A)

## 1. Điểm quay lại an toàn (Rollback Point)
- **Git Tag đã tạo:** `backup-truoc-tai-cau-truc-bo-ab`
- **Git Branch dự phòng:** `backup-truoc-tai-cau-truc-bo-ab`
- **Commit gốc:** `e0aad6d docs: khoi phuc bao_cao_ngay3.md ve ban goc`
- **Trạng thái trước khi chuyển:** Toàn bộ 42/42 tests PASSED (2 test_data_quality + 5 test_quy_tac_dong_ban + 20 test_edge_cases + 15 test_gold_invariants).

---

## 2. Bảng ánh xạ chuyển đổi vị trí file (A1)

| STT | File hiện tại | Vị trí đích | Lý do chuyển / Phân loại nghiệp vụ |
|:---:|:---|:---|:---|
| 1 | `common/config.py` | `common/config.py` | Cập nhật bổ sung đường dẫn `ket_qua_cua_ban` và file kết quả Gold của tôi |
| 2 | `common/data_gen/*` | `common/data_gen/*` | Giữ nguyên các script sinh dữ liệu dùng chung (`gen_bhyt.py`, `gen_bhyt_script1.py`, `validate_bhyt.py`, `chay_sinh_du_lieu.bat`, `legacy/*`) |
| 3 | `bai_ram_1_10_100m/resource_monitor.py` | `bai_ram_1_10_100m/resource_monitor.py` | Giữ nguyên (bài toán đo RAM 1-10-100M) |
| 4 | `bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/*` | `bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/*` | Giữ nguyên DDL, test_data_quality, bao_cao_ngay1 |
| 5 | `bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/*` | `bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/*` | Giữ nguyên build_bronze, build_silver, phan_tich_131_nguoi, test_quy_tac_dong_ban |
| 6 | `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/*` | `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/*` | Giữ nguyên gold_logic, build_gold, ddl_output_tables, test_edge_cases, test_gold_invariants |
| 7 | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_a/query_y1.sql` | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/sql/query_y1_cte_window.sql` | Chuyển file SQL sang thư mục SQL đối soát, đổi tên kỹ thuật (CTE + Window function) |
| 8 | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_b/query_y1.sql` | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/sql/query_y1_left_join.sql` | Chuyển file SQL sang thư mục SQL đối soát, đổi tên kỹ thuật (Left Join IS NULL) |
| 9 | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_a/pipeline_dev_a.py` | `_luu_tru/p4_giai_phap_a_b/dev_a/pipeline_dev_a.py` | Bỏ A/B: lưu trữ pipeline A do bạn cùng làm có giải pháp riêng ở máy khác |
| 10 | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_a/chay.bat` | `_luu_tru/p4_giai_phap_a_b/dev_a/chay.bat` | Bỏ A/B: kịch bản chạy pipeline A |
| 11 | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_a/README.md` | `_luu_tru/p4_giai_phap_a_b/dev_a/README.md` | Tài liệu A cũ |
| 12 | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_b/pipeline_dev_b.py` | `_luu_tru/p4_giai_phap_a_b/dev_b/pipeline_dev_b.py` | Bỏ A/B: lưu trữ pipeline B |
| 13 | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_b/chay.bat` | `_luu_tru/p4_giai_phap_a_b/dev_b/chay.bat` | Bỏ A/B: kịch bản chạy pipeline B |
| 14 | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/dev_b/README.md` | `_luu_tru/p4_giai_phap_a_b/dev_b/README.md` | Tài liệu B cũ |
| 15 | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/README.md` | `_luu_tru/p4_giai_phap_a_b/README.md` | Bỏ A/B: thư mục p4_giai_phap_a_b không còn dùng |
| 16 | `bai_tuan1_y1_hssv_dung_bhyt/p4_giai_phap_a_b/__init__.py` | `_luu_tru/p4_giai_phap_a_b/__init__.py` | Bỏ A/B: init package |
| 17 | `bai_tuan1_y1_hssv_dung_bhyt/p5_doi_soat` | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat` | Đổi tên Phần 5 thành Phần 4 (do bỏ p4_giai_phap_a_b) |
| 18 | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/compare_results.py` | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/compare_results.py` | Sửa đường dẫn: so kết quả Gold của tôi với `ket_qua_cua_ban` |
| 19 | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/verify_sql_duckdb.py` | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/verify_sql_duckdb.py` | Script kiểm chứng độc lập bằng SQL DuckDB |
| 20 | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/chay_doi_soat.bat` | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/chay_doi_soat.bat` | Cập nhật lệnh chạy compare_results từ p4_doi_soat |
| 21 | *(Mới)* | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/ket_qua_cua_ban/README.md` | Thư mục rỗng nhận file kết quả từ bạn cùng làm |
| 22 | *(Mới)* | `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/dinh_dang_trao_doi.md` | Tài liệu đặc tả định dạng file kết quả đối soát trao đổi |
| 23 | `src/config.py` | `_luu_tru/src/config.py` | File cũ trong root, đã thay bằng common/config.py |
| 24 | `src/pipelines/__init__.py` | `_luu_tru/src/pipelines/__init__.py` | Thư mục cũ không còn dùng |
| 25 | `src/reconciliation/__init__.py` | `_luu_tru/src/reconciliation/__init__.py` | Thư mục cũ không còn dùng |
| 26 | `tests/__init__.py` | `_luu_tru/tests/__init__.py` | Thư mục cũ không còn dùng (test đã chuyển về từng phần) |
| 27 | `bai_tuan1_y1_hssv_dung_bhyt/chay_tat_ca.bat` | `bai_tuan1_y1_hssv_dung_bhyt/chay_tat_ca.bat` | Cập nhật gọi build_gold (phương pháp chuẩn global), không gọi pipeline A/B |

---

## 3. Danh sách các vị trí cần sửa đường dẫn & import (A2)

### A. Sửa đường dẫn trong `common/config.py`
- Bổ sung cấu hình đường dẫn `KET_QUA_CUA_BAN_DIR = PROJECT_ROOT / "bai_tuan1_y1_hssv_dung_bhyt" / "p4_doi_soat" / "ket_qua_cua_ban"`.
- Bổ sung `GOLD_RESULT_DIR = OUTPUT_DIR / "gold" / "20241001_20260801_any"`.
- Bổ sung `GOLD_BC_FILE = GOLD_RESULT_DIR / "bc_hssv_dung_tham_gia.parquet"`.

### B. Sửa `compare_results.py`
- Thay `OUTPUT_DEV_A_DIR` thành file kết quả của tôi (`GOLD_BC_FILE`).
- Thay `OUTPUT_DEV_B_DIR` thành thư mục kết quả của bạn (`KET_QUA_CUA_BAN_DIR / "bc_hssv_dung_tham_gia.parquet"`).
- Sửa header dòng 1: `# Bài: tuan1_y1 | Phần: p4_doi_soat`.

### C. Sửa `bai_tuan1_y1_hssv_dung_bhyt/chay_tat_ca.bat`
- Bỏ các lệnh gọi `pipeline_dev_a` và `pipeline_dev_b`.
- Gọi pipeline chính thống:
  1. `python -m bai_tuan1_y1_hssv_dung_bhyt.p2_bronze_silver.build_silver` (nếu cần)
  2. `python -m bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold --method global`
  3. `python -m bai_tuan1_y1_hssv_dung_bhyt.p4_doi_soat.compare_results`

### D. Cập nhật README các cấp (B2, B5)
- README gốc (`README.md`): Cấu trúc mới 4 phần, bỏ hoàn toàn Bạn A/Bạn B trong cây thư mục chính.
- `bai_tuan1_y1_hssv_dung_bhyt/README.md`: Cập nhật bảng 4 phần, luồng xử lý và đối soát qua file.
- Mỗi phần (`p1_du_lieu`, `p2_bronze_silver`, `p3_gold`, `p4_doi_soat`, `common/data_gen`): README đúng chuẩn 5 dòng.

---

## 4. Kết quả kiểm tra 4 điểm trọng yếu trước khi chuyển (A3)

### (a) Kiểm tra phân loại `test_edge_cases.py` (25 tests):
- **Phần 2 (`test_quy_tac_dong_ban.py`):** 5 tests kiểm tra 5 quy tắc dòng bẩn (Lỗi 1 TU>DEN, Lỗi 4 Chuẩn hóa mã khối, Lỗi 2 Họ tên null, Lỗi 3 Giới tính không hợp lệ, Lỗi 5 Khử trùng lặp ID).
- **Phần 3 (`test_edge_cases.py`):** 20 tests kiểm tra logic thẻ giao tháng M và dừng tham gia BHYT (5 basic tests + 15 advanced tests).
- Tổng số: 5 + 20 = 25 tests, bảo toàn 100%.

### (b) Kiểm tra `src/generator/`:
- Không có bất kỳ file nào trong dự án import `src.generator`.
- Code lịch sử đã được lưu trữ an toàn tại `common/data_gen/legacy/`.

### (c) Kiểm tra `resource_monitor.py`:
- `bai_ram_1_10_100m/resource_monitor.py` chỉ được import bởi:
  - `bai_tuan1_y1_hssv_dung_bhyt/p3_gold/build_gold.py` dòng 45: `from bai_ram_1_10_100m.resource_monitor import ProcessTreeMemoryMonitor`.
- Đã được cập nhật và kiểm thử hoạt động bình thường.

### (d) Kiểm tra tham chiếu Bạn A / Bạn B:
- Không còn bất kỳ file code nào trong pipeline hay test phụ thuộc vào `pipeline_dev_a` hay `pipeline_dev_b`.
- Các báo cáo lịch sử (`bao_cao_ngay1.md`, `bao_cao_ngay2.md`, `bao_cao_ngay3.md`) giữ nguyên nội dung gốc làm bằng chứng nghiệm thu các ngày trước.
- Toàn bộ code dev_a/dev_b sẽ được chuyển vào `_luu_tru/`.
- 2 file SQL dev_a/dev_b được giữ lại trong `p4_doi_soat/sql/` và đổi tên theo đúng kỹ thuật (`query_y1_cte_window.sql` và `query_y1_left_join.sql`).

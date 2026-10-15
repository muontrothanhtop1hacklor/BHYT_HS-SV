# Bài Tuần 1 - Ý 1: Rà soát HSSV dừng tham gia BHYT (CV 835/QLT)

## 1. Tóm tắt Đề bài & Nghiệp vụ
Thực hiện công văn 835/QLT ngày 10/08/2026 của Ban Quản lý Thu - Sổ, Thẻ (BHXH Việt Nam) về việc rà soát học sinh, sinh viên (HSSV) tham gia BHYT nhưng đến nay đã dừng tham gia.
- **Mốc gốc (T10/2024):** Có tham gia BHYT thuộc khối Học sinh (`HS`) hoặc Sinh viên (`SV`).
- **Mốc kiểm tra "đến nay" (T08/2026):** Không còn tham gia BHYT ở bất kỳ đối tượng/khối nào.

### Định nghĩa Thẻ có tham gia tại tháng M (Giao tháng M)
Một thẻ BHYT được xác định là có giá trị sử dụng trong tháng $M$ khi và chỉ khi thỏa mãn đồng thời 3 điều kiện:
1. `TRANG_THAI = 1` (Thẻ có hiệu lực, không bị hủy).
2. `TU_NGAY < M_NEXT` (Bắt đầu trước ngày đầu tiên của tháng sau $M$).
3. `DEN_NGAY >= M_START` (Hết hạn từ ngày đầu tiên của tháng $M$ trở về sau).

### Định nghĩa "Đã dừng tham gia"
- **Định nghĩa mặc định (`stop_def = "any"`):** Người có thẻ `HS` hoặc `SV` giao tháng 10/2024, và **không có bất kỳ thẻ nào** (thuộc mọi khối `HS`, `SV`, `DN`, `GD`, `TE`, `HT`...) giao tháng 08/2026.
- **Quy tắc giải quyết xung đột đa thẻ (Tie-breaking):**
  - Nếu một người có nhiều thẻ cùng giao tháng 10/2024: Ưu tiên khối `SV` > `HS`.
  - Nếu cùng khối: Chọn thẻ có `DEN_NGAY` lớn nhất.
  - Nếu cùng `DEN_NGAY`: Chọn theo thứ tự `SO_THE_KCB` (alphabet).

---

## 2. Bảng cơ cấu các phần của bài toán

| Phần | Tên thư mục | Chức năng chính | Đầu ra chính | Lệnh chạy |
|:---|:---|:---|:---|:---|
| **Phần 1** | `p1_du_lieu` | DDL bảng thô và kiểm tra chất lượng dữ liệu nguồn | Schema validation, Báo cáo Ngày 1 | `pytest bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/test_data_quality.py -v` |
| **Phần 2** | `p2_bronze_silver` | Kiến trúc Medallion Bronze (nạp thô) & Silver (làm sạch 5 loại lỗi) | `data/bronze/`, `data/silver/`, `quarantine/` | `python -m bai_tuan1_y1_hssv_dung_bhyt.p2_bronze_silver.build_bronze`<br>`python -m bai_tuan1_y1_hssv_dung_bhyt.p2_bronze_silver.build_silver` |
| **Phần 3** | `p3_gold` | Pipeline tổng hợp báo cáo Gold danh sách & thống kê 63 tỉnh | `data/output/gold/` | `python -m bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold --method global` |
| **Phần 4** | `p4_doi_soat` | Đối soát độc lập với file bạn cùng làm & kiểm chứng DuckDB SQL | Báo cáo đối soát `reconciliation_report.md` | `python -m bai_tuan1_y1_hssv_dung_bhyt.p4_doi_soat.compare_results` |

---

## 3. Thứ tự thực thi toàn bộ bài toán

### Cách 1: Chạy tự động toàn bộ bằng file Batch
Chạy file [chay_tat_ca.bat](file:///c:/Users/Administrator/200m/bai_tuan1_y1_hssv_dung_bhyt/chay_tat_ca.bat):
```powershell
.\bai_tuan1_y1_hssv_dung_bhyt\chay_tat_ca.bat
```

### Cách 2: Chạy lần lượt từng bước qua dòng lệnh (`python -m`)
1. **Kiểm tra chất lượng dữ liệu nguồn:**
   ```powershell
   pytest bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/test_data_quality.py -v
   ```
2. **Làm sạch dữ liệu tầng Silver:**
   ```powershell
   python -m bai_tuan1_y1_hssv_dung_bhyt.p2_bronze_silver.build_silver
   ```
3. **Xây dựng Báo cáo tổng hợp tầng Gold:**
   ```powershell
   python -m bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold --method global
   ```
4. **Đối soát kết quả với file của bạn cùng làm:**
   *(Đặt file `bc_hssv_dung_tham_gia.parquet` nhận từ bạn vào `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/ket_qua_cua_ban/`)*
   ```powershell
   python -m bai_tuan1_y1_hssv_dung_bhyt.p4_doi_soat.compare_results
   ```
5. **Chạy toàn bộ bộ kiểm thử đơn vị & biên (42 tests):**
   ```powershell
   pytest -v
   ```

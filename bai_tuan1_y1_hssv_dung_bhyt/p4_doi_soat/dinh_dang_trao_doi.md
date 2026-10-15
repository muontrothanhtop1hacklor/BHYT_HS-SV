# ĐẶC TẢ ĐỊNH DẠNG FILE KẾT QUẢ TRAO ĐỔI ĐỐI SOÁT

Tài liệu này mô tả chi tiết quy cách, cấu trúc và định dạng file dữ liệu kết quả xuất ra từ hệ thống xử lý để thực hiện trao đổi và đối soát độc lập giữa các bên (hoặc giữa 2 kỹ sư trên các máy khác nhau).

---

## 1. Danh mục file kết quả trao đổi

Khi hoàn tất tính toán tầng Gold cho một bộ tham số (ví dụ: mốc gốc `2024-10-01`, mốc kiểm tra `2026-08-01`, định nghĩa dừng `any`), bên cung cấp kết quả cần xuất và đóng gói các file sau vào thư mục trao đổi (hoặc đặt vào thư mục `p4_doi_soat/ket_qua_cua_ban/`):

| Tên file | Định dạng | Mục đích | Bắt buộc |
|:---|:---|:---|:---:|
| `bc_hssv_dung_tham_gia.parquet` | Apache Parquet (nén `zstd`) | Danh sách chi tiết từng cá nhân HSSV dừng tham gia | **Bắt buộc** |
| `tk_dbhc_hssv_dung_tham_gia.csv` | CSV (UTF-8, dấu phẩy `,`) | Bảng tổng hợp số lượng theo 63 tỉnh/thành phố | Khuyến nghị |
| `tk_dbhc_hssv_dung_tham_gia.parquet` | Apache Parquet (nén `zstd`) | Bảng tổng hợp theo tỉnh dạng Parquet | Tùy chọn |
| `_manifest.json` | JSON (UTF-8) | Siêu dữ liệu tham số chạy và mã băm SHA-256 | Khuyến nghị |

---

## 2. Cấu trúc chi tiết từng file

### 2.1. File danh sách chi tiết: `bc_hssv_dung_tham_gia.parquet`
* **Mục đích:** Chứa toàn bộ danh sách từng học sinh, sinh viên được xác định là dừng tham gia BHYT.
* **Định dạng:** Apache Parquet, nén `zstd` (level 1).
* **Khóa chính duy nhất:** `SO_SO_BHXH` (mỗi cá nhân chỉ xuất hiện duy nhất 1 dòng).
* **Schema chi tiết:**

| STT | Tên cột | Kiểu dữ liệu | Mô tả & Ràng buộc giá trị |
|:---:|:---|:---|:---|
| 1 | `SO_SO_BHXH` | `VARCHAR(10)` / `string` | **Khóa chính.** Mã số bảo hiểm xã hội (10 chữ số). |
| 2 | `HO_TEN` | `VARCHAR(100)` / `string` | Họ và tên người tham gia. |
| 3 | `NGAY_SINH` | `DATE` | Ngày tháng năm sinh (`YYYY-MM-DD`). |
| 4 | `GIOI_TINH` | `SMALLINT` / `int16` | Giới tính (1: Nam, 2: Nữ). |
| 5 | `SO_CMND` | `VARCHAR(12)` / `string` | Số CCCD/CMND (12 hoặc 9 chữ số). |
| 6 | `SO_THE_KCB_GOC` | `VARCHAR(15)` / `string` | Mã số thẻ BHYT có giá trị sử dụng tại mốc gốc (T10/2024). |
| 7 | `MA_KHOI_GOC` | `VARCHAR(10)` / `string` | Mã khối tại mốc gốc: Chỉ nhận giá trị `'HS'` hoặc `'SV'`. |
| 8 | `TU_NGAY_GOC` | `DATE` | Ngày bắt đầu giá trị thẻ tại mốc gốc. |
| 9 | `DEN_NGAY_GOC` | `DATE` | Ngày hết hạn giá trị thẻ tại mốc gốc. |
| 10 | `DM_BHXH_ID` | `INTEGER` / `int32` | Mã định danh cơ quan BHXH quản lý cấp thẻ mốc gốc. |
| 11 | `MA_TINH` | `VARCHAR(20)` / `string` | Mã tỉnh/thành phố quản lý (tra từ DM_BHXH). |
| 12 | `NGAY_GOC` | `DATE` | Ngày đầu tháng mốc gốc (mặc định: `2024-10-01`). |
| 13 | `NGAY_KIEM_TRA` | `DATE` | Ngày mốc kiểm tra (mặc định: `2026-08-10` hoặc `2026-08-01`). |
| 14 | `CREATED_AT` | `TIMESTAMP` | Thời điểm ghi nhận bản ghi. |

---

### 2.2. File bảng tổng hợp theo tỉnh: `tk_dbhc_hssv_dung_tham_gia.csv`
* **Mục đích:** Thống kê số lượng HSSV dừng tham gia BHYT phân bổ theo 63 tỉnh/thành phố.
* **Định dạng:** CSV UTF-8 có header, ngăn cách bằng dấu phẩy `,`.
* **Số dòng:** Đúng 63 dòng (ứng với 63 tỉnh/thành phố).
* **Schema chi tiết:**

| STT | Tên cột | Kiểu dữ liệu | Mô tả |
|:---:|:---|:---|:---|
| 1 | `MA_TINH` | `VARCHAR(20)` / `string` | Mã BHXH của Tỉnh/Thành phố (2 chữ số, ví dụ `'01'`, `'79'`). |
| 2 | `TEN_TINH` | `VARCHAR(200)` / `string` | Tên Tỉnh/Thành phố. |
| 3 | `SO_LUONG_HS_DUNG` | `BIGINT` / `int64` | Số lượng học sinh (`HS`) dừng tham gia. |
| 4 | `SO_LUONG_SV_DUNG` | `BIGINT` / `int64` | Số lượng sinh viên (`SV`) dừng tham gia. |
| 5 | `TONG_SO_NGUOI_DUNG` | `BIGINT` / `int64` | Tổng số lượng người dừng (`SO_LUONG_HS_DUNG + SO_LUONG_SV_DUNG`). |
| 6 | `NGAY_BAO_CAO` | `DATE` | Ngày xuất báo cáo (`YYYY-MM-DD`). |

---

### 2.3. File siêu dữ liệu tham số: `_manifest.json`
* **Mục đích:** Ghi nhận cấu hình và kiểm chứng tính toàn vẹn (checksum).
* **Cấu trúc JSON mẫu:**
```json
{
  "timestamp": "2026-10-15T09:30:00.000000",
  "parameters": {
    "base_start": "2024-10-01",
    "base_next": "2024-11-01",
    "chk_start": "2026-08-01",
    "chk_next": "2026-09-01",
    "report_date": "2026-08-10",
    "stop_def": "any"
  },
  "output_files": {
    "bc_parquet_path": ".../bc_hssv_dung_tham_gia.parquet",
    "bc_row_count": 850190,
    "sha256_bc_parquet": "abc123...",
    "tk_csv_path": ".../tk_dbhc_hssv_dung_tham_gia.csv",
    "sha256_tk_csv": "def456..."
  }
}
```

---

## 3. Các tham số nghiệp vụ cần thống nhất khi đối soát

Để hai bên đối chiếu đạt độ khớp 100%, bắt buộc phải thống nhất các tham số sau:
1. **Mốc tháng gốc:** Giao tháng 10/2024 (`TU_NGAY < 2024-11-01` và `DEN_NGAY >= 2024-10-01`).
2. **Mốc kiểm tra:** Giao tháng 08/2026 (`TU_NGAY < 2026-09-01` và `DEN_NGAY >= 2026-08-01`).
3. **Định nghĩa dừng tham gia (`stop_def`):**
   - Mặc định: `stop_def = "any"` (không còn bất kỳ thẻ BHYT hợp lệ nào ở mọi khối tại mốc kiểm tra).
4. **Quy tắc giải quyết xung đột đa thẻ (Tie-breaking):**
   - Ưu tiên khối: `SV` > `HS`.
   - Cùng khối: ưu tiên thẻ có `DEN_NGAY` lớn nhất.
   - Cùng `DEN_NGAY`: sắp xếp theo `SO_THE_KCB`.
5. **Quy tắc làm sạch dữ liệu bẩn tầng Silver:**
   - Dòng bẩn Loại 1 (`TU_NGAY > DEN_NGAY`): Đưa vào `quarantine`, không đoán sửa.
   - Dòng bẩn Loại 4 (Mã khối chữ thường hoặc có khoảng trắng): Cắt khoảng trắng và `UPPER(TRIM(MA_KHOI))`.

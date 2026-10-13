# ĐẶC TẢ NGHIỆP VỤ & QUY TẮC XỬ LÝ DỮ LIỆU (NGÀY 2)
**Dự án:** Tuần 1 – HSSV dừng tham gia BHYT (CV 835/QLT – Ý 1)  
**Ngày chốt đặc tả:** 13/10/2026  
**Trạng thái:** Đã thống nhất & Tham số hóa  

---

## 1. Mục tiêu & Phạm vi
Đặc tả chi tiết các quyết định nghiệp vụ, tham số hóa các mốc thời gian, quy tắc phân tầng dữ liệu (Medallion Architecture: Bronze $\to$ Silver) và chính sách quản lý chất lượng dữ liệu (Data Quality & Quarantine) nhằm phục vụ bài toán Ý 1 (CV 835/QLT).

---

## 2. Tham số hóa mốc thời gian nghiệp vụ

| Tham số | Giá trị mặc định | Giải thích nghiệp vụ |
|---|---|---|
| `BASE_MONTH` | `2024-10` | Tháng gốc xét đối tượng Học sinh / Sinh viên tham gia BHYT |
| `BASE_START_DATE` | `2024-10-01` | Ngày đầu tháng gốc |
| `BASE_NEXT_START_DATE` | `2024-11-01` | Ngày đầu tháng sau tháng gốc |
| `CHECK_MONTH` | `2026-08` | Tháng kiểm tra tình trạng "đến nay" theo thời điểm ban hành công văn |
| `CHECK_START_DATE` | `2026-08-01` | Ngày đầu tháng kiểm tra |
| `CHECK_NEXT_START_DATE` | `2026-09-01` | Ngày đầu tháng sau tháng kiểm tra |
| `REPORT_DATE` | `2026-08-10` | Ngày ký công văn 835/QLT (hiển thị trên các báo cáo thống kê) |

### Quy tắc giao thời gian:
Một cá nhân được tính là **có tham gia BHYT tại tháng $M$** khi có ít nhất một thẻ thỏa mãn:
$$\text{TRANG\_THAI} = 1 \quad \land \quad \text{TU\_NGAY} < \text{Ngày đầu tháng } (M+1) \quad \land \quad \text{DEN\_NGAY} \ge \text{Ngày đầu tháng } M$$

---

## 3. Ma trận quyết định nghiệp vụ & Đánh đổi

| Quyết định | Phương án chốt | Phương án dự phòng | Đánh đổi & Rủi ro |
|---|---|---|---|
| **Định nghĩa "dừng" (`stop_def`)** | **Mặc định `any`:** Người đó không còn bất kỳ thẻ BHYT hợp lệ nào ở bất kỳ khối nào (`HS, SV, TE, DN, GD, HT`) trong tháng kiểm tra. | **Tham số `hssv`:** Chỉ xét không còn thẻ khối `HS` hoặc `SV` tại tháng kiểm tra (nếu đã chuyển sang `DN` hoặc `GD` vẫn tính là dừng HSSV). | `hssv` cho tập kết quả lớn hơn (~+37% ở mẫu thử). Phương án `any` phản ánh đúng bản chất người hoàn toàn ra khỏi hệ thống an sinh BHYT. |
| **Dòng bẩn loại 1 (`TU_NGAY > DEN_NGAY`)** | **Đưa vào Quarantine (`silver_quarantine`), không đoán sửa.** | Hoán đổi: $\text{TU\_NGAY} \leftrightarrow \text{DEN\_NGAY}$. | Hoán đổi là suy đoán kỹ thuật không có căn cứ nghiệp vụ gốc. Đưa vào quarantine giúp bảo toàn tính toàn vẹn và minh bạch dữ liệu. |
| **Dòng bẩn loại 2 (`HO_TEN IS NULL`)** | **Giữ dòng, gắn cờ `FLAG_NAME_NULL = True`.** | Loại bỏ dòng. | Không ảnh hưởng đến định danh người (`SO_SO_BHXH`) và logic xác định dừng tham gia. Giữ lại để đối soát danh sách. |
| **Dòng bẩn loại 3 (`GIOI_TINH NOT IN (1, 2)`)** | **Giữ dòng, gắn cờ `FLAG_GENDER_INVALID = True`.** | Gán mặc định hoặc loại bỏ. | Không ảnh hưởng đến điều kiện dừng tham gia BHYT. Giữ nguyên trạng để báo cáo chất lượng dữ liệu. |
| **Dòng bẩn loại 4 (`MA_KHOI` viết thường/khoảng trắng)** | **Chuẩn hóa tự động:** `UPPER(TRIM(MA_KHOI))`. | Chuyển quarantine. | Lỗi định dạng đơn giản, chuẩn hóa xác định được 100% về khối gốc (`hs` $\to$ `HS`, `sv` $\to$ `SV`) mà không mất thông tin. |
| **Dòng bẩn loại 5 (Dòng trùng lặp cùng `ID`)** | **Khử trùng theo `ID` (Deduplicate), giữ 1 bản ghi đầu tiên.** | Giữ nguyên cả hai dòng. | Dòng trùng lặp có nội dung giống hệt nhau, khử trùng đảm bảo nguyên tắc mỗi bản ghi thẻ có ID duy nhất. |
| **Thẻ có `TRANG_THAI = 0`** | **Giữ trong Silver để tra cứu lịch sử thẻ cũ, nhưng LOẠI KHỎI phép tính tham gia.** | Xóa hẳn khỏi Silver. | Phục vụ truy vết `SO_THE_CU` khi cấp đổi thẻ. Đúng quy tắc: chỉ thẻ hiệu lực mới chứng minh quyền lợi BHYT. |

---

## 4. Đặc tả kiến trúc tầng dữ liệu Medallion

```
[Raw Parquet 200 chunks]
          │
          ▼
┌────────────────────────┐
│     BRONZE LAYER       │  --> Nạp nguyên trạng 30 cột + 4 cột kỹ thuật (_source_file, _chunk_id, _ingested_at, _batch_id)
└──────────┬─────────────┘
           │
     ┌─────┴─────────────────────────┐
     ▼                               ▼
┌────────────────────────┐    ┌────────────────────────┐
│      SILVER LAYER      │    │   SILVER QUARANTINE    │
│  - Ép kiểu chuẩn       │    │  - Dòng TU_NGAY >      │
│  - Khử trùng theo ID   │    │    DEN_NGAY            │
│  - Chuẩn hóa MA_KHOI   │    │  - Kèm lý do lỗi       │
│  - Gắn cờ chất lượng   │    └────────────────────────┘
└────────────────────────┘
```

### 4.1. Lớp Bronze
* **Mục tiêu:** Lưu trữ nguyên trạng bản sao dữ liệu nguồn, bổ sung siêu dữ liệu kỹ thuật để đảm bảo khả năng truy vết và nạp lại an toàn (Idempotent).
* **Cấu trúc:** 30 cột dữ liệu gốc + 4 cột kỹ thuật:
  * `_SOURCE_FILE`: Tên file gốc (ví dụ: `part-00000.parquet`).
  * `_CHUNK_ID`: Mã chunk tương ứng (`0` đến `199`).
  * `_INGESTED_AT`: Thời điểm nạp (Timestamp).
  * `_BATCH_ID`: Mã đợt nạp dữ liệu (UUID / Run ID).

### 4.2. Lớp Silver
* **Mục tiêu:** Dữ liệu đã làm sạch, chuẩn hóa kiểu dữ liệu, khử trùng lặp và gắn cờ chất lượng.
* **Cải tiến kiểu dữ liệu:**
  * `SO_SO_BHXH`: Lưu trữ dạng chuỗi 10 ký tự số (chuẩn định danh) và hỗ trợ chỉ mục số nguyên 64-bit khi truy vấn.
  * `TU_NGAY`, `DEN_NGAY`, `NGAY_SINH`, `NGAY_CAP`, `NGAY_HUY`, `NGAY_TAO`, `NGAY_CAP_NHAT`: Ép chuẩn `date32`.
* **Bổ sung cột chất lượng dữ liệu:**
  * `FLAG_NAME_NULL`: Boolean (True nếu `HO_TEN` bị null).
  * `FLAG_GENDER_INVALID`: Boolean (True nếu `GIOI_TINH` khác 1 và 2).
* **Phân vùng/Lưu trữ:** Phân chia theo chunk file đảm bảo tính độc lập dữ liệu theo từng dải cá nhân.

### 4.3. Lớp Silver Quarantine
* Lưu trữ các dòng vi phạm nguyên tắc toàn vẹn không thể suy đoán (`TU_NGAY > DEN_NGAY`).
* Bổ sung cột:
  * `QUARANTINE_REASON`: `TU_NGAY_LON_HON_DEN_NGAY`.
  * `QUARANTINE_AT`: Thời điểm đưa vào cách ly.

---

## 5. Nguyên tắc bảo toàn số dòng (Row Conservation)
Tại mỗi lần xử lý, hệ thống phải thỏa mãn phương trình bảo toàn tuyệt đối:
$$\text{Số dòng Bronze} = \text{Số dòng Silver} + \text{Số dòng Quarantine} + \text{Số dòng trùng đã khử (Deduplicated)}$$

Đồng thời, đối chiếu với nhật ký lỗi của generator (`dirty_log`):
* $\text{Số dòng Quarantine} = \text{Số dòng lỗi Loại 1 trong dirty\_log}$.
* $\text{Số dòng có FLAG\_NAME\_NULL} = \text{Số dòng lỗi Loại 2 trong dirty\_log}$.
* $\text{Số dòng có FLAG\_GENDER\_INVALID} = \text{Số dòng lỗi Loại 3 trong dirty\_log}$.
* $\text{Số dòng MA\_KHOI được viết hoa} = \text{Số dòng lỗi Loại 4 trong dirty\_log}$.
* $\text{Số dòng trùng đã khử} = \text{Số dòng lỗi Loại 5 trong dirty\_log}$.

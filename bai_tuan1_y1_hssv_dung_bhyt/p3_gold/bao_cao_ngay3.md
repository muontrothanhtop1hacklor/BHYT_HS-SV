# BÁO CÁO NGÀY 3: RÀ SOÁT TẦNG SILVER VÀ CHUẨN BỊ XUẤT KẾT QUẢ

**Dự án:** Xử lý dữ liệu BHYT 200M dòng (CV 835/QLT - Ý 1: HSSV dừng tham gia BHYT)  
**Nội dung trọng tâm:** Rà soát kiểm chứng tầng Silver, phân tích dữ liệu bẩn và hoàn thiện kiến trúc, kế hoạch xuất kết quả (chưa chạy Gold).

---

## 1. RÀ SOÁT VÀ KIỂM CHỨNG TOÀN VẸN TẦNG SILVER

### 1.1. Phương trình bảo toàn số dòng tuyệt đối
Đã đối soát toàn bộ 200 chunk dữ liệu giữa tầng Bronze và Silver, xác nhận bảo toàn dữ liệu chính xác 100%:
$$\text{Bronze } (195.305.908) = \text{Silver sạch } (194.526.132) + \text{Quarantine } (390.254) + \text{Trùng lặp } (389.522)$$
- **Chênh lệch:** $0$ dòng.
- Không có bất kỳ bản ghi nào bị thất thoát ngoài hai cơ chế xử lý: khử trùng ID (Loại 5) và cách ly lỗi ngày không hợp lệ (Loại 1).

### 1.2. Đối chiếu 5 loại lỗi với nhật ký lỗi gài sẵn (`dirty_log`)
Khớp chính xác số lượng từng loại dữ liệu bẩn được tiêm có chủ đích (~1% dữ liệu):
- **Loại 1 (Đảo ngày `TU_NGAY > DEN_NGAY`):** **390.254 dòng** $\rightarrow$ Cách ly vào `data/silver/quarantine/`, không để dữ liệu sai lệch đi vào tính toán.
- **Loại 2 (Họ tên `NULL`):** **389.918 dòng** $\rightarrow$ Giữ nguyên bản ghi, gắn cờ `_FLAG_NAME_NULL = True`.
- **Loại 3 (Giới tính ngoài `[1, 2]`):** **390.216 dòng** $\rightarrow$ Giữ nguyên bản ghi, gắn cờ `_FLAG_GENDER_INVALID = True`.
- **Loại 4 (Mã khối chữ thường/khoảng trắng):** **389.768 dòng** $\rightarrow$ Chuẩn hóa bằng `UPPER(TRIM(MA_KHOI))`, phục hồi đúng khối đối tượng.
- **Loại 5 (Trùng lặp khóa ID):** **389.522 dòng** $\rightarrow$ Khử trùng lặp trên Bronze, chỉ giữ lại 1 bản ghi duy nhất.

### 1.3. Phân tích nguyên nhân chênh lệch 131 người giữa Dữ liệu thô và Silver
Đã chạy script phân tích chuyên sâu đối chiếu nhóm chênh lệch với ground truth (`persons_gt`):
- **Bản chất 131 người:** 100% cá nhân này thuộc kịch bản chuyển khối (`SWITCH` từ HSSV sang Doanh nghiệp/Hộ gia đình tại tháng 08/2026).
- **Cơ chế gây lệch:** Thẻ mới tháng 08/2026 của họ bị lỗi Loại 1 (`TU_NGAY > DEN_NGAY`) nên bị đưa vào Quarantine. Khi tầng Silver sạch bị thiếu thẻ này, hệ thống coi họ là "dừng tham gia BHYT" $\rightarrow$ tạo ra **Dương tính giả (False Positive)**.
- **Quyết định nghiệp vụ:** Trong môi trường thực tế, dữ liệu thẻ BHYT không được tự ý hoán đổi hay sửa ngày khi chưa có xác nhận từ cơ quan BHXH phát hành. Do đó, việc duy trì cách ly vào **Quarantine** bảo đảm tính tuân thủ pháp lý và quản trị dữ liệu (Data Governance) cao nhất.

---

## 2. CÔNG TÁC CHUẨN BỊ CHO TẦNG XUẤT KẾT QUẢ (GOLD)

### 2.1. Kế hoạch và thiết kế hai bảng đầu ra chuẩn DDL
Đã xây dựng kế hoạch chi tiết cho tầng Gold với 2 bảng đầu ra tuân thủ cấu trúc DDL:
1. **Bảng chi tiết cá nhân (`BC_HSSV_DUNG_THAM_GIA`):** 14 cột nghiệp vụ (`SO_SO_BHXH`, `HO_TEN`, `NGAY_SINH`, `GIOI_TINH`, `SO_CMND`, `SO_THE_KCB_GOC`, `MA_KHOI_GOC`, `TU_NGAY_GOC`, `DEN_NGAY_GOC`, `DM_BHXH_ID`, `MA_TINH`, `NGAY_GOC`, `NGAY_KIEM_TRA`, `CREATED_AT`).
2. **Bảng thống kê địa bàn (`TK_DBHC_HSSV_DUNG_THAM_GIA`):** 6 cột tổng hợp theo 63 tỉnh/thành phố (`MA_TINH`, `TEN_TINH`, `SO_LUONG_HS_DUNG`, `SO_LUONG_SV_DUNG`, `TONG_SO_NGUOI_DUNG`, `NGAY_BAO_CAO`), quy đổi thông qua danh mục `DM_BHXH` (xử lý `MA_CHA` đệ quy).

### 2.2. Tham số hóa và thiết kế tính Idempotent
- **Tham số hóa nghiệp vụ linh hoạt:**
  - Mốc gốc: `base_start = 2024-10-01`, `base_next = 2024-11-01`.
  - Mốc kiểm tra: `chk_start = 2026-08-01`, `chk_next = 2026-09-01`.
  - Định nghĩa dừng (`stop_def`): Hỗ trợ cả 2 định nghĩa `any` (dừng mọi khối) và `hssv` (chỉ dừng ở khối HSSV).
- **Cơ chế Idempotent (chạy lại cho kết quả giống hệt nhau):** Thiết kế ghi file nguyên tử (Atomic write: ghi file `.tmp` $\rightarrow$ atomic rename) kèm băm SHA-256 để kiểm chứng tính toàn vẹn byte-for-byte khi tái thực thi.

---

## 3. CHỐT CẤU TRÚC REPO THEO BÀI / PHẦN

Đã tổ chức lại toàn bộ repository từ mô hình phân loại theo chức năng sang mô hình **BÀI / PHẦN**, tạo điều kiện mở rộng nhiều bài toán độc lập:
- **`common/`:** Cấu hình chung (`config.py`), bộ công cụ sinh dữ liệu (`gen_bhyt.py`, `gen_bhyt_script1.py`), xác thực và xuất Ground Truth (`validate_bhyt.py`).
- **`bai_ram_1_10_100m/`:** Module đo lường tài nguyên và giám sát RSS cây tiến trình cha/con (`resource_monitor.py`).
- **`bai_tuan1_y1_hssv_dung_bhyt/`:** Toàn bộ nội dung của bài Tuần 1 phân theo 5 phần:
  - `p1_du_lieu/`: DDL bảng thô, kiểm tra chất lượng schema dữ liệu nguồn.
  - `p2_bronze_silver/`: Pipelines Bronze, Silver, phân tích 131 người, 5 test quy tắc dòng bẩn.
  - `p3_gold/`: Logic nghiệp vụ lõi (`gold_logic.py`), kế hoạch Gold, bộ test 20 ca biên và 15 ca bất biến.
  - `p4_giai_phap_a_b/`: Tách biệt mã nguồn và kịch bản chạy độc lập của Bạn A (PyArrow Streaming) và Bạn B (DuckDB SQL).
  - `p5_doi_soat/`: Module đối soát chéo kết quả giữa Bạn A, Bạn B, SCENARIO và kiểm chứng DuckDB SQL thuần.

---

## 4. CHUẨN BỊ ĐỊNH DẠNG FILE KẾT QUẢ ĐỐI SOÁT VỚI BẠN CÙNG LÀM

Đã thống nhất đặc tả kỹ thuật file đầu ra để phục vụ việc ghép nối và đối soát chéo độc lập giữa hai bạn:
1. **File chi tiết cá nhân:** Định dạng Parquet, nén `zstd`, chuẩn hóa kiểu dữ liệu khóa `SO_SO_BHXH` (dạng chuỗi ký tự) để thực hiện đối soát tập hợp chính xác qua phép trừ tập hợp ($A \setminus B = \emptyset$ và $B \setminus A = \emptyset$).
2. **File tổng hợp thống kê:** Định dạng CSV chuẩn UTF-8, mã tỉnh `MA_TINH` chuẩn hóa 2-3 ký tự có số 0 ở đầu (zero-padding), sắp xếp theo mã tỉnh để so sánh khớp từng dòng.
3. **Kịch bản đối soát tự động:** Xây dựng sẵn script `compare_results.py` so sánh trực tiếp số lượng bản ghi, cơ cấu khối HS/SV, sự trùng khớp 100% của danh sách cá nhân và bảng số liệu 63 tỉnh/thành phố.

---

## 5. KẾT LUẬN & KẾ HOẠCH BƯỚC TIẾP THEO

- **Kết quả Ngày 3:** Đã hoàn thành 100% việc rà soát tầng Silver, đóng dứt điểm câu hỏi về 131 người chênh lệch, chốt kiến trúc cấu trúc thư mục repo và chuẩn bị đầy đủ quy chuẩn xuất kết quả tầng Gold.
- **Kế hoạch Ngày 4:** Thực thi chính thức pipeline Gold, đối soát chéo kết quả Bạn A vs Bạn B và đóng gói nghiệm thu toàn bộ bài toán Tuần 1.

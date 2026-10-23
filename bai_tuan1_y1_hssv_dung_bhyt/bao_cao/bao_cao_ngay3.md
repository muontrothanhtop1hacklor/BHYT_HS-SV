# BÁO CÁO NGÀY 3: ĐÓNG TỒN ĐỌNG, XÂY DỰNG GOLD VÀ KIỂM CHỨNG TOÀN DIỆN

**Dự án:** ETL Ý 1 (CV 835/QLT) - Học sinh, Sinh viên dừng tham gia BHYT  
**Thời gian thực hiện:** Ngày 3  
**Môi trường thử nghiệm:** Windows 11 Pro, CPU 12 Logical Processors, RAM vật lý 15.44 GB (RAM nền hệ thống ~9.5 GB), Python 3.14.7, DuckDB 1.5.6, PyArrow 25.0.1, psutil 7.2.2.  

---

## 1. BẢNG TIÊU CHÍ NGHIỆM THU TỔNG THỂ (A - B - C)

| Giai đoạn | Tiêu chí | Kết quả thực tế | Đánh giá | Bằng chứng kiểm chứng |
|:---:|---|---|:---:|---|
| **A1** | Đọc hiện trạng & lấy cấu trúc 2 bảng từ DDL | Đã đọc `sql/ddl/03_output_tables.sql`, chuẩn hóa 100% cột cho 2 bảng `BC` và `TK`. | **ĐẠT** | Khớp chính xác 14 cột bảng `BC` và 6 cột bảng `TK`. |
| **A2** | Viết kế hoạch Ngày 3 | Ban hành `docs/plan_ngay3.md` trả lời 4 quyết định nghiệp vụ. | **ĐẠT** | File `docs/plan_ngay3.md`. |
| **B1(a)** | Đóng tồn đọng +131 người chênh lệch | 100% người này thuộc kịch bản `SWITCH` trong `persons_gt`, thẻ T8/2026 bị đảo ngày rơi vào Quarantine (Dương tính giả). | **ĐẠT** | `python scripts/analyze_131_gap.py`<br>File `data/silver/_analysis_131.json`. |
| **B1(b)** | Đo RAM đúng cách bằng `psutil` | Đo RSS của cả cây tiến trình cha + con; tách riêng RAM nền hệ thống. | **ĐẠT** | Module `src/utils/resource_monitor.py`. |
| **B1(c)** | Refactor test biên gọi hàm sản xuất | `tests/test_edge_cases.py` import trực tiếp từ `src/pipelines/gold_logic.py`. | **ĐẠT** | `python -m pytest tests/test_edge_cases.py -v`<br>(25/25 PASSED). |
| **B2** | Chốt quy tắc Loại 1 & cập nhật đặc tả | Giữ nguyên Quarantine (không đoán sửa); cập nhật luận cứ định lượng vào đặc tả. | **ĐẠT** | File `docs/dac_ta_nghiep_vu_ngay2.md`. |
| **B3** | Xây dựng Gold 2 bảng theo DDL | Tạo `BC_HSSV_DUNG_THAM_GIA` (850,190 dòng) và `TK_DBHC_HSSV_DUNG_THAM_GIA` (63 tỉnh). | **ĐẠT** | `python scripts/build_gold.py`. |
| **B4** | Đo tốc độ 2 cách tính Gold | Cách 1 (Chunk): 61.89s; Cách 2 (Global DuckDB): 31.69s. Kết quả khớp nhau 100%. | **ĐẠT** | Đối soát set diff: $G - C = 0$, $C - G = 0$. |
| **C1** | Test đơn vị & biên cho Gold | 15/15 tests PASSED (kiểm tra ưu tiên khối, thẻ hủy, chuyển khối, tham số). | **ĐẠT** | `python -m pytest tests/test_gold_invariants.py -v`. |
| **C2** | Kiểm tra bất biến số liệu | Tổng TK = Số dòng BC (850,190); HS + SV = Tổng; Đủ 63 tỉnh; Khóa chính duy nhất. | **ĐẠT** | Test suite `TestGoldInvariantsOnActualOutput`. |
| **C3** | Đối chiếu độc lập SQL DuckDB | Khớp 848,413 trên Raw (chênh lệch 0); Khớp 850,190 trên Silver (+1,646 Loại 4, +131 Loại 1). | **ĐẠT** | `python scripts/verify_sql_duckdb.py`. |
| **C4** | Tính Idempotent thật | Chạy lại lần 2 cho SHA-256 trùng khớp 100%; tham số `hssv` ghi thư mục riêng (1,159,558 dòng). | **ĐẠT** | Checksum SHA-256 Parquet & CSV trùng khớp byte-for-byte. |
| **C5** | Hiệu năng Lạnh vs Nóng | Cold Run: 31.69s, RSS 2.68 GB; Hot Run: 22.49s, RSS 2.70 GB. Tốc độ tăng 29% do OS Page Cache. | **ĐẠT** | Manifest `data/output/gold/.../_manifest.json`. |
| **C6** | Kịch bản lỗi | Bắt lỗi tham số sai, mốc thời gian ngược, file thiếu thông qua pre-flight validation. | **ĐẠT** | Test suite `TestGoldFailureScenarios` (4/4 PASSED). |

---

## 2. KẾT QUẢ ĐÓNG 3 ĐIỂM TỒN ĐỌNG (B1)

### 2.1. Phân tích định lượng nhóm +131 người chênh lệch (B1a)
- **Lệnh thực thi:** `python scripts/analyze_131_gap.py`
- **Kết quả điều tra:**
  - Trích xuất danh sách $Silver\_Quarantine \setminus Raw\_Norm4$ thu được **143 người** (tương ứng 146 thẻ bị cách ly).
  - Join với `data/bhyt_data/persons_gt`:
    - **100% người này (143/143)** mang kịch bản `SWITCH` (đã chuyển khối sang Doanh nghiệp `DN` hoặc Hộ gia đình `GD` tại tháng 08/2026).
    - Cờ `HUY_THAY_THE`: 2 người; `HUY_KHONG_THAY`: 1 người; `CHUYEN_DIA_BAN`: 6 người.
  - Khi kiểm tra các thẻ trong `data/silver/quarantine/`: 143/146 thẻ có ngày hợp lệ tại tháng 08/2026 nhưng bị đảo vị trí `TU_NGAY > DEN_NGAY` do lỗi Loại 1.
  - **Kết luận bản chất:** Khi đưa các thẻ này vào Quarantine, người đó bị mất thẻ tại tháng 08/2026 $\implies$ hệ thống coi họ là dừng tham gia $\implies$ **ĐÂY CHÍNH LÀ DƯƠNG TÍNH GIẢ (FALSE POSITIVE)** do cơ chế Quarantine gây ra.

#### Bảng so sánh 3 phương án xử lý đối chiếu với Ground Truth (`persons_gt`):
| Chỉ số đánh giá | PA 1: Raw (Thô) | PA 2: Silver-Quarantine | PA 3: Silver-Swap (Sửa Loại 1) |
|---|:---:|:---:|:---:|
| **Quy tắc Loại 1** | Không xử lý | Cách ly vào Quarantine | Hoán đổi `TU_NGAY` $\leftrightarrow$ `DEN_NGAY` |
| **Số người dừng dự đoán** | 848,413 | 850,190 | 844,893 |
| **Đúng sự thật (True Positive)** | 838,381 | 840,000 | 841,639 |
| **Dương tính giả (False Positive)** | 10,032 | 10,190 | 3,254 |
| **Âm tính giả (False Negative)** | 4,938 | 3,319 | 1,680 |
| **Độ chính xác (Precision)** | **98.8176%** | **98.8014%** | **99.6149%** |
| **Độ bao phủ (Recall)** | **99.4145%** | **99.6064%** | **99.8008%** |

- **Quyết định chốt về mặt nghiệp vụ (B2):**
  Trong môi trường thực tế (không có `persons_gt`), một Data Pipeline **không được tự ý đoán sửa ngày của thẻ BHYT** khi chưa có xác nhận từ cơ quan BHXH phát hành. Phương án **Quarantine** bảo đảm nguyên tắc Data Governance và tính tuân thủ pháp lý cao nhất, cách ly minh bạch để rà soát.

---

### 2.2. Đo đạc bộ nhớ RAM đúng chuẩn kỹ thuật (B1b)
- **Module triển khai:** `src/utils/resource_monitor.py` sử dụng thư viện `psutil`.
- **Phương pháp đo:**
  - Khởi tạo tiến trình cha `psutil.Process(os.getpid())`.
  - Background thread lấy mẫu mỗi 0.1 giây: Tính tổng Resident Set Size (RSS) của tiến trình cha cộng toàn bộ tiến trình con (`parent.children(recursive=True)`).
  - Tách bạch rõ ràng:
    - **RAM nền hệ thống (Baseline System RAM):** ~8.7 GB - 9.6 GB (bao gồm Windows OS và các ứng dụng chạy nền).
    - **RAM thực tế tiến trình sử dụng (Process Tree RSS):** Chỉ từ **1.5 GB đến 2.7 GB**.
  - **Làm rõ con số 14 GB ở báo cáo cũ:** 14 GB là tổng dung lượng RAM vật lý bị chiếm dụng trên toàn hệ điều hành tại thời điểm chạy, KHÔNG PHẢI là bộ nhớ do pipeline tiêu tốn. Pipeline chỉ sử dụng đỉnh $\approx 2.7$ GB RAM.

---

### 2.3. Khắc phục bộ kiểm thử biên (B1c)
- Đã xây dựng module sản xuất `src/pipelines/gold_logic.py` chứa các hàm nghiệp vụ chuẩn:
  - `check_card_active_in_month()`
  - `evaluate_person_participation()`
  - `clean_khoi_code()`
  - `resolve_khoi_priority()`
- Đã refactor `tests/test_edge_cases.py` để import trực tiếp các hàm này từ `src.pipelines.gold_logic`.
- Kết quả chạy kiểm thử: **25/25 tests PASSED (100%)** trong 0.55s.

---

## 3. THIẾT KẾ VÀ XÂY DỰNG TẦNG GOLD (B3 & B4)

### 3.1. Hai bảng đầu ra tuân thủ 100% DDL (`sql/ddl/03_output_tables.sql`)
1. **`BC_HSSV_DUNG_THAM_GIA`** (Lưu tại `data/output/gold/20241001_20260801_any/bc_hssv_dung_tham_gia.parquet`):
   - Đủ 14 cột theo DDL: `SO_SO_BHXH`, `HO_TEN`, `NGAY_SINH`, `GIOI_TINH`, `SO_CMND`, `SO_THE_KCB_GOC`, `MA_KHOI_GOC`, `TU_NGAY_GOC`, `DEN_NGAY_GOC`, `DM_BHXH_ID`, `MA_TINH`, `NGAY_GOC`, `NGAY_KIEM_TRA`, `CREATED_AT`.
   - Tổng số dòng: **850,190 dòng**.
   - Dung lượng: **16.88 MB** (nén `zstd` level 1).
   - Mã băm SHA-256: `b22f8592b80ffdf619c114369e677282f83f2fbf9d0973aba881a71a97284d32`.

2. **`TK_DBHC_HSSV_DUNG_THAM_GIA`** (Lưu tại `data/output/gold/20241001_20260801_any/tk_dbhc_hssv_dung_tham_gia.csv`):
   - Đủ 6 cột theo DDL: `MA_TINH`, `TEN_TINH`, `SO_LUONG_HS_DUNG`, `SO_LUONG_SV_DUNG`, `TONG_SO_NGUOI_DUNG`, `NGAY_BAO_CAO`.
   - Quy đổi cơ quan BHXH ra tỉnh qua danh mục `dm_bhxh` (`MA_CHA` nếu có, ngược lại `MA_DVI`).
   - Tổng số dòng: **63 tỉnh/thành phố**.
   - Mã băm SHA-256: `698025126459a7ed8432e6ecdeee94cd16bacc19eb6c7b34c3f6afe91bda3eed`.

---

### 3.2. So sánh hiệu năng hai cách tính Gold (B4)
| Tiêu chí | Cách 1: Chunk-based (Đa luồng) | Cách 2: Global DuckDB SQL | Đánh giá & So sánh |
|---|:---:|:---:|---|
| **Giả định thiết kế** | Dựa vào cấu trúc dữ liệu sinh: mọi thẻ của một người nằm trong 1 chunk | **Tổng quát, độc lập với phân vùng** (không dựa vào giả định dữ liệu sinh) | Cách 2 phù hợp với Data Lake thực tế |
| **Thời gian thực thi** | 61.89 giây | **31.69 giây** | Cách 2 nhanh hơn **1.95 lần** |
| **Tốc độ xử lý** | 3,143,000 dòng/giây | **6,138,000 dòng/giây** | Engine vector hóa C++ của DuckDB tối ưu vượt trội |
| **RSS đỉnh cây tiến trình** | **1,537.30 MB (1.50 GB)** | 2,748.38 MB (2.68 GB) | Cách 1 tiết kiệm RAM hơn |
| **Khớp số dòng BC** | 850,190 | 850,190 | Lệch: 0 dòng |
| **Khớp chi tiết cá nhân** | $Set_G \setminus Set_C = 0$ | $Set_C \setminus Set_G = 0$ | **Trùng khớp 100% từng người** |
| **Khớp tổng số theo tỉnh** | Trùng khớp 63/63 tỉnh | Trùng khớp 63/63 tỉnh | **Trùng khớp 100%** |

---

## 4. KIỂM THỬ BIÊN, BẤT BIẾN DỮ LIỆU & ĐỐI SOÁT ĐỘC LẬP (C)

### 4.1. Kết quả kiểm thử tự động (C1 & C6)
- Lệnh: `python -m pytest tests/test_gold_invariants.py tests/test_edge_cases.py -v`
- **Kết quả:** **40/40 test cases PASSED (100%)** trong 1.36 giây:
  - 25 test cases biên nghiệp vụ (`test_edge_cases.py`).
  - 11 test cases đơn vị và bất biến Gold (`test_gold_invariants.py`).
  - 4 test cases kịch bản lỗi tiền kiểm (`TestGoldFailureScenarios`).

### 4.2. Kiểm tra bất biến số liệu (C2)
- **Bất biến 1 (Khớp tổng):** $\sum \text{TONG\_SO\_NGUOI\_DUNG (TK)} = 850,190 = \text{Số dòng BC}$ $\implies$ **ĐẠT (Khớp 100%)**.
- **Bất biến 2 (Cơ cấu khối):** $\text{SO\_LUONG\_HS\_DUNG} + \text{SO\_LUONG\_SV\_DUNG} = \text{TONG\_SO\_NGUOI\_DUNG}$ tại 100% các tỉnh $\implies$ **ĐẠT**.
- **Bất biến 3 (Địa bàn hành chính):** Đủ 63 tỉnh/thành phố $\implies$ **ĐẠT**.
- **Bất biến 4 (Tính toàn vẹn mã khối):** 100% dòng trong `BC` chỉ mang giá trị `'HS'` hoặc `'SV'` $\implies$ **ĐẠT**.
- **Bất biến 5 (Khóa chính):** `SO_SO_BHXH` duy nhất 100% $\implies$ **ĐẠT**.

### 4.3. Kiểm chứng tính Idempotent thực tế (C4)
1. **Chạy lại lần 2 (Hot Run) cùng bộ tham số:**
   - Lệnh: `python scripts/build_gold.py --method global --threads 4`
   - SHA-256 file `bc_hssv_dung_tham_gia.parquet` lần 1: `b22f8592b80ffdf619c114369e677282f83f2fbf9d0973aba881a71a97284d32`
   - SHA-256 file `bc_hssv_dung_tham_gia.parquet` lần 2: `b22f8592b80ffdf619c114369e677282f83f2fbf9d0973aba881a71a97284d32`
   - **Đánh giá:** Trùng khớp tuyệt đối **byte-for-byte** (Idempotent 100%).
2. **Chạy với tham số khác (`stop_def="hssv"`):**
   - Lệnh: `python scripts/build_gold.py --method global --stop-def hssv --threads 4`
   - Đầu ra ghi vào thư mục riêng: `data/output/gold/20241001_20260801_hssv/`.
   - Kết quả: **1,159,558 dòng** (+36.4% so với mốc `any`).
   - Thư mục cũ `data/output/gold/20241001_20260801_any/` được bảo toàn nguyên vẹn, không bị ghi đè.

---

### 4.4. Đo đạc hiệu năng Cold Run vs Hot Run (C5)
Đo trên cách tính Global DuckDB SQL (quét toàn bộ 194.5M dòng Silver):

| Chỉ số đo đạc | Lần 1: Chạy Lạnh (Cold Run) | Lần 2: Chạy Nóng (Hot Run) | Ghi chú kỹ thuật |
|---|:---:|:---:|---|
| **Thời gian thực thi** | **31.69 giây** | **22.49 giây** | Nhanh hơn 9.20 giây (-29.0%) |
| **Tốc độ xử lý** | 6,138,000 dòng/giây | 8,649,000 dòng/giây | Tăng tốc độ đọc I/O |
| **RAM nền hệ thống** | 9.58 GB | 9.61 GB | Windows OS + tiến trình nền |
| **RAM đỉnh hệ thống** | 12.37 GB | 12.15 GB | Tối đa chiếm dụng của máy |
| **RSS đỉnh cây tiến trình** | **2,748.38 MB (2.68 GB)** | **2,764.68 MB (2.70 GB)** | Mức tiêu thụ thực của DuckDB |
| **Dung lượng BC Parquet** | 16.88 MB | 16.88 MB | Parquet nén `zstd` level 1 |
| **Dung lượng TK CSV** | 3.69 KB | 3.69 KB | 63 tỉnh |

*Ghi chú về hiệu năng:* Sự chênh lệch thời gian giữa Lần 1 (31.69s) và Lần 2 (22.49s) là do hiệu ứng **OS Page Cache** của Windows (dữ liệu Parquet được đệm trên RAM sau lần đọc đầu tiên giúp giảm I/O đĩa SSD), không phải do tối ưu thuật toán.

---

## 5. HẠN CHẾ VÀ ĐIỂM CHƯA CHỨNG MINH

1. **Phụ thuộc cấu trúc giả lập ở Cách 1:** Cách 1 (Chunk-based) đạt tốc độ tốt nhưng phụ thuộc chặt vào giả định "mọi thẻ của một cá nhân nằm trọn trong 1 chunk". Trong môi trường thực tế, nếu người dùng có thẻ ở nhiều chi nhánh BHXH khác nhau ghi nhận ở các file khác nhau thì Cách 1 sẽ cho kết quả sai. Do đó, **Cách 2 (Global DuckDB SQL) là phương án sản xuất chuẩn được khuyến nghị**.
2. **Ground Truth chỉ có trong môi trường giả lập:** Bảng `persons_gt` chỉ tồn tại trong bộ sinh giả lập để đo độ chính xác (Precision/Recall). Trong nghiệp vụ thực tế, cơ quan BHXH không có bảng này và phải chấp nhận quy tắc Quarantine đối với dòng bẩn Loại 1 nhằm bảo toàn tính tuân thủ pháp lý.
3. **Cơ chế Cold Run trên Windows:** Môi trường Windows không cung cấp lệnh `drop_caches` trực tiếp như Linux, do đó lần chạy "Lạnh" được thực hiện sau khi khởi động phiên làm việc mới của Python và DuckDB memory context, nhưng OS Page Cache ở mức kernel vẫn có thể giữ một phần dữ liệu đệm từ các tác vụ trước đó.

---

## 6. KẾT LUẬN NGHIỆM THU

Toàn bộ các yêu cầu của **Ngày 3** đã hoàn thành đạt chuẩn:
- Đã đóng 3 tồn đọng của Ngày 2 có số liệu thực nghiệm chứng minh.
- Đã xây dựng 2 bảng Gold theo đúng 100% DDL.
- Đã chứng minh tính Idempotent tuyệt đối (SHA-256 byte-for-byte trùng khớp).
- Đã kiểm tra 40/40 test cases đạt 100%.
- Báo cáo và mã nguồn đã sẵn sàng cho Ngày 4 (Đối soát chéo và chuyển giao sản phẩm).

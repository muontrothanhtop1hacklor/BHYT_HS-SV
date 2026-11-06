# BÁO CÁO KỸ THUẬT & TỔNG KẾT KẾT QUẢ THỰC TẬP KỸ SƯ DỮ LIỆU

| Thông tin quản lý | Nội dung chi tiết |
| :--- | :--- |
| **Mã tài liệu** | `RPT-DE-INTERN-2026` |
| **Loại tài liệu** | Báo cáo tổng kết kết quả thực hiện, kiểm toán dữ liệu, phân tích kỹ thuật (RCA) & đề xuất nghiệp vụ |
| **Kỳ báo cáo** | `07/09/2026` – `05/11/2026` (09 tuần) |
| **Phạm vi hệ thống** | `pyspark-course` (`spark introduce learn`), `etl_course` (`etl_learn`), `BHYT_HS-SV` (`200m`) |
| **Hạ tầng thực thi** | Windows 11 Pro (12 Logical Cores, 16 GB RAM); Docker Engine (Spark, Airflow, Kafka KRaft, MinIO, Nessie) |
| **Công nghệ cốt lõi** | Python 3.11/3.14, PySpark 3.5/4.0, DuckDB 1.5, PyArrow 25.0, Numba 0.61, Apache Iceberg, PostgreSQL 16 |

---

## MỤC LỤC

1. [Tóm tắt điều hành & Chỉ số nghiệm thu tổng thể](#1-tóm-tắt-điều-hành--chỉ-số-nghiệm-thu-tổng-thể)
2. [Ma trận tiến độ & Danh mục sản phẩm bàn giao](#2-ma-trận-tiến-độ--danh-mục-sản-phẩm-bàn-giao)
3. [Báo cáo kết quả chuyên môn & Thực nghiệm kỹ thuật](#3-báo-cáo-kết-quả-chuyên-môn--thực-nghiệm-kỹ-thuật)
   - [3.1. Hệ thống 1: Xử lý phân tán PySpark, Streaming & Lakehouse (`pyspark-course`)](#31-hệ-thống-1-xử-lý-phân-tán-pyspark-streaming--lakehouse-pyspark-course)
   - [3.2. Hệ thống 2: Pipeline Medallion Quá trình tham gia BHXH (`etl_course`)](#32-hệ-thống-2-pipeline-medallion-quá-trình-tham-gia-bhxh-etl_course)
   - [3.3. Hệ thống 3: Phân tích 200M dòng thẻ BHYT & Thiết kế Hệ thống API (`BHYT_HS-SV`)](#33-hệ-thống-3-phân-tích-200m-dòng-thẻ-bhyt--thiết-kế-hệ-thống-api-bhyt_hs-sv)
4. [Phân tích nguyên nhân gốc rễ (RCA) các vấn đề phát sinh](#4-phân-tích-nguyên-nhân-gốc-rễ-rca-các-vấn-đề-phát-sinh)
5. [Báo cáo kiểm toán dữ liệu & Danh mục công việc tồn đọng (Backlog)](#5-báo-cáo-kiểm-toán-dữ-liệu--danh-mục-công-việc-tồn-đọng-backlog)
6. [Danh mục câu hỏi nghiệp vụ & Kiến nghị phê duyệt](#6-danh-mục-câu-hỏi-nghiệp-vụ--kiến-nghị-phê-duyệt)

---

## 1. TÓM TẮT ĐIỀU HÀNH & CHỈ SỐ NGHIỆM THU TỔNG THỂ

Trong kỳ thực tập 09 tuần (`07/09/2026` – `05/11/2026`), công việc được triển khai xuyên suốt qua 03 kho mã nguồn độc lập, đáp ứng lộ trình từ chuẩn hóa nền tảng xử lý dữ liệu phân tán đến xây dựng hệ thống phân tích dữ liệu lớn quy mô 200 triệu bản ghi và đặc tả thiết kế hệ thống cấp sản xuất (Production-grade Design).

### Bảng 1.1. Tổng hợp các chỉ số kỹ thuật cốt lõi đạt được

| Hạng mục / Hệ thống | Quy mô dữ liệu xử lý | Chỉ số chất lượng / Độ chính xác | Hiệu năng thực thi & Tài nguyên | Mức độ hoàn thành |
| :--- | :--- | :--- | :--- | :---: |
| **1. `pyspark-course`**<br>*(22 chuyên đề thực nghiệm)* | `100K` $\to$ `100.000.000` bản ghi<br>(`167` phân vùng Parquet) | Khớp 100% Parity Batch–Streaming;<br>Bảo toàn 100% bản ghi qua Quarantine | Tập `1M`: `34,0s` \| Tập `10M`: `315,0s`<br>Pandas UDF tăng tốc `2,96x` so với Python UDF | **22 / 22 bài**<br>(100%) |
| **2. `etl_course`**<br>*(Pipeline QTTG BHXH)* | Master: `142.857` dòng<br>Detail: `1.000.000` dòng | `ERROR_ROWS = 0` trên 4 điều kiện Data Contract;<br>Bảo toàn: `169.658` Valid + `830.342` Quarantine | Điều phối tự động qua Airflow DAG (`0 2 * * 1`) & Spark Cluster | **5 / 5 tầng**<br>(100%) |
| **3. `BHYT_HS-SV` — Ý 1**<br>*(CV 835: HSSV dừng BHYT)* | `195.305.908` dòng thẻ<br>(`20.000.000` đối tượng, `200` chunks) | Khớp 100% đáp án chuẩn (`848.413` đối tượng);<br>`44 / 44` bài kiểm thử tự động đạt | Global DuckDB SQL: `31,69s` (Cold) / `22,49s` (Hot);<br>Đỉnh RAM tiến trình: `1,50 – 2,68 GB` | **Hoàn thành**<br>(100%) |
| **4. `BHYT_HS-SV` — Ý 2**<br>*(CV 835: Gián đoạn $\ge 90$ ngày)* | `194.526.132` dòng thẻ sạch<br>(Cửa sổ quan sát `669` ngày) | Khớp 100% đối soát SQL độc lập (`242.290` đối tượng);<br>`20 / 20` bài kiểm thử tự động đạt | Thời gian chạy 200 chunks: `247,89s`;<br>Đỉnh RAM tiến trình: `1.073,68 MB` (`~1,05 GB`) | **Hoàn thành**<br>(100%) |
| **5. `BHYT_HS-SV` — Thiết kế**<br>*(System & API Design)* | `10` bảng vật lý (`200M` dòng Silver, `1,09M` dòng Serving DB) | Đồng bộ 100% giữa đặc tả Markdown & Excel;<br>Bao phủ `32` kịch bản Unit Test & `15` mã kiểm tra | Thiết kế đáp ứng SLA `p95 <= 150ms – 300ms` cho `06` RESTful APIs | **02 bộ hồ sơ**<br>(`BD` & `DD`) |

---

## 2. MA TRẬN TIẾN ĐỘ & DANH MỤC SẢN PHẨM BÀN GIAO

### Bảng 2.1. Phân bổ hạng mục thực hiện theo kỳ báo cáo

| Giai đoạn | Thời gian | Hệ thống mục tiêu | Hạng mục công việc triển khai | Sản phẩm bàn giao (Deliverables) | Mã tham chiếu Git |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **Tuần 01** | `07/09 – 13/09` | `pyspark-course` | Thiết lập hạ tầng container (Docker, MinIO, Hadoop Winutils, Conda); triển khai Lakehouse cơ bản & điều phối Airflow. | Bài thực hành `00`, `00b`, `01`, `02-orders-lakehouse`, `03-airflow-orchestration`. | `606d4bf`..`3799d59` |
| **Tuần 02** | `14/09 – 20/09` | `etl_course` | Thiết kế và lập trình pipeline Medallion cho nghiệp vụ Quá trình tham gia BHXH 1M dòng; tích hợp kiểm định tự động. | `bronze_qttg.py`, `silver_qttg.py`, `gold_qttg.py`, `validate_qttg.py`, `dag_qttg_bronze_silver_gold.py`. | `c3e6645`..`04d9faa` |
| **Tuần 03** | `21/09 – 27/09` | `pyspark-course` | Thực nghiệm quản trị kiểu dữ liệu, phép kết nối bảng, hàm cửa sổ, tối ưu hóa phân vùng vật lý và đánh giá hiệu năng UDF. | Bài thực hành `04` đến `10`; Báo cáo đo kiểm phân vùng & Benchmark 1M dòng. | `6cbb84e`..`f61b3f2` |
| **Tuần 04** | `28/09 – 04/10` | `pyspark-course` | Xây dựng luồng xử lý thời gian thực với Kafka KRaft và Spark Structured Streaming; kiểm nghiệm cơ chế chịu lỗi. | Bài thực hành `11` đến `16`; Pipeline Multi-Sink kết hợp Dead-Letter Queue (DLQ). | `c40f809`..`5154336` |
| **Tuần 05** | `05/10 – 11/10` | `pyspark-course` | Phát triển bộ sinh dữ liệu `synthetic_bhxh` quy mô 100M dòng; thử nghiệm tràn đĩa (Spill-to-Disk) và bảng Iceberg/Nessie. | Module `synthetic_bhxh`, `resume_100M.py`; Bài thực hành `17` đến `21`; Custom Airflow-Spark Dockerfile. | `b1da665`..`5d941d3` |
| **Tuần 06** | `12/10 – 18/10` | `BHYT_HS-SV` | Xây dựng bộ sinh `gen_bhyt.py` (200M dòng); triển khai pipeline Bronze–Silver–Gold giải quyết Ý 1 Công văn 835/QLT. | [`common/data_gen/`](common/data_gen/README.md), [`bai_tuan1_y1_hssv_dung_bhyt/`](bai_tuan1_y1_hssv_dung_bhyt/README.md), 04 báo cáo kỹ thuật & 44 bài test. | `7f09a6b`..`384a89a` |
| **Tuần 07** | `19/10 – 25/10` | `BHYT_HS-SV` | Thiết kế giải thuật hợp nhất khoảng thời gian (Interval Merging) và triển khai pipeline tầng Gold giải quyết Ý 2 Công văn 835/QLT. | [`bai_tuan2_y2_hssv_gian_doan/`](bai_tuan2_y2_hssv_gian_doan/README.md), [`bao_cao_giai_phap_y2.md`](bai_tuan2_y2_hssv_gian_doan/bao_cao/bao_cao_giai_phap_y2.md) & 20 bài test. | `26c1791`..`66fbb9b` |
| **Tuần 08** | `26/10 – 01/11` | `BHYT_HS-SV` | Đặc tả kiến trúc hệ thống Batch–Serving và thiết kế cổng dịch vụ 06 RESTful APIs phục vụ khai thác báo cáo BHYT HSSV. | Hồ sơ [`ThietKeCoBan_BasicDesign_VN`](design/ThietKeCoBan_BasicDesign_VN.md) (15 sheets) & [`ThietKeChiTiet_DetailDesign_VN`](design/ThietKeChiTiet_DetailDesign_VN.md) (11 sheets). | `86dc952`..`08fbb20` |
| **Tuần 09** | `02/11 – 05/11` | Liên hệ thống | Kiểm toán tính toàn vẹn dữ liệu vật lý trên cả 03 dự án, chuẩn hóa hồ sơ tài liệu và lập báo cáo tổng kết giai đoạn. | `BAO_CAO_TONG_KET_THUC_TAP.md`, đồng bộ chỉ số nghiệm thu trên 03 kho mã nguồn. | `3801dd2` / Hiện tại |

---

## 3. BÁO CÁO KẾT QUẢ CHUYÊN MÔN & THỰC NGHIỆM KỸ THUẬT

### 3.1. Hệ thống 1: Xử lý phân tán PySpark, Streaming & Lakehouse (`pyspark-course`)

Kho lưu trữ: `https://github.com/muontrothanhtop1hacklor/pyspark-course.git`

#### 3.1.1. Chuẩn hóa Kiểu dữ liệu, Quản trị Chất lượng & Phép kết nối (Chuyên đề 00–06, 08–09)
* **Quản trị lược đồ (Schema Enforcement):** Áp dụng khai báo tường minh `StructType`/`StructField` thay cho cơ chế tự suy diễn (`inferSchema=True`), loại bỏ thao tác quét dữ liệu hai lần (double-scan) ở tầng nạp dữ liệu. Sử dụng kiểu `DecimalType(18, 2)` cho các trường giá trị tiền tệ (`amount`, `MUC_LUONG`) nhằm triệt tiêu sai số dấu phẩy động nhị phân.
* **Cô lập bản ghi lỗi & Bảo toàn dữ liệu:** Thiết lập luồng phân tách dữ liệu thành hai nhánh độc lập (`Valid` và `Quarantine` kèm trường nguyên nhân `error_reason`), kiểm soát chặt chẽ điều kiện bất biến trên toàn tuyến:
  $$N_{\text{raw}} = N_{\text{valid}} + N_{\text{quarantine}} + N_{\text{dedup}}$$
* **Xử lý khóa ngoại mồ côi & Khử trùng lặp:** Sử dụng `Left Anti Join` để thu thập các giao dịch phát sinh mã đối tượng chưa đồng bộ trong bảng danh mục (`unmapped_transactions`); áp dụng hàm cửa sổ `ROW_NUMBER() OVER (PARTITION BY key ORDER BY updated_at DESC)` để chuẩn hóa bản ghi trạng thái mới nhất.

#### 3.1.2. Đo kiểm hiệu năng Phân vùng vật lý & Hàm xử lý dữ liệu (Chuyên đề 07, 10, 21)

**Bảng 3.1. Kết quả đo kiểm chiến lược phân vùng trên 200.000 bản ghi (`spark.sql.adaptive.enabled = false`)**

| Phương thức phân vùng | Số file sinh ra | Thời gian ghi | Kích thước TB / file | Đặc tính kỹ thuật ghi nhận từ Physical Plan |
| :--- | :---: | :---: | :---: | :--- |
| **`coalesce(2)`** | `2` | **`0,80s`** | `~1,80 MB` | Gộp phân vùng cục bộ trong cùng Executor, không phát sinh Shuffle Stage. |
| **`repartition(2)`** | `2` | `2,30s` | `~1,80 MB` | Phát sinh Full Shuffle (`Exchange RoundRobinPartitioning`), thời gian tăng `2,88x`. |
| **`repartition(8, "province")`** | `6` *(2 rỗng)* | `2,45s` | Không đều | Xảy ra xung đột băm (`hash(province) % 8`), 10 mã tỉnh chỉ phân bổ vào `6/8` phân vùng. |
| **`repartition(200)`** | `200` | `3,02s` | `18,28 KB` | Gây hiện tượng phân mảnh tệp nhỏ (*Small Files Problem*), làm tăng chi phí I/O metadata. |
| **`repartition` trước `groupBy`** | Theo `shuffle.partitions` | — | — | Cấu trúc phân vùng trước `groupBy` bị hủy bỏ hoàn toàn do `groupBy` kích hoạt Shuffle mới. |

**Bảng 3.2. Kết quả đo kiểm hiệu năng thực thi trên 1.000.000 bản ghi (Ghi toàn tập ra Parquet)**

| Cơ chế thực thi | Toán tử vật lý (Spark Plan) | Thời gian thực thi | Tốc độ tương đối | Đánh giá kỹ thuật |
| :--- | :--- | :---: | :---: | :--- |
| **Python UDF (`@udf`)** | `BatchEvalPython` / `ArrowEvalPython` | `9,21s` | `1,00x` (Baseline) | Hộp đen đối với Catalyst Optimizer; chi phí tuần tự hóa dòng cao giữa JVM và Python. |
| **Spark Built-in Functions** | `Project` (Whole-Stage Codegen) | `3,98s` | **`2,31x` nhanh hơn** | Thực thi trực tiếp trong không gian bộ nhớ JVM, tối ưu hóa toàn diện cây biểu thức. |
| **Pandas UDF (`@pandas_udf`)** | `ArrowEvalPython` (Columnar Batch) | **`3,11s`** | **`2,96x` nhanh hơn** | Truyền tải lô dữ liệu dạng cột qua Apache Arrow và tính toán vector hóa trên C/NumPy. |

#### 3.1.3. Xử lý luồng thời gian thực với Kafka KRaft & Structured Streaming (Chuyên đề 11–16)
* **Kiểm chứng tính tương đương (Batch–Streaming Parity):** Thực thi cùng quy tắc biến đổi trên tập kiểm chuẩn (30 giao dịch qua 3 micro-batches), xác nhận tập đầu ra của luồng Streaming trùng khớp 100% với luồng Batch (`21` bản ghi hợp lệ, `9` bản ghi lỗi, tổng giá trị `40.000.000 VND`).
* **Kiểm nghiệm ràng buộc trạng thái (Stateful Constraints):** Xác minh thực nghiệm cơ chế chống xử lý trùng tệp qua `FileStreamSourceLog`, bắt buộc khai báo Schema tĩnh khi đọc luồng, yêu cầu gắn `Watermark` khi tổng hợp ở chế độ `append`, và giới hạn của hàm cửa sổ không gắn thời gian trên luồng vô hạn.
* **Tối ưu hóa kiến trúc Đa đích ghi (Multi-Sink Pipeline):** Sử dụng `foreachBatch` kết hợp `cache()` DataFrame trung gian để thực hiện khử trùng lặp cục bộ và phân phối đồng thời vào 03 đích lưu trữ (`Valid Parquet`, `DLQ Error Sink`, `Aggregated Mart`) chỉ với một lần đọc từ Kafka KRaft; áp dụng `Trigger(availableNow=True)` để giải phóng tài nguyên ngay sau khi xử lý hết dữ liệu tồn đọng.

#### 3.1.4. Mở rộng quy mô 100M bản ghi & Quản trị bảng Apache Iceberg (Chuyên đề 17–21)
* **Cơ chế phục hồi sinh dữ liệu quy mô lớn (`Phased Resume`):** Giải quyết bài toán gián đoạn ở phân vùng `45/167` khi sinh 100M bản ghi thông qua: (1) Kiểm tra tính toàn vẹn bằng PyArrow Parquet Footer (không nạp dữ liệu vào RAM), (2) Hạt giống ngẫu nhiên tất định theo chỉ số phân vùng (`seed = 42 + chunk_id`), và (3) Ghi tệp nguyên tử qua tệp tạm (`.tmp` $\to$ `os.replace`).
* **Đo kiểm khả năng mở rộng luồng Medallion (`8GB` RAM, `200` shuffle partitions):**

| Quy mô dữ liệu | Tầng Bronze (Ingestion) | Tầng Silver (Join + `partitionBy("MA_TINH")`) | Tầng Gold (`AGG_PERSON`, `AGG_COMPANY`) | Tổng thời gian | Hệ số co giãn |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Tập `1M` (1 triệu dòng)** | `13,0s` | `10,0s` | `11,0s` | **`34,0s`** | `1,0x` |
| **Tập `10M` (10 triệu dòng)** | `57,0s` | `220,0s` | `38,0s` | **`315,0s`** | `9,3x` *(Silver tăng 22x do Shuffle + Partition I/O)* |

* **Kiểm thử chịu tải bộ nhớ thấp (`Low-Memory Spill Test`):** Cố định cấu hình `1GB` RAM cho tập `10M` (`50` partitions) và `2GB` RAM cho tập `100M` (`200` partitions), xác nhận cơ chế tự động tràn đĩa (*Spill in-memory bytes to disk*) giúp duy trì tiến trình hoàn tất mà không gây lỗi `OutOfMemoryError`.
* **Data Lakehouse Catalog:** Triển khai bảng định dạng **Apache Iceberg** trên hạ tầng lưu trữ đối tượng **MinIO (S3 API)** với trình quản lý danh mục **Project Nessie**, thực thi thành công thao tác phân nhánh dữ liệu (`branch`), cập nhật ACID và truy vấn lịch sử (**Time Travel**).

---

### 3.2. Hệ thống 2: Pipeline Medallion Quá trình tham gia BHXH (`etl_course`)

Kho lưu trữ: `https://github.com/muontrothanhtop1hacklor/etl_course.git`

#### 3.2.1. Đặc tả mô hình dữ liệu nguồn
* **Bảng cha `RAW_QTTG_BHXH` (`142.857` bản ghi):** Lưu trữ các bản chụp lịch sử đồng bộ (snapshots) thông tin người lao động (`SO_SO_BHXH`, `NLD_ID`) theo mốc thời gian `CREATED_AT`.
* **Bảng con `RAW_QTTG_BHXH_DETAIL` (`1.000.000` bản ghi):** Lưu trữ chi tiết từng giai đoạn đóng BHXH (`TU_THANG`, `DEN_THANG`, `MA_DON_VI`, `MUC_LUONG`), liên kết với bản chụp cha qua khóa `MASTER_ID = RAW_QTTG_BHXH.ID`.
* **Ràng buộc chuẩn hóa hạt dữ liệu:** Mọi phép tổng hợp trực tiếp trên bảng con khi chưa khử trùng bảng cha đều gây nhân bản số liệu qua các kỳ đồng bộ. Tầng Silver bắt buộc xác định bản chụp `MASTER_ID` mới nhất cho từng `SO_SO_BHXH` trước khi lọc chi tiết quá trình đóng.

#### 3.2.2. Kết quả nghiệm thu kỹ thuật theo từng tầng xử lý

**Bảng 3.3. Thông số kỹ thuật và kết quả đầu ra của Pipeline QTTG BHXH**

| Tầng / Tác vụ | Module thực thi | Quy tắc xử lý & Biến đổi dữ liệu | Chỉ số đầu ra nghiệm thu |
| :--- | :--- | :--- | :--- |
| **1. Bronze** | `bronze_qttg.py` | Đọc CSV nguồn, gắn siêu dữ liệu kiểm toán (`source_file`, `load_time`, `layer`), kiểm tra sơ bộ định dạng kỳ đóng. | Master: **`142.857`** dòng<br>Detail: **`1.000.000`** dòng |
| **2. Silver** | `silver_qttg.py` | - Khử trùng Master theo `SO_SO_BHXH` (`ORDER BY to_timestamp(CREATED_AT) DESC, ID DESC`).<br>- Chuẩn hóa chuỗi kỳ đóng `YYYYMM`, kiểm tra miền năm `1960..hiện tại`, tháng `01..12`, `TU_THANG <= DEN_THANG`.<br>- Ép kiểu `MUC_LUONG` về `DECIMAL(18,2)`; đối chiếu khóa kép `MASTER_ID` và `NLD_ID` (`eqNullSafe`). | Silver Master: **`21.838`** người<br>Silver Detail: **`169.658`** dòng hợp lệ |
| **3. Quarantine** | `silver_qttg.py` | Tách biệt toàn bộ bản ghi Detail vi phạm kèm mã lý do `_quarantine_reason` (`MASTER_NOT_CURRENT`, `NLD_ID_MISMATCH`, `INVALID_VALUE`). | Quarantine: **`830.342`** dòng<br>*(Bảo toàn: `169.658 + 830.342 = 1.000.000`)* |
| **4. Gold** | `gold_qttg.py` | Sinh bảng chiều thời gian `dim_thang` bằng `sequence(..., INTERVAL 1 MONTH)` + `explode`; kết nối khoảng thời gian tính 05 chỉ tiêu KPI tháng (`SO_NGUOI_THAM_GIA`, `SO_DON_VI`, `TONG_QUY_LUONG`, `LUONG_BINH_QUAN`, `SO_NGUOI_LUONG_0`). | `dim_thang`: **`629`** tháng<br>`bao_cao_bhxh_thang`: **`629`** dòng |
| **5. Validate** | `validate_qttg.py` | Kiểm định tự động 04 điều kiện Data Contract: không trùng `SO_SO_BHXH`, không tồn tại Detail mồ côi, không sai thứ tự kỳ tháng, không trùng `THANG_ID` ở Gold. | `STATUS = SUCCESS`<br>**`ERROR_ROWS = 0`** |

---

### 3.3. Hệ thống 3: Phân tích 200M dòng thẻ BHYT & Thiết kế Hệ thống API (`BHYT_HS-SV`)

Kho lưu trữ: `https://github.com/muontrothanhtop1hacklor/BHYT_HS-SV.git`

#### 3.3.1. Đặc tả tập dữ liệu kiểm chuẩn quy mô 200M bản ghi ([`common/data_gen/`](common/data_gen/README.md))
* **Công nghệ sinh dữ liệu:** Biên dịch JIT đa luồng bằng **Numba `@njit`**, mô phỏng xuyên suốt vòng đời tham gia BHYT (Person Lifecycle) của **20.000.000 cá nhân**, tạo ra **195.305.908 bản ghi thẻ** phân bổ trên `200` tệp Parquet (`~4,59 GB`, nén Snappy/ZSTD).
* **Phân bố kịch bản nghiệp vụ:** Bao phủ 06 nhóm hành vi thực tế (Tham gia liên tục `CONT`, Dừng hẳn `STOP`, Chuyển khối sang Doanh nghiệp/Hộ gia đình `SWITCH`, Gián đoạn ngắt quãng `GAP`, Nhập học muộn `LATE`, Cấp đổi/Nâng quyền lợi `UPGRADE`) cùng các trường hợp thẻ hủy (`TRANG_THAI = 0`).
* **Cấu trúc lỗi kiểm thử:** Tiêm có kiểm soát **1.949.678 bản ghi lỗi** thuộc 05 nhóm lỗi định danh vào tập nguồn, đồng thời xuất nhật ký đối chứng `dirty_log` và bảng chân lý `persons_gt` độc lập hoàn toàn với mã nguồn ETL.

#### 3.3.2. Kết quả Hạng mục Ý 1 — Rà soát HSSV dừng tham gia BHYT ([`bai_tuan1_y1_hssv_dung_bhyt/`](bai_tuan1_y1_hssv_dung_bhyt/README.md))
* **Định nghĩa nghiệp vụ:** Xác định danh sách cá nhân có thẻ hợp lệ (`TRANG_THAI = 1`) thuộc khối `HS` hoặc `SV` giao với tháng `10/2024` (`TU_NGAY < 2024-11-01 AND DEN_NGAY >= 2024-10-01`), nhưng không có bất kỳ thẻ hợp lệ nào (ở mọi khối đối tượng) giao với tháng `08/2026` (`TU_NGAY < 2026-09-01 AND DEN_NGAY >= 2026-08-01`).

**Bảng 3.4. Kết quả kiểm toán làm sạch tầng Silver trên 195.305.908 bản ghi**

| Mã lỗi | Đặc tả vi phạm dữ liệu | Số lượng trong `dirty_log` | Số lượng Silver phát hiện | Sai lệch | Phương thức xử lý tại tầng Silver |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **Loại 1** | Ngày hiệu lực đảo ngược (`TU_NGAY > DEN_NGAY`) | `390.254` | `390.254` | `0` | Hỗ trợ 02 chế độ: `quarantine` hoặc `smart-repair` ($\Delta \in [25, 375]$ ngày, gắn cờ `_FLAG_DATE_SWAPPED`). |
| **Loại 2** | Thiếu họ tên (`HO_TEN IS NULL` / rỗng) | `389.918` | `389.918` | `0` | Giữ lại bản ghi phục vụ thống kê số lượng, gắn cờ `_FLAG_NAME_NULL = True`. |
| **Loại 3** | Sai miền giá trị giới tính (`GIOI_TINH` $\notin \{1, 2\}$) | `390.216` | `390.216` | `0` | Giữ lại bản ghi, gắn cờ `_FLAG_GENDER_INVALID = True`. |
| **Loại 4** | Mã khối sai định dạng chữ hoa/khoảng trắng (`' hs '`, `'sv'`) | `389.768` | `389.768` | `0` | Chuẩn hóa `UPPER(TRIM(MA_KHOI))`, phục hồi `+1.646` đối tượng HSSV hợp lệ tại mốc gốc. |
| **Loại 5** | Bản ghi trùng lặp khóa định danh thẻ (`ID`) | `389.522` | `389.522` | `0` | Loại bỏ bản sao trên phạm vi toàn cục 200 chunks qua `GlobalDedupTracker`. |
| **Tổng** | **Tổng hợp kết quả bảo toàn dòng tầng Silver** | **`1.949.678`** | **`1.949.678`** | **`0`** | **Silver sạch: `194.526.132` \| Quarantine: `390.254` \| Dedup: `389.522`** |

**Bảng 3.5. Đối sánh kết quả đầu ra tầng Gold Ý 1 và hiệu năng thực thi**

| Phương án / Kiến trúc thực thi | Số lượng HSSV dừng tham gia | Giải trình định lượng & Độ chính xác | Thời gian chạy | Đỉnh RAM tiến trình (RSS) |
| :--- | :---: | :--- | :---: | :---: |
| **Đối chiếu trực tiếp trên Raw (Oracle)** | `848.413` | Mốc tham chiếu gốc chưa chuẩn hóa chuỗi `MA_KHOI`. | `9,74s` *(chỉ đếm)* | — |
| **Silver (Chế độ `quarantine` mặc định)** | `850.190` | Cân bằng: `848.413 (Raw) + 1.646 (Chuẩn hóa Loại 4) + 131 (Cách ly Loại 1)`. | — | — |
| **Silver (Chế độ `smart-repair` chuẩn hóa)** | **`848.413`** | Khôi phục thẻ tháng 08/2026 bị đảo ngày của 131 ca chuyển khối (`SWITCH`), triệt tiêu 100% Dương tính giả. | — | — |
| **Gold Engine 1: Chunk-based Đa luồng** | Khớp 100% | Xử lý độc lập từng phân vùng kết hợp gộp kết quả; đạt `44/44` pytest. | `61,89s` | `1,50 GB` |
| **Gold Engine 2: Global DuckDB SQL** | Khớp 100% | Không phụ thuộc giả định phân vùng theo mã sổ; thông lượng đạt `~8,65M dòng/s`. | **`31,69s`** *(Cold)*<br>**`22,49s`** *(Hot)* | `2,68 GB` |

#### 3.3.3. Kết quả Hạng mục Ý 2 — Rà soát HSSV gián đoạn $\ge 90$ ngày ([`bai_tuan2_y2_hssv_gian_doan/`](bai_tuan2_y2_hssv_gian_doan/README.md))
* **Định nghĩa nghiệp vụ:** Xác định các cá nhân thuộc khối `HS`/`SV` tại tháng `10/2024`, đến tháng `07/2026` vẫn có thẻ BHYT hiệu lực (ở bất kỳ khối nào), nhưng tổng số ngày trống thẻ cộng dồn trong cửa sổ quan sát $W = [\text{2024-10-01}, \text{2026-07-31}]$ (`669` ngày) đạt từ `90` ngày trở lên.
* **Đặc tả giải thuật Chuỗi thời gian (`Interval Merging`):**
  1. *Cắt biên hiệu lực (Window Clipping):* Chuẩn hóa mọi thẻ hợp lệ (`TRANG_THAI = 1`) vào trong cửa sổ quan sát: $t_{\text{clip}} = \max(\text{TU\_NGAY}, \text{2024-10-01})$, $d_{\text{clip}} = \min(\text{DEN\_NGAY}, \text{2026-07-31})$.
  2. *Gộp các khoảng chồng lấn, nối tiếp và lồng nhau (Islands Identification):* Xác định biên kết thúc lớn nhất lũy kế trước bản ghi hiện tại thông qua hàm cửa sổ:
     $$\text{prev\_max\_den} = \max(d_{\text{clip}}) \text{ OVER } (\text{PARTITION BY SO\_SO\_BHXH ORDER BY } t_{\text{clip}}, d_{\text{clip}} \text{ ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING})$$
     Khởi tạo cụm liên tục mới khi và chỉ khi $t_{\text{clip}} > \text{prev\_max\_den} + 1\text{ ngày}$, từ đó thu gọn lịch sử thẻ về tập các khoảng rời nhau tối đại $\{[M_{k,\text{start}}, M_{k,\text{end}}]\}_{k=1}^m$.
  3. *Tổng hợp đầy đủ 03 nhóm khoảng trống:*
     * Khoảng trống đầu kỳ (`DAU_KY`): $M_{1,\text{start}} - \text{2024-10-01}$ (khi $M_{1,\text{start}} > \text{2024-10-01}$).
     * Khoảng trống giữa kỳ (`GIUA_KY`): $\sum_{k=2}^m (M_{k,\text{start}} - M_{k-1,\text{end}} - 1)$.
     * Khoảng trống cuối kỳ (`CUOI_KY`): $\text{2026-07-31} - M_{m,\text{end}}$ (khi $M_{m,\text{end}} < \text{2026-07-31}$).

**Bảng 3.6. Thông số nghiệm thu thực thi tầng Gold Ý 2 trên tập 200M bản ghi**

| Chỉ tiêu nghiệm thu | Kết quả đo lường chính thức | Ghi chú kỹ thuật & Kiểm định |
| :--- | :--- | :--- |
| **Tổng số đối tượng gián đoạn $\ge 90$ ngày** | **`242.290` người** | Tăng `+421` người so với phiên bản trước khi tính khoảng trống 2 biên (`241.869`). |
| **Phân rã theo khối đối tượng gốc** | Học sinh (`HS`): **`176.042`** (`72,66%`)<br>Sinh viên (`SV`): **`66.248`** (`27,34%`) | Tổng 63 tỉnh trên bảng `TK_DBHC_HSSV_GIAN_DOAN_BHYT` khớp tuyệt đối 100%. |
| **Thời gian gián đoạn trung bình** | **`144,5` ngày** (`~4,8` tháng) | 100% bản ghi thỏa mãn bất biến `SO_NGAY_GIAN_DOAN >= 90`. |
| **Thời gian thực thi & Tiêu thụ bộ nhớ** | **`247,89s`** (`~4,1` phút) \| **`1.073,68 MB` RSS** | Thực thi trên 4 luồng xử lý; kiểm thử tự động đạt **`20 / 20` bài** (`13` unit + `7` invariant). |

#### 3.3.4. Kết quả Hạng mục Thiết kế Hệ thống & Dịch vụ API ([`design/`](design/README.md))
* **Hồ sơ bàn giao:**
  * **Thiết kế Cơ bản (`HSSV-BD-001`):** Gồm `15` phân mục/sheets ([`ThietKeCoBan_BasicDesign_VN.md`](design/ThietKeCoBan_BasicDesign_VN.md) & [`.xlsx`](design/ThietKeCoBan_BasicDesign_VN.xlsx)) quy định kiến trúc tổng thể Batch Lakehouse $\to$ Serving DB (PostgreSQL 16 + Redis 7.2 + MinIO), thiết kế `04` màn hình nghiệp vụ, `05` tiến trình Batch (`BAT-HSSV-001..005`), lược đồ `10` bảng dữ liệu và các yêu cầu phi chức năng (ATTT cấp độ 3, khả năng chịu tải).
  * **Thiết kế Chi tiết (`HSSV-DD-001`):** Gồm `11` phân mục/sheets ([`ThietKeChiTiet_DetailDesign_VN.md`](design/ThietKeChiTiet_DetailDesign_VN.md) & [`.xlsx`](design/ThietKeChiTiet_DetailDesign_VN.xlsx)) đặc tả luồng xử lý `35` bước tuần tự, `08` truy vấn SQL tối ưu hóa kèm kịch bản xử lý ngoại lệ, ma trận `15` quy tắc kiểm tra đầu vào (`CHK-01..15`) và `32` kịch bản kiểm thử đơn vị (`UT-001..032`).

**Bảng 3.7. Danh mục đặc tả kỹ thuật 06 RESTful APIs thuộc tầng Serving**

| Mã API | Phương thức & Endpoint | Chức năng nghiệp vụ | Cơ chế tối ưu hóa truy vấn / Lưu trữ | Mục tiêu SLA (`p95`) |
| :---: | :--- | :--- | :--- | :---: |
| **`API-HSSV-001`** | `GET /api/v1/hssv/persons` | Tra cứu, lọc đa tiêu chí và phân trang danh sách HSSV vi phạm. | B-Tree Composite Index + GIN Trigram Index (`unaccent`) trên `HSSV_PERSON_SUMMARY` (`1.090.703` dòng). | `<= 300 ms` |
| **`API-HSSV-002`** | `GET /api/v1/hssv/persons/{soSoBhxh}` | Truy xuất hồ sơ nhân thân, thẻ đại diện mốc gốc/hiện tại và tổng hợp vi phạm. | Truy vấn khóa chính (Point Lookup) trên PostgreSQL Serving DB. | `<= 150 ms` |
| **`API-HSSV-003`** | `GET /api/v1/hssv/persons/{soSoBhxh}/timeline` | Truy xuất danh sách thẻ gốc, các khoảng liên tục đã gộp và chi tiết từng đợt gián đoạn. | Kết hợp bảng `BC_HSSV_GAP_HISTORY` (`DAU_KY`, `GIUA_KY`, `CUOI_KY`) đánh chỉ mục theo `SO_SO_BHXH`. | `<= 250 ms` |
| **`API-HSSV-004`** | `GET /api/v1/hssv/reports/provinces` | Báo cáo thống kê số liệu dừng đóng và gián đoạn theo 63 Tỉnh/TP và toàn quốc. | Đọc trực tiếp từ bộ nhớ đệm Redis (`TK_DBHC_HSSV_TONG_HOP`, 63 bản ghi, warm-up sau Batch). | `<= 200 ms` |
| **`API-HSSV-005`** | `GET /api/v1/hssv/reports/distribution` | Thống kê phân bố thời gian gián đoạn theo 05 ngưỡng (`90-120d` đến `>365d`). | Tổng hợp sẵn tại bảng `TK_PHAN_BO_GIAN_DOAN` (`320` dòng) kết hợp lưu đệm trên Redis. | `<= 200 ms` |
| **`API-HSSV-006`** | `POST /api/v1/hssv/reports/export` | Xuất tệp báo cáo định dạng `XLSX` / `CSV` theo bộ lọc nghiệp vụ. | Cơ chế kết hợp (Hybrid): Xuất đồng bộ nếu $\le 10.000$ dòng; đẩy Queue Worker + MinIO Presigned URL (`HTTP 202`) nếu $> 10.000$ dòng. | Phản hồi `< 1s` *(Async)* |

---

## 4. PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ (RCA) CÁC VẤN ĐỀ PHÁT SINH

**Bảng 4.1. Hồ sơ phân tích kỹ thuật các sự cố phát sinh và biện pháp khắc phục**

| Mã sự cố | Hạng mục liên quan | Mô tả hiện tượng ghi nhận | Nguyên nhân gốc rễ (Root Cause) | Giải pháp kỹ thuật đã áp dụng (Resolution) | Kết quả xác minh |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **`ISS-01`** | Bộ sinh dữ liệu `200m` | Khi kiểm thử trên tập mẫu 10.000 dòng ban đầu, 100% đối tượng HSSV tham gia tháng 10/2024 đều rơi vào trạng thái dừng đóng tại tháng 08/2026 (`1.398 / 1.398`). | Thuật toán sinh ngẫu nhiên rời rạc từng dòng thẻ không duy trì tính liên kết trạng thái của cùng một cá nhân qua thời gian, không tạo ra các kịch bản gia hạn hoặc chuyển khối. | Thiết kế lại kiến trúc [`gen_bhyt.py`](common/data_gen/gen_bhyt.py) theo mô hình trạng thái vòng đời cá nhân (*Person Lifecycle*), kiểm soát tỷ lệ phân phối 06 kịch bản và xuất bảng đối chứng `persons_gt`. | Tạo lập đầy đủ ca biên; tỷ lệ phân bố sát thực tế ngành. |
| **`ISS-02`** | Tầng Silver & Gold Ý 1 (`200m`) | Kết quả Gold trên dữ liệu đã cách ly lỗi Loại 1 phát sinh chênh lệch tăng **`+131` người** so với tập đáp án chuẩn đã chuẩn hóa Loại 4. | `131` cá nhân này đã chuyển sang đóng BHYT khối Doanh nghiệp/Hộ gia đình tại tháng 08/2026, nhưng bản ghi thẻ mới bị lỗi nhập ngược ngày (`TU_NGAY > DEN_NGAY`). Việc cách ly cứng toàn bộ dòng lỗi làm mất thông tin thẻ đang hoạt động, dẫn đến kết luận Dương tính giả. | Xây dựng cơ chế `--mode-loai1 smart-repair`: chỉ hoán đổi lại cặp ngày khi độ dài hiệu lực nằm trong miền chu kỳ cấp thẻ hợp lệ ($\Delta \in [25, 375]$ ngày) và gắn cờ kiểm toán `_FLAG_DATE_SWAPPED = True`. | Độ chính xác đạt `100%` (`0` False Positive). |
| **`ISS-03`** | Thuật toán Timeline Ý 2 (`200m`) | Sai lệch kết quả khoảng trống trong hai tình huống: (1) Thẻ ngắn hạn nằm lọt bên trong thẻ dài hạn; (2) Thẻ đầu kỳ bắt đầu sau ngày `01/10/2024` hoặc thẻ cuối kết thúc trước `31/07/2026`. | (1) Phép toán `LAG(DEN_NGAY)` chỉ tham chiếu dòng liền trước theo thứ tự sắp xếp thay vì biên kết thúc xa nhất đã đạt được.<br>(2) Truy vấn ban đầu chỉ tính hiệu số giữa các cặp đoạn liên tiếp (`GIUA_KY`), bỏ sót hai khoảng biên của cửa sổ quan sát. | (1) Thay thế `LAG` bằng `MAX(den) OVER (... ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)`.<br>(2) Bổ sung hai nhánh `UNION ALL` tính khoảng trống `DAU_KY` và `CUOI_KY`. | Thu nhận chính xác thêm `+421` đối tượng ở biên (`242.290` người). |
| **`ISS-04`** | Khử trùng lặp Silver (`200m`) | Phép khử trùng theo từng tệp phân vùng (`np.unique` cục bộ) không phát hiện được các bản ghi trùng mã `ID` nằm khác tệp `part-*.parquet`. | Xử lý độc lập theo lô giúp giới hạn bộ nhớ nhưng làm mất ngữ cảnh định danh toàn cục giữa các phân vùng. | Cài đặt cấu trúc `GlobalDedupTracker` lưu trữ tập khóa `int64` toàn cục an toàn đa luồng (`threading.Lock`), dung lượng bộ nhớ tăng thêm trong ngưỡng kiểm soát (`~1,2 GB`). | Phát hiện đủ `389.522 / 389.522` bản ghi trùng toàn cục. |
| **`ISS-05`** | Đo lường tài nguyên & Engine | Chỉ số `psutil.virtual_memory().used` báo cáo mức tiêu thụ `14,59 GB / 15,44 GB`; PySpark gặp lỗi `Java heap space` khi chạy mặc định trên 100M dòng. | Phép đo mức hệ thống cộng gộp cả bộ nhớ của hệ điều hành và các tiến trình nền (~9,5 GB). Với PySpark trên máy đơn, JVM đòi hỏi cấu hình tường minh `driver.memory` và `shuffle.partitions`. | Xây dựng `MemoryMonitor` đo đệ quy riêng cây tiến trình thực thi (`Process Tree RSS`); cấu hình tường minh bộ nhớ cho Spark và sử dụng DuckDB + PyArrow cho tác vụ phân tích trên máy đơn. | Xác định chính xác RSS thực tế chỉ từ `1,05 – 2,68 GB`; quét 200M dòng trong `~31s`. |
| **`ISS-06`** | Sinh dữ liệu `100M` (`pyspark-course`) | Tiến trình sinh tập dữ liệu 100 triệu dòng bị ngắt ở phân vùng `45/167`, nguy cơ phải hủy bỏ `1,39 GB` dữ liệu đã ghi và mất tính đồng bộ với tệp đáp án lỗi. | Tiến trình ban đầu chưa tách biệt cơ chế ghi nhận trạng thái hoàn thành cấp phân vùng và chưa cố định hạt giống ngẫu nhiên theo chỉ số phân vùng. | Thiết lập cơ chế `Phased Resume` (`seed = 42 + chunk_id`), ghi tệp nguyên tử qua `.tmp`, đọc kiểm tra bằng PyArrow Footer và trích xuất bù danh sách mã lỗi cho 45 phân vùng đầu. | Khôi phục liền mạch đủ `167/167` phân vùng và tệp `error_keys_100M.csv`. |
| **`ISS-07`** | Tương thích môi trường Windows / Docker | Phát sinh lỗi mã hóa `UnicodeEncodeError` khi xuất tiếng Việt trên PowerShell, xung đột phiên bản bytecode Java với PySpark và sai lệch ký tự phân cách đường dẫn (`\` vs `/`). | Console mặc định của Windows dùng bảng mã `cp1252`; container Airflow mặc định thiếu JDK 17 tương thích với Spark 3.5+/4.0. | Chuẩn hóa `sys.stdout.reconfigure(encoding='utf-8')` ở đầu mọi module, chuẩn hóa đường dẫn bằng `.as_posix()` và đóng gói Dockerfile tích hợp sẵn OpenJDK 17. | Vận hành ổn định trên cả Windows Host và Linux Container. |

---

## 5. BÁO CÁO KIỂM TOÁN DỮ LIỆU & DANH MỤC CÔNG VIỆC TỒN ĐỌNG (BACKLOG)

### 5.1. Kết quả kiểm toán hiện trạng dữ liệu vật lý và hồ sơ tài liệu (Đã hoàn tất 100%)

Qua rà soát đối chiếu trực tiếp trên hệ thống tệp của cả 03 kho mã nguồn tại thời điểm lập báo cáo:
1. **Tính đầy đủ của dữ liệu thực thi:** Toàn bộ các tập dữ liệu nguồn, tầng trung gian (`Bronze`, `Silver`, `Quarantine`) và tầng kết quả (`Gold`, `_manifest.json`, `_metadata.json`, `_answer_key`) của cả 03 dự án đều đã được thực thi hoàn chỉnh và lưu trữ nguyên vẹn trên ổ đĩa.
2. **Tính nhất quán giữa tài liệu và dữ liệu vật lý:** Các sai lệch nhỏ về mặt văn bản (chỉ số `242.290` người của Ý 2 trong báo cáo Tuần 2 & Thiết kế Tuần 3; bảng thời gian thực thi Benchmark `1M` vs `10M` trong `logs/chapter-18.md`; đường dẫn lệnh chạy trong `etl_learn/README.md`) đều đã được cập nhật và đồng bộ hoàn tất lên hệ thống quản lý phiên bản Git.

### 5.2. Danh mục công việc tồn đọng / Chưa triển khai (Open Backlog)

**Bảng 5.1. Các hạng mục công việc chờ triển khai ở giai đoạn tiếp theo**

| Mã tồn đọng | Hệ thống | Hạng mục công việc | Hiện trạng tại thời điểm báo cáo | Mức độ ưu tiên | Đề xuất hướng xử lý |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **`BL-01`** | `BHYT_HS-SV` (`200m`) | **Lập trình tiến trình Batch `BAT-HSSV-004` (Serving DB Loader)** | Đã hoàn thành đặc tả chi tiết trong `HSSV-BD-001` và `HSSV-DD-001`; chưa viết mã nguồn thực thi việc sinh bảng chi tiết từng đợt gián đoạn (`BC_HSSV_GAP_HISTORY`), bảng phân bố 5 ngưỡng (`TK_PHAN_BO_GIAN_DOAN`) và nạp sang PostgreSQL/Redis. | **Cao** *(nếu triển khai pha Backend)* | Lập trình module ETL đồng bộ từ Parquet tầng Gold sang PostgreSQL 16 (`COPY` + hoán đổi phân vùng) và warm-up Redis Cache. |
| **`BL-02`** | `BHYT_HS-SV` (`200m`) | **Hiện thực hóa (Coding) dịch vụ Backend 06 RESTful APIs & Giao diện tra cứu** | Đã hoàn thành toàn bộ đặc tả API, lược đồ cơ sở dữ liệu, mã kiểm tra đầu vào (`CHK-01..15`), truy vấn SQL (`SQL-01..07`) và kịch bản Unit Test (`UT-001..032`) ở Tuần 3; chưa triển khai mã nguồn ứng dụng Web/API. | **Tùy thuộc kế hoạch kỳ tới** | Triển khai dịch vụ bằng FastAPI (Python) hoặc Spring Boot kết nối PostgreSQL, Redis và MinIO theo đúng hồ sơ Thiết kế Chi tiết. |
| **`BL-03`** | `BHYT_HS-SV` (`200m`) | **Cập nhật chỉ số dòng kỳ vọng trong tệp Excel thiết kế (`.xlsx`)** | Các tệp Markdown thiết kế (`ThietKeCoBan_BasicDesign_VN.md`, `ThietKeChiTiet_DetailDesign_VN.md`) đã cập nhật con số `242.290` của Ý 2; hai tệp nhị phân `.xlsx` tương ứng vẫn giữ giá trị ước lượng cũ (`~241.869`). | **Thấp** | Chạy script đồng bộ lại giá trị ô ước lượng số bản ghi trong 2 tệp `.xlsx` khi chốt phiên bản thiết kế cuối cùng sau khi có ý kiến của Mentor. |
| **`BL-04`** | `etl_course` (`etl_learn`) | **Bổ sung hình ảnh chụp giao diện vận hành Airflow UI & cấu hình mount CSV 1M** | Minh chứng thực thi DAG trong kho mã nguồn hiện lưu dưới dạng nhật ký dòng lệnh (CLI execution logs); đường dẫn mount mặc định trong container Airflow đang trỏ tới tập mẫu nếu chưa gắn volume chứa tệp CSV 1M dòng từ `requirements/data/`. | **Thấp** | Cấu hình ánh xạ trực tiếp thư mục `requirements/data/` vào Docker Compose và lưu ảnh chụp đồ thị DAG xanh (Graph/Grid View) nếu phục vụ nghiệm thu trực quan. |

---

## 6. DANH MỤC CÂU HỎI NGHIỆP VỤ & KIẾN NGHỊ PHÊ DUYỆT

Để đảm bảo tính chặt chẽ về mặt nghiệp vụ trước khi chuyển sang giai đoạn phát triển phần mềm tiếp theo, kính trình Mentor / Phụ trách nghiệp vụ xem xét và cho ý kiến đối với **04 vấn đề** sau:

**Bảng 6.1. Danh mục các vấn đề cần xác nhận nghiệp vụ và định hướng kỹ thuật**

| Mã vấn đề | Nội dung vấn đề cần làm rõ | Phân tích bối cảnh kỹ thuật / Nghiệp vụ | Các phương án đề xuất & Kiến nghị |
| :---: | :--- | :--- | :--- |
| **`Q-01`** | **Quy tắc định danh khóa chính và phân loại đối tượng giao thoa đồng thời cả Ý 1 và Ý 2 trong bảng `HSSV_PERSON_SUMMARY`** | Ý 2 xét đối tượng còn tham gia tại **tháng 07/2026** (có gián đoạn $\ge 90$ ngày trong kỳ `10/2024 – 07/2026`), trong khi Ý 1 xét đối tượng dừng tham gia tại **tháng 08/2026**. Do đó, một HSSV có thẻ kết thúc đúng ngày `31/07/2026` (sau khi từng gián đoạn $\ge 90$ ngày trước đó) và không gia hạn trong tháng `08/2026` sẽ **thỏa mãn đồng thời cả Ý 1 và Ý 2**. Hiện tại bảng `HSSV_PERSON_SUMMARY` đang thiết kế khóa chính đơn `(SO_SO_BHXH)` với một cột `TIEU_CHI` đơn trị. | - **PA1 (Kiến nghị):** Đổi khóa chính thành khóa phức hợp `(SO_SO_BHXH, TIEU_CHI)` để bảo toàn độc lập danh sách của từng báo cáo trên cùng bảng Serving.<br>- **PA2:** Giữ khóa chính `(SO_SO_BHXH)` nhưng tách thành 02 cờ độc lập `IS_DUNG_THAM_GIA (BOOLEAN)` và `IS_GIAN_DOAN (BOOLEAN)`.<br>- **PA3:** Quy định thứ tự ưu tiên loại trừ (ví dụ ưu tiên xếp vào `DUNG_THAM_GIA`). |
| **`Q-02`** | **Xác nhận định nghĩa "Gián đoạn không tham gia từ 3 tháng trở lên" tại Công văn 835/QLT (Ý 2)** | Giải thuật hiện tại đang tính theo **tổng số ngày gián đoạn cộng dồn** trong toàn bộ cửa sổ quan sát đạt $\ge 90$ ngày ($\sum \text{gap}_i \ge 90$, ví dụ nghỉ 2 đợt rời nhau: `30 ngày + 60 ngày = 90 ngày`). Trong thực tế quản lý thu BHYT (xét quyền lợi 5 năm liên tục không gián đoạn quá 3 tháng), tiêu chí có thể được hiểu theo từng đợt đơn lẻ. | Đề nghị xác nhận nghiệp vụ áp dụng:<br>- **Cách 1 (Hiện tại):** Tổng số ngày trống thẻ cộng dồn trong kỳ $\ge 90$ ngày; hay<br>- **Cách 2:** Tồn tại ít nhất **01 đợt gián đoạn liên tục** có độ dài $\ge 90$ ngày ($\max(\text{gap}_i) \ge 90$)? |
| **`Q-03`** | **Quy ước hiển thị các bản ghi thẻ đã hiệu chỉnh tự động (`Smart Repair`) trên API tra cứu chuỗi thời gian (`API-HSSV-003`)** | Tại tầng Silver, các thẻ bị lỗi đảo ngược ngày (`TU_NGAY > DEN_NGAY`) nhưng có khoảng cách nằm trong chu kỳ cấp thẻ hợp lệ ($25..375$ ngày) được hoán đổi lại ngày và đánh dấu `_FLAG_DATE_SWAPPED = True`. | Xác nhận có cần bổ sung thuộc tính `isDateSwapped: boolean` vào cấu trúc JSON trả về của `API-HSSV-003` để hiển thị cảnh báo kiểm toán cho cán bộ nghiệp vụ khi tra cứu lịch sử thẻ hay không. |
| **`Q-04`** | **Phê duyệt lộ trình công việc giai đoạn tiếp theo (Tuần 10 trở đi)** | Hồ sơ Thiết kế Cơ bản (`HSSV-BD-001`) và Thiết kế Chi tiết (`HSSV-DD-001`) của hệ thống `BHYT_HS-SV` đã hoàn thiện đầy đủ. | Đề nghị xác nhận trọng tâm giai đoạn tới là triển khai lập trình hệ thống Backend 06 RESTful APIs + Serving DB (`BL-01`, `BL-02`) theo bản thiết kế đã lập, hay chuyển sang hạng mục chuyên đề mới. |

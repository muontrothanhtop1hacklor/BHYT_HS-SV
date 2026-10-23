# BÁO CÁO KẾT QUẢ NGÀY 1
**Dự án:** Tuần 1 – HSSV dừng tham gia BHYT (CV 835/QLT – Ý 1)
**Ngày báo cáo:** 12/10/2026
**Giai đoạn:** Chốt đặc tả nghiệp vụ và dựng khung kỹ thuật

---

## 1. Mục tiêu Ngày 1
1. Hiểu và đặc tả nghiệp vụ bài toán.
2. Chốt kiến trúc lưu trữ và công nghệ xử lý.
3. Chốt cấu trúc bảng nguồn và bảng đích (DDL).
4. Dựng khung dự án để các ngày sau triển khai.

## 2. Kết quả đạt được

### 2.1. Đặc tả nghiệp vụ
- Định nghĩa "có tham gia tại tháng M": có ít nhất một thẻ `TRANG_THAI = 1` với `TU_NGAY < đầu tháng M+1` và `DEN_NGAY >= đầu tháng M`.
- Mốc gốc: tháng 10/2024, thẻ có `MA_KHOI` là `HS` hoặc `SV`.
- Mốc kiểm tra "đến nay": tạm đặt `2026-08-10` (ngày ký công văn).
- Logic xử lý: tập HSSV tháng 10/2024 trừ (anti-join) tập người còn thẻ hiệu lực tại mốc kiểm tra.

### 2.2. Kiến trúc lưu trữ
- Chọn **Parquet chia chunk** làm nguồn dữ liệu dùng chung, chỉ đọc.
- Lý do: ổ C còn khoảng 37,9 GB; 200 triệu dòng dạng Parquet nén ước tính 4–5 GB (ước tính, chưa đo thực tế). SQL Server Express trên máy bị giới hạn 10 GB mỗi DB.
- Docker không chạy; DuckDB chưa được cài.

### 2.3. DDL
DDL nguồn được lưu tại [ddl_dm_bhxh.sql](../p1_du_lieu/ddl_dm_bhxh.sql) và [ddl_st_inthe_dtl.sql](../p1_du_lieu/ddl_st_inthe_dtl.sql):
- `DM_BHXH`, `ST_INTHE_DTL`
- `BC_HSSV_DUNG_THAM_GIA` (chi tiết), `TK_DBHC_HSSV_DUNG_THAM_GIA` (tổng hợp theo tỉnh)

### 2.4. Khung dự án
| Thành phần | Vị trí |
|---|---|
| Cấu hình (mốc ngày, seed 2026, đường dẫn) | `src/config.py` |
| Sinh danh mục BHXH (160 đơn vị) | `src/generator/generate_dm_bhxh.py` |
| Sinh thẻ BHYT theo chunk Parquet | `src/generator/generate_st_inthe_dtl.py` |
| Pipeline Bạn A / Bạn B | `src/pipelines/` |
| SQL tham chiếu A / B | `sql/dev_a/`, `sql/dev_b/` |
| Đối chiếu A và B, xuất báo cáo | `src/reconciliation/compare_results.py` |
| Test schema | `tests/test_data_quality.py` |
| Script chạy nhanh | `scripts/*.bat` |

### 2.5. Kiểm thử đã chạy
Chạy thử với 10.000 dòng: sinh dữ liệu, hai pipeline, đối chiếu và `pytest` (2 test) đều chạy thành công. Hai pipeline cho cùng kết quả 1.398 người (HS 962, SV 436). Sau đó đã xóa dữ liệu thử.

## 3. Vấn đề tồn đọng (cần lưu ý, chưa hoàn thành)

| # | Vấn đề | Mức độ |
|---|---|---|
| 1 | **Dữ liệu fake chưa thực tế.** Script hiện sinh từng dòng ngẫu nhiên, chưa theo vòng đời đối tượng. `lifecycle.py` mới chỉ định nghĩa hằng số 6 nhóm tình huống, chưa có logic sinh. | Cao |
| 2 | **Kết quả thử nghiệm chưa có giá trị kiểm chứng.** 1.398 trên 1.398 HSSV tháng 10/2024 đều "dừng" vì thẻ ngẫu nhiên hầu như không nối tiếp nhau. Khớp 100% giữa A và B chỉ cho thấy hai đoạn code tương đồng, vì chúng do cùng một người viết. | Cao |
| 3 | **Chưa chạy ở quy mô 200 triệu dòng.** Chưa đo thời gian, dung lượng thực và bộ nhớ. Pipeline hiện nạp tập kết quả vào pandas/set, có nguy cơ thiếu RAM ở quy mô lớn. | Cao |
| 4 | **Mốc ngày kiểm tra và quy tắc chuyển khối `DN`/`GD` chưa được hai bạn thống nhất.** Giá trị trong code chỉ là mặc định tạm. | Trung bình |
| 5 | Số người tối đa trong script là 20 triệu, nhưng một người chỉ có một thẻ ngẫu nhiên nên chưa phản ánh việc mỗi người có nhiều thẻ. | Trung bình |
| 6 | Chưa có script nạp DDL vào DB, và `requirements.txt` có `duckdb`/`polars` nhưng chưa cài. | Thấp |

## 4. Đánh giá theo tiêu chí Gate 1

| Tiêu chí | Trạng thái |
|---|---|
| Biên bản thống nhất spec nghiệp vụ | **Chưa hoàn thành.** Mới có đề xuất, cần xác nhận với đồng nghiệp |
| DDL nguồn và đích | Đã soạn, chờ rà soát |
| Chốt công nghệ lưu trữ | Đã đề xuất Parquet, chưa đo thực tế |
| Khung dự án chạy được | Hoàn thành |

**Kết luận:** Phần khung kỹ thuật của Ngày 1 đã xong. Phần quyết định nghiệp vụ vẫn mở, chưa nên coi Gate 1 là đã duyệt.

## 5. Kế hoạch tiếp theo (Ngày 2–3)
1. Hai bạn chốt mốc ngày kiểm tra và quy tắc chuyển khối, ghi lại thành biên bản.
2. Viết lại generator theo vòng đời đối tượng, phủ đủ 6 nhóm tình huống và có số liệu kỳ vọng đã biết trước.
3. Chạy thử 1–5 triệu dòng, đo dung lượng và thời gian, rồi mới sinh đủ 200 triệu.
4. Dùng số liệu kỳ vọng từ generator để kiểm tra pipeline, thay vì chỉ so A với B.

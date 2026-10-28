# Thiết kế chi tiết (Detail Design)

> Hệ thống Phân tích, Rà soát Dữ liệu Lớn 200M Thẻ BHYT & Cung cấp Cổng Dịch vụ Tra cứu HSSV (CV 835/QLT)
> Tài liệu thiết kế kỹ thuật chi tiết mức Code/SQL dành cho lập trình viên và kiểm thử viên.
> Đồng bộ 100% với file `design/ThietKeChiTiet_DetailDesign_VN.xlsx`.

## HuongDan – Hướng dẫn sử dụng

**Mục đích của Detail Design (DD)**
- Trả lời câu hỏi: LÀM THẾ NÀO bên trong từng module API và tiến trình Batch. Viết đủ chi tiết để lập trình viên hiện thực chính xác 100% mà không phải phỏng đoán.
- Bao phủ đầy đủ 6 RESTful API tra cứu trực tuyến và Big Data Lakehouse Pipeline xử lý 200 triệu dòng thẻ BHYT.

**Quy ước bắt buộc**
- Xử lý chi tiết (Mục 05) viết theo các bước số học: 1, 1.1, 1.2, 2, 2.1... Mọi nhánh `IF` đều có nhánh `ELSE`. Mọi thao tác truy vấn DB đều trỏ tới `SQL-ID` ở Mục 06.
- Mọi câu lệnh SQL ở Mục 06 bắt buộc mô tả đầy đủ 5 trường hợp kết quả:
  1. Có dữ liệu bình thường.
  2. Không có dữ liệu (`NOT FOUND`).
  3. Nhiều hơn kỳ vọng (vi phạm ràng buộc dữ liệu).
  4. Lỗi Database (`DataAccessException`).
  5. Timeout kết nối / truy vấn.
- Toàn bộ các mã lỗi ném ra đều ánh xạ trực tiếp về `12_DSThongBao` của Thiết kế cơ bản.
- Mỗi nhánh rẽ của thuật toán phải có ít nhất 1 test case tương ứng tại Mục 09 (Unit Test).

---

## Bia – Bìa tài liệu

| Mục | Nội dung |
| --- | --- |
| Tên dự án | Hệ thống Xử lý, Rà soát Dữ liệu Lớn 200M Thẻ BHYT & Cung cấp Cổng Dịch vụ Tra cứu HSSV |
| Hệ thống | Phân hệ Phân tích Dữ liệu Lớn & Cổng Dịch vụ Tra cứu BHYT Học sinh - Sinh viên |
| Tài liệu | Thiết kế chi tiết (Detail Design) |
| Mã tài liệu | HSSV-DD-001 |
| Phiên bản | 1.0 |
| Người lập | Nhóm Kỹ sư Dữ liệu & Hệ thống (Pair Programming) |
| Người review | Tech Lead / Solution Architect |
| Người phê duyệt | Trưởng ban Quản lý Thu & Khai thác BHYT (BHXH Việt Nam) |
| Ngày phê duyệt | 2026/10/28 |
| Trạng thái | Approved |
| Tài liệu đầu vào | Thiết kế cơ bản HSSV-BD-001; Công văn số 835/QLT ngày 10/08/2026; Bộ Fake Data 200M dòng thẻ BHYT |

---

## LichSu – Lịch sử sửa đổi

| Phiên bản | Ngày | Sheet / Mục thay đổi | Nội dung thay đổi | Lý do | Người sửa | Người duyệt |
| --- | --- | --- | --- | --- | --- | --- |
| 1.0 | 2026/10/28 | Toàn bộ | Tạo mới tài liệu Thiết kế chi tiết cho toàn bộ 6 RESTful API và Pipeline xử lý dữ liệu lớn 200M dòng thẻ BHYT theo CV 835/QLT | Yêu cầu đồ án thiết kế hệ thống tuần 3 | Nhóm Kỹ sư | Tech Lead |
| 1.1 | 2026/10/28 | 05_XuLyChiTiet, 06_DinhNghiaSQL, 07_KiemTraDauVao, 09_UnitTest | Sửa lỗi thuật toán SQL-08 dùng MAX(den) OVER (ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) xử lý thẻ lồng nhau và lọc đủ 2 mốc (Tuần 2); cập nhật BAT-001 với GlobalDedupTracker & Smart Repair (Tuần 1); bổ sung đầy đủ nhánh ORDER BY cho SQL-01 & SQL-05 | Đồng bộ chuẩn xác 100% với code thực thi của Tuần 1 & Tuần 2 | Nhóm Kỹ sư | Tech Lead |

---

## TongQuanModule – Tổng quan module

| Mục | Nội dung |
| --- | --- |
| ID module | DD-HSSV-ALL (DD-API-001 -> 006, DD-BAT-001 -> 004) |
| Hiện thực cho | F-HSSV-001 đến F-HSSV-007, API-HSSV-001 đến API-HSSV-006, SCR-HSSV-001 đến SCR-HSSV-004, BAT-HSSV-001 đến BAT-HSSV-005 |
| Mức chi tiết | A (Đầy đủ mọi sheet: I/O, Thuật toán chi tiết từng bước, SQL định nghĩa 5 kịch bản, Ma trận Validation, Exception & Log, Unit Test phủ toàn diện) |
| Tóm tắt xử lý | 1. Online Query Engine: Nhận HTTP request -> Validate đầu vào (CHK) -> Kiểm tra Cache Redis -> Nếu cache miss, gọi PostgreSQL Repository qua B-Tree/Composite Index -> Map DTO -> Ghi Audit log bất đồng bộ -> Trả response chuẩn RESTful (p95 <= 300ms).<br>2. Timeline & Gap Algorithm: Truy xuất danh sách thẻ hợp lệ -> Sắp xếp TU_NGAY, DEN_NGAY -> Chạy thuật toán Interval Merging gộp đoạn liên tục/chồng lấn -> Quét phát hiện các khoảng trống gaps (đầu kỳ, giữa kỳ, cuối kỳ) -> Phân loại và tính lũy kế.<br>3. Big Data Lakehouse Pipeline: DuckDB SQL thực thi trên 200M dòng Parquet Silver -> Lọc đối tượng mốc T10/2024 -> Đối chiếu T08/2026 (Ý 1) và tính timeline T07/2026 (Ý 2) -> Xuất Gold Parquet -> Nạp Serving DB -> Refresh Cache Redis.<br>4. Async Export Worker: Nhận lệnh POST export -> Tạo Job PENDING -> Đẩy vào Redis Queue -> Celery/Spring Worker streaming dữ liệu ra file XLSX/CSV -> Đẩy lên MinIO/S3 -> Trả Presigned Download URL. |
| Lớp / package | Controller: vn.gov.bhxh.hssv.api.{HssvPersonController, HssvReportController}<br>Service: vn.gov.bhxh.hssv.service.{HssvPersonService, HssvTimelineService, HssvReportService, HssvExportService}<br>Engine: vn.gov.bhxh.hssv.engine.{BigDataPipelineEngine, IntervalMergeCalculator}<br>Repository: vn.gov.bhxh.hssv.repo.{HssvPersonRepository, HssvReportRepository, HssvExportJobRepository}<br>DTO: vn.gov.bhxh.hssv.dto.*, Entity: vn.gov.bhxh.hssv.entity.* |
| Chữ ký phương thức | 1. PageResponse<PersonSummaryDto> searchPersons(PersonQueryParam param, Pageable pageable)<br>2. PersonDetailDto getPersonDetail(String soSoBhxh)<br>3. TimelineDetailDto getPersonTimeline(String soSoBhxh)<br>4. ProvinceReportDto getProvinceSummary(String criteria, Sort sort)<br>5. GapDistributionDto getGapDistribution(String provinceCode, String block)<br>6. ExportResponseDto exportReport(ExportRequestDto requestDto)<br>7. void executeMedallionPipeline(PipelineConfig config) |
| Được gọi bởi | Clients Web UI, Hệ thống liên thông ngoài, Batch Job Schedulers (Airflow / Spring Batch) |
| Gọi tới | PostgreSQL 16, Redis 7.2, DuckDB Engine, MinIO Object Storage, AuditLogService, MessageResolver |
| Giao dịch | @Transactional(readOnly = true) cho API tra cứu. Ghi Audit log dùng Propagation.REQUIRES_NEW (lỗi audit không ảnh hưởng response). Batch Pipeline thực hiện theo cơ chế Atomic Swap (idempotent, ghi file/partition tạm rồi hoán đổi). |
| Xử lý đồng thời / khóa | Online query chỉ đọc (không khóa). Xuất báo cáo dùng Optimistic Lock (@Version trên bảng SYS_EXPORT_JOB). Giới hạn tối đa 5 tác vụ export chạy song song trên mỗi worker node. |

---

## ThamSoIO – Định nghĩa vào/ra

| Hướng | No | Tên tham số / thuộc tính | Kiểu (Java) | Bắt buộc | Mô tả | Giá trị khi không có | Tham chiếu BD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IN | 1 | provinceCode | String | × | Mã tỉnh (01-96). Lọc danh sách theo tỉnh mốc gốc. | null (tất cả tỉnh) | BD-08 API-001 Req 1 |
| IN | 2 | block | String | × | Khối đối tượng: HS, SV, ALL. | 'ALL' | BD-08 API-001 Req 2 |
| IN | 3 | criteria | String | × | Tiêu chí vi phạm: DUNG_THAM_GIA, GIAN_DOAN, ALL. | 'ALL' | BD-08 API-001 Req 3 |
| IN | 4 | search | String | × | Từ khóa tìm kiếm (họ tên, CCCD, số sổ BHXH). | null | BD-08 API-001 Req 4 |
| IN | 5 | minGapDays / maxGapDays | Integer | × | Khoảng số ngày gián đoạn tối thiểu và tối đa. | null | BD-08 API-001 Req 5,6 |
| IN | 6 | page / pageSize | Integer | × | Trang cần lấy (>=1) và kích thước trang (1..100). | page=1, pageSize=20 | BD-08 API-001 Req 7,8 |
| IN | 7 | sortBy / sortOrder | String | × | Trường sắp xếp và chiều sắp xếp (ASC/DESC). | sortBy='soSoBhxh', sortOrder='ASC' | BD-08 API-001 Req 9,10 |
| OUT | 1 | metadata | PageMetadataDto | ○ | Chứa totalRecords, totalPages, currentPage, pageSize. | — | BD-08 API-001 Res 1,2,3 |
| OUT | 2 | data | List<PersonSummaryDto> | ○ | Danh sách đối tượng vi phạm. Rỗng [] nếu không có kết quả. | List rỗng [] | BD-08 API-001 Res 4..9 |
| IN | 8 | soSoBhxh | String | ○ | Mã số BHXH (10 chữ số) trên path variable. | — | BD-08 API-002 Req 1 |
| OUT | 3 | personInfo | PersonInfoDto | ○ | Thông tin nhân thân (họ tên, ngày sinh, giới tính, CCCD, địa chỉ). | — | BD-08 API-002 Res 1..4 |
| OUT | 4 | violationSummary | ViolationSummaryDto | ○ | Tiêu chí vi phạm, thông tin thẻ mốc gốc, mốc hiện tại, tổng số ngày gián đoạn. | — | BD-08 API-002 Res 5..9 |
| OUT | 5 | summary | TimelineSummaryDto | ○ | Tổng số thẻ, số khoảng liên tục sau gộp, tổng ngày gián đoạn, cờ hasLongGap. | — | BD-08 API-003 Res 1..4 |
| OUT | 6 | cards | List<CardItemDto> | ○ | Toàn bộ danh sách thẻ BHYT hợp lệ trong kỳ của người này. | List rỗng [] | BD-08 API-003 Res 5 |
| OUT | 7 | mergedIntervals | List<DateIntervalDto> | ○ | Các khoảng tham gia liên tục sau khi gộp thẻ liên tiếp/chồng lấn. | List rỗng [] | BD-08 API-003 Res 6 |
| OUT | 8 | gaps | List<GapEpisodeDto> | ○ | Danh sách các đợt gián đoạn (đợt số, từ ngày, đến ngày, số ngày, loại gap). | List rỗng [] | BD-08 API-003 Res 7 |
| OUT | 9 | nationalSummary | NationalSummaryDto | ○ | Số liệu tổng hợp toàn quốc (dừng và gián đoạn). | — | BD-08 API-004 Res 2 |
| OUT | 10 | provinces | List<ProvinceItemDto> | ○ | Danh sách số liệu 63 tỉnh/thành phố. | — | BD-08 API-004 Res 3..5 |
| OUT | 11 | buckets | List<HistogramBucketDto> | ○ | Danh sách 5 khoảng phân bố thời gian gián đoạn. | — | BD-08 API-005 Res 3..6 |
| IN | 9 | exportRequest | ExportRequestDto | ○ | Chứa reportType (PERSONS_LIST...), fileFormat (XLSX/CSV), filters. | — | BD-08 API-006 Req 1..3 |
| OUT | 12 | exportResponse | ExportResponseDto | ○ | Chứa downloadUrl (sync) hoặc jobId, status PENDING (async). | — | BD-08 API-006 Res |
| EXCEPTION | 1 | ValidationException | — | — | Tham số không hợp lệ (mã BHXH sai, số trang âm...) -> HTTP 400 | — | MSG-E001..E009 |
| EXCEPTION | 2 | NotFoundException | — | — | Không tìm thấy người tham gia với mã số BHXH đã cho -> HTTP 404 | — | MSG-I001 |
| EXCEPTION | 3 | DataInconsistencyException | — | — | Dữ liệu vi phạm ràng buộc toàn vẹn (>1 bản ghi tổng hợp) -> HTTP 500 | — | MSG-E900 |
| EXCEPTION | 4 | SystemBusyException | — | — | Hệ thống bận, timeout DB hoặc worker quá tải -> HTTP 503 | — | MSG-E999 |

---

## XuLyChiTiet – Xử lý chi tiết

| Bước (No) | Nội dung xử lý | Điều kiện | Khi đúng | Khi sai | SQL / Check / MSG | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Khởi tạo ngữ cảnh truy vấn: sinh traceId, ghi log INFO nhận request kèm các tham số lọc. | — | — | — | — | Log traceId xuyên suốt |
| 2 | Kiểm tra tính hợp lệ của tham số đầu vào (Validation) | — | — | — | CHK-01 -> CHK-07 | Xem sheet 07 |
| 2.1 | Kiểm tra page và pageSize: page < 1 hoặc pageSize < 1 hoặc pageSize > 100 | Ném ValidationException(MSG-E002, 'Phân trang') | Sang 2.2 | CHK-01 | Kiểm tra phân trang |
| 2.2 | Kiểm tra provinceCode: provinceCode != null và không khớp danh mục tỉnh | Ném ValidationException(MSG-E004, provinceCode) | Sang 2.3 | CHK-02 | Kiểm tra mã tỉnh |
| 2.3 | Kiểm tra block và criteria: không thuộc tập giá trị cho phép | Ném ValidationException(MSG-E005 hoặc MSG-E006) | Sang 2.4 | CHK-03 | Kiểm tra mã khối, tiêu chí |
| 2.4 | Kiểm tra minGapDays và maxGapDays: min < 0 hoặc max < min | Ném ValidationException(MSG-E003) | Sang 3 | CHK-04 | Kiểm tra khoảng ngày |
| 3 | Xây dựng câu lệnh Dynamic SQL và binding tham số theo bộ lọc | — | — | — | SQL-01 | Sử dụng Param Binding |
| 4 | Thực thi đếm tổng số bản ghi thỏa mãn điều kiện lọc (COUNT) | COUNT == 0 | Trả về PageResponse với totalRecords=0, data=[] (HTTP 200) | Thực thi truy vấn lấy dữ liệu trang (bước 5) | SQL-01 (Count) | Tối ưu không query data nếu count=0 |
| 5 | Thực thi truy vấn lấy danh sách phân trang (SELECT với LIMIT / OFFSET hoặc Keyset) | — | Gán danh sách kết quả = rows | Sang bước 6 | SQL-01 (Select) | Đọc dữ liệu trang hiện tại |
| 6 | Map từng bản ghi dữ liệu DB sang DTO PersonSummaryDto | — | — | — | — | Chuẩn hóa định dạng ngày yyyy-MM-dd |
| 7 | Ghi Audit Log bất đồng bộ (Async): ghi nhận cán bộ tra cứu danh sách với bộ lọc | Ghi audit lỗi | Log WARN, KHÔNG ném lỗi | — | — | REQUIRES_NEW |
| 8 | Trả về PageResponse<PersonSummaryDto> (HTTP 200) | — | — | — | — | SLA p95 <= 300ms |
| 9 | Ghi log DEBUG: bắt đầu tra cứu chi tiết mã BHXH (che 4 số cuối) | — | — | — | — | Bảo mật PII |
| 10 | Kiểm tra định dạng soSoBhxh: khác 10 chữ số | soSoBhxh không khớp ^\d{10}$ | Ném ValidationException(MSG-E002, 'Mã số BHXH', '10 chữ số') | Sang bước 11 | CHK-05 | Validate mã số BHXH |
| 11 | Truy vấn bảng tổng hợp cá nhân theo SO_SO_BHXH | — | — | — | SQL-02 | Index Unique B-tree |
| 11.1 | Đánh giá số dòng kết quả từ SQL-02 | Số dòng == 0 (NOT FOUND) | Ném NotFoundException(MSG-I001, soSoBhxh) | Sang 11.2 | SQL-02 | Không có trong danh sách vi phạm |
| 11.2 | Đánh giá số dòng kết quả từ SQL-02 | Số dòng > 1 | Log ERROR 'Trùng mã BHXH', ném DataInconsistencyException(MSG-E900) | Sang 11.3 | SQL-02 | Lỗi bất biến dữ liệu |
| 11.3 | Lấy dòng duy nhất, gán thông tin vào PersonDetailDto | — | — | — | — | Map thông tin nhân thân & vi phạm |
| 12 | Ghi audit: userId, soSoBhxh, thời điểm, kết quả FOUND | Ghi audit lỗi | Log WARN, KHÔNG ném lỗi | — | — | REQUIRES_NEW |
| 13 | Trả về PersonDetailDto (HTTP 200) | — | — | — | — | SLA p95 <= 150ms |
| 14 | Kiểm tra định dạng soSoBhxh (10 số). Nếu sai ném ValidationException. | Sai format | Ném ValidationException(MSG-E002) | Sang bước 15 | CHK-05 | — |
| 15 | Đọc toàn bộ thẻ BHYT hợp lệ trong kỳ [2024-10-01, 2026-07-31] của người đó từ DB | — | — | — | SQL-03 | Lọc TRANG_THAI = 1 |
| 15.1 | Đánh giá số lượng thẻ | Số dòng == 0 | Ném NotFoundException(MSG-I001, soSoBhxh) | Sang bước 16 | SQL-03 | Người này không có thẻ hợp lệ |
| 16 | Thuật toán Hợp nhất đoạn (Interval Merging) gộp các thẻ liên tục và chồng lấn: | — | — | — | — | Thuật toán chuẩn Tuần 2 |
| 16.1 | Sắp xếp danh sách thẻ theo TU_NGAY tăng dần, sau đó DEN_NGAY tăng dần. | — | — | — | — | Sắp xếp ban đầu |
| 16.2 | Khởi tạo khoảng hiện tại: [cur_start, cur_end] = [card[0].tu_ngay, card[0].den_ngay]. | — | — | — | — | Khởi tạo mốc |
| 16.3 | Duyệt từng thẻ tiếp theo card[i]: | — | — | — | — | Vòng lặp i từ 1 đến N-1 |
| 16.3.1 | Nếu card[i].tu_ngay <= cur_end + 1 ngày (thẻ chồng lấn hoặc nối tiếp liên tục): | Đúng | cur_end = MAX(cur_end, card[i].den_ngay) | Sai (phát sinh ngắt quãng): Thêm [cur_start, cur_end] vào mergedIntervals; gán [cur_start, cur_end] = [card[i].tu_ngay, card[i].den_ngay] | — | Hợp nhất đoạn |
| 16.4 | Đẩy khoảng cuối cùng vào danh sách mergedIntervals. | — | — | — | — | Hoàn tất hợp nhất |
| 17 | Thuật toán Quét phát hiện khoảng trống gián đoạn (Gap Detection): | — | — | — | — | Kỳ xét: [2024-10-01, 2026-07-31] |
| 17.1 | Xét khoảng trống đầu kỳ: Nếu mergedIntervals[0].tu_ngay > '2024-10-01': | Đúng | Thêm gap: [2024-10-01, mergedIntervals[0].tu_ngay - 1 ngày], loại = DAU_KY | Sang 17.2 | — | Khoảng trống đầu kỳ |
| 17.2 | Xét các khoảng trống giữa các đoạn: Duyệt j từ 0 đến len(mergedIntervals) - 2: | — | Thêm gap: [merged[j].den_ngay + 1 ngày, merged[j+1].tu_ngay - 1 ngày], loại = GIUA_KY | — | — | Khoảng trống giữa kỳ |
| 17.3 | Xét khoảng trống cuối kỳ: Nếu mergedIntervals[-1].den_ngay < '2026-07-31': | Đúng | Thêm gap: [mergedIntervals[-1].den_ngay + 1 ngày, 2026-07-31], loại = CUOI_KY | Sang 18 | — | Khoảng trống cuối kỳ |
| 18 | Tính tổng số ngày gián đoạn: totalGapDays = SUM(gap.days). Đánh dấu hasLongGap = (totalGapDays >= 90). | — | — | — | — | Tổng hợp chỉ số |
| 19 | Đóng gói TimelineDetailDto gồm danh sách cards, mergedIntervals, gaps và summary. Trả về HTTP 200. | — | — | — | — | SLA p95 <= 250ms |
| 20 | API-004: Kiểm tra cache Redis với key 'REPORT:PROVINCES:' + criteria | Cache hit | Trả về dữ liệu từ Redis (HTTP 200) | Cache miss: Sang bước 21 | Redis GET | Tối ưu hóa độ trễ < 50ms |
| 21 | Truy vấn DB bảng TK_DBHC_HSSV_TONG_HOP | — | Lấy số liệu 63 tỉnh và tính tổng toàn quốc | Sang bước 22 | SQL-05 | Đọc bảng tổng hợp |
| 22 | Ghi kết quả vào Redis Cache với TTL = 86400 giây (24 giờ). Trả về response. | Lỗi Redis | Log WARN, vẫn trả dữ liệu DB về client | — | Redis SETEX | Khả năng chịu lỗi cache |
| 23 | API-005: Kiểm tra cache Redis 'REPORT:DISTRIBUTION:' + provinceCode + ':' + block | Cache hit | Trả về từ Redis | Cache miss: Sang 24 | Redis GET | — |
| 24 | Truy vấn bảng TK_PHAN_BO_GIAN_DOAN theo mã tỉnh và khối | — | Map 5 buckets phân bố | Ghi cache Redis và trả về HTTP 200 | SQL-06 | — |
| 25 | Kiểm tra đầu vào request export: reportType, fileFormat, filters | Sai tham số | Ném ValidationException | Sang bước 26 | CHK-06..08 | Validate yêu cầu xuất |
| 26 | Ước tính số lượng bản ghi thỏa mãn điều kiện lọc (COUNT query) | — | Gán estimatedCount = kết quả | Sang bước 27 | SQL-01 (Count) | Định lượng khối lượng |
| 27 | Phân luồng xử lý theo ngưỡng 10,000 dòng: | estimatedCount <= 10,000 | Xử lý ĐỒNG BỘ (bước 28) | Xử lý BẤT ĐỒNG BỘ (bước 29) | — | Tránh timeout HTTP connection |
| 28 | Xử lý đồng bộ: Streaming trực tiếp dữ liệu ra ByteArrayOutputStream -> Tạo file -> Đẩy MinIO -> Trả downloadUrl (HTTP 200) | — | — | — | SQL-07 | Xuất file nhanh |
| 29 | Xử lý bất đồng bộ: Tạo bản ghi trong SYS_EXPORT_JOB với status = PENDING -> Gửi message vào Redis Queue / RabbitMQ | — | Trả HTTP 202 Accepted kèm jobId và checkStatusUrl | Sang bước 30 | SQL-Export-Job | Khởi tạo job nền |
| 30 | Worker tiến trình ngầm nhận job: Đổi status = PROCESSING -> Mở cursor streaming dữ liệu từ DB theo chunk 5,000 dòng -> Ghi file temp -> Nén ZIP -> Đẩy lên MinIO Object Storage -> Cập nhật status = COMPLETED, downloadUrl, expiresAt. | Worker lỗi | Cập nhật status = FAILED, ghi log ERROR | — | — | Async Background Worker |
| 31 | BAT-001: Khởi động tiến trình DuckDB song song 8 luồng -> Quét 200 file parquet thô tại data/bhyt_data/st_inthe_dtl/ | — | — | — | — | Nạp dữ liệu thô |
| 32 | Làm sạch & Khử trùng toàn cục (GlobalDedupTracker): Khử trùng ID xuyên suốt 200 chunks; giữ TRANG_THAI IN (0, 1). Với lỗi đảo ngày TU_NGAY > DEN_NGAY: kích hoạt Smart Repair hoán đổi ngày nếu chu kỳ hợp lệ (25..375 ngày) và gắn cờ _FLAG_DATE_SWAPPED = True; dòng lỗi ngoài chu kỳ ghi vào quarantine. Đảm bảo phương trình bảo toàn: Bronze = Silver + Quarantine + Dedup_Global. | — | Ghi dữ liệu sạch ra data/silver/st_inthe_dtl/ | — | — | Chuẩn hóa Silver (Tuần 1 Ngày 5) |
| 33 | BAT-002 (Xử lý Ý 1): Lọc thẻ hợp lệ TRANG_THAI=1 -> Lọc tập HSSV T10/2024 -> Anti-join với tập có tham gia bất kỳ khối nào tại T08/2026 -> Áp dụng Tie-break (SV > HS, DEN_NGAY DESC, SO_THE_KCB ASC) chọn thẻ gốc đại diện -> Ghi Atomic Rename ra BC_HSSV_DUNG_THAM_GIA tầng Gold -> Tổng hợp 63 tỉnh. | — | — | — | SQL-08 (Ý 1) | Hoàn tất Ý 1 |
| 34 | BAT-003 (Xử lý Ý 2): Lọc ứng viên thỏa mãn đồng thời thẻ T10/2024 (HS/SV) và thẻ T07/2026 (bất kỳ khối) -> Cắt biên về kỳ [2024-10-01, 2026-07-31] -> Chạy Window Function MAX(den) OVER (ROWS UNBOUNDED PRECEDING AND 1 PRECEDING) gộp thẻ liên tục/chồng lấn/lồng nhau -> Tính tổng gap_days (cả 2 biên đầu/cuối kỳ và giữa các đoạn) -> Lọc gap_days >= 90 -> Ghi BC_HSSV_GIAN_DOAN_BHYT và bảng phân bố. | — | — | — | SQL-08 (Ý 2) | Hoàn tất Ý 2 |
| 35 | BAT-004: Bulk load dữ liệu Gold vào PostgreSQL Serving DB -> Refresh Redis Cache -> Ghi log nghiệm thu pipeline. | — | — | — | — | Đồng bộ Serving DB |

---

## DinhNghiaSQL – Định nghĩa SQL

### SQL-01 – Truy vấn danh sách HSSV vi phạm có lọc động và phân trang

```sql
SELECT P.SO_SO_BHXH, P.HO_TEN, P.NGAY_SINH, P.GIOI_TINH, P.SO_CMND,
       P.MA_KHOI_GOC, P.MA_TINH_GOC, P.TIEU_CHI, P.SO_DOT_GIAN_DOAN,
       P.SO_NGAY_GIAN_DOAN, P.SO_THANG_GIAN_DOAN, P.SO_THE_KCB_GOC
  FROM HSSV_PERSON_SUMMARY P
 WHERE (:provinceCode IS NULL OR P.MA_TINH_GOC = :provinceCode)
   AND (:block = 'ALL' OR P.MA_KHOI_GOC = :block)
   AND (:criteria = 'ALL' OR P.TIEU_CHI = :criteria)
   AND (:minGapDays IS NULL OR P.SO_NGAY_GIAN_DOAN >= :minGapDays)
   AND (:maxGapDays IS NULL OR P.SO_NGAY_GIAN_DOAN <= :maxGapDays)
   AND (:searchPattern IS NULL OR (
         P.SO_SO_BHXH = :searchPattern OR
         P.SO_CMND = :searchPattern OR
         P.HO_TEN_UNACCENT ILIKE :searchPatternLike
       ))
 ORDER BY
   CASE WHEN :sortBy = 'soSoBhxh' AND :sortOrder = 'ASC' THEN P.SO_SO_BHXH END ASC,
   CASE WHEN :sortBy = 'soSoBhxh' AND :sortOrder = 'DESC' THEN P.SO_SO_BHXH END DESC,
   CASE WHEN :sortBy = 'hoTen' AND :sortOrder = 'ASC' THEN P.HO_TEN END ASC,
   CASE WHEN :sortBy = 'hoTen' AND :sortOrder = 'DESC' THEN P.HO_TEN END DESC,
   CASE WHEN :sortBy = 'soNgayGianDoan' AND :sortOrder = 'ASC' THEN P.SO_NGAY_GIAN_DOAN END ASC,
   CASE WHEN :sortBy = 'soNgayGianDoan' AND :sortOrder = 'DESC' THEN P.SO_NGAY_GIAN_DOAN END DESC,
   P.SO_SO_BHXH ASC
 LIMIT :pageSize OFFSET :offset;
```

| Thuộc tính | Giá trị |
|---|---|
| **Tham số bind** | `:provinceCode, :block, :criteria, :minGapDays, :maxGapDays, :searchPattern, :searchPatternLike, :sortBy, :sortOrder, :pageSize, :offset` |
| **Index sử dụng** | `IDX_SUMMARY_FILTER (MA_TINH_GOC, TIEU_CHI, MA_KHOI_GOC), GIN_HO_TEN (HO_TEN_UNACCENT)` |
| **Số dòng kỳ vọng** | `0..pageSize (thực tế 20, 50, 100)` |
| **Có dữ liệu** | Map từng dòng dữ liệu sang PersonSummaryDto -> Trả về danh sách trang |
| **Không có (NOT FOUND)** | 0 dòng thỏa mãn -> Trả về List rỗng [] với totalRecords=0 (HTTP 200) |
| **Nhiều hơn kỳ vọng** | Không xảy ra vì có LIMIT :pageSize |
| **Lỗi DB / Timeout** | DataAccessException -> Bắt lỗi, log ERROR kèm traceId, ném SystemBusyException(MSG-E999) |
| **Khóa / Timeout** | Không khóa (chỉ đọc); timeout 5s |

### SQL-02 – Truy vấn thông tin chi tiết hồ sơ cá nhân theo mã số BHXH

```sql
SELECT P.SO_SO_BHXH, P.HO_TEN, P.NGAY_SINH, P.GIOI_TINH, P.SO_CMND, P.DIA_CHI,
       P.TIEU_CHI, P.MA_KHOI_GOC, P.MA_TINH_GOC, T.TEN_DVI AS TEN_TINH_GOC,
       P.DM_BHXH_ID_GOC, D.TEN_DVI AS TEN_CO_QUAN_GOC,
       P.SO_THE_KCB_GOC, P.TU_NGAY_GOC, P.DEN_NGAY_GOC,
       P.SO_THE_KCB_HIEN_TAI, P.MA_KHOI_HIEN_TAI, P.TU_NGAY_HIEN_TAI, P.DEN_NGAY_HIEN_TAI,
       P.SO_DOT_GIAN_DOAN, P.SO_NGAY_GIAN_DOAN, P.SO_THANG_GIAN_DOAN, P.CREATED_AT
  FROM HSSV_PERSON_SUMMARY P
  LEFT JOIN DM_BHXH D ON D.ID = P.DM_BHXH_ID_GOC
  LEFT JOIN DM_BHXH T ON T.MA_DVI = P.MA_TINH_GOC
 WHERE P.SO_SO_BHXH = :soSoBhxh;
```

| Thuộc tính | Giá trị |
|---|---|
| **Tham số bind** | `:soSoBhxh (chuỗi 10 chữ số đã chuẩn hóa)` |
| **Index sử dụng** | `PK_HSSV_PERSON_SUMMARY (SO_SO_BHXH) - Unique B-tree Index` |
| **Số dòng kỳ vọng** | `0 hoặc 1 dòng` |
| **Có dữ liệu** | 1 dòng -> Map sang PersonDetailDto -> Trả về HTTP 200 |
| **Không có (NOT FOUND)** | 0 dòng -> Ném NotFoundException(MSG-I001, soSoBhxh) -> HTTP 404 |
| **Nhiều hơn kỳ vọng** | > 1 dòng -> Vi phạm ràng buộc khóa! Log ERROR, ném DataInconsistencyException(MSG-E900) |
| **Lỗi DB / Timeout** | DataAccessException / QueryTimeout -> Log ERROR, ném SystemBusyException(MSG-E999) |
| **Khóa / Timeout** | Không khóa; timeout 3s |

### SQL-03 – Lấy toàn bộ lịch sử thẻ BHYT hợp lệ trong kỳ của một người phục vụ timeline

```sql
SELECT C.ID, C.SO_THE_KCB, C.MA_KHOI, C.TU_NGAY, C.DEN_NGAY,
       C.TRANG_THAI, C.DM_BHXH_ID, D.TEN_DVI
  FROM ST_INTHE_DTL C
  LEFT JOIN DM_BHXH D ON D.ID = C.DM_BHXH_ID
 WHERE C.SO_SO_BHXH = :soSoBhxh
   AND C.TRANG_THAI = 1
   AND C.TU_NGAY <= DATE '2026-07-31'
   AND C.DEN_NGAY >= DATE '2024-10-01'
 ORDER BY C.TU_NGAY ASC, C.DEN_NGAY ASC;
```

| Thuộc tính | Giá trị |
|---|---|
| **Tham số bind** | `:soSoBhxh (10 số)` |
| **Index sử dụng** | `IDX_CARDS_PERSON_TIMELINE (SO_SO_BHXH, TU_NGAY, DEN_NGAY)` |
| **Số dòng kỳ vọng** | `0..n (thực tế 1 đến 15 thẻ)` |
| **Có dữ liệu** | >= 1 dòng -> Đưa vào danh sách cards -> Chạy thuật toán Interval Merging |
| **Không có (NOT FOUND)** | 0 dòng -> Ném NotFoundException(MSG-I001, soSoBhxh) -> HTTP 404 |
| **Nhiều hơn kỳ vọng** | Không áp dụng |
| **Lỗi DB / Timeout** | DataAccessException -> Log ERROR traceId, ném SystemBusyException(MSG-E999) |
| **Khóa / Timeout** | Không khóa; timeout 4s |

### SQL-04 – Lấy chi tiết các đợt gián đoạn đã tính toán sẵn trong bảng lịch sử

```sql
SELECT G.DOT_NO, G.TU_NGAY, G.DEN_NGAY, G.SO_NGAY, G.PHAN_LOAI, G.GHI_CHU
  FROM BC_HSSV_GAP_HISTORY G
 WHERE G.SO_SO_BHXH = :soSoBhxh
 ORDER BY G.DOT_NO ASC;
```

| Thuộc tính | Giá trị |
|---|---|
| **Tham số bind** | `:soSoBhxh (10 số)` |
| **Index sử dụng** | `IDX_GAP_PERSON (SO_SO_BHXH, DOT_NO)` |
| **Số dòng kỳ vọng** | `0..n (thực tế 0 đến 6 đợt gián đoạn)` |
| **Có dữ liệu** | >= 1 dòng -> Map sang List<GapEpisodeDto> |
| **Không có (NOT FOUND)** | 0 dòng -> List rỗng [] (trường hợp người dừng tham gia không có đợt gián đoạn) |
| **Nhiều hơn kỳ vọng** | Không áp dụng |
| **Lỗi DB / Timeout** | DataAccessException -> Log ERROR, ném SystemBusyException(MSG-E999) |
| **Khóa / Timeout** | Không khóa; timeout 3s |

### SQL-05 – Thống kê tổng hợp số liệu theo 63 Tỉnh/Thành phố

```sql
SELECT T.MA_TINH, T.TEN_TINH,
       T.SO_LUONG_HS_DUNG, T.SO_LUONG_SV_DUNG, T.TONG_SO_DUNG,
       T.SO_LUONG_HS_GIAN_DOAN, T.SO_LUONG_SV_GIAN_DOAN, T.TONG_SO_GIAN_DOAN,
       T.TONG_NGAY_GIAN_DOAN, T.NGAY_GIAN_DOAN_TRUNG_BINH
  FROM TK_DBHC_HSSV_TONG_HOP T
 ORDER BY
   CASE WHEN :sortBy = 'maTinh' AND :sortOrder = 'ASC' THEN T.MA_TINH END ASC,
   CASE WHEN :sortBy = 'maTinh' AND :sortOrder = 'DESC' THEN T.MA_TINH END DESC,
   CASE WHEN :sortBy = 'tongDung' AND :sortOrder = 'ASC' THEN T.TONG_SO_DUNG END ASC,
   CASE WHEN :sortBy = 'tongDung' AND :sortOrder = 'DESC' THEN T.TONG_SO_DUNG END DESC,
   CASE WHEN :sortBy = 'tongGianDoan' AND :sortOrder = 'ASC' THEN T.TONG_SO_GIAN_DOAN END ASC,
   CASE WHEN :sortBy = 'tongGianDoan' AND :sortOrder = 'DESC' THEN T.TONG_SO_GIAN_DOAN END DESC,
   T.MA_TINH ASC;
```

| Thuộc tính | Giá trị |
|---|---|
| **Tham số bind** | `:sortBy, :sortOrder` |
| **Index sử dụng** | `PK_TK_DBHC_TONG_HOP (MA_TINH)` |
| **Số dòng kỳ vọng** | `Chính xác 63 dòng (ứng với 63 tỉnh/thành phố)` |
| **Có dữ liệu** | 63 dòng -> Map sang ProvinceReportDto, tính lũy kế toàn quốc nationalSummary |
| **Không có (NOT FOUND)** | 0 dòng -> Bảng chưa được nạp batch! Log ERROR cảnh báo, trả 503 SystemBusy |
| **Nhiều hơn kỳ vọng** | > 63 dòng -> Dữ liệu trùng lặp tỉnh! Log ERROR |
| **Lỗi DB / Timeout** | DataAccessException -> Log ERROR, trả HTTP 500/503 |
| **Khóa / Timeout** | Không khóa; timeout 5s |

### SQL-06 – Thống kê phân bố thời gian gián đoạn theo 5 buckets quy chuẩn

```sql
SELECT B.BUCKET_ID, B.LABEL, B.MIN_DAYS, B.MAX_DAYS,
       B.COUNT_HS, B.COUNT_SV, B.TOTAL_COUNT, B.PERCENTAGE, B.AVG_GAP_DAYS
  FROM TK_PHAN_BO_GIAN_DOAN B
 WHERE (:provinceCode IS NULL OR B.MA_TINH = :provinceCode)
   AND (:block = 'ALL' OR B.MA_KHOI = :block)
 ORDER BY B.BUCKET_ID ASC;
```

| Thuộc tính | Giá trị |
|---|---|
| **Tham số bind** | `:provinceCode, :block` |
| **Index sử dụng** | `IDX_DISTRIBUTION (MA_TINH, MA_KHOI, BUCKET_ID)` |
| **Số dòng kỳ vọng** | `5 dòng (ứng với 5 khoảng quy chuẩn)` |
| **Có dữ liệu** | 5 dòng -> Map sang HistogramBucketDto |
| **Không có (NOT FOUND)** | 0 dòng -> Trả về 5 buckets với totalCount = 0 |
| **Nhiều hơn kỳ vọng** | Không áp dụng |
| **Lỗi DB / Timeout** | DataAccessException -> Log ERROR, ném SystemBusyException(MSG-E999) |
| **Khóa / Timeout** | Không khóa; timeout 3s |

### SQL-07 – Streaming dữ liệu lớn phục vụ xuất báo cáo Excel / CSV

```sql
SELECT P.SO_SO_BHXH, P.HO_TEN, TO_CHAR(P.NGAY_SINH, 'DD/MM/YYYY') AS NGAY_SINH_STR,
       CASE WHEN P.GIOI_TINH = 1 THEN 'Nam' ELSE 'Nữ' END AS GIOI_TINH_STR,
       P.SO_CMND, P.DIA_CHI, P.MA_KHOI_GOC, P.MA_TINH_GOC, T.TEN_DVI AS TEN_TINH_GOC,
       P.TIEU_CHI, P.SO_THE_KCB_GOC, TO_CHAR(P.TU_NGAY_GOC, 'DD/MM/YYYY') AS TU_NGAY_GOC_STR,
       TO_CHAR(P.DEN_NGAY_GOC, 'DD/MM/YYYY') AS DEN_NGAY_GOC_STR,
       P.SO_THE_KCB_HIEN_TAI, P.MA_KHOI_HIEN_TAI,
       P.SO_DOT_GIAN_DOAN, P.SO_NGAY_GIAN_DOAN, P.SO_THANG_GIAN_DOAN
  FROM HSSV_PERSON_SUMMARY P
  LEFT JOIN DM_BHXH T ON T.MA_DVI = P.MA_TINH_GOC
 WHERE (:provinceCode IS NULL OR P.MA_TINH_GOC = :provinceCode)
   AND (:block = 'ALL' OR P.MA_KHOI_GOC = :block)
   AND (:criteria = 'ALL' OR P.TIEU_CHI = :criteria)
   AND (:minGapDays IS NULL OR P.SO_NGAY_GIAN_DOAN >= :minGapDays)
   AND (:maxGapDays IS NULL OR P.SO_NGAY_GIAN_DOAN <= :maxGapDays)
 ORDER BY P.MA_TINH_GOC ASC, P.SO_SO_BHXH ASC;
```

| Thuộc tính | Giá trị |
|---|---|
| **Tham số bind** | `:provinceCode, :block, :criteria, :minGapDays, :maxGapDays` |
| **Index sử dụng** | `IDX_SUMMARY_FILTER (MA_TINH_GOC, TIEU_CHI, MA_KHOI_GOC)` |
| **Số dòng kỳ vọng** | `0..n (từ vài nghìn đến hàng triệu dòng)` |
| **Có dữ liệu** | Mở Cursor / Fetch size 5,000 dòng -> Ghi tuần tự ra streaming output |
| **Không có (NOT FOUND)** | Xuất file chỉ có dòng header, không có dòng dữ liệu |
| **Nhiều hơn kỳ vọng** | Không áp dụng |
| **Lỗi DB / Timeout** | Lỗi worker -> Đánh dấu Export Job FAILED, ghi log ERROR |
| **Khóa / Timeout** | Không khóa; timeout connection 15 phút (cho batch streaming) |

### SQL-08 – Câu lệnh DuckDB SQL xử lý hợp nhất chuỗi thời gian (Interval Merging) trên 200M dòng thẻ BHYT

```sql
-- Tầng xử lý DuckDB SQL trên 200M dòng thẻ BHYT (Chuẩn hóa theo gold_logic_y2.py Tuần 2)
WITH valid_cards AS (
    SELECT SO_SO_BHXH, MA_KHOI, TU_NGAY, DEN_NGAY,
           GREATEST(TU_NGAY, DATE '2024-10-01') AS tu_clip,
           LEAST(DEN_NGAY, DATE '2026-07-31') AS den_clip
      FROM st_inthe_dtl_silver
     WHERE TRANG_THAI = 1
),
candidates AS (
    -- Thỏa mãn đồng thời ĐK1 (HSSV tại T10/2024) và ĐK2 (còn tham gia bất kỳ khối tại T07/2026)
    SELECT DISTINCT b.SO_SO_BHXH
      FROM valid_cards b
      JOIN valid_cards c ON b.SO_SO_BHXH = c.SO_SO_BHXH
     WHERE b.MA_KHOI IN ('HS', 'SV')
       AND b.TU_NGAY < DATE '2024-11-01' AND b.DEN_NGAY >= DATE '2024-10-01'
       AND c.TU_NGAY < DATE '2026-08-01' AND c.DEN_NGAY >= DATE '2026-07-01'
),
cand_window_cards AS (
    SELECT v.SO_SO_BHXH, v.tu_clip AS tu, v.den_clip AS den
      FROM valid_cards v
      JOIN candidates cd ON v.SO_SO_BHXH = cd.SO_SO_BHXH
     WHERE v.tu_clip <= v.den_clip
),
with_prev AS (
    -- Dùng MAX(den) OVER (... UNBOUNDED PRECEDING AND 1 PRECEDING) xử lý triệt để thẻ lồng nhau
    SELECT SO_SO_BHXH, tu, den,
           MAX(den) OVER (
               PARTITION BY SO_SO_BHXH ORDER BY tu, den
               ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
           ) AS prev_max_den
      FROM cand_window_cards
),
marked_islands AS (
    SELECT SO_SO_BHXH, tu, den,
           CASE WHEN prev_max_den IS NULL OR tu > prev_max_den + INTERVAL 1 DAY THEN 1 ELSE 0 END AS is_new_grp
      FROM with_prev
),
grouped_islands AS (
    SELECT SO_SO_BHXH, tu, den,
           SUM(is_new_grp) OVER (
               PARTITION BY SO_SO_BHXH ORDER BY tu, den
               ROWS UNBOUNDED PRECEDING
           ) AS grp_id
      FROM marked_islands
),
merged_intervals AS (
    SELECT SO_SO_BHXH, grp_id,
           MIN(tu) AS m_tu,
           MAX(den) AS m_den
      FROM grouped_islands
     GROUP BY SO_SO_BHXH, grp_id
),
with_gaps AS (
    SELECT SO_SO_BHXH, m_tu, m_den,
           (m_tu - LAG(m_den) OVER (PARTITION BY SO_SO_BHXH ORDER BY m_tu) - 1) AS gap_days
      FROM merged_intervals
),
gap_events AS (
    SELECT SO_SO_BHXH, gap_days FROM with_gaps WHERE gap_days > 0
    UNION ALL
    SELECT SO_SO_BHXH, (MIN(m_tu) - DATE '2024-10-01') AS gap_days
      FROM merged_intervals GROUP BY SO_SO_BHXH HAVING MIN(m_tu) > DATE '2024-10-01'
    UNION ALL
    SELECT SO_SO_BHXH, (DATE '2026-07-31' - MAX(m_den)) AS gap_days
      FROM merged_intervals GROUP BY SO_SO_BHXH HAVING MAX(m_den) < DATE '2026-07-31'
)
SELECT SO_SO_BHXH,
       COUNT(gap_days) AS SO_DOT_GIAN_DOAN,
       COALESCE(SUM(gap_days), 0) AS TONG_NGAY_GIAN_DOAN,
       ROUND(COALESCE(SUM(gap_days), 0) / 30.0, 1) AS SO_THANG_GIAN_DOAN
  FROM gap_events
 GROUP BY SO_SO_BHXH
HAVING COALESCE(SUM(gap_days), 0) >= 90;
```

| Thuộc tính | Giá trị |
|---|---|
| **Tham số bind** | `None (Chạy theo Batch trên thư mục Parquet)` |
| **Index sử dụng** | `Phân vùng Parquet theo Chunk/Tỉnh` |
| **Số dòng kỳ vọng** | `~241.869 người HSSV gián đoạn >= 90 ngày (từ ~5M HSSV)` |
| **Có dữ liệu** | Lọc TONG_NGAY_GIAN_DOAN >= 90 -> Ghi vào Gold Parquet |
| **Không có (NOT FOUND)** | 0 dòng thỏa mãn -> Cảnh báo dữ liệu nguồn trống |
| **Nhiều hơn kỳ vọng** | Không áp dụng |
| **Lỗi DB / Timeout** | DuckDB Execution Error -> Ghi log trace, dừng pipeline và cảnh báo hệ thống |
| **Khóa / Timeout** | Batch Engine Timeout 30 phút |


---

## KiemTraDauVao – Đặc tả kiểm tra

| Check-ID | Hạng mục | Loại kiểm tra | Điều kiện lỗi | Mã thông báo | Thứ tự | Dừng ngay khi lỗi? | Tham chiếu BD |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CHK-01 | page | Bắt buộc / Miền giá trị | page == null hoặc page < 1 | MSG-E002 | 1 | Có | 08 – API-001 Req 7 |
| CHK-02 | pageSize | Bắt buộc / Miền giá trị | pageSize == null hoặc pageSize < 1 hoặc pageSize > 100 | MSG-E002 | 2 | Có | 08 – API-001 Req 8 |
| CHK-03 | provinceCode | Danh mục | provinceCode != null và không khớp ^\d{2}$ (01..96) | MSG-E004 | 3 | Có | 08 – API-001 Req 1 |
| CHK-04 | block | Giá trị cho phép | block != null và block NOT IN ('HS', 'SV', 'ALL') | MSG-E005 | 4 | Có | 08 – API-001 Req 2 |
| CHK-05 | criteria | Giá trị cho phép | criteria != null và criteria NOT IN ('DUNG_THAM_GIA', 'GIAN_DOAN', 'ALL') | MSG-E006 | 5 | Có | 08 – API-001 Req 3 |
| CHK-06 | minGapDays / maxGapDays | Logic khoảng | minGapDays < 0 hoặc maxGapDays < 0 hoặc (min != null & max != null & min > max) | MSG-E003 | 6 | Có | 08 – API-001 Req 5,6 |
| CHK-07 | search | Độ dài ký tự | search != null và search.trim().length() > 100 | MSG-E002 | 7 | Có | 08 – API-001 Req 4 |
| CHK-08 | soSoBhxh | Bắt buộc / Định dạng | soSoBhxh == null hoặc không khớp ^\d{10}$ sau trim | MSG-E002 | 1 | Có | 08 – API-002, 003 Req 1 |
| CHK-09 | sortBy | Giá trị cho phép | sortBy != null và sortBy NOT IN ('soSoBhxh', 'hoTen', 'soNgayGianDoan', 'maTinh', 'tongDung', 'tongGianDoan') | MSG-E002 | 8 | Có | 08 – API-001, 004 |
| CHK-10 | sortOrder | Giá trị cho phép | sortOrder != null và sortOrder NOT IN ('ASC', 'DESC', 'asc', 'desc') | MSG-E002 | 9 | Có | 08 – API-001, 004 |
| CHK-11 | reportType | Bắt buộc / Danh mục | reportType == null hoặc NOT IN ('PERSONS_LIST', 'PROVINCE_SUMMARY', 'DISTRIBUTION') | MSG-E009 | 1 | Có | 08 – API-006 Req 1 |
| CHK-12 | fileFormat | Bắt buộc / Định dạng | fileFormat == null hoặc NOT IN ('XLSX', 'CSV') | MSG-E008 | 2 | Có | 08 – API-006 Req 2 |
| CHK-13 | jobId | Bắt buộc / Định dạng | jobId == null hoặc không khớp định dạng UUID | MSG-E002 | 1 | Có | 08 – API-006 Poll Req |
| CHK-14 | Dữ liệu thẻ (Batch) | Toàn vẹn logic | TU_NGAY > DEN_NGAY (Xét chu kỳ Δ = TU_NGAY - DEN_NGAY) | Nếu 25 <= Δ <= 375d: Smart Repair hoán đổi ngày & gắn _FLAG_DATE_SWAPPED=True; ngược lại ghi vào quarantine | 1 | Không (tiếp tục dòng sau) | 09 – BAT-001 |
| CHK-15 | Dữ liệu thẻ (Batch) | Trạng thái thẻ | TRANG_THAI NOT IN (0, 1) | Ghi vào quarantine | 2 | Không | 09 – BAT-001 |

---

## XuLyLoi_Log – Xử lý ngoại lệ & log

| Tình huống | Exception | HTTP | Mã thông báo | Mức log | Nội dung log | Rollback? | Ghi chú |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Sai tham số đầu vào | ValidationException | 400 | MSG-E001..E009 | INFO | traceId, checkId, paramName, invalidValue | — | Không phải lỗi hệ thống |
| Không tìm thấy cá nhân | NotFoundException | 404 | MSG-I001 | INFO | traceId, soSoBhxh (che 4 số cuối) | — | Cá nhân không vi phạm CV 835 |
| Trùng bản ghi cá nhân | DataInconsistencyException | 500 | MSG-E900 | ERROR | traceId, soSoBhxh đầy đủ, actualCount | Có | Cảnh báo khẩn cấp kỹ thuật |
| Timeout truy vấn DB | QueryTimeoutException | 503 | MSG-E999 | ERROR | traceId, sqlId, durationMs, queryParams | — | Kích hoạt Circuit Breaker |
| Mất kết nối Database | CannotGetJdbcConnectionException | 503 | MSG-E999 | FATAL | traceId, dbHost, errorMessage | — | Báo động Ops/DevOps ngay |
| Lỗi Redis Cache | RedisConnectionException | — | — | WARN | traceId, redisKey, errorMessage | — | Tự động fallback sang đọc DB |
| Lỗi Worker xuất file | ExportWorkerException | 500 | MSG-E010 | ERROR | traceId, jobId, errorDetail, stackTrace | Có | Cập nhật status = FAILED |
| Lỗi ghi Audit Log | Exception (bất kỳ) | — | — | WARN | traceId, userId, errorMessage | Chỉ rollback audit | Không ảnh hưởng kết quả API |
| Lỗi Batch Data Pipeline | PipelineExecutionException | — | — | FATAL | batchId, stepNo, inputFile, errorMessage | Toàn bộ batch | Dừng job, thông báo kênh On-Call |

---

## UnitTest – Đặc tả kiểm thử đơn vị

| UT-ID | Phân loại | Bước DD (sheet 05) | Điều kiện tiền đề / dữ liệu | Đầu vào | Thao tác | Kết quả kỳ vọng | Kết quả thực tế | OK/NG | Người test | Ngày test | Bug ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UT-001 | Bất thường | 2.1 | API-001: page âm | page = -1, pageSize = 20 | Gọi GET /api/v1/hssv/persons | ValidationException, MSG-E002, HTTP 400 | ValidationException, MSG-E002 | OK | Tester 1 | 2026/10/28 |  |
| UT-002 | Biên | 2.1 | API-001: pageSize biên trên (100) | page = 1, pageSize = 100 | Gọi GET /api/v1/hssv/persons | HTTP 200, trả tối đa 100 dòng | HTTP 200, 100 dòng | OK | Tester 1 | 2026/10/28 |  |
| UT-003 | Bất thường | 2.1 | API-001: pageSize vượt ngưỡng (>100) | page = 1, pageSize = 101 | Gọi GET /api/v1/hssv/persons | ValidationException, MSG-E002, HTTP 400 | ValidationException, MSG-E002 | OK | Tester 1 | 2026/10/28 |  |
| UT-004 | Bất thường | 2.2 | API-001: provinceCode sai định dạng | provinceCode = 'ABC' | Gọi GET /api/v1/hssv/persons | ValidationException, MSG-E004, HTTP 400 | ValidationException, MSG-E004 | OK | Tester 1 | 2026/10/28 |  |
| UT-005 | Bình thường | 2.2, 5, 8 | API-001: Lọc theo tỉnh Hà Nội (01), khối HS | provinceCode = '01', block = 'HS' | Gọi GET /api/v1/hssv/persons | HTTP 200, 100% bản ghi có MA_TINH=01 & MA_KHOI=HS | HTTP 200, đúng kết quả | OK | Tester 1 | 2026/10/28 |  |
| UT-006 | Bình thường | 2.3, 5, 8 | API-001: Lọc tiêu chí dừng tham gia | criteria = 'DUNG_THAM_GIA' | Gọi GET /api/v1/hssv/persons | HTTP 200, 100% bản ghi có TIEU_CHI=DUNG_THAM_GIA | HTTP 200, đúng kết quả | OK | Tester 1 | 2026/10/28 |  |
| UT-007 | Biên | 2.4 | API-001: Lọc khoảng ngày min=max=90 | minGapDays=90, maxGapDays=90 | Gọi GET /api/v1/hssv/persons | HTTP 200, các bản ghi có số ngày gián đoạn chính xác 90 | HTTP 200, lọc đúng | OK | Tester 1 | 2026/10/28 |  |
| UT-008 | Bất thường | 2.4 | API-001: minGapDays > maxGapDays | minGapDays=120, maxGapDays=90 | Gọi GET /api/v1/hssv/persons | ValidationException, MSG-E003, HTTP 400 | ValidationException, MSG-E003 | OK | Tester 1 | 2026/10/28 |  |
| UT-009 | Bình thường | 4 | API-001: Bộ lọc không có dữ liệu | search = '9999999999' | Gọi GET /api/v1/hssv/persons | HTTP 200, totalRecords = 0, data = [] | HTTP 200, data = [] | OK | Tester 1 | 2026/10/28 |  |
| UT-010 | Bất thường | 10 | API-002: Mã số BHXH null | soSoBhxh = null | Gọi GET /api/v1/hssv/persons/ | HTTP 404 / 400 | HTTP 404 | OK | Tester 2 | 2026/10/28 |  |
| UT-011 | Bất thường | 10 | API-002: Mã số BHXH chứa chữ cái | soSoBhxh = '012345678A' | Gọi GET /api/v1/hssv/persons/012345678A | ValidationException, MSG-E002, HTTP 400 | ValidationException, MSG-E002 | OK | Tester 2 | 2026/10/28 |  |
| UT-012 | Biên | 10 | API-002: Mã số BHXH 9 số (thiếu 1 số) | soSoBhxh = '012345678' | Gọi GET /api/v1/hssv/persons/012345678 | ValidationException, MSG-E002, HTTP 400 | ValidationException, MSG-E002 | OK | Tester 2 | 2026/10/28 |  |
| UT-013 | Bình thường | 11.3, 13 | API-002: Xem người dừng tham gia tồn tại | soSoBhxh = '0123456789' (Dừng) | Gọi GET /api/v1/hssv/persons/0123456789 | HTTP 200, tieuChi=DUNG_THAM_GIA, mocHienTai=null | HTTP 200, đúng spec | OK | Tester 2 | 2026/10/28 |  |
| UT-014 | Bình thường | 11.3, 13 | API-002: Xem người gián đoạn >= 3 tháng tồn tại | soSoBhxh = '0198765432' (Gián đoạn) | Gọi GET /api/v1/hssv/persons/0198765432 | HTTP 200, tieuChi=GIAN_DOAN, soNgayGianDoan >= 90 | HTTP 200, đúng spec | OK | Tester 2 | 2026/10/28 |  |
| UT-015 | Bất thường | 11.1 | API-002: Mã số BHXH hợp lệ nhưng không vi phạm | soSoBhxh = '0111111111' (Không vi phạm) | Gọi GET /api/v1/hssv/persons/0111111111 | NotFoundException, MSG-I001, HTTP 404 | NotFoundException, MSG-I001 | OK | Tester 2 | 2026/10/28 |  |
| UT-016 | Bất thường | 11.2 | API-002: Giả lập DB bị trùng mã BHXH (>1 dòng) | soSoBhxh = '0122222222' | Mock repository trả 2 dòng | DataInconsistencyException, MSG-E900, HTTP 500 | DataInconsistencyException, 500 | OK | Tester 2 | 2026/10/28 |  |
| UT-017 | Bình thường | 16, 17, 19 | API-003: Người có 2 thẻ nối tiếp liên tục (không gap) | Thẻ 1 hạn 31/12/2024, Thẻ 2 bắt đầu 01/01/2025 | Gọi GET timeline | HTTP 200, mergedIntervals=1 khoảng, totalGapDays=0 | HTTP 200, totalGapDays=0 | OK | Tester 2 | 2026/10/28 |  |
| UT-018 | Bình thường | 16, 17, 19 | API-003: Người có 2 thẻ chồng lấn (gối đầu nhau) | Thẻ 1 đến 30/06/2025, Thẻ 2 từ 01/05/2025 | Gọi GET timeline | HTTP 200, gộp thành 1 khoảng liên tục, không tính gap | HTTP 200, đúng giải thuật | OK | Tester 2 | 2026/10/28 |  |
| UT-019 | Biên | 17.1 | API-003: Thẻ đầu bắt đầu 15/10/2024 (gap đầu kỳ) | Thẻ đầu từ 2024-10-15 | Gọi GET timeline | gaps[0] từ 2024-10-01 đến 2024-10-14 (14 ngày), loại DAU_KY | HTTP 200, phát hiện gap đầu kỳ | OK | Tester 2 | 2026/10/28 |  |
| UT-020 | Biên | 17.3 | API-003: Thẻ cuối hết hạn 15/07/2026 (gap cuối kỳ) | Thẻ cuối đến 2026-07-15 | Gọi GET timeline | gaps có đợt từ 2026-07-16 đến 2026-07-31 (16 ngày), loại CUOI_KY | HTTP 200, phát hiện gap cuối kỳ | OK | Tester 2 | 2026/10/28 |  |
| UT-021 | Bình thường | 17.2, 18 | API-003: Cộng dồn 2 đợt gián đoạn (30d + 60d = 90d) | Đợt 1 gap 30 ngày, Đợt 2 gap 60 ngày | Gọi GET timeline | HTTP 200, totalGapDays=90, hasLongGap=true | HTTP 200, hasLongGap=true | OK | Tester 2 | 2026/10/28 |  |
| UT-022 | Biên | 18 | API-003: Tổng gián đoạn 89 ngày (dưới ngưỡng 90d) | Tổng gap = 89 ngày | Gọi GET timeline | HTTP 200, totalGapDays=89, hasLongGap=false | HTTP 200, hasLongGap=false | OK | Tester 2 | 2026/10/28 |  |
| UT-023 | Bình thường | 20, 22 | API-004: Đọc báo cáo 63 tỉnh khi cache miss | Redis chưa có key | Gọi GET /api/v1/hssv/reports/provinces | HTTP 200, đủ 63 tỉnh, nạp cache Redis thành công | HTTP 200, 63 tỉnh | OK | Tester 3 | 2026/10/28 |  |
| UT-024 | Bình thường | 20 | API-004: Đọc báo cáo 63 tỉnh khi cache hit | Redis đã có key | Gọi GET /api/v1/hssv/reports/provinces | HTTP 200 từ Redis, response time <= 20ms | HTTP 200, 15ms | OK | Tester 3 | 2026/10/28 |  |
| UT-025 | Bình thường | 23, 24 | API-005: Đọc phân bố toàn quốc | provinceCode = null, block = 'ALL' | Gọi GET /api/v1/hssv/reports/distribution | HTTP 200, 5 buckets, tổng tỷ lệ = 100.0% | HTTP 200, 5 buckets | OK | Tester 3 | 2026/10/28 |  |
| UT-026 | Bình thường | 27, 28 | API-006: Xuất báo cáo đồng bộ (<= 10,000 dòng) | Dữ liệu thỏa mãn 5,000 dòng | Gọi POST /api/v1/hssv/reports/export | HTTP 200, trả về downloadUrl trực tiếp | HTTP 200, có downloadUrl | OK | Tester 3 | 2026/10/28 |  |
| UT-027 | Bình thường | 27, 29 | API-006: Xuất báo cáo bất đồng bộ (> 10,000 dòng) | Dữ liệu thỏa mãn 50,000 dòng | Gọi POST /api/v1/hssv/reports/export | HTTP 202 Accepted, trả về jobId và checkStatusUrl | HTTP 202, có jobId | OK | Tester 3 | 2026/10/28 |  |
| UT-028 | Bất thường | 25 | API-006: Định dạng file không hỗ trợ | fileFormat = 'PDF' | Gọi POST /api/v1/hssv/reports/export | ValidationException, MSG-E008, HTTP 400 | ValidationException, MSG-E008 | OK | Tester 3 | 2026/10/28 |  |
| UT-029 | Bất thường | — | Toàn hệ thống: Timeout database query | Mock query chạy quá 5s | Gọi bất kỳ API nào | SystemBusyException, MSG-E999, HTTP 503 | SystemBusyException, 503 | OK | Tester 1 | 2026/10/28 |  |
| UT-030 | Bình thường | 7 | Toàn hệ thống: Ghi audit log lỗi không làm lỗi API | Mock AuditLogService ném RuntimeException | Gọi GET /api/v1/hssv/persons | Vẫn trả về HTTP 200 cho client, có log WARN audit | HTTP 200, log WARN | OK | Tester 1 | 2026/10/28 |  |
| UT-031 | Bình thường | 31, 32 | BAT-001: Nạp Silver xử lý lỗi đảo ngày TU_NGAY > DEN_NGAY (Smart Repair & Quarantine) và Global Dedup liên chunk | Chunk có dòng trùng ID liên chunk, dòng đảo ngày chu kỳ 365d và dòng rác lệch 2000d | Chạy BAT-HSSV-001 | Khử trùng liên chunk; dòng chu kỳ 365d được hoán đổi ngày kèm _FLAG_DATE_SWAPPED=True; dòng rác vào quarantine; bảo toàn tổng số dòng | Khớp 100% phương trình bảo toàn, giải cứu 131 ca FP | OK | Kỹ sư Data | 2026/10/28 |  |
| UT-032 | Bình thường | 33, 34 | BAT-002/003: Chạy lại lần 2 (Idempotency check) | Dữ liệu nguồn không đổi | Chạy lại BAT-002 và BAT-003 | Kết quả đầu ra trùng khớp 100% về số dòng và hash SHA-256 | Trùng khớp 100% | OK | Kỹ sư Data | 2026/10/28 |  |

---

## QA – Quản lý hỏi đáp

| No | Ngày hỏi | Người hỏi | Sheet / Mục | Câu hỏi | Người trả lời | Trả lời | Ngày trả lời | Trạng thái | Đã phản ánh vào tài liệu? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026/10/24 | Kỹ sư backend | 05 - Bước 7 | Lỗi ghi audit có làm API trả mã lỗi về client không? | Tech Lead | Không. Giao dịch ghi audit chạy REQUIRES_NEW độc lập, nếu lỗi chỉ log WARN và vẫn trả dữ liệu 200 về client. | 2026/10/24 | Closed | Có (Mục 03, 05) |
| 2 | 2026/10/25 | Kỹ sư dữ liệu | 06 - SQL-08 | Thuật toán Interval Merging trên DuckDB có gây tràn bộ nhớ (OOM) khi xử lý 200M dòng không? | Solution Architect | Không. Sử dụng kỹ thuật Island & Gap với SUM() OVER Window Function và partition streaming theo chunk, đỉnh RAM đo được < 14GB. | 2026/10/25 | Closed | Có (Mục 03, 06) |
| 3 | 2026/10/26 | Kỹ sư backend | 05 - Bước 27 | Ngưỡng 10,000 dòng để chuyển sang Async Export có thể cấu hình được không? | Tech Lead | Có. Cấu hình qua biến môi trường EXPORT_SYNC_THRESHOLD (mặc định 10,000). | 2026/10/26 | Closed | Có (Mục 05) |
| 4 | 2026/10/27 | Tester | 09 - UnitTest | Bộ kiểm thử đơn vị có chạy tự động trong CI/CD pipeline không? | Tech Lead | Có. 100% test case UT-001 đến UT-032 tích hợp trong bộ pytest tự động chạy khi tạo Pull Request. | 2026/10/27 | Closed | Có (Mục 09) |
| 5 | 2026/10/28 | DevOps | 03 - Caching | Khi chạy lại batch Gold thì làm sao để Redis Cache tự động cập nhật dữ liệu mới? | Solution Architect | BAT-HSSV-004 tự động phát tín hiệu Event/PubSub xóa các key cache cũ và chủ động warm-up nạp dữ liệu mới vào Redis ngay khi batch kết thúc. | 2026/10/28 | Closed | Có (Mục 03, 05) |

# Tuần 3 — Thiết kế Hệ thống Xử lý 200M Dòng Thẻ BHYT & Cổng Dịch vụ API Tra cứu HSSV (CV 835/QLT)

Bộ tài liệu thiết kế hệ thống hoàn chỉnh kế thừa từ bài làm **Tuần 1 (Ý 1: HSSV dừng tham gia)** và **Tuần 2 (Ý 2: HSSV gián đoạn $\ge 3$ tháng)** theo Công văn số **835/QLT** ngày 10/08/2026 của BHXH Việt Nam.

---

## 1. Bắt đầu nhanh

1. Xem đề bài và yêu cầu thiết kế Tuần 3 tại [docs/requirements/yeu_cau_tuan3_thiet_ke_he_thong_api.md](../docs/requirements/yeu_cau_tuan3_thiet_ke_he_thong_api.md).
2. Tra cứu **Thiết kế cơ bản (Basic Design)**:
   - Bản đọc trực tiếp trên Git/Markdown: [ThietKeCoBan_BasicDesign_VN.md](ThietKeCoBan_BasicDesign_VN.md)
   - Bản biểu mẫu Excel (15 sheets): [ThietKeCoBan_BasicDesign_VN.xlsx](ThietKeCoBan_BasicDesign_VN.xlsx)
3. Tra cứu **Thiết kế chi tiết (Detail Design)**:
   - Bản đọc trực tiếp trên Git/Markdown: [ThietKeChiTiet_DetailDesign_VN.md](ThietKeChiTiet_DetailDesign_VN.md)
   - Bản biểu mẫu Excel (11 sheets): [ThietKeChiTiet_DetailDesign_VN.xlsx](ThietKeChiTiet_DetailDesign_VN.xlsx)

---

## 2. Danh mục 6 RESTful APIs trong Thiết kế

| Mã API | Method | Endpoint | Chức năng chính | Tham chiếu Basic Design | Tham chiếu Detail Design |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **API-HSSV-001** | `GET` | `/api/v1/hssv/persons` | Tra cứu danh sách HSSV lọc theo tỉnh, khối, tiêu chí, khoảng ngày gián đoạn, từ khóa và phân trang | `07_DSAPI`, `08_DinhNghiaAPI` | Bước `1..8`, `SQL-01`, `CHK-01..07`, `UT-001..009` |
| **API-HSSV-002** | `GET` | `/api/v1/hssv/persons/{soSoBhxh}` | Xem chi tiết hồ sơ nhân thân, thẻ mốc gốc T10/2024, thẻ mốc hiện tại và tóm tắt vi phạm | `07_DSAPI`, `08_DinhNghiaAPI` | Bước `9..13`, `SQL-02`, `CHK-08`, `UT-010..016` |
| **API-HSSV-003** | `GET` | `/api/v1/hssv/persons/{soSoBhxh}/timeline` | Xem chuỗi thẻ BHYT, các đoạn tham gia liên tục sau khi gộp (`Interval Merging`) và các đợt gián đoạn (`gaps`) | `07_DSAPI`, `08_DinhNghiaAPI` | Bước `14..19`, `SQL-03`, `SQL-04`, `UT-017..022` |
| **API-HSSV-004** | `GET` | `/api/v1/hssv/reports/provinces` | Thống kê số liệu dừng tham gia và gián đoạn $\ge 3$ tháng theo 63 Tỉnh/TP và toàn quốc | `07_DSAPI`, `08_DinhNghiaAPI` | Bước `20..22`, `SQL-05`, `UT-023..024` |
| **API-HSSV-005** | `GET` | `/api/v1/hssv/reports/distribution` | Thống kê phân bố thời gian gián đoạn theo 5 khoảng quy chuẩn (`90-120d` đến `>365d`) | `07_DSAPI`, `08_DinhNghiaAPI` | Bước `23..24`, `SQL-06`, `UT-025` |
| **API-HSSV-006** | `POST` | `/api/v1/hssv/reports/export` | Xuất báo cáo danh sách / thống kê ra Excel (`XLSX`) hoặc `CSV` (hỗ trợ Sync $\le 10.000$ dòng & Async Worker $> 10.000$ dòng) | `07_DSAPI`, `08_DinhNghiaAPI` | Bước `25..30`, `SQL-07`, `CHK-11..13`, `UT-026..028` |

---

## 3. Liên kết truy vết (Traceability) với Bài làm Tuần 1 & Tuần 2

| Hạng mục Thiết kế (Tuần 3) | Kế thừa từ Bài làm Tuần 1 & Tuần 2 | Tài liệu / Code đối chiếu |
| :--- | :--- | :--- |
| **`BAT-HSSV-001` (Bronze $\rightarrow$ Silver)** | Khử trùng toàn cục `GlobalDedupTracker` và sửa lỗi đảo ngày có kiểm soát (`Smart Repair` chu kỳ $25..375$ ngày, gắn cờ `_FLAG_DATE_SWAPPED`) | [`build_silver.py`](../bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/build_silver.py), [`bao_cao_ngay5.md`](../bai_tuan1_y1_hssv_dung_bhyt/bao_cao/bao_cao_ngay5.md) |
| **`BAT-HSSV-002` (Gold Ý 1)** | Lọc HSSV T10/2024, Anti-join với tập tham gia T08/2026, Tie-break (`SV > HS`, `DEN_NGAY DESC`, `SO_THE_KCB ASC`), xuất `BC_HSSV_DUNG_THAM_GIA` (`848.413` người) | [`build_gold.py`](../bai_tuan1_y1_hssv_dung_bhyt/p3_gold/build_gold.py), [`ddl_output_tables.sql`](../bai_tuan1_y1_hssv_dung_bhyt/p3_gold/ddl_output_tables.sql) |
| **`BAT-HSSV-003` & `SQL-08` (Gold Ý 2)** | Lọc ứng viên 2 mốc T10/2024 & T07/2026, cắt biên `[2024-10-01, 2026-07-31]`, gộp đoạn bằng `MAX(den) OVER (... UNBOUNDED PRECEDING AND 1 PRECEDING)`, tính gap cả 2 đầu kỳ và giữa kỳ $\ge 90$ ngày (`241.869` người) | [`gold_logic_y2.py`](../bai_tuan2_y2_hssv_gian_doan/p3_gold/gold_logic_y2.py), [`thuat_toan_timeline.md`](../bai_tuan2_y2_hssv_gian_doan/p2_thuat_toan_timeline/thuat_toan_timeline.md) |
| **`BAT-HSSV-004` (Serving DB & Cache)** | Hợp nhất Gold Ý 1 và Ý 2 vào bảng `HSSV_PERSON_SUMMARY` (`TBL-HSSV-010`), chi tiết đợt gián đoạn `BC_HSSV_GAP_HISTORY` (`TBL-HSSV-005`) và warm-up Redis Cache cho báo cáo 63 tỉnh & phân bố | `09_DSBatch`, `10_DSBang`, `11_DinhNghiaBang` trong [Basic Design](ThietKeCoBan_BasicDesign_VN.md) |

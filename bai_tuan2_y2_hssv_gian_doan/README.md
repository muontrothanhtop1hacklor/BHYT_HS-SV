# Tuần 2 — Ý 2: Rà soát HSSV vẫn tham gia nhưng gián đoạn ≥ 3 tháng (CV 835/QLT)

Bài toán thực hiện theo **Công văn số 835/QLT** ngày 10/08/2026 của Ban Quản lý thu và phát triển người tham gia (BHXH Việt Nam).  
Mục tiêu là tìm kiếm và báo cáo các trường hợp:
> *"Học sinh, sinh viên tham gia từ tháng 10/2024, tháng 7/2026 vẫn đang tham gia nhưng có thời gian gián đoạn không tham gia từ 3 tháng trở lên.*  
> *(Tách riêng danh sách học sinh và sinh viên)"*

---

## 1. Bắt đầu nhanh

1. Đảm bảo dữ liệu nguồn tầng Silver đã được chuẩn hóa trong `data/silver/st_inthe_dtl/` (200 file parquet, ~200M dòng thẻ).
2. Chạy toàn bộ luồng kiểm thử, build Gold và kiểm tra bất biến bằng script 1-click trên Windows:
   ```powershell
   .\bai_tuan2_y2_hssv_gian_doan\chay_tat_ca.bat
   ```
3. Chạy đối chiếu DuckDB trên toàn bộ dữ liệu:
   ```powershell
   .\bai_tuan2_y2_hssv_gian_doan\p4_doi_soat\chay_doi_soat_y2.bat
   ```

---

## 2. Quy tắc nghiệp vụ (CV 835/QLT – Ý 2)

Đặc tả nghiệp vụ đầy đủ tại [docs/requirements/yeu_cau_tuan2_hssv_gian_doan.md](../docs/requirements/yeu_cau_tuan2_hssv_gian_doan.md).

### 2.1. Ba điều kiện thỏa mãn đồng thời
1. **Mốc bắt đầu (Tháng 10/2024):** Có thẻ BHYT hợp lệ (`TRANG_THAI = 1`) thuộc khối Học sinh (`HS`) hoặc Sinh viên (`SV`), có hiệu lực giao tháng 10/2024 (`TU_NGAY < 2024-11-01` và `DEN_NGAY >= 2024-10-01`).
2. **Mốc kết thúc (Tháng 07/2026):** Vẫn đang tham gia BHYT ở bất kỳ khối đối tượng nào trong hệ thống (`HS`, `SV`, `DN`, `GD`, `TE`,...), có hiệu lực giao tháng 07/2026 (`TU_NGAY < 2026-08-01` và `DEN_NGAY >= 2026-07-01`).
3. **Kỳ tính gián đoạn (01/10/2024–31/07/2026, tính cả hai đầu):** Tổng số ngày không có thẻ hợp lệ cộng dồn đạt ít nhất 90 ngày; bao gồm ngày trống trước thẻ đầu và sau thẻ cuối.

### 2.2. Xử lý chuỗi thời gian (Timeline & Gaps)
- **Thẻ liên tục:** Thẻ mới có hiệu lực ngay sau thẻ cũ hết hạn ($T_{\text{mới}} = D_{\text{cũ}} + 1$ ngày) $\implies$ Không có gián đoạn.
- **Thẻ chồng lấn/cấp đổi:** Khoảng thời hạn gối đầu nhau $\implies$ Tham gia liên tục.
- **Thẻ bị hủy (`TRANG_THAI = 0`):** Loại trừ khỏi chuỗi thời gian hợp lệ.
- **Tính cộng dồn:** Các khoảng trống đầu kỳ, giữa các đoạn và cuối kỳ được cộng dồn. Nếu tổng số ngày trống $\sum \text{gap}_i \ge 90$ ngày (`sum(gap_days) >= 90`) thì đưa vào kết quả.

---

## 3. Cấu trúc thư mục

```text
bai_tuan2_y2_hssv_gian_doan/
├── README.md                     # Hướng dẫn tổng quan bài toán Tuần 2
├── chay_tat_ca.bat               # Chạy tự động kiểm thử + build Gold + kiểm tra bất biến
├── p1_du_lieu/                   # DDL các bảng nguồn và 2 bảng kết quả đầu ra
│   ├── ddl_output_tables.sql     # DDL BC_HSSV_GIAN_DOAN_BHYT & TK_DBHC_HSSV_GIAN_DOAN_BHYT
│   ├── ddl_st_inthe_dtl.sql      # DDL bảng thẻ BHYT chi tiết
│   └── ddl_dm_bhxh.sql           # DDL danh mục cơ quan BHXH
├── p2_thuat_toan_timeline/       # Thiết kế và phân tích giải thuật chuỗi thời gian
│   ├── thuat_toan_timeline.md    # Phân tích toán học Interval Merging & Gap Detection
│   └── timeline_algorithm.py     # Cài đặt hàm gộp đoạn và tính khoảng trống chuẩn
├── p3_gold/                      # Pipeline sản xuất tầng Gold & Kiểm thử bất biến
│   ├── gold_logic_y2.py          # Logic SQL DuckDB xử lý dữ liệu lớn
│   ├── build_gold_y2.py          # Pipeline sản xuất chính thức (kèm Monitor RAM/CPU)
│   ├── test_timeline_gaps.py     # Kiểm thử chuỗi thời gian, biên kỳ, ngưỡng và tie-break
│   └── test_gold_y2_invariants.py# 6 kiểm thử kiểm tra tính toàn vẹn dữ liệu tầng Gold
└── p4_doi_soat/                  # Đối chiếu kết quả và kiểm chứng chéo
    ├── sql/query_y2_timeline_window.sql # Truy vấn DuckDB đối chiếu từng người
    ├── verify_sql_duckdb_y2.py   # So sánh từng người và chỉ tiêu với file Gold
    ├── compare_results_y2.py     # Đối soát kết quả với file của bạn cùng làm
    └── chay_doi_soat_y2.bat      # Kịch bản chạy nhanh đối soát trên Windows
```

---

## 4. Kết quả đầu ra

Các file kết quả được lưu tại `data/output/gold_y2/20241001_20260731_gap3m/`:
1. **`bc_hssv_gian_doan_bhyt.parquet`**: Bảng danh sách chi tiết cá nhân HSSV gián đoạn $\ge 3$ tháng.
2. **`tk_dbhc_hssv_gian_doan_bhyt.csv`**: Bảng tổng hợp số lượng theo 63 Tỉnh/Thành phố.
3. **`_metadata.json`**: Ghi nhận toàn bộ thông số đo lường hiệu năng, đỉnh RAM Process Tree, thời gian thực thi và mã băm SHA-256.

---

## 5. Kiểm thử và Kiểm chứng

Chạy toàn bộ bài kiểm thử của Tuần 2:
```powershell
pytest bai_tuan2_y2_hssv_gian_doan/ -v
```

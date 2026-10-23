# Phần 1 — Dữ liệu nguồn

Phần này mô tả cấu trúc dữ liệu BHYT đầu vào và các kiểm tra chất lượng cơ bản.

- DDL: `ddl_dm_bhxh.sql`, `ddl_st_inthe_dtl.sql`
- Kiểm tra schema: `test_data_quality.py`
- Dữ liệu đầu vào: `data/bhyt_data/` (hoặc nguồn thay thế trong `data/source/`)

Chạy kiểm tra từ thư mục gốc repo:

```powershell
pytest bai_tuan1_y1_hssv_dung_bhyt/p1_du_lieu/test_data_quality.py -v
```

Báo cáo tiến độ nằm trong [bao_cao/](../bao_cao/).

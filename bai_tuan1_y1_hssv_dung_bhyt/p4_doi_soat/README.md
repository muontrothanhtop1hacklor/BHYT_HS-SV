# Phần 4 — Đối soát

Phần này so sánh kết quả Gold với tệp kết quả nhận từ cộng tác viên và cung cấp truy vấn kiểm chứng độc lập bằng DuckDB.

- `compare_results.py`: so sánh các tệp kết quả và ghi báo cáo vào `data/output/reconciliation/`.
- `verify_sql_duckdb.py`: đối chiếu kết quả bằng SQL.
- `sql/`: các truy vấn tham chiếu.
- `ket_qua_cua_ban/`: nơi đặt tệp Parquet nhận được; xem README trong thư mục này để biết tên và schema mong đợi.

Chạy từ thư mục gốc repo:

```powershell
python -m bai_tuan1_y1_hssv_dung_bhyt.p4_doi_soat.compare_results
python -m bai_tuan1_y1_hssv_dung_bhyt.p4_doi_soat.verify_sql_duckdb
```

Xem [đặc tả trao đổi](dinh_dang_trao_doi.md), [bố trí dữ liệu](../../docs/data-layout.md) và [báo cáo](../bao_cao/README.md).

# Phần 3 — Gold

Phần này áp dụng quy tắc nghiệp vụ để tạo danh sách HSSV dừng tham gia BHYT và bảng tổng hợp theo tỉnh/thành phố.

- Đầu vào: `data/silver/st_inthe_dtl/` và danh mục `DM_BHXH`.
- Mã nghiệp vụ: `gold_logic.py`.
- Pipeline và xuất kết quả: `build_gold.py`.
- Kết quả: `data/output/gold/`.

Chạy từ thư mục gốc repo:

```powershell
python -m bai_tuan1_y1_hssv_dung_bhyt.p3_gold.build_gold --method global
```

Kiểm thử logic và bất biến:

```powershell
pytest bai_tuan1_y1_hssv_dung_bhyt/p3_gold/test_edge_cases.py bai_tuan1_y1_hssv_dung_bhyt/p3_gold/test_gold_invariants.py -v
```

Xem [bố trí dữ liệu](../../docs/data-layout.md) và [báo cáo](../bao_cao/README.md).

# Phần 2 — Bronze và Silver

Phần này nạp dữ liệu nguồn vào Bronze, sau đó chuẩn hóa và phân loại dữ liệu ở Silver.

- `build_bronze.py`: nạp Parquet nguồn và gắn metadata kỹ thuật.
- `build_silver.py`: chuẩn hóa mã khối, đánh dấu trường thiếu hoặc giới tính không hợp lệ, khử trùng ID toàn cục và xử lý ngày không hợp lệ.
- `--mode-loai1 quarantine` là chế độ mặc định; `--mode-loai1 smart-repair` cho phép sửa có cờ audit các khoảng ngày đảo trong ngưỡng 25–375 ngày.
- Đầu ra: `data/bronze/st_inthe_dtl/`, `data/silver/st_inthe_dtl/` và `data/silver/quarantine/`.

Chạy từ thư mục gốc repo:

```powershell
python -m bai_tuan1_y1_hssv_dung_bhyt.p2_bronze_silver.build_bronze
python -m bai_tuan1_y1_hssv_dung_bhyt.p2_bronze_silver.build_silver
```

Kiểm thử quy tắc dữ liệu:

```powershell
pytest bai_tuan1_y1_hssv_dung_bhyt/p2_bronze_silver/test_quy_tac_dong_ban.py -v
```

Xem [bố trí dữ liệu](../../docs/data-layout.md) và [báo cáo](../bao_cao/README.md).

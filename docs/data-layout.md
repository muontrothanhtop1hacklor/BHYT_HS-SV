# Bố trí dữ liệu

Toàn bộ dữ liệu chạy và kết quả được lưu dưới `data/`. Thư mục này bị Git bỏ qua vì chứa Parquet và dữ liệu quy mô lớn; mã nguồn, cấu hình và tài liệu hướng dẫn vẫn được lưu trong repo.

| Thư mục | Vai trò | Nội dung thường gặp |
|---|---|---|
| `data/bhyt_data/` | Dữ liệu BHYT giả lập gốc | `DM_BHXH.csv`, `dm_bhxh.parquet`, `st_inthe_dtl/`, `persons_gt/`, `dirty_log/`, `SCENARIO/`, `_manifest/` |
| `data/bhyt_answer/` | Đáp án tham chiếu xuất bởi validator | `answer_list.parquet`, `answer_by_tinh.csv` |
| `data/bronze/` | Bản nạp thô có metadata kỹ thuật | `st_inthe_dtl/` |
| `data/silver/` | Dữ liệu đã chuẩn hóa và khu cách ly | `st_inthe_dtl/`, `quarantine/`, các manifest và báo cáo audit |
| `data/output/` | Kết quả cuối và đối soát | `gold/`, `reconciliation/`; `dev_a/` và `dev_b/` là kết quả lưu từ cấu trúc cũ |
| `data/source/` | Vị trí dành cho nguồn đầu vào bên ngoài generator | `dm_bhxh/`, `st_inthe_dtl/` |

## Luồng dữ liệu

```text
data/bhyt_data ──> data/bronze ──> data/silver ──> data/output/gold
       │                 │              │                  │
       └──> bhyt_answer  └──────────────┴──> reconciliation
```

`data/source/` là phương án đầu vào thay thế khi dữ liệu không nằm trong `data/bhyt_data/`. Đường dẫn mặc định và mốc nghiệp vụ được khai báo tại [common/config.py](../common/config.py); các script P2–P4 cũng nhận tùy chọn đường dẫn dòng lệnh khi cần.

Các thư mục `data/output/dev_a/` và `data/output/dev_b/` hiện vẫn còn dữ liệu đối chiếu cũ. Pipeline hiện hành ghi kết quả vào `gold/` và `reconciliation/`; hai thư mục cũ được giữ nguyên để không làm mất kết quả đã lưu.

Không chuyển hoặc đổi tên thư mục dữ liệu nếu chưa cập nhật cấu hình và các lệnh SQL/script tham chiếu đường dẫn đó.

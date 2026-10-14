# common/data_gen: Sinh và kiểm tra dữ liệu BHYT giả lập (CV 835/QLT)
- **Mục đích**: Cung cấp công cụ sinh dữ liệu BHYT chuẩn quy mô lớn theo vòng đời người (Script 1 SplitMix64 & Script 2 Numba).
- **Đầu vào**: Các tham số dòng lệnh (`--persons`, `--chunk`, `--seed`, `--workers`).
- **Đầu ra**: `data/bhyt_data` (`DM_BHXH.csv/.parquet`, `ST_INTHE_DTL/*.parquet`, `SCENARIO/*.parquet`).
- **Cách chạy**: Chạy trực tiếp `common\data_gen\chay_sinh_du_lieu.bat` hoặc lệnh `python common/data_gen/gen_bhyt_script1.py --persons 200000 --chunk 100000 --out data/bhyt_data`.
- **Test kiểm tra**: Chạy `python common/data_gen/validate_bhyt.py --data data/bhyt_data --export data/bhyt_answer` để xác thực toàn vẹn dữ liệu.

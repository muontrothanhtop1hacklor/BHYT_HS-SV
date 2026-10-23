# Hướng dẫn sinh và kiểm tra dữ liệu BHYT 200M (CV 835/QLT)

## Mã nguồn và đầu ra

- Bộ sinh chuẩn: [`common/data_gen/gen_bhyt.py`](../../common/data_gen/gen_bhyt.py)
- Validator và xuất đáp án: [`common/data_gen/validate_bhyt.py`](../../common/data_gen/validate_bhyt.py)
- Batch Windows: [`common/data_gen/chay_sinh_du_lieu.bat`](../../common/data_gen/chay_sinh_du_lieu.bat)
- Dữ liệu sinh: `data/bhyt_data/`
- Đáp án tham chiếu: `data/bhyt_answer/`

## Lệnh chuẩn

Sinh thử 200.000 người:

```powershell
python common/data_gen/gen_bhyt.py generate --out data/bhyt_data --persons 200000 --chunk-persons 50000 --workers 4
```

Sinh đủ 20 triệu người (khoảng 200 triệu dòng thẻ):

```powershell
python common/data_gen/gen_bhyt.py generate --out data/bhyt_data --persons 20000000 --chunk-persons 100000 --workers 4
```

Kiểm tra toàn vẹn và xuất đáp án:

```powershell
python common/data_gen/validate_bhyt.py --data data/bhyt_data --export data/bhyt_answer
```

Trên Windows/PowerShell, giữ đầu ra UTF-8 để hiển thị đúng tiếng Việt. Cấu trúc các thư mục dữ liệu được mô tả trong [`docs/data-layout.md`](../../docs/data-layout.md).

# -*- coding: utf-8 -*-
"""
compare_results_y2.py
Đối soát và so sánh kết quả Ý 2 (CV 835/QLT) giữa 2 bạn làm độc lập.
"""
import argparse
import sys
import time
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = str(Path(__file__).resolve().parents[2])
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import pandas as pd
import pyarrow.parquet as pq

from common.config import (
    GOLD_Y2_BC_FILE,
    GOLD_Y2_TK_CSV,
    KET_QUA_CUA_BAN_Y2_DIR,
    OUTPUT_DIR,
)


def main():
    parser = argparse.ArgumentParser(
        description="Đối soát kết quả bài toán Ý 2 (CV 835/QLT)"
    )
    parser.add_argument(
        "--my-file",
        default=str(GOLD_Y2_BC_FILE),
        help="File kết quả của bạn (mặc định: tầng Gold)",
    )
    parser.add_argument(
        "--friend-file",
        default=str(KET_QUA_CUA_BAN_Y2_DIR / "bc_hssv_gian_doan_bhyt.parquet"),
        help="File kết quả nhận từ bạn cùng làm",
    )
    parser.add_argument(
        "--report-out",
        default=str(OUTPUT_DIR / "reconciliation" / "reconciliation_report_y2.md"),
        help="Đường dẫn xuất báo cáo đối soát Markdown",
    )
    args = parser.parse_args()

    my_path = Path(args.my_file).resolve()
    friend_path = Path(args.friend_file).resolve()
    report_path = Path(args.report_out).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("CHƯƠNG TRÌNH ĐỐI SOÁT KẾT QUẢ BÀI TOÁN Ý 2 (CV 835/QLT)")
    print(f"File của bạn:   {my_path}")
    print(f"File của bạn B: {friend_path}")
    print("=" * 80)

    if not my_path.exists():
        sys.exit(f"LỖI: Chưa có file kết quả của bạn tại: {my_path}")

    my_df = pq.read_table(str(my_path)).to_pandas()
    print(f"\n[1] Đã nạp file kết quả của bạn: {len(my_df):,} bản ghi")

    if not friend_path.exists():
        print(f"\n[THÔNG BÁO] Chưa tìm thấy file của bạn B tại: {friend_path}")
        print("  -> Vui lòng chép file 'bc_hssv_gian_doan_bhyt.parquet' nhận từ bạn vào thư mục:")
        print(f"     {friend_path.parent}")
        print("\nTổng quan kết quả hiện tại của bạn:")
        print(f"  - Tổng số người gián đoạn >= 3 tháng: {len(my_df):,} người")
        print(f"  - Học sinh (HS):                     {(my_df['MA_KHOI_GOC'] == 'HS').sum():,} người")
        print(f"  - Sinh viên (SV):                    {(my_df['MA_KHOI_GOC'] == 'SV').sum():,} người")
        print(f"  - Số ngày gián đoạn trung bình:      {my_df['SO_NGAY_GIAN_DOAN'].mean():.1f} ngày")
        return

    friend_df = pq.read_table(str(friend_path)).to_pandas()
    print(f"[2] Đã nạp file của bạn B: {len(friend_df):,} bản ghi")

    # So sánh tập SO_SO_BHXH
    my_set = set(my_df["SO_SO_BHXH"].astype(str))
    friend_set = set(friend_df["SO_SO_BHXH"].astype(str))

    intersection = my_set & friend_set
    only_my = my_set - friend_set
    only_friend = friend_set - my_set
    union = my_set | friend_set

    jaccard = len(intersection) / len(union) * 100 if union else 100.0

    print("\n" + "-" * 80)
    print("KẾT QUẢ ĐỐI SOÁT ĐỊNH DANH (SO_SO_BHXH):")
    print(f"  - Số lượng của bạn:                  {len(my_set):,} người")
    print(f"  - Số lượng của bạn B:                {len(friend_set):,} người")
    print(f"  - Số người trùng khớp cả hai:        {len(intersection):,} người")
    print(f"  - Chỉ có ở kết quả của bạn:          {len(only_my):,} người")
    print(f"  - Chỉ có ở kết quả bạn B:            {len(only_friend):,} người")
    print(f"  - Tỷ lệ tương đồng (Jaccard Index):  {jaccard:.4f}%")
    print("-" * 80)

    # Lập báo cáo đối soát Markdown
    md_content = f"""# Báo cáo Đối soát Kết quả Ý 2 (CV 835/QLT)

**Thời điểm đối soát:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Quy tắc nghiệp vụ:** HSSV tham gia 10/2024, vẫn tham gia 07/2026, gián đoạn tích lũy >= 3 tháng (>= 90 ngày).

## 1. So sánh tổng lượng bản ghi

| Chỉ tiêu | Kết quả của bạn | Kết quả bạn B | Chênh lệch | Đánh giá |
|---|---|---|---|---|
| **Tổng số người** | **{len(my_set):,}** | **{len(friend_set):,}** | **{abs(len(my_set) - len(friend_set)):,}** | {'Khớp 100%' if len(my_set) == len(friend_set) else 'Có sai khác'} |
| Học sinh (HS) | {(my_df['MA_KHOI_GOC'] == 'HS').sum():,} | {(friend_df['MA_KHOI_GOC'] == 'HS').sum():,} | {abs((my_df['MA_KHOI_GOC'] == 'HS').sum() - (friend_df['MA_KHOI_GOC'] == 'HS').sum()):,} | - |
| Sinh viên (SV) | {(my_df['MA_KHOI_GOC'] == 'SV').sum():,} | {(friend_df['MA_KHOI_GOC'] == 'SV').sum():,} | {abs((my_df['MA_KHOI_GOC'] == 'SV').sum() - (friend_df['MA_KHOI_GOC'] == 'SV').sum()):,} | - |

## 2. Phân tích tập hợp định danh (SO_SO_BHXH)

- **Trùng khớp cả 2 bên:** {len(intersection):,} người ({jaccard:.2f}% tương đồng)
- **Chỉ có ở bài của bạn:** {len(only_my):,} người
- **Chỉ có ở bài bạn B:** {len(only_friend):,} người

## 3. Kết luận nghiệm thu
{'Hai kết quả trùng khớp hoàn toàn 100%!' if len(only_my) == 0 and len(only_friend) == 0 else 'Cần kiểm tra lại các trường hợp chênh lệch (kiểm tra điều kiện mốc kết thúc 07/2026 hoặc ngưỡng 90 ngày).'}
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\nĐã xuất báo cáo đối soát tại: {report_path}")


if __name__ == "__main__":
    main()

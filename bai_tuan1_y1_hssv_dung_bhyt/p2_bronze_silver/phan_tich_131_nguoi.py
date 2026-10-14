# Bài: tuan1_y1 | Phần: p2_bronze_silver
# -*- coding: utf-8 -*-
"""
scripts/analyze_131_gap.py
Phân tích chi tiết nhóm +131 người chênh lệch (848.413 -> 850.190):
1. Trích xuất danh sách 131 người chênh lệch giữa Raw-normalized và Silver-quarantine.
2. Join với data/bhyt_data/persons_gt để phân tích:
   - KICH_BAN (CONT, STOP, SWITCH, GAP, LATE, UPGRADE)
   - Cờ HUY_THAY_THE, HUY_KHONG_THAY, CHUYEN_DIA_BAN
3. Trích xuất thẻ của 131 người trong data/silver/quarantine để kiểm tra nguyên nhân.
4. Đánh giá 3 phương án:
   - Phương án 1: Raw (Dữ liệu thô)
   - Phương án 2: Silver-Quarantine (Cách ly dòng lỗi Loại 1)
   - Phương án 3: Silver-Swap (Sửa lỗi Loại 1 bằng hoán đổi ngày TU_NGAY <-> DEN_NGAY)
   So sánh với sự thật persons_gt (KHOI_GOC in ('HS', 'SV') & KICH_BAN == 'STOP').
"""

import os
import sys
import time
import json
import duckdb
import pandas as pd
import pyarrow.parquet as pq

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def analyze():
    con = duckdb.connect()
    con.execute("PRAGMA threads=4;")

    print("=" * 80)
    print(" BƯỚC B1(a): PHÂN TÍCH NHÓM +131 NGƯỜI CHÊNH LỆCH & ĐỐI CHIẾU GROUND TRUTH")
    print("=" * 80)

    # 1. Trích xuất danh sách 131 người chênh lệch do cách ly Loại 1
    # Nhóm dừng theo Raw (đã chuẩn hóa Loại 4 để cô lập chỉ riêng tác động của Loại 1)
    print("\n1. Trích xuất 131 người thuộc tập (Silver_Quarantine - Raw_Norm4)...")
    query_131 = """
    WITH raw_norm4_stopped AS (
        SELECT DISTINCT CAST(SO_SO_BHXH AS BIGINT) AS SO_SO_BHXH
        FROM read_parquet('data/bhyt_data/st_inthe_dtl/*.parquet')
        WHERE TRANG_THAI = 1
          AND UPPER(TRIM(MA_KHOI)) IN ('HS', 'SV')
          AND TU_NGAY < DATE '2024-11-01'
          AND DEN_NGAY >= DATE '2024-10-01'
        EXCEPT
        SELECT DISTINCT CAST(SO_SO_BHXH AS BIGINT) AS SO_SO_BHXH
        FROM read_parquet('data/bhyt_data/st_inthe_dtl/*.parquet')
        WHERE TRANG_THAI = 1
          AND TU_NGAY < DATE '2026-09-01'
          AND DEN_NGAY >= DATE '2026-08-01'
    ),
    silver_stopped AS (
        SELECT DISTINCT CAST(SO_SO_BHXH AS BIGINT) AS SO_SO_BHXH
        FROM read_parquet('data/silver/st_inthe_dtl/*.parquet')
        WHERE TRANG_THAI = 1
          AND MA_KHOI IN ('HS', 'SV')
          AND TU_NGAY < DATE '2024-11-01'
          AND DEN_NGAY >= DATE '2024-10-01'
        EXCEPT
        SELECT DISTINCT CAST(SO_SO_BHXH AS BIGINT) AS SO_SO_BHXH
        FROM read_parquet('data/silver/st_inthe_dtl/*.parquet')
        WHERE TRANG_THAI = 1
          AND TU_NGAY < DATE '2026-09-01'
          AND DEN_NGAY >= DATE '2026-08-01'
    )
    SELECT s.SO_SO_BHXH
    FROM silver_stopped s
    WHERE s.SO_SO_BHXH NOT IN (SELECT r.SO_SO_BHXH FROM raw_norm4_stopped r);
    """
    df_131 = con.execute(query_131).df()
    print(f" -> Số người chênh lệch tìm được: {len(df_131)} người")

    # 2. Join với persons_gt
    print("\n2. Join 131 người với persons_gt...")
    con.register("df_131", df_131)
    query_gt = """
    SELECT
        p.SO_SO_BHXH,
        p.KHOI_GOC,
        p.KICH_BAN,
        p.HUY_THAY_THE,
        p.HUY_KHONG_THAY,
        p.CHUYEN_DIA_BAN
    FROM df_131 d
    JOIN read_parquet('data/bhyt_data/persons_gt/*.parquet') p
      ON d.SO_SO_BHXH = p.SO_SO_BHXH;
    """
    df_gt_131 = con.execute(query_gt).df()
    print(" Thống kê KỊCH BẢN trong persons_gt của nhóm 131 người:")
    print(df_gt_131["KICH_BAN"].value_counts())
    print("\n Thống kê cờ thẻ hủy / chuyển địa bàn của nhóm 131 người:")
    print(f" - HUY_THAY_THE : {df_gt_131['HUY_THAY_THE'].sum()}/{len(df_gt_131)}")
    print(f" - HUY_KHONG_THAY: {df_gt_131['HUY_KHONG_THAY'].sum()}/{len(df_gt_131)}")
    print(f" - CHUYEN_DIA_BAN: {df_gt_131['CHUYEN_DIA_BAN'].sum()}/{len(df_gt_131)}")

    # 3. Xem các thẻ trong Quarantine của nhóm 131 người này
    print("\n3. Kiểm tra thẻ trong Quarantine của 131 người này...")
    query_q_cards = """
    SELECT
        CAST(q.SO_SO_BHXH AS BIGINT) AS SO_SO_BHXH,
        q.MA_KHOI,
        q.TU_NGAY,
        q.DEN_NGAY,
        q.TRANG_THAI,
        q._QUARANTINE_REASON
    FROM read_parquet('data/silver/quarantine/*.parquet') q
    WHERE CAST(q.SO_SO_BHXH AS BIGINT) IN (SELECT SO_SO_BHXH FROM df_131)
    ORDER BY q.SO_SO_BHXH;
    """
    df_q = con.execute(query_q_cards).df()
    print(f" -> Tìm thấy {len(df_q)} thẻ bị cách ly của 131 người này.")
    print(" -> Mẫu 5 thẻ bị cách ly:")
    print(df_q.head(5))

    # Kiểm tra xem thẻ bị cách ly có TU_NGAY và DEN_NGAY ban đầu (trước khi bị đảo) rơi vào đâu
    # Trong gen_bhyt.py: lỗi loại 1 được tạo bằng: tu, den = den, tu (hoán đổi vị trí ngày)
    # Nghĩa là ngày thật ban đầu là: tu_that = DEN_NGAY (nhỏ hơn), den_that = TU_NGAY (lớn hơn)!
    query_swapped_valid = """
    SELECT
        COUNT(*) AS cnt_valid_at_chk
    FROM df_q
    WHERE TRANG_THAI = 1
      AND DEN_NGAY < DATE '2026-09-01'  -- ngày TU_NGAY thật
      AND TU_NGAY >= DATE '2026-08-01'; -- ngày DEN_NGAY thật
    """
    swapped_match = con.execute(query_swapped_valid).fetchone()[0]
    print(f" -> Số thẻ nếu đảo lại ngày sẽ CÓ HIỆU LỰC TẠI THÁNG 08/2026: {swapped_match}/{len(df_q)} thẻ!")

    # 4. ĐÁNH GIÁ ĐỊNH LƯỢNG 3 PHƯƠNG ÁN SO VỚI SỰ THẬT (GROUND TRUTH)
    print("\n" + "=" * 80)
    print(" 4. SO SÁNH 3 PHƯƠNG ÁN VỚI SỰ THẬT (GROUND TRUTH: persons_gt)")
    print("=" * 80)

    # Dựng tập Sự thật: HSSV có KICH_BAN == 'STOP'
    # Lưu ý: Nhóm HUY_KHONG_THAY có thẻ bị hủy ở tháng gốc nên không tham gia tháng gốc
    query_truth = """
    CREATE OR REPLACE TEMPORARY TABLE ground_truth AS
    SELECT DISTINCT SO_SO_BHXH
    FROM read_parquet('data/bhyt_data/persons_gt/*.parquet')
    WHERE KHOI_GOC IN ('HS', 'SV')
      AND KICH_BAN = 'STOP';
    """
    con.execute(query_truth)
    total_truth = con.execute("SELECT COUNT(*) FROM ground_truth").fetchone()[0]
    print(f" Tổng số người HSSV có KICH_BAN = 'STOP' trong persons_gt: {total_truth:,} người")

    # Phương án 1: Raw (Dữ liệu thô nguyên bản của đề)
    query_pa1 = """
    CREATE OR REPLACE TEMPORARY TABLE pa1_raw AS
    SELECT DISTINCT CAST(SO_SO_BHXH AS BIGINT) AS SO_SO_BHXH
    FROM read_parquet('data/bhyt_data/st_inthe_dtl/*.parquet')
    WHERE TRANG_THAI = 1
      AND MA_KHOI IN ('HS', 'SV')
      AND TU_NGAY < DATE '2024-11-01'
      AND DEN_NGAY >= DATE '2024-10-01'
    EXCEPT
    SELECT DISTINCT CAST(SO_SO_BHXH AS BIGINT) AS SO_SO_BHXH
    FROM read_parquet('data/bhyt_data/st_inthe_dtl/*.parquet')
    WHERE TRANG_THAI = 1
      AND TU_NGAY < DATE '2026-09-01'
      AND DEN_NGAY >= DATE '2026-08-01';
    """
    con.execute(query_pa1)

    # Phương án 2: Silver-Quarantine (Đang áp dụng: Cách ly Loại 1 không đoán sửa)
    query_pa2 = """
    CREATE OR REPLACE TEMPORARY TABLE pa2_quarantine AS
    SELECT DISTINCT CAST(SO_SO_BHXH AS BIGINT) AS SO_SO_BHXH
    FROM read_parquet('data/silver/st_inthe_dtl/*.parquet')
    WHERE TRANG_THAI = 1
      AND MA_KHOI IN ('HS', 'SV')
      AND TU_NGAY < DATE '2024-11-01'
      AND DEN_NGAY >= DATE '2024-10-01'
    EXCEPT
    SELECT DISTINCT CAST(SO_SO_BHXH AS BIGINT) AS SO_SO_BHXH
    FROM read_parquet('data/silver/st_inthe_dtl/*.parquet')
    WHERE TRANG_THAI = 1
      AND TU_NGAY < DATE '2026-09-01'
      AND DEN_NGAY >= DATE '2026-08-01';
    """
    con.execute(query_pa2)

    # Phương án 3: Silver-Swap (Sửa Loại 1 bằng cách hoán đổi ngày nếu TU_NGAY > DEN_NGAY)
    # Lấy từ Silver và gộp thêm các thẻ từ Quarantine đã được hoán đổi ngày
    query_pa3 = """
    CREATE OR REPLACE TEMPORARY TABLE pa3_swap_cards AS
    SELECT
        CAST(SO_SO_BHXH AS BIGINT) AS SO_SO_BHXH,
        MA_KHOI,
        TRANG_THAI,
        TU_NGAY,
        DEN_NGAY
    FROM read_parquet('data/silver/st_inthe_dtl/*.parquet')
    UNION ALL
    SELECT
        CAST(SO_SO_BHXH AS BIGINT) AS SO_SO_BHXH,
        UPPER(TRIM(MA_KHOI)) AS MA_KHOI,
        TRANG_THAI,
        DEN_NGAY AS TU_NGAY, -- Hoán đổi
        TU_NGAY AS DEN_NGAY  -- Hoán đổi
    FROM read_parquet('data/silver/quarantine/*.parquet');

    CREATE OR REPLACE TEMPORARY TABLE pa3_swap AS
    SELECT DISTINCT SO_SO_BHXH
    FROM pa3_swap_cards
    WHERE TRANG_THAI = 1
      AND MA_KHOI IN ('HS', 'SV')
      AND TU_NGAY < DATE '2024-11-01'
      AND DEN_NGAY >= DATE '2024-10-01'
    EXCEPT
    SELECT DISTINCT SO_SO_BHXH
    FROM pa3_swap_cards
    WHERE TRANG_THAI = 1
      AND TU_NGAY < DATE '2026-09-01'
      AND DEN_NGAY >= DATE '2026-08-01';
    """
    con.execute(query_pa3)

    # Đo ma trận cho cả 3 phương án
    def evaluate_pa(table_name):
        tot = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        tp = con.execute(f"SELECT COUNT(*) FROM {table_name} WHERE SO_SO_BHXH IN (SELECT SO_SO_BHXH FROM ground_truth)").fetchone()[0]
        fp = tot - tp
        fn = con.execute(f"SELECT COUNT(*) FROM ground_truth WHERE SO_SO_BHXH NOT IN (SELECT SO_SO_BHXH FROM {table_name})").fetchone()[0]
        return tot, tp, fp, fn

    tot1, tp1, fp1, fn1 = evaluate_pa("pa1_raw")
    tot2, tp2, fp2, fn2 = evaluate_pa("pa2_quarantine")
    tot3, tp3, fp3, fn3 = evaluate_pa("pa3_swap")

    # In bảng so sánh
    print(f"\n{'Chỉ số đánh giá':<35} | {'PA 1: Raw':<18} | {'PA 2: Quarantine':<18} | {'PA 3: Swap (Sửa)':<18}")
    print("-" * 95)
    print(f"{'Tổng số người dừng dự đoán':<35} | {tot1:<18,d} | {tot2:<18,d} | {tot3:<18,d}")
    print(f"{'Đúng so với STOP (True Positive)':<35} | {tp1:<18,d} | {tp2:<18,d} | {tp3:<18,d}")
    print(f"{'Dương tính giả (False Positive)':<35} | {fp1:<18,d} | {fp2:<18,d} | {fp3:<18,d}")
    print(f"{'Âm tính giả (False Negative)':<35} | {fn1:<18,d} | {fn2:<18,d} | {fn3:<18,d}")
    print(f"{'Độ chính xác Precision (%)':<35} | {tp1/tot1*100:<18.4f} | {tp2/tot2*100:<18.4f} | {tp3/tot3*100:<18.4f}")
    print(f"{'Độ bao phủ Recall (%)':<35} | {tp1/total_truth*100:<18.4f} | {tp2/total_truth*100:<18.4f} | {tp3/total_truth*100:<18.4f}")
    print("=" * 95)

    # Lưu kết quả phân tích
    res_dict = {
        "n_diff_131": len(df_131),
        "gt_scenarios_131": df_gt_131["KICH_BAN"].value_counts().to_dict(),
        "pa1_raw": {"total": tot1, "tp": tp1, "fp": fp1, "fn": fn1},
        "pa2_quarantine": {"total": tot2, "tp": tp2, "fp": fp2, "fn": fn2},
        "pa3_swap": {"total": tot3, "tp": tp3, "fp": fp3, "fn": fn3},
    }
    with open("data/silver/_analysis_131.json", "w", encoding="utf-8") as f:
        json.dump(res_dict, f, indent=2, ensure_ascii=False)
    print("\n -> Đã lưu kết quả chi tiết vào data/silver/_analysis_131.json")


if __name__ == "__main__":
    analyze()

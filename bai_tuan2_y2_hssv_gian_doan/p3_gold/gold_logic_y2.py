# -*- coding: utf-8 -*-
"""
gold_logic_y2.py
Logic nghiệp vụ cốt lõi và xây dựng truy vấn SQL cho tầng Gold Ý 2 (CV 835/QLT).

Các hàm hỗ trợ:
- build_gold_y2_sql: Sinh câu lệnh SQL DuckDB hoàn chỉnh cho bài toán Ý 2.
- map_provinces_y2: Ánh xạ mã tỉnh chuẩn từ DM_BHXH.
"""
from pathlib import Path
from typing import Optional


def build_gold_y2_sql(
    silver_pattern: str,
    dm_path: str,
    base_start: str = "2024-10-01",
    base_next: str = "2024-11-01",
    chk_start: str = "2026-07-01",
    chk_next: str = "2026-08-01",
    window_start: str = "2024-10-01",
    window_end: str = "2026-07-31",
    min_gap_days: int = 90,
    report_date: str = "2026-08-10"
) -> str:
    """
    Sinh câu lệnh SQL DuckDB xử lý toàn bộ bài toán Ý 2:
    1. Lọc thẻ hợp lệ (TRANG_THAI = 1).
    2. Xác định người tham gia HSSV mốc 10/2024 và thẻ đại diện mốc gốc.
    3. Xác định người còn tham gia BHYT mốc 07/2026 và thẻ đại diện mốc hiện tại.
    4. Cắt các thẻ vào cửa sổ [window_start, window_end].
    5. Gộp các khoảng thời gian liên tục / chồng lấn bằng Window Functions.
    6. Tính các khoảng trống gián đoạn giữa các đoạn liên tục.
    7. Lọc điều kiện tổng số ngày gián đoạn >= min_gap_days.
    8. Nối danh mục DM_BHXH để quy đổi tỉnh và tổng hợp số liệu 63 tỉnh/thành phố.
    """
    dm_read_sql = (
        f"read_csv_auto('{dm_path}')"
        if str(dm_path).endswith(".csv")
        else f"read_parquet('{dm_path}')"
    )

    sql = f"""
    -- =========================================================================
    -- BÀI TOÁN Ý 2 (CV 835/QLT) - HSSV GIÁN ĐOẠN BHYT >= 3 THÁNG
    -- =========================================================================
    
    -- 1. Bảng thẻ hợp lệ trong toàn hệ thống
    CREATE TEMPORARY TABLE valid_cards AS
    SELECT
        SO_SO_BHXH,
        HO_TEN,
        NGAY_SINH,
        GIOI_TINH,
        SO_CMND,
        DIA_CHI,
        SO_THE_KCB,
        MA_KHOI,
        TU_NGAY,
        DEN_NGAY,
        DM_BHXH_ID,
        MA_TINH,
        GREATEST(TU_NGAY, DATE '{window_start}') AS tu_clip,
        LEAST(DEN_NGAY, DATE '{window_end}') AS den_clip
    FROM read_parquet('{silver_pattern}')
    WHERE TRANG_THAI = 1;

    -- 2. Thẻ mốc gốc (Tháng 10/2024) thuộc khối Học sinh (HS) hoặc Sinh viên (SV)
    CREATE TEMPORARY TABLE base_cards AS
    SELECT
        *,
        CASE WHEN MA_KHOI = 'SV' THEN 2 ELSE 1 END AS PRIORITY_SCORE,
        ROW_NUMBER() OVER (
            PARTITION BY SO_SO_BHXH
            ORDER BY 
                CASE WHEN MA_KHOI = 'SV' THEN 2 ELSE 1 END DESC,
                DEN_NGAY DESC,
                SO_THE_KCB ASC
        ) AS rn_base
    FROM valid_cards
    WHERE TU_NGAY < DATE '{base_next}' AND DEN_NGAY >= DATE '{base_start}'
      AND MA_KHOI IN ('HS', 'SV');

    -- Thẻ đại diện mốc gốc của từng cá nhân
    CREATE TEMPORARY TABLE primary_base AS
    SELECT * FROM base_cards WHERE rn_base = 1;

    -- 3. Thẻ mốc kết thúc (Tháng 07/2026) thuộc bất kỳ khối đối tượng nào
    CREATE TEMPORARY TABLE check_cards AS
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY SO_SO_BHXH
            ORDER BY DEN_NGAY DESC, SO_THE_KCB ASC
        ) AS rn_chk
    FROM valid_cards
    WHERE TU_NGAY < DATE '{chk_next}' AND DEN_NGAY >= DATE '{chk_start}';

    -- Thẻ đại diện mốc kết thúc của từng cá nhân
    CREATE TEMPORARY TABLE primary_chk AS
    SELECT * FROM check_cards WHERE rn_chk = 1;

    -- 4. Tập ứng viên thỏa mãn cả 2 mốc bắt đầu và kết thúc
    CREATE TEMPORARY TABLE candidates AS
    SELECT
        b.SO_SO_BHXH,
        b.HO_TEN,
        b.NGAY_SINH,
        b.GIOI_TINH,
        b.SO_CMND,
        b.DIA_CHI,
        b.SO_THE_KCB AS SO_THE_KCB_GOC,
        b.MA_KHOI AS MA_KHOI_GOC,
        b.TU_NGAY AS TU_NGAY_GOC,
        b.DEN_NGAY AS DEN_NGAY_GOC,
        b.DM_BHXH_ID AS DM_BHXH_ID_GOC,
        b.MA_TINH AS MA_TINH_GOC,
        c.SO_THE_KCB AS SO_THE_KCB_HIEN_TAI,
        c.MA_KHOI AS MA_KHOI_HIEN_TAI,
        c.TU_NGAY AS TU_NGAY_HIEN_TAI,
        c.DEN_NGAY AS DEN_NGAY_HIEN_TAI,
        c.DM_BHXH_ID AS DM_BHXH_ID_HIEN_TAI,
        c.MA_TINH AS MA_TINH_HIEN_TAI
    FROM primary_base b
    JOIN primary_chk c ON b.SO_SO_BHXH = c.SO_SO_BHXH;

    -- 5. Toàn bộ các thẻ của ứng viên nằm trong cửa sổ [{window_start}, {window_end}]
    CREATE TEMPORARY TABLE cand_window_cards AS
    SELECT
        v.SO_SO_BHXH,
        v.tu_clip AS tu,
        v.den_clip AS den
    FROM valid_cards v
    JOIN (SELECT DISTINCT SO_SO_BHXH FROM candidates) cd ON v.SO_SO_BHXH = cd.SO_SO_BHXH
    WHERE v.tu_clip <= v.den_clip;

    -- 6. Thuật toán Window Function gộp khoảng thời gian chồng lấn/liên tục
    CREATE TEMPORARY TABLE with_prev AS
    SELECT
        SO_SO_BHXH,
        tu,
        den,
        MAX(den) OVER (
            PARTITION BY SO_SO_BHXH
            ORDER BY tu, den
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS prev_max_den
    FROM cand_window_cards;

    CREATE TEMPORARY TABLE with_new_grp AS
    SELECT
        SO_SO_BHXH,
        tu,
        den,
        CASE
            WHEN prev_max_den IS NULL OR tu > prev_max_den + INTERVAL 1 DAY THEN 1
            ELSE 0
        END AS is_new_grp
    FROM with_prev;

    CREATE TEMPORARY TABLE with_grp_id AS
    SELECT
        SO_SO_BHXH,
        tu,
        den,
        SUM(is_new_grp) OVER (
            PARTITION BY SO_SO_BHXH
            ORDER BY tu, den
            ROWS UNBOUNDED PRECEDING
        ) AS grp_id
    FROM with_new_grp;

    CREATE TEMPORARY TABLE merged_intervals AS
    SELECT
        SO_SO_BHXH,
        grp_id,
        MIN(tu) AS m_tu,
        MAX(den) AS m_den
    FROM with_grp_id
    GROUP BY SO_SO_BHXH, grp_id;

    -- 7. Tính khoảng trống giữa các đoạn và ở hai biên của cửa sổ
    CREATE TEMPORARY TABLE with_gaps AS
    SELECT
        SO_SO_BHXH,
        m_tu,
        m_den,
        LAG(m_den) OVER (PARTITION BY SO_SO_BHXH ORDER BY m_tu) AS prev_m_den,
        (m_tu - LAG(m_den) OVER (PARTITION BY SO_SO_BHXH ORDER BY m_tu) - 1) AS gap_days
    FROM merged_intervals;

    CREATE TEMPORARY TABLE gap_events AS
    SELECT SO_SO_BHXH, gap_days
    FROM with_gaps
    WHERE gap_days > 0
    UNION ALL
    SELECT SO_SO_BHXH, m_tu - DATE '{window_start}' AS gap_days
    FROM merged_intervals mi
    WHERE m_tu = (SELECT MIN(m_tu) FROM merged_intervals x WHERE x.SO_SO_BHXH = mi.SO_SO_BHXH)
      AND m_tu > DATE '{window_start}'
    UNION ALL
    SELECT SO_SO_BHXH, DATE '{window_end}' - m_den AS gap_days
    FROM merged_intervals mi
    WHERE m_tu = (SELECT MAX(m_tu) FROM merged_intervals x WHERE x.SO_SO_BHXH = mi.SO_SO_BHXH)
      AND m_den < DATE '{window_end}';

    CREATE TEMPORARY TABLE person_gaps AS
    SELECT
        SO_SO_BHXH,
        COUNT(gap_days) AS SO_DOT_GIAN_DOAN,
        COALESCE(SUM(gap_days), 0) AS SO_NGAY_GIAN_DOAN,
        ROUND(COALESCE(SUM(gap_days), 0) / 30.0, 1) AS SO_THANG_GIAN_DOAN
    FROM gap_events
    GROUP BY SO_SO_BHXH;

    -- 8. Bảng chi tiết kết quả Gold Ý 2: BC_HSSV_GIAN_DOAN_BHYT
    CREATE TEMPORARY TABLE bc_raw AS
    SELECT
        CAST(c.SO_SO_BHXH AS VARCHAR(10)) AS SO_SO_BHXH,
        CAST(c.HO_TEN AS VARCHAR(100)) AS HO_TEN,
        CAST(c.NGAY_SINH AS DATE) AS NGAY_SINH,
        CAST(c.GIOI_TINH AS SMALLINT) AS GIOI_TINH,
        CAST(c.SO_CMND AS VARCHAR(12)) AS SO_CMND,
        CAST(c.DIA_CHI AS VARCHAR(255)) AS DIA_CHI,
        CAST(c.SO_THE_KCB_GOC AS VARCHAR(15)) AS SO_THE_KCB_GOC,
        CAST(c.MA_KHOI_GOC AS VARCHAR(10)) AS MA_KHOI_GOC,
        CAST(c.TU_NGAY_GOC AS DATE) AS TU_NGAY_GOC,
        CAST(c.DEN_NGAY_GOC AS DATE) AS DEN_NGAY_GOC,
        CAST(c.DM_BHXH_ID_GOC AS INTEGER) AS DM_BHXH_ID_GOC,
        CAST(c.MA_TINH_GOC AS VARCHAR(20)) AS MA_TINH_GOC,
        CAST(c.SO_THE_KCB_HIEN_TAI AS VARCHAR(15)) AS SO_THE_KCB_HIEN_TAI,
        CAST(c.MA_KHOI_HIEN_TAI AS VARCHAR(10)) AS MA_KHOI_HIEN_TAI,
        CAST(c.TU_NGAY_HIEN_TAI AS DATE) AS TU_NGAY_HIEN_TAI,
        CAST(c.DEN_NGAY_HIEN_TAI AS DATE) AS DEN_NGAY_HIEN_TAI,
        CAST(c.DM_BHXH_ID_HIEN_TAI AS INTEGER) AS DM_BHXH_ID_HIEN_TAI,
        CAST(c.MA_TINH_HIEN_TAI AS VARCHAR(20)) AS MA_TINH_HIEN_TAI,
        CAST(g.SO_DOT_GIAN_DOAN AS INTEGER) AS SO_DOT_GIAN_DOAN,
        CAST(g.SO_NGAY_GIAN_DOAN AS INTEGER) AS SO_NGAY_GIAN_DOAN,
        CAST(g.SO_THANG_GIAN_DOAN AS NUMERIC(4, 1)) AS SO_THANG_GIAN_DOAN,
        DATE '{base_start}' AS NGAY_GOC,
        DATE '{window_end}' AS NGAY_KIEM_TRA,
        CAST('{report_date} 08:00:00' AS TIMESTAMP) AS CREATED_AT
    FROM candidates c
    JOIN person_gaps g ON c.SO_SO_BHXH = g.SO_SO_BHXH
    WHERE g.SO_NGAY_GIAN_DOAN >= {min_gap_days}
    ORDER BY c.SO_SO_BHXH ASC;

    -- 9. Danh mục 63 tỉnh chuẩn
    CREATE TEMPORARY TABLE dm_tinh AS
    SELECT
        CAST(MA_DVI AS VARCHAR(20)) AS MA_TINH,
        CAST(TEN_DVI AS VARCHAR(200)) AS TEN_TINH
    FROM {dm_read_sql}
    WHERE MA_CHA IS NULL OR MA_CHA = '' OR MA_CHA = '00';

    -- Bảng ánh xạ DM_BHXH_ID ra mã tỉnh quản lý
    CREATE TEMPORARY TABLE dm_mapping AS
    SELECT
        ID AS DM_BHXH_ID,
        CAST(COALESCE(NULLIF(NULLIF(MA_CHA, ''), '00'), MA_DVI) AS VARCHAR(20)) AS MA_TINH_QUY_DOI
    FROM {dm_read_sql};

    -- 10. Bảng tổng hợp thống kê địa bàn hành chính: TK_DBHC_HSSV_GIAN_DOAN_BHYT
    CREATE TEMPORARY TABLE tk_raw AS
    WITH person_prov AS (
        SELECT
            bc.SO_SO_BHXH,
            bc.MA_KHOI_GOC,
            bc.SO_NGAY_GIAN_DOAN,
            COALESCE(m.MA_TINH_QUY_DOI, LPAD(CAST(bc.MA_TINH_GOC AS VARCHAR), 2, '0')) AS MA_TINH_FINAL
        FROM bc_raw bc
        LEFT JOIN dm_mapping m ON bc.DM_BHXH_ID_GOC = m.DM_BHXH_ID
    ),
    agg_prov AS (
        SELECT
            MA_TINH_FINAL,
            COUNT(CASE WHEN MA_KHOI_GOC = 'HS' THEN 1 END) AS SO_LUONG_HS_GIAN_DOAN,
            COUNT(CASE WHEN MA_KHOI_GOC = 'SV' THEN 1 END) AS SO_LUONG_SV_GIAN_DOAN,
            COUNT(*) AS TONG_SO_NGUOI_GIAN_DOAN,
            COALESCE(SUM(SO_NGAY_GIAN_DOAN), 0) AS TONG_NGAY_GIAN_DOAN
        FROM person_prov
        GROUP BY MA_TINH_FINAL
    )
    SELECT
        t.MA_TINH,
        t.TEN_TINH,
        COALESCE(a.SO_LUONG_HS_GIAN_DOAN, 0) AS SO_LUONG_HS_GIAN_DOAN,
        COALESCE(a.SO_LUONG_SV_GIAN_DOAN, 0) AS SO_LUONG_SV_GIAN_DOAN,
        COALESCE(a.TONG_SO_NGUOI_GIAN_DOAN, 0) AS TONG_SO_NGUOI_GIAN_DOAN,
        COALESCE(a.TONG_NGAY_GIAN_DOAN, 0) AS TONG_NGAY_GIAN_DOAN,
        DATE '{report_date}' AS NGAY_BAO_CAO
    FROM dm_tinh t
    LEFT JOIN agg_prov a ON t.MA_TINH = a.MA_TINH_FINAL
    ORDER BY t.MA_TINH ASC;
    """
    return sql

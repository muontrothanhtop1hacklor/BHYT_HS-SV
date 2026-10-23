-- ============================================================================================
-- TRUY VẤN SQL ĐỘC LẬP KIỂM CHỨNG BÀI TOÁN Ý 2 (CV 835/QLT)
-- Mục tiêu: Tìm học sinh, sinh viên tham gia tháng 10/2024, tháng 7/2026 vẫn đang tham gia,
-- nhưng có thời gian gián đoạn không tham gia từ 3 tháng trở lên (>= 90 ngày).
-- ============================================================================================

WITH valid_cards AS (
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
        GREATEST(TU_NGAY, DATE '2024-10-01') AS tu_clip,
        LEAST(DEN_NGAY, DATE '2026-07-31') AS den_clip
    FROM read_parquet('data/silver/st_inthe_dtl/*.parquet')
    WHERE TRANG_THAI = 1
),
-- 1. Thẻ giao tháng gốc (10/2024) thuộc khối HS, SV
base_cards AS (
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
    WHERE TU_NGAY < DATE '2024-11-01' AND DEN_NGAY >= DATE '2024-10-01'
      AND MA_KHOI IN ('HS', 'SV')
),
primary_base AS (
    SELECT * FROM base_cards WHERE rn_base = 1
),
-- 2. Thẻ giao tháng kiểm tra (07/2026) thuộc mọi khối
check_cards AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY SO_SO_BHXH
            ORDER BY DEN_NGAY DESC, SO_THE_KCB ASC
        ) AS rn_chk
    FROM valid_cards
    WHERE TU_NGAY < DATE '2026-08-01' AND DEN_NGAY >= DATE '2026-07-01'
),
primary_chk AS (
    SELECT * FROM check_cards WHERE rn_chk = 1
),
-- 3. Ứng viên thỏa mãn cả 2 mốc bắt đầu và kết thúc
candidates AS (
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
    JOIN primary_chk c ON b.SO_SO_BHXH = c.SO_SO_BHXH
),
-- 4. Toàn bộ các thẻ của ứng viên nằm trong cửa sổ [2024-10-01, 2026-07-31]
cand_window_cards AS (
    SELECT
        v.SO_SO_BHXH,
        v.tu_clip AS tu,
        v.den_clip AS den
    FROM valid_cards v
    JOIN (SELECT DISTINCT SO_SO_BHXH FROM candidates) cd ON v.SO_SO_BHXH = cd.SO_SO_BHXH
    WHERE v.tu_clip <= v.den_clip
),
-- 5. Thuật toán gộp các khoảng thời gian chồng lấn/liên tục
with_prev AS (
    SELECT
        SO_SO_BHXH,
        tu,
        den,
        MAX(den) OVER (
            PARTITION BY SO_SO_BHXH
            ORDER BY tu, den
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS prev_max_den
    FROM cand_window_cards
),
with_new_grp AS (
    SELECT
        SO_SO_BHXH,
        tu,
        den,
        CASE
            WHEN prev_max_den IS NULL OR tu > prev_max_den + INTERVAL 1 DAY THEN 1
            ELSE 0
        END AS is_new_grp
    FROM with_prev
),
with_grp_id AS (
    SELECT
        SO_SO_BHXH,
        tu,
        den,
        SUM(is_new_grp) OVER (
            PARTITION BY SO_SO_BHXH
            ORDER BY tu, den
            ROWS UNBOUNDED PRECEDING
        ) AS grp_id
    FROM with_new_grp
),
merged_intervals AS (
    SELECT
        SO_SO_BHXH,
        grp_id,
        MIN(tu) AS m_tu,
        MAX(den) AS m_den
    FROM with_grp_id
    GROUP BY SO_SO_BHXH, grp_id
),
-- 6. Tính khoảng trống giữa các đoạn liên tục và ở hai biên kỳ
with_gaps AS (
    SELECT
        SO_SO_BHXH,
        m_tu,
        m_den,
        LAG(m_den) OVER (PARTITION BY SO_SO_BHXH ORDER BY m_tu) AS prev_m_den,
        (m_tu - LAG(m_den) OVER (PARTITION BY SO_SO_BHXH ORDER BY m_tu) - 1) AS gap_days
    FROM merged_intervals
),
gap_events AS (
    SELECT SO_SO_BHXH, gap_days
    FROM with_gaps
    WHERE gap_days > 0
    UNION ALL
    SELECT mi.SO_SO_BHXH, mi.m_tu - DATE '2024-10-01' AS gap_days
    FROM merged_intervals mi
    WHERE mi.m_tu = (
        SELECT MIN(x.m_tu) FROM merged_intervals x WHERE x.SO_SO_BHXH = mi.SO_SO_BHXH
    ) AND mi.m_tu > DATE '2024-10-01'
    UNION ALL
    SELECT mi.SO_SO_BHXH, DATE '2026-07-31' - mi.m_den AS gap_days
    FROM merged_intervals mi
    WHERE mi.m_tu = (
        SELECT MAX(x.m_tu) FROM merged_intervals x WHERE x.SO_SO_BHXH = mi.SO_SO_BHXH
    ) AND mi.m_den < DATE '2026-07-31'
),
person_gaps AS (
    SELECT
        SO_SO_BHXH,
        COUNT(gap_days) AS SO_DOT_GIAN_DOAN,
        COALESCE(SUM(gap_days), 0) AS SO_NGAY_GIAN_DOAN,
        ROUND(COALESCE(SUM(gap_days), 0) / 30.0, 1) AS SO_THANG_GIAN_DOAN
    FROM gap_events
    GROUP BY SO_SO_BHXH
),
-- 7. Lọc điều kiện gián đoạn >= 3 tháng (>= 90 ngày)
result_y2 AS (
    SELECT
        c.*,
        g.SO_DOT_GIAN_DOAN,
        g.SO_NGAY_GIAN_DOAN,
        g.SO_THANG_GIAN_DOAN,
        DATE '2024-10-01' AS NGAY_GOC,
        DATE '2026-07-31' AS NGAY_KIEM_TRA
    FROM candidates c
    JOIN person_gaps g ON c.SO_SO_BHXH = g.SO_SO_BHXH
    WHERE g.SO_NGAY_GIAN_DOAN >= 90
)
SELECT 
    CAST(SO_SO_BHXH AS VARCHAR) AS SO_SO_BHXH,
    MA_KHOI_GOC,
    SO_DOT_GIAN_DOAN,
    SO_NGAY_GIAN_DOAN,
    SO_THANG_GIAN_DOAN
FROM result_y2
ORDER BY SO_SO_BHXH ASC;

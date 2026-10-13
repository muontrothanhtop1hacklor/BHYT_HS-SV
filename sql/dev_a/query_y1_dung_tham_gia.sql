-- ==============================================================================
-- GIẢI PHÁP BẠN A: Xử lý bài toán Ý 1 (CV 835/QLT)
-- Logic: Lọc CTE tập gốc T10/2024 -> Lọc tập đang tham gia hiện tại -> Anti Join
-- ==============================================================================

-- Mốc thời gian:
-- Kỳ gốc: Tháng 10/2024 (TU_NGAY < '2024-11-01' AND DEN_NGAY >= '2024-10-01')
-- Mốc hiện tại: '2026-08-10' (hoặc '2026-08-31')

WITH tap_goc_t10_2024 AS (
    -- Bước 1: Những người tham gia BHYT mốc T10/2024 với tư cách HSSV
    SELECT 
        s.SO_SO_BHXH,
        s.HO_TEN,
        s.NGAY_SINH,
        s.GIOI_TINH,
        s.SO_CMND,
        s.SO_THE_KCB AS SO_THE_KCB_GOC,
        s.MA_KHOI AS MA_KHOI_GOC,
        s.TU_NGAY AS TU_NGAY_GOC,
        s.DEN_NGAY AS DEN_NGAY_GOC,
        s.DM_BHXH_ID,
        ROW_NUMBER() OVER (
            PARTITION BY s.SO_SO_BHXH 
            ORDER BY s.DEN_NGAY DESC, s.ID DESC
        ) AS rn
    FROM ST_INTHE_DTL s
    WHERE s.TRANG_THAI = 1
      AND s.MA_KHOI IN ('HS', 'SV')
      AND s.TU_NGAY < DATE '2024-11-01'
      AND s.DEN_NGAY >= DATE '2024-10-01'
),
tap_goc_unique AS (
    SELECT * FROM tap_goc_t10_2024 WHERE rn = 1
),
tap_hien_tai AS (
    -- Bước 2: Những người ĐANG CÒN THAM GIA BHYT tại mốc hiện tại (bất kỳ khối nào)
    SELECT DISTINCT s.SO_SO_BHXH
    FROM ST_INTHE_DTL s
    WHERE s.TRANG_THAI = 1
      AND s.TU_NGAY <= DATE '2026-08-10'
      AND s.DEN_NGAY >= DATE '2026-08-10'
)
-- Bước 3: Lấy người trong tập gốc T10/2024 nhưng KHÔNG có trong tập hiện tại
SELECT 
    g.SO_SO_BHXH,
    g.HO_TEN,
    g.NGAY_SINH,
    g.GIOI_TINH,
    g.SO_CMND,
    g.SO_THE_KCB_GOC,
    g.MA_KHOI_GOC,
    g.TU_NGAY_GOC,
    g.DEN_NGAY_GOC,
    g.DM_BHXH_ID,
    d.MA_CHA AS MA_TINH,
    DATE '2024-10-01' AS NGAY_GOC,
    DATE '2026-08-10' AS NGAY_KIEM_TRA
FROM tap_goc_unique g
LEFT JOIN DM_BHXH d ON g.DM_BHXH_ID = d.ID
WHERE NOT EXISTS (
    SELECT 1 FROM tap_hien_tai h WHERE h.SO_SO_BHXH = g.SO_SO_BHXH
);

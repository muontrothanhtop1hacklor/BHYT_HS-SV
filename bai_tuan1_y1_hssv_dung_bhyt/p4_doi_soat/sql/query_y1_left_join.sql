-- ==============================================================================
-- GIẢI PHÁP BẠN B: Xử lý bài toán Ý 1 (CV 835/QLT)
-- Logic: Sử dụng Window Function + Left Join IS NULL kiểm tra thẻ sau mốc gốc
-- ==============================================================================

-- Bạn B có thể độc lập thiết kế cách tiếp cận riêng (ví dụ: tối ưu phép join hoặc group by)

WITH hssv_oct_2024 AS (
    SELECT 
        SO_SO_BHXH,
        HO_TEN,
        NGAY_SINH,
        GIOI_TINH,
        SO_CMND,
        SO_THE_KCB AS SO_THE_KCB_GOC,
        MA_KHOI AS MA_KHOI_GOC,
        TU_NGAY AS TU_NGAY_GOC,
        DEN_NGAY AS DEN_NGAY_GOC,
        DM_BHXH_ID,
        ROW_NUMBER() OVER (PARTITION BY SO_SO_BHXH ORDER BY TU_NGAY DESC, DEN_NGAY DESC) AS rnk
    FROM ST_INTHE_DTL
    WHERE TRANG_THAI = 1
      AND MA_KHOI IN ('HS', 'SV')
      AND TU_NGAY < DATE '2024-11-01'
      AND DEN_NGAY >= DATE '2024-10-01'
),
active_now AS (
    SELECT DISTINCT SO_SO_BHXH
    FROM ST_INTHE_DTL
    WHERE TRANG_THAI = 1
      AND TU_NGAY <= DATE '2026-08-10'
      AND DEN_NGAY >= DATE '2026-08-10'
)
SELECT 
    b.SO_SO_BHXH,
    b.HO_TEN,
    b.NGAY_SINH,
    b.GIOI_TINH,
    b.SO_CMND,
    b.SO_THE_KCB_GOC,
    b.MA_KHOI_GOC,
    b.TU_NGAY_GOC,
    b.DEN_NGAY_GOC,
    b.DM_BHXH_ID,
    d.MA_CHA AS MA_TINH,
    DATE '2024-10-01' AS NGAY_GOC,
    DATE '2026-08-10' AS NGAY_KIEM_TRA
FROM hssv_oct_2024 b
LEFT JOIN active_now a ON b.SO_SO_BHXH = a.SO_SO_BHXH
LEFT JOIN DM_BHXH d ON b.DM_BHXH_ID = d.ID
WHERE b.rnk = 1
  AND a.SO_SO_BHXH IS NULL;

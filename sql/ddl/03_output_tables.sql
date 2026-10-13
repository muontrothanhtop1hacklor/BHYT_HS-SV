-- 1. Bảng danh sách chi tiết: BC_HSSV_DUNG_THAM_GIA
-- Chứa danh sách từng cá nhân HSSV thỏa mãn điều kiện dừng tham gia

CREATE TABLE IF NOT EXISTS BC_HSSV_DUNG_THAM_GIA (
    SO_SO_BHXH          VARCHAR(10) PRIMARY KEY, -- Mã số BHXH người dừng
    HO_TEN              VARCHAR(100),
    NGAY_SINH           DATE,
    GIOI_TINH           SMALLINT,
    SO_CMND             VARCHAR(12),
    SO_THE_KCB_GOC      VARCHAR(15),             -- Mã thẻ tại mốc gốc T10/2024
    MA_KHOI_GOC         VARCHAR(10),             -- 'HS' hoặc 'SV'
    TU_NGAY_GOC         DATE,
    DEN_NGAY_GOC        DATE,
    DM_BHXH_ID          INTEGER,                 -- Cơ quan BHXH quản lý tại mốc gốc
    MA_TINH             VARCHAR(20),             -- Mã tỉnh/thành phố quản lý
    NGAY_GOC            DATE,                    -- Mốc gốc: 2024-10-01
    NGAY_KIEM_TRA       DATE,                    -- Mốc kiểm tra: 2026-08-10 (hoặc 2026-08-31)
    CREATED_AT          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng tổng hợp thống kê theo địa bàn hành chính: TK_DBHC_HSSV_DUNG_THAM_GIA
-- Tổng hợp theo từng Tỉnh/Thành phố

CREATE TABLE IF NOT EXISTS TK_DBHC_HSSV_DUNG_THAM_GIA (
    MA_TINH             VARCHAR(20) PRIMARY KEY, -- Mã BHXH Tỉnh/TP
    TEN_TINH            VARCHAR(200),            -- Tên Tỉnh/TP
    SO_LUONG_HS_DUNG    BIGINT DEFAULT 0,        -- Số lượng học sinh dừng
    SO_LUONG_SV_DUNG    BIGINT DEFAULT 0,        -- Số lượng sinh viên dừng
    TONG_SO_NGUOI_DUNG  BIGINT DEFAULT 0,        -- Tổng cộng (HS + SV)
    NGAY_BAO_CAO        DATE
);

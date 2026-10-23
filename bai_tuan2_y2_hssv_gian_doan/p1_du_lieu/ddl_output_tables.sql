-- ============================================================================================
-- DDL CÁC BẢNG KẾT QUẢ ĐẦU RA CHO BÀI TOÁN Ý 2 (CV 835/QLT)
-- Học sinh, sinh viên tham gia từ tháng 10/2024, tháng 7/2026 vẫn đang tham gia
-- nhưng có thời gian gián đoạn không tham gia từ 3 tháng trở lên (>= 90 ngày).
-- ============================================================================================

-- 1. BẢNG DANH SÁCH CHI TIẾT: BC_HSSV_GIAN_DOAN_BHYT
-- Ghi nhận danh sách từng cá nhân thỏa mãn cả 3 điều kiện:
-- - Mốc bắt đầu (T10/2024): Đang tham gia khối Học sinh (HS) hoặc Sinh viên (SV).
-- - Mốc kết thúc (T07/2026): Vẫn đang tham gia BHYT ở bất kỳ khối nào.
-- - Tiến trình: Tổng thời gian gián đoạn tích lũy >= 3 tháng (>= 90 ngày).

CREATE TABLE IF NOT EXISTS BC_HSSV_GIAN_DOAN_BHYT (
    SO_SO_BHXH                  VARCHAR(10) PRIMARY KEY, -- Mã số BHXH (10 chữ số)
    HO_TEN                      VARCHAR(100),            -- Họ và tên
    NGAY_SINH                   DATE,                    -- Ngày sinh
    GIOI_TINH                   SMALLINT,                -- 1: Nam, 2: Nữ
    SO_CMND                     VARCHAR(12),             -- CCCD / CMND
    DIA_CHI                     VARCHAR(255),            -- Địa chỉ cư trú
    
    -- Thông tin thẻ đại diện tại mốc bắt đầu (Tháng 10/2024)
    SO_THE_KCB_GOC              VARCHAR(15),             -- Mã thẻ BHYT mốc gốc (VD: HS479..., SV479...)
    MA_KHOI_GOC                 VARCHAR(10),             -- Khối mốc gốc: 'HS' hoặc 'SV'
    TU_NGAY_GOC                 DATE,                    -- Ngày bắt đầu thẻ mốc gốc
    DEN_NGAY_GOC                DATE,                    -- Ngày kết thúc thẻ mốc gốc
    DM_BHXH_ID_GOC              INTEGER,                 -- Mã cơ quan quản lý tại mốc gốc
    MA_TINH_GOC                 VARCHAR(20),             -- Mã tỉnh/thành phố quản lý tại mốc gốc
    
    -- Thông tin thẻ đại diện tại mốc kết thúc (Tháng 07/2026)
    SO_THE_KCB_HIEN_TAI         VARCHAR(15),             -- Mã thẻ BHYT mốc hiện tại
    MA_KHOI_HIEN_TAI            VARCHAR(10),             -- Khối hiện tại ('HS', 'SV', 'DN', 'GD',...)
    TU_NGAY_HIEN_TAI            DATE,                    -- Ngày bắt đầu thẻ hiện tại
    DEN_NGAY_HIEN_TAI           DATE,                    -- Ngày kết thúc thẻ hiện tại
    DM_BHXH_ID_HIEN_TAI         INTEGER,                 -- Mã cơ quan quản lý hiện tại
    MA_TINH_HIEN_TAI            VARCHAR(20),             -- Mã tỉnh/thành phố quản lý hiện tại
    
    -- Thông tin về chuỗi thời gian gián đoạn (Gaps)
    SO_DOT_GIAN_DOAN            INTEGER,                 -- Số đợt gián đoạn phát hiện trong kỳ
    SO_NGAY_GIAN_DOAN           INTEGER,                 -- Tổng số ngày gián đoạn cộng dồn (>= 90)
    SO_THANG_GIAN_DOAN          NUMERIC(4, 1),           -- Số tháng gián đoạn quy chuẩn (= SO_NGAY / 30.0)
    
    -- Thông tin mốc báo cáo
    NGAY_GOC                    DATE,                    -- Mốc gốc: 2024-10-01
    NGAY_KIEM_TRA               DATE,                    -- Mốc kết thúc: 2026-07-31
    CREATED_AT                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Thời điểm ghi nhận
);

-- Chỉ mục tối ưu truy vấn tra cứu và đối soát:
CREATE INDEX IF NOT EXISTS idx_bc_y2_khoi_goc ON BC_HSSV_GIAN_DOAN_BHYT(MA_KHOI_GOC);
CREATE INDEX IF NOT EXISTS idx_bc_y2_tinh_goc ON BC_HSSV_GIAN_DOAN_BHYT(MA_TINH_GOC);
CREATE INDEX IF NOT EXISTS idx_bc_y2_days ON BC_HSSV_GIAN_DOAN_BHYT(SO_NGAY_GIAN_DOAN);


-- 2. BẢNG TỔNG HỢP THỐNG KÊ THEO ĐỊA BÀN HÀNH CHÍNH: TK_DBHC_HSSV_GIAN_DOAN_BHYT
-- Tổng hợp số lượng theo 63 Tỉnh/Thành phố phục vụ công tác quản lý thu

CREATE TABLE IF NOT EXISTS TK_DBHC_HSSV_GIAN_DOAN_BHYT (
    MA_TINH                     VARCHAR(20) PRIMARY KEY, -- Mã BHXH Tỉnh/TP (01 đến 96)
    TEN_TINH                    VARCHAR(200),            -- Tên Tỉnh/Thành phố
    SO_LUONG_HS_GIAN_DOAN       BIGINT DEFAULT 0,        -- Số lượng học sinh gián đoạn >= 3 tháng
    SO_LUONG_SV_GIAN_DOAN       BIGINT DEFAULT 0,        -- Số lượng sinh viên gián đoạn >= 3 tháng
    TONG_SO_NGUOI_GIAN_DOAN     BIGINT DEFAULT 0,        -- Tổng cộng HSSV gián đoạn (HS + SV)
    TONG_NGAY_GIAN_DOAN         BIGINT DEFAULT 0,        -- Tổng số ngày gián đoạn lũy kế của toàn tỉnh
    NGAY_BAO_CAO                DATE                     -- Ngày lập báo cáo (2026-08-10)
);

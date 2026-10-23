-- Bảng thẻ BHYT chi tiết (ST_INTHE_DTL)
-- Dữ liệu nguồn dùng chung từ Tuần 1: ~200 triệu bản ghi (Giai đoạn 2024 - 2026)

CREATE TABLE IF NOT EXISTS ST_INTHE_DTL (
    ID              BIGINT,           -- Định danh bản ghi thẻ
    SO_SO_BHXH      VARCHAR(10),      -- Mã số BHXH (10 số, định danh duy nhất người)
    SO_THE_KCB      VARCHAR(15),      -- Mã thẻ BHYT 15 ký tự (VD: HS479..., SV479...)
    HO_TEN          VARCHAR(100),     -- Họ và tên
    NGAY_SINH       DATE,             -- Ngày sinh
    GIOI_TINH       SMALLINT,         -- 1: Nam, 2: Nữ
    SO_CMND         VARCHAR(12),      -- CCCD/CMND
    DIA_CHI         VARCHAR(255),     -- Địa chỉ
    MA_KHOI         VARCHAR(10),      -- Mã khối: 'HS', 'SV', 'DN', 'GD', 'TE',...
    TU_NGAY         DATE,             -- Ngày thẻ bắt đầu hiệu lực
    DEN_NGAY        DATE,             -- Ngày thẻ hết hiệu lực
    TRANG_THAI      SMALLINT,         -- Trạng thái thẻ: 1 (Hiệu lực), 0 (Hủy/Cấp đổi)
    DM_BHXH_ID      INTEGER           -- Mã cơ quan quản lý (trỏ sang DM_BHXH.ID)
);

-- Chỉ mục khuyến nghị (nếu lưu trên RDBMS / DuckDB):
CREATE INDEX IF NOT EXISTS idx_st_inthe_person ON ST_INTHE_DTL(SO_SO_BHXH);
CREATE INDEX IF NOT EXISTS idx_st_inthe_dates ON ST_INTHE_DTL(TU_NGAY, DEN_NGAY, TRANG_THAI, MA_KHOI);

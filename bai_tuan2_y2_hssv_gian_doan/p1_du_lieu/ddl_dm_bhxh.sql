-- Bảng danh mục cơ quan BHXH (DM_BHXH)
-- Chứa danh mục phân cấp đơn vị BHXH từ cấp tỉnh xuống quận/huyện/cơ sở

CREATE TABLE IF NOT EXISTS DM_BHXH (
    ID          INTEGER PRIMARY KEY, -- Mã định danh cơ sở
    MA_DVI      VARCHAR(20),         -- Mã đơn vị BHXH (VD: '01' cho BHXH TP Hà Nội)
    TEN_DVI     VARCHAR(200),        -- Tên đơn vị BHXH
    MA_CHA      VARCHAR(20)          -- Mã cơ quan cấp trên (Mã tỉnh quản lý)
);

CREATE INDEX IF NOT EXISTS idx_dm_bhxh_ma_cha ON DM_BHXH(MA_CHA);

-- Bảng danh mục cơ quan BHXH (DM_BHXH)
-- Dùng để phân bổ địa bàn và quy đổi cơ quan quản lý về Tỉnh/Thành phố (MA_CHA)

CREATE TABLE IF NOT EXISTS DM_BHXH (
    ID          INTEGER PRIMARY KEY,  -- Mã định danh đơn vị
    MA_DVI      VARCHAR(20) NOT NULL, -- Mã cơ quan BHXH (VD: 00101, 79001)
    TEN_DVI     VARCHAR(200) NOT NULL,-- Tên cơ quan BHXH
    MA_CHA      VARCHAR(20)           -- Mã cơ quan cấp trên (Mã BHXH Tỉnh/TP)
);

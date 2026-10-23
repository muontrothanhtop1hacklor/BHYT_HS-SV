# Kế hoạch Tuần 2 — HSSV gián đoạn BHYT

**Thời gian:** Thứ Hai 19/10/2026 đến Thứ Sáu 23/10/2026  
**Mục tiêu tuần:** Chốt đúng nghiệp vụ tính gián đoạn, kiểm chứng pipeline Gold trên dữ liệu mẫu và dữ liệu đầy đủ, rồi bàn giao báo cáo có thể tái lập.

## Nhiệm vụ hôm nay — Thứ Hai 19/10

### Chủ đề: Khóa đặc tả nghiệp vụ và kiểm tra thuật toán Timeline

**Mục tiêu:** Bảo đảm cách hiểu khoảng thời gian, điều kiện chọn người và ngưỡng 90 ngày nhất quán giữa yêu cầu, thuật toán Python, SQL Gold và kiểm thử trước khi chạy toàn bộ dữ liệu.

### Các việc cần làm

1. Đối chiếu `docs/requirements/yeu_cau_tuan2_hssv_gian_doan.md`, `p2_thuat_toan_timeline/thuat_toan_timeline.md`, `p2_thuat_toan_timeline/timeline_algorithm.py` và `p3_gold/gold_logic_y2.py`.
2. Lập bảng ca nghiệp vụ tối thiểu, nêu rõ ngày gap và số ngày gap cho từng trường hợp:
   - Thẻ liên tục, thẻ chồng lấn và thẻ nằm trọn trong thẻ khác.
   - Một gap ngắn dưới 90 ngày; đúng 90 ngày; trên 90 ngày.
   - Nhiều gap ngắn cộng dồn đạt ngưỡng.
   - Gap đầu kỳ, gap cuối kỳ và trường hợp thẻ phủ toàn bộ cửa sổ.
   - Thẻ bị hủy; người thiếu thẻ ở mốc tháng 10/2024 hoặc tháng 07/2026.
   - Nhiều thẻ tại mốc gốc/mốc hiện tại để xác nhận quy tắc chọn thẻ đại diện.
3. So sánh từng kết quả mong đợi với cách tính trong Python và SQL; ghi lại điểm không khớp và sửa đặc tả hoặc logic tại nguồn phù hợp.
4. Chốt tiêu chí duy nhất cho “3 tháng trở lên” là tổng số ngày gián đoạn trong cửa sổ bao gồm hai đầu, với ngưỡng `>= 90` ngày.

### Bàn giao cuối ngày

- Bảng ca biên và kết quả mong đợi được ghi trong tài liệu thuật toán hoặc bộ kiểm thử hiện có.
- Mỗi ca có thể truy ngược tới điều kiện nghiệp vụ tương ứng; các quy tắc tie-break và cách đếm ngày không còn mâu thuẫn giữa tài liệu và mã nguồn.
- Danh sách vấn đề cần xử lý ngày mai, nếu có, được ghi cụ thể kèm tệp và tình huống tái hiện.

### Điều kiện hoàn thành

- Không còn bất đồng về cửa sổ `[2024-10-01, 2026-07-31]`, tính bao gồm ngày đầu/cuối, cách gộp khoảng liên tục/chồng lấn, hoặc ngưỡng `>= 90` ngày.
- Các ca biên quan trọng có expected result rõ ràng; mọi khác biệt giữa Python và SQL được sửa hoặc ghi thành việc cần xử lý.
- Chưa chạy pipeline 200 triệu dòng trong ngày này; mục tiêu là có bộ tiêu chí đúng để các bước kiểm chứng tiếp theo dựa vào.

## Lộ trình đến hết tuần

| Ngày | Trọng tâm | Kết quả cần có |
|---|---|---|
| Thứ Hai 19/10 | Khóa đặc tả và rà soát Timeline | Bảng ca biên, expected result, danh sách sai khác đã xử lý |
| Thứ Ba 20/10 | Hoàn thiện kiểm thử đơn vị và bất biến Gold | Bộ kiểm thử bao phủ các ca đã chốt; kết quả kiểm thử được ghi nhận |
| Thứ Tư 21/10 | Kiểm tra vận hành và hiệu năng pipeline | Cấu hình chạy, log/metadata và xác nhận xử lý đúng cấu trúc dữ liệu |
| Thứ Năm 22/10 | Chạy Gold đầy đủ và đối soát độc lập | Parquet/CSV mới; so sánh từng mã tỉnh và chỉ tiêu với truy vấn đối chiếu |
| Thứ Sáu 23/10 | Hoàn thiện báo cáo và bàn giao | Báo cáo cập nhật bằng số liệu mới, lệnh tái lập, giới hạn và kết luận |

## Thứ tự ưu tiên nếu phát hiện sai lệch

1. Sửa quy tắc nghiệp vụ trong tài liệu gốc nếu cách diễn đạt chưa rõ.
2. Cập nhật thuật toán Python và SQL để cùng thực thi một quy tắc.
3. Thêm ca kiểm thử hồi quy cho sai lệch vừa sửa.
4. Chỉ dùng số liệu Gold cũ làm lịch sử; không báo cáo chúng như kết quả đã xác nhận của tuần này.

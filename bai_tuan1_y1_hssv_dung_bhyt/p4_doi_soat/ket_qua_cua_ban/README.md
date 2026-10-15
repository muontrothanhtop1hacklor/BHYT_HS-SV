# Thư mục nhận kết quả từ bạn cùng làm

Thư mục này dùng để chứa file kết quả (`bc_hssv_dung_tham_gia.parquet`) nhận từ máy của bạn cùng làm để chạy đối soát chéo độc lập:
1. Đặt file kết quả của bạn vào thư mục này:
   `bai_tuan1_y1_hssv_dung_bhyt/p4_doi_soat/ket_qua_cua_ban/bc_hssv_dung_tham_gia.parquet`
2. Chạy đối soát:
   `python -m bai_tuan1_y1_hssv_dung_bhyt.p4_doi_soat.compare_results`
   hoặc chạy file batch: `bai_tuan1_y1_hssv_dung_bhyt\p4_doi_soat\chay_doi_soat.bat`
3. Xem báo cáo đối chiếu sinh ra tại:
   `data/output/reconciliation/reconciliation_report.md`

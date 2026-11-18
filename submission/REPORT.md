# Báo cáo Day 09 — Trần Đình Quang Vinh, 2A202603041

## 1. Kết luận trước

Pipeline AutoQC xử lý **224 ảnh đầu vào**, giữ lại **193/224 ảnh (86,16%)** và loại **31/224 ảnh (13,84%)** tại Intake. Dataset Clean v1 được xuất dưới dạng bản nháp tại `submission/export/clean_v1/`.

**Kết luận: HOLD.** Sau khi AutoFix và mô phỏng người duyệt, còn **34/193 ảnh (17,62%)** có cảnh báo chưa duyệt, vượt ngưỡng HOLD **10%**. Dataset chưa được phép phát hành chính thức.

## 2. Lỗi và phân việc

Theo `02_error_list_v1.csv`, Intake ghi nhận 31 lỗi loại ảnh; QC vòng 1 ghi nhận **36 lỗi bắt buộc và 145 cảnh báo**. Các mã được thống kê như sau:

| Mã lỗi | Số ảnh/dòng | Ai xử lý | Vì sao |
|---|---:|---|---|
| `CORRUPT_IMAGE` | 2 ảnh | Máy | Loại ảnh hỏng |
| `BAD_SIZE` | 3 ảnh | Máy | Loại ảnh quá nhỏ |
| `DUP_IMAGE_EXACT` | 8 ảnh | Máy | Loại ảnh trùng tuyệt đối |
| `DUP_IMAGE_NEAR` | 7 ảnh | Máy | Loại ảnh gần trùng |
| `LEAK_TEST` | 11 ảnh | Máy | Ngăn rò rỉ tập test/val |
| `MISSING_LABEL_FILE` | 6 ảnh | Người | Cần gán nhãn thủ công |
| `BAD_FORMAT` | 3 dòng | Máy | Loại dòng sai định dạng |
| `BAD_CLASS_ID` | 6 dòng | Máy | Loại nhãn có ID không hợp lệ |
| `BAD_CLASS_NAME` | 2 dòng | Máy/người | Chuẩn hóa tên lớp theo taxonomy |
| `BOX_OUT_OF_IMAGE` | 8 dòng | Máy | Clip box khi có thể sửa an toàn |
| `BOX_ZERO` | 4 dòng | Máy | Loại box có kích thước bằng 0 |
| `DUP_BOX` | 7 dòng | Máy | Loại box trùng |
| `EMPTY_LABEL` | 11 ảnh | Người | Xác minh ảnh nền hay thiếu nhãn |
| `BOX_TINY` | 6 dòng/4 ảnh | Người | Xác minh đối tượng nhỏ |
| `BOX_HUGE` | 3 dòng | Người | Kiểm tra box quá lớn |
| `CLASS_RARE` | 4 dòng thống kê | Người | Xem xét phân bố lớp hiếm |
| `POSSIBLE_MISSING` | 53 cảnh báo/52 ảnh | Người | Kiểm tra thiếu đối tượng |
| `POSSIBLE_FALSE_POS` | 24 cảnh báo/23 ảnh | Người | Kiểm tra nhãn thừa |
| `POSSIBLE_WRONG_CLASS` | 17 cảnh báo/17 ảnh | Người | Xác minh sai lớp |
| `POSSIBLE_LOOSE_BOX` | 27 cảnh báo/23 ảnh | Người | Kiểm tra box chưa khít |

AutoFix thực hiện **35 thay đổi**. Sau AutoFix, còn **6 lỗi bắt buộc** chuyển vào quy trình người duyệt.

**Review Queue:** Có **121 ảnh cần duyệt**, ngân sách **80 ảnh (66,12% hàng đợi)**. Hàng đợi ưu tiên ảnh thiếu nhãn (`NEEDS_LABEL`, trọng số 10), sai lớp (3), thiếu nhãn và false positive (2).

Theo `06_review_log.csv`, người duyệt mô phỏng xử lý **80 ảnh**, gồm 88 lượt ghi nhận mã cảnh báo ngữ nghĩa: `POSSIBLE_MISSING` 51, `POSSIBLE_WRONG_CLASS` 17, `POSSIBLE_FALSE_POS` 12 và `POSSIBLE_LOOSE_BOX` 8. Một ảnh có thể mang nhiều mã.

## 3. Calibration (2 ngưỡng)

Calibration thực hiện trên **39 ảnh** có lỗi cố ý.

| Tham số | Khởi đầu | Đã chọn | Precision / Recall trước → sau | Lý do |
|---|---:|---:|---|---|
| `duplicates.phash_dist` | 2 | **16** | Near duplicate: P 1,00 → 1,00; R 0,50 → 0,83 | F1 tăng từ 0,67 lên 0,91 |
| `second_opinion.conf` | 0.25 | **0.60** | Wrong class: P 0,56 → 0,62; R 0,83 → 0,83 | Giảm cảnh báo sai mà giữ recall |

Ở `conf = 0.60`, `POSSIBLE_MISSING` đạt Precision **0,57**, Recall **1,00**. Nếu tăng đến 0,80, Recall giảm còn 0,75. Vì vậy chọn 0,60 để hạn chế bỏ sót nhãn.

**Điểm Calibration có thể đánh lừa:** Tập calib chỉ có 39 ảnh. Dù `DUP_IMAGE_NEAR` đạt Precision 1,00, ngưỡng pHash 16 vẫn có nguy cơ loại ảnh khác nhau nhưng có cấu trúc tương tự. Trong dữ liệu thực, `img_0011` gần trùng `img_0008` (distance 16), `img_0084` gần trùng `img_0074` (distance 16). Tổng cộng Intake loại 31/224 ảnh; cần đối chiếu trực quan những cặp này trước khi phát hành.

## 4. Cửa chặn và điều pipeline KHÔNG bắt được

**Thí nghiệm 1 — Ngân sách 80 ảnh:**

Pipeline kết luận **HOLD**: không còn lỗi bắt buộc (`n_errors = 0`), nhưng **34/193 ảnh (17,62%)** còn cảnh báo chưa duyệt, vượt ngưỡng 10%.

**Thí nghiệm 2 — Ngân sách 0 ảnh:**

Đã chạy:

```bash
python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb
```

Kết quả:

- Nhận 193/224 ảnh, loại 31.
- AutoFix thực hiện 35 thay đổi.
- Sau AutoFix còn 6 lỗi bắt buộc.
- Không thực hiện review vì ngân sách 0 ảnh.
- Gate kết luận **REWORK**, còn 6 lỗi bắt buộc.
- **Không xuất dataset**; mã thoát quy định cho REWORK là 20.

Thí nghiệm xác nhận Gate không cho phép phát hành khi còn lỗi bắt buộc. Log đã xác nhận REWORK và không xuất dữ liệu; mã thoát 20 cần kiểm tra riêng nếu muốn chứng minh bằng Terminal.

**Hai điểm mù:**

1. `POSSIBLE_LOOSE_BOX` tại confidence 0,60 đạt Recall **0,20**, nghĩa là chỉ phát hiện 1/5 lỗi loose box được chèn vào calib. Những box lệch nhẹ vẫn có thể bị bỏ sót.
2. `POSSIBLE_WRONG_CLASS` đạt Recall **0,83**, bỏ sót 1/6 trường hợp sai lớp trong calib. Model YOLO26l có thể dự đoán sai tương tự người gán nhãn nên không thể thay thế ground truth.

Vì vậy, AutoQC phù hợp để sàng lọc và ưu tiên review, không thay thế kiểm tra ngữ nghĩa của con người.

## 5. Train: raw vs clean (tùy chọn, chấm riêng)

**Trạng thái: Chưa chạy.**

Nguyên nhân: đang hoàn thiện kiểm thử, Calibration, AutoQC Pipeline và báo cáo trước khi huấn luyện.

Thí nghiệm dự kiến sử dụng YOLO26n, 20 epochs, seed 0 và 1 cho hai biến thể Raw/Clean, đánh giá trên cùng tập test.

Chưa có kết quả mAP50 hay độ lệch chuẩn giữa các seed nên chưa thể kết luận Clean tốt hơn Raw. Các giả thuyết cần kiểm chứng gồm ảnh trùng/rò rỉ trong Raw, cảnh báo chưa xử lý trong Clean và độ biến động do tập test chỉ có 100 ảnh.

## 6. Quyết định và ghi chú AI

**Quyết định cuối: HOLD — chưa phát hành Clean v1.**

Để chuyển sang RELEASE cần xử lý các cảnh báo còn tồn tại, ưu tiên **34/193 ảnh chưa duyệt có cảnh báo**, xác minh các cặp ảnh gần trùng, kiểm tra lại nhãn ngữ nghĩa và chạy lại pipeline. Điều kiện là không còn lỗi bắt buộc và tỷ lệ ảnh còn cảnh báo chưa duyệt phải thấp hơn 10%.

**Ghi chú AI:**

- **Prompt chính:** Sử dụng AI để phân tích repository Day 09, và hỗ trợ triển khai bốn module `label_format`, `gate`, `autofix`, `second_opinion`.
- **Kiểm tra code AI:** Chạy `python -m pytest -q` đạt **79/79 test PASS**, Calibration trên 39 ảnh và thực nghiệm pipeline với ngân sách 80 và 0 ảnh.
- **Một lần AI sai:** AI nhận định chưa chính xác nguyên nhân hai lỗi trong `pipeline/calibrate.py`. Sau khi kiểm tra Git và `_protected.json`, xác nhận đây là file gốc được bảo vệ. Không sửa file này để né kiểm tra; cần đối chiếu mã nguồn thực tế trước khi áp dụng đề xuất.

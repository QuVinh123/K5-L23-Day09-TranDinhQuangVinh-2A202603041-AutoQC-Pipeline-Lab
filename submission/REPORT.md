# Báo cáo Day 09 — Trần Đình Quang Vinh, 2A202603041

## 1. Kết luận trước

AutoQC xử lý **224 ảnh đầu vào**, giữ lại **193/224 ảnh (86,16%)**, loại **31/224 ảnh (13,84%)** tại Intake. Sau tự động sửa lỗi và mô phỏng người duyệt, pipeline kết luận **HOLD**: **34/193 ảnh (17,62%)** vẫn có cảnh báo chưa duyệt, vượt ngưỡng **10%**. Không còn lỗi bắt buộc sau review (`n_errors = 0`). Dữ liệu tại `submission/export/clean_v1/` là **bản nháp cho thí nghiệm**, chưa được phát hành chính thức.

## 2. Lỗi và phân việc

Intake loại 31 ảnh; QC vòng 1 phát hiện **36 lỗi bắt buộc, 145 cảnh báo**. AutoFix ghi nhận **35 thay đổi**, QC vòng 2 còn **6 lỗi bắt buộc**. Bảng dưới đây tổng hợp các mã thực sự xuất hiện trong `02_error_list_v1.csv`; một ảnh có thể có nhiều lỗi nên không cộng số dòng để suy ra số ảnh duy nhất.

| Mã lỗi | Số ảnh/dòng cảnh báo | Ai xử lý | Vì sao |
|---|---:|---|---|
| `CORRUPT_IMAGE` | 2 ảnh | Máy | Loại ảnh không mở được |
| `BAD_SIZE` | 3 ảnh | Máy | Loại ảnh dưới kích thước tối thiểu |
| `DUP_IMAGE_EXACT` | 8 ảnh | Máy | Loại bản sao trùng byte |
| `DUP_IMAGE_NEAR` | 7 ảnh | Máy, cần kiểm tra mẫu | Loại ảnh gần trùng theo pHash |
| `LEAK_TEST` | 11 ảnh | Máy | Loại ảnh trùng tập test/validation |
| `MISSING_LABEL_FILE` | 6 ảnh | Người | Máy không được tự tạo nhãn thiếu |
| `BAD_FORMAT` | 3 dòng | Máy | Bỏ dòng sai định dạng |
| `BAD_CLASS_ID` | 6 dòng | Máy | Xử lý nhãn có class ID ngoài taxonomy |
| `BAD_CLASS_NAME` | 2 dòng (trong `data.yaml`) | Máy | Chuẩn hóa tên lớp theo taxonomy |
| `BOX_OUT_OF_IMAGE` | 8 dòng | Máy | Giới hạn box về biên ảnh nếu sửa an toàn |
| `BOX_ZERO` | 4 dòng | Máy | Loại box không có diện tích dương |
| `DUP_BOX` | 7 dòng | Máy | Loại box trùng nhau |
| `EMPTY_LABEL` | 11 ảnh | Người | Phân biệt ảnh nền với ảnh thiếu nhãn |
| `BOX_TINY` | 6 dòng/4 ảnh | Người | Xác minh vật thể quá nhỏ |
| `BOX_HUGE` | 3 dòng | Người | Xác minh box quá lớn |
| `CLASS_RARE` | 4 cảnh báo mức dataset | Người | Rà soát phân bố lớp bất thường |
| `POSSIBLE_MISSING` | 53 cảnh báo | Người | Xác minh vật thể chưa được gán nhãn |
| `POSSIBLE_FALSE_POS` | 24 cảnh báo | Người | Xác minh box không khớp vật thể |
| `POSSIBLE_WRONG_CLASS` | 17 cảnh báo | Người | Xác minh lớp gán có đúng không |
| `POSSIBLE_LOOSE_BOX` | 27 cảnh báo | Người | Xác minh box chưa khít |

Có **121 ảnh trong hàng đợi**, ngân sách mô phỏng **80/121 ảnh (66,12%)**. Hàng đợi ưu tiên theo điểm rủi ro: `NEEDS_LABEL` có trọng số 10, `POSSIBLE_WRONG_CLASS` 3, `POSSIBLE_MISSING` và `POSSIBLE_FALSE_POS` 2. Theo `06_review_log.csv`, 80 ảnh được duyệt mang **88 lượt ghi nhận mã cảnh báo ngữ nghĩa** (`POSSIBLE_MISSING`: 51; `POSSIBLE_WRONG_CLASS`: 17; `POSSIBLE_FALSE_POS`: 12; `POSSIBLE_LOOSE_BOX`: 8). Đây là lượt mã gắn với ảnh được duyệt, **không phải số lỗi thật đã được xác minh riêng lẻ**.

## 3. Calibration (2 ngưỡng)

Calibration dùng **39 ảnh** có lỗi được chèn có chủ đích.

| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau) | Lý do/đánh đổi |
|---|---:|---:|---|---|
| `duplicates.phash_dist` | 2 | **16** | `DUP_IMAGE_NEAR`: P **1,00 → 1,00**; R **0,50 → 0,83** | F1 từ **0,67 → 0,91**; ngưỡng 20 làm kết quả phát hiện trùng suy giảm trên calib |
| `second_opinion.conf` | 0,25 | **0,60** | `POSSIBLE_WRONG_CLASS`: P **0,56 → 0,62**; R **0,83 → 0,83** | Tăng precision mà giữ recall của cảnh báo sai lớp |

Ở `conf = 0,60`, `POSSIBLE_MISSING` có **P = 0,57; R = 1,00**; nếu nâng lên 0,80 thì **P = 0,67; R = 0,75**, tức bỏ sót thêm nhãn. Với `POSSIBLE_LOOSE_BOX`, cả precision và recall ở ngưỡng 0,60 đều chỉ **0,20**.

**Calibration có thể đánh lừa:** 39 ảnh là mẫu nhỏ; precision 1,00 trên các cặp near-duplicate trong calib chưa bảo đảm không loại nhầm ảnh thật. Trong lô raw, `img_0011` bị đánh gần trùng `img_0008` (pHash 16), `img_0084` gần trùng `img_0074` (pHash 16). Cần mở trực quan các cặp này và kiểm tra 31 ảnh bị loại tại Intake trước khi phát hành.

## 4. Cửa chặn và điều pipeline KHÔNG bắt được

**Chạy bình thường (ngân sách 80):** `python -m pipeline.run` cho kết luận **HOLD** vì còn **34/193 ảnh (17,62%)** chưa duyệt có cảnh báo, vượt ngưỡng 10%; số lỗi bắt buộc sau vòng cuối là **0**. Pipeline xuất bản nháp để so sánh train, không phải bản RELEASE.

**Chạy không có người duyệt:**

```bash
python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb
```

Kết quả thực nghiệm: nhận **193/224 ảnh**; AutoFix **35 thay đổi**; sau AutoFix vẫn còn **6 lỗi bắt buộc**; ngân sách review **0 ảnh**; Gate trả về **REWORK** và **không xuất dataset**. Theo tài liệu, mã thoát quy ước của REWORK là **20**; lần ghi log này chưa lưu trực tiếp `$LASTEXITCODE` để đối chiếu mã thoát.

**Điểm mù có bằng chứng:** (1) `POSSIBLE_LOOSE_BOX` chỉ đạt **Recall 0,20** tại ngưỡng conf 0,60 trên calib, có thể bỏ sót box lệch. (2) `POSSIBLE_WRONG_CLASS` đạt **Recall 0,83**, tức còn **1/6** lỗi sai lớp chèn vào calib chưa được phát hiện. YOLO26l chỉ cung cấp *second opinion*, không thay người kiểm tra ngữ nghĩa.

## 5. Train: Raw vs Clean

Đã hoàn thành trên **Google Colab, GPU Tesla T4**. Thí nghiệm dùng cùng model **YOLO26n (`yolo26n.pt`)**, **20 epochs**, **batch 16**, **imgsz 640**, hai seed **0 và 1** cho mỗi biến thể (tổng **4 lượt train**). Raw có **224 ảnh train**, Clean **193 ảnh**; dùng chung **40 ảnh gold validation** và **100 ảnh test**.

| Biến thể | # ảnh train | # seed | mAP50 (TB ± độ lệch) | mAP50-95 (TB ± độ lệch) | Precision (TB ± độ lệch) | Recall (TB ± độ lệch) |
|---|---:|---:|---:|---:|---:|---:|
| Raw | 224 | 2 | **0,726 ± 0,000** | **0,512 ± 0,004** | **0,764 ± 0,061** | **0,649 ± 0,028** |
| Clean | 193 | 2 | **0,729 ± 0,002** | **0,500 ± 0,000** | **0,794 ± 0,028** | **0,619 ± 0,005** |

Theo `comparison.md`, chênh **mAP50 (Clean − Raw) = +0,004** theo số chưa làm tròn trong báo cáo tổng hợp (giá trị hiển thị 3 chữ số thập phân là 0,729 so với 0,726). Trong khi đó, **mAP50-95 giảm khoảng 0,012**, **recall giảm khoảng 0,030**. Chênh lệch mAP50 nhỏ và số seed chỉ bằng 2, nên **chưa đủ bằng chứng để kết luận Clean tốt hơn Raw ổn định**.

**AP50 theo lớp (trung bình hai seed):**

| Lớp | Raw | Clean | Clean − Raw |
|---|---:|---:|---:|
| Car | 0,7375 | 0,7530 | +0,0155 |
| Person | 0,8221 | 0,8277 | +0,0056 |
| Truck | 0,6485 | 0,6215 | −0,0270 |
| Bus | 0,6949 | 0,7153 | +0,0204 |

Clean tăng AP50 ở **3/4 lớp** nhưng giảm ở **Truck**. Hai giả thuyết cần kiểm: (1) Raw còn ảnh trùng, rò rỉ test và nhãn sai khiến đánh giá có nhiễu — đối chiếu danh sách Intake và những mẫu train bị loại; (2) Clean ít hơn 31 ảnh và vẫn có 34 ảnh cảnh báo chưa duyệt, có thể làm giảm đa dạng hay ảnh hưởng phân bố lớp — đối chiếu số box/lớp và xem dự đoán sai trên test. Tập test chỉ **100 ảnh** cũng tạo bất định; nên đánh giá thêm seed và kiểm tra từng lớp trước khi kết luận.

## 6. Quyết định và ghi chú AI

**Quyết định cuối: HOLD, chưa phát hành Clean v1.** Để RELEASE cần xác minh các ảnh bị loại nhầm, xử lý/duyệt **34 ảnh còn cảnh báo chưa duyệt**, bảo đảm không còn lỗi bắt buộc và chạy lại Gate để tỷ lệ ảnh có cảnh báo chưa duyệt **dưới 10%**. Kết quả train chỉ hỗ trợ đánh giá, không thay thế quyết định QC.

**Ghi chú AI (3 dòng):**

- **Prompt chính:** Nhờ AI hỗ trợ hiện thực bốn module `label_format`, `gate`, `autofix`, `second_opinion` theo giao diện và test có sẵn.
- **Cách kiểm:** Chạy `python -m pytest -q` (**79/79 PASS**), calibration trên 39 ảnh, pipeline hai ngân sách review (80 và 0), rồi train Raw/Clean 2 seed và đối chiếu báo cáo.
- **Một lần AI sai:** AI nhận định nhầm nguyên nhân lỗi cảnh báo `pipeline/calibrate.py` của checker; sau khi đối chiếu Git và `_protected.json`, xác nhận đây là file gốc được bảo vệ, không sửa module đó để né kiểm tra.

"""Đối chiếu dự đoán của model với nhãn; chỉ phát cảnh báo để người kiểm."""
from ..common import WARN, Issue, iou_xywh, parse_yolo_line
from ..model_cache import get_preds


def run(ds, cfg, preds=None):
    if preds is None:
        preds = get_preds(ds, cfg, "checker")
    params = cfg["second_opinion"]
    issues = []
    for image in ds.image_files():
        stem = image.stem
        if stem not in preds or ds.read_label_lines(stem) is None:
            continue
        size = ds.image_size(stem)
        if size is None:
            continue
        labels = []
        for line, raw in ds.read_label_lines(stem):
            try:
                box = parse_yolo_line(raw)
            except (ValueError, OverflowError):
                continue
            if 0 <= box[0] < len(ds.classes) and box[3] > 0 and box[4] > 0:
                labels.append((line, box))
        predictions = preds[stem]
        for pred in predictions:
            cls, confidence, *coords = pred
            if confidence < params["conf"] or coords[2]*size[0]*coords[3]*size[1] < params["min_area_px"]:
                continue
            matches = [(iou_xywh(coords, box[1:]), box[0]) for _, box in labels]
            matches = [(iou, label_cls) for iou, label_cls in matches if iou >= params["iou_missing"]]
            if not matches:
                code, extra = "POSSIBLE_MISSING", {"conf": confidence}
            else:
                same = [iou for iou, label_cls in matches if label_cls == cls]
                if same:
                    best = max(same)
                    if best >= params["iou_loose"]:
                        continue
                    code, extra = "POSSIBLE_LOOSE_BOX", {"conf": confidence, "iou": best}
                elif max(iou for iou, _ in matches) >= params["iou_match"]:
                    code, extra = "POSSIBLE_WRONG_CLASS", {"conf": confidence, "iou": max(iou for iou, _ in matches)}
                else:
                    continue
            issues.append(Issue("second_opinion", WARN, code, stem, f"Model gợi ý kiểm tra {code}", extra=extra))
        fp_preds = [p for p in predictions if p[1] >= params["fp_conf"]]
        for line, label in labels:
            if not any(iou_xywh(label[1:], p[2:]) >= params["iou_missing"] for p in fp_preds):
                issues.append(Issue("second_opinion", WARN, "POSSIBLE_FALSE_POS", stem, "Box nhãn không khớp dự đoán", line=line))
    return issues

"""Check cú pháp nhãn YOLO, hình học và box trùng trong mỗi ảnh."""
from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line


def run(ds, cfg):
    settings = cfg["label_format"]
    issues = []
    for image in ds.image_files():
        stem = image.stem
        size = ds.image_size(stem)
        seen = []
        for line_no, raw in ds.read_label_lines(stem) or []:
            try:
                cls, x, y, w, h = parse_yolo_line(raw)
            except (ValueError, OverflowError):
                issues.append(Issue("label_format", ERROR, "BAD_FORMAT", stem, "Dòng nhãn không có đúng 5 giá trị hợp lệ", line_no))
                continue
            if cls < 0 or cls >= len(ds.classes):
                issues.append(Issue("label_format", ERROR, "BAD_CLASS_ID", stem, f"ID lớp {cls} không hợp lệ", line_no))
                continue
            if w <= 0 or h <= 0:
                issues.append(Issue("label_format", ERROR, "BOX_ZERO", stem, "Chiều rộng hoặc cao không dương", line_no))
                continue
            coords = (x, y, w, h)
            overflow = max(0.0, -(x-w/2), -(y-h/2), x+w/2-1, y+h/2-1)
            if overflow > settings["overflow_tol"]:
                issues.append(Issue("label_format", ERROR, "BOX_OUT_OF_IMAGE", stem, "Box tràn biên ảnh", line_no, {"overflow": overflow}))
            if any(prev_cls == cls and iou_xywh(coords, prev_box) > settings["dup_box_iou"] for prev_cls, prev_box in seen):
                issues.append(Issue("label_format", ERROR, "DUP_BOX", stem, "Box trùng với dòng trước cùng lớp", line_no))
            seen.append((cls, coords))
            if size and min(w*size[0], h*size[1]) < settings["min_box_px"]:
                issues.append(Issue("label_format", WARN, "BOX_TINY", stem, "Box quá nhỏ", line_no))
            if w*h > settings["max_box_frac"]:
                issues.append(Issue("label_format", WARN, "BOX_HUGE", stem, "Box quá lớn", line_no))
    return issues

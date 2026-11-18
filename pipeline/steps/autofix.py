"""Sửa an toàn trên bản dataset làm việc, giữ lại dấu vết trước/sau."""
from collections import defaultdict
import yaml
from ..common import ERROR, parse_yolo_line

DROP = {"BAD_FORMAT", "BAD_CLASS_ID", "BOX_ZERO", "DUP_BOX"}
REMOVE = {"DUP_IMAGE_EXACT", "DUP_IMAGE_NEAR", "LEAK_TEST", "CORRUPT_IMAGE", "BAD_SIZE"}


def _clip(text):
    cls, x, y, w, h = parse_yolo_line(text)
    x1, y1 = max(0.0, x-w/2), max(0.0, y-h/2)
    x2, y2 = min(1.0, x+w/2), min(1.0, y+h/2)
    if x2 <= x1 or y2 <= y1:
        return None
    return f"{cls} {(x1+x2)/2:.8f} {(y1+y2)/2:.8f} {x2-x1:.8f} {y2-y1:.8f}"


def fix(ds, issues, cfg):
    changes = []
    errors = [i for i in issues if i.severity == ERROR]
    removed = set()
    # Xử lý ảnh trước để các issue cùng ảnh đã xoá không còn tác dụng.
    for issue in errors:
        stem = issue.image
        if issue.code not in REMOVE or stem in removed:
            continue
        image = ds.image_path(stem)
        if image is None:
            continue
        image.unlink()
        label = ds.label_path(stem)
        if label.exists():
            label.unlink()
        ds._size_cache.pop(stem, None)
        removed.add(stem)
        changes.append(dict(image=stem, line=issue.line, action="remove_image", before=image.name, after="(đã xoá)"))
    grouped = defaultdict(lambda: defaultdict(set))
    for issue in errors:
        if issue.image in removed:
            continue
        if issue.code in DROP | {"BOX_OUT_OF_IMAGE"} and issue.line is not None:
            grouped[issue.image][issue.line].add(issue.code)
    for stem in sorted(grouped):
        p = ds.label_path(stem)
        if not p.exists() or ds.image_path(stem) is None:
            continue
        original = p.read_text(encoding="utf-8").splitlines(keepends=True)
        output = []
        for no, raw in enumerate(original, 1):
            codes = grouped[stem].get(no, set())
            if not codes:
                output.append(raw)
                continue
            before = raw.rstrip("\r\n")
            if codes & DROP:
                changes.append(dict(image=stem, line=no, action="drop_line", before=before, after="(đã xoá)"))
                continue
            try:
                clipped = _clip(before)
            except (ValueError, OverflowError):
                clipped = None
            if clipped is None:
                changes.append(dict(image=stem, line=no, action="drop_line", before=before, after="(đã xoá)"))
            elif clipped != before:
                output.append(clipped + ("\n" if raw.endswith("\n") else ""))
                changes.append(dict(image=stem, line=no, action="clip_box", before=before, after=clipped))
            else:
                output.append(raw)
        if output != original:
            p.write_text("".join(output), encoding="utf-8")
    if any(i.code == "BAD_CLASS_NAME" for i in errors):
        p = ds.yaml_path
        if p.exists():
            data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            target = {i: name for i, name in enumerate(cfg["classes"])}
            if ds.yaml_names() != target:
                before = str(data.get("names"))
                data["names"] = target
                p.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
                changes.append(dict(image="data.yaml", line=None, action="rename_classes", before=before, after=str(target)))
    for issue in errors:
        if issue.code == "MISSING_LABEL_FILE" and issue.image not in removed and ds.image_path(issue.image) is not None and not ds.label_path(issue.image).exists():
            changes.append(dict(image=issue.image, line=None, action="needs_label", before="(không có file)", after="chuyển người gán"))
    return changes

"""Cửa chặn chất lượng: lỗi bắt buộc thắng mọi quyết định duyệt."""
from ..common import ERROR, WARN


def decide(issues, image_stems, cfg, reviewed=frozenset()):
    stems = set(image_stems)
    reviewed = set(reviewed)
    errors = sum(issue.severity == ERROR for issue in issues)
    warned = {issue.image for issue in issues if issue.severity == WARN and issue.image in stems and issue.image not in reviewed}
    count = len(stems)
    ratio = len(warned) / count if count else 0.0
    threshold = cfg["gate"]["warn_ratio_hold"]
    if errors:
        decision = "Rework"
        reasons = [f"Còn {errors} lỗi bắt buộc; cần sửa trước khi phát hành."]
    elif ratio >= threshold:
        decision = "Hold"
        reasons = [f"Còn {len(warned)}/{count} ảnh có cảnh báo chưa duyệt ({ratio:.2%}), đạt/vượt ngưỡng {threshold:.2%}."]
    else:
        decision = "Release"
        reasons = [f"Không còn lỗi bắt buộc; cảnh báo chưa duyệt {len(warned)}/{count} ảnh ({ratio:.2%}), dưới ngưỡng {threshold:.2%}."]
    return dict(decision=decision, n_errors=errors, n_warn_images=len(warned), n_images=count,
                warn_ratio=round(ratio, 4), reasons=reasons)

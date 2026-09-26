"""
Shared frame-resizing core for the Conform nodes. Both the IMAGE-batch
version (conform_resolution.py) and the native-VIDEO version
(conform_video_resolution.py) call into this module, so "Cover" / "Contain"
/ "Stretch" behave identically no matter which one you use — one piece of
math backing both nodes, not two copies that can quietly drift apart.
"""

import torch
import torch.nn.functional as F


FIT_MODES = ["Cover (scale + center crop)", "Contain (scale + pad)", "Stretch"]

INTERPOLATION_MODES = {
    "lanczos": "bicubic",  # torch has no native lanczos; bicubic is the closest supported mode
    "bicubic": "bicubic",
    "bilinear": "bilinear",
    "nearest": "nearest-exact",
}


def _resize(img_bhwc: torch.Tensor, w: int, h: int, mode: str) -> torch.Tensor:
    # img_bhwc: (B, H, W, C) float 0..1  ->  torch wants (B, C, H, W)
    x = img_bhwc.permute(0, 3, 1, 2)
    kwargs = {}
    if mode in ("bicubic", "bilinear"):
        kwargs["align_corners"] = False
    x = F.interpolate(x, size=(h, w), mode=mode, **kwargs)
    return x.permute(0, 2, 3, 1).clamp(0, 1)


def _cover(img, target_w, target_h, interp):
    b, h, w, c = img.shape
    scale = max(target_w / w, target_h / h)
    new_w, new_h = round(w * scale), round(h * scale)
    resized = _resize(img, new_w, new_h, interp)

    top = (new_h - target_h) // 2
    left = (new_w - target_w) // 2
    return resized[:, top:top + target_h, left:left + target_w, :]


def _contain(img, target_w, target_h, interp, pad_color):
    b, h, w, c = img.shape
    scale = min(target_w / w, target_h / h)
    new_w, new_h = round(w * scale), round(h * scale)
    resized = _resize(img, new_w, new_h, interp)

    canvas = torch.zeros((b, target_h, target_w, c), dtype=img.dtype, device=img.device)
    canvas[..., 0] = pad_color[0]
    canvas[..., 1] = pad_color[1]
    if c > 2:
        canvas[..., 2] = pad_color[2]

    top = (target_h - new_h) // 2
    left = (target_w - new_w) // 2
    canvas[:, top:top + new_h, left:left + new_w, :] = resized
    return canvas


def _stretch(img, target_w, target_h, interp):
    return _resize(img, target_w, target_h, interp)


def hex_to_rgb01(pad_color_hex):
    hexv = pad_color_hex.lstrip("#")
    if len(hexv) >= 6:
        return tuple(int(hexv[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return (0.0, 0.0, 0.0)


def conform_frames(images, target_width, target_height, fit_mode, interpolation, pad_color_hex="#000000"):
    """Shared entry point: takes a (B, H, W, C) float 0..1 tensor, returns
    (resized_tensor, report_string). Used by both conform nodes."""
    b, h, w, c = images.shape
    interp = INTERPOLATION_MODES[interpolation]

    if w == target_width and h == target_height:
        return images, f"Already {w}x{h}, no change needed."

    if fit_mode.startswith("Cover"):
        out = _cover(images, target_width, target_height, interp)
    elif fit_mode.startswith("Contain"):
        rgb = hex_to_rgb01(pad_color_hex)
        out = _contain(images, target_width, target_height, interp, rgb)
    else:
        out = _stretch(images, target_width, target_height, interp)

    report = f"{w}x{h} -> {target_width}x{target_height} ({fit_mode}, {interpolation})"
    return out, report

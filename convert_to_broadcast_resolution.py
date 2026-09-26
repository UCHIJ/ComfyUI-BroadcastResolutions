"""
@author: UCHIJ
@title: Convert to Broadcast Resolution
@nickname: Video Profile Selector
@description: Outputs a broadcast/cinema standard resolution. If `multiple`
              is set (8/16/32/64), width/height are snapped UP to that
              divisor so the output can feed a generation model directly
              (0 = off). `cinema_delivery`, when set to anything other than
              "None", overrides `resolution`/`aspect_ratio` entirely with a
              fixed DCI delivery container size.
"""

import json
import math
from pathlib import Path

# Inline fallback — an exact copy of broadcast_profiles.json's contents.
# Used only if the JSON file can't be found on disk. This guarantees the
# extension can never fail to load (and take BOTH nodes down with it, since
# __init__.py imports this module unconditionally) just because the JSON
# file ended up in a different folder than expected on someone's install.
_FALLBACK_PROFILE_DATA = {
    "resolutions": {
        "SD NTSC":  [720, 480],
        "SD PAL":   [720, 576],
        "HD 720p":  [1280, 720],
        "HD 1080p": [1920, 1080],
        "UHD 4K":   [3840, 2160],
        "5K UHD":   [5120, 2880],
        "UHD 8K":   [7680, 4320],
    },
    "aspect_ratios": {
        "16:9  Widescreen (YouTube)":               [16, 9],
        "9:16  Vertical (Reels / TikTok / Shorts)": [9, 16],
        "1:1   Square (Instagram / Universal)":     [1, 1],
        "4:3   Standard (legacy TV)":                [4, 3],
        "3:4   Vertical (legacy photo/grid)":        [3, 4],
        "4:5   Instagram Feed Portrait":             [4, 5],
        "Flat (1.85:1 cinema widescreen)":           [1.85, 1],
        "Scope (2.39:1 cinema widescreen)":          [2.39, 1],
    },
    "cinema_delivery": {
        "None": None,
        "DCI 2K Flat \u2014 1998\u00d71080":  [1998, 1080],
        "DCI 4K Flat \u2014 3996\u00d72160":  [3996, 2160],
        "DCI 2K Scope \u2014 2048\u00d7858":  [2048, 858],
        "DCI 4K Scope \u2014 4096\u00d71716": [4096, 1716],
    },
}

# Checked in order. Covers both "JSON sits next to the .py files" and
# "JSON sits inside the web/ folder" layouts, so this never depends on one
# exact install arrangement.
_CANDIDATE_PATHS = [
    Path(__file__).parent / "broadcast_profiles.json",
    Path(__file__).parent / "web" / "broadcast_profiles.json",
]

_PROFILE_DATA = None
for _candidate in _CANDIDATE_PATHS:
    try:
        with open(_candidate, "r", encoding="utf-8") as _f:
            _PROFILE_DATA = json.load(_f)
        break
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        continue

if _PROFILE_DATA is None:
    print(
        "[Broadcast Video Profile] broadcast_profiles.json not found in any "
        "expected location — using built-in defaults. Node will still work; "
        "check that broadcast_profiles.json ships alongside the .py files "
        "or inside web/."
    )
    _PROFILE_DATA = _FALLBACK_PROFILE_DATA

RESOLUTIONS = {k: tuple(v) for k, v in _PROFILE_DATA["resolutions"].items()}
ASPECT_RATIOS = {k: tuple(v) for k, v in _PROFILE_DATA["aspect_ratios"].items()}
CINEMA_DELIVERY = {
    k: (tuple(v) if v is not None else None)
    for k, v in _PROFILE_DATA["cinema_delivery"].items()
}

# Stores true broadcast target for conform_to_broadcast_resolution.py
BROADCAST_CACHE = {
    "width": 1920,
    "height": 1080,
    "snapped_w": 1920,
    "snapped_h": 1080,
}


def _round_even(value):
    rounded = round(value)
    if rounded % 2 != 0:
        rounded += 1
    return rounded


def _snap_to_multiple(value, multiple):
    # Always rounds UP, never down. A model fed fewer pixels than it
    # expects will error, so this has no "round down" branch.
    if multiple <= 1:
        return value
    snapped = math.ceil(value / multiple) * multiple
    return max(multiple, snapped)


def compute_dims(resolution, aspect_key):
    native_w, native_h = RESOLUTIONS[resolution]
    ratio_w, ratio_h = ASPECT_RATIOS[aspect_key]

    if ratio_w >= ratio_h:
        height = native_h
        width = _round_even(height * (ratio_w / ratio_h))
    else:
        width = native_h
        height = _round_even(width * (ratio_h / ratio_w))
    return width, height


class ConvertToBroadcastResolution:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "resolution": (list(RESOLUTIONS.keys()), {
                    "default": "HD 1080p"
                }),
                "aspect_ratio": (list(ASPECT_RATIOS.keys()), {
                    "default": "16:9  Widescreen (YouTube)"
                }),
                "cinema_delivery": (list(CINEMA_DELIVERY.keys()), {
                    "default": "None",
                    "tooltip": "Overrides resolution/aspect_ratio with a fixed DCI delivery container size"
                }),
                "multiple": ("INT", {
                    "default": 32, "min": 0, "max": 128, "step": 8,
                    "tooltip": "Snap dimensions UP to nearest multiple for generator nodes (0 = off)"
                }),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "select_resolution"
    CATEGORY = "Broadcast Video Profile"

    def select_resolution(self, resolution, aspect_ratio, cinema_delivery, multiple):
        cinema_dims = CINEMA_DELIVERY.get(cinema_delivery)

        if cinema_dims is not None:
            # 1a. Fixed DCI delivery container: bypass the ladder entirely.
            target_w, target_h = cinema_dims
        else:
            # 1b. Compute true target broadcast dimensions from the ladder.
            target_w, target_h = compute_dims(resolution, aspect_ratio)

        # 2. Snap UP for the generator node's model-facing output.
        snapped_w = _snap_to_multiple(target_w, multiple)
        snapped_h = _snap_to_multiple(target_h, multiple)

        # 3. Cache TRUE broadcast target for the Conform node.
        BROADCAST_CACHE["width"] = target_w
        BROADCAST_CACHE["height"] = target_h
        BROADCAST_CACHE["snapped_w"] = snapped_w
        BROADCAST_CACHE["snapped_h"] = snapped_h
        BROADCAST_CACHE["resolution_name"] = (
            cinema_delivery if cinema_dims is not None else resolution
        )

        return (snapped_w, snapped_h)


NODE_CLASS_MAPPINGS = {
    "ConvertToBroadcastResolution": ConvertToBroadcastResolution
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ConvertToBroadcastResolution": "Broadcast Resolution (input)"
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY", "BROADCAST_CACHE"]
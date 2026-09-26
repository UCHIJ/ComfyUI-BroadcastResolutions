"""
ComfyUI-BroadcastResolutions
Author: UCHIJ

A clean 2-node extension for post-production creators to deliver AI video
and images at guaranteed broadcast and social platform standards (1080p, 4K, 9:16, 4:5, etc.).

  - Input Broadcast Resolution: Computes true broadcast standards while snapping 
    output dimensions up to model-safe multiples (8/16/32/64) for samplers (LTX, MiniMax, Hunyuan).
  - Output Broadcast Resolution: Wireless conform node that automatically crops/scales 
    the generated video back to the true broadcast standard before saving.
"""

from .convert_to_broadcast_resolution import (
    NODE_CLASS_MAPPINGS as _BROADCAST_CLASSES,
    NODE_DISPLAY_NAME_MAPPINGS as _BROADCAST_NAMES,
)
from .conform_to_broadcast_resolution import (
    NODE_CLASS_MAPPINGS as _CONFORM_CLASSES,
    NODE_DISPLAY_NAME_MAPPINGS as _CONFORM_NAMES,
)

NODE_CLASS_MAPPINGS = {
    **_BROADCAST_CLASSES,
    **_CONFORM_CLASSES,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **_BROADCAST_NAMES,
    **_CONFORM_NAMES,
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
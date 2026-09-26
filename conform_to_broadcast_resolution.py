"""
@author: UCHIJ
@title: Conform Video to Resolution
@nickname: Video Profile Selector
@description: Native VIDEO standardizer. Automatically scales incoming
              VIDEO to whatever Input Broadcast Resolution last computed
              (shared via BROADCAST_CACHE) using Cover, Contain, or Stretch,
              preserving audio and frame rate. No wiring required — the two
              nodes stay in sync automatically.
"""

from ._resize_core import FIT_MODES, INTERPOLATION_MODES, conform_frames

try:
    from comfy_api.input_impl import VideoFromComponents
    from comfy_api.latest import VideoComponents
    _VIDEO_API_AVAILABLE = True
except ImportError:
    _VIDEO_API_AVAILABLE = False


class ConformVideoToResolution:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("VIDEO",),
                "fit_mode": (FIT_MODES, {"default": "Cover (scale + center crop)"}),
                "interpolation": (list(INTERPOLATION_MODES.keys()), {"default": "lanczos"}),
            },
            "optional": {
                "pad_color_hex": ("STRING", {"default": "#000000"}),
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    FUNCTION = "conform_video"
    CATEGORY = "Broadcast Video Profile"

    def conform_video(self, video, fit_mode, interpolation, pad_color_hex="#000000"):
        if not _VIDEO_API_AVAILABLE:
            raise RuntimeError(
                "Conform Video to Resolution requires a ComfyUI version with the "
                "native VIDEO type (comfy_api.input_impl.VideoFromComponents). "
                "Update ComfyUI to use this node."
            )

        from .convert_to_broadcast_resolution import BROADCAST_CACHE
        target_width = BROADCAST_CACHE.get("width", 1920)
        target_height = BROADCAST_CACHE.get("height", 1080)

        components = video.get_components()
        resized_images, _ = conform_frames(
            components.images, target_width, target_height, fit_mode, interpolation, pad_color_hex
        )

        try:
            bit_depth = video.get_bit_depth()
        except AttributeError:
            bit_depth = 8

        new_components = VideoComponents(
            images=resized_images,
            audio=components.audio,
            frame_rate=components.frame_rate,
        )
        out_video = VideoFromComponents(new_components, bit_depth=bit_depth)
        return (out_video,)


NODE_CLASS_MAPPINGS = {
    "ConformVideoToResolution": ConformVideoToResolution,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ConformVideoToResolution": "Broadcast Resolution (output)",
}

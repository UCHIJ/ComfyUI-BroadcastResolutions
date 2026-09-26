# Broadcast Resolutions for ComfyUI

A drop-in custom node suite built for video editors, motion designers, and creators to force AI-generated video onto **real broadcast and social delivery standards** without manual dimension math or messy canvas wires.

## The Problem

Video diffusion models (LTX, MiniMax, Hunyuan, CogVideo) require latent tensor dimensions divisible by 8, 16, 32, or 64. Because pure broadcast resolutions like 1080p ($1920 \times 1080$) aren't always divisible by model requirements, samplers often crash or output odd frame sizes. 

This node suite solves that seamlessly in two steps:
1. **Input Stage:** Computes your target broadcast standard, snaps dimensions *up* to the nearest model-safe multiple so the sampler never crashes, and passes the true target down the pipeline wirelessly.
2. **Delivery Stage:** Automatically crops, letterboxes, or scales the output video back to the exact broadcast standard right before export.

---

## Workflow Pipeline

[Input Broadcast Resolution] (multiple=32)
│
├─► width / height ─► [Empty Latent / Generator Model] ─► Sampler
│                                                              │
│ (wireless sync)                                              ▼
└─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─► [Output Broadcast Resolution] ─► Save Video

---

## Nodes

### 1. Input Broadcast Resolution (`ConvertToBroadcastResolution`)

Selects your target delivery profile and outputs model-safe dimensions for your generator.

| Parameter | Type | Description |
| --- | --- | --- |
| `resolution` | Dropdown | Delivery standards (`HD 1080p`, `UHD 4K`, `SD NTSC`, `2K DCI`, etc.). |
| `aspect_ratio` | Dropdown | Target aspect ratio (`16:9`, `9:16`, `4:5 Instagram`, `1:1 Square`, `2.39:1 CinemaScope`). |
| `multiple` | Integer | Model divisor snapping (`32` for LTX/MiniMax, `16`, `64`, or `0` for off). |
| `input_width` / `input_height` | Optional Inputs | Connect upstream generation nodes to auto-match standard aspect ratios live. |

**Outputs:** `width`, `height` (INT) — model-safe snapped dimensions ready to plug into latent or generator nodes.

---

### 2. Output Broadcast Resolution (`ConformVideoToResolution`)

Native VIDEO standardizer. Automatically syncs with the input profile wirelessly—no target width/height wiring needed.

| Parameter | Type | Description |
| --- | --- | --- |
| `video` | VIDEO | Incoming native VIDEO stream from your sampler/decoder. |
| `fit_mode` | Dropdown | `Cover (scale + center crop)`, `Contain (scale + pad)`, or `Stretch`. |
| `interpolation` | Dropdown | `lanczos`, `bicubic`, `bilinear`, `nearest`. |
| `pad_color_hex` | String | Hex color code used when `Contain` mode adds letterboxing/pillarboxing (default `#000000`). |

**Outputs:** `video` (VIDEO) — scaled and cropped to the exact broadcast standard.

---

## Installation

1. Clone or copy this repository into your `ComfyUI/custom_nodes/` directory:
   ```bash
   cd ComfyUI/custom_nodes/
   git clone [https://github.com/UCHIJ/ComfyUI-BroadcastResolutions.git](https://github.com/your-username/ComfyUI-BroadcastResolutions.git)

3. Restart ComfyUI.

4. Find the nodes under the Broadcast Video Profile category.

## Credits

Built by UCHIJP

## License

MIT — see [LICENSE] for details.



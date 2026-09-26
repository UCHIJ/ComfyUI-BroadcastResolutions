
# Broadcast Resolutions for ComfyUI

A drop-in custom node suite built for video editors, motion designers, and creators. Generating video with modern AI models shouldn’t require advanced math just to produce a standard frame. Rigid requirements for pixel alignment and megapixel limits can lead to broken latents, CUDA crashes, and unexpected output sizes.

This node pack handles the resolution math automatically, letting you generate clean 4K, 1080p, 720p, and SD video using familiar formats—without worrying about tensor dimensions or sampler errors.

Why It Happens:
Modern video diffusion models (LTX, MiniMax, Hunyuan, CogVideo) require frame dimensions strictly divisible by 8, 16, 32, or 64. Because native delivery standards like 1080p or DCI Flat violate these strict macroblock rules, standard samplers either crash outright or output off-spec pixel bounds.

---

**This node suite solves that seamlessly in two steps:**

<img width="1488" height="400" alt="broadcast-pullout" src="https://github.com/user-attachments/assets/09aac70a-1cc2-4a84-867c-c2aa8341b646" />

1. **Input Stage (`Broadcast Resolution (input)`):** Computes your true target broadcast or DCI standard, snaps dimensions *up* to the nearest model-safe multiple so the sampler never crashes, and passes the true target down the pipeline wirelessly.

2. **Delivery Stage (`Broadcast Resolution (output)`):** Automatically crops, letterboxes, or scales the output video back to the exact target standard right before export.

---

## Workflow Pipeline

```text
[Broadcast Resolution (input)] (multiple=32)
│
├─► width / height ─► [Empty Latent / Generator Model] ─► Sampler
│                                                              │
│ (wireless sync)                                              ▼
└─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─► [Broadcast Resolution (output)] ─► Save Video

```
---

<img width="1919" height="903" alt="broadcast-workflow" src="https://github.com/user-attachments/assets/c12120e9-143c-4d4e-bfb9-a9e41e660031" />




## Nodes

### 1. Broadcast Resolution (input) (`ConvertToBroadcastResolution`)

Selects your target delivery profile and outputs model-safe dimensions for your generator nodes.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `resolution` | Dropdown | `HD 1080p` | Delivery standards (`HD 1080p`, `UHD 4K`, `SD NTSC`, `5K UHD`, `UHD 8K`, etc.). |
| `aspect_ratio` | Dropdown | `16:9 Widescreen (YouTube)` | Target aspect ratio (`16:9`, `9:16`, `1:1 Square`, `4:5 Portrait`, `Flat 1.85:1`, `Scope 2.39:1`). |
| `cinema_delivery` | Dropdown | `None` | Fixed DCI delivery container size (`DCI 2K Flat`, `DCI 4K Flat`, `DCI 2K Scope`, `DCI 4K Scope`). When selected, **overrides** `resolution` and `aspect_ratio`. |
| `multiple` | Integer | `32` | Model divisor snapping (`32` for LTX/MiniMax, `16`, `64`, or `0` for off). Always rounds **UP** to avoid generator out-of-bounds errors. |

**Outputs:**

* `width` (INT) — Model-facing snapped width.
* `height` (INT) — Model-facing snapped height.

---

### 2. Broadcast Resolution (output) (`ConformVideoToResolution`)

Native VIDEO standardizer. Automatically syncs with the input profile wirelessly in real time—no target width or height wiring required.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `video` | VIDEO | *Required* | Incoming native VIDEO stream from your sampler or video decoder. |
| `fit_mode` | Dropdown | `Cover (scale + center crop)` | Canvas framing strategy: `Cover (scale + center crop)`, `Contain (scale + pad)`, or `Stretch`. |
| `interpolation` | Dropdown | `lanczos` | Resampling algorithm (`lanczos`, `bicubic`, `bilinear`, `nearest`). |
| `pad_color_hex` | String | `#000000` | Hex color code used when `Contain` mode adds letterboxing or pillarboxing. |

**Outputs:**

* `video` (VIDEO) — Scaled and framed native video stream matching the true target broadcast resolution.

---

## Configuration (`broadcast_profiles.json`)

Resolution presets, aspect ratios, and cinema container sizes are managed via `broadcast_profiles.json`. You can customize or add your own standards directly in this file without modifying Python or JavaScript code.

---

## Installation

1. Clone or copy this repository into your `ComfyUI/custom_nodes/` directory:
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/UCHIJ/ComfyUI-BroadcastResolutions.git

```

2. Restart ComfyUI.
3. Find the nodes under the `Broadcast Video Profile` category.

---

## Credits

Built by, UCHIJ

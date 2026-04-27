"""AI super-resolution using Real-ESRGAN (2x upscale).

Implements the RRDBNet architecture from scratch (no basicsr dependency)
and loads the official Real-ESRGAN x2plus pretrained weights. This produces
Magnific.AI-style detail enhancement: the upscale-then-downsample process
adds genuine high-frequency detail that persists at the final resolution.
"""

import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from pathlib import Path
from PIL import Image


# ── RRDBNet Architecture ──────────────────────────────────────────────


class _ResidualDenseBlock(nn.Module):
    def __init__(self, num_feat=64, num_grow_ch=32):
        super().__init__()
        self.conv1 = nn.Conv2d(num_feat, num_grow_ch, 3, 1, 1)
        self.conv2 = nn.Conv2d(num_feat + num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv3 = nn.Conv2d(num_feat + 2 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv4 = nn.Conv2d(num_feat + 3 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv5 = nn.Conv2d(num_feat + 4 * num_grow_ch, num_feat, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x


class _RRDB(nn.Module):
    def __init__(self, num_feat, num_grow_ch=32):
        super().__init__()
        self.rdb1 = _ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb2 = _ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb3 = _ResidualDenseBlock(num_feat, num_grow_ch)

    def forward(self, x):
        out = self.rdb1(x)
        out = self.rdb2(out)
        out = self.rdb3(out)
        return out * 0.2 + x


class RRDBNet(nn.Module):
    def __init__(self, num_in_ch=3, num_out_ch=3, scale=4,
                 num_feat=64, num_block=23, num_grow_ch=32):
        super().__init__()
        self.scale = scale
        # x2 model uses pixel-unshuffle: 3ch → 12ch, then 4x internal upscale
        if scale == 2:
            num_in_ch = num_in_ch * 4
        self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        self.body = nn.Sequential(
            *[_RRDB(num_feat, num_grow_ch) for _ in range(num_block)]
        )
        self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_up1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_up2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_hr = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x):
        if self.scale == 2:
            feat = F.pixel_unshuffle(x, 2)
        else:
            feat = x
        feat = self.conv_first(feat)
        body_feat = self.conv_body(self.body(feat))
        feat = feat + body_feat
        feat = self.lrelu(
            self.conv_up1(F.interpolate(feat, scale_factor=2, mode="nearest"))
        )
        feat = self.lrelu(
            self.conv_up2(F.interpolate(feat, scale_factor=2, mode="nearest"))
        )
        return self.conv_last(self.lrelu(self.conv_hr(feat)))


# ── Model loading & caching ──────────────────────────────────────────

_MODEL_DIR = Path(__file__).parent.parent / "models"
_MODEL_URL = (
    "https://github.com/xinntao/Real-ESRGAN/releases/download/"
    "v0.2.1/RealESRGAN_x2plus.pth"
)
_MODEL_FILE = "RealESRGAN_x2plus.pth"
_model_cache = None


def _download_model() -> Path:
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    path = _MODEL_DIR / _MODEL_FILE
    if path.exists():
        return path

    import urllib.request

    print(f"[upscale] Downloading Real-ESRGAN x2plus model ({_MODEL_FILE})...")
    urllib.request.urlretrieve(_MODEL_URL, str(path))
    print("[upscale] Download complete.")
    return path


def _get_model() -> RRDBNet:
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    model_path = _download_model()
    model = RRDBNet(
        num_in_ch=3, num_out_ch=3, scale=2,  # scale=2 triggers pixel-unshuffle path
        num_feat=64, num_block=23, num_grow_ch=32,
    )

    loadnet = torch.load(str(model_path), map_location="cpu", weights_only=False)
    state = loadnet.get("params_ema", loadnet.get("params", loadnet))
    model.load_state_dict(state, strict=True)
    model.eval()
    _model_cache = model
    return _model_cache


# ── Tiled inference ──────────────────────────────────────────────────


def _tile_process(model, img_t, tile=400, pad=10, scale=2):
    _, _, h, w = img_t.shape
    out_h, out_w = h * scale, w * scale
    output = img_t.new_zeros((1, 3, out_h, out_w))

    # Ensure tile size is even (required by pixel_unshuffle)
    tile = tile - (tile % 2)
    pad = pad - (pad % 2)

    tiles_y = max(1, (h + tile - 1) // tile)
    tiles_x = max(1, (w + tile - 1) // tile)

    for iy in range(tiles_y):
        for ix in range(tiles_x):
            sx = ix * tile
            sy = iy * tile
            in_x0 = max(sx - pad, 0)
            in_y0 = max(sy - pad, 0)
            in_x1 = min(sx + tile + pad, w)
            in_y1 = min(sy + tile + pad, h)

            # Ensure even dimensions for pixel_unshuffle
            if (in_x1 - in_x0) % 2:
                in_x1 = min(in_x1 + 1, w)
            if (in_y1 - in_y0) % 2:
                in_y1 = min(in_y1 + 1, h)

            tile_in = img_t[:, :, in_y0:in_y1, in_x0:in_x1]
            with torch.no_grad():
                tile_out = model(tile_in)

            crop_y0 = (sy - in_y0) * scale
            crop_x0 = (sx - in_x0) * scale
            out_tile_h = min(tile, h - sy) * scale
            out_tile_w = min(tile, w - sx) * scale

            output[
                :, :,
                sy * scale: sy * scale + out_tile_h,
                sx * scale: sx * scale + out_tile_w,
            ] = tile_out[
                :, :,
                crop_y0: crop_y0 + out_tile_h,
                crop_x0: crop_x0 + out_tile_w,
            ]

    return output


# ── Public API ───────────────────────────────────────────────────────


def ai_upscale(bgr_image: np.ndarray) -> np.ndarray:
    """Upscale a BGR image 2x using Real-ESRGAN.

    Returns a BGR numpy array at 2x the input resolution with
    AI-generated detail (not just interpolation).
    """
    model = _get_model()
    h, w = bgr_image.shape[:2]

    # Pad to even dimensions (pixel_unshuffle requires divisibility by 2)
    pad_h = h % 2
    pad_w = w % 2
    if pad_h or pad_w:
        bgr_image = cv2.copyMakeBorder(
            bgr_image, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT_101
        )

    img = bgr_image[:, :, ::-1].astype(np.float32) / 255.0
    img_t = torch.from_numpy(np.transpose(img, (2, 0, 1))).unsqueeze(0)

    ph, pw = bgr_image.shape[:2]
    if max(ph, pw) > 600:
        out_t = _tile_process(model, img_t, tile=400, pad=10, scale=2)
    else:
        with torch.no_grad():
            out_t = model(img_t)

    out = out_t.squeeze(0).clamp(0, 1).cpu().numpy()
    out = np.transpose(out, (1, 2, 0))
    out = (out * 255.0).round().astype(np.uint8)
    result = out[:, :, ::-1].copy()

    # Remove padding from the 2x output
    if pad_h or pad_w:
        result = result[: h * 2, : w * 2]

    return result


def upscale_pil(pil_image: Image.Image, target_size: tuple[int, int] | None = None) -> Image.Image:
    """Upscale a PIL Image with Real-ESRGAN, then optionally resize.

    The upscale-then-downsample path adds genuine detail that persists
    even after resizing back — this is the Magnific.AI principle.
    """
    bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    upscaled_bgr = ai_upscale(bgr)
    upscaled_rgb = cv2.cvtColor(upscaled_bgr, cv2.COLOR_BGR2RGB)
    result = Image.fromarray(upscaled_rgb)

    if target_size:
        result = result.resize(target_size, Image.LANCZOS)

    return result

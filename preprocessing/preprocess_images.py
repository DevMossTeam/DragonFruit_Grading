#!/usr/bin/env python3
"""
preprocess_images.py — Enhanced adaptive tight-crop pipeline (fixed)

Perbaikan utama:
- Hindari shadowing nama fungsi dengan variabel lokal (mis. mask_otsu -> mask_otsu_img)
- Konsistensi penamaan variabel mask
- Menjaga seluruh fitur sebelumnya (autotune, review, debug, intermediates)

Author: Assistant (fixed)
Date: 2025-09
"""

from __future__ import annotations
import os
import sys
import time
import math
import json
import argparse
import logging
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
import cv2
from PIL import Image, ImageOps

# Optional libs
try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False

try:
    from tqdm import tqdm
except Exception:
    tqdm = None

# ----------------------------
# Logging setup
# ----------------------------
def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True
    )

# ----------------------------
# Utility helpers
# ----------------------------
def ensure_dir(path: str):
    """Create directory if it does not exist."""
    Path(path).mkdir(parents=True, exist_ok=True)

# ----------------------------
# Config dataclass
# ----------------------------
@dataclass
class CFG:
    raw_dir: str = "raw_data"
    out_dir: str = "dataset"
    target_size: Tuple[int, int] = (224, 224)  # (H, W)
    margin: float = 0.06                        # base margin fraction (6%)
    min_contour_area_fraction: float = 0.0008   # fraction of image area -> min contour area
    use_exif: bool = True
    use_clahe: bool = True
    clahe_clip: float = 2.0
    clahe_grid: Tuple[int,int] = (8,8)
    save_quality: int = 95
    debug: bool = False
    save_intermediates: bool = False
    force: bool = False
    verbose: bool = False
    autotune_samples: Optional[int] = None
    review_mode: bool = False
    review_save_path: str = "dataset_review"
    reject_folder_name: str = "rejects"
    sample_downscale: int = 4
    kmeans_clusters: int = 3
    hsv_ranges: Optional[List[Tuple[Tuple[int,int,int], Tuple[int,int,int]]]] = None
    timestamp_format: str = "%Y%m%d_%H%M%S"
    # thresholds
    crop_mask_coverage_threshold: float = 0.12  # fraction of pixels inside crop that must be mask>0
    margin_increment_steps: List[float] = (0.06, 0.10, 0.18)  # try increasing margin when validation fails
    max_attempts: int = 4

# ----------------------------
# Utility IO helpers (unicode-safe)
# ----------------------------
def imread_unicode(path: str) -> Optional[np.ndarray]:
    try:
        arr = np.fromfile(path, dtype=np.uint8)
        if arr.size == 0:
            return None
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return None
        return img
    except Exception as e:
        logging.debug("imread_unicode failed for %s: %s", path, e)
        return None

def imwrite_unicode(path: str, img: np.ndarray, quality: int = 95) -> bool:
    try:
        ext = Path(path).suffix.lower()
        if ext == "":
            path = str(path) + ".jpg"
            ext = ".jpg"
        if ext in (".jpg", ".jpeg"):
            ok, enc = cv2.imencode(ext, img, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        else:
            ok, enc = cv2.imencode(ext, img)
        if not ok:
            logging.error("imencode failed for %s", path)
            return False
        enc.tofile(path)
        return True
    except Exception as e:
        logging.exception("imwrite_unicode failed for %s: %s", path, e)
        return False

def load_image_exif(path: str, use_exif: bool = True) -> Optional[np.ndarray]:
    try:
        if use_exif:
            im = Image.open(path)
            im = ImageOps.exif_transpose(im)
            im = im.convert("RGB")
            arr = np.asarray(im)
            bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            return bgr
        else:
            return imread_unicode(path)
    except Exception:
        return imread_unicode(path)

# ----------------------------
# Color operations
# ----------------------------
def grey_world(bgr: np.ndarray) -> np.ndarray:
    img = bgr.astype(np.float32)
    means = img.mean(axis=(0,1))
    global_mean = means.mean()
    scales = np.where(means > 1e-6, global_mean / (means + 1e-8), 1.0)
    balanced = img * scales
    return np.clip(balanced, 0, 255).astype(np.uint8)

def apply_clahe(bgr: np.ndarray, clip: float, grid: Tuple[int,int]) -> np.ndarray:
    try:
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=grid)
        l2 = clahe.apply(l)
        lab2 = cv2.merge([l2, a, b])
        return cv2.cvtColor(lab2, cv2.COLOR_LAB2BGR)
    except Exception:
        return bgr

# ----------------------------
# Mask helpers
# ----------------------------
def mask_otsu_fn(bgr: np.ndarray) -> np.ndarray:
    # renamed function internally to avoid any chance of name conflict in local scopes
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5,5), 0)
    _, m = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if np.count_nonzero(m) < m.size/2:
        m = cv2.bitwise_not(m)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=2)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, kernel, iterations=1)
    return m

# Keep original function name for compatibility with earlier uses:
mask_otsu = mask_otsu_fn

def mask_edges(bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 60, 160)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    m = cv2.dilate(edges, kernel, iterations=2)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel, iterations=2)
    return m

def mask_hsv_with_ranges(bgr: np.ndarray, ranges: List[Tuple[Tuple[int,int,int], Tuple[int,int,int]]]) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    combined = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for low, high in ranges:
        low = np.array(low, dtype=np.uint8)
        high = np.array(high, dtype=np.uint8)
        m = cv2.inRange(hsv, low, high)
        combined = cv2.bitwise_or(combined, m)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)
    combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=1)
    return combined

def default_hsv_ranges() -> List[Tuple[Tuple[int,int,int], Tuple[int,int,int]]]:
    return [
        ((15, 60, 60), (45, 255, 255)),  # yellow kernels
        ((30, 30, 20), (90, 255, 255)),  # green husk
    ]

# ----------------------------
# Contour helpers & rotated crop
# ----------------------------
def largest_contour_minarea_rect(mask: np.ndarray, min_area: int):
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    areas = [cv2.contourArea(c) for c in cnts]
    idx = int(np.argmax(areas))
    if areas[idx] < min_area:
        return None
    cnt = cnts[idx]
    rect = cv2.minAreaRect(cnt)
    box = cv2.boxPoints(rect).astype(int)
    return box, cnt, areas[idx]

def rotate_crop_by_box(bgr: np.ndarray, box: np.ndarray, margin_frac: float) -> np.ndarray:
    rect = cv2.minAreaRect(box)
    (cx,cy),(w,h),angle = rect
    M = cv2.getRotationMatrix2D((cx,cy), angle, 1.0)
    H, W = bgr.shape[:2]
    rotated = cv2.warpAffine(bgr, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    ones = np.ones((box.shape[0],1))
    pts = np.hstack([box.astype(np.float32), ones])
    rot_pts = (M @ pts.T).T
    x_min, y_min = rot_pts.min(axis=0)
    x_max, y_max = rot_pts.max(axis=0)
    max_side = max(x_max - x_min, y_max - y_min)
    pad = int(round(max_side * margin_frac))
    x0 = int(max(0, math.floor(x_min - pad)))
    y0 = int(max(0, math.floor(y_min - pad)))
    x1 = int(min(W, math.ceil(x_max + pad)))
    y1 = int(min(H, math.ceil(y_max + pad)))
    crop = rotated[y0:y1, x0:x1]
    return crop

# ----------------------------
# KMeans HSV fallback (optional)
# ----------------------------
def hsv_kmeans_mask(bgr: np.ndarray, downscale: int = 4, n_clusters: int = 3) -> Optional[np.ndarray]:
    if not HAS_SKLEARN:
        return None
    H0, W0 = bgr.shape[:2]
    if min(H0,W0) < 32:
        return None
    small = cv2.resize(bgr, (max(32, W0//downscale), max(32, H0//downscale)), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    h = hsv[:,:,0].reshape(-1,1)
    s = hsv[:,:,1].reshape(-1,1)
    v = hsv[:,:,2].reshape(-1,1)
    X = np.concatenate([h,s,v], axis=1).astype(np.float32)
    k = min(n_clusters, max(2, int(len(X) / 1000)))
    try:
        km = KMeans(n_clusters=k, random_state=0, n_init="auto").fit(X)
        labels = km.labels_
        centers = km.cluster_centers_
        scores = centers[:,1] * centers[:,2]
        idx = int(np.argmax(scores))
        mask_small = (labels.reshape(hsv.shape[:2]) == idx).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        mask_small = cv2.morphologyEx(mask_small, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask_small = cv2.morphologyEx(mask_small, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.resize(mask_small, (W0, H0), interpolation=cv2.INTER_NEAREST)
        return mask
    except Exception as e:
        logging.debug("hsv_kmeans_mask failure: %s", e)
        return None

# ----------------------------
# Resize fill & crop to fixed size (no padding)
# ----------------------------
def resize_fill(img: np.ndarray, th: int, tw: int) -> np.ndarray:
    H, W = img.shape[:2]
    if H == 0 or W == 0:
        return np.zeros((th, tw, 3), dtype=np.uint8)
    scale = max(tw / W, th / H)
    new_w = int(round(W * scale))
    new_h = int(round(H * scale))
    interp = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
    resized = cv2.resize(img, (new_w, new_h), interpolation=interp)
    left = max(0, (new_w - tw) // 2)
    top = max(0, (new_h - th) // 2)
    cropped = resized[top: top + th, left: left + tw]
    return cropped

# ----------------------------
# Validation helpers
# ----------------------------
def compute_mask_coverage(mask: np.ndarray, crop_shape: Tuple[int,int]) -> float:
    if mask is None:
        return 0.0
    h, w = crop_shape[:2]
    if h == 0 or w == 0:
        return 0.0
    total = h * w
    foreground = int(np.count_nonzero(mask))
    return foreground / float(total) if total > 0 else 0.0

# ----------------------------
# Single-image full pipeline (improved)
# ----------------------------
def process_single_image(src: str, dst: str, cfg: CFG, intermediates_root: Optional[str] = None, tuned_params: Optional[Dict[str,Any]]=None) -> Optional[Dict[str,Any]]:
    meta = {"src": src, "dst": dst, "status": "unknown", "timestamp": time.strftime(cfg.timestamp_format)}
    try:
        img = load_image_exif(src, use_exif=cfg.use_exif)
        if img is None:
            meta['status'] = 'read_failed'
            logging.warning("Failed to read %s", src)
            return meta
        H0, W0 = img.shape[:2]
        meta['orig_w'] = int(W0); meta['orig_h'] = int(H0)

        area = float(H0 * W0)
        min_contour_area = max(int(max(100, cfg.min_contour_area_fraction * area)), 100)
        margin = tuned_params.get('margin', cfg.margin) if tuned_params else cfg.margin
        hsv_ranges = tuned_params.get('hsv_ranges', cfg.hsv_ranges) if tuned_params else cfg.hsv_ranges
        if hsv_ranges is None:
            hsv_ranges = default_hsv_ranges()

        img_bal = grey_world(img)
        if cfg.use_clahe:
            img_bal = apply_clahe(img_bal, cfg.clahe_clip, cfg.clahe_grid)

        if cfg.save_intermediates and intermediates_root:
            inter_dir = Path(intermediates_root) / Path(src).parent.name
            inter_dir.mkdir(parents=True, exist_ok=True)
            imwrite_unicode(str(inter_dir / (Path(src).stem + "_balanced.jpg")), img_bal, quality=95)

        # BUILD MASKS (use unique variable names)
        mask_hsv = mask_hsv_with_ranges(img_bal, hsv_ranges)
        mask_otsu_img = mask_otsu(img_bal)  # variable name changed to avoid shadowing function
        mask_edge_img = mask_edges(img_bal)
        combined = cv2.bitwise_or(mask_hsv, cv2.bitwise_or(mask_otsu_img, mask_edge_img))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=1)

        if cfg.save_intermediates and intermediates_root:
            inter_dir = Path(intermediates_root) / Path(src).parent.name
            imwrite_unicode(str(inter_dir / (Path(src).stem + "_mask_combined.png")), combined, quality=100)

        attempt = 0
        used_strategy = None
        crop_img = None
        crop_mask = None

        while attempt < cfg.max_attempts:
            if attempt == 0:
                target_mask = combined.copy()
                try_margin = margin
            elif attempt == 1:
                kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9,9))
                target_mask = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel2, iterations=2)
                try_margin = margin
            elif attempt == 2:
                target_mask = mask_hsv.copy()
                try_margin = margin + 0.02
            else:
                target_mask = combined.copy()
                try_margin = margin + cfg.margin_increment_steps[min(attempt - 3, len(cfg.margin_increment_steps)-1)]

            lamr = largest_contour_minarea_rect(target_mask, min_contour_area)
            if lamr:
                box, cnt, cnt_area = lamr
                crop_img = rotate_crop_by_box(img_bal, box, try_margin)
                crop_mask = rotate_crop_by_box(target_mask, box, try_margin)
                used_strategy = f"minarea_attempt_{attempt}"
                logging.debug("minarea found (area=%.0f) on attempt %d for %s", float(cnt_area), attempt, src)
            else:
                crop_img = None
                crop_mask = None
                logging.debug("no minarea rect found attempt=%d for %s", attempt, src)

            if crop_img is not None:
                coverage = compute_mask_coverage((crop_mask > 0).astype(np.uint8), crop_img.shape[:2])
                meta['coverage'] = float(coverage)
                if coverage >= cfg.crop_mask_coverage_threshold:
                    meta['status'] = 'ok'
                    break
                else:
                    logging.debug("coverage %.3f below threshold %.3f on attempt %d for %s", coverage, cfg.crop_mask_coverage_threshold, attempt, src)
            attempt += 1

        # KMeans fallback
        if crop_img is None or meta.get('coverage', 0.0) < cfg.crop_mask_coverage_threshold:
            if HAS_SKLEARN:
                km_mask = hsv_kmeans_mask(img_bal, downscale=cfg.sample_downscale, n_clusters=cfg.kmeans_clusters)
                if km_mask is not None:
                    if cfg.save_intermediates and intermediates_root:
                        inter_dir = Path(intermediates_root) / Path(src).parent.name
                        imwrite_unicode(str(inter_dir / (Path(src).stem + "_mask_kmeans.png")), km_mask, quality=100)
                    lamr2 = largest_contour_minarea_rect(km_mask, max(200, int(min_contour_area/2)))
                    if lamr2:
                        box2, cnt2, area2 = lamr2
                        crop_img2 = rotate_crop_by_box(img_bal, box2, margin + 0.02)
                        crop_mask2 = rotate_crop_by_box(km_mask, box2, margin + 0.02)
                        cov2 = compute_mask_coverage((crop_mask2 > 0).astype(np.uint8), crop_img2.shape[:2])
                        logging.debug("kmeans cov=%.3f for %s", cov2, src)
                        if cov2 >= cfg.crop_mask_coverage_threshold:
                            crop_img = crop_img2
                            crop_mask = crop_mask2
                            used_strategy = "kmeans_minarea"
                            meta['coverage'] = float(cov2)
                            meta['status'] = 'ok'
            else:
                logging.debug("sklearn not installed; skipping kmeans fallback")

        # Axis bbox fallback
        if (crop_img is None) or (meta.get('coverage', 0.0) < cfg.crop_mask_coverage_threshold):
            cnt_bbox = largest_component_bbox_from_mask(combined, min_area=max(50, int(min_contour_area/4)))
            if cnt_bbox is not None:
                x,y,w,h = cnt_bbox
                pad = int(round(max(w,h) * (margin + 0.02)))
                x0 = max(0, x - pad); y0 = max(0, y - pad); x1 = min(W0, x + w + pad); y1 = min(H0, y + h + pad)
                crop_img = img_bal[y0:y1, x0:x1]
                crop_mask = combined[y0:y1, x0:x1]
                used_strategy = "axis_bbox_fallback"
                cov = compute_mask_coverage((crop_mask > 0).astype(np.uint8), crop_img.shape[:2])
                meta['coverage'] = float(cov)
                if cov >= cfg.crop_mask_coverage_threshold:
                    meta['status'] = 'ok'

        # Center fallback
        if (crop_img is None) or (meta.get('coverage', 0.0) < cfg.crop_mask_coverage_threshold):
            side = int(round(min(H0, W0) * 0.85))
            cx, cy = W0//2, H0//2
            x0 = max(0, cx - side//2); y0 = max(0, cy - side//2)
            x1 = min(W0, x0 + side); y1 = min(H0, y0 + side)
            crop_img = img_bal[y0:y1, x0:x1]
            used_strategy = "center_fallback"
            crop_mask = combined[y0:y1, x0:x1]
            meta['coverage'] = float(compute_mask_coverage((crop_mask > 0).astype(np.uint8), crop_img.shape[:2]))
            meta['status'] = 'fallback_center'

        if crop_img is None:
            meta['status'] = 'crop_failed'
            logging.error("Crop failed entirely for %s", src)
            return meta

        th, tw = cfg.target_size
        out = resize_fill(crop_img, th, tw)

        if cfg.save_intermediates and intermediates_root:
            inter_dir = Path(intermediates_root) / Path(src).parent.name
            ensure_dir(str(inter_dir))
            imwrite_unicode(str(inter_dir / (Path(src).stem + "_crop_raw.jpg")), crop_img, quality=95)
            if crop_mask is not None:
                imwrite_unicode(str(inter_dir / (Path(src).stem + "_crop_mask.png")), crop_mask, quality=100)

        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        if Path(dst).exists() and not cfg.force:
            meta['status'] = 'skipped'
            return meta
        saved = imwrite_unicode(dst, out, quality=cfg.save_quality)
        if not saved:
            meta['status'] = 'save_failed'
            return meta

        meta['status'] = 'ok' if meta.get('status') != 'fallback_center' else 'fallback_center'
        meta['used_strategy'] = used_strategy
        meta['final_w'] = int(tw); meta['final_h'] = int(th)
        return meta

    except Exception as e:
        logging.exception("Exception processing %s: %s", src, e)
        meta['status'] = 'error'
        meta['exception'] = str(e)
        return meta

# helper used above
def largest_component_bbox_from_mask(mask: np.ndarray, min_area: int):
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    areas = [cv2.contourArea(c) for c in cnts]
    idx = int(np.argmax(areas))
    if areas[idx] < min_area:
        return None
    x,y,w,h = cv2.boundingRect(cnts[idx])
    return (x,y,w,h)

# ----------------------------
# Autotune: sample N images and find robust margin & optionally HSV tweak
# ----------------------------
def autotune_parameters(cfg: CFG, sample_n: int = 30, random_seed: int = 0) -> Dict[str,Any]:
    np.random.seed(random_seed)
    mapping = collect_input_mapping(cfg.raw_dir)
    paths = []
    for cls, files in mapping.items():
        paths.extend(files)
    if not paths:
        raise FileNotFoundError("No files found for autotune")
    sample_n = min(sample_n, len(paths))
    samples = list(np.random.choice(paths, sample_n, replace=False))

    margins_to_try = [0.02, 0.04, 0.06, 0.08, 0.10, 0.14, 0.18]
    good_margins = []
    logging.info("Autotune: sampling %d images to test margins %s", len(samples), margins_to_try)
    for p in samples:
        img = load_image_exif(p, use_exif=cfg.use_exif)
        if img is None:
            continue
        img_bal = grey_world(img)
        if cfg.use_clahe:
            img_bal = apply_clahe(img_bal, cfg.clahe_clip, cfg.clahe_grid)
        hsv_ranges = cfg.hsv_ranges if cfg.hsv_ranges is not None else default_hsv_ranges()
        combined = mask_hsv_with_ranges(img_bal, hsv_ranges)
        m2 = mask_otsu(img_bal)
        me = mask_edges(img_bal)
        combined = cv2.bitwise_or(combined, cv2.bitwise_or(m2, me))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)

        area = float(img.shape[0] * img.shape[1])
        min_contour_area = max(int(area * cfg.min_contour_area_fraction), 100)

        found_good = False
        for m in margins_to_try:
            lamr = largest_contour_minarea_rect(combined, min_contour_area)
            if lamr:
                box, cnt, cnt_area = lamr
                crop_img = rotate_crop_by_box(img_bal, box, m)
                crop_mask = rotate_crop_by_box(combined, box, m)
                cov = compute_mask_coverage((crop_mask > 0).astype(np.uint8), crop_img.shape[:2])
                if cov >= cfg.crop_mask_coverage_threshold:
                    good_margins.append(m)
                    found_good = True
                    break
        if not found_good:
            if HAS_SKLEARN:
                kmask = hsv_kmeans_mask(img_bal, downscale=cfg.sample_downscale, n_clusters=cfg.kmeans_clusters)
                if kmask is not None:
                    lamr2 = largest_contour_minarea_rect(kmask, max(200, int(min_contour_area/2)))
                    if lamr2:
                        box2, cnt2, _ = lamr2
                        m2 = cfg.margin
                        crop_img = rotate_crop_by_box(img_bal, box2, m2)
                        crop_mask = rotate_crop_by_box(kmask, box2, m2)
                        cov2 = compute_mask_coverage((crop_mask>0).astype(np.uint8), crop_img.shape[:2])
                        if cov2 >= cfg.crop_mask_coverage_threshold:
                            good_margins.append(m2)
    if not good_margins:
        logging.warning("Autotune didn't find consistent margins; falling back to default margin %.3f", cfg.margin)
        return {"margin": cfg.margin}
    chosen = float(np.median(np.array(good_margins)))
    logging.info("Autotune chosen median margin=%.4f from %d samples", chosen, len(good_margins))
    return {"margin": chosen}

def collect_input_mapping(raw_dir: str) -> Dict[str, List[str]]:
    p = Path(raw_dir)
    if not p.exists():
        return {}
    classes = [x for x in sorted(p.iterdir()) if x.is_dir()]
    mapping = {}
    for c in classes:
        files = [str(f) for f in sorted(c.rglob("*")) if f.suffix.lower() in (".jpg",".jpeg",".png",".bmp",".tiff")]
        mapping[c.name] = files
    return mapping

# ----------------------------
# Batch driver including review mode
# ----------------------------
def run_pipeline(cfg: CFG, tuned: Optional[Dict[str,Any]]=None):
    mapping = collect_input_mapping(cfg.raw_dir)
    if not mapping:
        logging.error("No classes found in %s", cfg.raw_dir)
        return

    ensure_dir(cfg.out_dir)
    review_root = Path(cfg.review_save_path)
    if cfg.review_mode:
        ensure_dir(str(review_root))
        ensure_dir(str(review_root / cfg.reject_folder_name))

    intermediates_root = None
    if cfg.save_intermediates or cfg.debug:
        intermediates_root = str(Path(cfg.out_dir) / "_intermediates")
        ensure_dir(intermediates_root)

    results = []
    items = []
    for cls, files in mapping.items():
        out_cls = Path(cfg.out_dir) / cls
        out_cls.mkdir(parents=True, exist_ok=True)
        for f in files:
            dst = str(out_cls / Path(f).name)
            items.append((f, dst, cls))

    total = len(items)
    logging.info("Processing %d images across %d classes", total, len(mapping))

    iterator = items if tqdm is None else tqdm(items, desc="Preprocessing", ncols=100)

    for src, dst, cls in iterator:
        if Path(dst).exists() and not cfg.force:
            results.append({"src": src, "dst": dst, "class": cls, "status": "skipped"})
            continue
        meta = process_single_image(src, dst, cfg, intermediates_root, tuned_params=tuned)
        if meta is None:
            results.append({"src": src, "dst": dst, "class": cls, "status": "error"})
            continue
        meta['class'] = cls
        results.append(meta)

        if cfg.review_mode:
            status = meta.get('status', '')
            cov = meta.get('coverage', 0.0)
            flag_for_review = (status not in ("ok",)) or (cov < cfg.crop_mask_coverage_threshold)
            if flag_for_review:
                try:
                    review_dst = review_root / cfg.reject_folder_name / Path(src).name
                    shutil.copy(dst, str(review_dst))
                    logging.info("Copied low-confidence result %s -> %s", dst, str(review_dst))
                except Exception:
                    logging.exception("Failed to copy for review")
    ts = time.strftime(cfg.timestamp_format)
    meta_csv = Path(cfg.out_dir) / f"metadata_{ts}.csv"
    try:
        df = pd.DataFrame(results)
        df.to_csv(str(meta_csv), index=False)
        summary = {
            "total": len(results),
            "ok": int((df['status']=='ok').sum()) if 'status' in df.columns else 0,
            "skipped": int((df['status']=='skipped').sum()) if 'status' in df.columns else 0,
            "failed": int((df['status']!='ok').sum()) if 'status' in df.columns else 0
        }
        json_path = Path(cfg.out_dir) / f"summary_{ts}.json"
        with open(str(json_path), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logging.info("Saved metadata %s and summary %s", str(meta_csv), str(json_path))
    except Exception:
        logging.exception("Failed to write metadata/summary")

# ----------------------------
# Interactive review (optional)
# ----------------------------
def interactive_review(cfg: CFG):
    review_dir = Path(cfg.review_save_path) / cfg.reject_folder_name
    if not review_dir.exists():
        logging.error("No review rejects found at %s", str(review_dir))
        return
    files = list(review_dir.glob("*"))
    if not files:
        logging.info("No files to review.")
        return
    idx = 0
    while idx < len(files):
        f = files[idx]
        src = str(f)
        logging.info("Reviewing %s (%d/%d)", src, idx+1, len(files))
        preview = imread_unicode(src)
        if preview is None:
            logging.warning("Cannot read preview %s", src)
            idx += 1
            continue
        cv2.imshow("Preview (press y accept / n reject / q quit)", preview)
        k = cv2.waitKey(0) & 0xFF
        if k == ord('y'):
            logging.info("Accepted %s", src)
            idx += 1
        elif k == ord('n'):
            logging.info("Rejected %s", src)
            idx += 1
        elif k == ord('q'):
            logging.info("User requested quit review")
            break
        else:
            logging.info("Key %d pressed; skipping", k)
            idx += 1
    cv2.destroyAllWindows()

# ----------------------------
# CLI
# ----------------------------
def parse_cli() -> Tuple[CFG, argparse.Namespace]:
    p = argparse.ArgumentParser(description="Adaptive tight-crop preprocessing for Sortir Buah Jagung")
    p.add_argument("--raw_dir", type=str, default=None)
    p.add_argument("--out_dir", type=str, default=None)
    p.add_argument("--target_size", nargs=2, type=int, default=None, help="H W")
    p.add_argument("--margin", type=float, default=None)
    p.add_argument("--min_area_frac", type=float, default=None, help="min contour area as fraction of image area")
    p.add_argument("--no_exif", action="store_true")
    p.add_argument("--no_clahe", action="store_true")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--save_intermediates", action="store_true")
    p.add_argument("--force", action="store_true")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--autotune", type=int, default=None, help="autotune with N samples")
    p.add_argument("--review", action="store_true", help="enable review mode (copies low-confidence crops to dataset_review/rejects)")
    p.add_argument("--self_test", action="store_true", help="run synthetic self-test")
    return p.parse_args(), p

def create_synthetic_dataset(base_dir: str = "tmp_synth", classes: int = 3, per_class: int = 6):
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    rng = np.random.RandomState(0)
    for ci in range(classes):
        cls = f"grade_{ci}"
        dirc = Path(base_dir) / cls
        dirc.mkdir(parents=True, exist_ok=True)
        for i in range(per_class):
            h = rng.randint(240, 640); w = rng.randint(240, 640)
            img = np.ones((h,w,3), dtype=np.uint8) * 255
            color = (int(rng.randint(0,255)), int(rng.randint(0,255)), int(rng.randint(0,255)))
            center = (w//2, h//2)
            axes = (w//4, h//6)
            angle = rng.randint(0,359)
            cv2.ellipse(img, center, axes, angle, 0, 360, color, -1)
            imwrite_unicode(str(dirc / f"{cls}_{i}.jpg"), img, quality=95)
    return base_dir

def run_self_test_quick():
    tmp = create_synthetic_dataset()
    out = "tmp_dataset_out"
    cfg = CFG(raw_dir=tmp, out_dir=out, debug=True, save_intermediates=True, verbose=True, force=True)
    run_pipeline(cfg)
    ok = any(Path(out).rglob("*.jpg"))
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(out, ignore_errors=True)
    return ok

def main():
    args_ns, parser = parse_cli()
    cfg = CFG()
    if args_ns.raw_dir: cfg.raw_dir = args_ns.raw_dir
    if args_ns.out_dir: cfg.out_dir = args_ns.out_dir
    if args_ns.target_size:
        cfg.target_size = (int(args_ns.target_size[0]), int(args_ns.target_size[1]))
    if args_ns.margin is not None: cfg.margin = float(args_ns.margin)
    if args_ns.min_area_frac is not None: cfg.min_contour_area_fraction = float(args_ns.min_area_frac)
    if args_ns.no_exif: cfg.use_exif = False
    if args_ns.no_clahe: cfg.use_clahe = False
    if args_ns.debug: cfg.debug = True
    if args_ns.save_intermediates: cfg.save_intermediates = True
    if args_ns.force: cfg.force = True
    if args_ns.verbose: cfg.verbose = True
    if args_ns.autotune: cfg.autotune_samples = int(args_ns.autotune)
    if args_ns.review: cfg.review_mode = True

    setup_logging(cfg.verbose)

    if args_ns.self_test:
        ok = run_self_test_quick()
        logging.info("Self-test quick: %s", ok)
        sys.exit(0 if ok else 2)

    if not Path(cfg.raw_dir).exists():
        logging.error("raw_dir '%s' not found. Place images under raw_data/<class>", cfg.raw_dir)
        sys.exit(2)
    Path(cfg.out_dir).mkdir(parents=True, exist_ok=True)

    tuned = None
    if cfg.autotune_samples:
        try:
            tuned = autotune_parameters(cfg, sample_n=cfg.autotune_samples)
            logging.info("Autotune result: %s", str(tuned))
        except Exception:
            logging.exception("Autotune failed; proceeding with defaults")

    run_pipeline(cfg, tuned)

    if cfg.review_mode:
        logging.info("Entering interactive review (if GUI available).")
        try:
            interactive_review(cfg)
        except Exception:
            logging.exception("Interactive review failed or not supported in this environment.")

    logging.info("All done.")

if __name__ == "__main__":
    main()

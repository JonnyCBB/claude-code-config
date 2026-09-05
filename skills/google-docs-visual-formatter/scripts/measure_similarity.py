#!/usr/bin/env python3
"""
SSIM (Structural Similarity Index) measurement for image comparison.

Provides quantitative similarity metric (0-1 scale, higher is better).
Used for validation after formatting fixes are applied.
"""

import argparse
import sys
import json
from pathlib import Path

try:
    from skimage.metrics import structural_similarity as ssim
    from skimage import io
    from skimage.transform import resize
    import numpy as np
except ImportError:
    print("Error: scikit-image not installed. Install with: pip install scikit-image", file=sys.stderr)
    sys.exit(1)


def measure_ssim(image1_path, image2_path):
    """
    Computes SSIM (Structural Similarity Index) between two images.

    Args:
        image1_path: Path to first image (reference)
        image2_path: Path to second image (comparison)

    Returns:
        dict: {"ssim": float, "quality": str, "status": str}
    """
    print(f"Loading images...")
    img1 = io.imread(image1_path)
    img2 = io.imread(image2_path)

    # Ensure same dimensions
    if img1.shape != img2.shape:
        print(f"Resizing images to match dimensions: {img1.shape}")
        img2 = resize(img2, img1.shape, anti_aliasing=True, preserve_range=True)
        img2 = img2.astype(img1.dtype)

    print("Computing SSIM...")

    # Compute SSIM with appropriate parameters
    if len(img1.shape) == 3:  # Color image
        score = ssim(img1, img2, channel_axis=2, data_range=img1.max() - img1.min())
    else:  # Grayscale
        score = ssim(img1, img2, data_range=img1.max() - img1.min())

    # Interpret score
    if score >= 0.95:
        quality = "excellent"
        status = "success"
    elif score >= 0.85:
        quality = "good"
        status = "acceptable"
    else:
        quality = "poor"
        status = "needs_improvement"

    return {
        "ssim": round(score, 4),
        "quality": quality,
        "status": status,
        "threshold_met": bool(score >= 0.95)
    }


def main():
    parser = argparse.ArgumentParser(
        description='Measure SSIM (Structural Similarity Index) between two images'
    )
    parser.add_argument('--image1', required=True, help='Reference image path')
    parser.add_argument('--image2', required=True, help='Comparison image path')

    args = parser.parse_args()

    # Validate paths
    if not Path(args.image1).exists():
        print(f"Error: Image not found: {args.image1}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.image2).exists():
        print(f"Error: Image not found: {args.image2}", file=sys.stderr)
        sys.exit(1)

    result = measure_ssim(args.image1, args.image2)

    # Output JSON
    print(json.dumps(result, indent=2))

    # Human-readable summary
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"SSIM Score: {result['ssim']}", file=sys.stderr)
    print(f"Quality: {result['quality']}", file=sys.stderr)
    print(f"Status: {result['status']}", file=sys.stderr)
    print(f"Threshold (≥0.95): {'✓ PASS' if result['threshold_met'] else '✗ FAIL'}", file=sys.stderr)
    print(f"{'='*50}", file=sys.stderr)

    # Exit code based on threshold
    sys.exit(0 if result['threshold_met'] else 1)


if __name__ == '__main__':
    main()

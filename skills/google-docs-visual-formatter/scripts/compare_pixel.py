#!/usr/bin/env python3
"""
Pixel-level image comparison using odiff.

Performs fast perceptual comparison and returns diff percentage.
Used for pre-screening: if <1% different, skip expensive LLM analysis.
"""

import argparse
import subprocess
import sys
import json
import re


def compare_images_with_odiff(image1_path, image2_path, diff_output_path, threshold=0.1):
    """
    Compares two images using odiff and returns diff percentage.

    Args:
        image1_path: Path to first image
        image2_path: Path to second image
        diff_output_path: Path to save diff image
        threshold: Sensitivity threshold (0.0 = identical, 1.0 = very different)

    Returns:
        dict: {"diff_percent": float, "diff_pixels": int, "total_pixels": int}
    """
    print(f"Comparing images with odiff (threshold={threshold})...")

    try:
        result = subprocess.run(
            [
                'odiff',
                str(image1_path),
                str(image2_path),
                str(diff_output_path),
                '--threshold', str(threshold),
                '--output-diff-mask'
            ],
            capture_output=True,
            text=True
        )

        # Parse odiff output: "X pixels (Y%) are different"
        output = result.stdout + result.stderr

        # Extract diff percentage
        percent_match = re.search(r'\((\d+\.?\d*)%\)', output)
        pixel_match = re.search(r'(\d+)\s+pixels?', output)

        if percent_match:
            diff_percent = float(percent_match.group(1))
            diff_pixels = int(pixel_match.group(1)) if pixel_match else 0

            return {
                "diff_percent": diff_percent,
                "diff_pixels": diff_pixels,
                "status": "different" if diff_percent > 0 else "identical"
            }
        else:
            # Images are identical (no diff reported)
            return {
                "diff_percent": 0.0,
                "diff_pixels": 0,
                "status": "identical"
            }

    except FileNotFoundError:
        print("Error: odiff not found. Install with: npm install -g odiff-bin", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running odiff: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Fast pixel-level image comparison using odiff'
    )
    parser.add_argument('--image1', required=True, help='First image path')
    parser.add_argument('--image2', required=True, help='Second image path')
    parser.add_argument('--output', required=True, help='Diff image output path')
    parser.add_argument('--threshold', type=float, default=0.1, help='Sensitivity threshold (default: 0.1)')

    args = parser.parse_args()

    result = compare_images_with_odiff(
        args.image1,
        args.image2,
        args.output,
        args.threshold
    )

    # Output JSON for easy parsing
    print(json.dumps(result, indent=2))

    # Exit code based on difference
    if result['diff_percent'] < 1.0:
        print(f"\n✓ Images are very similar ({result['diff_percent']}% different)", file=sys.stderr)
        sys.exit(0)
    else:
        print(f"\n⚠ Images have noticeable differences ({result['diff_percent']}% different)", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Render a Manim scene file to GIF or WebM.

Usage:
    python3 render_manim.py <scene_file.py> <SceneClassName> [options]

Options:
    --format gif|webm   Output format (default: gif)
    --output-dir DIR    Output directory (default: current directory)
    --quality low|medium|high  Render quality (default: medium)
    --help              Show this help message

Examples:
    python3 render_manim.py gradient.py GradientScene --format gif --output-dir ./media
    python3 render_manim.py nn.py NeuralNetScene --format webm --quality high
"""

import argparse
import subprocess
import sys
from pathlib import Path


QUALITY_MAP = {
    "low": "-ql",
    "medium": "-qm",
    "high": "-qh",
}


def find_output_file(scene_file, scene_class, fmt, quality_flag):
    """Find the rendered output file in Manim's default output location."""
    quality_dirs = {"-ql": "480p15", "-qm": "720p30", "-qh": "1080p60"}
    quality_dir = quality_dirs.get(quality_flag, "720p30")
    stem = Path(scene_file).stem

    # Manim outputs to media/videos/<stem>/<quality>/<ClassName>.<ext>
    candidates = [
        Path("media") / "videos" / stem / quality_dir / f"{scene_class}.{fmt}",
        Path("media") / "videos" / stem / quality_dir / f"{scene_class}.mp4",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Render a Manim scene to GIF or WebM"
    )
    parser.add_argument("scene_file", help="Path to the Manim scene Python file")
    parser.add_argument("scene_class", help="Name of the Scene class to render")
    parser.add_argument(
        "--format", choices=["gif", "webm"], default="gif", help="Output format"
    )
    parser.add_argument(
        "--output-dir", default=".", help="Directory to place the output file"
    )
    parser.add_argument(
        "--quality",
        choices=["low", "medium", "high"],
        default="medium",
        help="Render quality",
    )

    args = parser.parse_args()

    scene_path = Path(args.scene_file)
    if not scene_path.exists():
        print(f"Error: Scene file not found: {scene_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    quality_flag = QUALITY_MAP[args.quality]

    # Build manim command
    cmd = [
        "manim",
        quality_flag,
        "--format",
        args.format,
        str(scene_path),
        args.scene_class,
    ]

    print(f"Rendering {args.scene_class} from {scene_path}...")
    print(f"  Format: {args.format}, Quality: {args.quality}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: Manim rendering failed", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("Error: manim command not found. Run install_deps.sh first.", file=sys.stderr)
        sys.exit(1)

    # Find and move output
    output_file = find_output_file(
        args.scene_file, args.scene_class, args.format, quality_flag
    )

    if output_file is None:
        print("Error: Could not find rendered output file", file=sys.stderr)
        print(f"Manim stdout: {result.stdout}", file=sys.stderr)
        sys.exit(1)

    # Copy to output directory
    dest = output_dir / f"{args.scene_class}.{args.format}"
    import shutil
    shutil.copy2(output_file, dest)

    print(f"Output: {dest}")


if __name__ == "__main__":
    main()

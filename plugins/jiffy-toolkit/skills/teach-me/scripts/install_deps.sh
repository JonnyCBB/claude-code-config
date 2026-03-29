#!/bin/bash
# install_deps.sh — Idempotent installation of Manim and system dependencies
# Usage:
#   bash install_deps.sh              # Install all dependencies
#   bash install_deps.sh --check-only # Check if Manim is installed

set -e

# Check-only mode
if [ "$1" = "--check-only" ]; then
  if python3 -c "import manim" 2>/dev/null; then
    echo "installed"
  else
    echo "not-installed"
  fi
  exit 0
fi

echo "Installing Manim dependencies..."

# System deps via Homebrew (macOS)
if command -v brew &>/dev/null; then
  for pkg in cairo pango ffmpeg pkg-config; do
    if brew list "$pkg" &>/dev/null; then
      echo "  $pkg: already installed"
    else
      echo "  Installing $pkg..."
      brew install "$pkg"
    fi
  done
else
  echo "Warning: Homebrew not found. Please install system dependencies manually:"
  echo "  cairo, pango, ffmpeg, pkg-config"
fi

# Manim via uv (preferred) with pip fallback
if python3 -c "import manim" 2>/dev/null; then
  echo "Manim: already installed"
else
  if command -v uv &>/dev/null; then
    echo "Installing Manim via uv..."
    uv pip install manim
  else
    echo "uv not found, falling back to pip..."
    pip3 install manim 2>/dev/null || pip install manim
  fi
fi

# Verify installation
if python3 -c "import manim" 2>/dev/null; then
  echo "Manim installed successfully"
  exit 0
else
  echo "Error: Manim installation failed"
  exit 1
fi

#!/bin/bash

# Script to copy agents, skills, hooks, and config to ~/.claude folder

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Target directory
CLAUDE_DIR="$HOME/.claude"

echo "Claude Code Setup Installation"
echo "==============================="
echo ""

# Check if ~/.claude directory exists
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "Error: ~/.claude directory does not exist."
    echo "Please create it first or run Claude Code to initialize it."
    exit 1
fi

# Function to copy directory with backup
copy_with_backup() {
    local source_dir="$1"
    local target_dir="$2"
    local dir_name="$3"

    if [ -d "$source_dir" ]; then
        if [ -d "$target_dir" ]; then
            echo "Backing up existing $dir_name to ${dir_name}.backup..."
            rm -rf "${target_dir}.backup"
            mv "$target_dir" "${target_dir}.backup"
        fi

        echo "Copying $dir_name..."
        cp -r "$source_dir" "$target_dir"
        echo "  ✓ $dir_name copied successfully"
    else
        echo "Warning: $source_dir not found, skipping..."
    fi
}

# Function to copy a single file with backup
copy_file_with_backup() {
    local source_file="$1"
    local target_file="$2"
    local file_name="$3"

    if [ -f "$source_file" ]; then
        if [ -f "$target_file" ]; then
            echo "Backing up existing $file_name to ${file_name}.backup..."
            cp "$target_file" "${target_file}.backup"
        fi

        echo "Copying $file_name..."
        cp "$source_file" "$target_file"
        echo "  ✓ $file_name copied successfully"
    else
        echo "Warning: $source_file not found, skipping..."
    fi
}

# Copy directories
copy_with_backup "$SCRIPT_DIR/agents" "$CLAUDE_DIR/agents" "agents"
copy_with_backup "$SCRIPT_DIR/skills" "$CLAUDE_DIR/skills" "skills"
copy_with_backup "$SCRIPT_DIR/hooks" "$CLAUDE_DIR/hooks" "hooks"

# Copy individual files
copy_file_with_backup "$SCRIPT_DIR/settings.json" "$CLAUDE_DIR/settings.json" "settings.json"
copy_file_with_backup "$SCRIPT_DIR/statusline.sh" "$CLAUDE_DIR/statusline.sh" "statusline.sh"

echo ""
echo "Installation complete!"
echo ""
echo "The following have been installed to ~/.claude:"
[ -d "$CLAUDE_DIR/agents" ] && echo "  • agents/"
[ -d "$CLAUDE_DIR/skills" ] && echo "  • skills/"
[ -d "$CLAUDE_DIR/hooks" ] && echo "  • hooks/"
[ -f "$CLAUDE_DIR/settings.json" ] && echo "  • settings.json"
[ -f "$CLAUDE_DIR/statusline.sh" ] && echo "  • statusline.sh"
echo ""

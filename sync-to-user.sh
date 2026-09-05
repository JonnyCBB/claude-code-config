#!/bin/bash

# Script to sync agents, skills, hooks, and config to ~/.claude folder
# Assumes the directories already exist

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Target directory
CLAUDE_DIR="$HOME/.claude"

echo "Claude Code Setup Sync"
echo "======================"
echo ""

# Check if ~/.claude directory exists
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "Error: ~/.claude directory does not exist."
    echo "Please run apply-to-user.sh first or create the directory."
    exit 1
fi

# Function to sync directory
sync_dir() {
    local source_dir="$1"
    local target_dir="$2"
    local dir_name="$3"

    if [ -d "$source_dir" ]; then
        if [ ! -d "$target_dir" ]; then
            echo "Error: $target_dir does not exist."
            echo "Please run apply-to-user.sh first."
            exit 1
        fi

        echo "Syncing $dir_name..."
        rsync -av --delete "$source_dir/" "$target_dir/"
        echo "  ✓ $dir_name synced successfully"
    else
        echo "Warning: $source_dir not found, skipping..."
    fi
}

# Function to sync a single file
sync_file() {
    local source_file="$1"
    local target_file="$2"
    local file_name="$3"

    if [ -f "$source_file" ]; then
        echo "Syncing $file_name..."
        cp "$source_file" "$target_file"
        echo "  ✓ $file_name synced successfully"
    else
        echo "Warning: $source_file not found, skipping..."
    fi
}

# Sync directories
sync_dir "$SCRIPT_DIR/agents" "$CLAUDE_DIR/agents" "agents"
sync_dir "$SCRIPT_DIR/skills" "$CLAUDE_DIR/skills" "skills"
sync_dir "$SCRIPT_DIR/hooks" "$CLAUDE_DIR/hooks" "hooks"

# Sync individual files
sync_file "$SCRIPT_DIR/settings.json" "$CLAUDE_DIR/settings.json" "settings.json"
sync_file "$SCRIPT_DIR/statusline.sh" "$CLAUDE_DIR/statusline.sh" "statusline.sh"

echo ""
echo "Sync complete!"
echo ""

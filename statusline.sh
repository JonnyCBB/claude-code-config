#!/bin/bash

# Claude Code Status Line - Enhanced Multi-line
# Line 1: directory | branch | context% | model | cost | languages
# Line 2: git diff stats
# Line 3: MCP server status

# Read JSON input from stdin
input=$(cat)

# Extract values using jq
PROJECT_DIR=$(echo "$input" | jq -r '.workspace.project_dir // empty')
CURRENT_DIR=$(echo "$input" | jq -r '.workspace.current_dir // empty')
COST_USD=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
MODEL_NAME=$(echo "$input" | jq -r '.model.display_name // empty')

# Get directory names
PROJECT_NAME=$(basename "$PROJECT_DIR")

# Calculate relative path from project to current dir
RELATIVE_DIR=""
if [ -n "$PROJECT_DIR" ] && [ -n "$CURRENT_DIR" ] && [ "$PROJECT_DIR" != "$CURRENT_DIR" ]; then
    RELATIVE_DIR="${CURRENT_DIR#$PROJECT_DIR/}"
fi

# Git directory for all git operations
GIT_DIR="${PROJECT_DIR:-$CURRENT_DIR}"

# Get git branch
GIT_BRANCH=""
if [ -d "${GIT_DIR}/.git" ] || git -C "${GIT_DIR}" rev-parse --git-dir >/dev/null 2>&1; then
    GIT_BRANCH=$(git -C "${GIT_DIR}" branch --show-current 2>/dev/null)
fi

# Get context percentage with color coding
CONTEXT_PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d'.' -f1)
[ -z "$CONTEXT_PCT" ] && CONTEXT_PCT=0

if [ "$CONTEXT_PCT" -ge 70 ]; then
    CTX_COLOR="\033[31m"  # Red
elif [ "$CONTEXT_PCT" -ge 50 ]; then
    CTX_COLOR="\033[33m"  # Yellow
else
    CTX_COLOR="\033[32m"  # Green
fi
RESET="\033[0m"
DIM="\033[2m"
CYAN="\033[36m"
GREEN="\033[32m"
RED="\033[31m"
YELLOW="\033[33m"
BLUE="\033[1;34m"      # Bright blue for directory
MAGENTA="\033[1;35m"   # Bright magenta for branch
ORANGE="\033[1;33m"    # Bright yellow/orange for Git label
BRIGHT_CYAN="\033[1;36m" # Bright cyan for new/untracked files

# Get token counts for display
INPUT_TOKENS=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
OUTPUT_TOKENS=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
CACHE_READ=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')

# Format cost or token count
COST_CENTS=$(awk "BEGIN {printf \"%.0f\", $COST_USD * 100}" 2>/dev/null)
[ -z "$COST_CENTS" ] && COST_CENTS=0

if [ "$COST_CENTS" -eq 0 ]; then
    TOTAL_TOKENS=$((INPUT_TOKENS + OUTPUT_TOKENS + CACHE_READ))
    if [ "$TOTAL_TOKENS" -ge 1000000 ]; then
        TOKEN_DISPLAY=$(awk "BEGIN {printf \"%.1fM\", $TOTAL_TOKENS / 1000000}")
    elif [ "$TOTAL_TOKENS" -ge 1000 ]; then
        TOKEN_DISPLAY=$(awk "BEGIN {printf \"%.1fK\", $TOTAL_TOKENS / 1000}")
    else
        TOKEN_DISPLAY="${TOTAL_TOKENS}"
    fi
    COST_DISPLAY="${TOKEN_DISPLAY} tok"
elif [ "$COST_CENTS" -ge 100 ]; then
    COST_DISPLAY=$(awk "BEGIN {printf \"\$%.2f\", $COST_CENTS / 100}")
else
    COST_DISPLAY="${COST_CENTS}c"
fi

# Language environment detection functions
get_python_info() {
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "$(basename "$VIRTUAL_ENV")"
    elif [ -n "$CONDA_DEFAULT_ENV" ]; then
        echo "$CONDA_DEFAULT_ENV"
    elif command -v python3 >/dev/null 2>&1; then
        python3 --version 2>&1 | sed 's/Python //'
    elif command -v python >/dev/null 2>&1; then
        python --version 2>&1 | sed 's/Python //'
    fi
}

get_node_info() {
    if command -v node >/dev/null 2>&1; then
        node -v 2>/dev/null | tr -d 'v'
    fi
}

# Git diff stats function
get_git_diff_stats() {
    if [ -z "$GIT_BRANCH" ]; then
        echo ""
        return
    fi

    # Get file counts
    STAGED=$(git -C "${GIT_DIR}" diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
    UNSTAGED=$(git -C "${GIT_DIR}" diff --numstat 2>/dev/null | wc -l | tr -d ' ')
    UNTRACKED=$(git -C "${GIT_DIR}" ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')

    # Get lines added/removed (staged + unstaged)
    STAGED_STATS=$(git -C "${GIT_DIR}" diff --cached --shortstat 2>/dev/null)
    UNSTAGED_STATS=$(git -C "${GIT_DIR}" diff --shortstat 2>/dev/null)

    STAGED_ADD=$(echo "$STAGED_STATS" | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+' || echo "0")
    STAGED_DEL=$(echo "$STAGED_STATS" | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' || echo "0")
    UNSTAGED_ADD=$(echo "$UNSTAGED_STATS" | grep -oE '[0-9]+ insertion' | grep -oE '[0-9]+' || echo "0")
    UNSTAGED_DEL=$(echo "$UNSTAGED_STATS" | grep -oE '[0-9]+ deletion' | grep -oE '[0-9]+' || echo "0")

    [ -z "$STAGED_ADD" ] && STAGED_ADD=0
    [ -z "$STAGED_DEL" ] && STAGED_DEL=0
    [ -z "$UNSTAGED_ADD" ] && UNSTAGED_ADD=0
    [ -z "$UNSTAGED_DEL" ] && UNSTAGED_DEL=0

    TOTAL_ADD=$((STAGED_ADD + UNSTAGED_ADD))
    TOTAL_DEL=$((STAGED_DEL + UNSTAGED_DEL))

    # Build output
    local OUTPUT=""

    # File status
    if [ "$STAGED" -gt 0 ] 2>/dev/null; then
        OUTPUT="${GREEN}✓${STAGED}${RESET}"
    fi
    if [ "$UNSTAGED" -gt 0 ] 2>/dev/null; then
        OUTPUT="${OUTPUT:+$OUTPUT }${YELLOW}!${UNSTAGED}${RESET}"
    fi
    if [ "$UNTRACKED" -gt 0 ] 2>/dev/null; then
        OUTPUT="${OUTPUT:+$OUTPUT }${BRIGHT_CYAN}+${UNTRACKED} new${RESET}"
    fi

    # Lines changed
    if [ "$TOTAL_ADD" -gt 0 ] || [ "$TOTAL_DEL" -gt 0 ]; then
        OUTPUT="${OUTPUT:+$OUTPUT }${GREEN}+${TOTAL_ADD}${RESET} ${RED}-${TOTAL_DEL}${RESET}"
    fi

    if [ -z "$OUTPUT" ]; then
        echo "${DIM}no changes${RESET}"
    else
        echo "$OUTPUT"
    fi
}

# MCP server status function
get_mcp_status() {
    local CLAUDE_CONFIG="$HOME/.claude.json"

    if [ ! -f "$CLAUDE_CONFIG" ]; then
        echo "${DIM}no MCP config${RESET}"
        return
    fi

    # Count configured MCP servers
    local SERVER_COUNT=$(jq -r '.mcpServers | keys | length' "$CLAUDE_CONFIG" 2>/dev/null)
    [ -z "$SERVER_COUNT" ] && SERVER_COUNT=0

    if [ "$SERVER_COUNT" -eq 0 ]; then
        echo "${DIM}no MCP servers${RESET}"
        return
    fi

    # Get server names
    local SERVERS=$(jq -r '.mcpServers | keys | join(", ")' "$CLAUDE_CONFIG" 2>/dev/null)

    echo "${CYAN}🔌 ${SERVER_COUNT} MCP servers${RESET} ${DIM}(${SERVERS})${RESET}"
}

# Gather language info
PYTHON_VER=$(get_python_info)
NODE_VER=$(get_node_info)

# ============ LINE 1: Main status ============
LINE1=""

# Directory (required) - bright blue
if [ -n "$RELATIVE_DIR" ]; then
    LINE1="📁 ${BLUE}${PROJECT_NAME}/${RELATIVE_DIR}${RESET}"
else
    LINE1="📁 ${BLUE}${PROJECT_NAME}${RESET}"
fi

# Git branch (required) - bright magenta
if [ -n "$GIT_BRANCH" ]; then
    LINE1="${LINE1} | 🌿 ${MAGENTA}${GIT_BRANCH}${RESET}"
fi

# Context percentage
LINE1="${LINE1} | ${CTX_COLOR}📊 ${CONTEXT_PCT}%${RESET}"

# Model (required)
LINE1="${LINE1} | 🤖 ${MODEL_NAME}"

# Cost/tokens
if [ "$COST_CENTS" -eq 0 ]; then
    LINE1="${LINE1} | 🔢 ${COST_DISPLAY}"
else
    LINE1="${LINE1} | 💰 ${COST_DISPLAY}"
fi

# Language environments (only show if detected)
LANG_INFO=""
[ -n "$PYTHON_VER" ] && LANG_INFO="🐍${PYTHON_VER}"
[ -n "$NODE_VER" ] && LANG_INFO="${LANG_INFO:+$LANG_INFO }⬢${NODE_VER}"

if [ -n "$LANG_INFO" ]; then
    LINE1="${LINE1} | ${LANG_INFO}"
fi

# ============ LINE 2: Git diff stats ============
GIT_STATS=$(get_git_diff_stats)
LINE2="📝 ${ORANGE}Git:${RESET} ${GIT_STATS}"

# ============ LINE 3: MCP server status ============
MCP_STATUS=$(get_mcp_status)
LINE3="${MCP_STATUS}"

# Output all lines
printf "%b\n" "$LINE1"
printf "%b\n" "$LINE2"
printf "%b" "$LINE3"

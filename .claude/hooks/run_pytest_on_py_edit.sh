#!/bin/bash
# PostToolUse hook: app/ または tests/ 配下の .py 編集後に pytest を自動実行

# stdin から tool_input の file_path を抽出
FILE_PATH=$(python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
" 2>/dev/null)

# app/ または tests/ 配下の .py ファイルに該当するか判定
if echo "$FILE_PATH" | grep -qE '(app|tests)/.*\.py$'; then
    PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
    echo "[Hook] pytest を実行します: $FILE_PATH"
    cd "$PROJECT_ROOT"
    python3 -m pytest tests/ -x -q
fi

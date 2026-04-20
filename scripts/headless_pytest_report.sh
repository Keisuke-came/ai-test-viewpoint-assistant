#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

REPORT_DIR="$PROJECT_ROOT/reports"
DATE=$(date +%Y-%m-%d)
DATETIME=$(date +"%Y-%m-%d %H:%M:%S")
OUTPUT="$REPORT_DIR/${DATE}_pytest_report.md"

echo "▶ pytest レポート生成開始: $DATE"

# pytestを直接実行して結果を取得
PYTEST_OUTPUT=$(python3 -m pytest tests/ -x -q 2>&1)
if [ $? -eq 0 ]; then
  RESULT="✅ PASSED"
else
  RESULT="❌ FAILED"
fi

# テスト件数を抽出
TOTAL=$(echo "$PYTEST_OUTPUT" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+')
FAILED=$(echo "$PYTEST_OUTPUT" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+')
FAILED=${FAILED:-0}

# Markdownをシェル側で生成して保存
cat > "$OUTPUT" << EOF
# pytest レポート — $DATE

## サマリー
- 実行日時: $DATETIME
- 結果: $RESULT
- 総テスト数: $TOTAL
- 失敗数: $FAILED

## 詳細ログ
\`\`\`
$PYTEST_OUTPUT
\`\`\`
EOF

echo "✅ 完了: $OUTPUT"
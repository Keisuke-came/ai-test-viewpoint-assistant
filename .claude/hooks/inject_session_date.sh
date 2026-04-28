#!/bin/bash
# .claude/hooks/inject_session_date.sh
#
# SessionStart Hook:
# セッション開始時に今日の日付（曜日付き）を自動コンテキストとして注入する。
#
# 設定: .claude/settings.json の SessionStart セクションで本スクリプトを呼ぶ
# 仕様: stdout に書いた内容がそのままセッション初期コンテキストに追加される

echo "[session context]"
echo "session started at: $(date '+%Y-%m-%d (%A)')"
exit 0

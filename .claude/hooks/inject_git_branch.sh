#!/bin/bash
# .claude/hooks/inject_git_branch.sh
#
# UserPromptSubmit Hook:
# ユーザーのプロンプト送信時に、現在の git ブランチ名を
# 自動コンテキストとして Claude に注入する。
#
# 設定: .claude/settings.json の UserPromptSubmit セクションで本スクリプトを呼ぶ
# 仕様: stdout に書いた内容がそのままプロンプトに追加される (exit 0 の場合)
#       git 外や異常時は黙って通過させ、プロンプトを止めない

# git リポジトリでなければ何も注入せず正常終了
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  exit 0
fi

# 現在ブランチ名を取得。detached HEAD のとき文字列 "HEAD" が返る
branch=$(git rev-parse --abbrev-ref HEAD)

if [ "$branch" = "HEAD" ]; then
  # detached HEAD: 代わりに short SHA を表示
  short_sha=$(git rev-parse --short HEAD 2>/dev/null)
  if [ -n "$short_sha" ]; then
    echo "[auto-injected context]"
    echo "current git branch: detached ($short_sha)"
  fi
else
  echo "[auto-injected context]"
  echo "current git branch: $branch"
fi

exit 0

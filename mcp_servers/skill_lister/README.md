# skill-lister MCP サーバー

このプロジェクトの `.claude/skills/` 配下にある Skill 一覧を Claude Code から取得できるようにする MCP サーバー。

## 提供 Tool

### list_skills

引数なし。プロジェクトに定義された Skill の一覧を `[{name, description, path}, ...]` の形式で返す。

- `name`: Skill のディレクトリ名
- `description`: `SKILL.md` frontmatter の `description`（取得できない場合は空文字）
- `path`: プロジェクトルートからの `SKILL.md` への相対パス

## 起動方式

stdio（Claude Code が `.mcp.json` 経由で子プロセスとして起動）。

## 単体動作確認

```bash
.venv/bin/python -m mcp_servers.skill_lister.server
# stdio 待機状態になればOK。Ctrl+C で抜ける。
```

## 依存

- mcp（公式 MCP Python SDK・FastMCP 利用）
- Python 3.10+ が必須（mcp パッケージの要件）

## 注意点

- `print()` は使わない（stdio 通信を破壊するため）
- ログ出力は `sys.stderr` 経由
- サーバーロジック変更後は Claude Code セッション再起動が必須
- `.mcp.json` の `command` は `.venv/bin/python` を指している。プロジェクトルートで `python3 -m venv .venv && pip install -r requirements.txt` を済ませておくこと

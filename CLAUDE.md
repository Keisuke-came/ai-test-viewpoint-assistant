# CLAUDE.md — Claude Code 向けプロジェクトガイド

このファイルは Claude Code がこのリポジトリで作業する際に参照するガイドです。
プロジェクトの概要・セットアップ手順は README.md を参照してください。

---

## プロジェクト概要

テスト仕様書・要件定義書をもとにテスト観点を生成・整理する AI アシスタント。
OpenAI API を呼び出し、Streamlit で UI を提供する。

---

## ディレクトリ構成と各ディレクトリの役割

```
app/
├── streamlit_app.py      # UI エントリーポイント（テスト対象外）
├── config/settings.py    # 環境変数の読み込みと設定管理
├── domain/models.py      # データクラス・例外クラス定義
├── llm/
│   ├── openai_client.py  # OpenAI API ラッパー（外部依存の境界）
│   └── schemas.py        # LLM 入出力の Pydantic スキーマ
├── services/             # ビジネスロジック層（中核）
│   ├── viewpoint_generation_service.py  # 観点生成の主処理
│   ├── prompt_builder.py                # プロンプト組み立て（純粋関数）
│   ├── markdown_formatter.py            # Markdown 整形（純粋関数）
│   └── result_formatter.py             # 結果整形（純粋関数）
└── utils/
    ├── category_utils.py   # カテゴリ・優先度ソート
    └── input_validator.py  # 入力バリデーション

tests/                    # pytest ユニットテスト（app/ と対称構造）
docs/                     # 設計書
```

---

## コーディングルール

### 型ヒント

- すべての関数引数・戻り値に型ヒントを付ける
- `Optional[X]` は `X | None`（Python 3.10+）ではなく `Optional[X]` で統一（3.9 対応）
- Pydantic モデルのフィールドは必ず型を明示する

### docstring

- public 関数・クラスには Google スタイルの docstring を書く
- 内部実装（`_` プレフィックス）は省略可

### 例外設計

- ドメイン固有の例外は `app/domain/models.py` に定義する
- 例外クラスは `InputValidationError` / `LlmApiError` / `ResponseFormatError` の 3 種を使い分ける
- 外部 API エラーは `LlmApiError` でラップして上位に伝播させる
- 握りつぶし（`except Exception: pass`）は禁止

---

## テストルール

### 基本方針

- `python3 -m pytest tests/ -x -q` を基準コマンドとして使う（`pytest.ini` で `testpaths = tests` 設定済み）
- テストは正常系・異常系・境界値の 3 軸を必ず網羅する
- 各テストは独立して実行可能にする（テスト間の状態依存を禁止）

### ファイル配置ルール

- `app/xxx/yyy.py` のテストは `tests/xxx/test_yyy.py` に置く
- 新規ディレクトリを切る場合は `__init__.py` を必ず追加する
- 共通フィクスチャは `tests/conftest.py` に集約する

### モック方針

- OpenAI API (`openai.OpenAI`) は `unittest.mock.patch` でクラスごとモック
- 環境変数は `monkeypatch.setattr(settings, "KEY", "value")` で上書き
- 純粋関数（`prompt_builder` / `markdown_formatter` / `result_formatter` / `category_utils`）はモックせず実装を直接呼ぶ
- `OpenAiClient` を使うサービス層はコンストラクタの `client` 引数（DI）にモックを注入する

---

## 禁止事項

| 禁止 | 理由 |
|---|---|
| `.env` の直接編集 | API キーが漏洩するリスクがある。変更する場合は `.env.example` も合わせて更新する |
| `print()` によるデバッグ | ログが本番コードに残留する。デバッグには pytest の `-s` フラグを使う |
| テストなしのロジック変更 | `app/services/` `app/utils/` のロジックを変更する場合は対応するテストを必ず更新・追加する |
| `except Exception: pass` | エラーの握りつぶしは不具合の原因になる |
| `streamlit_app.py` のユニットテスト | UI 層は Playwright MCP で手動確認する |

---

## Claude Code 固有の設定

### PostToolUse Hook（自動 pytest）

`.claude/settings.json` に PostToolUse Hook を設定済み。
`app/` または `tests/` 配下の `.py` ファイルを Edit / Write / MultiEdit した直後に
`python3 -m pytest tests/ -x -q` が自動実行される。

- Hook スクリプト: `.claude/hooks/run_pytest_on_py_edit.sh`
- 対象ツール: `Edit | Write | MultiEdit`
- 非対象: `README.md` など `.py` 以外のファイルは発火しない

テストが失敗した場合は実装を修正してから次の編集に進むこと。

### UserPromptSubmit Hook（git ブランチ注入）

`.claude/settings.json` に UserPromptSubmit Hook を設定済み。
プロンプト送信時に現在の git ブランチ名を自動でコンテキストとして注入する。

- Hook スクリプト: `.claude/hooks/inject_git_branch.sh`
- 発火タイミング: ユーザーのプロンプト送信直後・Claude 処理前
- stdout の挙動: PostToolUse と異なり、stdout がそのままプロンプトにコンテキストとして追加される（公式仕様）

注入される内容の例:

​```
[auto-injected context]
current git branch: feature/user-prompt-submit-hook
​```

git リポジトリ外や detached HEAD のときもプロンプトを止めず安全に通す設計（常に exit 0）。
新規 Hook を追加したあとは Claude Code セッションの再起動が必要。

### Skill（pytest-impl）

`.claude/skills/pytest-impl/SKILL.md` に pytest 実装用 Skill を定義済み。

```
# 使い方
/pytest-impl app/services/viewpoint_generation_service.py
```

設計書（`docs/viewpoint_generation_detailed_design.md`）と既存コードを参照しながら、
正常系・異常系・境界値を網羅したテストを自動生成する。

### Subagents（役割分担エージェント）

`.claude/agents/` 配下に Subagents を定義済み。
1エージェント1責務で、調査・レビュー・テスト設計を分業する。

| エージェント | 役割 | 使う場面 |
|---|---|---|
| `repo-explorer` | 事前調査 | 実装前の関連箇所把握 |
| `reviewer` | 差分レビュー | git diff のレビュー |
| `test-designer` | テスト設計 | テスト観点の整理（実装前） |

**Skills との使い分け**

- Skills（`/pytest-impl`）: 観点が固まったあとの「テスト実装」に使う
- Subagents: 実装前の「調査・設計・レビュー」に使う

詳細は `.claude/agents/README.md` を参照。

### MCP（Playwright）

`.mcp.json` に Playwright MCP を設定済み（project-scoped）。
Streamlit UI（`localhost:8501`）をブラウザ操作で確認できる。

```
# 使い方例（Claude Code のチャットで指示）
localhost:8501 を開いて初期表示を確認してください。
```

前提: `streamlit run app/streamlit_app.py` で起動済みであること。

### Headless モード（claude -p）

`scripts/headless_pytest_report.sh` を実行することで、
`claude -p` 経由ではなくシェル側でpytestを直接実行し、結果をMarkdownレポートとして保存する。

```bash
bash scripts/headless_pytest_report.sh
# → reports/YYYY-MM-DD_pytest_report.md を生成
```

- レポートは `reports/` に保存される（`.gitignore` 対象・ローカル限定）
- Macでの定期実行設定は `scripts/cron_example.txt` を参照
- 検証後は必ず `launchctl unload` でlaunchdを無効化すること

### GitHub Actions（CI）

`.github/workflows/` 配下に2本のワークフローを設定済み。

- `pytest.yml`: PR作成時・main へのpush時に `python -m pytest tests/ -x -q` を自動実行
- `claude-review.yml`: PR作成時に `anthropics/claude-code-action@v1` でコードレビューを自動実行

Claude レビューは本ファイル（CLAUDE.md）の禁止事項・テストルール・コーディングルールを
観点としてチェックする。指摘はPRコメントとして自動投稿される。

**必要な設定**
- [Claude Code GitHub App](https://github.com/apps/claude) を対象リポジトリに Install する（ANTHROPIC_API_KEY とは別に必須）
  - 未インストールの場合 `401 Unauthorized - Claude Code is not installed` で失敗する
- GitHub Secrets に `ANTHROPIC_API_KEY` を登録（ポートフォリオ専用発行キー推奨）
- `claude-review.yml` の permissions に `id-token: write` が必要（`claude-code-action@v1` の OIDC 認証に必須）
- `pull_request` トリガーを使用（fork安全性のため `pull_request_target` は使わない）

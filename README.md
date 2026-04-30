# AI テスト観点整理アシスタント

テスト仕様書・要件定義書・チケット文をもとに、テスト観点を自動で整理・生成する AI アシスタント。
Python + Streamlit + OpenAI API で構築したアプリ本体に加え、
**Claude Code を使った AI 支援開発基盤**（Skill / Subagents / Hook / MCP）も組み込んでいる。

---

## このプロジェクトの見どころ

### アプリ設計面

- **業務寄りテーマ**: テスト観点の整理は手間がかかる実務作業。LLM を使って生産性を上げることに着目した
- **レイヤ分割構成**: UI（Streamlit）・サービス層・LLM層・ドメインモデルを明確に分離。テスタビリティを意識した設計
- **Pydantic によるスキーマ管理**: LLM の出力を Pydantic モデルで受け取り、型安全に処理する
- **pytest によるユニットテスト**: 正常系・異常系・境界値を網羅。モック方針を明確に定義している

### AI 支援開発面

- **Claude Code Skill**: pytest 実装を定型化した Skill を定義し、毎回ゼロから指示しなくても一貫した品質のテストを生成できる
- **Subagents による責務分離**: 調査・テスト設計・差分レビューを専任エージェントに分業。1つの AI に全部やらせない設計
- **PostToolUse Hook**: `.py` 編集のたびに pytest を自動実行。AI が書いたコードが即座に検証される
- **UserPromptSubmit Hook**: プロンプト送信のたびに現在の git ブランチ名を自動注入。AI がブランチ文脈を常に把握できる
- **Playwright MCP**: Claude Code から直接ブラウザを操作し、Streamlit UI の動作確認を自然言語で指示できる
- **CLAUDE.md**: コーディングルール・テスト方針・禁止事項をファイルに定義し、AI との作業ルールを明文化

---

## 技術スタック

| 区分 | 技術 |
|---|---|
| 言語 | Python 3.10+ |
| UI | Streamlit |
| LLM 連携 | OpenAI API / openai-python |
| データバリデーション | Pydantic |
| 設定管理 | python-dotenv |
| テスト | pytest |
| UI 確認 | Playwright MCP |
| AI 開発支援 | Claude Code（Skill / Subagents / Hook） |

---

## アーキテクチャ / ディレクトリ構成

```
ai-test-viewpoint-assistant/
├── app/
│   ├── streamlit_app.py      # UI エントリーポイント（テスト対象外）
│   ├── services/             # ビジネスロジック層（テストの中心）
│   │   ├── viewpoint_generation_service.py
│   │   ├── prompt_builder.py
│   │   ├── markdown_formatter.py
│   │   └── result_formatter.py
│   ├── llm/                  # OpenAI API ラッパー（外部依存の境界）
│   ├── domain/               # データクラス・例外定義
│   ├── utils/                # 純粋関数ユーティリティ
│   └── config/               # 環境変数管理
├── tests/                    # pytest ユニットテスト（app/ と対称構造）
├── docs/
│   └── viewpoint_generation_detailed_design.md  # 詳細設計書
├── .claude/
│   ├── agents/               # Subagent 定義（repo-explorer / test-designer / reviewer）
│   ├── skills/pytest-impl/   # pytest 実装 Skill
│   ├── hooks/                # Hook スクリプト（PostToolUse / UserPromptSubmit）
│   └── settings.json         # Hook 設定
├── .mcp.json                 # Playwright MCP 設定（project-scoped）
├── CLAUDE.md                 # Claude Code 向けプロジェクトルール
└── README.md
```

---

## Claude Code / AI 支援開発

このプロジェクトは Claude Code を使った AI 支援開発フローを構築している。
ツールごとに役割を分担し、「AI に全部任せる」ではなく「AI と分業する」設計を意識している。

| ツール | 役割 |
|---|---|
| Playwright MCP | UI の動作確認を自然言語で指示 |
| 自作 MCP（skill-lister） | プロジェクト内の Skill 一覧を Claude から取得可能に |
| PostToolUse Hook | `.py` 編集後に pytest を自動実行 |
| UserPromptSubmit Hook | プロンプト送信時に git ブランチ名を自動注入 |
| SessionStart Hook | セッション開始時に日付・曜日を自動注入 |
| Skill（pytest-impl） | pytest 実装の定型化された入口 |
| Subagents | 調査・テスト設計・差分レビューの専任担当 |
| CLAUDE.md | コーディングルール・禁止事項の明文化 |
| Headless モード | `claude -p` でバッチ実行・レポート自動生成 |
| GitHub Actions + claude-code-action | PR自動レビュー・pytest自動実行のCI基盤 |

---

### Playwright MCP による UI 確認

`.mcp.json` に Playwright MCP を設定（project-scoped）。
Claude Code から直接ブラウザを操作し、Streamlit UI の動作を自然言語で確認できる。
clone したメンバー全員が同じ設定を共有できる。

```
# 使い方例
localhost:8501 を開いて、タイトル・入力欄・ボタンが表示されていることを確認してください。
何も入力せずにボタンを押して、エラーメッセージが表示されるか確認してください。
```

**前提**: Node.js 18+、`npx playwright install chromium`（初回のみ）

---

### PostToolUse Hook（pytest 自動実行）

`.claude/settings.json` に PostToolUse Hook を設定済み。
`app/` または `tests/` 配下の `.py` ファイルを編集した直後に
`python3 -m pytest tests/ -x -q` が自動実行される。

AI が生成したコードが即座に検証されるため、テスト未通過の状態でそのまま進んでしまうリスクを防ぐ。

---

### UserPromptSubmit Hook（git ブランチ自動注入）

`.claude/settings.json` に UserPromptSubmit Hook を設定済み。
プロンプト送信のたびに `.claude/hooks/inject_git_branch.sh` が実行され、
現在の git ブランチ名がコンテキストとして Claude に自動注入される。

```
# 注入されるコンテキスト例
[auto-injected context]
current git branch: feature/user-prompt-submit-hook
```

- git リポジトリ外や detached HEAD のときも安全にスルーする（常に `exit 0`）
- detached HEAD の場合は short SHA を代わりに表示する
- 毎回ブランチを伝えなくても、AI が常に作業文脈を把握できる

---

### Skill（pytest-impl）

`.claude/skills/pytest-impl/SKILL.md` に pytest 実装用の Skill を定義。

```bash
# 使い方
/pytest-impl app/services/viewpoint_generation_service.py
```

設計書（`docs/viewpoint_generation_detailed_design.md`）と既存コードを参照しながら、
正常系・異常系・境界値を意識したテストを自動生成する。

Skill を使うことで以下が安定する。

- 設計書を必ず最初に読む
- `streamlit_app.py`（UI層）はテスト対象外にする
- OpenAI API や環境変数は適切にモックする
- brittle test（壊れやすいテスト）を避ける
- 実装後にファイル一覧とテスト実行コマンドも整理する

---

### Subagents（調査・設計・レビューの専任担当）

`.claude/agents/` 配下に、役割の異なる3つの Subagent を定義している。

| エージェント | 役割 | 使う場面 |
|---|---|---|
| `repo-explorer` | 事前調査専任 | 実装前に関連ファイル・設計・パターンを把握したいとき |
| `test-designer` | テスト設計専任 | テスト観点（正常系・異常系・境界値）を整理したいとき |
| `reviewer` | 差分レビュー専任 | git diff をレビューしてバグや保守性の問題を指摘させたいとき |

1 つのエージェントに調査・設計・実装・レビューをすべてやらせるのではなく、
フェーズごとに専任エージェントを使い分ける設計にしている。

---

### CLAUDE.md

プロジェクト固有のルールを `CLAUDE.md` にまとめている。

- 型ヒントの形式（`Optional[X]`、Python 3.9 対応）
- docstring スタイル（Google スタイル）
- 例外設計（`InputValidationError` / `LlmApiError` / `ResponseFormatError` の3種）
- テスト配置規則（`app/xxx/yyy.py` → `tests/xxx/test_yyy.py`）
- 禁止事項（`except Exception: pass` / `print()` デバッグ / テストなしのロジック変更 等）

Claude Code との作業ルールを明文化することで、セッションをまたいでも一貫した品質が保てる。

---

### Headless モード（claude -p）によるバッチ実行

`claude -p` を使い、人間が操作しなくてもpytestを実行してMarkdownレポートを自動生成する仕組みを構築している。

```bash
# 手動実行
bash scripts/headless_pytest_report.sh

# 出力先
reports/YYYY-MM-DD_pytest_report.md（.gitignore 対象・ローカル限定）
```

レポートには実行日時・結果（PASSED/FAILED）・総テスト数・詳細ログが含まれる。

Macでの定期自動実行はlaunchdを使う。設定サンプルは `scripts/cron_example.txt` を参照。
launchd登録後は検証が終わり次第、必ず `launchctl unload` で無効化すること。

将来的にはCron + Headless の組み合わせを月次KPI集計などのバッチ処理に横展開できる。

---

### GitHub Actions によるCI自動化

PR作成時に以下の2本のワークフローが自動実行される。

| ワークフロー | 役割 | 実行タイミング |
|---|---|---|
| `pytest.yml` | pytest自動実行 | PR作成・更新・mainへのpush |
| `claude-review.yml` | Claude Codeによる自動レビュー | PR作成・更新 |

Claude Codeレビューは CLAUDE.md の禁止事項（`except Exception: pass` / `print()`デバッグ /
テストなしロジック変更 等）を観点にチェックし、PRコメントとして指摘を自動投稿する。

Headlessモード（`claude -p`）をGitHub Actions上に載せ替えた構成で、
ローカルPCの稼働状態に依存しない安定したCI基盤を実現している。

**設定手順**
1. [Claude Code GitHub App](https://github.com/apps/claude) にアクセスし、対象リポジトリに Install する
   - ANTHROPIC_API_KEY の登録とは**別に必須**。未インストールの場合 `401 Unauthorized - Claude Code is not installed` で失敗する
2. リポジトリの Settings → Secrets and variables → Actions → New repository secret
   - Name: `ANTHROPIC_API_KEY` / Secret: （ポートフォリオ専用に発行したAPIキー）
3. Workflow permissions の `id-token: write` が `claude-review.yml` に設定済みであることを確認
   - `claude-code-action@v1` の OIDC 認証に必須。未設定の場合 `Could not fetch an OIDC token` で失敗する
4. 以降、PRを作成すると自動でワークフローが起動する

---

## 開発フロー例

Skill と Subagents を組み合わせた典型的な開発フロー。

```
1. repo-explorer  → 対象ファイルの責務・関連モジュール・既存パターンを把握
2. test-designer  → 正常系・異常系・境界値・モック要否を設計
3. /pytest-impl   → 設計をもとに pytest テストを実装（Skill）
4. reviewer       → 追加した差分をレビューし、バグ・保守性・テスト不足を指摘
```

このフローにより、「何のために何を作るか」を整理してから実装に入る習慣をつけている。

---

## AI 出力品質 評価フレームワーク

複数の評価ケースをまとめて実行し、生成結果をルールベースで自動評価する機能。
LLM-as-a-judge のような追加 LLM 呼び出しは行わず、ローカル判定とキャッシュ再利用でトークンを節約する。

**評価ロジック**: 観点数・必須セクション・カテゴリ・キーワード・禁止ワード等をローカルで判定
**キャッシュ**: 同一条件（model + target_type + spec_text）ならキャッシュを再利用（`.eval_cache/` に JSON 保存）
**レポート**: JSON / Markdown で出力。PR や README に貼りやすい形式

```bash
# デフォルトケース（6件）で評価実行（キャッシュ利用）
python eval_run.py

# キャッシュを無視して再生成
python eval_run.py --refresh

# 結果をファイルに保存
python eval_run.py --output-json results/eval.json --output-md results/eval.md
```

Streamlit UI からも「🔬 AI 出力品質 評価」セクションを開いて実行できる。

---

## セットアップ

```bash
# 仮想環境の作成・有効化
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .env を編集して OPENAI_API_KEY を設定
```

---

## 起動方法

```bash
# Streamlit アプリの起動
streamlit run app/streamlit_app.py

# ユニットテストの実行
python3 -m pytest tests/ -x -q
```

### PostToolUse Hook（自動 pytest）

`.claude/settings.json` に PostToolUse Hook を設定している。
`app/` または `tests/` 配下の `.py` ファイルを編集するたびに
`python3 -m pytest tests/ -x -q` が自動実行される。
詳細は `CLAUDE.md` および `.claude/hooks/run_pytest_on_py_edit.sh` を参照。

### CLAUDE.md によるルール定義

`CLAUDE.md` をプロジェクトルートに配置することで、Claude Code がセッションをまたいで
コーディングルール・テスト方針・禁止事項を自動参照できる。

---

## 開発状況

- [x] プロジェクト骨組み作成
- [x] 詳細設計書追加（`docs/viewpoint_generation_detailed_design.md`）
- [x] ドメインモデル定義
- [x] テスト観点生成ロジック実装
- [x] LLM 連携実装（OpenAI API）
- [x] pytest によるユニットテスト実装
- [x] Playwright MCP による UI 動作確認
- [x] PostToolUse Hook（pytest 自動実行）
- [x] Claude Code Skill（pytest-impl）
- [x] CLAUDE.md によるプロジェクトルール定義
- [x] Subagents 基盤（repo-explorer / test-designer / reviewer）
- [x] AI 出力品質 評価フレームワーク（ルールベース + キャッシュ、CLI / UI 対応）
- [x] UserPromptSubmit Hook（git ブランチ名の自動注入）
- [x] SessionStart Hook（日付・曜日の自動注入）
- [x] 自作 MCP サーバー（skill-lister: list_skills ツール）

# AIテスト観点整理アシスタント

テスト仕様書や要件定義書をもとに、テスト観点を整理・生成するAIアシスタントのMVP。

## 技術スタック

- Python 3.9+
- Streamlit（UI）
- python-dotenv（環境変数管理）
- OpenAI API / openai-python（LLM連携）
- pydantic（データバリデーション）
- pytest（ユニットテスト）
- Playwright MCP（UI動作確認）

## ディレクトリ構成

```
ai-test-viewpoint-assistant/
├── app/
│   ├── streamlit_app.py   # UIエントリーポイント
│   ├── services/          # ビジネスロジック層
│   ├── llm/               # LLM連携層（OpenAI API）
│   ├── domain/            # データクラス・型定義
│   ├── utils/             # 共通ユーティリティ
│   └── config/            # 設定管理
├── docs/                  # 設計書
│   └── viewpoint_generation_detailed_design.md
├── tests/                 # pytestユニットテスト
├── .mcp.json              # Playwright MCP 設定（project-scoped）
├── requirements.txt
├── .env.example
└── README.md
```

## セットアップ

```bash
# 仮想環境の作成・有効化
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .env を編集してAPIキー等を設定
```

## 起動方法

```bash
# プロジェクトルートから実行
streamlit run app/streamlit_app.py
```

## Playwright MCP を使った UI 確認

Claude Code から Playwright MCP 経由で `localhost:8501` の Streamlit UI を直接確認できる。
設定は `.mcp.json`（プロジェクトルート）で project-scoped 管理しているため、clone したメンバー全員が同じ設定を利用できる。

### 前提

- Node.js 18+ がインストールされていること
- Streamlit アプリが起動していること

### ブラウザのインストール（初回のみ）

```bash
npx playwright install chromium
```

### 使い方

1. Claude Code を再起動して `.mcp.json` を読み込ませる
2. Streamlit を起動する: `streamlit run app/streamlit_app.py`
3. Claude Code のチャットで自然言語で UI 操作を指示する

```
# 例: 画面の初期表示確認
localhost:8501 を開いて、タイトル・入力欄・ボタンが表示されていることを確認してください。

# 例: 未入力エラーの確認
何も入力せずに「観点を生成する」ボタンを押して、エラーメッセージが表示されるか確認してください。
```

## Claude Code / AI支援開発

このプロジェクトは Claude Code を使った AI 支援開発で構築されている。

### Playwright MCP による UI 確認フロー

`.mcp.json` に Playwright MCP を設定することで、Claude Code が直接ブラウザを操作して UI の動作確認を行える。
スクリーンショットやアクセシビリティスナップショットを取得し、ボタンクリックやフォーム入力の自動操作が可能。

### Claude Code Skill（pytest-impl）

`.claude/skills/pytest-impl/SKILL.md` に pytest 実装用の Skill を定義している。
設計書・既存コードを参照しながら、正常系・異常系・境界値を網羅したテストを自動生成できる。

---

## 開発状況

- [x] プロジェクト骨組み作成
- [x] 詳細設計書追加（`docs/viewpoint_generation_detailed_design.md`）
- [x] ドメインモデル定義
- [x] テスト観点生成ロジック実装
- [x] LLM連携実装（OpenAI API）
- [x] pytest によるUT実装
- [x] Playwright MCP による UI 動作確認

# AIテスト観点整理アシスタント

テスト仕様書や要件定義書をもとに、テスト観点を整理・生成するAIアシスタントのMVP。

## 技術スタック

- Python 3.9+
- Streamlit（UI）
- python-dotenv（環境変数管理）
- LLM連携（後から追加予定）

## ディレクトリ構成

```
ai-test-viewpoint-assistant/
├── app/
│   ├── streamlit_app.py   # UIエントリーポイント
│   ├── services/          # ビジネスロジック層
│   ├── llm/               # LLM連携層（後から実装）
│   ├── domain/            # データクラス・型定義
│   ├── utils/             # 共通ユーティリティ
│   └── config/            # 設定管理
├── docs/                  # 設計書（viewpoint_generation_detailed_design.md を後から追加）
├── tests/                 # テストコード
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

## 開発状況

- [x] プロジェクト骨組み作成
- [ ] 詳細設計書追加（`docs/viewpoint_generation_detailed_design.md`）
- [ ] ドメインモデル定義
- [ ] テスト観点生成ロジック実装
- [ ] LLM連携実装

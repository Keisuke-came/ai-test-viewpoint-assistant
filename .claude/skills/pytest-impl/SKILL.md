---
name: pytest-impl
description: Add pytest unit tests for this project. Read the design doc and existing code, create logic-focused tests under tests/, and mock external APIs.
disable-model-invocation: true
---

# pytest-impl — テスト実装 Skill

このプロジェクト向けの pytest 単体テストを実装する。

## 実行前に必ず読むもの

1. `docs/viewpoint_generation_detailed_design.md` — 設計書（最優先）
2. `app/domain/models.py` — データモデルと例外定義
3. テスト対象として指定されたモジュール（`$ARGUMENTS` が空の場合は `app/` 全体を対象とする）
4. `tests/conftest.py` — 既存フィクスチャの確認

## テスト実装ルール

### 対象範囲
- **対象**: `app/` 配下のロジック層（services / utils / llm / domain / config）
- **対象外**: `app/streamlit_app.py`（UI層は手動確認で対応）

### ファイル配置
- `app/xxx/yyy.py` に対応するテストは `tests/xxx/test_yyy.py` に作成
- `tests/` 配下のディレクトリには `__init__.py` を必ず置く
- 共通フィクスチャは `tests/conftest.py` に追記する

### テストケース設計
- 正常系・異常系・境界値の3軸を意識する
- 設計書の「バリデーション詳細設計」「例外種別」「処理フロー」に沿ったケースを必ず含める
- テスト名は `test_<状況>_<期待結果>` または `test_<動作>` の形式で日本語コメントより英語名を優先する

### 外部依存のモック方針
- OpenAI API（`openai.OpenAI`）: `unittest.mock.patch` でクラスごとモック
- `app.config.settings` の環境変数: `monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")` で上書き
- `OpenAiClient` を使うサービス層のテスト: コンストラクタの `client` 引数（DI）にモックを注入
- **過剰モックを避ける**: 純粋関数（prompt_builder / markdown_formatter / result_formatter / category_utils）は実装をそのまま呼ぶ

### 避けるべきパターン（brittle test の防止）
- 文字列の完全一致で長文を検証しない → キーワード包含 (`in`) を使う
- プライベート実装の詳細（内部変数名など）に依存しない
- テスト間に状態の依存関係を持たせない（各テストは独立して実行可能にする）
- アサーションを `assert result is not None` だけで終わらせない

### アサーション強度のガイドライン
| 検証対象 | 弱い例（NG） | 強い例（OK） |
|---|---|---|
| 型チェック | `assert result` | `assert isinstance(result, DisplayResult)` |
| 文字列包含 | `assert len(result) > 0` | `assert "# サマリ" in result` |
| 例外メッセージ | `pytest.raises(Error)` のみ | `exc_info.value` で文言も確認 |
| リスト | `assert result.viewpoints` | `assert len(result.viewpoints) == 2` |

## 本番コードの変更方針

- **原則: 変更しない**
- 例外: テスタビリティのために必要な最小限の変更のみ許容
  - コンストラクタへの DI 引数追加（`Optional[X] = None` 形式）
  - `from __future__ import annotations` の追加（型ヒント互換）
- 変更した場合は必ず変更理由をコメントに残す

## 設計書との整合チェックリスト

実装後、以下を自己レビューしてから出力する。

- [ ] 設計書の「入力バリデーション」チェックID（VAL-IN-01〜03）に対応するテストがあるか
- [ ] 設計書の「応答バリデーション」チェックID（VAL-RES-01〜06）に対応するテストがあるか
- [ ] 設計書の「例外種別」（InputValidationError / LlmApiError / ResponseFormatError）が正しく使われているか
- [ ] カテゴリ順・優先度順の仕様（`CATEGORY_ORDER` / `PRIORITY_ORDER`）が境界値を含めて検証されているか
- [ ] Markdown生成仕様（セクション名・観点フォーマット）が検証されているか

## 出力フォーマット（実装完了後に必ず提示）

### 追加・変更したファイル一覧

| ファイルパス | 種別 | 内容 |
|---|---|---|
| `tests/xxx/test_yyy.py` | 新規 | 〇〇モジュールのUT |
| `app/xxx/yyy.py` | 変更 | DI対応（理由: ~~~） |

### テスト実行コマンド

```bash
python3 -m pytest tests/ -v
# 特定ファイルのみ
python3 -m pytest tests/xxx/test_yyy.py -v
# カバレッジ付き
python3 -m pytest tests/ --cov=app --cov-report=term-missing
```

### 想定確認ポイント

実装したテストで「何を・なぜ」確認しているかを箇条書きで提示する。
設計書のどのセクションに対応するかも併記する。

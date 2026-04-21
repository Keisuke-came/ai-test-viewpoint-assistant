---
name: design-to-code
description: Implement a module based on a specified design doc. Usage: /design-to-code <design_doc_path> <target_module_path>. Read the design doc first, then implement faithfully without adding unspecified behavior.
disable-model-invocation: true
---

# design-to-code — 設計書ベース実装 Skill

## 呼び出し形式

```
/design-to-code <設計書パス> <実装対象モジュールパス>
```

例：
```
/design-to-code docs/viewpoint_generation_detailed_design.md app/services/viewpoint_generation_service.py
/design-to-code docs/foo_design.md app/services/foo_service.py
```

`$ARGUMENTS` の第1引数を設計書パス、第2引数を実装対象モジュールパスとして解釈する。
引数が不足している場合は実装を開始せず、正しい呼び出し形式を案内して終了する。

## 実行前に必ず読むもの

1. `$ARGUMENTS` の第1引数で指定された設計書 — 最優先・必須
2. `CLAUDE.md` — コーディングルール・禁止事項
3. `app/domain/models.py` — データモデルと例外定義
4. `$ARGUMENTS` の第2引数で指定されたモジュールと同一ディレクトリの既存ファイル — 命名規則・構造の把握

## 実装ルール

### 設計書との整合

- 設計書に記載されている仕様のみを実装する
- 設計書に書いていない処理・分岐・バリデーションを勝手に追加しない
- 設計書の記述が曖昧な場合は実装を止め、該当箇所と疑問点を列挙して確認を求める

### コーディングルール（CLAUDE.md 準拠）

- すべての関数引数・戻り値に型ヒントを付ける（`Optional[X]` 形式、Python 3.9 対応）
- public 関数・クラスには Google スタイルの docstring を書く
- 例外は `InputValidationError` / `LlmApiError` / `ResponseFormatError` の3種を使い分ける
- 外部 API エラーは `LlmApiError` でラップして上位に伝播させる
- `except Exception: pass` は禁止
- `print()` デバッグは禁止

### ファイル配置

- 新規モジュールは `app/` 配下の適切なレイヤに置く
  - ビジネスロジック → `app/services/`
  - 純粋関数ユーティリティ → `app/utils/`
  - 外部API境界 → `app/llm/`
  - データモデル・例外 → `app/domain/`
- 新規ディレクトリを作成する場合は `__init__.py` を必ず追加する

### テスタビリティ

- 外部依存（OpenAI API等）はコンストラクタの引数（DI）で受け取る形にする
- 純粋関数は副作用を持たせない

## やってはいけないこと

| 禁止 | 理由 |
|---|---|
| 設計書にない仕様の追加 | 設計との乖離が生じ、後続のテスト・レビューがずれる |
| `streamlit_app.py` の変更 | UI層はこの Skill の対象外 |
| 既存モジュールの破壊的変更 | 影響範囲が読めなくなる。変更が必要な場合は理由を明示して確認を求める |
| テストの同時作成 | 実装と分離する。テストは `/pytest-impl` で別途作成する |

## 設計書との整合チェックリスト

実装後、以下を自己レビューしてから出力する。

- [ ] 設計書の「処理フロー」に沿った実装になっているか
- [ ] 設計書に記載されているバリデーション仕様がすべて実装されているか
- [ ] 設計書の「例外種別」に対応する例外クラスが正しく使われているか
- [ ] 設計書に記載のない処理を追加していないか
- [ ] 型ヒント・docstring が全 public 関数に付いているか

## 完了後の推奨アクション

実装が完了したら、必ず以下を案内する。

```
# テストの作成
/pytest-impl app/xxx/yyy.py
```

テストなしで実装だけ終わらせない。

## 出力フォーマット（実装完了後に必ず提示）

### 追加・変更したファイル一覧

| ファイルパス | 種別 | 対応する設計書セクション |
|---|---|---|
| `app/xxx/yyy.py` | 新規 | 設計書「〇〇」節 |
| `app/domain/models.py` | 変更 | 例外クラス追加（理由: ~~~） |

### 設計書との対応サマリ

実装した内容が設計書のどのセクション・仕様に対応するかを箇条書きで提示する。

- `validate_input()` → VAL-IN-01〜03（入力バリデーション）
- `generate()` → 処理フロー図「正常系」「LLM エラー時」

### 未実装・確認が必要な箇所

設計書の記述が不明瞭で判断を保留した箇所があれば、ここに列挙する。

| 設計書セクション | 不明点 | 仮の対応 |
|---|---|---|
| 〇〇節 | ~~~ | 一旦 XXX として実装 |

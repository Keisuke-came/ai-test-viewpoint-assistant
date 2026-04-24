# CSV エクスポート機能 設計書（ミニ設計書）

> 対象モジュール：`app/services/csv_formatter.py`（新規）
> 関連：`app/services/markdown_formatter.py`（既存・参照パターン）
> ステータス：**v1 ドラフト（叩き台）** — Phase 1 の Subagent で検証・補強する

---

## 1. 目的とスコープ

### 目的

観点生成結果を CSV 形式でダウンロード可能にし、Excel / スプレッドシートでの集計・共有・編集を容易にする。

### スコープ

| 区分 | 対象 |
|---|---|
| ✅ 対象 | 観点リスト（`List[Viewpoint]`）→ CSV 文字列への変換、Streamlit 上でのダウンロードボタン追加 |
| ❌ 対象外 | CSV のインポート機能、他形式（TSV / JSON / Excel バイナリ）への対応、サーバ側でのファイル永続化 |

---

## 2. 機能概要

### 入力

- 観点生成サービス（`viewpoint_generation_service`）が返す観点リスト
- 型：`List[Viewpoint]`（推定。Phase 1 の repo-explorer が確定する）

### 出力

- CSV 形式の文字列（BOM 付き UTF-8 を想定）
- Streamlit UI のダウンロードボタン経由で、ブラウザ側で `viewpoints.csv` として保存される

### 実行タイミング

観点生成が完了した後、UI 上の「CSV ダウンロード」ボタン押下時。
既存の Markdown ダウンロードボタンと並列に配置する（片方を選ぶ UI にはしない）。

---

## 3. 公開 API 設計

### 関数シグネチャ（案）

```python
# app/services/csv_formatter.py

from typing import List
from app.domain.models import Viewpoint  # Phase 1 で実型を確認


def format_as_csv(viewpoints: List[Viewpoint]) -> str:
    """観点リストを CSV 形式の文字列に変換する。

    先頭に BOM（U+FEFF）を付与し、Excel で開いた際の文字化けを防ぐ。
    フィールド内のカンマ・改行・ダブルクォートは RFC 4180 に従って
    ダブルクォートで囲み、内部のダブルクォートは 2 つ重ねてエスケープする。

    Args:
        viewpoints: 変換対象の観点リスト。空リストの場合はヘッダ行のみ返す。

    Returns:
        BOM 付き CSV 文字列（UTF-8 エンコード想定）。

    Raises:
        InputValidationError: viewpoints が None、または要素が Viewpoint 型でない場合。
    """
```

### 補助関数（必要に応じて）

純粋関数として分離する想定。既存 `markdown_formatter.py` のパターンに合わせる（Phase 1 で確認）。

```python
def _build_header() -> List[str]:
    """CSV のヘッダ行を返す。"""


def _viewpoint_to_row(viewpoint: Viewpoint) -> List[str]:
    """Viewpoint 1 件を CSV の 1 行（列のリスト）に変換する。"""
```

---

## 4. CSV 仕様

| 項目 | 仕様 | 根拠 |
|---|---|---|
| エンコーディング | UTF-8（BOM 付き、U+FEFF を先頭に付与） | Excel が BOM なし UTF-8 を Shift_JIS と誤認し文字化けする問題の回避 |
| 区切り文字 | `,`（カンマ） | RFC 4180 標準、CSV の "C" |
| 改行コード | `\r\n`（CRLF） | RFC 4180 準拠、Excel 互換 |
| クォート | フィールドに `,` / `\r` / `\n` / `"` が含まれる場合、そのフィールド全体を `"` で囲む | RFC 4180 標準 |
| エスケープ | クォート内の `"` は `""` と重ねる | RFC 4180 標準 |
| ヘッダ行 | あり（1 行目） | Excel / スプレッドシートでの視認性 |

### 実装方針

Python 標準ライブラリの `csv` モジュール（`csv.writer` + `io.StringIO`）を使用する。上記ルールはデフォルトで対応されるため、自前で quote/escape ロジックを書かない。

```python
import csv
import io

def format_as_csv(viewpoints):
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(_build_header())
    for vp in viewpoints:
        writer.writerow(_viewpoint_to_row(vp))
    return "\ufeff" + buf.getvalue()
```

### ヘッダ列（案）

| 列名 | 内容 | 備考 |
|---|---|---|
| カテゴリ | 観点のカテゴリ（正常系 / 異常系 / 境界値 等） | Phase 1 で実フィールド名を確認 |
| 観点タイトル | 観点の短い表題 | 〃 |
| 説明 | 観点の詳細 | 〃 |
| 優先度 | 優先度（High / Middle / Low 等） | 〃 |

**注記**：列名と対応フィールドは `Viewpoint` の実際のスキーマに合わせる。Phase 1 の repo-explorer が `app/domain/models.py` を調査して確定する。

---

## 5. Streamlit UI への組み込み

### 配置

`app/streamlit_app.py` の既存 Markdown ダウンロードボタンの **直後** に配置する。具体的な行番号は Phase 1 の repo-explorer が特定する。

### UI コード（案）

```python
csv_text = format_as_csv(viewpoints)
st.download_button(
    label="CSV ダウンロード",
    data=csv_text.encode("utf-8"),
    file_name="viewpoints.csv",
    mime="text/csv",
)
```

### 表示条件

既存の Markdown ダウンロードボタンと同じ条件下で表示する（観点生成が成功したとき）。
エラー時や未生成時は表示しない。

---

## 6. 例外設計

CLAUDE.md の例外設計ルールに従う。

| 状況 | 挙動 |
|---|---|
| `viewpoints` が `None` | `InputValidationError("viewpoints must not be None")` を raise |
| `viewpoints` の要素が `Viewpoint` 型でない | `InputValidationError(...)` を raise |
| `viewpoints` が空リスト | エラーにせず、ヘッダ行のみを返す（正常動作） |
| その他予期しない例外 | そのまま伝播させる（握りつぶし禁止） |

---

## 7. テスト観点（叩き台）

**以下は叩き台。Phase 1 の test-designer が強化・補完する。**

### 7-1. 正常系

- 観点 1 件を含むリスト → ヘッダ行 + 1 行の CSV 文字列
- 観点 3 件を含むリスト → ヘッダ行 + 3 行の CSV 文字列
- 戻り値の先頭が BOM（`\ufeff`）であること

### 7-2. 異常系

- `None` を渡す → `InputValidationError`
- リスト内に `Viewpoint` 以外の型が混在 → `InputValidationError`

### 7-3. 境界値

- 空リスト → ヘッダ行のみ（エラーにならない）
- フィールドにカンマ `,` を含む → 該当フィールドが `"` で囲まれている
- フィールドに改行 `\n` を含む → 該当フィールドが `"` で囲まれている
- フィールドにダブルクォート `"` を含む → `""` にエスケープされている
- 日本語（ひらがな / カタカナ / 漢字 / 絵文字）→ UTF-8 で正しく出力される
- 長いテキスト（1000 文字超）を含む観点 → 正しく 1 フィールドに収まる

### 7-4. 仕様確認

- 行末が `\r\n`（CRLF）であること
- Excel で開いて文字化けしないこと（BOM 効果の確認、手動または Python 側で `.encode("utf-8")` → `.decode("utf-8-sig")` で BOM 検出）

### 7-5. 大量データ

- 観点 1000 件 → 正常に CSV 化される（パフォーマンス観点の叩き台。Phase 1 で MVP に過剰か判断）

---

## 8. 既存パターンとの整合メモ

**以下は推定。Phase 1 の repo-explorer が検証する。**

| 項目 | 推定される既存パターン | 確認ポイント |
|---|---|---|
| ファイル配置 | `app/services/` 配下 | markdown_formatter.py と並列配置で OK か |
| 関数形式 | 純粋関数（副作用なし） | markdown_formatter.py が純粋関数か |
| 例外の raise 位置 | 関数先頭で引数バリデーション | markdown_formatter.py の実装パターンを踏襲 |
| テスト配置 | `tests/services/test_csv_formatter.py` | CLAUDE.md の配置ルール通り |

---

## 9. 実装後の完了条件

- [ ] `app/services/csv_formatter.py` が存在し、`format_as_csv` が公開されている
- [ ] `tests/services/test_csv_formatter.py` が存在し、セクション 7 の観点を網羅している
- [ ] `python3 -m pytest tests/ -x -q` が全件 pass
- [ ] `app/streamlit_app.py` に CSV ダウンロードボタンが追加されている
- [ ] Playwright MCP でダウンロードボタンが表示・動作することを確認
- [ ] 実際にダウンロードした CSV を Excel で開き、文字化けしないことを手動確認

---

## 10. Phase 1 で Subagent が補強する箇所（サマリ）

| 担当 Subagent | 補強内容 |
|---|---|
| `repo-explorer` | ・`Viewpoint` の実フィールド名と型（セクション 3・4 のヘッダ列・ヘルパー関数）<br>・`markdown_formatter.py` の関数設計パターン（セクション 8）<br>・`streamlit_app.py` の既存 Markdown ボタンの行番号と配置コンテキスト（セクション 5） |
| `test-designer` | ・テスト観点の追加・削減（セクション 7）<br>・大量データ観点の要否判断（7-5）<br>・BOM 検証方法の具体化（7-4）<br>・過剰な観点の削減（MVP スコープ調整） |

Phase 2（fan-in）で親がこれらを反映し、本設計書を **v2** に更新してから Phase 3（実装）に進む。

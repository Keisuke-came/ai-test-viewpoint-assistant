# CSV エクスポート機能 設計書（ミニ設計書）

> 対象モジュール：`app/services/csv_formatter.py`（新規）
> 関連：`app/services/markdown_formatter.py`（既存・参照パターン）
> ステータス：**v2（確定版）** — Phase 1 Subagent（repo-explorer / test-designer）の調査結果を fan-in して更新

## v2 の変更点（Phase 2 fan-in による更新）

| セクション | 変更内容 |
|---|---|
| セクション 2 | `List[Viewpoint]` の型が確定済み（推定→確定）|
| セクション 4 | `priority` の実値が `高/中/低`（英語表記ではない）と確定 |
| セクション 5 | 挿入位置を確定：`render_result` 末尾（行 141 直後）。「既存 Markdown ダウンロードボタン」は実際には `st.text_area`（ダウンロードボタンではない）。`grouped_viewpoints` のフラット化が必要 |
| セクション 7 | テスト観点を test-designer の結果で更新：ヘッダ列・フィールドマッピング検証を追加、1000 件パフォーマンステストを削除（MVP スコープ外） |
| セクション 8 | `markdown_formatter.py` にバリデーションがないことを確定。csv_formatter のバリデーションは設計書固有の新規追加要件として明記 |

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
- 型：`List[Viewpoint]`（確定）

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
| 優先度 | 優先度（`高` / `中` / `低`） | `priority: Literal["高", "中", "低"]` の実値をそのまま出力 |

**確定事項**：`priority` の実値は日本語固定（`高/中/低`）。英語変換は行わず、そのまま CSV に出力する。

---

## 5. Streamlit UI への組み込み

### 配置

`app/streamlit_app.py` の `render_result` 関数末尾（行 141 の直後）に配置する。

**確定事項**：
- 設計書 v1 で「既存 Markdown ダウンロードボタン」と書いた箇所は、実際には `st.text_area`（コピー用テキストエリア、行 136-141）であり `st.download_button` は存在しない
- `render_result` は行 109-141。CSV ボタンは 142 行目以降に追記する
- `render_result` が受け取る `DisplayResult` は `grouped_viewpoints: dict[str, list[Viewpoint]]` のみ保持。フラットな `List[Viewpoint]` に変換してから `format_as_csv` に渡す

### UI コード（案）

```python
from app.services.csv_formatter import format_as_csv

# grouped_viewpoints をフラット化して csv_formatter に渡す
viewpoints = [vp for vps in result.grouped_viewpoints.values() for vp in vps]
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

## 7. テスト観点（v2 確定版）

**test-designer の調査結果を反映して確定。モック不要（純粋関数のため実装を直接呼ぶ）。**

### 7-1. 正常系（追加あり）

| # | 観点名 | 期待動作 |
|---|---|---|
| N-1 | 1 件リストの行数 | ヘッダ行 + データ 1 行、計 2 行 |
| N-2 | 3 件リストの行数 | ヘッダ行 + データ 3 行、計 4 行 |
| N-3 | BOM 先頭付与（文字）| 戻り値先頭文字が `"\ufeff"` |
| N-4 | BOM 先頭付与（バイト列）| `result.encode("utf-8")` 先頭 3 バイトが `b"\xef\xbb\xbf"` |
| N-5 | 戻り値の型 | `isinstance(result, str)` が True |
| N-6 | ヘッダ列名 | 1 行目が「カテゴリ,観点タイトル,説明,優先度」の 4 列 |
| N-7 | フィールドマッピング | `category/title/description/priority` が対応する列に正しく出力される |
| N-8 | priority 全パターン | `高/中/低` がそれぞれそのまま出力される |

### 7-2. 異常系（追加あり）

| # | 観点名 | 期待動作 |
|---|---|---|
| E-1 | `None` を渡す | `InputValidationError` |
| E-2 | 要素に `dict` が混在 | `InputValidationError` |
| E-3 | 要素に `None` が混在 | `InputValidationError` |
| E-4 | 要素に `str` が混在 | `InputValidationError` |

### 7-3. 境界値（一部削減）

| # | 観点名 | 期待動作 |
|---|---|---|
| B-1 | 空リスト | エラーにならずヘッダ行のみ返す |
| B-2 | 空リストの行数 | `\r\n` split で 1 行（ヘッダのみ） |
| B-3 | フィールドにカンマ含む | 該当フィールドが `"` で囲まれる |
| B-4 | フィールドに `\n` 含む | 該当フィールドが `"` で囲まれる |
| B-5 | フィールドにダブルクォート含む | `""` にエスケープされる |
| B-6 | 日本語フィールド | ひらがな / カタカナ / 漢字が文字化けせず出力される |
| B-7 | フィールド値が空文字列 | エラーにならず空フィールドとして出力される |
| B-8 | 1000 文字超のフィールド | エラーにならず 1 フィールドに収まる（フィールド長境界値） |

*削除*: 絵文字フィールド（Excel バージョン依存で合否判定不可）

### 7-4. 仕様確認（具体化）

| # | 観点名 | 期待動作 |
|---|---|---|
| S-1 | 行末が CRLF | `"\r\n"` で split したとき期待行数と一致する |
| S-2 | BOM を除いた本体の符号化健全性 | `result[1:].encode("utf-8").decode("utf-8")` が例外なく通る |
| S-3 | LF 単独が含まれない | `\r\n` 以外の改行コードが本体に含まれない |

### 7-5. 大量データ（削除）

MVP スコープ外として削除。理由：計算量 O(n) で自明・パフォーマンス基準未定義・CI 速度への影響。
将来要件化した時点で `tests/performance/` に追加する。

---

## 8. 既存パターンとの整合メモ

**repo-explorer の調査結果で確定済み。**

| 項目 | 確定値 | 備考 |
|---|---|---|
| ファイル配置 | `app/services/` 配下 | `markdown_formatter.py` と並列配置で OK |
| 関数形式 | 純粋関数（副作用なし） | `markdown_formatter.py` は純粋関数であることを確認済み |
| 例外の raise | **既存パターンにはない。csv_formatter 固有の新規追加要件** | `markdown_formatter.py` は引数バリデーションなし・例外 raise なし。csv_formatter の `InputValidationError` 設計は設計書セクション 6 に基づく独自要件 |
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

**v2 で解決済み。** Phase 1 の両 Subagent が独立して調査し、Phase 2 の親セッションが統合・確定させた。

| 担当 Subagent | 補強内容 | 結果 |
|---|---|---|
| `repo-explorer` | `Viewpoint` の実フィールド名と型、`markdown_formatter.py` のパターン、streamlit 挿入行番号 | すべて確定済み（本設計書 v2 に反映）|
| `test-designer` | テスト観点の追加・削減、1000 件の要否、BOM/CRLF 検証の具体化 | セクション 7 v2 に反映済み |

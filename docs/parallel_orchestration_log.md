# 並列オーケストレーション実行ログ

> ブランチ：`feature/csv-export-parallel-orchestration`
> 実施日：2026-04-24
> 目的：fan-out / fan-in パターンの実地体得

---

## 1. Phase 0 の設計書ドラフトが果たした役割

`docs/csv_export_mini_design.md` (v1) を事前に配置することで、2 つの Subagent に**共通の軸**を与えることができた。

具体的には：

- `repo-explorer` は「セクション 4 のヘッダ列案が実データと整合するか」「セクション 8 の推定が正しいか」という**検証タスク**として問いを立てられた。設計書がなければ「何を調査すべきか」から考える必要があり、報告内容が散漫になっていた可能性が高い。
- `test-designer` は「セクション 7 の叩き台を補強・削減する」という**差分設計タスク**として問いを立てられた。ゼロから観点を洗い出すより、「この観点は残すべきか削るべきか」の判断に集中できた。

**設計書がなければ Subagent は一から探索するしかない。設計書があることで「答え合わせ」と「差分補強」に特化できる。**

---

## 2. Phase 1 の並列起動ログ（fan-out 成立の証跡）

以下の 2 つのエージェント呼び出しが**同一ターン内で発行**された：

| エージェント | 起動タイミング | 完了時間（体感） |
|---|---|---|
| `repo-explorer` | 同一ターン（1回目のツール呼び出し） | 約 51 秒 |
| `test-designer` | 同一ターン（2回目のツール呼び出し） | 約 80 秒 |

Claude Code のターンログには両エージェントの起動が 1 ターン内に並んで表示された。これが **fan-out が成立した証拠**。

仮に逐次実行した場合：51 + 80 = 131 秒
並列実行した場合：max(51, 80) ≒ 80 秒
**約 40% の時間削減**（両タスクが独立していたため）

---

## 3. Phase 2 で親セッションが下した判断（fan-in）

### 矛盾の検出

2 つの Subagent の出力に**直接の矛盾はなかった**。

強いて言えば以下の潜在的不整合があったが、親が補足情報として解決した：

- `repo-explorer` が「`markdown_formatter.py` にバリデーションなし」と報告
- `test-designer` が「E-1〜E-4（異常系テスト）」を設計（バリデーションが存在する前提）

→ 親判断：csv_formatter のバリデーションは markdown_formatter のパターンとは無関係に、設計書セクション 6 の独自要件として追加する。矛盾ではなく「既存パターンを踏襲しない明示的な設計判断」として確定。

### 推定を確定値に置き換えた項目

| 設計書 v1 の推定 | 確定値（Phase 2） |
|---|---|
| `List[Viewpoint]`（推定） | 確定。`app/domain/models.py` で確認済み |
| `priority` の値（High / Middle / Low 等） | 日本語固定（`高/中/低`）と確定 |
| streamlit の挿入位置 | `render_result` 末尾（行 141 直後）と確定 |
| markdown_formatter のバリデーションパターン | バリデーションなしと確定。csv_formatter のバリデーションは新規追加要件 |
| 「既存 Markdown ダウンロードボタン」 | 実際には `st.text_area`（ダウンロードボタンではない）と確定 |

---

## 4. Phase 4 reviewer の指摘と親の判断

reviewer が以下を指摘：

| 指摘種別 | 内容 | 親の判断 |
|---|---|---|
| Critical | BOM が二重付与される | **誤検知として棄却**。`"\ufeff".encode("utf-8")` = `b"\xef\xbb\xbf"`（1個）。`utf-8-sig` codec とは異なる |
| Should Fix | `Optional[List[Viewpoint]]` 型ヒント | 採用して修正 |
| Should Fix | `render_result` 内の例外ハンドリング | 棄却。`grouped_viewpoints` の要素は必ず `Viewpoint` インスタンスであり、`InputValidationError` が発生するパスが存在しない |
| Suggestion | `test_empty_string_field` のアサーション弱い | 採用して修正 |

reviewer が「Critical」と判定した指摘が実際には誤検知だった点が学習ポイント。**Subagent の判断はそのまま採用せず、親（メインセッション）が検証・判断する**という fan-in の原則が重要であることが体感できた。

---

## 5. 逐次実行と比べて何が変わったか（所感）

### 時間的メリット（体感）

Phase 1 の 2 エージェント（repo-explorer / test-designer）を逐次実行した場合、合計 130 秒程度かかる。並列化で最長の 80 秒に短縮。フェーズ数が増えるほど積み上がる効果がある。

### 品質的メリット

- 設計書 v1 を書いてから Subagent に検証させることで、**「推定」と「確定」の境界が明確になった**。v2 は単なる情報追加ではなく、v1 の仮説を検証・棄却した結果物になっている。
- test-designer が「1000 件パフォーマンステストは MVP 過剰」と独立して判断したことで、その判断に根拠が生まれた。自分一人で判断するよりも、設計書への記載理由が明確になる。

### コンテキスト汚染の抑制

repo-explorer と test-designer は互いの結果を知らない。これにより：

- repo-explorer が「markdown_formatter にバリデーションなし」という事実を報告しても、test-designer の異常系テスト設計に干渉しない
- 各エージェントが独立した視点で調査できる

---

## 6. このパターンを別ユースケースに転用するとしたら

### 例：KPI 自動集計システムの設計

```
Phase 0: 集計仕様書のドラフト（どのテーブルの何を集計するか）
Phase 1 (fan-out):
  - data-explorer: 実テーブルのスキーマ・データ量・NULL 率を調査
  - alert-designer: 集計失敗・異常値検知の観点を設計
Phase 2 (fan-in): 親が仕様書を確定版に更新
Phase 3: 実装（逐次）
Phase 4: reviewer でレビュー
```

転用のポイント：

1. **共通入力（仕様書ドラフト）を事前に用意する**：Subagent への「軸」になる
2. **A の結論に B が依存しないか確認する**：今回は repo-explorer の結果を test-designer が参照しないことを確認してから並列化した
3. **fan-in は必ず親が担う**：Subagent 同士で結果をやりとりさせると「依存」になり並列化の意味がなくなる
4. **reviewer の判定も親が再検証する**：Subagent は独立したコンテキストで判断するため、プロジェクト固有の前提知識が抜けることがある

---

## コミット履歴（Phase 別）

| Phase | コミット |
|---|---|
| Phase 0 | `docs: add CSV export mini design draft (v1, to be refined by subagents)` |
| Phase 2 | `docs: refine CSV export design to v2 based on parallel subagent investigation` |
| Phase 3-1 | `feat: add csv_formatter for viewpoint export` |
| Phase 3-2 | `test: add csv_formatter unit tests` |
| Phase 3-3 | `feat: add CSV download button to streamlit UI` |
| Phase 4 | `fix: use Optional type hint in format_as_csv and strengthen empty field assertion` |
| Phase 5 | `docs: add parallel orchestration execution log` |

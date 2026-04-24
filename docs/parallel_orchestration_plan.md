# Subagent 並列オーケストレーション実行計画書（v2）

> 機能：観点生成結果の CSV エクスポート
> ブランチ：`feature/csv-export-parallel-orchestration`
> 目的：**fan-out / fan-in の実地体得**（機能そのものは学習の器）
>
> **v2 の変更点**：Phase 0（設計書ドラフト作成）を追加し、Phase 1 の Subagent の役割を「検証・補強」に明確化

---

## 0. このドキュメントの使い方

1. リポジトリのルートで `git switch -c feature/csv-export-parallel-orchestration` を実行
2. このファイルを `docs/parallel_orchestration_plan.md` として保存
3. 添付の設計書ドラフトを `docs/csv_export_mini_design.md` として保存
4. Claude Code セッションを起動し、Plan Mode で「`docs/parallel_orchestration_plan.md` に沿って進めてください」と指示
5. Phase 1 の並列起動プロンプトは、**親セッションに丸ごと貼る**（Plan Mode 抜けた後）

---

## 1. 前提と設計原則

### 前提

- 既存の Subagents：`repo-explorer` / `test-designer` / `reviewer`（`.claude/agents/` 配下）
- 既存の Skill：`/pytest-impl`（`.claude/skills/pytest-impl/SKILL.md`）、`/design-to-code`（`.claude/skills/design-to-code/SKILL.md`）
- 既存の formatter：`app/services/markdown_formatter.py`、`app/services/result_formatter.py`
- **事前作成物：`docs/csv_export_mini_design.md`（v1 ドラフト）**

### 設計原則（公式仕様に準拠）

- Subagent は Task tool 経由で起動される。**1 つのアシスタントターンで複数の Task を発行すると並列実行される**
- Subagent は独立したコンテキストウィンドウを持つ。互いの結果は見えない
- 並列化の判定基準：**「A の結論に B が依存するか」** → 依存なしなら並列、依存ありなら逐次
- **共通入力を持つことは依存ではない**（両 Subagent が同じ設計書を参照することは並列化を妨げない）
- `.claude/agents/*.md` を新規追加した場合はセッション再起動が必要（今回は既存 Subagent のみ使うので不要）

---

## 2. 全体フロー

```
Phase 0 : 設計書ドラフト作成（事前）
  docs/csv_export_mini_design.md (v1 = 叩き台)
       ↓
Phase 1 : fan-out(並列)
  親 ──→ repo-explorer    （設計書の「既存パターンとの整合」セクションを検証）
      ──→ test-designer   （設計書の「テスト観点」セクションを補強）
       ↓
Phase 2 : fan-in(統合)
  親が両結果を統合 → docs/csv_export_mini_design.md を v2 に更新
       ↓
Phase 3 : 実装(逐次)
  /design-to-code → csv_formatter.py 実装
  /pytest-impl    → テスト実装
  手動             → streamlit_app.py に CSV ダウンロードボタン追加
       ↓
Phase 4 : 検証
  reviewer → git diff レビュー
       ↓
Phase 5 : 観測・ログ化
  docs/parallel_orchestration_log.md に並列起動の証跡を残す
```

---

## 3. Phase 0 — 設計書ドラフト作成

添付の `csv_export_mini_design.md` をそのまま `docs/csv_export_mini_design.md` として配置し、**v1 ドラフト**としてコミットする。

```bash
git add docs/csv_export_mini_design.md
git commit -m "docs: add CSV export mini design draft (v1, to be refined by subagents)"
```

このドラフトは **意図的に「推定」「叩き台」として書かれている** 。Phase 1 の Subagent がここに書かれた推定を検証し、叩き台を強化する。

**Phase 0 の完了条件**

- [ ] `docs/csv_export_mini_design.md` がリポジトリに存在する
- [ ] 設計書内に「Phase 1 で補強する箇所」のサマリ（セクション 10）が含まれている
- [ ] v1 ドラフトがコミットされている

---

## 4. Phase 1 — fan-out(並列検証・補強)

### 4-1. 親セッションから発行するプロンプト（これを丸ごと貼る）

```
これから Subagent 並列オーケストレーションの学習のため、fan-out を実行します。

前提：
- 設計書 docs/csv_export_mini_design.md (v1) が既に存在します
- この設計書は「叩き台」であり、推定を含みます
- セクション 10 に「Phase 1 で補強する箇所」が明示されています

以下の 2 つのタスクを、**同一ターン内で Task tool を 2 回発行して並列に起動**してください。
結果が両方返ってくるまで、統合判断は保留してください。

---

【Task 1：repo-explorer に依頼】

前提：docs/csv_export_mini_design.md を読んでから開始してください。

対象：
- app/domain/models.py
- app/services/markdown_formatter.py
- app/services/result_formatter.py
- app/streamlit_app.py（formatter の呼び出し箇所のみ）

報告してほしい内容：
1. Viewpoint（観点）の実際のフィールド名と型
   - 設計書のヘッダ列案（カテゴリ / 観点タイトル / 説明 / 優先度）が実データと整合するか
   - 差分があれば具体的なフィールド名を提示
2. markdown_formatter.py の公開関数シグネチャと実装パターン
   - 純粋関数か / 引数バリデーションの位置 / 例外 raise の有無
   - csv_formatter.py が踏襲すべきパターン
3. streamlit_app.py から markdown_formatter を呼び出している箇所の行番号と前後コンテキスト
   - CSV ダウンロードボタンをどこに追加すべきかの具体指示
4. 設計書セクション 8「既存パターンとの整合メモ」の推定が正しいかの検証結果

制約：
- 他の Subagent の作業は参照しない（独立して調査する）
- ファイルを書き換えない（read-only 調査）
- 報告はセクション番号を付けて構造化して返す

---

【Task 2：test-designer に依頼】

前提：docs/csv_export_mini_design.md を読んでから開始してください。
特にセクション 7「テスト観点（叩き台）」を出発点にしてください。

補強してほしい内容：
1. セクション 7 の観点で、MVP に対して**過剰なもの**があれば削減案を提示
   - 例：観点 1000 件の大量データテストが MVP に必要か
2. セクション 7 に**欠落している観点**があれば追加
   - 例：CRLF 行末の具体的な検証方法、BOM 検出の具体的な実装方法
3. モック方針
   - csv.writer や io.StringIO をモックすべきか、実装を直接呼ぶか（CLAUDE.md のモック方針に従う）
4. Excel 互換性の確認観点を、pytest で自動化可能な形に具体化
   - 「Excel で開いて文字化けしない」は手動確認だが、BOM 有無は自動テスト可能

出力形式：
- セクション 7 の各サブセクション（7-1〜7-5）ごとに「追加 / 削減 / 変更なし」の判定を付ける
- 最終的に MVP 版のテスト観点リストを「観点名 / 期待動作 / 備考」の 3 列表で提示

制約：
- 他の Subagent の作業は参照しない（独立して設計する）
- 実装コードは書かない（観点整理のみ）

---

両タスクが完了したら、Phase 2(統合)に進みます。
```

### 4-2. 観測ポイント（並列実行の証跡）

起動直後、Claude Code のターンログに以下のような表示が **1 ターン内に 2 つ並ぶ** ことを確認する：

```
● Task(repo-explorer: ...)
● Task(test-designer: ...)
```

→ これが **fan-out が成立している証拠**。逐次だと `Task(A)` が完了してから `Task(B)` が表示される。
スクリーンショットまたはテキストログを `docs/parallel_orchestration_log.md` に保存する。

---

## 5. Phase 2 — fan-in(統合)

### 5-1. 親が担う統合判断チェックリスト

両 Subagent の結果が揃ったら、親（＝ Claude Code のメインセッション）に以下を依頼する：

```
両 Subagent の結果を統合して、以下のチェックリストに沿って判断してください。

1. [矛盾検出] repo-explorer が特定した既存パターンと、test-designer の観点に食い違いはないか？
   - 例：既存 markdown_formatter が None 入力で例外を raise しているのに、test-designer が空文字列返却を前提にしていないか
2. [推定の確定] 設計書 v1 で「推定」と書いた箇所を、repo-explorer の調査結果で確定値に置き換える
   - Viewpoint の実フィールド名、markdown_formatter のパターン、streamlit_app.py の行番号
3. [観点の確定] test-designer の追加・削減判断を反映し、MVP 版のテスト観点リストを確定させる
4. [スコープ最終調整] Phase 3 の実装範囲を確定（実装対象外の観点があれば docs に記録）

統合結果を docs/csv_export_mini_design.md に v2 として上書きしてください。
変更箇所は冒頭に「v2 の変更点」として明示してください。
```

### 5-2. fan-in がうまく機能しているかの判定

- 設計書 v2 に **両 Subagent の出力がどちらも反映されている** こと
- v1 で「推定」と書かれた箇所が **v2 では確定値に置き換わっている** こと
- 矛盾があった場合に **親が判断を下している** こと（決定理由が docs に残っている）
- Subagent 同士で直接の参照がないこと（あったらそれは並列化の前提が崩れている）

### 5-3. コミット

```bash
git add docs/csv_export_mini_design.md
git commit -m "docs: refine CSV export design to v2 based on parallel subagent investigation"
```

---

## 6. Phase 3 — 実装(逐次)

### 6-1. `/design-to-code` で csv_formatter.py を実装

```
/design-to-code docs/csv_export_mini_design.md app/services/csv_formatter.py
```

設計書 v2 をそのまま入力として使える。Phase 0 〜 2 で設計書を洗練させた成果がここで生きる。

### 6-2. `/pytest-impl` でテストを実装

```
/pytest-impl app/services/csv_formatter.py
```

設計書 v2 のセクション 7（テスト観点）を Skill が参照する。

### 6-3. Streamlit UI への組み込み（手動）

設計書 v2 のセクション 5 で確定した行番号に従い、`app/streamlit_app.py` に CSV ダウンロードボタンを追加。

**注意**：この編集で PostToolUse Hook が発火し、pytest が自動実行される。
テストが通らない場合はここで止めて修正してから進む。

### 6-4. Playwright MCP で UI 動作確認

```
localhost:8501 を開いて、観点生成を実行し、
CSV ダウンロードボタンが表示されること、および押下で CSV がダウンロードされることを確認してください。
```

手動で Excel を開いて文字化けしないことも確認する（これは自動化対象外と Phase 2 で確定済み）。

---

## 7. Phase 4 — レビュー（reviewer）

```
git diff main...HEAD の内容を reviewer Subagent にレビューさせてください。
観点：
- CLAUDE.md の禁止事項（except Exception: pass / print() デバッグ / テストなしロジック変更）に違反していないか
- csv_formatter.py が既存 markdown_formatter のパターンと一貫しているか（設計書 v2 のセクション 8 との整合）
- テストが設計書 v2 のセクション 7 を網羅しているか
- BOM 付き UTF-8 と CRLF 行末の仕様が実装で担保されているか
```

---

## 8. Phase 5 — 観測・ログ化

`docs/parallel_orchestration_log.md` に以下を記録：

1. Phase 0 の設計書ドラフトが果たした役割（Subagent に軸を与えたか）
2. Phase 1 の並列起動ログ（Task が同一ターンに 2 つ並んだ表示）
3. 各 Subagent の実行時間（体感）
4. Phase 2 で親が下した判断（矛盾があれば具体的に、推定を確定値に置き換えた項目のリスト）
5. 逐次でやった場合と比べて何が変わったか（所感）
6. 今回の並列オーケストレーションを、別のユースケースに転用するとしたらどう設計するか

このログ自体が、ポートフォリオの README に「並列オーケストレーションの実運用例」として引用できる資料になる。

---

## 9. コミット戦略

| タイミング | コミットメッセージ |
|---|---|
| Phase 0 完了後 | `docs: add CSV export mini design draft (v1, to be refined by subagents)` |
| Phase 2 完了後 | `docs: refine CSV export design to v2 based on parallel subagent investigation` |
| Phase 3-1 完了後 | `feat: add csv_formatter for viewpoint export` |
| Phase 3-2 完了後 | `test: add csv_formatter unit tests` |
| Phase 3-3 完了後 | `feat: add CSV download button to streamlit UI` |
| Phase 5 完了後 | `docs: add parallel orchestration execution log` |

Phase 4 の reviewer 指摘で修正が入る場合は、該当コミットを amend するのではなく `fix:` プレフィックスで積む。

---

## 10. 完了条件

- [ ] Phase 0：`docs/csv_export_mini_design.md` v1 がコミット済み
- [ ] Phase 1：2 つの Task が同一ターンで並列起動されたログが残っている
- [ ] Phase 2：設計書が v2 に更新され、両 Subagent の出力が反映されている
- [ ] Phase 3：`app/services/csv_formatter.py` と対応する pytest が追加され、全テストがパスする
- [ ] Phase 3：Streamlit UI に CSV ダウンロードボタンが追加され、Playwright MCP で動作確認済み
- [ ] Phase 4：reviewer の指摘がゼロ、または指摘に対応済み
- [ ] Phase 5：`docs/parallel_orchestration_log.md` に並列実行の証跡と所感が残っている
- [ ] PR を作成し、GitHub Actions（pytest + claude-review）が両方 green

---

## 11. 学習の自己チェック

全 Phase 完了後、以下の 4 問に自分の言葉で答えられれば学習目的達成：

1. Q. 今回のフローで、なぜ Phase 1 は並列化できて Phase 3 は並列化できないのか？
2. Q. fan-in の責務を Subagent ではなく親が持つ理由は何か？
3. Q. Phase 0(事前設計書)を置いたことで、Phase 1 の Subagent の仕事はどう変わったか？
4. Q. この並列オーケストレーションのパターンを、別事業（KPI 自動集計）にどう転用できるか？

1 つでも詰まったら、`docs/parallel_orchestration_log.md` の該当 Phase を読み返す。

# **AIテスト観点整理アシスタント 観点生成機能 詳細設計書**

## **1\. 文書概要**

### **1.1 文書名**

AIテスト観点整理アシスタント 観点生成機能 詳細設計書

### **1.2 目的**

本書は、AIテスト観点整理アシスタントにおける最初の中核機能である「観点生成機能」について、実装可能な粒度で詳細設計を定義することを目的とする。

### **1.3 対象機能**

* 仕様入力  
* 入力チェック  
* LLM呼び出し  
* 構造化出力検証  
* 画面表示用整形  
* 結果表示  
* コピー用Markdown生成

### **1.4 前提**

* MVPは Python ベースの軽量構成とする  
* UIは Streamlit を想定する  
* バックエンドロジックは Python モジュールとして分離する  
* LLM は OpenAI API 等のチャット/レスポンスAPIを利用する  
* 永続化は行わない

### **1.5 対象外**

* ログイン  
* 履歴保存  
* ファイルアップロード  
* 複数画面構成  
* 外部チケット連携  
* Excel/CSV出力

---

## **2\. 機能概要**

### **2.1 機能名**

観点生成機能

### **2.2 機能概要**

ユーザーが入力した仕様文・補足情報をもとに、LLM を利用してテスト観点を構造化出力させ、画面上にカテゴリ別で表示する機能。

### **2.3 目的**

* テスト観点のたたき台を短時間で作る  
* 正常系 / 異常系 / 境界値 / 業務ルールなどの整理を支援する  
* 仕様の曖昧点を早期に抽出する

### **2.4 利用者**

* QA担当者  
* 開発者  
* テスト設計担当者

---

## **3\. 採用構成**

## **3.1 技術構成**

* UI: Streamlit  
* アプリケーション: Python 3.11 以上  
* AI連携: OpenAI API  
* スキーマ検証: Pydantic  
* 設定管理: python-dotenv

## **3.2 処理方式**

* 同期処理  
* 1回のボタン押下に対し1回のLLM呼び出し  
* 結果はメモリ上のみ保持

## **3.3 全体処理イメージ**

```
[利用者]
  ↓
[Streamlit画面]
  ↓ 生成ボタン押下
[ViewpointGenerationService]
  ├─ 入力チェック
  ├─ プロンプト生成
  ├─ LLM呼び出し
  ├─ 構造化出力検証
  ├─ 表示整形
  └─ Markdown整形
  ↓
[Streamlit画面へ結果返却]
```

---

## **4\. 画面詳細設計**

## **4.1 画面ID**

SCR-01

## **4.2 画面名**

観点生成画面

## **4.3 画面項目一覧**

### **入力エリア**

| 項目ID | 項目名 | 型 | 必須 | 初期値 | 備考 |
| ----- | ----- | ----- | ----- | ----- | ----- |
| SCR-IN-01 | 対象種別 | selectbox | ○ | `screen` | 画面 / API / バッチ / チケット / その他 |
| SCR-IN-02 | 仕様テキスト | textarea | ○ | 空 | 最低20文字 |
| SCR-IN-03 | 補足情報 | textarea | \- | 空 | 任意 |

### **操作エリア**

| 項目ID | 項目名 | 種別 | 備考 |
| ----- | ----- | ----- | ----- |
| SCR-BTN-01 | 観点を生成する | button | メイン操作 |
| SCR-BTN-02 | クリア | button | 入力・結果・メッセージ初期化 |
| SCR-BTN-03 | Markdownをコピー | button | 結果生成後のみ活性 |

### **表示エリア**

| 項目ID | 項目名 | 内容 |
| ----- | ----- | ----- |
| SCR-OUT-01 | サマリ | 仕様全体の要約 |
| SCR-OUT-02 | テスト観点 | カテゴリ別一覧 |
| SCR-OUT-03 | 曖昧点・確認事項 | 要確認事項一覧 |
| SCR-OUT-04 | 注意事項 | notes表示 |
| SCR-MSG-01 | エラーメッセージ | 入力/API/応答形式エラー |
| SCR-MSG-02 | ステータスメッセージ | 生成中/成功など |

## **4.4 画面状態**

| 状態ID | 状態名 | 説明 |
| ----- | ----- | ----- |
| ST-01 | 初期状態 | 入力前 |
| ST-02 | 入力中 | ユーザーが入力している状態 |
| ST-03 | 生成中 | AI呼び出し中 |
| ST-04 | 生成成功 | 結果表示中 |
| ST-05 | エラー | エラー表示中 |

## **4.5 状態遷移**

```
初期状態 → 入力中 → 生成中 → 生成成功
                    └→ エラー
生成成功 → 入力中
エラー → 入力中
クリア押下 → 初期状態
```

---

## **5\. 入出力詳細設計**

## **5.1 入力項目仕様**

### **5.1.1 対象種別**

* 物理名: `target_type`  
* 型: `str`  
* 必須: 必須  
* 許容値:  
  * `screen`  
  * `api`  
  * `batch`  
  * `ticket`  
  * `other`

### **5.1.2 仕様テキスト**

* 物理名: `spec_text`  
* 型: `str`  
* 必須: 必須  
* 前後空白除去後の最小文字数: 20  
* 最大文字数: MVPでは明確制限なし。ただし長文時の注意表示は将来拡張

### **5.1.3 補足情報**

* 物理名: `supplemental_text`  
* 型: `str | None`  
* 必須: 任意  
* 未入力時は空文字として扱う

## **5.2 出力項目仕様**

### **5.2.1 LLM構造化出力**

```json
{
  "summary": "string",
  "viewpoints": [
    {
      "category": "string",
      "title": "string",
      "description": "string",
      "priority": "高"
    }
  ],
  "ambiguities": ["string"],
  "notes": ["string"]
}
```

### **5.2.2 アプリ内部表示用出力**

```py
class DisplayResult:
    summary: str
    grouped_viewpoints: dict[str, list[Viewpoint]]
    ambiguities: list[str]
    notes: list[str]
    markdown_text: str
```

---

## **6\. データモデル詳細設計**

## **6.1 InputData**

```py
from pydantic import BaseModel, Field
from typing import Literal

class InputData(BaseModel):
    target_type: Literal["screen", "api", "batch", "ticket", "other"]
    spec_text: str = Field(min_length=20)
    supplemental_text: str = ""
```

## **6.2 Viewpoint**

```py
from pydantic import BaseModel
from typing import Literal

class Viewpoint(BaseModel):
    category: str
    title: str
    description: str
    priority: Literal["高", "中", "低"]
```

## **6.3 LlmResult**

```py
from pydantic import BaseModel

class LlmResult(BaseModel):
    summary: str
    viewpoints: list[Viewpoint]
    ambiguities: list[str]
    notes: list[str]
```

## **6.4 DisplayResult**

```py
from pydantic import BaseModel

class DisplayResult(BaseModel):
    summary: str
    grouped_viewpoints: dict[str, list[Viewpoint]]
    ambiguities: list[str]
    notes: list[str]
    markdown_text: str
```

---

## **7\. カテゴリ・優先度仕様**

## **7.1 許容カテゴリ**

表示順も兼ねて以下の順序で扱う。

1. 正常系  
2. 異常系  
3. 境界値  
4. 必須入力・入力制約  
5. 業務ルール  
6. 権限・ロール  
7. 状態遷移  
8. 外部連携・データ連携  
9. 表示・メッセージ  
10. 非機能上の注意点

## **7.2 不明カテゴリ対応**

* 許容カテゴリ外の文字列が返却された場合は `その他` に丸める  
* MVPでは画面表示を優先し、即エラーにはしない

## **7.3 優先度仕様**

* `高`: 主要ユースケース、業務影響が大きい、障害時影響が大きい  
* `中`: 通常確認すべき標準的観点  
* `低`: 条件付き、補足的観点

## **7.4 優先度ソート順**

* `高` → `中` → `低`

---

## **8\. モジュール詳細設計**

## **8.1 ディレクトリ構成**

```
app/
 ├─ streamlit_app.py
 ├─ services/
 │   ├─ viewpoint_generation_service.py
 │   ├─ prompt_builder.py
 │   ├─ result_formatter.py
 │   └─ markdown_formatter.py
 ├─ llm/
 │   ├─ openai_client.py
 │   └─ schemas.py
 ├─ domain/
 │   └─ models.py
 ├─ utils/
 │   ├─ input_validator.py
 │   └─ category_utils.py
 └─ config/
     └─ settings.py
```

## **8.2 `streamlit_app.py`**

### **役割**

* UI描画  
* 入力受付  
* ボタン押下イベント処理  
* 結果表示  
* エラーメッセージ表示

### **主な関数案**

* `render_page()`  
* `render_input_form()`  
* `render_result(display_result)`  
* `handle_generate()`  
* `handle_clear()`

## **8.3 `viewpoint_generation_service.py`**

### **役割**

観点生成処理全体のオーケストレーションを行う。

### **公開メソッド**

```py
class ViewpointGenerationService:
    def generate(self, input_data: InputData) -> DisplayResult:
        ...
```

### **処理内容**

1. 入力チェック  
2. プロンプト生成  
3. LLM呼び出し  
4. 構造化出力検証  
5. カテゴリ・優先度整形  
6. Markdown生成  
7. `DisplayResult` 返却

## **8.4 `prompt_builder.py`**

### **役割**

LLMに送る system / user プロンプトを構築する。

### **公開メソッド**

```py
def build_system_prompt() -> str: ...
def build_user_prompt(input_data: InputData) -> str: ...
```

## **8.5 `openai_client.py`**

### **役割**

OpenAI API 呼び出しを行う。

### **公開メソッド**

```py
class OpenAiClient:
    def generate_viewpoints(self, system_prompt: str, user_prompt: str) -> str:
        ...
```

### **備考**

* 返却は原則 JSON文字列 または SDK の構造化データ  
* SDK仕様に応じて後で差し替えやすいよう抽象化する

## **8.6 `schemas.py`**

### **役割**

LLMの構造化出力スキーマ定義および検証を行う。

### **公開メソッド**

```py
def parse_llm_result(raw_text: str) -> LlmResult:
    ...
```

## **8.7 `result_formatter.py`**

### **役割**

* カテゴリ順整列  
* 優先度順整列  
* 許容外カテゴリの丸め

### **公開メソッド**

```py
def to_display_result(llm_result: LlmResult) -> DisplayResult:
    ...
```

## **8.8 `markdown_formatter.py`**

### **役割**

コピー用Markdownを生成する。

### **公開メソッド**

```py
def build_markdown_text(llm_result: LlmResult) -> str:
    ...
```

## **8.9 `input_validator.py`**

### **役割**

画面入力値の事前チェックを行う。

### **公開メソッド**

```py
def validate_input(input_data: InputData) -> None:
    ...
```

---

## **9\. 処理詳細設計**

## **9.1 観点生成処理フロー**

```
[1] 生成ボタン押下
  ↓
[2] 画面入力値を InputData に詰める
  ↓
[3] validate_input 実行
   ├─ NG: ValidationError を送出
   └─ OK
  ↓
[4] build_system_prompt 実行
[5] build_user_prompt 実行
  ↓
[6] OpenAiClient.generate_viewpoints 実行
   ├─ NG: API例外
   └─ OK
  ↓
[7] parse_llm_result 実行
   ├─ NG: ResponseFormatError
   └─ OK
  ↓
[8] to_display_result 実行
  ↓
[9] build_markdown_text 実行
  ↓
[10] DisplayResult をUIへ返却
```

## **9.2 クリア処理フロー**

```
[1] クリアボタン押下
  ↓
[2] 入力欄初期化
[3] 結果表示領域初期化
[4] メッセージ初期化
```

---

## **10\. プロンプト詳細設計**

## **10.1 system prompt**

```
あなたはQA支援の専門アシスタントです。
ユーザーが入力した仕様文・チケット文・設計メモをもとに、
テスト観点を日本語で整理してください。

必ず次のルールを守ってください。
- 仕様に明記されていない内容を断定しない
- 不足情報は「要確認事項」として ambiguities に出す
- 実務でレビューしやすい粒度で出力する
- 正常系、異常系、境界値、入力制約、業務ルール、権限、状態遷移、表示・メッセージ等を意識する
- 出力は必ず指定されたJSON形式にする
- 重複観点は極力避ける
```

## **10.2 user prompt テンプレート**

```
以下の仕様情報をもとに、テスト観点を整理してください。

【対象種別】
{target_type}

【仕様テキスト】
{spec_text}

【補足情報】
{supplemental_text}

出力要件:
- summary: 仕様の要点を1〜3行で要約
- viewpoints: テスト観点一覧
  - category: 観点カテゴリ
  - title: 観点タイトル
  - description: 何を確認するか
  - priority: 高 / 中 / 低
- ambiguities: 曖昧点・要確認事項
- notes: 注意事項

必ずJSONのみを返してください。
```

## **10.3 target\_type 表示文変換**

* `screen` → `画面`  
* `api` → `API`  
* `batch` → `バッチ`  
* `ticket` → `チケット`  
* `other` → `その他`

---

## **11\. バリデーション詳細設計**

## **11.1 入力バリデーション**

| チェックID | 対象 | 条件 | エラー文言 |
| ----- | ----- | ----- | ----- |
| VAL-IN-01 | target\_type | 許容値外 | 対象種別が不正です |
| VAL-IN-02 | spec\_text | 空文字 | 仕様テキストを入力してください |
| VAL-IN-03 | spec\_text | trim後20文字未満 | 仕様テキストが短すぎます。もう少し具体的に入力してください |

## **11.2 応答バリデーション**

| チェックID | 対象 | 条件 | 対応 |
| ----- | ----- | ----- | ----- |
| VAL-RES-01 | JSON形式 | JSONとして解釈不能 | 応答形式エラー |
| VAL-RES-02 | summary | 未存在 / 非文字列 | 応答形式エラー |
| VAL-RES-03 | viewpoints | 未存在 / 非配列 | 応答形式エラー |
| VAL-RES-04 | viewpoint.priority | 高中低以外 | 応答形式エラー |
| VAL-RES-05 | ambiguities | 非配列 | 応答形式エラー |
| VAL-RES-06 | notes | 非配列 | 応答形式エラー |

---

## **12\. 例外・エラーハンドリング詳細設計**

## **12.1 例外種別**

### **`InputValidationError`**

* 入力チェック失敗時に送出

### **`LlmApiError`**

* API呼び出し失敗時に送出

### **`ResponseFormatError`**

* LLM応答が想定スキーマを満たさない場合に送出

### **`ApplicationError`**

* その他の想定外エラー

## **12.2 画面表示文言**

| 例外 | 表示文言 |
| ----- | ----- |
| InputValidationError | 入力内容を見直してください |
| LlmApiError | AI呼び出しに失敗しました。時間をおいて再試行してください |
| ResponseFormatError | AI応答形式が不正です。再試行してください |
| ApplicationError | システムエラーが発生しました |

## **12.3 ログ出力方針**

* 例外発生箇所  
* 例外種別  
* 必要に応じてAPI応答概要  
* 個人情報や機密情報は出力しない

---

## **13\. Markdown生成仕様**

## **13.1 生成形式**

```
# サマリ
{summary}

# テスト観点
## 正常系
- ...

## 異常系
- ...

## 境界値
- ...

# 曖昧点・確認事項
- ...

# 注意事項
- ...
```

## **13.2 観点1件の整形ルール**

```
- [{priority}] {title}
  - {description}
```

例:

```
- [高] 必須項目を入力して登録成功すること
  - 名前とメールアドレスを正しく入力した場合に正常登録できること
```

---

## **14\. Streamlit実装仕様**

## **14.1 主なUI部品**

* `st.selectbox`  
* `st.text_area`  
* `st.button`  
* `st.spinner`  
* `st.subheader`  
* `st.markdown`  
* `st.warning`  
* `st.error`  
* `st.success`

## **14.2 session\_state 利用項目**

| キー | 用途 |
| ----- | ----- |
| `target_type` | 対象種別保持 |
| `spec_text` | 仕様テキスト保持 |
| `supplemental_text` | 補足情報保持 |
| `display_result` | 表示結果保持 |
| `error_message` | エラー表示 |
| `status_message` | ステータス表示 |

## **14.3 ボタン押下仕様**

* `観点を生成する`  
  * 生成中は spinner 表示  
* `クリア`  
  * session\_state の対象値を初期化  
* `Markdownをコピー`  
  * MVPではテキスト表示またはコピー領域提供で代替可

---

## **15\. 設定値仕様**

## **15.1 `.env` 項目**

| 項目名 | 必須 | 用途 |
| ----- | ----- | ----- |
| `OPENAI_API_KEY` | ○ | API認証 |
| `OPENAI_MODEL` | ○ | 利用モデル名 |
| `OPENAI_TIMEOUT_SECONDS` | \- | APIタイムアウト秒数 |

## **15.2 `settings.py` 仕様**

* `.env` 読み込み  
* 必須設定値検証  
* モデル名とタイムアウトの取得

---

## **16\. テスト観点（実装者向け）**

## **16.1 正常系**

* 正常な仕様文入力で観点が表示される  
* 補足情報なしでも生成できる  
* viewpoints がカテゴリ別・優先度順で表示される  
* Markdown文字列が生成される

## **16.2 入力異常系**

* 仕様テキスト未入力でエラー表示  
* 仕様テキストが短すぎる場合にエラー表示  
* 不正な対象種別でエラー

## **16.3 外部異常系**

* APIキー未設定で設定エラー  
* LLM API タイムアウトでエラー  
* ネットワーク障害でエラー

## **16.4 応答異常系**

* JSONでない応答を返した場合に ResponseFormatError  
* `priority` が不正値のときエラー  
* `viewpoints` が空配列でも summary/ambiguities が表示可能か確認

## **16.5 UI観点**

* 生成中にローディング表示される  
* エラー後も入力値が保持される  
* クリア押下で状態が初期化される

---

## **17\. 実装順序案**

### **Step 1**

* models.py  
* schemas.py  
* input\_validator.py

### **Step 2**

* prompt\_builder.py  
* markdown\_formatter.py  
* result\_formatter.py

### **Step 3**

* openai\_client.py  
* viewpoint\_generation\_service.py

### **Step 4**

* streamlit\_app.py

### **Step 5**

* 単体テスト  
* 手動テスト

---

## **18\. Claude Code へ渡す実装指示の要点**

この詳細設計を前提に、Claude Code には以下を伝える。

* Angularなし、Python \+ Streamlit の単画面MVPで実装すること  
* まずは観点生成機能のみ作ること  
* 構造化出力は Pydantic で検証すること  
* モジュールを責務分離すること  
* 画面ロジックとLLM呼び出しロジックを分けること  
* 仕様未記載事項は曖昧点として扱うこと

---

## **19\. この詳細設計の完了条件**

* 実装担当がこの文書だけで初期実装に着手できる  
* 入力/出力/例外/モジュール責務が明確になっている  
* Claude Code に対してPlan Modeで実装計画を作らせられる  
* 通常モードで段階実装させられる

---

## **20\. 結論**

観点生成機能は、本アプリの価値を最も端的に示す中核機能である。  
本詳細設計では、MVPとして必要十分な粒度で以下を定義した。

* 入力仕様  
* 出力仕様  
* データモデル  
* 処理フロー  
* プロンプト仕様  
* バリデーション  
* エラーハンドリング  
* UI実装方針  
* 実装順序

これにより、次工程として Claude Code を用いた実装計画作成、および実装着手が可能な状態となる。

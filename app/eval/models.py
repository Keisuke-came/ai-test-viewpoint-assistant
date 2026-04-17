"""評価フレームワークのデータモデル定義。"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Expectations:
    """評価ケースの期待値定義。各フィールドは省略可能で、設定した項目だけ評価される。

    Attributes:
        min_viewpoints: 最低限必要な観点数。0 の場合はチェックしない。
        required_sections: Markdown 出力に含まれるべきセクション文字列のリスト。
        expected_categories_any: いずれか 1 つ以上のカテゴリが出力に含まれるべきリスト。
        expected_categories_all: すべてのカテゴリが出力に含まれるべきリスト。
        expected_keywords_any: いずれか 1 つ以上のキーワードがテキストに含まれるべきリスト。
        expected_keywords_all: すべてのキーワードがテキストに含まれるべきリスト。
        forbidden_keywords: テキストに含まれてはいけないキーワードのリスト。
        notes_presence_expected: True なら notes が 1 件以上、False なら 0 件を期待。None は不問。
        ambiguities_presence_expected: True なら ambiguities が 1 件以上を期待。None は不問。
    """

    min_viewpoints: int = 0
    required_sections: List[str] = field(default_factory=list)
    expected_categories_any: List[str] = field(default_factory=list)
    expected_categories_all: List[str] = field(default_factory=list)
    expected_keywords_any: List[str] = field(default_factory=list)
    expected_keywords_all: List[str] = field(default_factory=list)
    forbidden_keywords: List[str] = field(default_factory=list)
    notes_presence_expected: Optional[bool] = None
    ambiguities_presence_expected: Optional[bool] = None


@dataclass
class EvalCase:
    """評価ケース 1 件の定義。

    Attributes:
        case_id: ケースの一意 ID（例: "TC-001"）。
        title: ケースのタイトル。
        target_type: 対象種別（"screen" / "api" / "batch" / "ticket" / "other"）。
        spec_text: 仕様テキスト（20 文字以上）。
        supplemental_text: 補足情報（省略可）。
        expectations: 期待値定義。
    """

    case_id: str
    title: str
    target_type: str
    spec_text: str
    supplemental_text: str = ""
    expectations: Expectations = field(default_factory=Expectations)


@dataclass
class CaseEvalResult:
    """1 ケースの評価結果。

    Attributes:
        case_id: ケース ID。
        title: ケースタイトル。
        passed: True なら全チェック通過。
        failures: 失敗理由のリスト。passed=True の場合は空。
        viewpoint_count: 生成された観点の総数。
        categories: 生成された観点のカテゴリ一覧（重複なし・ソート済み）。
        cache_hit: キャッシュから取得した場合 True。
        duration_seconds: 処理時間（秒）。
        token_usage: トークン使用量。キャッシュヒット時は None。
    """

    case_id: str
    title: str
    passed: bool
    failures: List[str]
    viewpoint_count: int
    categories: List[str]
    cache_hit: bool
    duration_seconds: float
    token_usage: Optional[Dict[str, int]] = None


@dataclass
class EvalReport:
    """全ケースの評価レポート。

    Attributes:
        total: 実行ケース数。
        passed: PASS 件数。
        failed: FAIL 件数。
        results: 各ケースの評価結果リスト。
        total_duration_seconds: 全ケース合計処理時間。
        total_tokens: 全ケース合計トークン数。キャッシュ使用時は None になる場合あり。
    """

    total: int
    passed: int
    failed: int
    results: List[CaseEvalResult]
    total_duration_seconds: float
    total_tokens: Optional[int] = None

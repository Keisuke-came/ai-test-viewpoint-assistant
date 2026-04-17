"""評価ケースの読み込みユーティリティ。"""
import json
from pathlib import Path
from typing import List, Optional

from app.eval.models import EvalCase, Expectations

# プロジェクトルートからの絶対パスで定義（CWD に依存しない）
DEFAULT_CASES_PATH = Path(__file__).resolve().parent.parent.parent / "eval_cases" / "default_cases.json"

_REQUIRED_KEYS = ("case_id", "title", "target_type", "spec_text")


def load_cases(path: Optional[Path] = None) -> List[EvalCase]:
    """JSON ファイルから評価ケースを読み込む。

    Args:
        path: JSON ファイルのパス。省略時は eval_cases/default_cases.json。

    Returns:
        EvalCase のリスト。

    Raises:
        FileNotFoundError: ファイルが存在しない場合。
        ValueError: JSON の形式が不正、または必須キーが欠落している場合。
    """
    target = path if path is not None else DEFAULT_CASES_PATH
    if not target.exists():
        raise FileNotFoundError(f"評価ケースファイルが見つかりません: {target}")

    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"評価ケース JSON の解析に失敗しました: {e}") from e

    if not isinstance(raw, list):
        raise ValueError("評価ケース JSON のトップレベルは配列である必要があります")

    return [_parse_case(item, idx) for idx, item in enumerate(raw)]


def _parse_case(data: dict, idx: int) -> EvalCase:
    """辞書から EvalCase を生成する。

    Args:
        data: ケースの辞書。
        idx: デバッグ用インデックス。

    Raises:
        ValueError: 必須キーが欠落している場合。
    """
    for key in _REQUIRED_KEYS:
        if key not in data:
            raise ValueError(f"評価ケース[{idx}] に必須キー '{key}' がありません")

    exp_data = data.get("expectations", {})
    expectations = Expectations(
        min_viewpoints=exp_data.get("min_viewpoints", 0),
        required_sections=exp_data.get("required_sections", []),
        expected_categories_any=exp_data.get("expected_categories_any", []),
        expected_categories_all=exp_data.get("expected_categories_all", []),
        expected_keywords_any=exp_data.get("expected_keywords_any", []),
        expected_keywords_all=exp_data.get("expected_keywords_all", []),
        forbidden_keywords=exp_data.get("forbidden_keywords", []),
        notes_presence_expected=exp_data.get("notes_presence_expected"),
        ambiguities_presence_expected=exp_data.get("ambiguities_presence_expected"),
    )
    return EvalCase(
        case_id=data["case_id"],
        title=data["title"],
        target_type=data["target_type"],
        spec_text=data["spec_text"],
        supplemental_text=data.get("supplemental_text", ""),
        expectations=expectations,
    )

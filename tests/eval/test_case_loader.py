"""app/eval/case_loader.py のテスト。

正常読み込み・FileNotFoundError・JSON 不正・必須キー欠落を検証する。
"""
import json
import pytest
from pathlib import Path

from app.eval.case_loader import load_cases, _parse_case, DEFAULT_CASES_PATH
from app.eval.models import EvalCase, Expectations


# ──────────────────────────────────────────────
# 正常系: デフォルトケースファイルの読み込み
# ──────────────────────────────────────────────

def test_load_default_cases_returns_list() -> None:
    """デフォルトケースファイルが EvalCase のリストとして読み込める。"""
    cases = load_cases()
    assert isinstance(cases, list)
    assert len(cases) > 0


def test_load_default_cases_have_required_fields() -> None:
    """デフォルトケースの全件が必須フィールドを持つ。"""
    cases = load_cases()
    for case in cases:
        assert isinstance(case, EvalCase)
        assert case.case_id
        assert case.title
        assert case.target_type
        assert len(case.spec_text) >= 20


def test_load_default_cases_target_types_are_valid() -> None:
    """デフォルトケースの target_type がすべて有効な値である。"""
    valid_types = {"screen", "api", "batch", "ticket", "other"}
    cases = load_cases()
    for case in cases:
        assert case.target_type in valid_types, f"{case.case_id}: 不正な target_type '{case.target_type}'"


def test_load_custom_cases_from_file(tmp_path: Path) -> None:
    """カスタム JSON ファイルから正しくケースを読み込める。"""
    data = [
        {
            "case_id": "CUSTOM-001",
            "title": "カスタムケース",
            "target_type": "api",
            "spec_text": "カスタムの仕様テキストです。必ず20文字以上にします。",
            "supplemental_text": "補足情報",
            "expectations": {
                "min_viewpoints": 3,
                "required_sections": [],
                "expected_categories_any": ["正常系"],
                "expected_categories_all": [],
                "expected_keywords_any": [],
                "expected_keywords_all": [],
                "forbidden_keywords": [],
                "notes_presence_expected": None,
                "ambiguities_presence_expected": None,
            },
        }
    ]
    json_file = tmp_path / "custom_cases.json"
    json_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    cases = load_cases(json_file)

    assert len(cases) == 1
    assert cases[0].case_id == "CUSTOM-001"
    assert cases[0].expectations.min_viewpoints == 3


def test_load_cases_expectations_defaults(tmp_path: Path) -> None:
    """expectations が省略された場合にデフォルト値で Expectations が生成される。"""
    data = [
        {
            "case_id": "TC-NOEXP",
            "title": "期待値なし",
            "target_type": "screen",
            "spec_text": "最低限の仕様テキストです。20文字以上必要。",
        }
    ]
    json_file = tmp_path / "no_exp.json"
    json_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    cases = load_cases(json_file)

    assert cases[0].expectations.min_viewpoints == 0
    assert cases[0].expectations.required_sections == []


# ──────────────────────────────────────────────
# 異常系: ファイル関連エラー
# ──────────────────────────────────────────────

def test_file_not_found_raises() -> None:
    """存在しないファイルパスを指定すると FileNotFoundError が発生する。"""
    with pytest.raises(FileNotFoundError, match="評価ケースファイルが見つかりません"):
        load_cases(Path("/nonexistent/path/cases.json"))


def test_invalid_json_raises_value_error(tmp_path: Path) -> None:
    """不正な JSON ファイルを指定すると ValueError が発生する。"""
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("not a json!!!", encoding="utf-8")

    with pytest.raises(ValueError, match="評価ケース JSON の解析に失敗しました"):
        load_cases(bad_file)


def test_non_array_json_raises_value_error(tmp_path: Path) -> None:
    """JSON トップレベルが配列でない場合 ValueError が発生する。"""
    bad_file = tmp_path / "obj.json"
    bad_file.write_text('{"key": "value"}', encoding="utf-8")

    with pytest.raises(ValueError, match="配列である必要があります"):
        load_cases(bad_file)


# ──────────────────────────────────────────────
# 異常系: 必須キー欠落
# ──────────────────────────────────────────────

@pytest.mark.parametrize("missing_key", ["case_id", "title", "target_type", "spec_text"])
def test_missing_required_key_raises_value_error(tmp_path: Path, missing_key: str) -> None:
    """必須キーが欠落していると ValueError が発生する。"""
    base = {
        "case_id": "TC-001",
        "title": "テスト",
        "target_type": "screen",
        "spec_text": "仕様テキストのサンプル文字列です。",
    }
    del base[missing_key]

    json_file = tmp_path / "missing.json"
    json_file.write_text(json.dumps([base], ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match=f"必須キー '{missing_key}'"):
        load_cases(json_file)


# ──────────────────────────────────────────────
# _parse_case のユニットテスト
# ──────────────────────────────────────────────

def test_parse_case_minimal() -> None:
    """必須フィールドのみで EvalCase が生成できる。"""
    data = {
        "case_id": "TC-MIN",
        "title": "最小ケース",
        "target_type": "api",
        "spec_text": "必要最小限の仕様テキストサンプルです。",
    }
    case = _parse_case(data, 0)
    assert case.case_id == "TC-MIN"
    assert case.supplemental_text == ""
    assert isinstance(case.expectations, Expectations)

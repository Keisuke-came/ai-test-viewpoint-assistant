"""app/eval/evaluator.py のテスト。

評価ルールはすべてローカル判定なので LLM 呼び出しなし・モック不要。
"""
import pytest
from app.domain.models import LlmResult, Viewpoint
from app.eval.evaluator import evaluate, _flatten_text
from app.eval.models import Expectations


# ──────────────────────────────────────────────
# フィクスチャ
# ──────────────────────────────────────────────

@pytest.fixture
def base_result() -> LlmResult:
    """正常系・異常系・境界値の 3 カテゴリを含む LlmResult。"""
    return LlmResult(
        summary="ログイン機能のテスト観点",
        viewpoints=[
            Viewpoint(category="正常系", title="正常ログイン", description="正しい認証情報でログインできる", priority="高"),
            Viewpoint(category="異常系", title="パスワード誤り", description="誤ったパスワードでエラー", priority="高"),
            Viewpoint(category="境界値", title="最大文字数", description="パスワード64文字で成功", priority="中"),
        ],
        ambiguities=["ロック解除手順が未定義"],
        notes=["テスト環境では別途設定が必要"],
    )


@pytest.fixture
def empty_result() -> LlmResult:
    """観点・ambiguities・notes がすべて空の LlmResult。"""
    return LlmResult(
        summary="空の結果",
        viewpoints=[],
        ambiguities=[],
        notes=[],
    )


# ──────────────────────────────────────────────
# 正常系: 全チェック通過
# ──────────────────────────────────────────────

def test_evaluate_no_expectations(base_result: LlmResult) -> None:
    """期待値が空の Expectations は全件 PASS になる。"""
    failures = evaluate(base_result, Expectations())
    assert failures == []


def test_evaluate_min_viewpoints_pass(base_result: LlmResult) -> None:
    """観点数が min_viewpoints 以上なら PASS。"""
    failures = evaluate(base_result, Expectations(min_viewpoints=3))
    assert failures == []


def test_evaluate_categories_any_pass(base_result: LlmResult) -> None:
    """expected_categories_any にマッチするカテゴリが 1 つ以上あれば PASS。"""
    failures = evaluate(base_result, Expectations(expected_categories_any=["正常系", "存在しない"]))
    assert failures == []


def test_evaluate_categories_all_pass(base_result: LlmResult) -> None:
    """expected_categories_all の全カテゴリが揃っていれば PASS。"""
    failures = evaluate(base_result, Expectations(expected_categories_all=["正常系", "異常系"]))
    assert failures == []


def test_evaluate_keywords_any_pass(base_result: LlmResult) -> None:
    """expected_keywords_any にマッチするキーワードが 1 つ以上含まれれば PASS。"""
    failures = evaluate(base_result, Expectations(expected_keywords_any=["ログイン", "存在しないワード"]))
    assert failures == []


def test_evaluate_keywords_all_pass(base_result: LlmResult) -> None:
    """expected_keywords_all の全キーワードが含まれれば PASS。"""
    failures = evaluate(base_result, Expectations(expected_keywords_all=["正常系", "異常系"]))
    assert failures == []


def test_evaluate_forbidden_keywords_pass(base_result: LlmResult) -> None:
    """forbidden_keywords が含まれなければ PASS。"""
    failures = evaluate(base_result, Expectations(forbidden_keywords=["存在しないキーワード"]))
    assert failures == []


def test_evaluate_notes_presence_true_pass(base_result: LlmResult) -> None:
    """notes あり期待 & 実際にあり → PASS。"""
    failures = evaluate(base_result, Expectations(notes_presence_expected=True))
    assert failures == []


def test_evaluate_notes_presence_false_pass(empty_result: LlmResult) -> None:
    """notes なし期待 & 実際になし → PASS。"""
    failures = evaluate(empty_result, Expectations(notes_presence_expected=False))
    assert failures == []


def test_evaluate_ambiguities_presence_true_pass(base_result: LlmResult) -> None:
    """ambiguities あり期待 & 実際にあり → PASS。"""
    failures = evaluate(base_result, Expectations(ambiguities_presence_expected=True))
    assert failures == []


# ──────────────────────────────────────────────
# 異常系: 各チェックが FAIL になるケース
# ──────────────────────────────────────────────

def test_evaluate_min_viewpoints_fail(base_result: LlmResult) -> None:
    """観点数が min_viewpoints 未満なら FAIL。"""
    failures = evaluate(base_result, Expectations(min_viewpoints=10))
    assert len(failures) == 1
    assert "観点数不足" in failures[0]


def test_evaluate_required_sections_fail(base_result: LlmResult) -> None:
    """テキストに含まれないセクションが required_sections にあれば FAIL。"""
    failures = evaluate(base_result, Expectations(required_sections=["存在しないセクション"]))
    assert len(failures) == 1
    assert "必須セクション欠落" in failures[0]


def test_evaluate_categories_any_fail(base_result: LlmResult) -> None:
    """expected_categories_any が 1 つもマッチしなければ FAIL。"""
    failures = evaluate(base_result, Expectations(expected_categories_any=["存在しないカテゴリA", "存在しないカテゴリB"]))
    assert len(failures) == 1
    assert "期待カテゴリ(any)なし" in failures[0]


def test_evaluate_categories_all_fail(base_result: LlmResult) -> None:
    """expected_categories_all に欠けているカテゴリがあれば FAIL。"""
    failures = evaluate(base_result, Expectations(expected_categories_all=["正常系", "存在しないカテゴリ"]))
    assert len(failures) == 1
    assert "期待カテゴリ(all)欠落" in failures[0]


def test_evaluate_keywords_any_fail(base_result: LlmResult) -> None:
    """expected_keywords_any が 1 つもマッチしなければ FAIL。"""
    failures = evaluate(base_result, Expectations(expected_keywords_any=["存在しないXYZ", "別の存在しないABC"]))
    assert len(failures) == 1
    assert "期待キーワード(any)なし" in failures[0]


def test_evaluate_keywords_all_fail(base_result: LlmResult) -> None:
    """expected_keywords_all に欠けているキーワードがあれば FAIL。"""
    failures = evaluate(base_result, Expectations(expected_keywords_all=["正常系", "存在しないキーワードXYZ"]))
    assert len(failures) == 1
    assert "期待キーワード(all)欠落" in failures[0]


def test_evaluate_forbidden_keywords_fail(base_result: LlmResult) -> None:
    """forbidden_keywords が含まれていれば FAIL。"""
    failures = evaluate(base_result, Expectations(forbidden_keywords=["正常系"]))
    assert len(failures) == 1
    assert "禁止キーワード検出" in failures[0]


def test_evaluate_notes_presence_true_fail(empty_result: LlmResult) -> None:
    """notes あり期待 & 実際になし → FAIL。"""
    failures = evaluate(empty_result, Expectations(notes_presence_expected=True))
    assert len(failures) == 1
    assert "notes 有無不一致" in failures[0]


def test_evaluate_notes_presence_false_fail(base_result: LlmResult) -> None:
    """notes なし期待 & 実際にあり → FAIL。"""
    failures = evaluate(base_result, Expectations(notes_presence_expected=False))
    assert len(failures) == 1
    assert "notes 有無不一致" in failures[0]


def test_evaluate_ambiguities_presence_fail(empty_result: LlmResult) -> None:
    """ambiguities あり期待 & 実際になし → FAIL。"""
    failures = evaluate(empty_result, Expectations(ambiguities_presence_expected=True))
    assert len(failures) == 1
    assert "ambiguities 有無不一致" in failures[0]


# ──────────────────────────────────────────────
# 複数 FAIL の集積
# ──────────────────────────────────────────────

def test_evaluate_multiple_failures(empty_result: LlmResult) -> None:
    """複数のチェックが同時に失敗した場合、すべての失敗理由が返る。"""
    expectations = Expectations(
        min_viewpoints=5,
        expected_categories_all=["正常系", "異常系"],
        notes_presence_expected=True,
    )
    failures = evaluate(empty_result, expectations)
    assert len(failures) >= 3


# ──────────────────────────────────────────────
# _flatten_text のユニットテスト
# ──────────────────────────────────────────────

def test_flatten_text_contains_all_fields(base_result: LlmResult) -> None:
    """_flatten_text がすべてのフィールドを含む文字列を返す。"""
    text = _flatten_text(base_result)
    assert "ログイン機能のテスト観点" in text
    assert "正常系" in text
    assert "正常ログイン" in text
    assert "正しい認証情報でログインできる" in text
    assert "ロック解除手順が未定義" in text
    assert "テスト環境では別途設定が必要" in text


def test_flatten_text_empty_result(empty_result: LlmResult) -> None:
    """観点・ambiguities・notes が空でも _flatten_text が動作する。"""
    text = _flatten_text(empty_result)
    assert "空の結果" in text

"""ルールベース評価ロジック。LLM を追加呼び出しせず、ローカルで判定する純粋関数群。"""
from app.domain.models import LlmResult
from app.eval.models import Expectations
from app.services.markdown_formatter import build_markdown_text


def evaluate(llm_result: LlmResult, expectations: Expectations) -> list:
    """LlmResult を expectations に照らし合わせてルールベースで評価する。

    追加の LLM 呼び出しは行わず、すべてローカルで判定する。

    required_sections は Markdown レンダリング後のテキストで判定する。
    その他のチェック（カテゴリ・キーワード等）は生データのフラットテキストで判定する。

    Args:
        llm_result: 評価対象の LLM 生成結果。
        expectations: 期待値定義。

    Returns:
        失敗理由の文字列リスト。空リストなら全チェック通過。
    """
    failures: list = []
    categories = [vp.category for vp in llm_result.viewpoints]
    all_text = _flatten_text(llm_result)

    # 最低観点数チェック
    if expectations.min_viewpoints > 0:
        count = len(llm_result.viewpoints)
        if count < expectations.min_viewpoints:
            failures.append(f"観点数不足: {count} < {expectations.min_viewpoints}")

    # 必須セクションチェック（Markdown レンダリング後のテキストで判定）
    if expectations.required_sections:
        markdown_text = build_markdown_text(llm_result)
        for section in expectations.required_sections:
            if section not in markdown_text:
                failures.append(f"必須セクション欠落: '{section}'")

    # カテゴリ（any）: いずれか 1 つ以上含まれるか
    if expectations.expected_categories_any:
        if not any(c in categories for c in expectations.expected_categories_any):
            failures.append(f"期待カテゴリ(any)なし: {expectations.expected_categories_any}")

    # カテゴリ（all）: すべて含まれるか
    for cat in expectations.expected_categories_all:
        if cat not in categories:
            failures.append(f"期待カテゴリ(all)欠落: '{cat}'")

    # キーワード（any）: いずれか 1 つ以上含まれるか
    if expectations.expected_keywords_any:
        if not any(kw in all_text for kw in expectations.expected_keywords_any):
            failures.append(f"期待キーワード(any)なし: {expectations.expected_keywords_any}")

    # キーワード（all）: すべて含まれるか
    for kw in expectations.expected_keywords_all:
        if kw not in all_text:
            failures.append(f"期待キーワード(all)欠落: '{kw}'")

    # 禁止キーワードチェック
    for kw in expectations.forbidden_keywords:
        if kw in all_text:
            failures.append(f"禁止キーワード検出: '{kw}'")

    # notes 有無チェック
    if expectations.notes_presence_expected is not None:
        has_notes = len(llm_result.notes) > 0
        if has_notes != expectations.notes_presence_expected:
            exp_str = "あり" if expectations.notes_presence_expected else "なし"
            act_str = "あり" if has_notes else "なし"
            failures.append(f"notes 有無不一致: 期待={exp_str}, 実際={act_str}")

    # ambiguities 有無チェック
    if expectations.ambiguities_presence_expected is not None:
        has_amb = len(llm_result.ambiguities) > 0
        if has_amb != expectations.ambiguities_presence_expected:
            exp_str = "あり" if expectations.ambiguities_presence_expected else "なし"
            act_str = "あり" if has_amb else "なし"
            failures.append(f"ambiguities 有無不一致: 期待={exp_str}, 実際={act_str}")

    return failures


def _flatten_text(llm_result: LlmResult) -> str:
    """LlmResult の全テキストフィールドを連結して検索用文字列を生成する。"""
    parts = [llm_result.summary]
    for vp in llm_result.viewpoints:
        parts.extend([vp.category, vp.title, vp.description])
    parts.extend(llm_result.ambiguities)
    parts.extend(llm_result.notes)
    return " ".join(parts)

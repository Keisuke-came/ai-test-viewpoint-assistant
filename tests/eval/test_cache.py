"""app/eval/cache.py のテスト。

キャッシュのヒット / ミス / 保存 / クリアをテストする。
"""
import pytest
from pathlib import Path
from unittest.mock import patch

from app.domain.models import LlmResult, Viewpoint
import app.eval.cache as eval_cache


@pytest.fixture
def tmp_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """テスト用の一時キャッシュディレクトリを設定する。"""
    monkeypatch.setattr(eval_cache, "CACHE_DIR", tmp_path / ".eval_cache_test")
    return eval_cache.CACHE_DIR


@pytest.fixture
def sample_llm_result() -> LlmResult:
    return LlmResult(
        summary="テスト用サマリ",
        viewpoints=[
            Viewpoint(category="正常系", title="正常テスト", description="成功する", priority="高"),
        ],
        ambiguities=[],
        notes=[],
    )


# ──────────────────────────────────────────────
# キャッシュミス
# ──────────────────────────────────────────────

def test_get_returns_none_when_no_cache(tmp_cache_dir: Path) -> None:
    """キャッシュが存在しない場合は None を返す。"""
    result = eval_cache.get("screen", "仕様テキストのサンプルです", "")
    assert result is None


# ──────────────────────────────────────────────
# 保存 → ヒット
# ──────────────────────────────────────────────

def test_set_and_get_returns_cached_result(tmp_cache_dir: Path, sample_llm_result: LlmResult) -> None:
    """set で保存した結果が get で取得できる。"""
    eval_cache.save("screen", "仕様テキストのサンプルです", "", sample_llm_result)
    cached = eval_cache.get("screen", "仕様テキストのサンプルです", "")
    assert cached is not None
    assert cached.summary == sample_llm_result.summary
    assert len(cached.viewpoints) == 1
    assert cached.viewpoints[0].category == "正常系"


def test_cache_creates_json_file(tmp_cache_dir: Path, sample_llm_result: LlmResult) -> None:
    """set 後に .json ファイルが作成される。"""
    eval_cache.save("api", "API の仕様テキストのサンプルです", "", sample_llm_result)
    json_files = list(eval_cache.CACHE_DIR.glob("*.json"))
    assert len(json_files) == 1


# ──────────────────────────────────────────────
# キャッシュキーの分離
# ──────────────────────────────────────────────

def test_different_target_type_yields_different_cache(
    tmp_cache_dir: Path, sample_llm_result: LlmResult
) -> None:
    """target_type が異なれば別キャッシュエントリになる。"""
    eval_cache.save("screen", "仕様テキストのサンプルです", "", sample_llm_result)
    result = eval_cache.get("api", "仕様テキストのサンプルです", "")
    assert result is None


def test_different_spec_text_yields_different_cache(
    tmp_cache_dir: Path, sample_llm_result: LlmResult
) -> None:
    """spec_text が異なれば別キャッシュエントリになる。"""
    eval_cache.save("screen", "仕様テキスト A のサンプルです", "", sample_llm_result)
    result = eval_cache.get("screen", "仕様テキスト B の別のサンプルです", "")
    assert result is None


def test_same_key_overwritten_on_second_set(
    tmp_cache_dir: Path, sample_llm_result: LlmResult
) -> None:
    """同じキーで set を 2 回呼ぶと上書きされ、ファイルは 1 件のまま。"""
    eval_cache.save("screen", "仕様テキストのサンプルです", "", sample_llm_result)

    updated = LlmResult(
        summary="更新されたサマリ",
        viewpoints=[],
        ambiguities=[],
        notes=[],
    )
    eval_cache.save("screen", "仕様テキストのサンプルです", "", updated)

    cached = eval_cache.get("screen", "仕様テキストのサンプルです", "")
    assert cached is not None
    assert cached.summary == "更新されたサマリ"
    assert len(list(eval_cache.CACHE_DIR.glob("*.json"))) == 1


# ──────────────────────────────────────────────
# clear_all
# ──────────────────────────────────────────────

def test_clear_all_removes_files(tmp_cache_dir: Path, sample_llm_result: LlmResult) -> None:
    """clear_all が全キャッシュファイルを削除し削除件数を返す。"""
    eval_cache.save("screen", "仕様テキスト 1 のサンプルです", "", sample_llm_result)
    eval_cache.save("api", "仕様テキスト 2 のサンプルです", "", sample_llm_result)

    count = eval_cache.clear_all()
    assert count == 2
    assert list(eval_cache.CACHE_DIR.glob("*.json")) == []


def test_clear_all_returns_zero_when_no_cache(tmp_cache_dir: Path) -> None:
    """キャッシュがない状態で clear_all を呼んでも 0 を返す。"""
    count = eval_cache.clear_all()
    assert count == 0


# ──────────────────────────────────────────────
# キャッシュファイル破損時のフォールバック
# ──────────────────────────────────────────────

def test_get_returns_none_on_corrupted_file(
    tmp_cache_dir: Path, sample_llm_result: LlmResult
) -> None:
    """キャッシュファイルが壊れている場合は None を返す（クラッシュしない）。"""
    eval_cache.save("screen", "仕様テキストのサンプルです", "", sample_llm_result)

    # ファイルを壊す
    for f in eval_cache.CACHE_DIR.glob("*.json"):
        f.write_text("invalid json!!!", encoding="utf-8")

    result = eval_cache.get("screen", "仕様テキストのサンプルです", "")
    assert result is None

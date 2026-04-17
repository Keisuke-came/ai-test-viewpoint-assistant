"""評価用キャッシュ。同一条件の LLM 呼び出し結果を JSON ファイルに保存して再利用する。

キャッシュキー: model + target_type + spec_text + supplemental_text の SHA256 (先頭 16 文字)
保存先: プロジェクトルートの .eval_cache/ ディレクトリ
フォーマット: {key}.json（LlmResult を JSON シリアライズ）

キャッシュを無効化したい場合:
  - eval_run.py で --refresh オプションを指定
  - または .eval_cache/ ディレクトリを手動で削除
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from app.config import settings
from app.domain.models import LlmResult

logger = logging.getLogger(__name__)

# プロジェクトルートからの絶対パスで定義（CWD に依存しない）
CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".eval_cache"


def _make_key(target_type: str, spec_text: str, supplemental_text: str) -> str:
    """キャッシュキーを生成する。

    モデル名と入力内容を組み合わせてハッシュ化するため、
    モデル変更や入力変更時は自動的に別キーになる。

    Args:
        target_type: 対象種別。
        spec_text: 仕様テキスト。
        supplemental_text: 補足情報。

    Returns:
        SHA256 ハッシュの先頭 16 文字。
    """
    payload = json.dumps(
        {
            "model": settings.OPENAI_MODEL,
            "target_type": target_type,
            "spec_text": spec_text,
            "supplemental_text": supplemental_text,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def get(target_type: str, spec_text: str, supplemental_text: str) -> Optional[LlmResult]:
    """キャッシュから LlmResult を取得する。

    Args:
        target_type: 対象種別。
        spec_text: 仕様テキスト。
        supplemental_text: 補足情報。

    Returns:
        キャッシュが存在すれば LlmResult、なければ None。
    """
    key = _make_key(target_type, spec_text, supplemental_text)
    path = CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return LlmResult.model_validate(data["llm_result"])
    except (json.JSONDecodeError, ValidationError, KeyError) as e:
        logger.warning("キャッシュ読み込み失敗 (key=%s): %s", key, e)
        return None


def save(
    target_type: str,
    spec_text: str,
    supplemental_text: str,
    llm_result: LlmResult,
) -> None:
    """LlmResult をキャッシュに保存する。

    Args:
        target_type: 対象種別。
        spec_text: 仕様テキスト。
        supplemental_text: 補足情報。
        llm_result: 保存する LlmResult。
    """
    key = _make_key(target_type, spec_text, supplemental_text)
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = CACHE_DIR / f"{key}.json"
        data = {"llm_result": llm_result.model_dump()}
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.debug("キャッシュ保存: %s", key)
    except OSError as e:
        logger.warning("キャッシュ保存失敗 (key=%s): %s", key, e)


def clear_all() -> int:
    """全キャッシュファイルを削除する。

    Returns:
        削除したファイル数。
    """
    if not CACHE_DIR.exists():
        return 0
    count = 0
    for f in CACHE_DIR.glob("*.json"):
        f.unlink()
        count += 1
    return count

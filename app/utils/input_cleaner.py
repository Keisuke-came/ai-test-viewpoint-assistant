import re
from typing import Optional

from app.domain.models import InputValidationError


def clean(text: str) -> str:
    """入力テキストを正規化・クリーニングする。

    以下の処理をこの順番で実行する:
    1. 先頭・末尾の空白を除去
    2. タブ文字を半角スペース1つに置換
    3. 3行以上連続する空行を2行に圧縮
    4. 各行の末尾の空白を除去

    Args:
        text: クリーニング対象のテキスト文字列

    Returns:
        クリーニング済みのテキスト文字列
    """
    text = text.strip()
    text = text.replace("\t", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = text.split("\n")
    lines = [line.rstrip() for line in lines]
    return "\n".join(lines)


def validate_length(text: str, max_chars: int) -> None:
    """テキストの文字数が上限を超えていないかチェックする。

    Args:
        text: チェック対象のテキスト
        max_chars: 最大文字数（1以上の整数）

    Raises:
        InputValidationError: max_chars が1未満の場合、または文字数が上限を超えた場合
    """
    if max_chars < 1:
        raise InputValidationError("max_chars は1以上を指定してください")
    if len(text) > max_chars:
        raise InputValidationError(
            f"入力テキストが上限（{max_chars}文字）を超えています。現在: {len(text)}文字"
        )


def truncate(text: str, max_chars: int) -> str:
    """テキストを指定文字数で切り詰める。

    Args:
        text: 切り詰め対象のテキスト
        max_chars: 最大文字数（1以上の整数）

    Returns:
        切り詰め後のテキスト文字列

    Raises:
        InputValidationError: max_chars が1未満の場合
    """
    if max_chars < 1:
        raise InputValidationError("max_chars は1以上を指定してください")
    if len(text) <= max_chars:
        return text
    return text[:max_chars]

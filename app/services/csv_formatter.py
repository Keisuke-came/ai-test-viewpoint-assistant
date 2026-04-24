import csv
import io
from typing import List, Optional

from app.domain.models import InputValidationError, Viewpoint


def format_as_csv(viewpoints: Optional[List[Viewpoint]]) -> str:
    """観点リストを CSV 形式の文字列に変換する。

    先頭に BOM（U+FEFF）を付与し、Excel で開いた際の文字化けを防ぐ。
    フィールド内のカンマ・改行・ダブルクォートは RFC 4180 に従って
    ダブルクォートで囲み、内部のダブルクォートは 2 つ重ねてエスケープする。

    Args:
        viewpoints: 変換対象の観点リスト。空リストの場合はヘッダ行のみ返す。

    Returns:
        BOM 付き CSV 文字列（UTF-8 エンコード想定）。

    Raises:
        InputValidationError: viewpoints が None、または要素が Viewpoint 型でない場合。
    """
    if viewpoints is None:
        raise InputValidationError("viewpoints must not be None")
    for item in viewpoints:
        if not isinstance(item, Viewpoint):
            raise InputValidationError(
                f"All elements must be Viewpoint instances, got {type(item)}"
            )

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(_build_header())
    for vp in viewpoints:
        writer.writerow(_viewpoint_to_row(vp))
    return "\ufeff" + buf.getvalue()


def _build_header() -> List[str]:
    """CSV のヘッダ行を返す。"""
    return ["カテゴリ", "観点タイトル", "説明", "優先度"]


def _viewpoint_to_row(viewpoint: Viewpoint) -> List[str]:
    """Viewpoint 1 件を CSV の 1 行（列のリスト）に変換する。"""
    return [viewpoint.category, viewpoint.title, viewpoint.description, viewpoint.priority]

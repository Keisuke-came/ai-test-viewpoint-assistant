from app.domain.models import Viewpoint

CATEGORY_ORDER = [
    "正常系",
    "異常系",
    "境界値",
    "必須入力・入力制約",
    "業務ルール",
    "権限・ロール",
    "状態遷移",
    "外部連携・データ連携",
    "表示・メッセージ",
    "非機能上の注意点",
    "その他",
]

PRIORITY_ORDER = {"高": 0, "中": 1, "低": 2}


def normalize_category(category: str) -> str:
    if category in CATEGORY_ORDER:
        return category
    return "その他"


def sort_viewpoints(viewpoints: list[Viewpoint]) -> list[Viewpoint]:
    return sorted(
        viewpoints,
        key=lambda v: (
            CATEGORY_ORDER.index(normalize_category(v.category)),
            PRIORITY_ORDER.get(v.priority, 99),
        ),
    )


def group_by_category(viewpoints: list[Viewpoint]) -> dict[str, list[Viewpoint]]:
    grouped: dict[str, list[Viewpoint]] = {}
    for vp in sort_viewpoints(viewpoints):
        cat = normalize_category(vp.category)
        grouped.setdefault(cat, []).append(vp)
    return grouped

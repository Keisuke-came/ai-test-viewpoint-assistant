import pytest
from app.domain.models import Viewpoint
from app.utils.category_utils import (
    normalize_category,
    sort_viewpoints,
    group_by_category,
    CATEGORY_ORDER,
    PRIORITY_ORDER,
)


def make_vp(category: str, priority: str = "中", title: str = "t") -> Viewpoint:
    return Viewpoint(category=category, title=title, description="d", priority=priority)


class TestNormalizeCategory:
    @pytest.mark.parametrize("category", CATEGORY_ORDER)
    def test_known_category_returned_as_is(self, category):
        assert normalize_category(category) == category

    def test_unknown_category_returns_sonota(self):
        assert normalize_category("未定義カテゴリ") == "その他"

    def test_empty_string_returns_sonota(self):
        assert normalize_category("") == "その他"


class TestSortViewpoints:
    def test_sorted_by_category_order(self):
        vps = [
            make_vp("境界値"),
            make_vp("正常系"),
            make_vp("異常系"),
        ]
        sorted_vps = sort_viewpoints(vps)
        categories = [vp.category for vp in sorted_vps]
        assert categories == ["正常系", "異常系", "境界値"]

    def test_sorted_by_priority_within_same_category(self):
        vps = [
            make_vp("正常系", priority="低"),
            make_vp("正常系", priority="高"),
            make_vp("正常系", priority="中"),
        ]
        sorted_vps = sort_viewpoints(vps)
        priorities = [vp.priority for vp in sorted_vps]
        assert priorities == ["高", "中", "低"]

    def test_category_then_priority_combined(self):
        vps = [
            make_vp("異常系", priority="低"),
            make_vp("正常系", priority="低"),
            make_vp("正常系", priority="高"),
            make_vp("異常系", priority="高"),
        ]
        sorted_vps = sort_viewpoints(vps)
        assert sorted_vps[0].category == "正常系"
        assert sorted_vps[0].priority == "高"
        assert sorted_vps[1].category == "正常系"
        assert sorted_vps[1].priority == "低"
        assert sorted_vps[2].category == "異常系"
        assert sorted_vps[2].priority == "高"

    def test_unknown_category_goes_to_end(self):
        vps = [
            make_vp("未知カテゴリ"),
            make_vp("正常系"),
        ]
        sorted_vps = sort_viewpoints(vps)
        assert sorted_vps[0].category == "正常系"
        # 未知カテゴリは「その他」扱いで末尾に
        assert sorted_vps[-1].category == "未知カテゴリ"

    def test_empty_list_returns_empty(self):
        assert sort_viewpoints([]) == []


class TestGroupByCategory:
    def test_grouped_correctly(self):
        vps = [
            make_vp("正常系", title="A"),
            make_vp("異常系", title="B"),
            make_vp("正常系", title="C"),
        ]
        grouped = group_by_category(vps)
        assert "正常系" in grouped
        assert "異常系" in grouped
        assert len(grouped["正常系"]) == 2
        assert len(grouped["異常系"]) == 1

    def test_empty_list_returns_empty_dict(self):
        assert group_by_category([]) == {}

    def test_unknown_category_grouped_as_sonota(self):
        vps = [make_vp("謎のカテゴリ")]
        grouped = group_by_category(vps)
        assert "その他" in grouped
        assert "謎のカテゴリ" not in grouped

    def test_dict_order_follows_category_order(self):
        vps = [
            make_vp("境界値"),
            make_vp("正常系"),
            make_vp("異常系"),
        ]
        grouped = group_by_category(vps)
        keys = list(grouped.keys())
        expected_order = ["正常系", "異常系", "境界値"]
        assert keys == expected_order

    def test_within_group_priority_order_preserved(self):
        vps = [
            make_vp("正常系", priority="低"),
            make_vp("正常系", priority="高"),
        ]
        grouped = group_by_category(vps)
        priorities = [vp.priority for vp in grouped["正常系"]]
        assert priorities == ["高", "低"]

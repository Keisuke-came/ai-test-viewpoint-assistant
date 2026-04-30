"""Tests for mcp_servers.skill_lister.server.

`_parse_skills` と `_extract_description` の単体テスト。
MCP サーバー本体（stdio 通信）はテスト対象外。
"""
from pathlib import Path

from mcp_servers.skill_lister.server import _parse_skills, _extract_description


def _write_skill(parent: Path, name: str, description: str = "") -> Path:
    """テスト用ヘルパ: parent 配下に Skill ディレクトリと SKILL.md を作る。"""
    skill_dir = parent / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    if description:
        body = f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n"
    else:
        body = f"# {name}\n"
    skill_md.write_text(body, encoding="utf-8")
    return skill_md


# ---------- _parse_skills 正常系 ----------


def test_parse_skills_returns_all_skills(tmp_path: Path) -> None:
    _write_skill(tmp_path, "alpha", description="alpha desc")
    _write_skill(tmp_path, "beta", description="beta desc")

    result = _parse_skills(tmp_path)

    assert len(result) == 2
    names = [s["name"] for s in result]
    assert names == ["alpha", "beta"]


def test_parse_skills_each_entry_has_required_keys(tmp_path: Path) -> None:
    _write_skill(tmp_path, "alpha", description="hello")

    result = _parse_skills(tmp_path)

    assert len(result) == 1
    entry = result[0]
    assert set(entry.keys()) == {"name", "description", "path"}
    assert entry["name"] == "alpha"
    assert entry["description"] == "hello"
    assert entry["path"].endswith("SKILL.md")


def test_parse_skills_sorts_by_name(tmp_path: Path) -> None:
    _write_skill(tmp_path, "charlie")
    _write_skill(tmp_path, "alpha")
    _write_skill(tmp_path, "bravo")

    result = _parse_skills(tmp_path)
    names = [s["name"] for s in result]

    assert names == ["alpha", "bravo", "charlie"]


# ---------- _parse_skills 異常系 ----------


def test_parse_skills_returns_empty_when_dir_missing(tmp_path: Path) -> None:
    missing = tmp_path / "no_such_dir"

    assert _parse_skills(missing) == []


def test_parse_skills_returns_empty_when_dir_empty(tmp_path: Path) -> None:
    assert _parse_skills(tmp_path) == []


def test_parse_skills_skips_dirs_without_skill_md(tmp_path: Path) -> None:
    _write_skill(tmp_path, "valid", description="ok")
    (tmp_path / "no_skill_md").mkdir()

    result = _parse_skills(tmp_path)
    names = [s["name"] for s in result]

    assert names == ["valid"]


def test_parse_skills_ignores_non_directory_entries(tmp_path: Path) -> None:
    _write_skill(tmp_path, "valid", description="ok")
    (tmp_path / "README.md").write_text("not a skill", encoding="utf-8")

    result = _parse_skills(tmp_path)
    names = [s["name"] for s in result]

    assert names == ["valid"]


# ---------- _extract_description 正常系 ----------


def test_extract_description_basic(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\ndescription: foo\n---\n\nbody\n", encoding="utf-8")

    assert _extract_description(skill_md) == "foo"


def test_extract_description_strips_double_quotes(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text('---\ndescription: "foo"\n---\n\nbody\n', encoding="utf-8")

    assert _extract_description(skill_md) == "foo"


def test_extract_description_strips_single_quotes(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\ndescription: 'foo'\n---\n\nbody\n", encoding="utf-8")

    assert _extract_description(skill_md) == "foo"


def test_extract_description_strips_surrounding_whitespace(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\ndescription:    foo bar    \n---\n\nbody\n", encoding="utf-8")

    assert _extract_description(skill_md) == "foo bar"


# ---------- _extract_description 異常系 ----------


def test_extract_description_no_frontmatter(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("# heading only\n\nno frontmatter here\n", encoding="utf-8")

    assert _extract_description(skill_md) == ""


def test_extract_description_frontmatter_without_description_key(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\nname: foo\n---\n\nbody\n", encoding="utf-8")

    assert _extract_description(skill_md) == ""


def test_extract_description_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist.md"

    assert _extract_description(missing) == ""


def test_extract_description_invalid_encoding(tmp_path: Path) -> None:
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_bytes(b"\xff\xfe\x00\x00invalid utf-8 \x80\x81")

    assert _extract_description(skill_md) == ""

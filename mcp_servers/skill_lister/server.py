"""skill-lister MCP server.

このプロジェクトの .claude/skills/ 配下にある Skill 一覧を返す
MCP サーバー（公式 MCP Python SDK の FastMCP 利用）。
"""
import re
import sys
from pathlib import Path
from typing import List, Dict

from mcp.server.fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"

mcp = FastMCP("skill-lister")


def _parse_skills(skills_dir: Path) -> List[Dict[str, str]]:
    """Skill ディレクトリから一覧を抽出する純粋関数（テスト対象）。

    Args:
        skills_dir: .claude/skills のような Skill 親ディレクトリの Path

    Returns:
        Skill ごとに以下のキーを持つ dict のリスト:
        - name: Skill のディレクトリ名
        - description: SKILL.md frontmatter の description（なければ空文字）
        - path: SKILL.md への相対パス（プロジェクトルートからの相対）

    Notes:
        - skills_dir が存在しない場合は空リストを返す
        - SKILL.md が存在しないディレクトリはスキップ
        - frontmatter が壊れていても落とさず description="" で返す
    """
    if not skills_dir.exists() or not skills_dir.is_dir():
        return []

    skills: List[Dict[str, str]] = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        description = _extract_description(skill_md)
        try:
            rel_path = skill_md.relative_to(PROJECT_ROOT)
        except ValueError:
            rel_path = skill_md

        skills.append({
            "name": skill_dir.name,
            "description": description,
            "path": str(rel_path),
        })
    return skills


def _extract_description(skill_md: Path) -> str:
    """SKILL.md の frontmatter から description を抽出する。

    frontmatter が無い・壊れている・description キーが無い場合は空文字を返す。
    YAML パーサは使わず正規表現で軽量に処理する（依存最小化）。
    """
    try:
        content = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return ""

    frontmatter = match.group(1)
    desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    if not desc_match:
        return ""

    return desc_match.group(1).strip().strip('"').strip("'")


@mcp.tool()
def list_skills() -> List[Dict[str, str]]:
    """このプロジェクトに定義されている Skill の一覧を返す。

    Returns:
        Skill ごとに name / description / path を持つ dict のリスト
    """
    return _parse_skills(SKILLS_DIR)


if __name__ == "__main__":
    # stdio 経由で Claude Code と通信。print() は禁止（stdio を破壊するため）。
    # ログを出したい場合は sys.stderr 経由で。
    mcp.run()

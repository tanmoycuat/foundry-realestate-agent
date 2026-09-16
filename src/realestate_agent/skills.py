"""Load source-controlled business instructions for local development."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


FRONT_MATTER = re.compile(r"^---\s*\n(?P<header>.*?)\n---\s*\n(?P<body>.*)$", re.DOTALL)


@dataclass(frozen=True)
class LoadedSkill:
    name: str
    description: str
    instructions: str
    version: str
    source: str


def _header_value(header: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+?)\s*$", header, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip('"\'')


def parse_skill(content: str, *, fallback_name: str, source: str) -> LoadedSkill:
    """Parse Foundry Agent Skills-compatible Markdown with optional front matter."""
    match = FRONT_MATTER.match(content)
    if match:
        header = match.group("header")
        body = match.group("body").strip()
        name = _header_value(header, "skill") or _header_value(header, "name") or fallback_name
        description = _header_value(header, "description") or f"Real-estate {name} capability"
        version = _header_value(header, "version") or "baseline"
    else:
        name = fallback_name
        description = f"Real-estate {name} capability"
        version = "baseline"
        body = content.strip()

    normalized_name = name.lower().replace("_", "-")
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?", normalized_name):
        raise ValueError(f"Invalid skill name: {name}")
    if not body:
        raise ValueError(f"Skill {normalized_name} has no instructions")
    return LoadedSkill(normalized_name, description[:1024], body, version, source)


class LocalSkillRepository:
    """Load baseline skills from the repository until Foundry Skills is configured."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parents[2]

    def load(self, name: str) -> LoadedSkill:
        path = self.root / "skills" / name / "SKILL.md"
        if not path.is_file():
            raise FileNotFoundError(f"Skill not found: {name}")
        return parse_skill(path.read_text(encoding="utf-8"), fallback_name=name, source=str(path))

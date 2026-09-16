from pathlib import Path

from realestate_agent.skills import LocalSkillRepository, parse_skill


def test_parse_foundry_skill() -> None:
    skill = parse_skill(
        "---\nname: realestate-test\ndescription: Test skill.\n---\n\nDo the work.",
        fallback_name="fallback",
        source="memory",
    )
    assert skill.name == "realestate-test"
    assert skill.instructions == "Do the work."


def test_load_project_skill_from_workspace() -> None:
    root = Path(__file__).resolve().parents[1]
    skill = LocalSkillRepository(root).load("realestate-comps")
    assert skill.name == "realestate-comps"
    assert "comparable" in skill.instructions.lower()

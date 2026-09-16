from pathlib import Path

from realestate_agent.models import AnalysisResult, PropertyProfile, SpecialistResult
from realestate_agent.reports import render_markdown, render_pdf


def sample_result() -> AnalysisResult:
    return AnalysisResult(
        analysis_id="sample",
        command="analyze",
        property=PropertyProfile(
            address="4821 Ridgeview Drive, Austin, TX 78735",
            price=425_000,
            bedrooms=3,
            bathrooms=2,
            square_feet=1_850,
            year_built=1998,
        ),
        specialists=[
            SpecialistResult(specialist="comps", score=72, findings=["Comparable evidence is limited."], confidence=0.7)
        ],
        overall_score=72,
        grade="A",
        signal="BUY",
        confidence=0.7,
        summary="A sample analysis.",
        warnings=["Manual data only."],
        model_profile_id="test",
    )


def test_markdown_contains_provenance_and_disclaimer() -> None:
    markdown = render_markdown(sample_result())
    assert "Not financial or investment advice" in markdown
    assert "Model profile: `test`" in markdown


def test_pdf_is_generated(tmp_path: Path) -> None:
    output = render_pdf(sample_result(), tmp_path / "report.pdf")
    assert output.exists()
    assert output.stat().st_size > 1_000

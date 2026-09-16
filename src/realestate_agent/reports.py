"""JSON, Markdown, and PDF report rendering."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import AnalysisResult


def render_json(result: AnalysisResult) -> str:
    return result.model_dump_json(indent=2)


def render_markdown(result: AnalysisResult) -> str:
    sections = [
        f"# Property Analysis: {result.property.address}",
        "",
        f"> Score: **{result.overall_score}/100** | Grade: **{result.grade}** | Signal: **{result.signal}**",
        "",
        "**For educational and research purposes only. Not financial or investment advice.**",
        "",
        "## Summary",
        "",
        result.summary or "No narrative summary was generated.",
        "",
        "## Specialist Results",
        "",
    ]
    for specialist in result.specialists:
        sections.extend(
            [
                f"### {specialist.specialist.title()} ({specialist.score}/100)",
                "",
                *[f"- {finding}" for finding in specialist.findings],
                "",
            ]
        )
    if result.warnings:
        sections.extend(["## Warnings", "", *[f"- {warning}" for warning in result.warnings], ""])
    sections.extend(
        [
            "## Provenance",
            "",
            f"- Model profile: `{result.model_profile_id}`",
            f"- Agent version: `{result.agent_version}`",
            f"- Toolbox version: `{result.toolbox_version or 'not configured'}`",
        ]
    )
    return "\n".join(sections)


def render_pdf(result: AnalysisResult, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17324D"),
            spaceAfter=18,
        )
    )
    document = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title=f"Property Analysis - {result.property.address}",
    )
    story = [
        Paragraph("Property Analysis", styles["ReportTitle"]),
        Paragraph(result.property.address, styles["Heading2"]),
        Spacer(1, 8),
        Table(
            [
                ["Price", f"${result.property.price:,.0f}", "Score", f"{result.overall_score}/100"],
                ["Type", result.property.property_type, "Grade", result.grade],
                ["Date", result.created_at.strftime("%B %d, %Y"), "Signal", result.signal],
            ],
            colWidths=[0.9 * inch, 2.1 * inch, 0.9 * inch, 2.1 * inch],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F0F5")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9AAAB8")),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 7),
                ]
            ),
        ),
        Spacer(1, 18),
        Paragraph("Summary", styles["Heading2"]),
        Paragraph(result.summary or "No narrative summary was generated.", styles["BodyText"]),
        Spacer(1, 14),
        Paragraph("Specialist Results", styles["Heading2"]),
    ]
    for specialist in result.specialists:
        story.extend(
            [
                Paragraph(
                    f"{specialist.specialist.title()} - {specialist.score}/100",
                    styles["Heading3"],
                ),
                *[Paragraph(f"- {finding}", styles["BodyText"]) for finding in specialist.findings],
                Spacer(1, 6),
            ]
        )
    if result.warnings:
        story.extend([Paragraph("Warnings", styles["Heading2"])])
        story.extend(Paragraph(f"- {warning}", styles["BodyText"]) for warning in result.warnings)
    story.extend(
        [
            Spacer(1, 16),
            Paragraph(
                "For educational and research purposes only. Not financial or investment advice.",
                styles["Italic"],
            ),
        ]
    )
    document.build(story)
    return output

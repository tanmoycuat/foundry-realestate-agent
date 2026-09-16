"""JSON, Markdown, and PDF output adapters."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Callable

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


def _legacy_generator() -> Callable[[dict[str, Any], str], str]:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "generate_realestate_pdf.py"
    spec = importlib.util.spec_from_file_location("realestate_pdf_generator", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load PDF generator from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_report


def to_legacy_pdf_data(result: AnalysisResult) -> dict[str, Any]:
    specialist_scores = {item.specialist: item.score for item in result.specialists}
    return {
        "address": result.property.address,
        "price": f"${result.property.price:,.0f}",
        "date": result.created_at.strftime("%B %d, %Y"),
        "overall_score": result.overall_score,
        "property_details": {
            "beds": str(result.property.bedrooms or "N/A"),
            "baths": str(result.property.bathrooms or "N/A"),
            "sqft": f"{result.property.square_feet:,.0f}" if result.property.square_feet else "N/A",
            "year_built": str(result.property.year_built or "N/A"),
            "lot_size": result.property.lot_size or "N/A",
            "property_type": result.property.property_type,
        },
        "categories": {
            "Value & Comps": {"score": specialist_scores.get("comps", 0), "weight": "25%"},
            "Income Potential": {"score": specialist_scores.get("rental", 0), "weight": "20%"},
            "Neighborhood Quality": {"score": specialist_scores.get("neighborhood", 0), "weight": "20%"},
            "Investment Upside": {"score": specialist_scores.get("investment", 0), "weight": "20%"},
            "Market Conditions": {"score": specialist_scores.get("market", 0), "weight": "15%"},
        },
        "recommendation": {"signal": result.signal, "summary": result.summary},
        "risk_factors": [
            {"factor": "Analysis warning", "probability": "Unknown", "impact": "Unknown", "notes": warning}
            for warning in result.warnings
        ],
    }


def render_pdf(result: AnalysisResult, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    _legacy_generator()(to_legacy_pdf_data(result), str(output))
    return output

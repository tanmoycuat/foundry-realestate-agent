"""Agent Framework construction and concurrent real-estate analysis workflow."""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Protocol
from uuid import uuid4

from agent_framework import Agent
from agent_framework.orchestrations import ConcurrentBuilder

from .calculations import calculate_property_score, mortgage_payment, property_signal, score_grade
from .data import manual_evidence
from .models import AnalysisRequest, AnalysisResult, PropertyProfile, SpecialistResult
from .reports import render_json
from .skills import LocalSkillRepository


SPECIALISTS = ("comps", "rental", "neighborhood", "investment", "market")
DISCLAIMER = "For educational and research purposes only. Not financial or investment advice."


class SupportsAgent(Protocol):
    def run(self, messages: Any = None, **kwargs: Any) -> Awaitable[Any]: ...


SpecialistRunner = Callable[[str, str], Awaitable[SpecialistResult]]


def specialist_prompt(role: str, evidence_json: str, instructions: str) -> str:
    return f"""You are the {role} specialist in a real-estate analysis workflow.

Follow these business instructions:
{instructions}

Analyze only the supplied evidence. Do not invent values or sources.
Return one JSON object with exactly these fields:
specialist, score, findings, risks, assumptions, evidence_keys, confidence.
specialist must be \"{role}\". score is 0-100 and confidence is 0-1.

EVIDENCE:
{evidence_json}

{DISCLAIMER}
"""


def parse_specialist_response(role: str, text: str) -> SpecialistResult:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        if cleaned.lstrip().startswith("json"):
            cleaned = cleaned.lstrip()[4:].lstrip()
    payload = json.loads(cleaned)
    payload["specialist"] = role
    return SpecialistResult.model_validate(payload)


async def run_with_agents(
    *, evidence_json: str, agents: Mapping[str, SupportsAgent], instructions: Mapping[str, str]
) -> list[SpecialistResult]:
    """Run specialists concurrently and validate each result independently."""

    async def run_one(role: str) -> SpecialistResult:
        response = await agents[role].run(specialist_prompt(role, evidence_json, instructions[role]))
        messages = getattr(response, "messages", [])
        text = messages[-1].text if messages else str(response)
        return parse_specialist_response(role, text)

    settled = await asyncio.gather(*(run_one(role) for role in SPECIALISTS), return_exceptions=True)
    return [result for result in settled if isinstance(result, SpecialistResult)]


def create_specialist_agents(client: Any, toolbox: Any, repository: LocalSkillRepository) -> tuple[dict[str, Agent], dict[str, str]]:
    agents: dict[str, Agent] = {}
    instructions: dict[str, str] = {}
    for role in SPECIALISTS:
        skill = repository.load(f"realestate-{role}")
        instructions[role] = skill.instructions
        agents[role] = Agent(
            client=client,
            name=f"realestate-{role}",
            instructions=f"You are a real-estate {role} specialist.",
            tools=[toolbox] if toolbox is not None else None,
            default_options={"store": False},
        )
    return agents, instructions


def build_concurrent_workflow(client: Any, toolbox: Any = None) -> Any:
    """Expose the explicit Agent Framework concurrent workflow for hosted use."""
    agents, _ = create_specialist_agents(client, toolbox, LocalSkillRepository())
    return ConcurrentBuilder(
        participants=list(agents.values()),
        intermediate_output_from=list(agents.values()),
    ).build()


async def analyze_with_runner(request: AnalysisRequest, runner: SpecialistRunner) -> AnalysisResult:
    """Testable analysis pipeline independent of a concrete model provider."""
    if request.property is None:
        raise ValueError("Manual PropertyProfile input is required until a property-data tool is configured")
    evidence = manual_evidence(request.property)
    evidence_json = evidence.model_dump_json(indent=2)
    settled = await asyncio.gather(
        *(runner(role, evidence_json) for role in SPECIALISTS),
        return_exceptions=True,
    )
    specialists = [result for result in settled if isinstance(result, SpecialistResult)]
    failures = len(SPECIALISTS) - len(specialists)
    if not specialists:
        raise RuntimeError("All specialist analyses failed")
    score = calculate_property_score({item.specialist: item.score for item in specialists})
    confidence = sum(item.confidence for item in specialists) / len(SPECIALISTS)
    warnings = list(evidence.warnings)
    if failures:
        warnings.append(f"{failures} specialist analysis result(s) were unavailable; score weights were renormalized.")
    return AnalysisResult(
        analysis_id=str(uuid4()),
        command=request.command,
        property=request.property,
        specialists=specialists,
        overall_score=score,
        grade=score_grade(score),
        signal=property_signal(score),
        confidence=round(confidence, 2),
        summary=f"{request.property.address} received a {score}/100 score based on {len(specialists)} specialist analyses.",
        warnings=warnings,
        model_profile_id=request.model_profile_id or "foundry-default",
        agent_version=os.getenv("FOUNDRY_AGENT_VERSION", "local"),
    )


def build_realestate_agent(client: Any, toolbox: Any = None) -> Agent:
    repository = LocalSkillRepository()
    specialist_agents, instructions = create_specialist_agents(client, toolbox, repository)

    async def analyze_property(property_json: str) -> str:
        """Analyze a property supplied as a PropertyProfile JSON object."""
        profile = PropertyProfile.model_validate_json(property_json)
        evidence = manual_evidence(profile)
        specialists = await run_with_agents(
            evidence_json=evidence.model_dump_json(indent=2),
            agents=specialist_agents,
            instructions=instructions,
        )
        if not specialists:
            raise RuntimeError("All specialist analyses failed")
        score = calculate_property_score({item.specialist: item.score for item in specialists})
        result = AnalysisResult(
            analysis_id=str(uuid4()),
            command="analyze",
            property=profile,
            specialists=specialists,
            overall_score=score,
            grade=score_grade(score),
            signal=property_signal(score),
            confidence=round(sum(item.confidence for item in specialists) / len(SPECIALISTS), 2),
            summary=f"{profile.address} received a {score}/100 score.",
            warnings=evidence.warnings,
            model_profile_id=os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "foundry-default"),
            agent_version=os.getenv("FOUNDRY_AGENT_VERSION", "local"),
            skill_versions={role: "baseline" for role in SPECIALISTS},
        )
        return render_json(result)

    def calculate_mortgage(principal: float, annual_rate_percent: float, years: int = 30) -> str:
        """Calculate the monthly principal-and-interest mortgage payment."""
        return json.dumps(
            {
                "principal": principal,
                "annual_rate_percent": annual_rate_percent,
                "years": years,
                "monthly_principal_and_interest": round(
                    mortgage_payment(principal, annual_rate_percent, years), 2
                ),
                "disclaimer": DISCLAIMER,
            }
        )

    main_skill = repository.load("realestate-main")
    return Agent(
        client=client,
        name="foundry-realestate-agent",
        description="Research and analyze residential real estate with deterministic financial calculations.",
        instructions=f"""{main_skill.instructions}

Use calculate_mortgage for mortgage arithmetic.
Use analyze_property for full analysis when the user provides property facts.
Never invent missing property data. State assumptions and cite tool evidence.
{DISCLAIMER}
""",
        tools=[analyze_property, calculate_mortgage, *([toolbox] if toolbox is not None else [])],
        default_options={"store": False},
    )

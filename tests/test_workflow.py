import json
import unittest

from realestate_agent.agent import analyze_with_runner
from realestate_agent.models import AnalysisRequest, PropertyProfile, SpecialistResult


class AnalysisWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_analysis_aggregates_specialists(self) -> None:
        async def runner(role: str, evidence_json: str) -> SpecialistResult:
            self.assertEqual(json.loads(evidence_json)["property"]["price"], 425_000)
            return SpecialistResult(
                specialist=role,
                score={"comps": 74, "rental": 62, "neighborhood": 78, "investment": 72, "market": 68}[role],
                findings=[f"{role} finding"],
                confidence=0.8,
            )

        result = await analyze_with_runner(
            AnalysisRequest(
                property=PropertyProfile(
                    address="4821 Ridgeview Drive, Austin, TX 78735",
                    price=425_000,
                    bedrooms=3,
                    bathrooms=2,
                    square_feet=1_850,
                )
            ),
            runner,
        )

        self.assertEqual(result.overall_score, 71.1)
        self.assertEqual(result.grade, "A")
        self.assertEqual(result.signal, "BUY")
        self.assertEqual(result.confidence, 0.8)

    async def test_analysis_survives_one_specialist_failure(self) -> None:
        async def runner(role: str, _: str) -> SpecialistResult:
            if role == "market":
                raise TimeoutError("market source timed out")
            return SpecialistResult(specialist=role, score=70, confidence=0.8)

        result = await analyze_with_runner(
            AnalysisRequest(
                property=PropertyProfile(address="1 Main Street, Austin, TX", price=300_000)
            )
            ,
            runner,
        )

        self.assertEqual(result.overall_score, 70)
        self.assertEqual(result.confidence, 0.64)
        self.assertTrue(any("1 specialist" in warning for warning in result.warnings))


if __name__ == "__main__":
    unittest.main()

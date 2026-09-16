import unittest

from realestate_agent.calculations import (
    calculate_property_score,
    mortgage_payment,
    property_signal,
    rental_metrics,
    score_grade,
)


class MortgageTests(unittest.TestCase):
    def test_standard_fixed_rate_payment(self) -> None:
        payment = mortgage_payment(340_000, 6.75, 30)
        self.assertAlmostEqual(payment, 2205.23, places=2)

    def test_zero_interest_payment(self) -> None:
        self.assertAlmostEqual(mortgage_payment(120_000, 0, 10), 1000.0)


class RentalMetricTests(unittest.TestCase):
    def test_metrics_use_noi_before_debt_service(self) -> None:
        metrics = rental_metrics(
            purchase_price=425_000,
            monthly_rent=2_650,
            monthly_operating_expenses=875,
            monthly_debt_service=1_180,
            cash_invested=100_000,
        )

        self.assertEqual(metrics.gross_annual_rent, 31_800)
        self.assertEqual(metrics.net_operating_income, 21_300)
        self.assertEqual(metrics.annual_cash_flow, 7_140)
        self.assertAlmostEqual(metrics.cap_rate, 5.0118, places=4)
        self.assertAlmostEqual(metrics.cash_on_cash_return, 7.14, places=2)
        self.assertAlmostEqual(metrics.debt_service_coverage_ratio, 1.5042, places=4)


class ScoringTests(unittest.TestCase):
    def test_full_weighted_score(self) -> None:
        score = calculate_property_score(
            {
                "comps": 74,
                "rental": 62,
                "neighborhood": 78,
                "investment": 72,
                "market": 68,
            }
        )
        self.assertEqual(score, 71.1)
        self.assertEqual(score_grade(score), "A")
        self.assertEqual(property_signal(score), "BUY")

    def test_partial_score_is_renormalized(self) -> None:
        score = calculate_property_score({"comps": 80, "rental": 60})
        self.assertEqual(score, 71.1)

    def test_invalid_score_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate_property_score({"comps": 101})


if __name__ == "__main__":
    unittest.main()
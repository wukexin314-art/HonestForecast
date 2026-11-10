import math
import random
import unittest

from honestforecast.screening import ScreeningError, screen_candidates, spearman


class ScreeningTests(unittest.TestCase):
    def test_spearman_handles_ties(self):
        self.assertAlmostEqual(spearman([1, 2, 2, 4], [1, 2, 2, 4]), 1.0)

    def test_screening_reports_fdr_and_unregistered_search(self):
        candidates = {}
        for lag in range(4):
            candidates[f"lag_{lag}"] = [
                {
                    "date": f"2023-{index + 1:02d}-01",
                    "feature": index + lag,
                    "target": math.sin(index),
                }
                for index in range(10)
            ]
        result = screen_candidates(
            candidates, development_end="2023-10-01", registered_variants=2
        )
        self.assertTrue(result["multiplicity_warning"])
        self.assertEqual(result["tested_variants"], 4)
        self.assertTrue(all("adjusted_pvalue" in row for row in result["results"]))

    def test_one_true_lag_among_nulls_can_pass(self):
        # Circular shifts had a 1/n p-value floor, so BH over 4 candidates could never pass at n=40.
        generator = random.Random(3)
        target = [generator.gauss(0, 1) for _ in range(40)]
        candidates = {
            name: [
                {"date": f"{2020 + i // 12}-{i % 12 + 1:02d}-01", "feature": value, "target": target[i]}
                for i, value in enumerate(feature)
            ]
            for name, feature in {
                "true": [t + generator.gauss(0, 0.3) for t in target],
                **{f"null_{k}": [generator.gauss(0, 1) for _ in target] for k in range(3)},
            }.items()
        }
        result = screen_candidates(candidates, development_end="2023-12-01")
        eligible = {row["feature_id"] for row in result["results"] if row["eligible"]}
        self.assertEqual(eligible, {"true"})

    def test_screening_rejects_confirmation_rows(self):
        with self.assertRaises(ScreeningError):
            screen_candidates(
                {
                    "x": [
                        {"date": f"2023-{month:02d}-01", "feature": month, "target": month}
                        for month in range(1, 7)
                    ]
                },
                development_end="2023-05-01",
            )


if __name__ == "__main__":
    unittest.main()

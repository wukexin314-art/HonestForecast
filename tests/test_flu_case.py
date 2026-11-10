import unittest

import math
from datetime import date, timedelta

from honestforecast.flu_case import value_as_of
from honestforecast.flu_nowcast import wiki_features


class FluCaseTests(unittest.TestCase):
    def test_value_as_of_uses_only_releases_on_or_before_origin(self):
        ledger = {"nat": {"2018-01-06": (["2018-01-12", "2018-01-19", "2018-03-02"], [5.8, 5.9, 6.0])}}
        self.assertIsNone(value_as_of(ledger, "nat", "2018-01-06", "2018-01-11"))
        self.assertEqual(value_as_of(ledger, "nat", "2018-01-06", "2018-01-12"), 5.8)
        self.assertEqual(value_as_of(ledger, "nat", "2018-01-06", "2018-02-01"), 5.9)
        self.assertEqual(value_as_of(ledger, "nat", "2018-01-06", None), 6.0)

    def test_partial_week_growth_uses_only_sunday_to_wednesday(self):
        saturday = date(2026, 1, 3)
        daily = {(saturday - timedelta(days=k)).isoformat(): 100.0 for k in range(7)}
        daily.update({(saturday + timedelta(days=k)).isoformat(): 200.0 for k in range(1, 5)})
        daily[(saturday + timedelta(days=5)).isoformat()] = 10_000.0  # Thursday: not yet complete at origin
        self.assertAlmostEqual(wiki_features(daily, saturday.isoformat())[0], math.log(2.0))
        del daily[(saturday + timedelta(days=4)).isoformat()]
        self.assertIsNone(wiki_features(daily, saturday.isoformat()))


if __name__ == "__main__":
    unittest.main()

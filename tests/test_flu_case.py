import unittest

from honestforecast.flu_case import value_as_of


class FluCaseTests(unittest.TestCase):
    def test_value_as_of_uses_only_releases_on_or_before_origin(self):
        ledger = {"nat": {"2018-01-06": (["2018-01-12", "2018-01-19", "2018-03-02"], [5.8, 5.9, 6.0])}}
        self.assertIsNone(value_as_of(ledger, "nat", "2018-01-06", "2018-01-11"))
        self.assertEqual(value_as_of(ledger, "nat", "2018-01-06", "2018-01-12"), 5.8)
        self.assertEqual(value_as_of(ledger, "nat", "2018-01-06", "2018-02-01"), 5.9)
        self.assertEqual(value_as_of(ledger, "nat", "2018-01-06", None), 6.0)


if __name__ == "__main__":
    unittest.main()

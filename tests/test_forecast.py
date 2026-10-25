import importlib.util
import unittest
from datetime import UTC, datetime
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "forecast",
    Path(__file__).parents[1] / "custom_components/wattwanneer_public/forecast.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ForecastTests(unittest.TestCase):
    def test_prices_preserved_and_sorted(self):
        rows = module.parse_forecast(
            [
                {"datetime": "2026-10-25 03:00", "price_eur_kwh": 0},
                {"datetime": "2026-10-25 02:00", "price_eur_kwh": -0.00451},
            ]
        )
        self.assertEqual(rows[0]["price_eur_kwh"], -0.00451)
        self.assertEqual(rows[1]["price_eur_kwh"], 0)

    def test_cet_and_cest(self):
        for month, expected in [(1, "13:00"), (7, "14:00")]:
            self.assertTrue(
                module.local_hour(datetime(2026, month, 1, 12, tzinfo=UTC)).endswith(expected)
            )

    def test_clock_label_matches_single_feed_entry(self):
        rows = module.parse_forecast([{"datetime": "2026-10-25 02:00", "price_eur_kwh": 0.1}])
        for hour in (0, 1):
            self.assertEqual(
                module.select_hour(rows, datetime(2026, 10, 25, hour, tzinfo=UTC)),
                rows[0],
            )
        self.assertEqual(len(rows), 1)

    def test_next_hour_across_midnight(self):
        self.assertEqual(
            module.local_hour(datetime(2026, 10, 25, 22, tzinfo=UTC), 1),
            "2026-10-26 00:00",
        )

    def test_missing_is_not_zero(self):
        self.assertIsNone(module.select_hour([], datetime.now(UTC)))

    def test_invalid_payloads(self):
        for payload in [
            [],
            {},
            [{"datetime": "bad", "price_eur_kwh": 1}],
            [{"datetime": "2026-10-25 00:00", "price_eur_kwh": None}],
            [{"datetime": "2026-10-25 00:00", "price_eur_kwh": float("nan")}],
        ]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                module.parse_forecast(payload)

    def test_daily_selection(self):
        rows = module.parse_forecast([{"datetime": "2026-10-26 00:00", "price_eur_kwh": 0.2}])
        self.assertEqual(
            module.daily_rows(rows, datetime(2026, 10, 25, 12, tzinfo=UTC), 1),
            rows,
        )

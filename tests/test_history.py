import importlib.util
import unittest
from copy import deepcopy
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "history",
    Path(__file__).parents[1] / "custom_components/wattwanneer_public/history.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class MemoryStore:
    def __init__(self):
        self.data = None
        self.writes = 0
        self.fail_save = False

    async def async_load(self):
        return deepcopy(self.data)

    async def async_save(self, data):
        if self.fail_save:
            raise OSError("disk full")
        self.data = deepcopy(data)
        self.writes += 1


class HistoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_rows_and_fields_preserved_per_generation(self):
        store = MemoryStore()
        history = module.ForecastHistory(store)
        rows = [
            {
                "generated_at": "2026-10-25 06:00",
                "datetime": "2026-10-26 00:00",
                "price_eur_kwh": -0.00451,
                "source": "prediction",
            },
            {
                "generated_at": "2026-10-25 06:00",
                "datetime": "2026-10-26 01:00",
                "price_eur_kwh": 0,
            },
            {
                "generated_at": "2026-10-25 18:00",
                "datetime": "2026-10-26 00:00",
                "price_eur_kwh": 0.2,
            },
        ]
        await history.async_archive(rows)
        self.assertEqual(store.data["2026-10-25 06:00"], rows[:2])
        self.assertEqual(store.data["2026-10-25 18:00"], rows[2:])

    async def test_restart_and_duplicates_keep_original_prices(self):
        store = MemoryStore()
        row = {"generated_at": "2026-10-25 06:00", "price_eur_kwh": 0.1}
        await module.ForecastHistory(store).async_archive([row])
        restarted = module.ForecastHistory(store)
        await restarted.async_archive([{**row, "price_eur_kwh": 0.9}])
        self.assertEqual(store.data[row["generated_at"]], [row])
        self.assertEqual(store.writes, 1)
        new_row = {**row, "generated_at": "2026-10-26 06:00"}
        await restarted.async_archive([new_row])
        self.assertEqual(len(store.data), 2)
        self.assertEqual(store.data[row["generated_at"]], [row])

    async def test_missing_generation_is_not_archived(self):
        store = MemoryStore()
        await module.ForecastHistory(store).async_archive(
            [{"generated_at": value} for value in (None, "", "  ", 123)] + [{}]
        )
        self.assertEqual(store.writes, 0)

    async def test_failed_save_is_retried_without_losing_history(self):
        store = MemoryStore()
        history = module.ForecastHistory(store)
        old_row = {"generated_at": "old", "price_eur_kwh": 0}
        new_row = {"generated_at": "new", "price_eur_kwh": -1}
        await history.async_archive([old_row])
        store.fail_save = True
        with self.assertRaises(OSError):
            await history.async_archive([new_row])
        self.assertEqual(store.data, {"old": [old_row]})
        store.fail_save = False
        await history.async_archive([new_row])
        self.assertEqual(store.data, {"old": [old_row], "new": [new_row]})

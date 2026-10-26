"""Test archive responses without requiring a Home Assistant installation."""

import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, Mock, patch


class StubView:
    """Stand in for HA's response helpers; HA handles token authentication."""

    def json(self, data):
        return 200, data

    def json_message(self, message, status):
        return status, {"message": message}


def load_api():
    package = ModuleType("archive_api_test")
    package.__path__ = [
        str(Path(__file__).parents[1] / "custom_components/wattwanneer_public")
    ]
    http = ModuleType("homeassistant.components.http")
    http.HomeAssistantView = StubView
    storage = ModuleType("homeassistant.helpers.storage")
    storage.Store = Mock()
    spec = importlib.util.spec_from_file_location(
        "archive_api_test.api", Path(package.__path__[0]) / "api.py"
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {
        "archive_api_test": package,
        "homeassistant.components.http": http,
        "homeassistant.helpers.storage": storage,
    }):
        spec.loader.exec_module(module)
    return module


api = load_api()


class ArchiveApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.hass = object()
        self.view = api.ForecastHistoryView(self.hass)
        self.store = Mock()
        self.store.async_load = AsyncMock()
        self.factory = patch.object(api, "Store", return_value=self.store)
        self.factory.start()
        self.addCleanup(self.factory.stop)

    async def test_returns_all_stored_generations_and_fields(self):
        snapshots = {
            "old": [{"price_eur_kwh": -0.1, "source": "prediction"}],
            "new": [{"price_eur_kwh": 0, "extra": "preserved"}],
        }
        self.store.async_load.return_value = snapshots
        self.assertEqual(await self.view.get(None), (200, {"data": snapshots}))
        api.Store.assert_called_once_with(
            self.hass, 1, "wattwanneer_public.forecast_history"
        )
        self.assertTrue(self.view.requires_auth)
        self.assertEqual(self.view.url, "/api/wattwanneer_public/forecast_history")

    async def test_missing_archive_is_empty(self):
        self.store.async_load.return_value = None
        self.assertEqual(await self.view.get(None), (200, {"data": {}}))

    async def test_each_request_loads_persisted_history_again(self):
        self.store.async_load.side_effect = [{"old": []}, {"old": [], "new": []}]
        self.assertEqual(await self.view.get(None), (200, {"data": {"old": []}}))
        self.assertEqual(
            await self.view.get(None), (200, {"data": {"old": [], "new": []}})
        )
        self.assertEqual(api.Store.call_count, 2)

    async def test_read_errors_do_not_return_a_successful_empty_archive(self):
        for error in (OSError("unreadable"), ValueError("invalid JSON")):
            with self.subTest(error=error):
                self.store.async_load.side_effect = error
                status, body = await self.view.get(None)
                self.assertEqual(status, 500)
                self.assertEqual(body, {"message": "Unable to read stored forecast history."})

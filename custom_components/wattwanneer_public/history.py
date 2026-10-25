"""Persistent forecast snapshots, keyed by the feed's generation timestamp."""


class ForecastHistory:
    """Keep the first complete set of rows seen for each generated_at value."""

    def __init__(self, store):
        self._store = store
        self._snapshots = None

    async def async_archive(self, rows):
        """Save new generations before marking them as archived in memory."""
        if self._snapshots is None:
            stored = await self._store.async_load()
            self._snapshots = stored if stored is not None else {}

        generations = {}
        for row in rows:
            generated_at = row.get("generated_at")
            if isinstance(generated_at, str) and generated_at.strip():
                generations.setdefault(generated_at, []).append(dict(row))

        new_generations = {
            stamp: prices
            for stamp, prices in generations.items()
            if stamp not in self._snapshots
        }
        if new_generations:
            snapshots = {**self._snapshots, **new_generations}
            await self._store.async_save(snapshots)
            self._snapshots = snapshots

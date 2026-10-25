# WattWanneer Public

Home Assistant custom integration for the public [WattWanneer JSON feed](https://wattwanneer.nl/public/week_forecast.json). No API key. Independent project, unaffiliated with WattWanneer and separate from its official paid integration.

## Installation

### Manual (works immediately)

Copy `custom_components/wattwanneer_public` into your Home Assistant configuration's `custom_components` directory. Restart Home Assistant. Open **Settings → Devices & services → Add integration → WattWanneer Public** and submit the setup form.

### HACS

Add `https://github.com/groninge01/wattwanneer` under **HACS -> Custom repositories**, type **Integration**. Download WattWanneer Public, restart Home Assistant, and add it under Devices & services. The source must be pushed to GitHub before HACS can download it. This repository is not in the default HACS catalog.

The repository includes HACS validation and hassfest workflows. GitHub repository settings must have issues enabled, a description, and topics such as `home-assistant`, `hacs`, and `electricity-prices`.

## Sensors

- Current price and next hour price
- Today's average, minimum and maximum
- Tomorrow's average
- Forecast average, with every feed entry in its `forecast` attribute

All prices are EUR/kWh, as supplied in `price_eur_kwh`, excluding taxes and supplier fees. The integration preserves negative and zero prices. The `source` field distinguishes published day-ahead prices from model predictions. Forecasts are predictions, not guaranteed future tariffs.

One shared request runs at setup and twice daily at 06:00 and 18:00 in Home Assistant's configured time zone, with a 30-second timeout. Entities also update at each hour boundary without an additional request. A failed refresh makes sensors unavailable until a successful refresh. A missing current or tomorrow price makes only the affected sensors unavailable. Feed generation time is exposed as `generated_at`; an older generation may still contain valid hours. No prices are extrapolated beyond the feed.

Feed timestamps are local clock labels. The integration matches the current date and hour in **Europe/Amsterdam**, automatically using CET or CEST, regardless of HA's configured timezone. Each source entry remains a single entry; no hours are synthesized or removed. The raw timestamp strings remain unchanged in the forecast attribute.

## Stored forecast history

Every successful refresh archives all price rows for each new `generated_at` value in
`<config>/.storage/wattwanneer_public.forecast_history`. Home Assistant's storage file
contains a `data` object mapping each full generation timestamp to its rows, including
prices, hourly timestamps, sources, and other feed fields. Different generation times
on the same date are stored separately. Repeated generations keep their first snapshot
without adding duplicates or overwriting prices. Rows without a non-empty string
`generated_at` remain available to sensors but are not archived.

History survives restarts and is retained without automatic expiry, independently of
recorder retention. Collection starts when this version is installed; only generations
observed during a refresh can be saved. Sensors continue to show the latest feed.
If saving history fails, the refresh fails and the next refresh retries the archive.

## Forecast chart

With ApexCharts Card installed, replace the entity ID below with your actual Forecast average entity ID:

```yaml
type: custom:apexcharts-card
graph_span: 7d
span:
  start: day
now:
  show: true
series:
  - entity: sensor.wattwanneer_public_forecast_average
    name: Price
    unit: EUR/kWh
    data_generator: |
      return entity.attributes.forecast.map(p => [
        new Date(p.datetime.replace(' ', 'T')).getTime(), p.price_eur_kwh
      ]);
```

The example interprets local feed labels in the dashboard browser's timezone; use a browser set to Europe/Amsterdam. The integration's current-hour selection always uses Europe/Amsterdam.

## Development

Run `python -m unittest discover -s tests -v`. Pure feed tests require Python 3.11+ and timezone data (`python -m pip install tzdata` on Windows). CI runs these tests and compiles the integration. A running Home Assistant instance is required for an installation smoke test.

The public feed is an undocumented external dependency and may change or disappear. Full forecast attributes can add recorder storage; optionally exclude the Forecast average entity from recorder if you only use it for charts.

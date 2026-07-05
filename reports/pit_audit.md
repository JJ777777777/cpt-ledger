# Point-in-time (PIT) data audit

Classification of every feature source per PRD §6.3. PIT-risky sources are
excluded from historical training and captured live from launch.

| Source | PIT class | In v1 model | Historical training | Notes |
|---|---|---|---|---|
| ohlcv_daily | pit_safe | yes | allowed | Exchange candles; prices are never revised after close. |
| ohlcv_hourly | pit_safe | yes | allowed | Used for intraday-derived daily features (realized vol, volume profile). |
| funding_rates | pit_risky | no | EXCLUDED | Archive provenance unverified (PRD §10 Q4, open investigation). Captured live from launch; needed for M5 paper-portfolio shorts. Excluded from v1 model features. |
| fear_greed | pit_risky | no | EXCLUDED | alternative.me history may not reflect as-published values. Live-captured from launch with capture timestamp; excluded from v1 model features until live history suffices. |
| event_calendar | pit_risky | no | EXCLUDED | Entries are timestamped when added, so only entries added before a given date are known at that date. LLM context only; never a model feature. |
| cross_asset_tradfi | pit_risky | no | EXCLUDED | DXY / index futures need a PIT-validated source; not implemented in v1. Cross-crypto signals (BTC<->ETH) come from ohlcv_daily instead. |

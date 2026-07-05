# CPT — Public Prediction Ledger

This repository is the **public, tamper-evident ledger** of an automated daily
BTC/ETH prediction system. The system's code runs in a private repository; every
prediction it emits is published here *before* its outcome window opens, then
scored automatically after.

## What's here

| Path | Contents |
|---|---|
| `ledger/ledger.jsonl` | Append-only record stream: predictions, scores, missed-run records, briefing outcomes, corrections. One JSON object per line. |
| `ledger/proofs/` | OpenTimestamps manifests + `.ots` proofs anchoring each run's record hashes. |
| `site/index.html` | The dashboard: track record with confidence intervals, calibration, burn-in labeling. |
| `reports/` | Point-in-time data audit and walk-forward validation reports (simulated, clearly labeled — not the live record). |
| `models.json` | Model version manifest: version ids, dates, freeze status, SHA-256 of every model artifact file. |
| `verify_ledger.py` | Standalone, dependency-free verifier for the hash chain and proof manifests. |

## Verify it yourself

Run the bundled verifier (Python 3 standard library only, no dependencies):

```bash
python verify_ledger.py
```

It recomputes the full hash chain and cross-checks every anchored hash in
`ledger/proofs/` against the ledger. The script is ~100 lines — read it before
trusting it. What it checks, spelled out:

1. **Hash chain:** each record carries `prev_sha256` and `record_sha256`
   (SHA-256 over the canonical JSON of the record minus `record_sha256`,
   with keys sorted). Recompute the chain from the first line; any edit,
   deletion, or reordering breaks it.
2. **External anchor:** `ots verify <manifest>.ots` against the matching
   `run-*.txt` in `ledger/proofs/` proves the record hashes existed at
   anchor time. Rewriting history is therefore third-party detectable.
3. **Scoring:** every score record references its prediction and includes the
   tercile boundaries used, so hit/miss classification is recomputable from
   public data.
4. **Model versions:** each prediction names its `model_version`; `models.json`
   pins each version's artifact hashes.

Records flagged `research` predate the declared model freeze and are excluded
from the public track record (they exist so nothing is hidden — research-phase
iteration involves multiple testing and is quarantined, not deleted).

---

*Informational and educational only — not financial advice. Past performance
does not indicate future results.*

#!/usr/bin/env python3
"""Independent verifier for the CPT public prediction ledger.

Standard library only — no dependencies, no code from the (private) pipeline.
Run it from the root of the public ledger repository:

    python verify_ledger.py

It checks:
1. Hash chain: every record's `record_sha256` is the SHA-256 of its canonical
   JSON (keys sorted, separators (",", ":"), ensure_ascii=False, minus the
   `record_sha256` field itself), and every `prev_sha256` equals the previous
   record's hash (genesis = 64 zeros). Any edit, deletion, insertion, or
   reordering of history breaks the chain.
2. Proof manifests: every hash listed in ledger/proofs/run-*.txt corresponds
   to a record in the ledger, and every record hash appears in some manifest
   (records not yet covered by a manifest are reported, not failed — the
   current run's manifest may not be mirrored yet).

It does NOT verify the OpenTimestamps attestations themselves; for that,
install the client (`pip install opentimestamps-client`) and run
`ots verify <manifest>.txt.ots` on any manifest here.

Exit code 0 = chain verified; 1 = verification FAILED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

GENESIS = "0" * 64


def canonical_hash(record: dict) -> str:
    body = {k: v for k, v in record.items() if k != "record_sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_chain(ledger_path: Path) -> tuple[list[dict], list[str]]:
    """Returns (records, failures)."""
    failures: list[str] = []
    records: list[dict] = []
    prev = GENESIS
    with ledger_path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                failures.append(f"line {lineno}: not valid JSON ({e})")
                continue
            rec_id = rec.get("id", "<no id>")
            if rec.get("prev_sha256") != prev:
                failures.append(
                    f"line {lineno} (id={rec_id}): chain break - prev_sha256 does not "
                    f"match the previous record's hash"
                )
            if canonical_hash(rec) != rec.get("record_sha256"):
                failures.append(
                    f"line {lineno} (id={rec_id}): record_sha256 does not match the "
                    f"record's content - record altered"
                )
            prev = rec.get("record_sha256", prev)
            records.append(rec)
    return records, failures


def verify_manifests(records: list[dict], proofs_dir: Path) -> tuple[list[str], list[str]]:
    """Returns (failures, warnings)."""
    failures: list[str] = []
    warnings: list[str] = []
    ledger_hashes = {r.get("record_sha256") for r in records}
    manifested: set[str] = set()
    manifests = sorted(proofs_dir.glob("run-*.txt"))
    if not manifests:
        warnings.append(f"no proof manifests found under {proofs_dir}")
        return failures, warnings
    for manifest in manifests:
        for h in manifest.read_text(encoding="utf-8").split():
            if h not in ledger_hashes:
                failures.append(
                    f"{manifest.name}: anchored hash {h[:16]}... has no matching ledger "
                    f"record - ledger truncated or rewritten after anchoring"
                )
            manifested.add(h)
        if not manifest.with_name(manifest.name + ".ots").exists():
            warnings.append(f"{manifest.name}: no .ots proof yet (anchor pending)")
    unanchored = ledger_hashes - manifested
    if unanchored:
        warnings.append(
            f"{len(unanchored)} record(s) not yet covered by a mirrored manifest "
            f"(expected briefly for the most recent run)"
        )
    return failures, warnings


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=here / "ledger" / "ledger.jsonl")
    parser.add_argument("--proofs", type=Path, default=here / "ledger" / "proofs")
    args = parser.parse_args(argv)

    if not args.ledger.exists():
        print(f"FAIL: ledger file not found: {args.ledger}")
        return 1

    records, failures = verify_chain(args.ledger)
    man_failures, warnings = verify_manifests(records, args.proofs)
    failures += man_failures

    for w in warnings:
        print(f"note: {w}")
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print(f"\nVERIFICATION FAILED - {len(failures)} problem(s) in {len(records)} record(s).")
        return 1
    by_type: dict[str, int] = {}
    for r in records:
        by_type[r.get("record_type", "?")] = by_type.get(r.get("record_type", "?"), 0) + 1
    summary = ", ".join(f"{n} {t}" for t, n in sorted(by_type.items()))
    print(f"OK: hash chain verified - {len(records)} records ({summary}).")
    print("To also verify the external Bitcoin anchor: ots verify <manifest>.txt.ots")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

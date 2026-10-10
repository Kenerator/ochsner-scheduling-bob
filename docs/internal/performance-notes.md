# Performance Evidence

Updated 2026-10-09; integration working tree based on `a43fb61532a62f83b91dd862099419b385caee98`.
The 400 ms goal is useful feedback, not a model completion SLA or readiness badge.

Measured using `.venv/bin/python scripts/measure_local.py --samples 30` on Darwin
arm64 / Python 3.11.13, one sequential client, no deliberate load. Real loopback
JSON transport → shared Conversation/Session → unchanged supplied HTTP service
(alternating public provider discovery and local Help) → decoded response:

| Samples | p50 | p95 | Maximum | Writes/model calls |
| --- | --- | --- | --- | --- |
| 30 | 0.931 ms | 2.163 ms | 2.358 ms | 0 / 0 |

This measures completion at the HTTP boundary, **not browser paint**, internet
latency or concurrent capacity. Local UI handlers show Working before awaiting
fetch; browser start-session showed 42 ms and paired join 25 ms in this manual
sample, not a percentile or frame-timing measurement. Genuine model timings are
case-specific in [qualification](live-qualification.md), not folded into this table.

`tests/test_latency_evidence.py` verifies the actual measurement path and bounds,
not a flaky absolute-time gate. `test_interaction_service.py` tests local safety,
reads and unrelated sessions remain responsive during a deliberately blocked
language request. `tests/widget_harness.mjs` proves Help is not swallowed by the
shipped pending-request guard, but is a DOM double rather than browser timing.

Deferred: browser frame/assistive-tech timing, representative load, non-Mac hosts,
real upstream service latency and production targets. Re-measure after boundary
or dependency changes; do not claim these numbers as general capacity.

## Final-source refresh — 2026-10-09

Code/test revision `5e7ae0c6b1ae29d198f734a0c26e2c96e525b961`; same explicit Python 3.11.13,
Darwin arm64. Reran 30 sequential requests: p50 **1.202 ms**, p95 **2.807 ms**,
max **2.849 ms**, no model call or effect; p95 remained below the 400 ms local
transport target. This supersedes the earlier dirty-source sample, not its
limitations. Browser paint, accessibility, concurrent load/capacity and external
service/model latency were not measured by this script.

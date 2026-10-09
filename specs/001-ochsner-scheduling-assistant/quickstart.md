# Quickstart Validation Guide

Required target: macOS ARM with an explicit Python 3.11+ executable and disposable project environment. Use only synthetic fixtures.

1. Create/activate the project-local environment and install pinned application/UI dependencies; do not modify global Python.
2. Start the supplied mock API on the documented loopback port and verify the owned process; keep API and UI ports distinct.
3. Run `PYTHONPATH=src python3 -m unittest discover -s tests -v` with the explicit compatible interpreter.
4. Run the success demo: public discovery → local identity → returned slot → immutable proposal → separate confirmation → validated receipt.
5. Run failure demos for identity correction, invalid date, no match, 409, outage, unknown booking, unknown handoff, help/medical boundary, replay, and support takeover/return.
6. Launch the Marimo patient/support views, exercise two isolated synthetic sessions, and inspect the lower Developer Mode panel.
7. Reset only BOB-owned mock/application processes and confirm no stale receipt or proposal survives outside the documented boundary.

Expected evidence and state definitions are in [data-model.md](data-model.md) and [interaction-contract.md](contracts/interaction-contract.md). Full completion also requires source-bound `docs/internal/video-notes.md`, UI asset provenance, persona/story/test crosswalk, and as-built docs updated from actual code/tests.

# Research: Ochsner Best-of-Breed Scheduling Assistant

## Decisions

- Deterministic core with thin adapters: application code owns identity, consent, policy, effects, certainty, and replay.
- Marimo first, dedicated frontend only on documented interaction/support blocker.
- Standalone ZEN policy and RapidFuzz public suggestions; no nxusKit runtime or multi-engine abstraction.
- In-memory synthetic state with explicit unknown latches; no durable/distributed production guarantee.
- Supplied HTTP mock remains unchanged; adapter validates its contract and failure injection.
- Genuine model qualification follows offline behavior; credentials, cost, and model choice are not inferred.

## Evidence and alternatives

Bound intake findings identify identity-correction, stale-consent, terminal-help, diagnostic-constructor, and handoff-truth failures. The design addresses them with revocation, current confirmation, reachable safety routes, constructor-level event sinks, and separate receipt/demo-support state. Merging original applications was rejected because their controllers and policies conflict. Persistent production storage, real authentication, live contact-center delivery, and clinical capability remain out of scope.

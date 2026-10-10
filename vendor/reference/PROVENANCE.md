# Supplied synthetic runtime subset

Adopted 2026-10-09 for the approved private BOB repository only. These five files
are byte-identical to the supplied scheduling assignment runtime. Raw intake and
the complete RFP remain ignored. No public redistribution license, sponsor
endorsement, production integration or real-patient-data permission is claimed.

| File | SHA-256 |
| --- | --- |
| mock-api/server.py | 9597f92fe3ec19c16e08b1491fbac12e1ffed87bd41c137be1e638addac2d1f1 |
| data/appointments.json | 02be083e7d1d5841b29a4bb1fb663ba49f6c3d9ed47c236fa67545e8432d0d65 |
| data/patients.json | 4bc471bef84eccee513b2ae15127cbf532b6aa47f151831ff7c2a6b832889d48 |
| data/providers.json | 0745b592a15821474ebee45f868c3ed90d4bf24846903a17e7da0b210a3d92d6 |
| data/slots.json | 340bb75c9c737281de2e48b7c299141ce4c27e41001c0172c4e8f0927cf0ce9b |

The service binds loopback, stores synthetic appointments in memory and supplies
relative-date timestamps with its fixed `-05:00` offset. Display its returned
`startTime` literally; do not reinterpret the fixtures as timezone/DST proof.
The local runner owns its process/port and suppresses raw service output. Tests
use fresh original Store/Handler instances and separately sanitized request audits.

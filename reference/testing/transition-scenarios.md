# Transition tests, not just happy-path scripts

Select the cases relevant to the application. Keep fixtures synthetic; supplied policies and API contracts remain authoritative. These suggestions create no new product requirements or permissions.

| Transition | Useful assertion |
| --- | --- |
| Selection or identity changes | Prior confirmation/proposed action is invalidated; current state is distinguishable from history. |
| User refuses or cancels | No write occurs; a stale proposal cannot later be committed. |
| Timeout/error after a write request | Unknown outcome is not called failure/success without evidence, and retry is not assumed safe. |
| Service returns stale/unavailable data | Refresh/reselection is offered; no invented availability or outcome. |
| User asks for help or recovery | The path remains reachable without completing the broken path first. |
| Permission or policy rejects an action | The denial is visible; there is no alternate-route bypass. |
| Reset/restart/repeated submission | State and idempotency behavior match the contract. |

For each chosen case, record initial state, event, expected effects/non-effects, actual result, mode (fixture/service/browser/live), and source revision. A unit result is not browser or live-model proof. Include primary-user and support/admin needs where relevant; do not automatically add an admin console or every reasoning engine.

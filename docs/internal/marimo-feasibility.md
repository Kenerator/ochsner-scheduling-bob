# Early Marimo feasibility checkpoint

Updated 2026-10-09; in progress, before substantial patient UI implementation.
Python 3.11.13 / Darwin arm64, Marimo 0.25.1, AnyWidget 0.11.0.

The disposable `apps/feasibility.py` first showed standard form submission does
not expose unsent input to Python. The supported AnyWidget bridge did expose a
public draft and focus while preserving the DOM input. This is not a reason to
select the authorized frontend fallback.

`apps/paired_probe.py` / `.js` use the canonical loopback BrowserService outside
the reactive notebook kernel. Through actual browser tabs, a patient created a
one-use pairing grant, and a separate support tab joined. The support projection
showed the unsent `Public synthetic draft` and expanded disclosure read-only,
with a freshness/age label. A third independent session started with a blank
draft, collapsed disclosure and revision zero. Polling preserved the original
draft/disclosure. Private identity controls are intentionally absent from this
throwaway probe, not silently mirrored. Capability tokens stay in per-tab session
storage and headers, never references or URLs.

Observed caveat: tabs restored across replacement of the notebook server
intermittently displayed `kernel not found` / reconnect while the independent
sidecar continued to work. A fresh tab connected without that warning. This is
not yet a fully qualified refresh/restart path and is retained as an integration
check, not dismissed as a passed framework test. Focus acknowledgements correctly
become null when the draft loses focus; exact last-observed focus and scroll
require final paired UI verification. The screenshot in `/private/tmp/` is
probe evidence only, not finished-product footage.

Additional actual probe evidence: refresh restored the public draft and open
disclosure; paired takeover/return produced a stale interval until the patient
acknowledged the new revision. A real shadow-DOM focus defect was observed
(`document.activeElement` identified the widget host), corrected using
`input.matches(':focus')`, and rechecked through the inactive support DOM: the
receipt then showed `focus: message` and the exact public draft.

Actual shared-core Help was captured and sealed. Open and Step showed
`simulation_only: true`, `executable_authority: false`, index -1 then 0, while
live revision stayed 2 with no current attempt. Starting capture late correctly
reported `incomplete_capture`, not invented full fidelity. The initial failed
open attempt mixed asynchronous dependent clicks without awaiting the visible
capture result; individually checked controls succeeded. Backend JSON roundtrip
and 17 interaction tests also passed, but those do not replace browser evidence.

Final early check passed through visible controls: hold patient revision 2,
advance to revision 3 using paired Help, submit the held Help revision. The
patient visibly reported “This screen is out of date. Review the current screen
before acting.” and stayed at revision 3. No write controls or model calls were
part of this checkpoint. Screenshot: `/private/tmp/bob-marimo-stale-probe.jpg`.

The early framework checkpoint is sufficient to continue with Marimo. Final
product reconnect/fidelity will be qualified again after integration; this
probe does not establish full renderer/replay parity. Product launch will retain
notebook sessions for the review session and preserve public UI state across
reconstruction; no server-side consent will be stored in browser state. No
framework fallback is selected.

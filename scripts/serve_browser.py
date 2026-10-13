"""Owned synthetic sidecar. Start Marimo separately; never manages unrelated ports."""
import argparse
from pathlib import Path
import signal
import sys

from mock_lifecycle import OwnedMock
from ochsner_bob.http_mock import HttpMockAdapter
from ochsner_bob.interaction_service import InteractionService
from ochsner_bob.local_transport import make_server
from ochsner_bob.language import LanguageAdapter
from ochsner_bob.model_budget import ModelBudget

ROOT=Path(__file__).resolve().parents[1]


def language_for_launch(enabled, *, unlimited_today=False):
    # CLI, browser and qualification share one ledger. A new effect namespace
    # must never replenish the model budget. Construction does not dispatch.
    options={"unlimited_today":True} if unlimited_today else {}
    return LanguageAdapter(budget=ModelBudget(ROOT/".bob-local/model-budget.json",**options)) if enabled else None


def server_for_launch(service,port,ui_port):
    server=make_server(service,port=port,allowed_origin=f"http://127.0.0.1:{ui_port}")
    # BaseServer invokes this on its poll loop, even without patient activity.
    # Maintenance handles/report errors categorically and never touches effects.
    server.service_actions=service.maintain_retention
    return server


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port",type=int,default=28451)
    parser.add_argument("--ui-port",type=int,default=28450)
    parser.add_argument("--namespace",type=Path,default=Path(".bob-local/browser"))
    parser.add_argument("--openai",action="store_true",help="explicit bounded public-language opt-in; runtime environment still required")
    parser.add_argument("--unlimited-today",action="store_true",help="BOB-only Oct 12 Central budget opt-in; expires 2026-10-13T05:00:00Z, requires --openai")
    parser.add_argument("--scenario",choices=("happy_path_booking","provider_lookup","no_patient_match","multiple_patient_matches","slot_conflict","no_availability","api_failure","unsupported_request"))
    args=parser.parse_args(argv)
    if args.unlimited_today and not args.openai:
        parser.error("--unlimited-today requires --openai; no service was started.")
    if sys.version_info<(3,11) or not 0<=args.port<=65535 or not 1<=args.ui_port<=65535:
        parser.error("Use Python 3.11+ and numeric loopback ports.")
    def stop(_signal,_frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    try:
        with OwnedMock() as mock:
            service=InteractionService(lambda:HttpMockAdapter(mock.base_url,scenario=args.scenario),args.namespace/"effects.json",language=language_for_launch(args.openai,unlimited_today=args.unlimited_today))
            server=server_for_launch(service,args.port,args.ui_port)
            try:
                print(f"BOB local backend ready: http://127.0.0.1:{server.server_port}",flush=True)
                if args.unlimited_today:
                    print("BOB budget opt-in applies only 2026-10-12T05:00:00Z through 2026-10-13T05:00:00Z (exclusive); ordinary limits apply outside that window. Accounting/storage guards remain.",flush=True)
                server.serve_forever()
            finally:
                server.server_close()
    except KeyboardInterrupt:
        return 0
    except (ValueError,RuntimeError,OSError):
        print("Local setup unavailable; check ports/private namespace. No existing process was stopped.",file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())

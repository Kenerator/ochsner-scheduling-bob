import argparse

from .core import BobSession, MockSchedulingApi


def main():
    parser = argparse.ArgumentParser(description="Synthetic Ochsner scheduling assistant")
    parser.add_argument("--scenario", choices=("success", "unknown"), default="success")
    args = parser.parse_args()
    api = MockSchedulingApi()
    session = BobSession(api)
    session.resolve_identity("5045550100", "1980-01-01", "70112")
    provider = session.discover("cardio", "new orleans")[0]
    slot = session.find_slots(provider["id"])[0]
    proposal = session.propose(slot["id"])
    session.confirm(proposal["id"])
    if args.scenario == "unknown":
        from .core import UnknownOutcome
        api.next_booking = UnknownOutcome("simulated timeout")
    print(session.book())


if __name__ == "__main__":
    main()

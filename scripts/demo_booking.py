from ochsner_bob import BobSession, MockSchedulingApi, UnknownOutcome


def main():
    api = MockSchedulingApi()
    session = BobSession(api)
    session.resolve_identity("5045550100", "1980-01-01", "70112")
    provider = session.discover("cardio", "new orleans")[0]
    slot = session.find_slots(provider["id"])[0]
    proposal = session.propose(slot["id"])
    print({"proposal": proposal, "bookings_before_confirmation": len(api.bookings)})
    session.confirm(proposal["id"])
    print({"receipt": session.book().__dict__, "bookings": api.bookings})
    session2 = BobSession(api)
    session2.resolve_identity("5045550100", "1980-01-01", "70112")
    second_provider = session2.discover("cardio", "new orleans")[0]
    session2.propose(session2.find_slots(second_provider["id"])[0]["id"])
    session2.confirm(session2.proposal["id"])
    api.next_booking = UnknownOutcome("simulated lost response")
    print({"unknown": session2.book().__dict__, "retry": "blocked"})


if __name__ == "__main__":
    main()

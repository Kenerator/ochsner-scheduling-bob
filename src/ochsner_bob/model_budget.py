"""Private, durable reservations with ordinary $20 / 200-call dispatch ceilings.

No prompts, response text, credentials or request identifiers are persisted.
Standard direct OpenAI text pricing reviewed 2026-10-09:
https://developers.openai.com/api/docs/models/gpt-5.4-mini
https://developers.openai.com/api/docs/models/gpt-5.4
Each request reserves its full context at worst-case uncached input pricing PLUS
its bounded output. This deliberately avoids a guessed tokenizer upper bound.
Unknown usage/crashes keep that reservation forever; call counts never refund.
"""
from contextlib import contextmanager
from decimal import Decimal
import fcntl
import json
import math
import os
from pathlib import Path
import tempfile
from threading import Lock, RLock
import time

from .journal import EffectJournal


DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
_NANOS = 1_000_000_000
# Fixed Oct 12 Central authorization, not a rolling "today" or renewable grant.
_UNLIMITED_START = 1791781200  # 2026-10-12T05:00:00Z
_UNLIMITED_END = 1791867600  # 2026-10-13T05:00:00Z
_MAX_LEDGER_BYTES = 100000  # Existing technical storage bound, not a spend cap.
# context, input/cached/output nanodollars per token, long-context threshold.
# Only pinned, price-verified standard direct text models are eligible.
_RATES = {
    DEFAULT_MODEL: (400_000, 750, 75, 4500, None),
    "gpt-5.4-2026-03-05": (1_050_000, 2500, 250, 15000, 272_000),
}
PRICED_MODELS = frozenset(_RATES)
_GUARD = Lock()
_LOCKS = {}


class BudgetError(RuntimeError):
    """Sanitized denial: no reservation means no dispatch permission."""


def _money(nanos):
    return f"{Decimal(nanos) / _NANOS:.9f}"


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError()
        value[key] = item
    return value


def _constant(_):
    raise ValueError()


def _usage(value, max_output, model=DEFAULT_MODEL):
    fields = {"input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens"}
    if type(value) is not dict or set(value) != fields:
        return None
    if any(type(item) is not int or item < 0 for item in value.values()):
        return None
    if (value["input_tokens"] > _RATES[model][0] or value["output_tokens"] > max_output
            or value["cached_input_tokens"] > value["input_tokens"]
            or value["reasoning_output_tokens"] > value["output_tokens"]):
        return None
    return dict(value)


def _cost(value, model=DEFAULT_MODEL):
    _, input_rate, cached_rate, output_rate, threshold = _RATES[model]
    if threshold is not None and value["input_tokens"] > threshold:
        # Official >272k uplift: 2x input, 1.5x output for the full request.
        input_rate *= 2
        cached_rate *= 2
        output_rate = output_rate * 3 // 2
    return ((value["input_tokens"] - value["cached_input_tokens"]) * input_rate
            + value["cached_input_tokens"] * cached_rate + value["output_tokens"] * output_rate)


def _maximum(model, max_output):
    if type(model) is not str or model not in PRICED_MODELS or type(max_output) is not int or not 1 <= max_output <= 512:
        raise BudgetError("Unpriced model or unsupported request bound; dispatch blocked.")
    context, input_rate, _, output_rate, threshold = _RATES[model]
    if threshold is not None:
        input_rate *= 2
        output_rate = output_rate * 3 // 2
    return context * input_rate + max_output * output_rate


class ModelBudget:
    """reserve(model=..., max_output_tokens=512), then settle(id, usage|None).

    Share ONE path across all callers under the grant. Independent paths cannot
    enforce an account-wide ceiling. Limits may be stricter, never exceed the
    ordinary grant, and cannot change on reopen. Explicit unlimited_today opts
    into the fixed BOB-only window; it changes NEW-reservation policy only.
    Historical valid entries remain readable/settleable after expiry, including
    over-cap entries. The runner always uses the same default path.
    """

    def __init__(self, path: Path, *, max_calls=200, ceiling_usd="20", unlimited_today=False, clock=None,
                 _existing_only=False):
        self._blocked = False
        self._seen = False
        try:
            clock = time.time if clock is None else clock
            ceiling = Decimal(str(ceiling_usd))
            if (type(unlimited_today) is not bool or type(_existing_only) is not bool or not callable(clock)
                    or type(max_calls) is not int or not 1 <= max_calls <= 200
                    or not ceiling.is_finite() or not 0 < ceiling <= 20
                    or ceiling * _NANOS != (ceiling * _NANOS).to_integral_value()):
                raise ValueError()
            self.max_calls = max_calls
            self.ceiling = int(ceiling * _NANOS)
            self._unlimited_today = unlimited_today
            self._clock = clock
            self._existing_only = _existing_only
            supplied = Path(path).absolute()
            parent = supplied.parent.resolve(strict=_existing_only)
            if not _existing_only:
                try:
                    parent.mkdir(mode=0o700)
                except FileExistsError:
                    pass
                else:
                    EffectJournal._sync_directory(parent.parent)
            self.path = parent / supplied.name
            self._lock_path = self.path.with_name(self.path.name + ".lock")
            with _GUARD:
                self._mutex = _LOCKS.setdefault(self.path, RLock())
            with self._locked() as fd:
                document = self._read()
                if document is None:
                    self._write(self._empty(), fd)
        except Exception:
            raise BudgetError("Private budget unavailable or invalid; dispatch blocked.") from None

    def _empty(self):
        return {"version": 1, "max_calls": self.max_calls, "ceiling_nanos": self.ceiling, "calls": []}

    @contextmanager
    def _locked(self):
        if self._blocked:
            raise BudgetError("Budget storage failed; dispatch blocked.")
        with self._mutex:
            fd = None
            try:
                info = self.path.parent.stat()
                if info.st_uid != os.getuid() or info.st_mode & 0o077:
                    raise ValueError()
                flags = os.O_RDONLY if self._existing_only else os.O_RDWR | os.O_CREAT
                fd = os.open(self._lock_path, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
                EffectJournal._private_file(fd)
                fcntl.flock(fd, fcntl.LOCK_EX)
                marker = os.read(fd, 2)
                if marker not in (b"", b"1") or ((self._seen or self._existing_only) and marker != b"1"):
                    raise ValueError()
                self._seen = self._seen or marker == b"1"
                yield fd
            except BudgetError:
                raise
            except Exception:
                self._blocked = True
                raise BudgetError("Private budget storage invalid; dispatch blocked.") from None
            finally:
                if fd is not None:
                    os.close(fd)

    def _read(self):
        try:
            fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            if self._seen:
                raise ValueError()
            return None
        try:
            EffectJournal._private_file(fd)
            raw = os.read(fd, _MAX_LEDGER_BYTES + 1)
            if os.fstat(fd).st_size > _MAX_LEDGER_BYTES or len(raw) > _MAX_LEDGER_BYTES:
                raise ValueError()
        finally:
            os.close(fd)
        document = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
        if (type(document) is not dict or set(document) != set(self._empty())
                or type(document["version"]) is not int or document["version"] != 1
                or type(document["max_calls"]) is not int or document["max_calls"] != self.max_calls
                or type(document["ceiling_nanos"]) is not int or document["ceiling_nanos"] != self.ceiling
                or type(document["calls"]) is not list):
            raise ValueError()
        for call in document["calls"]:
            if (type(call) is not dict or set(call) != {"model", "max_output_tokens", "reserved_nanos", "status", "usage"}
                    or type(call["status"]) is not str or call["status"] not in {"reserved", "unknown", "known"}
                    or type(call["reserved_nanos"]) is not int
                    or call["reserved_nanos"] != _maximum(call["model"], call["max_output_tokens"])):
                raise ValueError()
            if call["status"] == "known":
                if _usage(call["usage"], call["max_output_tokens"], call["model"]) is None:
                    raise ValueError()
            elif call["usage"] is not None:
                raise ValueError()
        # Ceilings are dispatch policy, not structural validity. Enforcing them
        # here would strand legitimate window reservations at midnight/reopen.
        return document

    @staticmethod
    def _encoded(document):
        raw = json.dumps(document, allow_nan=False).encode("utf-8")
        if len(raw) > _MAX_LEDGER_BYTES:
            raise BudgetError("Budget storage capacity reached; dispatch blocked.")
        return raw

    def _settlement_headroom(self, document):
        # Reserve enough bytes for every outstanding call's largest valid usage.
        # A full ledger must not prevent late accounting after the window ends.
        future = {**document, "calls": [
            {**call, "status": "known", "usage": {
                "input_tokens": _RATES[call["model"]][0],
                "output_tokens": call["max_output_tokens"],
                "cached_input_tokens": _RATES[call["model"]][0],
                "reasoning_output_tokens": call["max_output_tokens"]}}
            if call["status"] == "reserved" else call for call in document["calls"]]}
        self._encoded(future)

    def _window_status(self):
        if not self._unlimited_today:
            return "disabled"
        now = self._clock()
        if type(now) not in (int, float) or not math.isfinite(now):
            raise BudgetError("Budget window clock unavailable; dispatch blocked.")
        return "not_started" if now < _UNLIMITED_START else "active" if now < _UNLIMITED_END else "expired"

    def _write(self, document, marker):
        if self._existing_only:
            raise BudgetError("Read-only budget preflight cannot change storage.")
        raw = self._encoded(document)  # Reject before touching marker or file.
        temporary = None
        try:
            if not self._seen:
                os.lseek(marker, 0, os.SEEK_SET)
                os.write(marker, b"1")
                os.fsync(marker)
                EffectJournal._sync_directory(self.path.parent)
                self._seen = True
            fd, temporary = tempfile.mkstemp(prefix=".model-budget-", dir=self.path.parent)
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            temporary = None
            EffectJournal._sync_directory(self.path.parent)
        finally:
            if temporary is not None:
                os.unlink(temporary)

    @staticmethod
    def _liability(document):
        return sum(_cost(call["usage"], call["model"]) if call["status"] == "known" else call["reserved_nanos"]
                   for call in document["calls"])

    def reserve(self, *, model, max_output_tokens=512):
        maximum = _maximum(model, max_output_tokens)
        with self._locked() as marker:
            document = self._prepared_reservation(self._read(), model, max_output_tokens, maximum)
            self._write(document, marker)
            return len(document["calls"])

    def _prepared_reservation(self, document, model, max_output_tokens, maximum):
        # Shared by real reservation and read-only readiness; preparing this
        # in-memory candidate grants nothing until reserve durably writes it.
        if self._window_status() != "active" and (len(document["calls"]) >= self.max_calls
                or self._liability(document) + maximum > self.ceiling):
            raise BudgetError("Call count or dollar ceiling reached; dispatch blocked.")
        prepared = {**document, "calls": [*document["calls"], {
            "model": model, "max_output_tokens": max_output_tokens,
            "reserved_nanos": maximum, "status": "reserved", "usage": None}]}
        self._settlement_headroom(prepared)
        return prepared

    def settle(self, reservation, usage):
        with self._locked() as marker:
            document = self._read()
            if type(reservation) is not int or not 1 <= reservation <= len(document["calls"]):
                raise BudgetError("Invalid budget reservation.")
            call = document["calls"][reservation - 1]
            if call["status"] != "reserved":
                raise BudgetError("Budget reservation was already settled; no refund.")
            cleaned = _usage(usage, call["max_output_tokens"], call["model"])
            call.update(status="known" if cleaned is not None else "unknown", usage=cleaned)
            self._write(document, marker)
            return {"status": call["status"], "cost_usd": _money(_cost(cleaned, call["model"])) if cleaned is not None else None,
                    "reserved_usd": _money(call["reserved_nanos"])}

    def snapshot(self):
        with self._locked():
            document = self._read()
            calls = document["calls"]
            known = [call for call in calls if call["status"] == "known"]
            liability = self._liability(document)
            return {"calls": len(calls), "known_calls": len(known), "unknown_calls": len(calls) - len(known),
                "max_calls": self.max_calls, "ceiling_usd": _money(self.ceiling),
                "unlimited_today": {"opted_in": self._unlimited_today, "status": self._window_status(),
                    "starts_at": "2026-10-12T05:00:00Z", "expires_at": "2026-10-13T05:00:00Z"},
                **{key: sum(call["usage"][key] for call in known) for key in
                   ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens")},
                "known_cost_usd": _money(sum(_cost(call["usage"], call["model"]) for call in known)),
                "liability_usd": _money(liability), "remaining_usd": _money(self.ceiling - liability)}


def preflight_budget(path: Path, *, model: str, unlimited_today: bool = False) -> None:
    """Validate existing canonical readiness; never initialize, reserve or write.

    This is a point-in-time check, not dispatch authority. The actual model host
    must use the same ledger/explicit opt-in and reserve again before transport.
    Missing ledger/marker, unsafe storage, exhausted policy or capacity fail closed.
    """
    maximum = _maximum(model, 512)
    budget = ModelBudget(path, unlimited_today=unlimited_today, _existing_only=True)
    with budget._locked():
        budget._prepared_reservation(budget._read(), model, 512, maximum)

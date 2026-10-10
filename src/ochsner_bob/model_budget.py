"""Private, durable call reservations for the Operator's $20 / 200-call grant.

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
import os
from pathlib import Path
import tempfile
from threading import Lock, RLock

from .journal import EffectJournal


DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
_NANOS = 1_000_000_000
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
    grant, and cannot change on reopen. Only an explicit new Operator grant may
    establish a fresh namespace; the runner always uses the same default path.
    """

    def __init__(self, path: Path, *, max_calls=200, ceiling_usd="20"):
        self._blocked = False
        self._seen = False
        try:
            ceiling = Decimal(str(ceiling_usd))
            if (type(max_calls) is not int or not 1 <= max_calls <= 200
                    or not ceiling.is_finite() or not 0 < ceiling <= 20
                    or ceiling * _NANOS != (ceiling * _NANOS).to_integral_value()):
                raise ValueError()
            self.max_calls = max_calls
            self.ceiling = int(ceiling * _NANOS)
            supplied = Path(path).absolute()
            parent = supplied.parent.resolve()
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
                fd = os.open(self._lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
                EffectJournal._private_file(fd)
                fcntl.flock(fd, fcntl.LOCK_EX)
                marker = os.read(fd, 2)
                if marker not in (b"", b"1") or (self._seen and marker != b"1"):
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
            raw = os.read(fd, 100001)
            if os.fstat(fd).st_size > 100000 or len(raw) > 100000:
                raise ValueError()
        finally:
            os.close(fd)
        document = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
        if (type(document) is not dict or set(document) != set(self._empty())
                or type(document["version"]) is not int or document["version"] != 1
                or type(document["max_calls"]) is not int or document["max_calls"] != self.max_calls
                or type(document["ceiling_nanos"]) is not int or document["ceiling_nanos"] != self.ceiling
                or type(document["calls"]) is not list or len(document["calls"]) > self.max_calls):
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
        if self._liability(document) > self.ceiling:
            raise ValueError()
        return document

    def _write(self, document, marker):
        temporary = None
        try:
            if not self._seen:
                os.lseek(marker, 0, os.SEEK_SET)
                os.write(marker, b"1")
                os.fsync(marker)
                EffectJournal._sync_directory(self.path.parent)
                self._seen = True
            fd, temporary = tempfile.mkstemp(prefix=".model-budget-", dir=self.path.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                os.fchmod(stream.fileno(), 0o600)
                json.dump(document, stream, allow_nan=False)
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
            document = self._read()
            if (len(document["calls"]) >= self.max_calls
                    or self._liability(document) + maximum > self.ceiling):
                raise BudgetError("Call count or dollar ceiling reached; dispatch blocked.")
            document["calls"].append({"model": model, "max_output_tokens": max_output_tokens,
                "reserved_nanos": maximum, "status": "reserved", "usage": None})
            self._write(document, marker)
            return len(document["calls"])

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
                **{key: sum(call["usage"][key] for call in known) for key in
                   ("input_tokens", "output_tokens", "cached_input_tokens", "reasoning_output_tokens")},
                "known_cost_usd": _money(sum(_cost(call["usage"], call["model"]) for call in known)),
                "liability_usd": _money(liability), "remaining_usd": _money(self.ceiling - liability)}

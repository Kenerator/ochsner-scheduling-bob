"""Private indexed runtime accounting at the existing canonical ledger path.

The owner holds its stable flock throughout. JSON migration must be activated only
after old application processes are quiescent: old code cannot read SQLite. No
prompt, key or provider request ID enters this database. DELETE journals and memory
temporary storage avoid WAL/SHM companions; unexpected companions fail closed.
"""
from contextlib import contextmanager
import json
import os
import sqlite3
import tempfile

from .journal import EffectJournal
from .model_budget import BudgetError, _maximum, _usage, _cost, _money, _pairs, _constant


_SCHEMA = (
    "CREATE TABLE metadata (key TEXT PRIMARY KEY, value INTEGER NOT NULL)",
    "CREATE TABLE calls (id INTEGER PRIMARY KEY, model TEXT NOT NULL, max_output_tokens INTEGER NOT NULL, "
    "reserved_nanos INTEGER NOT NULL, status TEXT NOT NULL, usage TEXT)",
)


class RuntimeLedger:
    def __init__(self, owner):
        self.owner = owner
        self.path = owner.path
        self.legacy = None
        self._validated = None

    def _fingerprint(self):
        info = self.path.stat()
        return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns

    @staticmethod
    def is_database(path):
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            return False
        try:
            EffectJournal._private_file(fd)
            return os.read(fd, 16) == b"SQLite format 3\x00"
        finally:
            os.close(fd)

    def _files(self, path=None, *, writing=False):
        path = self.path if path is None else path
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            EffectJournal._private_file(fd)
            identity = os.fstat(fd)
        finally:
            os.close(fd)
        for suffix in ("-journal", "-wal", "-shm"):
            companion = path.with_name(path.name + suffix)
            if companion.exists() or companion.is_symlink():
                if not writing or suffix != "-journal":
                    raise ValueError("unexpected accounting companion")
                fd = os.open(companion, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                try:
                    EffectJournal._private_file(fd)
                finally:
                    os.close(fd)
        return identity.st_dev, identity.st_ino

    @contextmanager
    def _connection(self, *, write=False, path=None):
        path = self.path if path is None else path
        identity = self._files(path)
        # URI mode prevents accidental initialization of a missing database.
        connection = sqlite3.connect(path.as_uri() + ("?mode=rw" if write else "?mode=ro"), uri=True)
        try:
            connection.execute("PRAGMA trusted_schema=OFF")
            connection.execute("PRAGMA temp_store=MEMORY")
            if write:
                connection.execute("PRAGMA journal_mode=DELETE")
                connection.execute("PRAGMA synchronous=FULL")
                connection.execute("BEGIN IMMEDIATE")
            else:
                connection.execute("PRAGMA query_only=ON")
            if self._files(path, writing=write) != identity:
                raise ValueError("accounting identity changed")
            if path == self.path:
                # Own committed writes are validated by construction. Any other
                # change (including another process) revalidates all history in
                # bounded memory before granting a new reservation.
                self._validate_connection(connection, rows=self._validated != self._fingerprint())
            yield connection
            if write:
                self._files(path, writing=True)
                connection.commit()
                EffectJournal._sync_directory(path.parent)
            if path == self.path:
                self._validated = self._fingerprint()
        finally:
            connection.close()

    def initialize(self, marker):
        if self.is_database(self.path):
            self.validate()
            return
        if self.path.exists() or self.path.is_symlink():
            self._files()  # Reject companions before touching legacy bytes.
        document = self.owner._read()
        if self.owner._existing_only:
            # Readiness validates the existing JSON, never migrates or writes it.
            self.legacy = document
            return
        document = self.owner._empty() if document is None else document
        fd, name = tempfile.mkstemp(prefix=".model-accounting-", dir=self.path.parent)
        os.fchmod(fd, 0o600)
        os.close(fd)
        temporary = self.path.with_name(os.path.basename(name))
        try:
            with self._connection(write=True, path=temporary) as connection:
                for sql in _SCHEMA:
                    connection.execute(sql)
                connection.executemany("INSERT INTO metadata VALUES (?, ?)",
                    (("version", 1), ("max_calls", document["max_calls"]),
                     ("ceiling_nanos", document["ceiling_nanos"])))
                for index, call in enumerate(document["calls"], 1):
                    self._insert(connection, call, index)
            if not self.owner._seen:
                os.lseek(marker, 0, os.SEEK_SET)
                os.write(marker, b"1"); os.fsync(marker)
                EffectJournal._sync_directory(self.path.parent)
                self.owner._seen = True
            os.replace(temporary, self.path)
            EffectJournal._sync_directory(self.path.parent)
        finally:
            # This exact owned migration temporary is never an accounting source.
            if temporary.exists():
                temporary.unlink()
        self.validate()

    @staticmethod
    def _insert(connection, call, identifier=None):
        connection.execute("INSERT INTO calls VALUES (?, ?, ?, ?, ?, ?)",
            (identifier, call["model"], call["max_output_tokens"], call["reserved_nanos"],
             call["status"], json.dumps(call["usage"]) if call["usage"] is not None else None))

    @staticmethod
    def _call(row):
        identifier, model, output, maximum, status, raw = row
        if (type(identifier) is not int or identifier < 1 or maximum != _maximum(model, output)
                or status not in {"reserved", "unknown", "known"}):
            raise ValueError("invalid accounting row")
        usage = None if raw is None else json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
        if status == "known":
            if _usage(usage, output, model) is None:
                raise ValueError("invalid accounting usage")
        elif usage is not None:
            raise ValueError("unexpected accounting usage")
        return {"model": model, "max_output_tokens": output, "reserved_nanos": maximum,
                "status": status, "usage": usage}

    def validate(self):
        if self.legacy is not None:
            # Refresh under the lock instead of trusting a previous readiness read.
            self.legacy = self.owner._read()
            return
        with self._connection() as connection:
            self._validate_connection(connection, rows=True)

    def _validate_connection(self, connection, *, rows):
        schema = connection.execute("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
        if sorted(schema) != sorted(("table", name, sql) for name, sql in zip(("metadata", "calls"), _SCHEMA)):
            raise ValueError("invalid accounting schema")
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        if metadata != {"version": 1, "max_calls": self.owner.max_calls, "ceiling_nanos": self.owner.ceiling}:
            raise ValueError("accounting configuration changed")
        if rows:
            if connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                raise ValueError("corrupt accounting storage")
            for index, row in enumerate(connection.execute("SELECT * FROM calls ORDER BY id"), 1):
                if row[0] != index:
                    raise ValueError("missing accounting history")
                self._call(row)

    def _summary(self, connection=None):
        rows = self.legacy["calls"] if self.legacy is not None else (
            self._call(row) for row in connection.execute("SELECT * FROM calls ORDER BY id"))
        totals = {key: 0 for key in ("calls", "known_calls", "input_tokens", "output_tokens",
                  "cached_input_tokens", "reasoning_output_tokens", "known_cost", "liability")}
        for call in rows:
            totals["calls"] += 1
            if call["status"] == "known":
                totals["known_calls"] += 1
                cost = _cost(call["usage"], call["model"])
                totals["known_cost"] += cost
                totals["liability"] += cost
                for key, value in call["usage"].items():
                    totals[key] += value
            else:
                totals["liability"] += call["reserved_nanos"]
        return totals

    def reserve(self, model, output, maximum):
        if self.owner._existing_only and not self.owner._existing_writes:
            raise BudgetError("Read-only accounting cannot reserve.")
        with self._connection(write=True) as connection:
            if not self.owner.application_runtime:
                totals = self._summary(connection)
                if totals["calls"] >= self.owner.max_calls or totals["liability"] + maximum > self.owner.ceiling:
                    raise BudgetError("Call count or dollar ceiling reached; dispatch blocked.")
            self._insert(connection, {"model": model, "max_output_tokens": output,
                "reserved_nanos": maximum, "status": "reserved", "usage": None})
            identifier = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        return identifier

    def settle(self, reservation, usage):
        if (self.owner._existing_only and not self.owner._existing_writes) or type(reservation) is not int or reservation < 1:
            raise BudgetError("Invalid accounting reservation.")
        with self._connection(write=True) as connection:
            row = connection.execute("SELECT * FROM calls WHERE id=?", (reservation,)).fetchone()
            if row is None:
                raise BudgetError("Invalid accounting reservation.")
            call = self._call(row)
            if call["status"] != "reserved":
                raise BudgetError("Accounting reservation was already settled; no refund.")
            cleaned = _usage(usage, call["max_output_tokens"], call["model"])
            status = "known" if cleaned is not None else "unknown"
            connection.execute("UPDATE calls SET status=?, usage=? WHERE id=?", (
                status, json.dumps(cleaned) if cleaned is not None else None, reservation))
        return {"status": status, "cost_usd": _money(_cost(cleaned, call["model"])) if cleaned is not None else None,
                "reserved_usd": _money(call["reserved_nanos"])}

    def snapshot(self):
        if self.legacy is not None:
            totals = self._summary()
        else:
            with self._connection() as connection:
                totals = self._summary(connection)
        runtime = self.owner.application_runtime
        return {key: value for key, value in {
            **totals, "unknown_calls": totals["calls"] - totals["known_calls"],
            "max_calls": self.owner.max_calls, "ceiling_usd": _money(self.owner.ceiling),
            "policy": "application_runtime_unlimited" if runtime else "bounded_nonapplication",
            "known_cost_usd": _money(totals["known_cost"]), "liability_usd": _money(totals["liability"]),
            "remaining_usd": None if runtime else _money(self.owner.ceiling - totals["liability"])
        }.items() if key not in {"known_cost", "liability"}}

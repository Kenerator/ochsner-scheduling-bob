"""Own one subprocess running the byte-preserved vendored synthetic service.

with OwnedMock(port=0) as mock: use mock.base_url. close() terminates only its
Popen child. A private readiness pipe reports the OS-selected numeric port;
stdout/stderr are DEVNULL, so original request logging never escapes the child.
"""

import argparse
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
from time import monotonic


_ROOT = Path(__file__).resolve().parents[1]
_SERVER = _ROOT / "vendor/reference/mock-api/server.py"
# The model-hosting parent legitimately holds credentials. Its synthetic child
# needs only OS/locale/temp settings, never model flags, vault tokens or imports.
_CHILD_ENV_NAMES = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "TMPDIR", "SYSTEMROOT")
_RUNNER = """
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location('bob_owned_vendor_server', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.Handler.store = module.Store()
server = module.ThreadingHTTPServer(('127.0.0.1', int(sys.argv[3])), module.Handler)
os.write(int(sys.argv[2]), (str(server.server_port) + '\\n').encode('ascii'))
os.close(int(sys.argv[2]))
try:
    server.serve_forever()
finally:
    server.server_close()
"""


class OwnedMock:
    def __init__(self, port=0, *, startup_timeout=5):
        if type(port) is not int or not 0 <= port <= 65535:
            raise ValueError("Expected a numeric loopback port in [0, 65535]")
        if type(startup_timeout) not in (int, float) or not 0 < startup_timeout <= 30:
            raise ValueError("Expected a bounded positive startup timeout")
        self.port = port
        self.startup_timeout = startup_timeout
        self.process = None
        self.base_url = None

    def __enter__(self):
        if self.process is not None:
            raise RuntimeError("Owned mock contexts cannot be reused")
        if not _SERVER.is_file():
            raise RuntimeError("Vendored synthetic service is missing")
        read_fd, write_fd = os.pipe()
        deadline = monotonic() + self.startup_timeout
        failed = False
        try:
            try:
                self.process = subprocess.Popen(
                    [sys.executable, "-c", _RUNNER, str(_SERVER), str(write_fd), str(self.port)],
                    cwd=_ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    pass_fds=(write_fd,), env={
                        **{name: os.environ[name] for name in _CHILD_ENV_NAMES if name in os.environ},
                        "PYTHONDONTWRITEBYTECODE": "1"},
                )
            finally:
                os.close(write_fd)
            remaining = deadline - monotonic()
            if remaining <= 0 or not select.select([read_fd], [], [], remaining)[0]:
                failed = True
            else:
                ready = os.read(read_fd, 64)
                if not ready.endswith(b"\n") or not ready.strip().isdigit():
                    failed = True
                else:
                    port = int(ready.strip())
                    if not 1 <= port <= 65535 or self.process.poll() is not None:
                        failed = True
                    else:
                        self.base_url = f"http://127.0.0.1:{port}"
        except (OSError, ValueError):
            failed = True
        except BaseException as error:
            # __enter__ has not returned: __exit__ cannot own this cleanup.
            # Preserve cancellation/unexpected failure, never target other PIDs.
            try:
                self.close()
            except Exception:
                error.add_note("Owned synthetic child cleanup could not be verified.")
            raise
        finally:
            os.close(read_fd)
        if failed:
            self.close()
            raise RuntimeError("Owned synthetic service did not start within its bound")
        return self

    def close(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)

    def __exit__(self, *_exc):
        self.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Owned loopback synthetic scheduling service; Ctrl-C stops only this child")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args(argv)
    def stop(_signal, _frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, stop)
    try:
        with OwnedMock(args.port) as mock:
            print(f"Owned synthetic mock: {mock.base_url} (Ctrl-C to stop)", flush=True)
            mock.process.wait()
    except KeyboardInterrupt:
        return 0
    except (ValueError, RuntimeError):
        print("Owned synthetic mock could not start. Check the port and vendored files.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

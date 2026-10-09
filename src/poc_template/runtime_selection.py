"""Select a real local assistant and observe only its bounded version command."""
import os
from pathlib import Path
import shutil


def resolve_assistant(integration: str, executable: str | None = None) -> dict:
    if integration not in {"codex", "claude"}:
        raise ValueError("Choose codex or claude")
    key = f"SPECKIT_INTEGRATION_{integration.upper()}_EXECUTABLE"
    ambient = os.environ.get(key)
    selected = executable or ambient or integration
    found = shutil.which(selected)
    if not found:
        raise ValueError(f"{integration} executable missing or not executable")
    path = Path(found).resolve(strict=True)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError("Assistant must be an executable regular file")
    if executable and ambient:
        other = shutil.which(ambient)
        if other is None or Path(other).resolve() != path:
            raise ValueError(f"Conflicting {key}; value withheld")
    from .speckit_adapter import run_process
    try:
        result = run_process([str(path), "--version"], Path.cwd(), timeout=10)
    except OSError as error:
        raise ValueError("Assistant version probe could not complete") from error
    version = result["stdout"].strip()
    if result["returncode"] or result["timed_out"] or not version or len(version.encode()) > 4096:
        raise ValueError("Assistant version probe failed or exceeded its output bound")
    return dict(integration=integration, executable=str(path), version=version)


def verify_assistant_binding(binding: dict) -> None:
    if not isinstance(binding, dict) or set(binding) != {"integration", "executable", "version"}:
        raise ValueError("Invalid assistant binding")
    if not Path(binding["executable"]).is_absolute():
        raise ValueError("Assistant binding must use an absolute executable")
    current = resolve_assistant(binding["integration"], binding["executable"])
    if current != binding:
        raise ValueError("Bound assistant executable/version changed; select a reviewed new run")

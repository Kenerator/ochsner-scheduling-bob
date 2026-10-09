"""Bounded launch configuration, never instructions, credentials or authority."""
import hashlib
from pathlib import Path
import re

from .bootstrap import normalize_execution, stage_names
from .stage_guidance import strict_json

FIELDS = {"schema_version", "template_root", "destination", "name", "inputs", "rfp",
          "personas", "persona_catalog", "through", "integration", "execution",
          "capabilities", "ports", "qualification", "delivery"}
PATHS = {"template_root", "destination", "rfp", "persona_catalog"}


def _strings(value, name):
    if (not isinstance(value, list) or len(value) > 100 or
            any(not isinstance(item, str) or not item or len(item) > 4096 or "\0" in item for item in value)):
        raise ValueError(f"{name} requires a bounded ordered list of strings")
    return value


def _declaration(value, name, fields):
    if not isinstance(value, dict) or set(value) - set(fields):
        raise ValueError(f"Invalid {name} declaration fields; no credentials or authority")
    for key, item in value.items():
        kind = fields[key]
        if kind is list:
            _strings(item, name + "." + key)
        elif type(item) is not kind or (kind is str and (not item or len(item) > 4096 or "\0" in item)):
            raise ValueError(f"Invalid {name}.{key}")
    return value


def load_launch_spec(path: Path) -> dict:
    path = Path(path).absolute()
    if path.is_symlink() or not path.is_file():
        raise ValueError("Launch manifest must be a regular JSON file, not a symlink")
    with path.open("rb") as stream:
        data = stream.read(1048577)
    if len(data) > 1048576:
        raise ValueError("Launch manifest exceeds 1 MiB")
    try:
        value = strict_json(data.decode("utf-8"))
    except (ValueError, UnicodeError) as error:
        raise ValueError("Launch manifest must be strict UTF-8 JSON") from error
    if (not isinstance(value, dict) or set(value) - FIELDS or
            type(value.get("schema_version")) is not int or value["schema_version"] != 1):
        raise ValueError("Launch manifest requires schema_version 1 and only declared fields")
    result = {key: item for key, item in value.items() if key != "schema_version"}
    for key in PATHS & result.keys():
        item = result[key]
        if not isinstance(item, str) or not item or "\0" in item or len(item) > 4096:
            raise ValueError(f"Invalid launch path: {key}")
        candidate = Path(item)
        result[key] = (candidate if candidate.is_absolute() else path.parent / candidate).absolute()
    if "inputs" in result:
        result["inputs"] = [Path("-") if item == "-" else
                            (Path(item) if Path(item).is_absolute() else path.parent / item).absolute()
                            for item in _strings(result["inputs"], "inputs")]
    for key in ("personas", "capabilities"):
        if key in result:
            _strings(result[key], key)
    if "through" in result:
        stage_names(result["through"])
    integration = result.get("integration", "codex")
    if not isinstance(integration, str) or integration not in {"codex", "claude"}:
        raise ValueError("Choose codex or claude")
    if "name" in result and (not isinstance(result["name"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", result["name"])):
        raise ValueError("Launch name requires a lowercase technical slug")
    if "execution" in result:
        if not isinstance(result["execution"], dict):
            raise ValueError("Execution must be a declared object")
        result["execution"] = dict(result["execution"])
        if result["execution"].get("assistant_executable"):
            if not isinstance(result["execution"]["assistant_executable"], str):
                raise ValueError("Assistant executable must be a path string")
            item = Path(result["execution"]["assistant_executable"])
            result["execution"]["assistant_executable"] = str((item if item.is_absolute() else path.parent / item).absolute())
        normalize_execution(integration, result["execution"])
    if "ports" in result:
        ports = result["ports"]
        if (not isinstance(ports, dict) or len(ports) > 16 or
                any(not isinstance(key, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,39}", key) or
                    type(port) is not int or not 1024 <= port <= 65535 for key, port in ports.items()) or
                len(set(ports.values())) != len(ports)):
            raise ValueError("Ports require unique named integer ports from 1024 through 65535")
    if "qualification" in result:
        _declaration(result["qualification"], "qualification", {"profile": str, "required_kinds": list})
    if "delivery" in result:
        _declaration(result["delivery"], "delivery", {"owner": str, "repository": str, "private": bool, "ssh_alias": str})
    result["manifest_sha256"] = hashlib.sha256(data).hexdigest()
    return result


def merge_launch_options(manifest: dict, explicit: dict) -> dict:
    """Merge omitted choices, never override an explicitly different value."""
    merged = dict(manifest)
    for key, value in explicit.items():
        if key == "execution" and key in merged:
            merged[key] = merge_launch_options(merged[key], value)
            continue
        previous = merged.get(key)
        compare_value = value
        if key == "inputs":
            previous = [Path("-") if Path(item) == Path("-") else Path(item).resolve() for item in previous] if previous is not None else None
            compare_value = [Path("-") if Path(item) == Path("-") else Path(item).resolve() for item in value]
        if key in merged:
            if key in PATHS or key == "assistant_executable":
                previous, compare_value = Path(previous).resolve(), Path(value).resolve()
            if type(previous) is not type(compare_value) or previous != compare_value:
                raise ValueError(f"Conflicting manifest/CLI option: {key}")
            # Equality does not erase the manifest's original path: existing
            # safety validation must still reject its links/unsafe destination.
            continue
        merged[key] = value
    return merged

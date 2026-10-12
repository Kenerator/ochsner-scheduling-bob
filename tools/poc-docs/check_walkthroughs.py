"""Bounded, read-only training-document checks; never executes app or network I/O."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from urllib.parse import unquote, urlsplit

LIMIT = 1_048_576
IDENTIFIER = re.compile(r"[a-z][a-z0-9-]{0,95}\Z")
GROUPS = {"session-and-public", "private-and-booking", "help-and-outcomes", "support",
          "developer-recording", "replay-navigation", "replay-variants-and-data"}
LINK = re.compile(r"(!?)\[([^\]\n]*)\]\(<?([^\s)>]+)>?(?:\s+[\"'][^\n]*?[\"'])?\)")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _json(path):
    return json.loads(_read(path), object_pairs_hook=_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def _read(path):
    if path.stat().st_size > LIMIT:
        raise ValueError("file exceeds bound")
    return path.read_text(encoding="utf-8")


def _path(root, value):
    # Catalog paths are root-relative regular files; symlinked ancestors are unsafe.
    if not isinstance(value, str) or not value or len(value) > 512 or "\\" in value or "\x00" in value:
        raise ValueError("unsafe path")
    parsed = urlsplit(value)
    parts = PurePosixPath(value).parts
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or value.startswith("/") or ".." in parts:
        raise ValueError("unsafe path")
    candidate = root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("symlink")
    if not stat.S_ISREG(candidate.stat().st_mode):
        raise ValueError("not regular")
    candidate.resolve().relative_to(root)
    return candidate


def _slug(heading):
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def _sections(markdown):
    sections, counts, current, fenced = {}, {}, None, False
    for line in markdown.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        if not fenced and (match := re.match(r"^#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)):
            anchor = _slug(match[1])
            number = counts.get(anchor, 0)
            counts[anchor] = number + 1
            current = anchor + (f"-{number}" if number else "")
            sections[current] = []
        elif current:
            sections[current].append(line)
    return {key: "\n".join(value) for key, value in sections.items()}


def _reference(root, reference, base=None):
    if not isinstance(reference, str) or len(reference) > 1024:
        raise ValueError("invalid reference")
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or parsed.query:
        raise ValueError("nonlocal reference")
    raw = unquote(parsed.path)
    # Markdown may navigate parent directories, but never outside the project.
    candidate = ((base.parent / raw) if base else (root / raw)) if raw else base
    if candidate is None:
        raise ValueError("missing reference")
    relative = Path(os.path.normpath(candidate)).relative_to(root).as_posix()
    path = _path(root, relative)
    if parsed.fragment and unquote(parsed.fragment) not in _sections(_read(path)):
        raise ValueError("missing anchor")
    return path


def _strings(value, nonempty=False):
    return (isinstance(value, list) and len(value) <= 512 and (bool(value) or not nonempty)
            and all(isinstance(item, str) and 0 < len(item) <= 1024 for item in value))


def _schema(catalog):
    if not isinstance(catalog, dict) or set(catalog) != {"schema_version", "flows", "controls"} or type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1:
        return False
    for family in ("flows", "controls"):
        rows = catalog[family]
        if not isinstance(rows, list) or len(rows) > 512:
            return False
        identifiers = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not IDENTIFIER.fullmatch(row["id"]) or row["id"] in identifiers:
                return False
            identifiers.add(row["id"])
            if not isinstance(row.get("document"), str):
                return False
            if family == "controls":
                if set(row) != {"id", "label", "role", "group", "document", "visual_ids"} or not isinstance(row["label"], str) or not 1 <= len(row["label"]) <= 256 or row["role"] not in ("patient", "support", "both", "developer") or not isinstance(row["group"], str) or row["group"] not in GROUPS or not _strings(row["visual_ids"]):
                    return False
                continue
            if set(row) != {"id", "source_ids", "document", "status", "mode", "steps", "gap_refs", "evidence_refs"} or row["status"] not in ("implemented", "partial", "unsupported", "unverified") or row["mode"] not in ("model", "offline", "recorded-simulation", "not-executable"):
                return False
            if not all(_strings(row[key], key == "source_ids") for key in ("source_ids", "gap_refs", "evidence_refs")) or not isinstance(row["steps"], list) or len(row["steps"]) > 128:
                return False
            for step in row["steps"]:
                if not isinstance(step, dict) or not {"number", "anchor", "interactive"} <= set(step) or set(step) - {"number", "anchor", "interactive", "visual_ids", "control_ids"} or type(step["number"]) is not int or type(step["interactive"]) is not bool or not isinstance(step["anchor"], str) or not re.fullmatch(r"[\w-]{1,160}", step["anchor"]):
                    return False
                if any(not _strings(step[key]) for key in ("visual_ids", "control_ids") if key in step):
                    return False
    return True


def _sources(root):
    known = set()
    # Conventional native sources, not app imports or project-specific IDs.
    paths = list((root / "specs").glob("*/spec.md"))[:512]
    for path in paths:
        text = _read(_path(root, path.relative_to(root).as_posix()))
        known.update("US" + number for number in re.findall(r"User Story (\d+)", text))
        known.update(re.findall(r"\b(?:US\d+|FR-[A-Za-z0-9-]+)\b", text))
    source = root / "tests/fixtures/supplied_scenarios.json"
    if source.exists():
        data = _json(_path(root, source.relative_to(root).as_posix()))
        if not isinstance(data, dict) or not _strings(data.get("scenario_ids")):
            raise ValueError("invalid source inventory")
        known.update(data["scenario_ids"])
    return known


def check_catalog(root: Path, catalog: dict) -> list[str]:
    """Return bounded credential-free structural errors; never certify execution."""
    errors = []
    if not _schema(catalog):
        return ["catalog: invalid schema or duplicate identifier"]
    try:
        root = Path(root).resolve(strict=True)
        known = _sources(root)
        manifest = _json(_path(root, "assets/ui/walkthroughs/manifest.json"))
        if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "visuals"} or type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1 or not isinstance(manifest["visuals"], list) or len(manifest["visuals"]) > 512:
            raise ValueError("manifest schema")
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        return ["catalog: source inventory or visual manifest unavailable or invalid"]
    visuals = {}
    for visual in manifest["visuals"]:
        allowed = {"id", "kind", "path", "sha256", "source_revision", "working_tree_state", "scenario", "action", "result", "role", "viewport", "width", "height", "source_visual_id", "placements", "limitations"}
        if not isinstance(visual, dict) or set(visual) - allowed or not isinstance(visual.get("id"), str) or not IDENTIFIER.fullmatch(visual["id"]) or visual["id"] in visuals or visual.get("kind") not in ("screenshot", "schematic", "annotation", "composite") or not isinstance(visual.get("path"), str):
            return ["catalog: visual manifest schema or identifier invalid"]
        visuals[visual["id"]] = visual
        try:
            asset = _path(root, visual["path"])
            if visual["kind"] == "screenshot" and asset.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                errors.append(f"{visual['id']}: screenshot must be a raster capture")
        except (OSError, ValueError):
            errors.append(f"{visual['id']}: visual asset unavailable")

    controls = {row["id"]: row for row in catalog["controls"]}
    assigned = set()
    for row in catalog["flows"] + catalog["controls"]:
        identifier, flow = row["id"], "steps" in row
        if flow:
            if row["document"] in assigned:
                errors.append(f"{identifier}: document already assigned to another flow")
            assigned.add(row["document"])
            numbers = [step["number"] for step in row["steps"]]
            if numbers[:2] != [0, 1] or numbers != list(range(len(numbers))):
                errors.append(f"{identifier}: steps must start at 0 and be consecutive")
            if row["status"] != "implemented" and not row["gap_refs"]:
                errors.append(f"{identifier}: gap status requires a gap reference")
            for source in row["source_ids"]:
                if source not in known:
                    try:
                        _reference(root, source)
                    except (OSError, ValueError, UnicodeError):
                        errors.append(f"{identifier}: unresolved source ID")
            for reference in row["gap_refs"] + row["evidence_refs"]:
                try:
                    _reference(root, reference)
                except (OSError, ValueError, UnicodeError):
                    errors.append(f"{identifier}: reference unavailable or anchor missing")
        try:
            document = _path(root, row["document"])
            markdown = _read(document)
        except (OSError, ValueError, UnicodeError):
            errors.append(f"{identifier}: document unavailable or unsafe")
            continue
        for match in LINK.finditer(markdown):
            if match[1] and not match[2].strip():
                errors.append(f"{identifier}: image requires alt text")
            if urlsplit(match[3]).scheme in {"http", "https", "mailto"} and not match[1]:
                continue  # External links are never fetched or called verified.
            try:
                _reference(root, match[3], document)
            except (OSError, ValueError, UnicodeError):
                errors.append(f"{identifier}: Markdown target unavailable or anchor missing")
        sections = _sections(markdown)
        for step in row["steps"] if flow else [{"visual_ids": row["visual_ids"], "interactive": True}]:
            prefix = f"{identifier}: step {step['number']}" if flow else identifier
            section = sections.get(step.get("anchor"), "") if flow else markdown
            if flow and step["anchor"] not in sections:
                errors.append(f"{prefix} anchor unavailable")
            if step["interactive"] and not step.get("visual_ids"):
                errors.append(f"{prefix} requires a visual")
            for control in step.get("control_ids", []):
                if control not in controls:
                    errors.append(f"{prefix} has unresolved control")
            image_targets = set()
            for match in LINK.finditer(section):
                if match[1]:
                    try:
                        image_targets.add(_reference(root, match[3], document))
                    except (OSError, ValueError, UnicodeError):
                        pass
            for visual_id in step.get("visual_ids", []):
                visual = visuals.get(visual_id)
                if visual is None:
                    errors.append(f"{prefix} has unresolved visual")
                    continue
                try:
                    if _path(root, visual["path"]) not in image_targets:
                        errors.append(f"{prefix} visual not embedded at point of use")
                except (OSError, ValueError):
                    pass  # Manifest validation already explains the missing asset.
                if visual["kind"] == "schematic" and "schematic" not in section.lower():
                    errors.append(f"{prefix} schematic must be labeled")
    return list(dict.fromkeys(errors))[:256]


def main(argv: list[str] | None = None) -> int:
    """Read --root/--catalog; return 0 for structural success, 2 for errors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--catalog", required=True)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        catalog = _json(_path(root, args.catalog))
        errors = check_catalog(root, catalog)
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        errors = ["catalog: malformed, duplicate-field or unavailable JSON"]
    for error in errors:
        print(error)
    if not errors:
        print("structural check passed")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

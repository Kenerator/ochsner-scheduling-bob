"""Bounded, read-only training-document checks; never executes app or network I/O."""
import argparse
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import struct
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

LIMIT = 1_048_576
IDENTIFIER = re.compile(r"[a-z][a-z0-9-]{0,95}\Z")
# Project actor/group vocabularies belong to consumer catalogs, not this export.
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
SVG_ELEMENTS = {"svg", "g", "title", "desc", "rect", "circle", "ellipse", "line",
                "polyline", "polygon", "path", "text", "tspan", "image"}
SVG_ATTRIBUTES = {"width", "height", "viewBox", "preserveAspectRatio", "x", "y",
                  "x1", "x2", "y1", "y2", "rx", "ry", "cx", "cy", "r", "d",
                  "points", "transform", "fill", "fill-opacity", "fill-rule",
                  "stroke", "stroke-width", "stroke-opacity", "stroke-linecap",
                  "stroke-linejoin", "stroke-miterlimit", "stroke-dasharray",
                  "stroke-dashoffset", "opacity", "font-family", "font-size",
                  "font-weight", "text-anchor", "dominant-baseline", "dx", "dy",
                  "id", "role", "aria-label", "aria-labelledby", "aria-describedby",
                  "aria-hidden", "href"}
LINK = re.compile(r"(!?)\[([^\]\n]*)\]\(<?([^\s)>]+)>?(?:\s+[\"'][^\n]*?[\"'])?\)")
VISUAL_FIELDS = {"id", "kind", "path", "sha256", "source_revision", "working_tree_state",
                 "scenario", "action", "result", "role", "viewport", "width", "height",
                 "source_visual_id", "placements", "limitations"}


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
    lowered = [part.lower() for part in parts]
    if (any(part in {".git", ".bob-local", ".superpowers", ".venv", "tmp", "__pycache__"}
            or part.startswith(".env") for part in lowered)
        or lowered[:3] in (["docs", "product", "intake"], ["docs", "product", "rfp"])
        and (lowered[:3] != ["docs", "product", "rfp"] or len(lowered) > 3 and lowered[3] == "source")):
        raise ValueError("private path")
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


def _identifier(value):
    return isinstance(value, str) and bool(IDENTIFIER.fullmatch(value))


def _schema(catalog):
    if not isinstance(catalog, dict) or set(catalog) != {"schema_version", "flows", "controls"} or type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1:
        return False
    for family in ("flows", "controls"):
        rows = catalog[family]
        if not isinstance(rows, list) or len(rows) > 512 or family == "flows" and not rows:
            return False
        identifiers = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not IDENTIFIER.fullmatch(row["id"]) or row["id"] in identifiers:
                return False
            identifiers.add(row["id"])
            if not isinstance(row.get("document"), str):
                return False
            if family == "controls":
                if set(row) != {"id", "label", "role", "group", "document", "visual_ids"} or not isinstance(row["label"], str) or not 1 <= len(row["label"]) <= 256 or not _identifier(row["role"]) or not _identifier(row["group"]) or not _strings(row["visual_ids"]):
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


def check_placement(source: dict, placement: dict) -> list[str]:
    """Validate source-pixel rectangles; this never certifies the visual target."""
    if (not isinstance(source, dict) or not isinstance(placement, dict)
        or set(placement) != {"x", "y", "width", "height"}
        or any(type(source.get(k)) is not int or source[k] <= 0 for k in ("width", "height"))
        or any(type(placement.get(k)) is not int for k in ("x", "y", "width", "height"))
        or placement["x"] < 0 or placement["y"] < 0
        or placement["width"] <= 0 or placement["height"] <= 0):
        return ["invalid annotation placement"]
    if (placement["x"] + placement["width"] > source["width"]
        or placement["y"] + placement["height"] > source["height"]):
        return ["annotation exceeds source bounds"]
    return []


def _revision(root):
    """Best-effort local Git metadata only: no Git process, hooks or network."""
    try:
        directory = root / ".git"
        if directory.is_symlink():
            return None
        if directory.is_file():
            pointer = _read(directory).strip()
            if not pointer.startswith("gitdir: "):
                return None
            directory = (root / pointer[8:]).resolve()
        head = _read(directory / "HEAD").strip()
        if re.fullmatch(r"[0-9a-f]{40}", head):
            return head
        if not re.fullmatch(r"ref: refs/heads/[A-Za-z0-9/_-]{1,200}", head):
            return None
        reference = head[5:]
        common = directory / "commondir"
        if common.is_file() and not common.is_symlink():
            directory = (directory / _read(common).strip()).resolve()
        direct = directory / reference
        if direct.is_file() and not direct.is_symlink():
            value = _read(direct).strip()
            return value if re.fullmatch(r"[0-9a-f]{40}", value) else None
        packed = directory / "packed-refs"
        if packed.is_file() and not packed.is_symlink():
            for line in _read(packed).splitlines():
                if line.endswith(" " + reference) and re.fullmatch(r"[0-9a-f]{40}", line[:40]):
                    return line[:40]
    except (OSError, ValueError, UnicodeError):
        pass
    return None


def _dimensions(path, raw, *, root=None, source_asset=None):
    """Bounded header/SVG validation, not a complete image codec or pixel audit."""
    suffix = path.suffix.lower()
    if suffix == ".png" and len(raw) >= 33 and raw[:8] == b"\x89PNG\r\n\x1a\n" and raw[8:16] == b"\x00\x00\x00\rIHDR":
        return struct.unpack(">II", raw[16:24])
    if suffix in (".jpg", ".jpeg") and raw.startswith(b"\xff\xd8"):
        offset = 2
        while offset + 4 <= len(raw):
            if raw[offset] != 255:
                break
            while offset < len(raw) and raw[offset] == 255:
                offset += 1
            if offset >= len(raw):
                break
            marker = raw[offset]
            offset += 1
            if marker in (0xD8, 0xD9, 0xDA):
                break
            if marker == 0x01 or 0xD0 <= marker <= 0xD7:
                continue
            size = int.from_bytes(raw[offset:offset + 2], "big")
            if size < 2 or offset + size > len(raw):
                break
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF) and size >= 8:
                height, width = struct.unpack(">HH", raw[offset + 3:offset + 7])
                return width, height
            offset += size
    if suffix == ".svg":
        if b"<!" in raw or b"<?" in raw:
            raise ValueError("unsafe SVG declaration")
        element = ET.fromstring(raw)
        if element.tag.rsplit("}", 1)[-1] != "svg":
            raise ValueError("not SVG")
        for node in element.iter():
            namespace, _, name = node.tag[1:].partition("}") if node.tag.startswith("{") else ("", "", node.tag)
            if namespace not in ("", SVG_NS) or name not in SVG_ELEMENTS:
                raise ValueError("SVG element is not inert")
            # A small inert subset is intentional: SMIL/foreign namespaces/CSS
            # must not mutate a source-bound teaching visual after validation.
            for key in node.attrib:
                attr_ns, _, attr_name = key[1:].partition("}") if key.startswith("{") else ("", "", key)
                if (attr_name not in SVG_ATTRIBUTES
                    or attr_ns not in ("", XLINK_NS)
                    or attr_ns == XLINK_NS and (name != "image" or attr_name != "href")):
                    raise ValueError("SVG attribute is not inert")
            hrefs = [value for key, value in node.attrib.items() if key.rsplit("}", 1)[-1] == "href"]
            if name == "image":
                # A code-native composite may reuse exactly its verified original.
                # Self-contained SVG-as-image needs exact raster embedding. Never
                # allow arbitrary data, external URLs or annotation chains.
                if root is None or source_asset is None or len(hrefs) != 1:
                    raise ValueError("undeclared composite source")
                if hrefs[0].startswith("data:"):
                    match = re.fullmatch(r"data:image/(png|jpeg);base64,([A-Za-z0-9+/=]+)", hrefs[0])
                    if match is None or source_asset.stat().st_size > 16 * LIMIT:
                        raise ValueError("invalid embedded source")
                    try:
                        embedded = base64.b64decode(match[2], validate=True)
                    except binascii.Error:
                        raise ValueError("invalid embedded source") from None
                    mime = "png" if source_asset.suffix.lower() == ".png" else "jpeg"
                    if match[1] != mime or embedded != source_asset.read_bytes():
                        raise ValueError("embedded source mismatch")
                elif _reference(root, hrefs[0], path) != source_asset:
                    raise ValueError("undeclared composite source")
            elif hrefs:
                raise ValueError("linked SVG")
            if any(key.rsplit("}", 1)[-1].lower().startswith("on")
                   or "url(" in value.lower() for key, value in node.attrib.items()):
                raise ValueError("active or linked SVG")
        dimensions = tuple(element.get(k, "").removesuffix("px") for k in ("width", "height"))
        if all(re.fullmatch(r"[1-9][0-9]{0,5}", v) for v in dimensions):
            return tuple(map(int, dimensions))
    raise ValueError("unsupported or invalid image header")


def _visual_schema(visual):
    if not isinstance(visual, dict) or set(visual) != VISUAL_FIELDS:
        return False
    text = ("id", "kind", "path", "sha256", "source_revision", "working_tree_state",
            "scenario", "action", "result", "role")
    if any(not isinstance(visual[k], str) or not visual[k].strip() or len(visual[k]) > 1024
           or any(ord(c) < 32 for c in visual[k]) for k in text):
        return False
    return (bool(IDENTIFIER.fullmatch(visual["id"]))
            and visual["kind"] in ("screenshot", "schematic", "annotation", "composite")
            and bool(re.fullmatch(r"[0-9a-f]{64}", visual["sha256"]))
            and bool(re.fullmatch(r"[0-9a-f]{40}", visual["source_revision"]))
            and visual["working_tree_state"] in ("clean", "dirty", "unknown")
            and _identifier(visual["role"])
            and all(type(visual[k]) is int and 0 < visual[k] <= 32768 for k in ("width", "height"))
            and isinstance(visual["viewport"], dict) and set(visual["viewport"]) == {"width", "height"}
            and all(type(visual["viewport"][k]) is int and 0 < visual["viewport"][k] <= 32768 for k in ("width", "height"))
            and (visual["source_visual_id"] is None or isinstance(visual["source_visual_id"], str)
                 and bool(IDENTIFIER.fullmatch(visual["source_visual_id"])))
            and isinstance(visual["placements"], list) and len(visual["placements"]) <= 128
            and _strings(visual["limitations"]))


def _visuals(root, manifest):
    visuals, errors = {}, []
    revision = _revision(root)
    for visual in manifest["visuals"]:
        if not _visual_schema(visual) or visual["id"] in visuals:
            return {}, ["catalog: visual manifest schema or identifier invalid"]
        identifier = visual["id"]
        visuals[identifier] = visual
    for identifier, visual in visuals.items():
        try:
            asset = _path(root, visual["path"])
            if visual["kind"] == "screenshot" and asset.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                errors.append(f"{identifier}: screenshot must be a raster capture")
            if asset.stat().st_size > 16 * LIMIT:
                raise ValueError("image exceeds bound")
            raw = asset.read_bytes()
            if hashlib.sha256(raw).hexdigest() != visual["sha256"]:
                errors.append(f"{identifier}: visual hash mismatch")
            source = visuals.get(visual["source_visual_id"])
            source_asset = (_path(root, source["path"]) if visual["kind"] == "composite"
                            and source is not None and source["kind"] == "screenshot" else None)
            if _dimensions(asset, raw, root=root, source_asset=source_asset) != (visual["width"], visual["height"]):
                errors.append(f"{identifier}: visual dimensions mismatch")
        except OSError:
            errors.append(f"{identifier}: visual asset unavailable")
        except (ValueError, ET.ParseError):
            errors.append(f"{identifier}: visual asset unavailable or invalid")
        if revision and visual["source_revision"] != revision:
            if not any("historical" in value.lower() for value in visual["limitations"]):
                errors.append(f"{identifier}: historical source requires an explicit limitation")
        elif revision is None or visual["working_tree_state"] != "clean":
            if not visual["limitations"]:
                errors.append(f"{identifier}: unknown or dirty source requires a limitation")
    for identifier, visual in visuals.items():
        if visual["kind"] in ("screenshot", "schematic"):
            if visual["source_visual_id"] is not None or visual["placements"]:
                errors.append(f"{identifier}: clean visual cannot name an annotation source")
            continue
        source = visuals.get(visual["source_visual_id"])
        if source is None or source["kind"] != "screenshot":
            errors.append(f"{identifier}: annotation requires a clean screenshot source")
            continue
        if any(visual[k] != source[k] for k in ("width", "height", "viewport", "source_revision", "working_tree_state", "scenario", "role")):
            errors.append(f"{identifier}: annotation/source provenance or dimensions mismatch")
        if not visual["placements"]:
            errors.append(f"{identifier}: annotation requires placement rectangles")
        for placement in visual["placements"]:
            errors.extend(f"{identifier}: {error}" for error in check_placement(source, placement))
    return visuals, errors[:256]


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
    visuals, visual_errors = _visuals(root, manifest)
    errors.extend(visual_errors)

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
            if row["mode"] != "not-executable" and not any(step["interactive"] for step in row["steps"]):
                errors.append(f"{identifier}: executable flow requires an interactive step")
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
        if flow:
            # Visible instruction structure only: no claim about prose accuracy,
            # sample suitability, workflow execution or perceptual completeness.
            required = {"arrange-the-workspace", "synthetic-sample-data",
                        "completion-and-cleanup", "known-gaps-and-evidence", "references"}
            if not required <= set(sections):
                errors.append(f"{identifier}: required walkthrough section unavailable")
            if "synthetic-sample-data" in sections and not re.search(r"(?m)^[1-9][0-9]*\.\s+\S", sections["synthetic-sample-data"]):
                errors.append(f"{identifier}: synthetic sample data must be enumerated")
            completion = sections.get("completion-and-cleanup")
            if completion is not None and any(marker not in completion.lower() for marker in ("effect:", "cleanup:")):
                errors.append(f"{identifier}: completion must declare effect and cleanup")
            gaps = sections.get("known-gaps-and-evidence")
            if gaps is not None and "recovery:" not in gaps.lower():
                errors.append(f"{identifier}: known gaps must declare recovery")
            order = list(sections)
            if "revision-history" in sections and "references" in sections and order.index("revision-history") > order.index("references"):
                errors.append(f"{identifier}: revision history must precede final references")
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
    class SafeParser(argparse.ArgumentParser):
        def error(self, message):
            raise ValueError("invalid checker arguments")
    parser = SafeParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--catalog", required=True)
    try:
        args = parser.parse_args(argv)
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

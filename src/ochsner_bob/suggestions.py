"""Bounded public vocabularies only; suggestions never select a preference.

Provider records must be the current returned public projection. Arbitrary
vocabularies and patient-record shapes are rejected before RapidFuzz runs.
"""

import re

try:
    from rapidfuzz import process
except ImportError:  # The project environment verifies RapidFuzz; this keeps imports readable offline.
    process = None


def suggest(query, field, limit=3, *, providers=()):
    from .session import SPECIALTIES, LOCATIONS

    if (type(query) is not str or not re.fullmatch(r"[A-Za-z][A-Za-z _.'-]{0,127}", query)
            or type(field) is not str or field not in {"specialty", "location", "provider"}
            or type(limit) is not int or not 1 <= limit <= 3):
        raise ValueError("Use a bounded public suggestion field and query.")
    if field == "provider":
        if type(providers) not in (tuple, list) or len(providers) > 2000:
            raise ValueError("Use only current returned public providers.")
        vocabulary = []
        identifiers = set()
        for provider in providers:
            if (type(provider) is not dict
                    or set(provider) != {"providerId", "name", "specialty", "locations", "modalities"}
                    or type(provider["providerId"]) is not str
                    or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", provider["providerId"])
                    or provider["providerId"] in identifiers
                    or type(provider["name"]) is not str or not 1 <= len(provider["name"]) <= 128
                    or any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in provider["name"])
                    or type(provider["specialty"]) is not str or provider["specialty"] not in SPECIALTIES
                    or type(provider["locations"]) is not list or len(provider["locations"]) > 3
                    or any(type(v) is not str or v not in LOCATIONS for v in provider["locations"])
                    or type(provider["modalities"]) is not list or len(provider["modalities"]) > 32
                    or any(type(v) is not str or not 1 <= len(v) <= 128 for v in provider["modalities"])):
                raise ValueError("Use only current returned public providers.")
            identifiers.add(provider["providerId"])
            vocabulary.append(provider["name"])
    else:
        if providers != ():
            raise ValueError("Provider records are only permitted for public provider suggestions.")
        vocabulary = SPECIALTIES if field == "specialty" else LOCATIONS
    if process is None:
        raise RuntimeError("RapidFuzz is required for public suggestions")
    matches = process.extract(query.casefold(), vocabulary, processor=str.casefold, limit=limit, score_cutoff=60)
    if field == "provider":
        return [{"field": "provider_id", "value": providers[index]["providerId"], "label": name}
                for name, _score, index in matches]
    return [{"field": field, "value": name} for name, _score, _index in matches]

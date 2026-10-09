"""Public vocabulary suggestions; patient data never enters this module."""

try:
    from rapidfuzz import process
except ImportError:  # The project environment verifies RapidFuzz; this keeps imports readable offline.
    process = None


def suggest(query, vocabulary, limit=3):
    if process is None:
        raise RuntimeError("RapidFuzz is required for public suggestions")
    return [item[0] for item in process.extract(query, vocabulary, limit=limit) if item[1] >= 60]

"""Bound instruction parsing to the named medication and its clause."""

import re
from typing import Iterable, Optional


def medication_context(
    text: str, medication: str, medications: Iterable[str] = (), start_char: Optional[int] = None
) -> str:
    """Keep the medication's clause, stopping before the next known medication.

    Sentence boundaries exclude decimal points and abbreviations. Conjunctions
    remain in scope unless followed by another extracted medication.
    """
    if not medication:
        return ""
    matches = list(re.finditer(r"(?<!\w)" + re.escape(medication) + r"(?!\w)", text, re.I))
    match = next((m for m in matches if m.start() == start_char), None)
    if match is None and len(matches) == 1:
        match = matches[0]
    if match is None:
        return ""
    boundaries = list(re.finditer(r"[;\n]|\.(?=\s+[A-Z])", text))
    start = max((m.end() for m in boundaries if m.end() <= match.start()), default=0)
    end = min((m.start() for m in boundaries if m.start() >= match.end()), default=len(text))
    for other in medications:
        if not other:
            continue
        for other_match in re.finditer(r"(?<!\w)" + re.escape(other) + r"(?!\w)", text, re.I):
            if other_match.start() == match.start():
                continue
            if other_match.end() <= match.start():
                # Never borrow the preceding medication's trailing instructions.
                start = max(start, match.start())
            elif other_match.start() >= match.end():
                end = min(end, other_match.start())
    # A leading conjunction generally starts the next order's clause.
    prefix = text[start:match.start()]
    separators = list(re.finditer(r"\b(?:and|then)\b|,", prefix, re.I))
    if separators:
        start += separators[-1].end()
    return text[start:end].strip()

from __future__ import annotations

import re
from typing import List


SECTION_PATTERNS = [
    r"^\s*(\d+(\.\d+)*)\s+([A-Z][^\n]{1,80})$",
    r"^\s*(Abstract|Introduction|Related Work|Methodology|Method|Approach|Experiments|Results|Discussion|Conclusion|Future Work|Acknowledgments|References)\s*$",
]


def build_sections(content: str, max_snippet_len: int = 240) -> dict:
    lines = content.splitlines()
    indices = []
    toc_flat: List[str] = []

    for i, line in enumerate(lines):
        if any(re.match(pat, line.strip(), re.IGNORECASE) for pat in SECTION_PATTERNS):
            indices.append(i)
            toc_flat.append(line.strip())

    sections = []
    for idx, start in enumerate(indices):
        end = indices[idx + 1] if idx + 1 < len(indices) else len(lines)
        seg = "\n".join(lines[start:end]).strip()
        sections.append(
            {
                "number": idx + 1,
                "title": lines[start].strip(),
                "start_offset": start,
                "end_offset": end,
                "snippet": seg[:max_snippet_len],
            }
        )

    return {"sections": sections, "toc_flat": toc_flat}

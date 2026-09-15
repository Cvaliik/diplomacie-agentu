"""build_referee_rules.py

Vytah pravidel pro rozhodciho: z docs/pravidla.md vybere casti 1, 3 (vcetne 3.3a, 3.4, 3.4a, 3.5),
7.2, 9 a 10 a zapise docs/pravidla_rozhodci.md. Poustet pri kazde zmene docs/pravidla.md
(BUILD.md cast 3).

    python build_referee_rules.py
"""

from __future__ import annotations

import re
import sys

import config

KEEP_PARTS = ("1", "3", "9", "10")   # cele casti
KEEP_SUB = ("7.2",)                  # jednotlive podkapitoly
OUT = config.DOCS_DIR / "pravidla_rozhodci.md"


def extract(text: str) -> str:
    lines = text.split("\n")
    title = lines[0]
    out = []
    part = None      # cislo aktualni casti (## N.)
    sub = None       # cislo aktualni podkapitoly (### N.M)
    for line in lines[1:]:
        m2 = re.match(r"^## (\d+[a-z]?)\. ", line)
        m3 = re.match(r"^### (\d+\.\d+[a-z]?) ", line)
        if m2:
            part, sub = m2.group(1), None
            if part in KEEP_PARTS or any(s.split(".")[0] == part for s in KEEP_SUB):
                out.append(line)
            continue
        if m3:
            sub = m3.group(1)
        if part in KEEP_PARTS or (sub in KEEP_SUB and part is not None):
            out.append(line)
    head = [title.replace("# Pravidla", "# Výtah pravidel pro rozhodčího:"), "",
            "Generováno skriptem `build_referee_rules.py` z `docs/pravidla.md` (části 1, 3, 7.2, 9 a 10).",
            "Neupravovat ručně; po každé změně pravidel skript spustit znovu.", ""]
    return "\n".join(head + out).rstrip() + "\n"


def main() -> int:
    text = config.RULES_PATH.read_text(encoding="utf-8")
    result = extract(text)
    OUT.write_text(result, encoding="utf-8")
    print("zapsano %s (%d znaku z %d)" % (OUT.relative_to(config.ROOT), len(result), len(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

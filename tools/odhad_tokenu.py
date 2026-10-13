"""tools/odhad_tokenu.py

Odhad vstupnich tokenu promptu sestavenych pres --dry-model (debug/*.md), bez volani modelu.
Prepocet z bajtu UTF-8 podle pomeru namereneho na skutecnych volanich:
    hrac A, tah 13 (24. 9. 2026): 59 434 B = 29 101 tokenu  -> 2.04 B/token
    kronikar, den 4 (13. 10. 2026): 120 692 B = 51 520 tokenu -> 2.34 B/token
Kompaktni JSON ma mene bajtu na token nez odsazeny, odhad po kompaktizaci je proto spis spodni mez.

    python tools/odhad_tokenu.py debug/turn_013_A.md debug/day_004_kronikar.md ...
"""

from __future__ import annotations

import sys
from pathlib import Path

RATIO = {"kronikar": 2.34, "default": 2.04}


def estimate(path: Path) -> tuple[int, int]:
    b = len(path.read_bytes())
    ratio = RATIO["kronikar"] if "kronikar" in path.name else RATIO["default"]
    return b, round(b / ratio)


def main() -> int:
    for arg in sys.argv[1:]:
        b, t = estimate(Path(arg))
        print("%-60s %8d B  ~%6d tokenu" % (arg, b, t))
    return 0


if __name__ == "__main__":
    sys.exit(main())

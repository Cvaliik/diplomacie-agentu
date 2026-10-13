"""tools/overit_kola.py

Prepocet kol 1 az N aktualnim enginem z akci ulozenych ve snimcich history/turn_NNN.json a srovnani
ekonomickeho stavu se snimky (texty, zpravy a doruceni se nesrovnavaji, ty dela run_turn.py).
Vychozi stav kola 0 je state.json z commitu ba9f4a1 (reset v1.11 pred tahem 1).

    python tools/overit_kola.py            kola 1 az 6
    python tools/overit_kola.py --do 9
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import engine  # noqa: E402
from validate import validate  # noqa: E402

START_COMMIT = "ba9f4a1"
# klice doplnene v2.0 (banky) a pole, ktera nevznikaji v enginu (run_turn.py: texty, zpravy, doruceni)
IGNORE = {"banks_K", "banks_AUR", "bank_U", "moratoria", "genre", "meta", "news", "messages_pending", "log",
          "npc_decisions", "private_log"}


def diff(a, b, path="", out=None, tol=1e-6):
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if path == "" and k in IGNORE:
                continue
            if k not in a or k not in b:
                out.append("%s.%s: jen v %s" % (path, k, "prepoctu" if k in a else "snimku"))
                continue
            diff(a[k], b[k], "%s.%s" % (path, k), out, tol)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append("%s: delka %d x %d" % (path, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, "%s[%d]" % (path, i), out, tol)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if abs(float(a) - float(b)) > tol:
            out.append("%s: %r x %r" % (path, a, b))
    elif a != b:
        out.append("%s: %r x %r" % (path, str(a)[:60], str(b)[:60]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--do", type=int, default=6)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    raw = subprocess.run(["git", "show", "%s:state.json" % START_COMMIT], cwd=ROOT, capture_output=True,
                         check=True).stdout.decode("utf-8")
    prev = json.loads(raw)
    engine.normalize(prev)
    npcdata = json.loads((ROOT / "npc.json").read_text(encoding="utf-8"))
    ok = True
    for k in range(1, args.do + 1):
        snap = json.loads((ROOT / "history" / ("turn_%03d.json" % k)).read_text(encoding="utf-8"))
        new, _, applied = engine.apply_turn(prev, npcdata, snap["actions"])
        errs = validate(prev, new, applied, actions=snap["actions"], views=engine.build_views(new, npcdata))
        old = json.loads(json.dumps(snap["state"]))
        engine.normalize(old)
        new["minsky"].pop("orit_world", None)   # v2.0: evidence tezby a potreby oritu
        d = diff(new, old)
        print("kolo %d: validate %d chyb, rozdilu ve stavu %d" % (k, len(errs), len(d)))
        for line in (errs + d)[:6]:
            print("    " + line)
        ok &= not errs and not d
        prev = snap["state"]
    print("VYSLEDEK:", "kola 1 az %d sedi" % args.do if ok else "ROZDILY")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

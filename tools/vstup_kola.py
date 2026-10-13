"""tools/vstup_kola.py

Rekonstrukce vstupu hracu pro odehrane kolo: stav pred kolem z commitu, stejny los zanru (deterministicky)
a otazky novinaru ze snimku kola. Zapise debug/vstup_kolo_NNN_X.md (system a user jako ostry tah).
Bez volani modelu.

    python tools/vstup_kola.py --kolo 7 --commit 3624cc2
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
import run_turn  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kolo", type=int, required=True)
    ap.add_argument("--commit", required=True, help="commit se state.json pred kolem")
    args = ap.parse_args()
    raw = subprocess.run(["git", "show", "%s:state.json" % args.commit], cwd=ROOT, capture_output=True,
                         check=True).stdout.decode("utf-8")
    state = json.loads(raw)
    engine.normalize(state)
    engine.precompute_needs(state)
    assert run_turn.next_turn(state) == args.kolo, "stav z commitu neni pred kolem %d" % args.kolo
    npcdata = json.loads((ROOT / "npc.json").read_text(encoding="utf-8"))
    snap = json.loads((ROOT / "history" / ("turn_%03d.json" % args.kolo)).read_text(encoding="utf-8"))
    views = engine.build_views(state, npcdata)
    run_turn.fill_auto_block(state, views)
    for pid in run_turn.active_players(state):
        info = run_turn.draw_genre(state, npcdata, pid, args.kolo) if pid in run_turn.GENRE_PLAYERS else None
        stored = ((snap.get("turns") or {}).get(pid) or {}).get("genre") or {}
        if info is not None:
            assert info["id"] == stored.get("id"), "los zanru %s nesedi se snimkem" % pid
            info["questions"] = list(stored.get("questions") or [])
        system, user = run_turn.player_prompt(state, views, pid, info)
        out = run_turn.DEBUG_DIR / ("vstup_kolo_%03d_%s.md" % (args.kolo, pid))
        run_turn.write_debug_prompt(out, "Vstup hráče %s, kolo %d (rekonstrukce)" % (pid, args.kolo), system, user)
        print("zapsano %s" % out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())

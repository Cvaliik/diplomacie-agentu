"""web_data.py

Data pro statickou stranku (BUILD.md cast 7): history/index.json, history/summary.json
a chronicle/index.json. Pouziva je run_turn.py (po kazdem tahu) a run_chronicle.py.

    python web_data.py      prepocita vsechny tri soubory ze snimku a kronik (zpetne)

Web nikdy nenacita vsechny snimky: summary.json nese jen to, co potrebuje mapa, slider a grafy;
plny snimek turn_NNN.json se nacita az po vyberu tahu.
"""

from __future__ import annotations

import datetime
import json
import re
import subprocess
import sys

import config

WEEKLY_DAYS = (7, 14, 21, 28)
FINAL_DAY = 30


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def _turn_files():
    out = []
    for p in config.HISTORY_DIR.glob("turn_*.json"):
        m = re.fullmatch(r"turn_(\d+)\.json", p.name)
        if m:
            out.append((int(m.group(1)), p))
    return sorted(out)


def _git_time(path):
    """Cas commitu souboru (pro tahy odehrane pred zavedenim played_at)."""
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%cI", "--", str(path.relative_to(config.ROOT))],
                           cwd=config.ROOT, capture_output=True, text=True, check=False)
        return r.stdout.strip() or None
    except OSError:
        return None


def _r(v, d=2):
    try:
        return round(float(v), d)
    except (TypeError, ValueError):
        return v


# --------------------------------------------------------------------------
# history/index.json
# --------------------------------------------------------------------------

def write_index(played_turn=None) -> None:
    """Seznam tahu s turn, day, slot, phase, cestou ke snimku a casem odehrani."""
    path = config.HISTORY_DIR / "index.json"
    known = {}
    if path.exists():
        try:
            for e in _load(path).get("turns", []):
                if isinstance(e, dict):
                    known[int(e["turn"])] = e
        except (ValueError, KeyError):
            known = {}
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    entries = []
    for turn, p in _turn_files():
        st = _load(p)["state"]
        played_at = (now if turn == played_turn else None) or (known.get(turn) or {}).get("played_at") or _git_time(p)
        entries.append({"turn": turn, "day": st["meta"]["day"], "slot": st["meta"]["slot"],
                        "phase": st["phase"], "file": "turn_%03d.json" % turn, "played_at": played_at})
    _write(path, {"turns": entries})


# --------------------------------------------------------------------------
# history/summary.json
# --------------------------------------------------------------------------

def _indicators(e) -> dict:
    """v1.11 (F13): goods (zasoba, vyroba, potreba), industry, law a tech pro panel statu."""
    return {"goods": {"stock": _r((e.get("stock") or {}).get("goods", 0), 1),
                      "vyroba": _r(e.get("goods_out"), 1) if e.get("goods_out") is not None else None,
                      "potreba": _r((e.get("need") or {}).get("goods"), 1) if (e.get("need") or {}).get("goods") is not None else None},
            "industry": _r(e.get("industry"), 2), "law": _r(e.get("law"), 2), "tech": _r(e.get("tech"), 2)}


def turn_summary(snap) -> dict:
    """Co web potrebuje o jednom tahu pro mapu, slider a grafy."""
    st = snap["state"]
    meta = st["meta"]
    states = {}
    for pid in ("A", "B"):
        p = st["players"][pid]
        states[pid] = {"wealth": _r(p.get("wealth")), "paper_wealth": _r(p.get("paper_wealth", 0)),
                       "pop": _r(p.get("pop"), 1), "orit": _r((p.get("prod") or {}).get("orit", 0)),
                       "occupied": list(p.get("occupied") or []), **_indicators(p)}
    for nid, n in st["npc"].items():
        states[nid] = {"wealth": _r(n.get("wealth")), "paper_wealth": _r(n.get("paper_wealth", 0)),
                       "status": n.get("status"), "kind": n.get("kind", "normal"),
                       "influence": {k: _r((n.get("influence") or {}).get(k, 0.0)) for k in ("A", "B")},
                       "pop": _r(n.get("pop"), 1), "orit": _r((n.get("prod") or {}).get("orit", 0)),
                       **_indicators(n)}
    C = st["players"]["C"]
    migration = []
    for rec in (st.get("minsky") or {}).get("migration_ledger") or []:
        for donor in rec.get("from") or []:
            pair = [donor, rec.get("to")]
            if pair not in migration:
                migration.append(pair)
    return {
        "turn": meta["turn"], "day": meta["day"], "slot": meta["slot"], "phase": st["phase"],
        "prices": {k: _r(v, 4) for k, v in (st.get("prices") or {}).items()},
        "metrics": {k: v for k, v in (st.get("metrics") or {}).items()},
        "union": {"name": C.get("name"), "active": bool(C.get("active")),
                  "members": list(C.get("members") or []), "candidates": list(C.get("candidates") or [])},
        "states": states,
        "deals": [{"id": d.get("id"), "type": d.get("type"), "owner": d.get("owner"),
                   "target": d.get("target"), "res": d.get("res")} for d in st.get("deals") or []],
        "invasions": [{"attacker": v.get("attacker"), "target": v.get("target"), "turns": v.get("turns"),
                       "need": 10 if (st["npc"].get(v.get("target")) or {}).get("kind") == "fallen" else 6}
                      for v in st.get("invasions") or []],
        "wars": [{"id": w.get("id"), "aggressor": w.get("aggressor"), "defender": w.get("defender"),
                  "since": w.get("since")} for w in st.get("wars") or []],
        "refugees": list(st.get("refugees") or []),
        "migration": migration,
        "news": list(snap.get("news") or []),
    }


def update_summary(snap) -> None:
    """Prida nebo prepise jeden tah v history/summary.json."""
    path = config.HISTORY_DIR / "summary.json"
    turns = []
    if path.exists():
        try:
            turns = _load(path).get("turns", [])
        except ValueError:
            turns = []
    row = turn_summary(snap)
    turns = [t for t in turns if int(t["turn"]) != int(row["turn"]) and int(t["turn"]) < int(row["turn"])]
    turns.append(row)
    turns.sort(key=lambda t: int(t["turn"]))
    _write(path, {"turns": turns})


def rebuild_summary() -> None:
    """history/summary.json znovu ze vsech snimku (zpetne, po rollbacku)."""
    _write(config.HISTORY_DIR / "summary.json",
           {"turns": [turn_summary(_load(p)) for _, p in _turn_files()]})


# --------------------------------------------------------------------------
# chronicle/index.json
# --------------------------------------------------------------------------

def write_chronicle_index() -> None:
    """Seznam kronik: den, soubor, typ (denni, tydenni, finale)."""
    entries = []
    for p in sorted(config.CHRONICLE_DIR.glob("day_*.md")):
        m = re.fullmatch(r"day_(\d+)\.md", p.name)
        if not m:
            continue
        day = int(m.group(1))
        typ = "finále" if day == FINAL_DAY else ("týdenní" if day in WEEKLY_DAYS else "denní")
        entries.append({"day": day, "file": p.name, "typ": typ})
    config.CHRONICLE_DIR.mkdir(exist_ok=True)
    _write(config.CHRONICLE_DIR / "index.json", {"days": entries})


def main() -> int:
    config.HISTORY_DIR.mkdir(exist_ok=True)
    write_index()
    rebuild_summary()
    write_chronicle_index()
    print("zapsano history/index.json, history/summary.json, chronicle/index.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

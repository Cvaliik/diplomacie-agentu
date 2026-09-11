"""test_run.py

Suchy beh bez volani modelu (BUILD.md cast 8, okno 45 tahu). Nic nezapisuje
do state.json ani do history/, jen pocita a tiskne.

Dve varianty podle rozhodnuti z 11. 9. 2026:

  (a) scenar ze zadani: A pujcuje N6 od tahu 8, B chrani N7, oba obchoduji obilim
  (b) realisticke pujcovani: hrac pujci jen v tahu, kdy nejake NPC zada pujcku
      (euforie) nebo ma deficit oritu; nejvys jedna pujcka na hrace a tah

Kriteria se vyhodnocuji v oknu 45 tahu. Pro tabulky do OPEN_QUESTIONS oddilu E
beh pokracuje do tahu 90.

Spusteni:
    python test_run.py
    python test_run.py --do 90
"""

from __future__ import annotations

import argparse
import sys

import config
import engine
from validate import validate

TEST_WINDOW = 45
PHASES_REQUIRED = ("displacement", "boom", "euphoria", "overtrading",
                   "distress", "panic", "crash")


# --------------------------------------------------------------------------
# scenare
# --------------------------------------------------------------------------

def _base_actions(turn: int, state) -> list[dict]:
    """Spolecny zaklad obou variant: obchod obilim a pakt B nad N7."""
    acts: list[dict] = []
    if turn == 1:
        acts.append({"player": "A", "type": "trade_offer", "target": "N1",
                     "res": "grain", "qty": 3, "price_per_unit": 0.8})
        acts.append({"player": "B", "type": "trade_offer", "target": "N2",
                     "res": "grain", "qty": 3, "price_per_unit": 0.8})
    if turn == 3:
        acts.append({"player": "B", "type": "protect", "target": "N7"})
    return acts


def scenario_a(turn: int, state) -> list[dict]:
    """(a) Scenar ze zadani."""
    acts = _base_actions(turn, state)
    if turn >= 8 and float(state["players"]["A"]["wealth"]) >= 10:
        acts.append({"player": "A", "type": "loan", "target": "N6", "amount": 10})
    return acts


def _loan_seekers(state) -> list[str]:
    """Kdo by podle Zprav zadal o pujcku.

    Dve situace z pravidel: ve fazi euphoria zadaji o pujcku NPC v boomu
    (drzitele oritu), a kdykoli od displacementu ma NPC deficit oritu, tedy
    potrebuje ho a nema vlastni tezbu.
    """
    out = []
    phase = state["phase"]
    for i, n in sorted(state["npc"].items()):
        if n.get("kind") == "fallen":
            continue
        if n["status"] not in ("independent", "sphere_A", "sphere_B"):
            continue
        orit_prod = float(n["prod"].get("orit", 0.0))
        orit_need = float(n.get("need", {}).get("orit", 0.0))
        zada = (phase == "euphoria" and orit_prod > 0) or \
               (phase in engine.ORIT_PHASES and orit_need > orit_prod)
        if zada:
            out.append(i)
    return out


def scenario_b(turn: int, state) -> list[dict]:
    """(b) Realisticke pujcovani, nejvys jedna pujcka na hrace a tah."""
    acts = _base_actions(turn, state)
    seekers = _loan_seekers(state)
    if not seekers:
        return acts
    for idx, pid in enumerate(("A", "B")):
        if len(acts) and sum(1 for a in acts if a["player"] == pid) >= engine.ACTION_LIMIT[pid]:
            continue
        if float(state["players"][pid]["wealth"]) < 12:
            continue
        # kazdy hrac si bere jineho zadatele, poradi se stridá podle tahu
        cil = seekers[(turn + idx) % len(seekers)]
        acts.append({"player": pid, "type": "loan", "target": cil, "amount": 10})
    return acts


# --------------------------------------------------------------------------
# beh
# --------------------------------------------------------------------------

def run(turns: int, action_fn):
    state, npcdata = engine.load_world(config.STATE_PATH, config.NPC_PATH)
    rows = []
    all_errors = []
    phase_first: dict[str, dict] = {}
    founders = None

    for t in range(1, turns + 1):
        prev = state
        actions = action_fn(t, state)
        new_state, events, applied = engine.apply_turn(state, npcdata, actions)
        views = engine.build_views(new_state, npcdata)
        errs = validate(prev, new_state, applied, actions=actions, views=views)
        if errs:
            all_errors.append((t, errs))

        ph = new_state["phase"]
        if ph not in phase_first:
            rec = [r for r in new_state["minsky"]["phase_log"] if r["to"] == ph]
            phase_first[ph] = {"turn": t, "day": engine.day_of(t),
                               "trigger": rec[-1]["threshold"] if rec else "start"}
        for e in events:
            if e.get("kind") == "union_founded" and founders is None:
                founders = {"turn": t, "members": list(e["members"]), "fund": e["fund"]}
            if e.get("kind") == "union_failed" and founders is None:
                founders = {"turn": t, "members": list(e.get("candidates", [])),
                            "failed": True}

        m = new_state["metrics"]
        C = new_state["players"]["C"]
        rows.append({
            "turn": t, "day": new_state["meta"]["day"], "phase": ph,
            "index": m["prosperity_index"], "W_real": m["W_real"],
            "n_bida": m["n_bida"],
            "prices": dict(new_state.get("prices") or {}),
            "vol_npc": m.get("trade_volume_npc", 0.0),
            "vol_players": m.get("trade_volume_players", 0.0),
            "members": list(C["members"]), "candidates": list(C["candidates"]),
            "errors": len(errs),
        })
        state = new_state

    return {"state": state, "rows": rows, "errors": all_errors,
            "phases": phase_first, "union": founders}


# --------------------------------------------------------------------------
# vystup
# --------------------------------------------------------------------------

def kriteria(res, window: int) -> bool:
    print("KONTROLNI SEZNAM (BUILD.md cast 8, okno %d tahu)" % window)
    print("-" * 78)
    ok = True
    ph = res["phases"]

    d = ph.get("displacement")
    passed = d is not None and d["turn"] == 7
    ok &= passed
    print("  [%s] displacement v tahu 7%s" % (
        "OK " if passed else "NE ",
        "" if passed else " (nastal: %s)" % (d["turn"] if d else "nikdy")))

    for name in PHASES_REQUIRED[1:]:
        rec = ph.get(name)
        passed = rec is not None and rec["turn"] <= window
        ok &= passed
        print("  [%s] faze %s%s" % (
            "OK " if passed else "NE ", name,
            " v tahu %d" % rec["turn"] if rec else " nenastala do tahu %d" % window))

    u = res["union"]
    passed = u is not None and not u.get("failed") and len(u["members"]) >= 3 \
        and u["turn"] <= window
    ok &= passed
    if u is None:
        print("  [NE ] vznik Unie s aspon 3 cleny (Unie nevznikla)")
    elif u.get("failed"):
        print("  [NE ] vznik Unie (zpusobilych jen %d)" % len(u["members"]))
    else:
        print("  [OK ] vznik Unie v tahu %d, zakladatelu %d: %s" % (
            u["turn"], len(u["members"]), ", ".join(u["members"])))

    idx_ok = all(r["index"] is not None for r in res["rows"][:window])
    ok &= idx_ok
    print("  [%s] index prosperity spocitan kazdy tah" % ("OK " if idx_ok else "NE "))

    val_errors = [(t, e) for t, e in res["errors"] if t <= window]
    val_ok = not val_errors
    ok &= val_ok
    print("  [%s] validate bez chyb" % ("OK " if val_ok else "NE "))
    for t, errs in val_errors[:10]:
        for e in errs:
            print("        tah %d: %s" % (t, e))
    return bool(ok)


def tabulky(res, label: str) -> None:
    rows = res["rows"]
    print()
    print("E.%s.1 faze" % label)
    print("  %-14s %5s %5s   %s" % ("faze", "tah", "den", "spoustec"))
    for name in engine.PHASE_ORDER:
        rec = res["phases"].get(name)
        if rec:
            print("  %-14s %5d %5d   %s" % (name, rec["turn"], rec["day"], rec["trigger"]))
        else:
            print("  %-14s %5s %5s   nenastala" % (name, "-", "-"))

    print()
    print("E.%s.2 index a ceny" % label)
    print("  %5s %8s %9s %6s   %s" % ("tah", "index", "W_real", "bida", "ceny zdroju"))
    for t in (1, 12, 30, 45, 60, 90):
        r = next((x for x in rows if x["turn"] == t), None)
        if not r:
            continue
        ceny = " ".join("%s %.2f" % (k, v) for k, v in sorted(r["prices"].items()))
        print("  %5d %8.2f %9.1f %6d   %s" % (
            r["turn"], r["index"], r["W_real"], r["n_bida"], ceny))

    print()
    print("E.%s.3 Unie" % label)
    u = res["union"]
    if u is None:
        print("  Unie nevznikla")
    elif u.get("failed"):
        print("  Unie nevznikla, zpusobilych %d" % len(u["members"]))
    else:
        print("  zakladatele (tah %d): %s" % (u["turn"], ", ".join(u["members"])))
        for t in (u["turn"], 60, 90):
            r = next((x for x in rows if x["turn"] == t), None)
            if r:
                print("  tah %2d: clenu %d (%s), kandidatu %d (%s)" % (
                    t, len(r["members"]), ", ".join(r["members"]) or "-",
                    len(r["candidates"]), ", ".join(r["candidates"]) or "-"))

    print()
    print("E.%s.4 obchod" % label)
    print("  %5s %14s %14s %8s" % ("tah", "NPC s NPC", "hraci", "podil NPC"))
    for t in (6, 30, 60, 90):
        r = next((x for x in rows if x["turn"] == t), None)
        if not r:
            continue
        total = r["vol_npc"] + r["vol_players"]
        podil = (r["vol_npc"] / total * 100.0) if total > 0 else 0.0
        print("  %5d %14.2f %14.2f %7.1f%%" % (t, r["vol_npc"], r["vol_players"], podil))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--do", type=int, default=90,
                    help="do ktereho tahu dopocitat tabulky (kriteria se meri v oknu 45)")
    args = ap.parse_args()

    vysledek = True
    for label, fn, popis in (
            ("a", scenario_a, "scenar ze zadani (A pujcuje N6 od tahu 8, B chrani N7)"),
            ("b", scenario_b, "realisticke pujcovani (jen kdyz NPC zada, max 1 na hrace a tah)")):
        print("=" * 78)
        print("VARIANTA %s: %s" % (label.upper(), popis))
        print("=" * 78)
        res = run(args.do, fn)
        ok = kriteria(res, TEST_WINDOW)
        print()
        print("VYSLEDEK varianty %s: %s" % (
            label.upper(), "vse proslo" if ok else "cast kriterii neprosla"))
        tabulky(res, label)
        print()
        vysledek &= ok

    return 0 if vysledek else 1


if __name__ == "__main__":
    sys.exit(main())

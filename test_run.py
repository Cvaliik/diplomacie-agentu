"""test_run.py

Suchy beh bez volani modelu (BUILD.md cast 8). Nic nezapisuje do state.json
ani do history/, jen pocita a tiskne.

Scenare podle rozhodnuti ze 14. 9. 2026 (pravidla v1.2):

  (0) nikdo netahne: hraci mlci, zadne akce. Kalibracni scenar.
      Kriteria: do tahu 15 zadne NPC v bide, W_real v tahu 30 aspon 90 % startu.
  (a) scenar ze zadani: A pujcuje N6 od tahu 8, B chrani N7, oba obchoduji obilim.
  (b) realisticke pujcovani: hrac pujci jen v tahu, kdy nejake NPC zada pujcku
      (euforie) nebo ma deficit oritu; nejvys jedna pujcka na hrace a tah.
      Kriteria pro (a) i (b): crash mezi dnem 7 a 11, Unie s aspon 3 zakladateli,
      validate 0 chyb.

Spusteni:
    python test_run.py
    python test_run.py --scenar 0
"""

from __future__ import annotations

import argparse
import sys

import config
import engine
from validate import validate

TURNS = 90
TRACKED = ("A", "B", "N1", "N6", "N11")


# --------------------------------------------------------------------------
# scenare
# --------------------------------------------------------------------------

def scenario_0(turn: int, state) -> list[dict]:
    """(0) Nikdo netahne."""
    return []


def _base_actions(turn: int, state) -> list[dict]:
    """Spolecny zaklad (a) a (b): obchod obilim a pakt B nad N7."""
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
    """Kdo by podle Zprav zadal o pujcku: v euforii drzitele oritu, od
    displacementu kazde NPC, ktere orit potrebuje a nema vlastni tezbu."""
    out = []
    phase = state["phase"]
    for i, n in sorted(state["npc"].items()):
        if n.get("kind") == "fallen":
            continue
        if n["status"] not in ("independent", "sphere_A", "sphere_B"):
            continue
        orit_prod = float(n["prod"].get("orit", 0.0))
        orit_need = float(engine.current_need(state, i).get("orit", 0.0))
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
        if sum(1 for a in acts if a["player"] == pid) >= engine.ACTION_LIMIT[pid]:
            continue
        if float(state["players"][pid]["wealth"]) < 12:
            continue
        cil = seekers[(turn + idx) % len(seekers)]
        acts.append({"player": pid, "type": "loan", "target": cil, "amount": 10})
    return acts


SCENARE = {
    "0": (scenario_0, "nikdo netahne"),
    "a": (scenario_a, "scenar ze zadani (A pujcuje N6 od tahu 8, B chrani N7)"),
    "b": (scenario_b, "realisticke pujcovani (jen kdyz NPC zada, max 1 na hrace a tah)"),
}


# --------------------------------------------------------------------------
# beh
# --------------------------------------------------------------------------

def run(turns: int, action_fn, state=None, npcdata=None):
    if state is None:
        state, npcdata = engine.load_world(config.STATE_PATH, config.NPC_PATH)
    w_start = float(state["metrics"]["W0"])
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
            "npc_bida": [i for i in m.get("poverty_ids", []) if engine.is_npc(i)],
            "prices": dict(new_state.get("prices") or {}),
            "vol_npc": m.get("trade_volume_npc", 0.0),
            "vol_players": m.get("trade_volume_players", 0.0),
            "vol_goods": m.get("trade_volume_goods", 0.0),
            "members": list(C["members"]), "candidates": list(C["candidates"]),
            "coups": sum(int(n.get("coups", 0)) for n in new_state["npc"].values()),
            "wealth": {i: float(engine.ent(new_state, i)["wealth"]) for i in engine.world_ids(new_state)},
            "industry": {i: float(engine.ent(new_state, i).get("industry") or 0.0) for i in TRACKED},
            "goods_out": {i: float(engine.ent(new_state, i).get("goods_out") or 0.0) for i in TRACKED},
            "errors": len(errs),
        })
        state = new_state

    return {"state": state, "rows": rows, "errors": all_errors,
            "phases": phase_first, "union": founders, "w_start": w_start}


def row_at(res, t):
    return next((x for x in res["rows"] if x["turn"] == t), None)


# --------------------------------------------------------------------------
# kriteria
# --------------------------------------------------------------------------

def kriteria_0(res) -> bool:
    print("KONTROLNI SEZNAM scenare (0)")
    print("-" * 78)
    ok = True
    prvni = next((r for r in res["rows"] if r["turn"] <= 15 and r["npc_bida"]), None)
    passed = prvni is None
    ok &= passed
    if passed:
        print("  [OK ] do tahu 15 zadne NPC v bide")
    else:
        print("  [NE ] do tahu 15 zadne NPC v bide (prvni v tahu %d: %s)" % (
            prvni["turn"], ", ".join(prvni["npc_bida"])))
    r30 = row_at(res, 30)
    podil = r30["W_real"] / res["w_start"] if res["w_start"] else 0.0
    passed = podil >= 0.9
    ok &= passed
    print("  [%s] W_real v tahu 30 aspon 90 %% startu (%.1f z %.1f, tj. %.1f %%)" % (
        "OK " if passed else "NE ", r30["W_real"], res["w_start"], podil * 100))
    val_ok = not res["errors"]
    ok &= val_ok
    print("  [%s] validate bez chyb" % ("OK " if val_ok else "NE "))
    for t, errs in res["errors"][:5]:
        print("        tah %d: %s" % (t, errs[0]))
    return bool(ok)


def kriteria_ab(res) -> bool:
    print("KONTROLNI SEZNAM (crash mezi dnem 7 a 11, Unie, validate)")
    print("-" * 78)
    ok = True
    crash = res["phases"].get("crash")
    passed = crash is not None and 7 <= crash["day"] <= 11
    ok &= passed
    if crash is None:
        print("  [NE ] crash mezi dnem 7 a 11 (crash nenastal)")
    else:
        print("  [%s] crash mezi dnem 7 a 11 (tah %d, den %d)" % (
            "OK " if passed else "NE ", crash["turn"], crash["day"]))
    u = res["union"]
    passed = u is not None and not u.get("failed") and len(u["members"]) >= 3
    ok &= passed
    if u is None:
        print("  [NE ] Unie s aspon 3 zakladateli (Unie nevznikla)")
    elif u.get("failed"):
        print("  [NE ] Unie s aspon 3 zakladateli (zpusobilych jen %d)" % len(u["members"]))
    else:
        print("  [OK ] Unie s aspon 3 zakladateli (tah %d: %s)" % (
            u["turn"], ", ".join(u["members"])))
    val_ok = not res["errors"]
    ok &= val_ok
    print("  [%s] validate bez chyb" % ("OK " if val_ok else "NE "))
    for t, errs in res["errors"][:5]:
        print("        tah %d: %s" % (t, errs[0]))
    return bool(ok)


def souhrn(res) -> None:
    print()
    print("  faze: " + ", ".join("%s t%d" % (k, v["turn"]) for k, v in res["phases"].items()))
    for t in (1, 12, 30, 45, 60, 90):
        r = row_at(res, t)
        if r:
            print("  tah %2d: index %6.2f  W_real %8.1f  v bide %2d  goods %.2f" % (
                t, r["index"], r["W_real"], r["n_bida"], r["prices"].get("goods", 0.0)))
    print("  prevratu celkem: %d" % res["rows"][-1]["coups"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenar", choices=["0", "a", "b", "vse"], default="vse")
    args = ap.parse_args()
    klice = ["0", "a", "b"] if args.scenar == "vse" else [args.scenar]

    vysledek = True
    for k in klice:
        fn, popis = SCENARE[k]
        print("=" * 78)
        print("SCENAR (%s): %s" % (k, popis))
        print("=" * 78)
        res = run(TURNS, fn)
        ok = kriteria_0(res) if k == "0" else kriteria_ab(res)
        souhrn(res)
        print()
        print("VYSLEDEK (%s): %s" % (k, "vse proslo" if ok else "cast kriterii neprosla"))
        print()
        vysledek &= ok
    return 0 if vysledek else 1


if __name__ == "__main__":
    sys.exit(main())

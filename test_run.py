"""test_run.py

Suchy beh bez volani modelu (BUILD.md cast 8). Nic nezapisuje do state.json
ani do history/, jen pocita a tiskne.

Scenare (pravidla v1.6):

  (0) nikdo netahne: hraci mlci, zadne akce.
      Kriteria: do tahu 15 nejvys dve NPC v bide a zadne z N1 az N5, N7, N11 az N14;
      W_real v tahu 30 aspon 90 % startu; do tahu 90 nejvys 6 NPC v bide (z 16).
  (a) scenar ze zadani: A pujcuje N6 od tahu 8, B chrani N7, oba obchoduji obilim.
  (b) realisticke pujcovani: hrac pujci jen v tahu, kdy nejake NPC zada pujcku
      (euforie) nebo ma deficit oritu; nejvys jedna pujcka na hrace a tah.
      Oba skripty navic prijimaji nabidky NPC (3.5): sell, ktere kryji deficit hrace,
      a loan_request ve fazich boom a euphoria, do limitu akci.
      Kriteria pro (a) i (b): crash mezi dnem 7 a 11, Unie s aspon 3 zakladateli,
      validate 0 chyb. Mine-li okno kvuli pujckam odmitnutym podle 3.4, je to informace.

Vyklad kriterii (0) podle pravidel cast 11.

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
PROTECTED = ("N1", "N2", "N3", "N4", "N5", "N7", "N11", "N12", "N13", "N14")
MAX_POVERTY_90 = 6


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


def _accept_offers(state, acts: list[dict]) -> None:
    """3.5: prijmi sell, ktere kryji deficit hrace, a loan_request v boom a euphoria."""
    turn = int(state["meta"]["turn"]) + 1
    for o in state.get("offers", []):
        pid = o["player"]
        if pid not in ("A", "B") or turn > int(o["expires"]):
            continue
        if sum(1 for a in acts if a["player"] == pid) >= engine.ACTION_LIMIT[pid]:
            continue
        if o["type"] == "sell":
            deficit = float(engine.current_need(state, pid).get(o["res"], 0.0)) - \
                engine.supply_of(state, pid, o["res"])
            if deficit > 0:
                acts.append({"player": pid, "type": "accept_offer", "offer_id": o["offer_id"]})
        elif o["type"] == "loan_request" and state["phase"] in ("boom", "euphoria"):
            if float(state["players"][pid]["wealth"]) >= float(o["amount"]):
                acts.append({"player": pid, "type": "accept_offer", "offer_id": o["offer_id"]})


def scenario_a(turn: int, state) -> list[dict]:
    """(a) Scenar ze zadani."""
    acts = _base_actions(turn, state)
    if turn >= 8 and float(state["players"]["A"]["wealth"]) >= 10:
        acts.append({"player": "A", "type": "loan", "target": "N6", "amount": 10})
    _accept_offers(state, acts)
    return acts


def _loan_seekers(state) -> list[str]:
    """Kdo by podle Zprav zadal o pujcku: v euforii drzitele oritu, od
    displacementu kazde NPC, ktere orit potrebuje a nema vlastni tezbu."""
    out = []
    phase = state["phase"]
    for i, n in sorted(state["npc"].items(), key=lambda x: int(x[0][1:])):
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
    if seekers:
        for idx, pid in enumerate(("A", "B")):
            if sum(1 for a in acts if a["player"] == pid) >= engine.ACTION_LIMIT[pid]:
                continue
            if float(state["players"][pid]["wealth"]) < 12:
                continue
            cil = seekers[(turn + idx) % len(seekers)]
            acts.append({"player": pid, "type": "loan", "target": cil, "amount": 10})
    _accept_offers(state, acts)
    return acts


SCENARE = {
    "0": (scenario_0, "nikdo netahne"),
    "a": (scenario_a, "scenar ze zadani (A pujcuje N6 od tahu 8, B chrani N7)"),
    "b": (scenario_b, "realisticke pujcovani (jen kdyz NPC zada, max 1 na hrace a tah)"),
}


# --------------------------------------------------------------------------
# beh
# --------------------------------------------------------------------------

def _balance(state, applied):
    """Svetova bilance ropy a obili v tahu: vyroba, potreba domacnosti a prumyslu, pokuty."""
    out = {}
    for res in ("oil", "grain"):
        prod = sum(engine.supply_of(state, i, res) for i in engine.world_ids(state))
        hh = sum(engine.household_need(engine.ent(state, i))[res] for i in engine.world_ids(state))
        ind = 0.0
        if res in engine.GOODS_INPUT:
            ind = sum(engine.GOODS_INPUT[res] * float(engine.ent(state, i).get("goods_out") or 0.0)
                      for i in engine.world_ids(state))
        pen = sum(float(a["outputs"]["pokuta_podle_statku"].get(res, 0.0))
                  for a in applied if a["rule"].startswith("4.1 zdroje"))
        out[res] = {"vyroba": prod, "domacnosti": hh, "prumysl": ind, "pokuty": pen}
    # v1.7: svetova bilance goods (kapacita, plan, vyroba, spotreba, prodano, cena)
    ids = engine.world_ids(state)
    out["goods"] = {
        "kapacita": sum(float(engine.ent(state, i).get("goods_capacity") or 0.0) for i in ids),
        "planovano": sum(float(engine.ent(state, i).get("goods_planned") or 0.0) for i in ids),
        "vyroba": sum(float(engine.ent(state, i).get("goods_out") or 0.0) for i in ids),
        "spotreba": sum(float((engine.ent(state, i).get("need") or {}).get("goods", 0.0)) for i in ids),
        "prodano": sum(float(engine.ent(state, i).get("goods_sold_last") or 0.0) for i in ids),
        "cena": float((state.get("prices") or {}).get("goods", 0.0)),
    }
    return out


def run(turns: int, action_fn, state=None, npcdata=None, keep_applied=False):
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
                founders = {"turn": t, "members": list(e["members"]), "fund": e["fund"],
                            "candidates": list(e.get("candidates", []))}
            if e.get("kind") == "union_failed" and founders is None:
                founders = {"turn": t, "members": list(e.get("candidates", [])), "failed": True}

        m = new_state["metrics"]
        C = new_state["players"]["C"]
        stock_world = {r: 0.0 for r in engine.STOCK_RESOURCES}
        for i in engine.world_ids(new_state):
            for r in engine.STOCK_RESOURCES:
                stock_world[r] += float(engine.ent(new_state, i)["stock"].get(r, 0.0))
        rows.append({
            "turn": t, "day": new_state["meta"]["day"], "phase": ph,
            "index": m["prosperity_index"], "W_real": m["W_real"],
            "n_bida": m["n_bida"],
            "npc_bida": [i for i in m.get("poverty_ids", []) if engine.is_npc(i)],
            "prices": dict(new_state.get("prices") or {}),
            "vol_npc": m.get("trade_volume_npc", 0.0),
            "vol_players": m.get("trade_volume_players", 0.0),
            "vol_goods": m.get("trade_volume_goods", 0.0),
            "vol_ab": m.get("trade_volume_AB", 0.0),
            "members": list(C["members"]), "candidates": list(C["candidates"]),
            "fund": float(C["wealth"]) if C["active"] else None,
            "solidarity": sum(float(v) for v in (new_state.get("union_solidarity") or {}).values()),
            "contributions": sum(float(v) for v in (new_state.get("union_contributions") or {}).values()),
            "spheres": {p: sum(1 for x in new_state["npc"].values() if x["status"] == "sphere_%s" % p)
                        for p in ("A", "B")},
            "coups": sum(int(x.get("coups", 0)) for x in new_state["npc"].values()),
            "wealth": {i: float(engine.ent(new_state, i)["wealth"]) for i in engine.world_ids(new_state)},
            "law": {i: float(x["law"]) for i, x in new_state["npc"].items()},
            "industry": {i: float(engine.ent(new_state, i).get("industry") or 0.0) for i in TRACKED},
            "goods_out": {i: float(engine.ent(new_state, i).get("goods_out") or 0.0) for i in TRACKED},
            "stock_world": stock_world,
            # v1.8: svetova produkce zdroju, clo celni unie a investice do zdroju
            "prod_world": {r: sum(engine.supply_of(new_state, i, r) for i in engine.world_ids(new_state))
                           for r in ("oil", "grain", "metal", "orit")},
            "tariff": sum(float(v) for v in (new_state.get("union_tariff") or {}).values()),
            "invest_prod": sum(1 for e in events if e.get("kind") in ("invest_prod_done", "npc_invest_prod")),
            "balance": _balance(new_state, applied),
            "decisions": [(d["player"], d["action"], d["outcome"]) for d in new_state.get("npc_decisions", [])],
            "offers_new": [(o["player"], o["type"]) for o in new_state.get("offers_new", [])],
            "offers_accepted": [(e["player"], e["offer"]["type"]) for e in events if e.get("kind") == "offer_accepted"],
            "errors": len(errs),
            "applied": applied if keep_applied else None,
        })
        state = new_state

    return {"state": state, "rows": rows, "errors": all_errors,
            "phases": phase_first, "union": founders, "w_start": w_start}


def row_at(res, t):
    return next((x for x in res["rows"] if x["turn"] == t), None)


def poverty_measures(res):
    """Miry pro kriteria (0): ruzna NPC v bide do tahu 15 a nejvyssi soubezny pocet do 90."""
    ever15 = sorted({i for r in res["rows"] if r["turn"] <= 15 for i in r["npc_bida"]},
                    key=lambda x: int(x[1:]))
    peak = max(res["rows"], key=lambda r: len(r["npc_bida"]))
    ever90 = sorted({i for r in res["rows"] for i in r["npc_bida"]}, key=lambda x: int(x[1:]))
    return ever15, peak, ever90


# --------------------------------------------------------------------------
# kriteria
# --------------------------------------------------------------------------

def kriteria_0(res) -> bool:
    print("KONTROLNI SEZNAM scenare (0)")
    print("-" * 78)
    ok = True
    ever15, peak, ever90 = poverty_measures(res)
    chranena = [i for i in ever15 if i in PROTECTED]

    passed = len(ever15) <= 2
    ok &= passed
    print("  [%s] do tahu 15 nejvys dve NPC v bide (%d: %s)" % (
        "OK " if passed else "NE ", len(ever15), ", ".join(ever15) or "zadne"))
    passed = not chranena
    ok &= passed
    print("  [%s] do tahu 15 v bide zadne z N1 az N5, N7, N11 az N14 (%s)" % (
        "OK " if passed else "NE ", ", ".join(chranena) or "zadne"))

    r30 = row_at(res, 30)
    podil = r30["W_real"] / res["w_start"] if res["w_start"] else 0.0
    passed = podil >= 0.9
    ok &= passed
    print("  [%s] W_real v tahu 30 aspon 90 %% startu (%.1f z %.1f, tj. %.1f %%)" % (
        "OK " if passed else "NE ", r30["W_real"], res["w_start"], podil * 100))

    passed = len(peak["npc_bida"]) <= MAX_POVERTY_90
    ok &= passed
    print("  [%s] do tahu 90 nejvys %d NPC v bide z 16 (nejvic %d v tahu %d; ruznych za beh %d)" % (
        "OK " if passed else "NE ", MAX_POVERTY_90, len(peak["npc_bida"]), peak["turn"], len(ever90)))

    print("  [info] validate: %s" % ("0 chyb" if not res["errors"] else "%d tahu s chybou" % len(res["errors"])))
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
    loans = [d for r in res["rows"] for d in r["decisions"] if d[1] == "loan"]
    refused = sum(1 for d in loans if d[2] in ("protinavrh", "odmitnuto"))
    if not passed:
        print("  [info] pujcky podle 3.4: %d vyhodnocenych, %d neprijatych" % (len(loans), refused))
    u = res["union"]
    passed = u is not None and not u.get("failed") and len(u["members"]) >= 3
    ok &= passed
    if u is None:
        print("  [NE ] Unie s aspon 3 zakladateli (Unie nevznikla)")
    elif u.get("failed"):
        print("  [NE ] Unie s aspon 3 zakladateli (skupina jen %d)" % len(u["members"]))
    else:
        print("  [OK ] Unie s aspon 3 zakladateli (tah %d: %s)" % (u["turn"], ", ".join(u["members"])))
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
            print("  tah %2d: index %6.2f  W_real %8.1f  v bide %2d  oil %.2f goods %.2f  NPC v bide: %s" % (
                t, r["index"], r["W_real"], r["n_bida"], r["prices"].get("oil", 0.0),
                r["prices"].get("goods", 0.0), ", ".join(r["npc_bida"]) or "-"))
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

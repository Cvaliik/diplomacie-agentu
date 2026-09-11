"""test_run.py

Suchy beh bez volani modelu (BUILD.md cast 8). Nic nezapisuje do state.json
ani do history/, jen pocita a tiskne.

Scenar zadani: A pujcuje N6 od tahu 8, B chrani N7, oba obchoduji obilim,
N6 exploruje (automaticky podle pravidla 5).

Kontroluje se: displacement v tahu 7, boom, euphoria, overtrading, distress,
panic, crash, vznik Unie s aspon 3 cleny, index spocitany kazdy tah,
validate bez chyb.

Pokud Minsky neprojde vsemi fazemi do tahu 12, skript dopocita diagnosticky
beh do tahu 90 a vytiskne konkretni cisla pro docs/OPEN_QUESTIONS.md.
Prahy v pravidlech nijak nemeni.

Spusteni:
    python test_run.py
    python test_run.py --diagnostika-do 90
"""

from __future__ import annotations

import argparse
import sys

import config
import engine
from validate import validate

PHASES_REQUIRED = ("displacement", "boom", "euphoria", "overtrading",
                   "distress", "panic", "crash")


def scripted_actions(turn: int, state) -> list[dict]:
    """Scenar ze zadani."""
    acts: list[dict] = []
    if turn == 1:
        acts.append({"player": "A", "type": "trade_offer", "target": "N1",
                     "res": "grain", "qty": 3, "price_per_unit": 0.8})
        acts.append({"player": "B", "type": "trade_offer", "target": "N2",
                     "res": "grain", "qty": 3, "price_per_unit": 0.8})
    if turn == 3:
        acts.append({"player": "B", "type": "protect", "target": "N7"})
    if turn >= 8:
        if float(state["players"]["A"]["wealth"]) >= 10:
            acts.append({"player": "A", "type": "loan", "target": "N6", "amount": 10})
    return acts


def aggressive_actions(turn: int, state) -> list[dict]:
    """Diagnosticky scenar: oba hraci pujcuji co nejvic, aby se ukazalo,
    kdy by prahy Minskyho cyklu vubec mohly nastat. Neni to herni doporuceni."""
    acts = scripted_actions(turn, state)
    if turn >= 8:
        targets = [i for i, n in sorted(state["npc"].items())
                   if n.get("kind") == "normal"]
        pick = targets[(turn * 2) % len(targets)]
        for pid in ("A", "B"):
            if float(state["players"][pid]["wealth"]) >= 12:
                if sum(1 for a in acts if a["player"] == pid) < engine.ACTION_LIMIT[pid]:
                    acts.append({"player": pid, "type": "loan", "target": pick,
                                 "amount": 10})
    return acts


def run(turns: int, action_fn, verbose: bool = True):
    state, npcdata = engine.load_world(config.STATE_PATH, config.NPC_PATH)
    rows = []
    all_errors = []
    phase_first_turn: dict[str, int] = {"pre": 0}
    union_info = None

    for t in range(1, turns + 1):
        prev = state
        actions = action_fn(t, state)
        new_state, events, applied = engine.apply_turn(state, npcdata, actions)
        views = engine.build_views(new_state, npcdata)
        errs = validate(prev, new_state, applied, actions=actions, views=views)
        if errs:
            all_errors.append((t, errs))
        ph = new_state["phase"]
        phase_first_turn.setdefault(ph, t)
        for e in events:
            if e.get("kind") == "union_founded" and union_info is None:
                union_info = {"turn": t, "members": e["members"], "fund": e["fund"]}
            if e.get("kind") == "union_failed" and union_info is None:
                union_info = {"turn": t, "members": e.get("candidates", []),
                              "failed": True}
        m = new_state["metrics"]
        debts = sum(sum(float(v) for v in n["debt"].values())
                    for n in new_state["npc"].values())
        npc_wealth = sum(float(n["wealth"]) for n in new_state["npc"].values())
        rows.append({
            "turn": t, "day": new_state["meta"]["day"], "phase": ph,
            "orit": new_state["minsky"]["orit_price"],
            "index": m["prosperity_index"], "W_real": m["W_real"],
            "n_bida": m["n_bida"], "debts": debts, "npc_wealth": npc_wealth,
            "debt_ratio": (debts / npc_wealth) if npc_wealth else 0.0,
            "defaults": len(new_state["minsky"]["defaults"]),
            "errors": len(errs),
        })
        state = new_state

    if verbose:
        print(f"{'tah':>3} {'den':>3}  {'faze':<13} {'cena oritu':>10} "
              f"{'W_real':>8} {'index':>7} {'bida':>4} {'dluh/wealth':>11} "
              f"{'default':>7} {'chyby':>5}")
        print("-" * 88)
        for r in rows:
            orit = "-" if r["orit"] is None else f"{r['orit']:.2f}"
            print(f"{r['turn']:>3} {r['day']:>3}  {r['phase']:<13} {orit:>10} "
                  f"{r['W_real']:>8.1f} {r['index']:>7.2f} {r['n_bida']:>4} "
                  f"{r['debt_ratio']:>11.3f} {r['defaults']:>7} {r['errors']:>5}")
    return state, rows, all_errors, phase_first_turn, union_info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diagnostika-do", type=int, default=90,
                    help="do ktereho tahu dopocitat diagnosticky beh")
    ap.add_argument("--bez-diagnostiky", action="store_true")
    args = ap.parse_args()

    print("=" * 88)
    print("SUCHY BEH 12 TAHU (scenar ze zadani, bez volani modelu)")
    print("=" * 88)
    state, rows, errors, phases, union = run(12, scripted_actions)

    print()
    print("KONTROLNI SEZNAM (BUILD.md cast 8)")
    print("-" * 88)
    ok = True

    disp = phases.get("displacement")
    passed = disp == 7
    ok &= passed
    print(f"  [{'OK ' if passed else 'NE '}] displacement v tahu 7"
          f"{'' if passed else f' (nastal: {disp})'}")

    for ph in PHASES_REQUIRED[1:]:
        t = phases.get(ph)
        passed = t is not None
        ok &= passed
        print(f"  [{'OK ' if passed else 'NE '}] faze {ph}"
              f"{f' v tahu {t}' if passed else ' nenastala do tahu 12'}")

    passed = union is not None and not union.get("failed") and len(union["members"]) >= 3
    ok &= passed
    if union is None:
        print("  [NE ] vznik Unie s aspon 3 cleny (Unie nevznikla, crash nenastal)")
    elif union.get("failed"):
        print(f"  [NE ] vznik Unie s aspon 3 cleny (kandidatu jen {len(union['members'])})")
    else:
        print(f"  [OK ] vznik Unie v tahu {union['turn']}, clenu {len(union['members'])}")

    idx_ok = all(r["index"] is not None for r in rows)
    ok &= idx_ok
    print(f"  [{'OK ' if idx_ok else 'NE '}] index prosperity spocitan kazdy tah")

    val_ok = not errors
    ok &= val_ok
    print(f"  [{'OK ' if val_ok else 'NE '}] validate bez chyb")
    for t, errs in errors:
        for e in errs:
            print(f"        tah {t}: {e}")

    print()
    print(f"VYSLEDEK: {'vse proslo' if ok else 'cast kriterii neprosla'}")

    if not args.bez_diagnostiky and not ok:
        print()
        print("=" * 88)
        print(f"DIAGNOSTIKA: kdy by faze nastaly (agresivni pujcovani, do tahu "
              f"{args.diagnostika_do if hasattr(args, 'diagnostika_do') else args.__dict__['diagnostika_do']})")
        print("=" * 88)
        limit = args.__dict__["diagnostika_do"]
        _, drows, derrors, dphases, dunion = run(limit, aggressive_actions, verbose=False)
        print(f"{'faze':<15} {'tah':>5} {'den':>5}   poznamka")
        print("-" * 88)
        for ph in engine.PHASE_ORDER:
            t = dphases.get(ph)
            if t is None:
                print(f"{ph:<15} {'-':>5} {'-':>5}   nenastala do tahu {limit}")
            else:
                row = next((r for r in drows if r["turn"] == t), None)
                note = ""
                if row:
                    if ph == "euphoria":
                        note = f"cena oritu {row['orit']:.2f}"
                    elif ph == "overtrading":
                        note = f"dluh/wealth {row['debt_ratio']:.3f}"
                    elif ph in ("distress", "panic"):
                        note = f"zaznamu o nesplaceni {row['defaults']}"
                print(f"{ph:<15} {t:>5} {engine.day_of(t):>5}   {note}")
        if dunion and not dunion.get("failed"):
            print(f"\nUnie vznikla v tahu {dunion['turn']} s {len(dunion['members'])} cleny: "
                  f"{', '.join(dunion['members'])}")
        elif dunion:
            print(f"\nUnie nevznikla, kandidatu {len(dunion['members'])}")
        else:
            print("\nUnie nevznikla, crash do konce behu nenastal")
        if derrors:
            print(f"\nvalidate nahlasilo chyby v {len(derrors)} tazich:")
            for t, errs in derrors[:10]:
                print(f"  tah {t}: {errs[0]}")

        print()
        print("PODKLAD PRO docs/OPEN_QUESTIONS.md (prahy nemenim, jen navrhuji):")
        print("-" * 88)
        boom_t = dphases.get("boom")
        if boom_t:
            row12 = next((r for r in drows if r["turn"] == 12), None)
            if row12 and row12["orit"]:
                print(f"  cena oritu v tahu 12: {row12['orit']:.2f} "
                      f"(prah euphoria je 20)")
            print(f"  boom zacal v tahu {boom_t}, cena roste x1.15 za tah "
                  f"z vychozich 10")
        print("  aby cyklus probehl do tahu 12, musel by kazdy prah nastat "
              "prakticky obratem po predchozim")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

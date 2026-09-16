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


def _foreign(acts, pid) -> int:
    """Pocet zahranicnich akci hrace (v1.11: domaci akce a zprava se do limitu nepocitaji)."""
    return sum(1 for a in acts if a["player"] == pid and engine.action_slot(a) == "foreign")


def _accept_offers(state, acts: list[dict], stock_cap: dict | None = None, only=("A", "B")) -> None:
    """3.5: prijmi sell, ktere kryji deficit hrace, a loan_request v boom a euphoria.
    stock_cap {hrac: tahy}: sell jen pri zasobe statku pod tolika tahy potreby (scenar v)."""
    turn = int(state["meta"]["turn"]) + 1
    for o in state.get("offers", []):
        pid = o["player"]
        if pid not in only or turn > int(o["expires"]):
            continue
        if _foreign(acts, pid) >= engine.ACTION_LIMIT[pid]:
            continue
        if o["type"] == "sell":
            deficit = float(engine.current_need(state, pid).get(o["res"], 0.0)) - \
                engine.supply_of(state, pid, o["res"])
            if stock_cap and pid in stock_cap:
                need = float(engine.current_need(state, pid).get(o["res"], 0.0))
                if float(state["players"][pid]["stock"].get(o["res"], 0.0)) >= stock_cap[pid] * need:
                    continue
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
            if _foreign(acts, pid) >= engine.ACTION_LIMIT[pid]:
                continue
            if float(state["players"][pid]["wealth"]) < 12:
                continue
            cil = seekers[(turn + idx) % len(seekers)]
            acts.append({"player": pid, "type": "loan", "target": cil, "amount": 10})
    _accept_offers(state, acts)
    return acts


TURNS_K = 15


def scenario_k(turn: int, state) -> list[dict]:
    """(k) v1.10: soutez o cil, jeden pakt, pakt s invazi, arm, valka hracu a ustup."""
    acts: list[dict] = []
    if turn == 2:
        # cena platna v tomto tahu: engine ji prepocita na zacatku tahu (4.1b), proto na kopii
        nxt = engine.deepcopy(state)
        engine.step_prices(nxt, engine.Trace())
        price = round(engine.market_price(nxt, "oil"), 4)
        for pid in ("A", "B"):
            acts.append({"player": pid, "type": "trade_offer", "target": "N3", "res": "oil",
                         "qty": 3, "price_per_unit": price})
    if turn == 3:
        acts += [{"player": "A", "type": "protect", "target": "N1"},
                 {"player": "B", "type": "protect", "target": "N1"},
                 {"player": "B", "type": "protect", "target": "N6"}]   # B ziska vliv pred valkou (N2 pakt odmitne hodem)
    if turn == 4:
        acts += [{"player": "B", "type": "protect", "target": "N1"},
                 {"player": "B", "type": "protect", "target": "N4"}]
    if turn == 5:
        acts += [{"player": "A", "type": "protect", "target": "N5"},
                 {"player": "B", "type": "invade", "target": "N5"}]
    if 6 <= turn <= 9:
        acts += [{"player": "B", "type": "invade", "target": "N5"},
                 {"player": "A", "type": "arm", "amount": 40}]
    if turn == 10:
        acts.append({"player": "A", "type": "declare_war", "target": "B"})
    if turn == 13:
        war = next((w for w in state.get("wars", []) if "B" in (w["aggressor"], w["defender"])), None)
        acts.append({"player": "B", "type": "cancel", "deal_id": war["id"] if war else "w?"})
    if turn == 15:
        # 1b: tah 14 A neodpovi (nabidka propadne), tah 15 A vyslovne ustoupi
        war = next((w for w in state.get("wars", []) if "A" in (w["aggressor"], w["defender"])), None)
        acts.append({"player": "A", "type": "cancel", "deal_id": war["id"] if war else "w?", "retreat": True})
    return acts


def analyza_k(res) -> list[tuple[str, bool, str]]:
    """Body oddilu T (v1.10): (bod, ano/ne, cisla)."""
    R = {r["turn"]: r for r in res["rows"]}

    def ev(t, kind, **kw):
        return [e for e in R[t]["events"] if e.get("kind") == kind and all(e.get(k) == v for k, v in kw.items())]

    def rules(t, name):
        return [a for a in R[t]["applied"] if a["rule"] == name]

    out = []
    # 1. soutez o N3 ropu
    lost = ev(2, "competition_lost", npc="N3")
    dec = [d for d in R[2]["decisions"] if d[1] == "trade_offer"]
    comp = rules(2, "3.4a soutez o cil")
    ok = len(lost) == 1 and len({d[0] for d in dec}) == 1 and lost[0]["player"] not in {d[0] for d in dec}
    out.append(("tah 2: jedna trade_offer provedena, log prohraného", ok,
                "soutěž %s; vyhodnoceno 3.4 jen %s (%s); log %s: „%s“" % (
                    comp[0]["outputs"] if comp else "-", ", ".join(sorted({d[0] for d in dec})) or "nikdo",
                    ", ".join(d[2] for d in dec), lost[0]["player"] if lost else "-",
                    R[2]["private_log_last"].get(lost[0]["player"], "-") if lost else "-")))
    # 2. jeden pakt N1
    lost3 = ev(3, "competition_lost", npc="N1")
    owners = R[3]["protect_n"].get("N1", [])
    out.append(("tah 3: nejvýš jeden pakt na N1", len(lost3) == 1 and len(owners) <= 1,
                "prohrál %s; výsledek vítěze %s; pakt N1 po tahu 3: %s" % (
                    lost3[0]["player"] if lost3 else "-",
                    [d for d in R[3]["decisions"] if d[1] == "protect"], owners or "žádný")))
    # 3. vyrazeni B protect N1 v tahu 4
    inv4 = ev(4, "action_invalid", player="B", type="protect")
    holder = R[3]["protect_n"].get("N1", [])
    expect = holder == ["A"]
    ok = bool(inv4) and inv4[0]["reason"] == "NPC je pod paktem A" if expect else not inv4
    out.append(("tah 4: B protect N1 vyřazen bez hodu", ok and expect,
                "pakt N1 před tahem 4: %s; vyřazení: %s; hod B u N1: %s" % (
                    holder or "žádný", inv4[0]["reason"] if inv4 else "ne",
                    [d for d in R[4]["decisions"] if d[0] == "B"] or "žádný")))
    # 4. pakt a invaze v tomtez tahu
    dec5 = [d for d in R[5]["decisions"] if d[0] == "A" and d[1] == "protect"]
    blk = ev(5, "invade_blocked", player="B")
    prog = ev(5, "invade_progress", player="B")
    war5 = ev(5, "war_declared")
    order = [a["rule"] for a in R[5]["applied"] if a["rule"] in ("3.4 rozhodnuti NPC", "3.3 invaze", "3.2 protect")]
    out.append(("tah 5: pakt vyhodnocen před invazí; válka v tomtéž tahu", bool(war5),
                "pakt A u N5: %s; pořadí pravidel %s; invaze B: %s; válka: %s" % (
                    dec5 or "-", order, (blk[0]["reason"] if blk else ("postup %d" % prog[0]["turns"] if prog else "-")),
                    "ano" if war5 else "ne")))
    # 5. arm 40 -> +25 power
    gains = [a["outputs"]["gain"] for t in range(6, 10) for a in rules(t, "3.2 arm")]
    out.append(("tahy 6 až 9: arm 40 = +25 power", len(gains) == 4 and all(abs(g - 25.0) < 1e-9 for g in gains),
                "přírůstky %s; power A tah 5 %.1f, tah 9 %.1f" % (gains, R[5]["power"]["A"], R[9]["power"]["A"])))
    # 6. valka od tahu 10
    w10 = ev(10, "war_declared")
    out.append(("válka od tahu 10", bool(w10) and all(R[t]["wars"] for t in (10, 11, 12)),
                "%s; aktivní v tazích %s" % (w10[0] if w10 else "nevyhlášena",
                                             [t for t in range(1, 15) if R[t]["wars"]])))
    # 7. ztraty za tah a preruseni obchodu
    losses = []
    for t in (10, 11, 12):
        for a in rules(t, "3.3a valka"):
            o = a["outputs"]
            losses.append("t%d A power %.1f→%.1f wealth %.1f→%.1f, B power %.1f→%.1f wealth %.1f→%.1f" % (
                t, o["A"]["power_pred"], o["A"]["power_po"], o["A"]["wealth_pred"], o["A"]["wealth_po"],
                o["B"]["power_pred"], o["B"]["power_po"], o["B"]["wealth_pred"], o["B"]["wealth_po"]))
    ab = {t: sum(a["outputs"]["objem"] for a in rules(t, "4.1a automaticky trh")
                 if {a["inputs"]["prodejce"], a["inputs"]["kupec"]} == {"A", "B"}) for t in range(8, 15)}
    ok = len(losses) == 3 and all(ab[t] == 0 for t in (10, 11, 12))
    out.append(("tahy 10 až 12: power −10, wealth −5 %, obchod A s B přerušen", ok,
                "; ".join(losses) + "; objem A s B podle tahů %s" % {t: round(v, 2) for t, v in ab.items()}))
    # 8. primeri (v1.10 dodatek)
    inf9 = {nid: v for nid, v in R[9]["influence"]["B"].items() if v > 0}
    out.append(("vliv B u dvou NPC před válkou (tah 9)", len(inf9) >= 2,
                "vliv B %s; pakty B po tahu 9: %s" % ({k: round(v, 1) for k, v in inf9.items()},
                                                    [nid for nid, o in R[9]["protect_n"].items() if "B" in o])))
    offer = ev(13, "war_cancel_offered", player="B")
    out.append(("tah 13: B nabídne příměří, válka trvá", bool(offer) and bool(R[13]["wars"]) and not rules(13, "3.3a konec valky"),
                "nabídka %s; válka po tahu 13: %s" % ("ano" if offer else "ne", "trvá" if R[13]["wars"] else "skončila")))
    exp = ev(14, "war_cancel_expired", player="B")
    loss14 = rules(14, "3.3a valka")
    ok = bool(exp) and bool(R[14]["wars"]) and bool(loss14) and not rules(14, "3.3a konec valky")
    detail = "nabídka propadla: %s; válka po tahu 14: %s; ztráty tahu 14: %s; ústup ani příměří: %s" % (
        "ano" if exp else "ne", "trvá" if R[14]["wars"] else "skončila",
        ("A power %.1f→%.1f, B power %.1f→%.1f" % (loss14[0]["outputs"]["A"]["power_pred"], loss14[0]["outputs"]["A"]["power_po"],
                                                   loss14[0]["outputs"]["B"]["power_pred"], loss14[0]["outputs"]["B"]["power_po"])) if loss14 else "žádné",
        "ne" if not rules(14, "3.3a konec valky") else "ano")
    out.append(("tah 14: A neodpoví, nabídka propadne bez následku, válka trvá", ok, detail))
    end = rules(15, "3.3a konec valky")
    o = end[0]["outputs"] if end else {}
    ratio = (o["vliv_po"] / o["vliv_pred"]) if end and o.get("vliv_pred") else None
    ok = bool(end) and o.get("jak") == "ustup" and o.get("porazeny") == "A" and ratio is not None \
        and abs(ratio - 0.7) < 1e-6 and not rules(15, "3.3a valka") and not R[15]["wars"]
    out.append(("tah 15: A retreat, vliv A −30 %, válka končí okamžitě", ok,
                "%s, ustoupil %s; součet vlivu A %s → %s (poměr %s); ztráty tahu 15: %s; válka po tahu 15: %s" % (
                    o.get("jak", "-"), o.get("porazeny", "-"), o.get("vliv_pred"), o.get("vliv_po"),
                    ("%.3f" % ratio) if ratio is not None else "-", "ano" if rules(15, "3.3a valka") else "žádné",
                    "trvá" if R[15]["wars"] else "skončila")))
    return out


def kriteria_k(res) -> bool:
    print("KONTROLNI SEZNAM scenare (k)")
    print("-" * 78)
    ok = True
    for bod, passed, detail in analyza_k(res):
        ok &= passed
        print("  [%s] %s: %s" % ("OK " if passed else "NE ", bod, detail))
    val_ok = not res["errors"]
    ok &= val_ok
    print("  [%s] validate bez chyb" % ("OK " if val_ok else "NE "))
    for t, errs in res["errors"][:5]:
        print("        tah %d: %s" % (t, errs[0]))
    return bool(ok)


def scenario_v(turn: int, state) -> list[dict]:
    """(v) v1.11, A jako rozumna vlada: tah 1 smlouva ropa 6 za 0.85 s N3, tah 2 obili 4 za 0.85
    s N1, tah 3 pakt s N3, dal nic noveho; nabidky NPC neprijima; domaci invest_industry jen pri
    wealth > 60, nejvys jednou za den. B: pakty N5 a N1 v tahu 1, N7 a N15 v tahu 4, od tahu 3
    domaci arm pri wealth > 60, pujcky a nabidky jako ve (b)."""
    acts: list[dict] = []
    if turn == 1:
        acts += [{"player": "A", "type": "trade_offer", "target": "N3", "res": "oil", "qty": 6, "price_per_unit": 0.85},
                 {"player": "B", "type": "protect", "target": "N5"},
                 {"player": "B", "type": "protect", "target": "N1"}]
    if turn == 2:
        acts.append({"player": "A", "type": "trade_offer", "target": "N1", "res": "grain", "qty": 4, "price_per_unit": 0.85})
    if turn == 3:
        acts.append({"player": "A", "type": "protect", "target": "N3"})
    if turn == 4:
        acts += [{"player": "B", "type": "protect", "target": "N7"},
                 {"player": "B", "type": "protect", "target": "N15"}]
    den = engine.day_of(turn)
    if float(state["players"]["A"]["wealth"]) > 60 and _v_invest_day.get("A") != den:
        _v_invest_day["A"] = den
        acts.append({"player": "A", "type": "invest_industry", "slot": "domestic"})
    if turn >= 3 and float(state["players"]["B"]["wealth"]) > 60:
        acts.append({"player": "B", "type": "arm", "amount": 16, "slot": "domestic"})
    seekers = _loan_seekers(state)
    if seekers and _foreign(acts, "B") < engine.ACTION_LIMIT["B"] and float(state["players"]["B"]["wealth"]) >= 12:
        acts.append({"player": "B", "type": "loan", "target": seekers[(turn + 1) % len(seekers)], "amount": 10})
    _accept_offers(state, acts, only=("B",))
    return acts


_v_invest_day: dict = {}


SCENARE = {
    "0": (scenario_0, "nikdo netahne"),
    "a": (scenario_a, "scenar ze zadani (A pujcuje N6 od tahu 8, B chrani N7)"),
    "b": (scenario_b, "realisticke pujcovani (jen kdyz NPC zada, max 1 na hrace a tah)"),
    "v": (scenario_v, "v1.11: A jako v ostrem behu, domaci akce, goods jako kapital"),
    "k": (scenario_k, "v1.10: soutez o cil, jeden pakt, valka hracu (14 tahu)"),
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


def _trade_split(state, applied):
    """v1.9: objem automatickeho trhu celkem a s hracem jako stranou; obchod clenu Unie
    mezi sebou (vnitrni trh v trzni cene) a s necleny (automaticky, cileny, obchod Unie)."""
    members = set(state["players"]["C"].get("members") or [])
    out = {"auto": 0.0, "auto_hraci": 0.0, "unie_vnitrni": 0.0, "unie_s_necleny": 0.0}
    for a in applied:
        rule, inp, o = a["rule"], a["inputs"], a["outputs"]
        if rule == "4.1a automaticky trh":
            v = float(o["objem"])
            out["auto"] += v
            if inp["prodejce"] in ("A", "B") or inp["kupec"] in ("A", "B"):
                out["auto_hraci"] += v
            if (inp["prodejce"] in members) != (inp["kupec"] in members):
                out["unie_s_necleny"] += v
        elif rule == "4.1 cileny obchod":
            if (inp["prodejce"] in members) != (inp["kupec"] in members):
                out["unie_s_necleny"] += float(o["objem"])
        elif rule == "7.2 obchod Unie za cleny":
            out["unie_s_necleny"] += float(o["objem"])
        elif rule == "7.2 vnitrni trh Unie":
            out["unie_vnitrni"] += float(o.get("hodnota", 0.0))
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
            "split": _trade_split(new_state, applied),
            # v1.10: valky, pakty, sila, udalosti a posledni zaznam soukromeho logu
            "wars": [dict(w) for w in new_state.get("wars", [])],
            "protect_n": {nid: [d["owner"] for d in new_state["deals"] if d["type"] == "protect" and d["target"] == nid]
                          for nid in new_state["npc"]},
            "power": {p: float(new_state["players"][p]["power"]) for p in ("A", "B")},
            "influence": {p: {nid: float(x["influence"].get(p, 0.0)) for nid, x in new_state["npc"].items()}
                          for p in ("A", "B")},
            "events": events if keep_applied else None,
            "private_log_last": {p: (new_state.get("private_log", {}).get(p) or [{}])[-1].get("reason", "-")
                                 for p in ("A", "B")},
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
    ap.add_argument("--scenar", choices=["0", "a", "b", "k", "vse"], default="vse")
    args = ap.parse_args()
    klice = ["0", "a", "b", "k"] if args.scenar == "vse" else [args.scenar]

    vysledek = True
    for k in klice:
        fn, popis = SCENARE[k]
        print("=" * 78)
        print("SCENAR (%s): %s" % (k, popis))
        print("=" * 78)
        if k == "k":
            res = run(TURNS_K, fn, keep_applied=True)
            ok = kriteria_k(res)
        else:
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

"""engine.py

Deterministicka cast sveta Ardan. Vykonava docs/pravidla.md 1:1.
Model sem nevstupuje: veskera aritmetika je tady, rozhodci jen preklada
tahy na akce a pise Zpravy (pravidla cast 9).

Poradi prepoctu podle BUILD.md cast 2:
    akce hracu -> 4.1 zdroje a obchod -> 4.2 rust -> 4.3 bida -> 4.5 splatky
    -> 3.3 invaze -> 4.4 vliv a sfery -> 5 Minsky -> 7 Unie -> 8 metriky

Kazdy krok zapisuje do snapshot.applied_rules zaznam {rule, inputs, outputs}.
Nahoda vyhradne z random.Random(rng_seed + turn).

Schemata dohodnuta v docs/OPEN_QUESTIONS.md (oddil B):

    deals[]      {"id":"d1","type":"trade","owner":"A","target":"N6",
                  "res":"grain","qty":3,"price":0.8,
                  "direction":"npc_sells"|"npc_buys","since":7}
                 {"id":"d2","type":"protect","owner":"B","target":"N7","since":5}
                 {"id":"d3","type":"pressure","owner":"A","target":"N3",
                  "demand":"text","since":9}

    invasions[]  {"id":"i1","attacker":"A","target":"N6","turns":3,
                  "last_turn":10,"since":8}

    minsky.defaults[]  {"turn":11,"npc":"N6","creditor":"A"}

    refugees[]   {"target":"N1","turns_left":3}   (pravidlo 3.3, uprchlici)
"""

from __future__ import annotations

import json
import random
from copy import deepcopy

RESOURCES = ("oil", "grain", "metal", "orit")
BASE_RESOURCES = ("oil", "grain", "metal")
BASE_PRICE = {"oil": 1.0, "grain": 0.8, "metal": 1.2}

# Faze, ve kterych orit uz existuje (displacement a dal).
ORIT_PHASES = ("displacement", "boom", "euphoria", "overtrading",
               "distress", "panic", "crash", "depression", "recovery")

PHASE_ORDER = ("pre", "displacement", "boom", "euphoria", "overtrading",
               "distress", "panic", "crash", "depression", "recovery")


# --------------------------------------------------------------------------
# pomocne funkce
# --------------------------------------------------------------------------

def day_of(turn: int) -> int:
    """Den hry. Tah 7 vychazi na den 3, tahy 88 az 90 na den 30."""
    return ((turn - 1) // 3) + 1


def slot_of(turn: int) -> int:
    """1 rano, 2 poledne, 3 vecer."""
    return ((turn - 1) % 3) + 1


def npc_ids(state) -> list[str]:
    return list(state["npc"].keys())


def world_ids(state) -> list[str]:
    """14 statu, ktere vstupuji do indexu prosperity (pravidla cast 8)."""
    return ["A", "B"] + npc_ids(state)


def ent(state, sid: str) -> dict:
    if sid in ("A", "B", "C"):
        return state["players"][sid]
    return state["npc"][sid]


def is_npc(sid: str) -> bool:
    return sid not in ("A", "B", "C")


def is_fallen(state, sid: str) -> bool:
    return is_npc(sid) and state["npc"][sid].get("kind") == "fallen"


def market_price(state, res: str) -> float:
    if res == "orit":
        p = state["minsky"].get("orit_price")
        return float(p) if p is not None else float(state["minsky"]["orit_price_start"])
    return BASE_PRICE[res]


def eff_prod(e: dict, res: str) -> float:
    """Efektivni produkce: prod x (1 + tech/20) x pop/100 (pravidla 4.1 a 10.2)."""
    base = float(e.get("prod", {}).get(res, 0.0))
    tech = float(e.get("tech") or 0.0)
    pop = float(e.get("pop") or 0.0)
    return base * (1.0 + tech / 20.0) * (pop / 100.0)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def normalize(state) -> None:
    """Doplni pole, ktera pravidla predpokladaji, ale state.json je nema.

    Viz docs/OPEN_QUESTIONS.md A1 (hraci bez poverty_streak a coups),
    A2 (fund jako zrcadlo wealth) a doprovodna evidence pro pravidla 7.1 a 7a.
    """
    for pid in ("A", "B"):
        p = state["players"][pid]
        p.setdefault("poverty_streak", 0)
        p.setdefault("coups", 0)
        p.setdefault("occupied", [])
        p.setdefault("paper_wealth", 0.0)
    for i, n in state["npc"].items():
        n.setdefault("poverty_streak", 0)
        n.setdefault("coups", 0)
        n.setdefault("paper_wealth", 0.0)
        # Predkrizove maximum wealth pro pravidlo 7.1 (ztrata >= 30 %).
        n.setdefault("wealth_peak", float(n["wealth"]))
    state.setdefault("deals", [])
    state.setdefault("invasions", [])
    state.setdefault("refugees", [])
    state.setdefault("messages_pending", [])
    state.setdefault("news", [])
    state.setdefault("log", [])
    state["minsky"].setdefault("defaults", [])
    state["minsky"].setdefault("phase_log", [])
    state["minsky"].setdefault("fragility", 0.0)
    # Ktereho padleho rise se behem boom az panic nekdo dotkl (pravidlo 7a).
    state["minsky"].setdefault("fallen_touched", [])
    state["minsky"].setdefault("migration_ledger", [])
    state["minsky"].setdefault("next_deal_id", 1)
    state["minsky"].setdefault("next_invasion_id", 1)


class Trace:
    """Sberac zaznamu do snapshot.applied_rules."""

    def __init__(self):
        self.items: list[dict] = []

    def add(self, rule: str, inputs, outputs) -> None:
        self.items.append({"rule": rule, "inputs": inputs, "outputs": outputs})

    def touched_pop(self) -> float:
        """Soucet zmen pop, ktere si pravidla naparovala. Cte validate.py (C2)."""
        total = 0.0
        for it in self.items:
            out = it.get("outputs") or {}
            if isinstance(out, dict) and "pop_delta" in out:
                total += float(out["pop_delta"])
        return total


# --------------------------------------------------------------------------
# nacteni
# --------------------------------------------------------------------------

def load_world(state_path, npc_path):
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
    with open(npc_path, encoding="utf-8") as f:
        npcdata = json.load(f)
    normalize(state)
    return state, npcdata


def neighbours(npcdata, sid: str) -> list[str]:
    return list(npcdata.get("adjacency", {}).get(sid, []))


# --------------------------------------------------------------------------
# akce hracu
# --------------------------------------------------------------------------

ACTION_LIMIT = {"A": 2, "B": 2, "C": 3}

COST = {
    "loan": None,          # promenna, plati se amount
    "invest_tech": 8.0,
    "invest_law": 6.0,
    "explore": 5.0,
    "arm": 8.0,
}


def _new_deal_id(state) -> str:
    n = state["minsky"]["next_deal_id"]
    state["minsky"]["next_deal_id"] = n + 1
    return f"d{n}"


def _new_invasion_id(state) -> str:
    n = state["minsky"]["next_invasion_id"]
    state["minsky"]["next_invasion_id"] = n + 1
    return f"i{n}"


def _active_deal(state, owner, target, dtype):
    for d in state["deals"]:
        if d["owner"] == owner and d["target"] == target and d["type"] == dtype:
            return d
    return None


def _npc_balance_for_trade(state, nid: str, res: str) -> float:
    """Bilance NPC u suroviny pred obchodem. Urcuje smer obchodu (C3)."""
    e = state["npc"][nid]
    return eff_prod(e, res) - float(e.get("need", {}).get(res, 0.0))


def apply_actions(state, npcdata, actions, rng, trace: Trace) -> list[dict]:
    """Provede akce hracu. Vraci seznam udalosti pro rozhodciho.

    `actions` je seznam {"player": "A", "type": "loan", ...}, uz overeny
    rozhodcim. Engine presto kontroluje tvrde podminky, protoze aritmetika
    a prahy patri sem (pravidla cast 9).
    """
    events: list[dict] = []
    counts: dict[str, int] = {}

    for act in actions:
        pid = act.get("player")
        atype = act.get("type")
        if pid not in ("A", "B", "C"):
            continue
        counts[pid] = counts.get(pid, 0) + 1
        if counts[pid] > ACTION_LIMIT[pid]:
            events.append({"kind": "action_over_limit", "player": pid, "type": atype})
            continue
        player = state["players"][pid]
        target = act.get("target")

        # --- trade_offer -------------------------------------------------
        if atype == "trade_offer":
            res = act.get("res")
            qty = float(act.get("qty", 0))
            price = float(act.get("price_per_unit", 0))
            if target not in state["npc"] or res not in RESOURCES or qty <= 0:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "neznamy cil nebo surovina"})
                continue
            mp = market_price(state, res)
            lo, hi = 0.7 * mp, 1.5 * mp
            if is_fallen(state, target):
                lo = 1.3 * mp  # pravidlo 7a: obchoduji jen za >= 1.3x
            if not (lo <= price <= hi):
                events.append({"kind": "trade_rejected", "player": pid, "target": target,
                               "res": res, "reason": "cena mimo pasmo"})
                continue
            bal = _npc_balance_for_trade(state, target, res)
            if bal > 0:
                direction = "npc_sells"
            elif bal < 0:
                direction = "npc_buys"
            else:
                events.append({"kind": "trade_rejected", "player": pid, "target": target,
                               "res": res, "reason": "NPC nema prebytek ani deficit"})
                continue
            qty = min(qty, abs(bal))
            deal = {"id": _new_deal_id(state), "type": "trade", "owner": pid,
                    "target": target, "res": res, "qty": round(qty, 3),
                    "price": price, "direction": direction,
                    "since": state["meta"]["turn"]}
            state["deals"].append(deal)
            events.append({"kind": "trade_opened", "deal": deal})
            trace.add("3.2 trade_offer", {"player": pid, "target": target, "res": res,
                                          "qty": qty, "price": price},
                      {"deal_id": deal["id"], "direction": direction})

        # --- loan ---------------------------------------------------------
        elif atype == "loan":
            amount = float(act.get("amount", 0))
            if target == "C" or target not in state["npc"] or amount <= 0:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "neplatny cil pujcky"})
                continue
            if is_fallen(state, target):
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "padla rise nepremia pujcku"})
                continue
            if float(player["wealth"]) < amount:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "nedostatek wealth"})
                continue
            n = state["npc"][target]
            player["wealth"] = float(player["wealth"]) - amount
            n["wealth"] = float(n["wealth"]) + amount
            owed = amount * 1.2
            n["debt"][pid] = float(n["debt"].get(pid, 0.0)) + owed
            # pravidlo 4.4: vliv jednorazove o debt/20
            gain = owed / 20.0
            if pid in ("A", "B"):
                if is_fallen(state, target):
                    gain *= 0.1
                n["influence"][pid] = float(n["influence"].get(pid, 0.0)) + gain
            events.append({"kind": "loan_given", "player": pid, "target": target,
                           "amount": amount, "debt": n["debt"][pid]})
            trace.add("3.2 loan / 4.4 vliv z pohledavky",
                      {"player": pid, "target": target, "amount": amount},
                      {"debt": n["debt"][pid], "influence_gain": gain})

        # --- pressure ------------------------------------------------------
        elif atype == "pressure":
            if target not in state["npc"]:
                continue
            if _active_deal(state, pid, target, "pressure"):
                continue
            # sankce prerusi obchody hrace s NPC
            removed = [d["id"] for d in state["deals"]
                       if d["type"] == "trade" and d["owner"] == pid and d["target"] == target]
            state["deals"] = [d for d in state["deals"] if d["id"] not in removed]
            deal = {"id": _new_deal_id(state), "type": "pressure", "owner": pid,
                    "target": target, "demand": act.get("demand", ""),
                    "since": state["meta"]["turn"]}
            state["deals"].append(deal)
            events.append({"kind": "pressure_started", "player": pid, "target": target,
                           "cancelled_trades": removed})
            trace.add("3.2 pressure", {"player": pid, "target": target},
                      {"deal_id": deal["id"], "cancelled": removed})
            _mark_fallen_touched(state, target)

        # --- protect --------------------------------------------------------
        elif atype == "protect":
            if target not in state["npc"]:
                continue
            if is_fallen(state, target):
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "padla rise nepremia pakt"})
                continue
            if _active_deal(state, pid, target, "protect"):
                continue
            deal = {"id": _new_deal_id(state), "type": "protect", "owner": pid,
                    "target": target, "since": state["meta"]["turn"]}
            state["deals"].append(deal)
            events.append({"kind": "protect_started", "player": pid, "target": target})
            trace.add("3.2 protect", {"player": pid, "target": target},
                      {"deal_id": deal["id"]})

        # --- invade ----------------------------------------------------------
        elif atype == "invade":
            _register_invasion(state, npcdata, pid, target, events, trace)

        # --- invest_tech / invest_law ----------------------------------------
        elif atype in ("invest_tech", "invest_law"):
            field = "tech" if atype == "invest_tech" else "law"
            cost = COST[atype]
            tgt = target or pid
            if tgt == pid:
                e = player
            elif tgt in state["npc"]:
                e = state["npc"][tgt]
                st = e.get("status")
                allowed_sphere = st in (f"sphere_{pid}", "union") if pid in ("A", "B") else True
                if pid == "C":
                    allowed_sphere = tgt in state["players"]["C"]["members"] or \
                                     tgt in state["players"]["C"]["candidates"]
                    cost = cost / 2.0  # pravidlo 7.2: polovicni cena
                if not allowed_sphere:
                    events.append({"kind": "action_invalid", "player": pid, "type": atype,
                                   "reason": "cil mimo sferu nebo Unii"})
                    continue
            else:
                continue
            if float(player["wealth"]) < cost:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "nedostatek wealth"})
                continue
            player["wealth"] = float(player["wealth"]) - cost
            before = float(e.get(field) or 0.0)
            e[field] = clamp(before + 0.3, 0.0, 10.0)
            events.append({"kind": f"{atype}_done", "player": pid, "target": tgt,
                           field: e[field]})
            trace.add(f"3.2 {atype}", {"player": pid, "target": tgt, "cost": cost},
                      {field: e[field], "from": before})

        # --- explore -----------------------------------------------------------
        elif atype == "explore":
            if float(player["wealth"]) < COST["explore"]:
                continue
            player["wealth"] = float(player["wealth"]) - COST["explore"]
            hit = rng.random() < 0.15
            if hit:
                player.setdefault("prod", {})
                player["prod"]["orit"] = float(player["prod"].get("orit", 0.0)) + 2.0
            events.append({"kind": "explore", "player": pid, "found": hit})
            trace.add("3.2 explore", {"player": pid, "cost": COST["explore"]},
                      {"found": hit})

        # --- arm ---------------------------------------------------------------
        elif atype == "arm":
            if float(player["wealth"]) < COST["arm"]:
                continue
            player["wealth"] = float(player["wealth"]) - COST["arm"]
            player["power"] = float(player["power"]) + 5.0
            events.append({"kind": "arm", "player": pid, "power": player["power"]})
            trace.add("3.2 arm", {"player": pid}, {"power": player["power"]})

        # --- cancel -------------------------------------------------------------
        elif atype == "cancel":
            did = act.get("deal_id")
            before = len(state["deals"])
            state["deals"] = [d for d in state["deals"]
                              if not (d["id"] == did and d["owner"] in (pid, "C"))]
            inv_before = len(state["invasions"])
            state["invasions"] = [v for v in state["invasions"]
                                  if not (v["id"] == did and v["attacker"] == pid)]
            if len(state["invasions"]) < inv_before:
                # pravidlo 10.4: kdo ustoupi, ztraci u nej veskery influence
                tgt = act.get("target")
                if tgt in state["npc"] and pid in ("A", "B"):
                    state["npc"][tgt]["influence"][pid] = 0.0
            events.append({"kind": "cancel", "player": pid, "deal_id": did,
                           "removed": before - len(state["deals"]) +
                                      inv_before - len(state["invasions"])})
            trace.add("3.2 cancel / 10.4 ustup", {"player": pid, "deal_id": did},
                      {"deals_left": len(state["deals"])})

        # --- message --------------------------------------------------------------
        elif atype == "message":
            state["messages_pending"].append({
                "from": pid, "to": act.get("target"), "text": act.get("text", ""),
                "turn": state["meta"]["turn"]})
            events.append({"kind": "message", "from": pid, "to": act.get("target")})

        # --- admit (jen Unie) -------------------------------------------------------
        elif atype == "admit":
            if pid != "C" or not state["players"]["C"]["active"]:
                continue
            _union_admit(state, target, events, trace)

        # --- union_fund -------------------------------------------------------------
        elif atype == "union_fund":
            if pid != "C" or not state["players"]["C"]["active"]:
                continue
            amount = float(act.get("amount", 0))
            C = state["players"]["C"]
            if target not in state["npc"] or amount <= 0 or float(C["wealth"]) < amount:
                continue
            if target not in C["members"] and target not in C["candidates"]:
                continue
            C["wealth"] = float(C["wealth"]) - amount
            state["npc"][target]["wealth"] = float(state["npc"][target]["wealth"]) + amount
            events.append({"kind": "union_fund", "target": target, "amount": amount})
            trace.add("7.2 union_fund", {"target": target, "amount": amount},
                      {"fund": C["wealth"]})

    return events


def _mark_fallen_touched(state, target) -> None:
    """Pravidlo 7a: kdo padlou risi behem boomu tlacil, nezisak ji do Unie."""
    if is_fallen(state, target) and state["phase"] in ("boom", "euphoria",
                                                       "overtrading", "distress", "panic"):
        if target not in state["minsky"]["fallen_touched"]:
            state["minsky"]["fallen_touched"].append(target)


def _register_invasion(state, npcdata, pid, target, events, trace) -> None:
    """Pravidlo 3.3. Podminky, valka s ochrancem, pocitadlo tahu."""
    if target not in state["npc"] or pid == "C":
        return
    n = state["npc"][target]
    player = state["players"][pid]
    crash_discount = state["phase"] == "crash"
    cost_w = 5.0 if crash_discount else 10.0
    cost_p = 3.0 if crash_discount else 5.0
    if float(player["wealth"]) < cost_w or float(player["power"]) < cost_p:
        events.append({"kind": "action_invalid", "player": pid, "type": "invade",
                       "reason": "nedostatek zdroju na invazi"})
        return
    ratio = 4.0 if n.get("kind") == "fallen" else 2.0
    if float(player["power"]) < ratio * float(n["power"]):
        events.append({"kind": "invade_blocked", "player": pid, "target": target,
                       "reason": f"power pod {ratio}x cile"})
        return
    # pakt druheho hrace => valka, ne invaze
    other = "B" if pid == "A" else "A"
    if _active_deal(state, other, target, "protect"):
        player["power"] = float(player["power"]) - 10.0
        state["players"][other]["power"] = float(state["players"][other]["power"]) - 10.0
        n["wealth"] = max(0.0, float(n["wealth"]) - 5.0)
        events.append({"kind": "war", "between": [pid, other], "over": target})
        trace.add("3.3 valka hracu", {"attacker": pid, "defender": other, "npc": target},
                  {"power_loss_each": 10.0, "npc_wealth": n["wealth"]})
        return
    # Unie brani cleny (pravidlo 7.2)
    C = state["players"]["C"]
    if C["active"] and target in C["members"]:
        events.append({"kind": "invade_blocked", "player": pid, "target": target,
                       "reason": "clen Unie, nutna valka s Unii"})
        return
    player["wealth"] = float(player["wealth"]) - cost_w
    player["power"] = float(player["power"]) - cost_p
    turn = state["meta"]["turn"]
    inv = None
    for v in state["invasions"]:
        if v["attacker"] == pid and v["target"] == target:
            inv = v
            break
    if inv is None:
        inv = {"id": _new_invasion_id(state), "attacker": pid, "target": target,
               "turns": 0, "last_turn": None, "since": turn}
        state["invasions"].append(inv)
    if inv["last_turn"] is not None and inv["last_turn"] != turn - 1:
        inv["turns"] = 0  # preruseni, start znovu
    inv["turns"] += 1
    inv["last_turn"] = turn
    events.append({"kind": "invade_progress", "player": pid, "target": target,
                   "turns": inv["turns"]})
    trace.add("3.3 invaze", {"attacker": pid, "target": target},
              {"turns": inv["turns"], "cost_wealth": cost_w, "cost_power": cost_p})
    _mark_fallen_touched(state, target)


# --------------------------------------------------------------------------
# trvale efekty paktu a sankci (pravidla 3.2)
# --------------------------------------------------------------------------

def upkeep_deals(state, trace: Trace, events: list) -> None:
    for d in list(state["deals"]):
        owner = d["owner"]
        tgt = d["target"]
        if tgt not in state["npc"]:
            continue
        n = state["npc"][tgt]
        player = state["players"].get(owner)
        if d["type"] == "protect":
            if player is None:
                continue
            player["power"] = float(player["power"]) - 2.0
            n["power"] = float(n["power"]) + 2.0
            if owner in ("A", "B"):
                mult = 0.1 if n.get("kind") == "fallen" else 1.0
                n["influence"][owner] = float(n["influence"].get(owner, 0.0)) + 2.0 * mult
            n["law"] = clamp(float(n["law"]) - 0.2, 0.0, 10.0)
            trace.add("3.2 protect upkeep", {"owner": owner, "target": tgt},
                      {"npc_power": n["power"], "npc_law": n["law"]})
        elif d["type"] == "pressure":
            if player is None:
                continue
            player["wealth"] = max(0.0, float(player["wealth"]) - 1.0)
            n["wealth"] = max(0.0, float(n["wealth"]) - 3.0)
            other = "B" if owner == "A" else "A"
            if owner in ("A", "B"):
                mult = 0.1 if n.get("kind") == "fallen" else 1.0
                n["influence"][other] = float(n["influence"].get(other, 0.0)) + 1.0 * mult
            trace.add("3.2 pressure upkeep", {"owner": owner, "target": tgt},
                      {"npc_wealth": n["wealth"], f"influence_{other}": n["influence"][other]})


# --------------------------------------------------------------------------
# 4.1 zdroje a obchod
# --------------------------------------------------------------------------

def step_resources(state, trace: Trace, events: list) -> dict:
    """Bilance, obchod, deficit. Vraci mapu deficitu obili pro pravidlo 4.3."""
    turn = state["meta"]["turn"]
    ids = world_ids(state)
    imports = {i: {r: 0.0 for r in RESOURCES} for i in ids}
    exports = {i: {r: 0.0 for r in RESOURCES} for i in ids}
    trade_volume = 0.0
    trade_volume_weighted = 0.0   # metrika A, orit 2x (pravidlo 10.5)
    volume_by_player = {"A": 0.0, "B": 0.0, "C": 0.0}
    volume_by_npc = {i: 0.0 for i in npc_ids(state)}

    # pravidlo 5, faze crash: obchod sveta x0.5 po 6 tahu
    crash_turn = state["minsky"].get("crash_turn")
    trade_mult = 1.0
    if crash_turn is not None and state["phase"] in ("crash",) and turn - crash_turn < 6:
        trade_mult = 0.5

    for d in state["deals"]:
        if d["type"] != "trade":
            continue
        owner, tgt, res = d["owner"], d["target"], d["res"]
        qty = float(d["qty"]) * trade_mult
        price = float(d["price"])
        if tgt not in state["npc"]:
            continue
        if d["direction"] == "npc_sells":
            seller, buyer = tgt, owner
        else:
            seller, buyer = owner, tgt
        if seller in imports:
            exports[seller][res] += qty
        if buyer in imports:
            imports[buyer][res] += qty
        value = qty * price
        se = ent(state, seller)
        be = ent(state, buyer)
        se["wealth"] = float(se["wealth"]) + value
        be["wealth"] = float(be["wealth"]) - value
        trade_volume += value
        trade_volume_weighted += value * (2.0 if res == "orit" else 1.0)
        if owner in volume_by_player:
            volume_by_player[owner] += value * (2.0 if res == "orit" else 1.0)
        if tgt in volume_by_npc:
            volume_by_npc[tgt] += value * (2.0 if res == "orit" else 1.0)

    # 7.2 vnitrni trh Unie: prebytek clena kryje deficit jineho clena zdarma
    C = state["players"]["C"]
    if C["active"] and C["members"]:
        for res in RESOURCES:
            surplus, deficit = [], []
            for m in C["members"]:
                e = state["npc"][m]
                bal = eff_prod(e, res) - float(e.get("need", {}).get(res, 0.0)) \
                      + imports[m][res] - exports[m][res]
                if bal > 0:
                    surplus.append([m, bal])
                elif bal < 0:
                    deficit.append([m, -bal])
            for dm, dneed in deficit:
                for sm in surplus:
                    if dneed <= 0:
                        break
                    take = min(sm[1], dneed)
                    if take <= 0:
                        continue
                    imports[dm][res] += take
                    exports[sm[0]][res] += take
                    sm[1] -= take
                    dneed -= take
            trace.add("7.2 vnitrni trh Unie", {"res": res, "members": list(C["members"])},
                      {"pokryto": True})

    grain_deficit = {}
    for i in ids:
        e = ent(state, i)
        total_deficit = 0.0
        for res in RESOURCES:
            if res == "orit" and state["phase"] not in ORIT_PHASES:
                continue
            if res == "orit" and is_fallen(state, i):
                continue  # pravidlo 7a: padle rise orit nepotrebuji
            bal = eff_prod(e, res) - float(e.get("need", {}).get(res, 0.0)) \
                  + imports[i][res] - exports[i][res]
            if res == "grain":
                grain_deficit[i] = max(0.0, -bal)
            if bal < 0:
                total_deficit += -bal
            if res == "orit":
                # spotrebovany orit: tech +0.1 a power +1 za jednotku (pravidlo 5).
                # Spotrebuje se tolik, kolik je potreba a zaroven k dispozici,
                # tedy i kdyz je bilance zaporna a stat pokryje jen cast.
                available = eff_prod(e, "orit") + imports[i]["orit"] - exports[i]["orit"]
                used = max(0.0, min(float(e.get("need", {}).get("orit", 0.0)), available))
                if used > 0:
                    e["tech"] = clamp(float(e["tech"]) + 0.1 * used, 0.0, 10.0)
                    e["power"] = float(e["power"]) + 1.0 * used
        if total_deficit > 0:
            e["wealth"] = max(0.0, float(e["wealth"]) - total_deficit)
        trace.add("4.1 zdroje a obchod", {"stat": i, "imports": imports[i],
                                          "exports": exports[i]},
                  {"deficit": round(total_deficit, 3), "wealth": round(float(e["wealth"]), 3)})

    state["_trade"] = {"volume": trade_volume, "weighted": trade_volume_weighted,
                       "by_player": volume_by_player, "by_npc": volume_by_npc}
    return grain_deficit


# --------------------------------------------------------------------------
# 4.2 rust, 4.3 bida
# --------------------------------------------------------------------------

def in_poverty(state, sid: str, grain_deficit: dict) -> bool:
    e = ent(state, sid)
    return float(e["wealth"]) < 15.0 or grain_deficit.get(sid, 0.0) >= 3.0


def step_growth(state, grain_deficit, trace: Trace) -> None:
    for i in world_ids(state):
        e = ent(state, i)
        poor = in_poverty(state, i, grain_deficit)
        law = float(e["law"] or 0.0)
        tech = float(e["tech"] or 0.0)
        w0 = float(e["wealth"])
        growth = round(0.02 * w0 * (law / 5.0) * (1.0 + tech / 10.0))
        e["wealth"] = w0 + growth
        if poor:
            e["tech"] = clamp(tech - 0.15, 0.0, 10.0)
        elif law >= 5.0:
            e["tech"] = clamp(tech + 0.15, 0.0, 10.0)
        if is_npc(i):
            total_debt = sum(float(v) for v in e["debt"].values())
            if total_debt > 0.5 * max(1.0, float(e["wealth"])):
                e["law"] = clamp(float(e["law"]) - 0.1, 0.0, 10.0)
        if is_npc(i):
            # predkrizove maximum pro pravidlo 7.1 (ztrata >= 30 % => zakladatel Unie)
            e["wealth_peak"] = max(float(e.get("wealth_peak", 0.0)), float(e["wealth"]))
        trace.add("4.2 rust", {"stat": i, "law": law, "tech": tech, "wealth_before": w0},
                  {"growth": growth, "wealth": e["wealth"], "tech_after": e["tech"]})


def step_poverty(state, npcdata, grain_deficit, trace: Trace, events: list) -> None:
    # Seznam statu v bide podle 4.3. Cte ho metrika n_bida (pravidlo 8),
    # aby index pouzival tutez definici jako efekty bidy, vcetne deficitu obili.
    poverty_set = []
    for i in world_ids(state):
        e = ent(state, i)
        poor = in_poverty(state, i, grain_deficit)
        if poor:
            poverty_set.append(i)
        if not poor:
            e["poverty_streak"] = 0
            continue
        e["poverty_streak"] = int(e.get("poverty_streak", 0)) + 1
        pop_before = float(e["pop"])
        e["pop"] = max(0.0, pop_before - 3.0)
        e["power"] = max(0.0, float(e["power"]) - 1.0)
        e["wealth"] = max(0.0, float(e["wealth"]))
        events.append({"kind": "poverty", "stat": i, "streak": e["poverty_streak"]})
        trace.add("4.3 bida", {"stat": i, "streak": e["poverty_streak"]},
                  {"pop": e["pop"], "power": e["power"],
                   "pop_delta": e["pop"] - pop_before})
        # pad vlady: jen u NPC (viz OPEN_QUESTIONS A1)
        if is_npc(i) and (e["poverty_streak"] >= 3 or float(e["wealth"]) <= 0.0):
            state["deals"] = [d for d in state["deals"] if d["target"] != i]
            e["influence"]["A"] = 0.0
            e["influence"]["B"] = 0.0
            e["coups"] = int(e.get("coups", 0)) + 1
            e["status"] = "independent"
            e["poverty_streak"] = 0
            events.append({"kind": "coup", "stat": i, "coups": e["coups"]})
            trace.add("4.3 pad vlady", {"stat": i}, {"coups": e["coups"],
                                                     "status": "independent"})
    state["_poverty"] = poverty_set


# --------------------------------------------------------------------------
# 4.5 splatky
# --------------------------------------------------------------------------

def step_repayments(state, trace: Trace, events: list) -> None:
    turn = state["meta"]["turn"]
    phase = state["phase"]
    for i, n in state["npc"].items():
        total_debt = sum(float(v) for v in n["debt"].values())
        if total_debt <= 0:
            continue
        rollover = phase == "overtrading" and total_debt > 0.5 * max(1.0, float(n["wealth"]))
        if rollover:
            # Ponziho zona: splaci novym dluhem, dluh x1.15 (pravidlo 5)
            for cred in list(n["debt"].keys()):
                if float(n["debt"][cred]) > 0:
                    n["debt"][cred] = float(n["debt"][cred]) * 1.15
            events.append({"kind": "rollover", "npc": i,
                           "debt": sum(float(v) for v in n["debt"].values())})
            trace.add("5 overtrading rollover", {"npc": i},
                      {"debt": sum(float(v) for v in n["debt"].values())})
            continue
        paid_any = False
        for cred in list(n["debt"].keys()):
            owed = float(n["debt"][cred])
            if owed <= 0:
                continue
            due = 0.10 * owed
            capacity = max(0.0, float(n["wealth"]) - 10.0)
            pay = min(due, capacity)
            if phase == "distress":
                pay *= 0.5  # veritele dostavaji jen 50 % splatek
            if pay > 0:
                n["wealth"] = float(n["wealth"]) - pay
                n["debt"][cred] = owed - pay
                creditor = state["players"].get(cred)
                if creditor is not None:
                    creditor["wealth"] = float(creditor["wealth"]) + pay
                paid_any = True
            unpaid = due - pay
            if unpaid > 0:
                n["debt"][cred] = float(n["debt"][cred]) + unpaid * 1.1
            if pay <= 0:
                state["minsky"]["defaults"].append({"turn": turn, "npc": i, "creditor": cred})
                events.append({"kind": "default", "npc": i, "creditor": cred,
                               "debt": n["debt"][cred]})
        trace.add("4.5 splatky", {"npc": i, "wealth": n["wealth"]},
                  {"debt": {k: round(float(v), 3) for k, v in n["debt"].items()},
                   "paid_any": paid_any})


# --------------------------------------------------------------------------
# 3.3 dokonceni invazi
# --------------------------------------------------------------------------

def step_invasions(state, npcdata, trace: Trace, events: list) -> None:
    turn = state["meta"]["turn"]
    for inv in list(state["invasions"]):
        if inv["last_turn"] != turn:
            continue
        target = inv["target"]
        n = state["npc"].get(target)
        if n is None:
            continue
        need = 10 if n.get("kind") == "fallen" else 6
        if inv["turns"] < need:
            continue
        att = inv["attacker"]
        n["status"] = f"occupied_{att}"
        n["law"] = clamp(float(n["law"]) - 3.0, 0.0, 10.0)
        loss = 0.5 if n.get("kind") == "fallen" else 0.3  # 7a: pevnost, kapital odchazi
        n["wealth"] = float(n["wealth"]) * (1.0 - loss)
        pop_before = float(n["pop"])
        refugees = pop_before * 0.20
        n["pop"] = pop_before - refugees
        nb = [x for x in neighbours(npcdata, target) if x in state["npc"]]
        dest = nb[0] if nb else None
        if dest:
            state["npc"][dest]["pop"] = float(state["npc"][dest]["pop"]) + refugees
            state["refugees"].append({"target": dest, "turns_left": 3})
        state["players"][att].setdefault("occupied", [])
        if target not in state["players"][att]["occupied"]:
            state["players"][att]["occupied"].append(target)
        state["invasions"].remove(inv)
        events.append({"kind": "occupied", "attacker": att, "target": target,
                       "refugees_to": dest})
        trace.add("3.3 dobyti", {"attacker": att, "target": target, "turns": inv["turns"]},
                  {"status": n["status"], "wealth": n["wealth"],
                   "pop_delta": 0.0 if dest else -refugees,
                   "refugees": refugees, "refugees_to": dest})

    # uprchlicke naklady: cil dostava wealth -2 po 3 tahy
    for r in list(state["refugees"]):
        tgt = r["target"]
        if tgt in state["npc"]:
            state["npc"][tgt]["wealth"] = max(0.0, float(state["npc"][tgt]["wealth"]) - 2.0)
        r["turns_left"] -= 1
        if r["turns_left"] <= 0:
            state["refugees"].remove(r)

    # strach z agresora: -1 influence u vsech nezavislych NPC za kazde okupovane
    for pid in ("A", "B"):
        occ = len(state["players"][pid].get("occupied", []))
        if occ <= 0:
            continue
        for i, n in state["npc"].items():
            if n["status"] == "independent":
                n["influence"][pid] = max(0.0, float(n["influence"].get(pid, 0.0)) - 1.0 * occ)
        trace.add("3.3 strach z agresora", {"player": pid, "okupovanych": occ},
                  {"influence_penalty": occ})


# --------------------------------------------------------------------------
# 4.4 vliv a sfery
# --------------------------------------------------------------------------

def step_influence(state, trace: Trace, events: list) -> None:
    for i, n in state["npc"].items():
        mult = 0.1 if n.get("kind") == "fallen" else 1.0
        has_link = {"A": False, "B": False}
        for d in state["deals"]:
            if d["target"] != i or d["owner"] not in ("A", "B"):
                continue
            if d["type"] == "trade":
                n["influence"][d["owner"]] = float(n["influence"][d["owner"]]) + 1.0 * mult
                has_link[d["owner"]] = True
                if d["owner"] == "A":
                    n["law"] = min(8.0, float(n["law"]) + 0.1) if float(n["law"]) < 8.0 \
                        else float(n["law"])
            elif d["type"] == "protect":
                has_link[d["owner"]] = True
            elif d["type"] == "pressure":
                has_link[d["owner"]] = True
        for pid in ("A", "B"):
            if float(n["debt"].get(pid, 0.0)) > 0:
                has_link[pid] = True
            if not has_link[pid]:
                n["influence"][pid] = max(0.0, float(n["influence"][pid]) - 1.0)
        infA, infB = float(n["influence"]["A"]), float(n["influence"]["B"])
        if n["status"] in ("independent", "sphere_A", "sphere_B"):
            new_status = n["status"]
            if infA >= 10 and infA > infB + 3:
                new_status = "sphere_A"
            elif infB >= 10 and infB > infA + 3:
                new_status = "sphere_B"
            if new_status != n["status"]:
                n["status"] = new_status
                events.append({"kind": "sphere", "npc": i, "status": new_status})
        # 7.5 odchod clena do sfery velmoci
        C = state["players"]["C"]
        if C["active"] and i in C["members"]:
            for pid, val in (("A", infA), ("B", infB)):
                if val >= 15:
                    C["members"].remove(i)
                    n["status"] = f"sphere_{pid}"
                    events.append({"kind": "union_exit", "npc": i, "to": pid})
                    break
        trace.add("4.4 vliv", {"npc": i}, {"A": n["influence"]["A"], "B": n["influence"]["B"],
                                           "status": n["status"]})


# --------------------------------------------------------------------------
# 5 Minsky
# --------------------------------------------------------------------------

def _set_phase(state, new_phase, threshold, value, trace, events) -> None:
    old = state["phase"]
    state["phase"] = new_phase
    state["minsky"]["phase_log"].append({
        "turn": state["meta"]["turn"], "from": old, "to": new_phase,
        "threshold": threshold, "value": value})
    events.append({"kind": "phase", "from": old, "to": new_phase, "threshold": threshold})
    trace.add("5 zmena faze", {"from": old, "threshold": threshold, "value": value},
              {"to": new_phase})


def _default_turns(state) -> int:
    """Pocet tahu, ve kterych doslo aspon k jednomu nesplaceni (OPEN_QUESTIONS B1)."""
    return len({d["turn"] for d in state["minsky"]["defaults"]})


def step_minsky(state, npcdata, rng, trace: Trace, events: list) -> None:
    turn = state["meta"]["turn"]
    phase = state["phase"]
    m = state["minsky"]

    # --- prechody -----------------------------------------------------------
    if phase == "pre" and turn >= 7:
        _set_phase(state, "displacement", "tah 7", turn, trace, events)
        m["orit_price"] = float(m["orit_price_start"])
        for nid, amount in (("N6", 6.0), ("N3", 1.0), ("N8", 1.0), ("N9", 1.0)):
            if nid in state["npc"]:
                state["npc"][nid]["prod"]["orit"] = amount
        for i in world_ids(state):
            e = ent(state, i)
            if is_fallen(state, i):
                continue  # 7a: padle rise orit ignoruji
            e.setdefault("need", {})["orit"] = 2.0
            e.setdefault("prod", {}).setdefault("orit", 0.0)
        trace.add("5 displacement", {"turn": turn},
                  {"orit_price": m["orit_price"], "loziska": ["N6", "N3", "N8", "N9"]})
        phase = state["phase"]

    elif phase == "displacement":
        loans = [e for e in events if e.get("kind") == "loan_given"]
        if loans:
            _set_phase(state, "boom", "prvni loan po displacementu", loans[0]["player"],
                       trace, events)
            m["boom_started_turn"] = turn
        elif turn >= 45:
            # bublina musi prijit (pravidlo 5, posledni odstavec)
            _set_phase(state, "boom", "tah 45 bez pujcky, vynuceny boom", turn, trace, events)
            m["boom_started_turn"] = turn
            events.append({"kind": "forced_boom", "npc": "N6"})
        phase = state["phase"]

    elif phase == "boom" and float(m["orit_price"] or 0) >= 20.0:
        _set_phase(state, "euphoria", "cena oritu >= 20", m["orit_price"], trace, events)
        phase = state["phase"]

    elif phase == "euphoria":
        debts = sum(sum(float(v) for v in n["debt"].values()) for n in state["npc"].values())
        wealth = sum(float(n["wealth"]) for n in state["npc"].values())
        if wealth > 0 and debts > 0.6 * wealth:
            _set_phase(state, "overtrading", "dluhy NPC > 60 % jejich wealth",
                       round(debts / wealth, 3), trace, events)
        phase = state["phase"]

    elif phase == "overtrading":
        if _default_turns(state) >= 1:
            _set_phase(state, "distress", "prvni nesplaceni", _default_turns(state),
                       trace, events)
        phase = state["phase"]

    elif phase == "distress":
        started = None
        for rec in reversed(m["phase_log"]):
            if rec["to"] == "distress":
                started = rec["turn"]
                break
        if _default_turns(state) >= 2 or (started is not None and turn - started >= 2):
            _set_phase(state, "panic", "druhe nesplaceni nebo 2 tahy distress",
                       _default_turns(state), trace, events)
        phase = state["phase"]

    elif phase == "panic":
        _set_phase(state, "crash", "po jednom tahu paniky", turn, trace, events)
        m["crash_turn"] = turn
        phase = state["phase"]

    elif phase == "crash" and m.get("crash_turn") is not None and turn - m["crash_turn"] >= 6:
        _set_phase(state, "depression", "6 tahu po crash", turn, trace, events)
        phase = state["phase"]

    elif phase == "depression" and m.get("crash_turn") is not None and turn - m["crash_turn"] >= 12:
        _set_phase(state, "recovery", "12 tahu po crash", turn, trace, events)
        phase = state["phase"]

    # --- efekty faze ---------------------------------------------------------
    price_before = m.get("orit_price")
    if phase == "boom":
        m["orit_price"] = float(m["orit_price"]) * 1.15
    elif phase == "euphoria":
        m["orit_price"] = float(m["orit_price"]) * 1.2
        for i, n in state["npc"].items():
            if sum(float(v) for v in n["debt"].values()) > 30:
                n["law"] = clamp(float(n["law"]) - 0.15, 0.0, 10.0)
    elif phase == "overtrading":
        m["orit_price"] = float(m["orit_price"]) * 1.1
    elif phase == "distress":
        for i in world_ids(state):
            e = ent(state, i)
            e["paper_wealth"] = float(e.get("paper_wealth", 0.0)) * 0.7
        state["deals"] = [d for d in state["deals"]
                          if not (d["type"] == "trade" and d.get("res") == "orit")]
    elif phase == "panic":
        m["orit_price"] = float(m["orit_price"]) * 0.5
        for i in world_ids(state):
            ent(state, i)["paper_wealth"] = 0.0
        for pid in ("A", "B", "C"):
            p = state["players"][pid]
            written_off = 0.0
            for n in state["npc"].values():
                owed = float(n["debt"].get(pid, 0.0))
                if owed > 0:
                    written_off += owed * 0.6
                    n["debt"][pid] = owed * 0.4
            if written_off > 0:
                p["wealth"] = max(0.0, float(p["wealth"]) - written_off)
                trace.add("5 panic odpis pohledavek", {"creditor": pid},
                          {"odepsano": round(written_off, 3)})
        for i, n in state["npc"].items():
            if sum(float(v) for v in n["debt"].values()) > 0:
                n["wealth"] = float(n["wealth"]) * 0.8
    elif phase == "crash":
        if m.get("crash_turn") == turn:
            m["orit_price"] = 3.0
            _migration_back(state, trace)
        # uvolneni sfer: NPC ve sphere_X, ktere X nesplacelo, zpet na independent
        if m.get("crash_turn") == turn:
            for i, n in state["npc"].items():
                for pid in ("A", "B"):
                    if n["status"] == f"sphere_{pid}" and any(
                            d["npc"] == i and d["creditor"] == pid for d in m["defaults"]):
                        n["status"] = "independent"
                        n["influence"][pid] = float(n["influence"][pid]) / 2.0
                        events.append({"kind": "sphere_released", "npc": i, "from": pid})
    elif phase == "depression":
        m["orit_price"] = 5.0
    elif phase == "recovery":
        m["orit_price"] = 5.0

    if price_before != m.get("orit_price"):
        trace.add("5 cena oritu", {"faze": phase, "pred": price_before},
                  {"po": m.get("orit_price")})

    # papirove bohatstvi (pravidla 5 a 10.3)
    if phase in ("boom", "euphoria", "overtrading"):
        price = float(m["orit_price"])
        for i, n in state["npc"].items():
            if float(n["prod"].get("orit", 0.0)) > 0:
                n["paper_wealth"] = float(n["prod"]["orit"]) * price
        for pid in ("A", "B"):
            total = 0.0
            for n in state["npc"].values():
                if float(n["prod"].get("orit", 0.0)) > 0:
                    total += float(n["debt"].get(pid, 0.0))
            state["players"][pid]["paper_wealth"] = total * (price / 10.0)
        trace.add("5 / 10.3 papirove bohatstvi", {"cena": price},
                  {"A": state["players"]["A"]["paper_wealth"],
                   "B": state["players"]["B"]["paper_wealth"]})

    # migrace v boomu (OPEN_QUESTIONS C1)
    if phase in ("boom", "euphoria", "overtrading"):
        _migration(state, rng, trace, events)

    # automaticky explore NPC od displacementu (pravidlo 5, OPEN_QUESTIONS C4)
    if phase in ORIT_PHASES:
        for i, n in sorted(state["npc"].items()):
            if n.get("kind") == "fallen":
                continue
            if float(n["wealth"]) >= 20.0:
                n["wealth"] = float(n["wealth"]) - 2.0
                if rng.random() < 0.15:
                    n["prod"]["orit"] = float(n["prod"].get("orit", 0.0)) + 2.0
                    events.append({"kind": "orit_found", "npc": i})
                    trace.add("5 explore NPC", {"npc": i}, {"prod_orit": n["prod"]["orit"]})

    # fragilita
    debts = sum(sum(float(v) for v in n["debt"].values()) for n in state["npc"].values())
    wealth = sum(float(n["wealth"]) for n in state["npc"].values())
    m["fragility"] = round(debts / wealth, 4) if wealth > 0 else 0.0


def _migration(state, rng, trace, events) -> None:
    """Boom: NPC s prod.orit >= 2 dostava pop +2, dva darci po -1 (C1)."""
    receivers = [i for i, n in sorted(state["npc"].items())
                 if float(n["prod"].get("orit", 0.0)) >= 2.0]
    donors_pool = [i for i, n in sorted(state["npc"].items())
                   if float(n["prod"].get("orit", 0.0)) == 0.0
                   and n.get("kind") != "fallen" and float(n["pop"]) > 1.0]
    for r in receivers:
        chosen = []
        pool = list(donors_pool)
        for _ in range(2):
            if not pool:
                break
            pick = pool.pop(rng.randrange(len(pool)))
            chosen.append(pick)
        if len(chosen) < 2:
            continue
        state["npc"][r]["pop"] = float(state["npc"][r]["pop"]) + float(len(chosen))
        for dnr in chosen:
            state["npc"][dnr]["pop"] = float(state["npc"][dnr]["pop"]) - 1.0
            g = float(state["npc"][dnr]["prod"].get("grain", 0.0))
            state["npc"][dnr]["prod"]["grain"] = max(0.0, g - 0.5)
        state["minsky"]["migration_ledger"].append({"to": r, "from": chosen})
        trace.add("5 migrace", {"cil": r, "darci": chosen},
                  {"pop_delta": 0.0, "pop_cil": state["npc"][r]["pop"]})
        events.append({"kind": "migration", "to": r, "from": chosen})


def _migration_back(state, trace) -> None:
    """Crash: migrace zpet (pravidlo 5). Rozpusti cely ucet migrace: kazdy
    migrant se vraci domu a docasna srazka prod.grain u darcu se rusi."""
    ledger = state["minsky"].get("migration_ledger", [])
    vraceno = 0
    for rec in ledger:
        r = rec["to"]
        donors = [d for d in rec["from"] if d in state["npc"]]
        # Docasna srazka obili konci vzdy, i kdyz uz neni koho vracet.
        for dnr in donors:
            g = float(state["npc"][dnr]["prod"].get("grain", 0.0))
            state["npc"][dnr]["prod"]["grain"] = g + 0.5
        if r not in state["npc"]:
            continue
        # Migrant, ktereho mezitim sebrala bida, se vratit nemuze.
        # Vraci se jen tolik lidi, kolik jich v cili opravdu je, aby soucet
        # pop sveta zustal zachovany (invariant ve validate.py).
        take = min(float(len(donors)), max(0.0, float(state["npc"][r]["pop"])))
        state["npc"][r]["pop"] = float(state["npc"][r]["pop"]) - take
        zbyva = take
        for dnr in donors:
            if zbyva <= 0:
                break
            dej = min(1.0, zbyva)
            state["npc"][dnr]["pop"] = float(state["npc"][dnr]["pop"]) + dej
            zbyva -= dej
            vraceno += dej
    state["minsky"]["migration_ledger"] = []
    trace.add("5 migrace zpet", {"faze": "crash", "zaznamu": len(ledger)},
              {"pop_delta": 0.0, "vraceno_migrantu": vraceno})


# --------------------------------------------------------------------------
# 7 Unie
# --------------------------------------------------------------------------

def step_union(state, npcdata, trace: Trace, events: list) -> None:
    C = state["players"]["C"]
    turn = state["meta"]["turn"]
    m = state["minsky"]

    # 7.1 vznik v tahu crash
    if not C["active"] and state["phase"] == "crash" and m.get("crash_turn") == turn:
        founders = []
        for i, n in sorted(state["npc"].items()):
            if n["status"] != "independent" or n.get("kind") != "normal":
                continue
            defaulted = any(d["npc"] == i for d in m["defaults"])
            peak = float(n.get("wealth_peak", n["wealth"]))
            lost = peak > 0 and float(n["wealth"]) <= 0.7 * peak
            if defaulted or lost:
                founders.append(i)
        for i, n in sorted(state["npc"].items()):
            if n.get("kind") != "fallen" or n["status"] != "independent":
                continue
            if i in m["fallen_touched"]:
                continue
            if any(f in neighbours(npcdata, i) for f in founders):
                founders.append(i)
        if len(founders) >= 3:
            C["active"] = True
            C["founded_turn"] = turn
            C["members"] = founders
            C["name"] = C.get("name") or "Unie"
            fund = 0.0
            for f in founders:
                take = float(state["npc"][f]["wealth"]) * 0.10
                state["npc"][f]["wealth"] -= take
                state["npc"][f]["status"] = "union"
                fund += take
            C["wealth"] = fund
            C["fund"] = fund
            events.append({"kind": "union_founded", "members": founders, "fund": fund})
            trace.add("7.1 vznik Unie", {"zakladatele": founders},
                      {"fond": round(fund, 3), "tah": turn})
        else:
            events.append({"kind": "union_failed", "candidates": founders})
            trace.add("7.1 Unie nevznikla", {"zakladatele": founders},
                      {"pocet": len(founders), "minimum": 3})

    if not C["active"]:
        return

    # 7.3 vstupni prah prava
    if C["members"]:
        avg = sum(float(state["npc"][mm]["law"]) for mm in C["members"]) / len(C["members"])
        C["law_threshold"] = round(avg - 1.0, 3)
        trace.add("7.3 prah prava", {"clenove": list(C["members"])},
                  {"law_threshold": C["law_threshold"]})

    # 7.4 bolest: nezavisle NPC v bide nebo po prevratu zada samo
    for i, n in sorted(state["npc"].items()):
        if n["status"] != "independent" or n.get("kind") == "fallen":
            continue
        hurting = float(n["wealth"]) < 15.0 or int(n.get("coups", 0)) > 0
        if not hurting:
            continue
        if C["law_threshold"] is not None and float(n["law"]) >= float(C["law_threshold"]):
            n["status"] = "union"
            C["members"].append(i)
            events.append({"kind": "union_join", "npc": i, "how": "bolest"})
        else:
            n["status"] = "candidate"
            if i not in C["candidates"]:
                C["candidates"].append(i)
            events.append({"kind": "union_candidate", "npc": i})
        trace.add("7.4 vstup bolesti", {"npc": i, "law": n["law"]},
                  {"status": n["status"]})

    # kandidat se stava clenem, jakmile splni prah
    for i in list(C["candidates"]):
        n = state["npc"].get(i)
        if n is None:
            continue
        if C["law_threshold"] is not None and float(n["law"]) >= float(C["law_threshold"]):
            C["candidates"].remove(i)
            C["members"].append(i)
            n["status"] = "union"
            events.append({"kind": "union_join", "npc": i, "how": "prah splnen"})

    C["power"] = sum(float(state["npc"][mm]["power"]) for mm in C["members"]) \
        if C["members"] else 0.0
    C["fund"] = C["wealth"]


def _union_admit(state, target, events, trace) -> None:
    """7.4 pritazlivost: Unie nabidne clenstvi, NPC prijme, pokud splni podminky."""
    C = state["players"]["C"]
    n = state["npc"].get(target)
    if n is None or n["status"] != "independent":
        return
    if C["law_threshold"] is not None and float(n["law"]) < float(C["law_threshold"]):
        events.append({"kind": "union_rejected", "npc": target, "reason": "law pod prahem"})
        return
    if float(n["influence"]["A"]) > 8 or float(n["influence"]["B"]) > 8:
        events.append({"kind": "union_rejected", "npc": target, "reason": "vliv velmoci"})
        return
    n["status"] = "union"
    C["members"].append(target)
    take = float(n["wealth"]) * 0.10
    n["wealth"] -= take
    C["wealth"] = float(C["wealth"]) + take
    events.append({"kind": "union_join", "npc": target, "how": "admit"})
    trace.add("7.4 admit", {"npc": target}, {"fond": C["wealth"]})


# --------------------------------------------------------------------------
# 8 metriky
# --------------------------------------------------------------------------

def step_metrics(state, trace: Trace) -> None:
    tr = state.get("_trade", {"volume": 0.0, "weighted": 0.0,
                              "by_player": {"A": 0.0, "B": 0.0, "C": 0.0},
                              "by_npc": {}})
    # A_trade_share
    world_vol = tr["weighted"]
    a_vol = tr["by_player"]["A"]
    for i, n in state["npc"].items():
        if n["status"] == "sphere_A":
            a_vol += 0.5 * tr["by_npc"].get(i, 0.0)
    a_share = (a_vol / world_vol) if world_vol > 0 else 0.0

    # B_resource_share (efektivni produkce, viz OPEN_QUESTIONS C5)
    def prod_units(e):
        return sum(eff_prod(e, r) for r in RESOURCES)

    world_prod = sum(prod_units(ent(state, i)) for i in world_ids(state))
    b_units = prod_units(state["players"]["B"])
    for t in state["players"]["B"].get("occupied", []):
        if t in state["npc"]:
            b_units += prod_units(state["npc"][t])
    for i, n in state["npc"].items():
        if n["status"] == "sphere_B":
            b_units += 0.5 * prod_units(n)
    b_share = (b_units / world_prod) if world_prod > 0 else 0.0

    # C_min_member
    C = state["players"]["C"]
    c_min = min((float(state["npc"][mm]["wealth"]) for mm in C["members"]), default=None) \
        if C["active"] and C["members"] else None

    # prosperity_index
    w_real = sum(float(ent(state, i)["wealth"]) for i in world_ids(state))
    w0 = float(state["metrics"]["W0"])
    shares = []
    for pid in ("A", "B"):
        own = float(state["players"][pid]["wealth"])
        for t in state["players"][pid].get("occupied", []):
            if t in state["npc"]:
                own += float(state["npc"][t]["wealth"])
        shares.append(own)
    shares += [float(n["wealth"]) for n in state["npc"].values()]
    max_share = (max(shares) / w_real) if w_real > 0 else 0.0
    # n_bida podle definice 4.3 (wealth < 15 nebo deficit obili >= 3), ne jen podle wealth
    n_bida = len(state.get("_poverty", []))
    index = 100.0 * (w_real / w0) * (1.0 - max_share) * (1.0 - n_bida / 14.0)

    state["metrics"].update({
        "A_trade_share": round(a_share, 4),
        "B_resource_share": round(b_share, 4),
        "C_min_member": round(c_min, 3) if c_min is not None else None,
        "prosperity_index": round(index, 2),
        "W_real": round(w_real, 2),
        "n_bida": n_bida,
        "max_share": round(max_share, 4),
    })
    trace.add("8 metriky", {"W_real": round(w_real, 2), "W0": w0, "n_bida": n_bida},
              {"prosperity_index": state["metrics"]["prosperity_index"],
               "A_trade_share": state["metrics"]["A_trade_share"],
               "B_resource_share": state["metrics"]["B_resource_share"]})


# --------------------------------------------------------------------------
# pohledy hracu (BUILD.md cast 2, pravidla cast 2)
# --------------------------------------------------------------------------

HIDDEN_FIELDS = ("law", "tech", "prosperity_index", "law_threshold",
                 "poverty_streak", "wealth_peak")


def build_views(state, npcdata) -> dict:
    views = {}
    C = state["players"]["C"]
    for pid in ("A", "B", "C"):
        if pid == "C" and not C["active"]:
            continue
        npc_view = {}
        for i, n in state["npc"].items():
            item = {
                "wealth": round(float(n["wealth"]) + float(n.get("paper_wealth", 0.0)), 2),
                "power": round(float(n["power"]), 2),
                "prod": {k: round(float(v), 3) for k, v in n["prod"].items()},
                "need": {k: round(float(v), 3) for k, v in n.get("need", {}).items()},
                "status": n["status"],
                "pop": round(float(n["pop"]), 2),
                "coups": int(n.get("coups", 0)),
                "kind": n.get("kind", "normal"),
            }
            if pid in ("A", "B"):
                item["influence_moje"] = round(float(n["influence"].get(pid, 0.0)), 3)
                item["dluzi_mne"] = round(float(n["debt"].get(pid, 0.0)), 3)
            else:
                item["dluzi_mne"] = round(float(n["debt"].get("C", 0.0)), 3)
                if i in C["members"] or i in C["candidates"]:
                    item["law"] = round(float(n["law"]), 3)
                    item["tech"] = round(float(n["tech"]), 3)
            npc_view[i] = item
        me = state["players"][pid]
        mine = {
            "wealth": round(float(me["wealth"]), 2),
            "paper_wealth": round(float(me.get("paper_wealth", 0.0)), 2),
            "power": round(float(me["power"]), 2),
        }
        if pid in ("A", "B"):
            mine["prod"] = {k: round(float(v), 3) for k, v in me["prod"].items()}
            mine["need"] = {k: round(float(v), 3) for k, v in me.get("need", {}).items()}
            mine["pop"] = round(float(me["pop"]), 2)
            mine["law"] = round(float(me["law"]), 3)
            mine["tech"] = round(float(me["tech"]), 3)
            mine["occupied"] = list(me.get("occupied", []))
        else:
            mine["members"] = list(C["members"])
            mine["candidates"] = list(C["candidates"])
        views[pid] = {
            "turn": state["meta"]["turn"],
            "day": state["meta"]["day"],
            "slot": state["meta"]["slot"],
            "ja": mine,
            "npc": npc_view,
            "ceny": {r: market_price(state, r) for r in
                     (BASE_RESOURCES + ("orit",) if state["phase"] in ORIT_PHASES
                      else BASE_RESOURCES)},
            "deals": [d for d in state["deals"] if d["owner"] == pid],
            "news": list(state.get("news", [])),
        }
    return views


# --------------------------------------------------------------------------
# hlavni vstupni bod
# --------------------------------------------------------------------------

def apply_turn(state, npcdata, actions):
    """Provede jeden tah. Vraci (novy_stav, events, applied_rules).

    Vstupni `state` se nemeni, pracuje se na kopii.
    """
    st = deepcopy(state)
    normalize(st)
    turn = int(st["meta"]["turn"]) + 1
    st["meta"]["turn"] = turn
    st["meta"]["day"] = day_of(turn)
    st["meta"]["slot"] = slot_of(turn)
    rng = random.Random(int(st["meta"]["rng_seed"]) + turn)
    trace = Trace()

    pop_before = sum(float(ent(st, i)["pop"]) for i in world_ids(st))

    events = apply_actions(st, npcdata, actions, rng, trace)
    upkeep_deals(st, trace, events)
    grain_deficit = step_resources(st, trace, events)
    step_growth(st, grain_deficit, trace)
    step_poverty(st, npcdata, grain_deficit, trace, events)
    step_repayments(st, trace, events)
    step_invasions(st, npcdata, trace, events)
    step_influence(st, trace, events)
    step_minsky(st, npcdata, rng, trace, events)
    step_union(st, npcdata, trace, events)
    step_metrics(st, trace)

    pop_after = sum(float(ent(st, i)["pop"]) for i in world_ids(st))
    trace.add("kontrola pop", {"pred": round(pop_before, 3)},
              {"po": round(pop_after, 3), "rozdil": round(pop_after - pop_before, 3)})

    st.pop("_trade", None)
    st.pop("_poverty", None)
    st["players"]["C"]["fund"] = st["players"]["C"]["wealth"]
    st["log"] = (st.get("log", []) + [{"turn": turn, "events": events}])[-9:]
    return st, events, trace.items

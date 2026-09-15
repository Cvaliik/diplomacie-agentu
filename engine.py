"""engine.py

Deterministicka cast sveta Ardan. Vykonava docs/pravidla.md 1:1.
Model sem nevstupuje: veskera aritmetika je tady, rozhodci jen preklada
tahy na akce a pise Zpravy (pravidla cast 9).

Poradi prepoctu (pravidla v1.2):
    4.1b ceny -> akce hracu -> 4.0 a 4.1 potreby, vyroba goods, obchod, zasoby, deficit
    -> 4.2 tech a pravo -> 4.2a automatika NPC -> 4.2b neformalni prijem
    -> 4.2c rust prumyslu -> 4.3 bida a prevrat -> 4.5 splatky -> 3.3 invaze
    -> 4.4 vliv a sfery -> 5 Minsky -> 7 Unie -> 8 metriky

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
import zlib
from copy import deepcopy

RESOURCES = ("oil", "grain", "metal", "orit")     # suroviny; do metriky B jde jen tohle
BASE_RESOURCES = ("oil", "grain", "metal")
GOODS = "goods"
# Poradi obchodu v tahu: nejdriv vstupy pro prumysl, pak produkt (4.0).
INPUT_GOODS = ("grain", "oil", "metal", "orit")
TRADEABLES = INPUT_GOODS + (GOODS,)
BASE_PRICE = {"oil": 1.0, "grain": 0.8, "metal": 1.2, "goods": 1.5}
GOODS_INPUT = {"oil": 0.5, "metal": 0.3}   # vstupy na jednotku goods (4.0)
ORIT_PRICE_CAP = 200.0                      # strop ceny oritu (5, v1.2)
CYCLE_GUARD_TURNS = 8                       # pojistka cyklu (5, v1.4)
COUP_IMMUNITY_TURNS = 6                     # imunita po prevratu (4.3, v1.2)
STOCK_RESOURCES = ("grain", "oil", "metal", "goods", "orit")   # zasoby (4.1c, v1.3)
STOCK_CAP_TURNS = 10                        # strop zasoby = 10 tahu spotreby
ORIT_STOCK_CAP = 20.0                       # strop zasoby oritu v jednotkach
RESERVE_TURNS = 3                           # 4.1a prodava prebytek nad 3 tahy spotreby
INDUSTRY_FLOOR = 0.5                        # dno prumyslu vsech statu (4.2c, v1.4)
INCOME_POP_DIVISOR = 60.0                   # neformalni prijem pop / 60 (4.2b, v1.4)
REFILL_MIN_WEALTH = 25.0                    # rezervu doplnuje jen stat s wealth >= 25 (4.1c, v1.6)
SPHERE_OVERLOAD = 0.8                       # pretizeni sfer: 0.8 na kazdou drzenou sferu (4.4, v1.6)
UNION_CONTRIBUTION = 0.02                   # prispevek clena do fondu za tah (7.2, v1.6)
UNION_FOUNDER_LOSS = 0.20                   # ztrata 20 % predkrizoveho maxima (7.1, v1.6)
OFFER_VALID_TURNS = 2                       # nabidka NPC plati 2 tahy (3.5, v1.6)
COUNTER_VALID_TURNS = 3                     # protinavrh plati 3 tahy (3.4, v1.6)
TARIFF_RATE = 0.10                          # vychozi clo celni unie (7.2, v1.8)
TARIFF_MAX = 0.20                           # set_tariff: sazba 0 az 0.20 (7.2, v1.9)
TARIFF_STEP = 0.05                          # set_tariff: krok sazby (7.2, v1.9)
PLAYER_FLAT_CROSSINGS = 1                   # pausal prejezdu A a B na automatickem trhu (4.1a, v1.9)
SPECULATIVE_SHARE = 0.1                     # spekulativni nabidka velkych tovaren (4.0, v1.9)
# 4.1a (v1.9): parovani podle ceny. False vraci parovani v1.8 jen pro srovnani v test_run.py.
PRICE_PAIRING = True
WAR_POWER_LOSS = 10.0                       # valka hracu: power -10 za tah obema (3.3a, v1.10)
WAR_WEALTH_LOSS = 0.05                      # valka hracu: wealth -5 % za tah obema
WAR_RETREAT_INFLUENCE = 0.30                # ustup: -30 % vlivu u vsech NPC
WAR_CAPITULATION_INFLUENCE = 0.50           # kapitulace: -50 % vlivu vsude
WAR_CAPITULATION_WEALTH = 0.20              # kapitulace: 20 % wealth jde vitezi
WAR_TARIFF_EXTRA = 0.10                     # clo Unie navic vuci tomu, kdo valku vyhlasil
WAR_SPHERE_TRADE = 0.5                      # obchod s NPC ve sfere nepritele x0.5
WAR_INFLUENCE_AGGRESSOR = 2.0               # nezavisla NPC: vliv vyhlasovatele -2 za tah (v1.10 dodatek)
WAR_INFLUENCE_DEFENDER = 1.0                # ... vliv napadeneho -1 za tah
WAR_CEASEFIRE_INFLUENCE = 0.10              # primeri: -10 % vlivu obema misto 30 % ustupu
ARM_MAX = 40.0                              # arm: nejvys 40 wealth na akci (3.2, v1.10)
ARM_RATIO = 1.6                             # arm: power += amount / 1.6
ADMIT_ZONE_MIN = 8.0                        # admit ze zony vlivu: vliv nad 8 ...
ADMIT_ZONE_MAX = 12.0                       # ... do 12 vcetne (7.4, v1.10)
MAX_CROSSINGS = 3                           # nejvys 3 prejezdy na trhu (4.1a, v1.5)
TRANSIT_SURCHARGE = 0.1                     # prirazka za prejezd (4.1a, v1.5)
SOLIDARITY_MAX = 3.0                        # automaticka solidarita Unie za tah (7.2, v1.5)
SOLIDARITY_FUND_FLOOR = 5.0                 # ve fondu musi zustat aspon 5 (7.2, v1.5)
COUP_LAW_PENALTY = 1.0                      # clenovi Unie po prevratu klesne law (4.3, v1.5)

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


def base_price(state, res: str) -> float:
    """Zaklad ceny pred dynamikou. U oritu je zakladem Minskyho cena z casti 5."""
    if res == "orit":
        p = state["minsky"].get("orit_price")
        return float(p) if p is not None else float(state["minsky"]["orit_price_start"])
    return BASE_PRICE[res]


def market_price(state, res: str) -> float:
    """Aktualni cena podle 4.1b. Prepocitava ji step_prices na zacatku tahu."""
    prices = state.get("prices") or {}
    if res in prices:
        return float(prices[res])
    return base_price(state, res)


def step_prices(state, trace: "Trace") -> None:
    """4.1b: cena = zaklad x clamp(svetova poptavka / svetova nabidka, 0.7, 1.5).

    Poptavka se bere z potreb spocitanych v minulem tahu (4.0); v prvnim tahu,
    kdy jeste nejsou, z predbezneho odhadu pri plnem vyuziti tovaren. Nabidkou
    goods je vyroba z minuleho tahu. U oritu je zakladem Minskyho cena, dynamika
    se k ni pricita a vysledek je zastropovany na 200 (5, v1.2).
    """
    prices = {}
    detail = {}
    orit_on = state["phase"] in ORIT_PHASES
    for res in TRADEABLES:
        if res == "orit" and not orit_on:
            continue
        demand = 0.0
        supply = 0.0
        for i in world_ids(state):
            if res == "orit" and is_fallen(state, i):
                continue  # 7a: padle rise orit nepotrebuji ani netezi
            demand += float(current_need(state, i).get(res, 0.0))
            supply += supply_of(state, i, res)
        ratio = (demand / supply) if supply > 0 else 1.5
        ratio = clamp(ratio, 0.7, 1.5)
        price = base_price(state, res) * ratio
        if res == "orit":
            price = min(ORIT_PRICE_CAP, price)
        prices[res] = round(price, 4)
        detail[res] = {"poptavka": round(demand, 2), "nabidka": round(supply, 2),
                       "pomer": round(ratio, 3), "cena": prices[res]}
    state["prices"] = prices
    trace.add("4.1b dynamicka cena", {"faze": state["phase"]}, detail)


def precompute_prices(state, trace=None) -> None:
    """4.1b (v1.10.2): cena pristiho tahu ze stavu na konci tohoto tahu (pro pohledy a pasmo trade_offer)."""
    step_prices(state, trace if trace is not None else Trace())
    state["prices_turn"] = int(state["meta"]["turn"]) + 1


def eff_prod(e: dict, res: str) -> float:
    """Efektivni produkce: prod x (1 + tech/20) x pop/pop_start (4.1 a 10.2, v1.3)."""
    base = float(e.get("prod", {}).get(res, 0.0))
    tech = float(e.get("tech") or 0.0)
    pop = float(e.get("pop") or 0.0)
    pop_start = float(e.get("pop_start") or 0.0) or 100.0
    return base * (1.0 + tech / 20.0) * (pop / pop_start)


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def household_need(e: dict, wealth=None) -> dict:
    """4.0: spotreba domacnosti podle obyvatelstva.

    v1.7: need.goods = (pop / 100) x (1 + wealth / 60), nejvys 4 na 100 pop. Pri
    prepoctu tahu se bere wealth zmrazene na zacatku 4.1 (Q2), jinak aktualni.
    """
    p = float(e.get("pop") or 0.0) / 100.0
    w = float(e.get("wealth") or 0.0) if wealth is None else float(wealth)
    goods = min(4.0 * p, p * (1.0 + max(0.0, w) / 60.0))
    return {"grain": 3.0 * p, "goods": goods, "oil": 0.6 * p, "metal": 0.5 * p}


def goods_potential(e: dict) -> float:
    """4.0: vyroba goods pri plnem pokryti vstupu (coverage = 1)."""
    industry = float(e.get("industry") or 0.0)
    pop = float(e.get("pop") or 0.0)
    pop_start = float(e.get("pop_start") or 0.0) or 100.0
    tech = float(e.get("tech") or 0.0)
    return industry * (pop / pop_start) * (1.0 + tech / 10.0)   # 4.0 (v1.4)


def orit_need(state, sid: str) -> float:
    """need.orit = 2 pro hrace a bezna NPC od displacementu (5)."""
    if state["phase"] not in ORIT_PHASES or is_fallen(state, sid):
        return 0.0
    return 2.0


def compute_need(state, sid: str, goods_out: float) -> dict:
    """4.0: potreby statu pri dane vyrobe goods (domacnosti plus prumysl)."""
    hh = household_need(ent(state, sid), state.get("_need_wealth", {}).get(sid))
    return {
        "grain": hh["grain"],
        "goods": hh["goods"],
        "oil": hh["oil"] + GOODS_INPUT["oil"] * goods_out,
        "metal": hh["metal"] + GOODS_INPUT["metal"] * goods_out,
        "orit": orit_need(state, sid),
    }


def planned_goods(state, sid: str, capacity: float) -> float:
    """4.0 (v1.7): planovana vyroba goods.

    Stat vyrabi jen do vyse vlastni potreby + 1.2 x prodane goods minuleho tahu
    + doplneni rezervy goods (3 tahy spotreby minus zasoba), nejvys do kapacity.
    Doplneni rezervy vlastni vyrobou neni vazane na wealth >= 25 (Q4).
    """
    e = ent(state, sid)
    own = household_need(e, state.get("_need_wealth", {}).get(sid))["goods"]
    sold = float(e.get("goods_sold_last") or 0.0)
    refill = max(0.0, RESERVE_TURNS * own - float((e.get("stock") or {}).get("goods", 0.0)))
    plan = own + 1.2 * sold + refill
    industry = float(e.get("industry") or 0.0)
    if industry < 2.0:
        # 4.0 (v1.8): male tovarny planuji nejvys 50 % vlastni potreby, zbytek se dovazi (S1)
        plan = min(plan, 0.5 * own)
    elif industry >= 4.0:
        # 4.0 (v1.8): velke tovarny pridavaji spekulativni exportni nabidku 10 % kapacity (S2)
        plan = plan + 0.1 * capacity
    return max(0.0, min(capacity, plan))


def current_need(state, sid: str) -> dict:
    """Potreby z posledniho prepoctu; bez nej predbezne pri plnem vyuziti tovaren."""
    e = ent(state, sid)
    need = e.get("need")
    if isinstance(need, dict) and GOODS in need:
        return need
    # 4.1b (v1.10.2): pred prvnim prepoctem z planu vyroby jako ostatni tahy, ne z plne kapacity
    return compute_need(state, sid, planned_goods(state, sid, goods_potential(e)))


def supply_of(state, sid: str, res: str) -> float:
    """Vlastni nabidka statku: efektivni produkce, u goods vyroba (posledni znama)."""
    e = ent(state, sid)
    if res == GOODS:
        if e.get("goods_out") is not None:
            return float(e["goods_out"])
        return planned_goods(state, sid, goods_potential(e))   # 4.1b (v1.10.2)
    return eff_prod(e, res)


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
        p.setdefault("industry", 0.0)
        p.setdefault("last_coup_turn", None)
        p.setdefault("pop_start", p.get("pop", 100))
        stock = p.setdefault("stock", {})
        for r in STOCK_RESOURCES:
            stock.setdefault(r, 0.0)
    for i, n in state["npc"].items():
        n.setdefault("poverty_streak", 0)
        n.setdefault("coups", 0)
        n.setdefault("paper_wealth", 0.0)
        n.setdefault("industry", 0.0)
        n.setdefault("pop_start", n.get("pop", 100))
        # Bohatstvi na konci poslednich tahu pro podminku rustu v 4.2a (v1.4).
        n.setdefault("wealth_history", [float(n["wealth"])])
        # Vliv na konci poslednich tahu pro protect_request v 3.5 (v1.6).
        n.setdefault("influence_history", [dict(n["influence"])])
        stock = n.setdefault("stock", {})
        for r in STOCK_RESOURCES:
            stock.setdefault(r, 0.0)
        # Tah posledniho prevratu pro imunitu 4.3 (v1.2).
        n.setdefault("last_coup_turn", None)
        # Predkrizove maximum wealth pro pravidlo 7.1 (ztrata >= 30 %).
        n.setdefault("wealth_peak", float(n["wealth"]))
    # 7.2 (v1.9): sazba cla celni unie a sazba ohlasena akci set_tariff na pristi tah
    state["players"]["C"].setdefault("tariff_rate", TARIFF_RATE)
    state["players"]["C"].setdefault("tariff_next", None)
    state.setdefault("deals", [])
    state.setdefault("wars", [])   # 3.3a (v1.10)
    state["minsky"].setdefault("next_war_id", 1)
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
    state["minsky"].setdefault("npc_trade_last", [])
    state["minsky"].setdefault("next_deal_id", 1)
    state["minsky"].setdefault("next_invasion_id", 1)
    # v1.6: sankce pro 3.4, nabidky NPC 3.5, protinavrhy a soukromy log hracu
    state["minsky"].setdefault("pressure_log", [])
    state["minsky"].setdefault("next_offer_id", 1)
    state["minsky"].setdefault("offer_ignored", {"A": {}, "B": {}, "C": {}})
    state.setdefault("offers", [])
    state.setdefault("counter_offers", [])
    state.setdefault("private_log", {"A": [], "B": [], "C": []})
    state.setdefault("npc_decisions", [])


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
    "invest_industry": 10.0,
    "invest_prod": 12.0,
    "explore": 5.0,
    "arm": 8.0,
}


def add_influence(state, nid: str, pid: str, amount: float) -> float:
    """4.4 (v1.6): prirustek vlivu hrace u NPC s pretizenim sfer.

    Kazda sfera, kterou hrac aktualne drzi, nasobi jeho prirustky vlivu u ostatnich
    NPC koeficientem 0.8. Snizeni vlivu se nenasobi. Vraci skutecne pripsanou hodnotu.
    """
    n = state["npc"][nid]
    if amount > 0 and n["status"] != "sphere_%s" % pid:
        held = sum(1 for x in state["npc"].values() if x["status"] == "sphere_%s" % pid)
        amount *= SPHERE_OVERLOAD ** held
    n["influence"][pid] = float(n["influence"].get(pid, 0.0)) + amount
    return amount


def _openness(npcdata, nid: str) -> float:
    """Skryta ochota NPC prijimat cilene nabidky (npc.json, 0 az 10)."""
    for item in npcdata.get("npc", []):
        if item.get("id") == nid:
            return float(item.get("openness", 5))
    return 5.0


def _decision_roll(state, nid: str) -> int:
    """3.4: hod d100 z random.Random(rng_seed + turn + hash(ID)).

    Vestaveny hash() retezcu je v Pythonu mezi behy nahodny, beh by nebyl
    reprodukovatelny; engine proto bere stabilni CRC32 z ID NPC (N1).
    """
    seed = int(state["meta"]["rng_seed"]) + int(state["meta"]["turn"]) + zlib.crc32(nid.encode("utf-8"))
    return random.Random(seed).randint(1, 100)


DECISION_REASONS = {
    "vliv": "Váš vliv u nás je slabší než vliv vašeho soupeře.",
    "cena": "Nabízené podmínky pro nás nejsou výhodné.",
    "prah": "Zatím nesplňujeme podmínky pro vstup.",
    "otevrenost": "K zahraničním nabídkám jsme obecně zdrženliví.",
    "dluh": "Jsme už příliš zadlužení.",
    "sila": "Svou obranu zvládneme sami.",
    "sankce": "Nedávno jste proti nám uvalili sankce.",
    "pravo": "Naše soudy by takovou cenu neuznaly.",
}
DECISION_POSITIVE = "Nabídka odpovídá našim zájmům."
DECISION_NEUTRAL = "Nabídku jsme po zvážení nepřijali."


def _npc_score(state, npcdata, pid, nid, atype, params, price_ratio=None, direction=None):
    """3.4: faktory a skore NPC bez hodu. Pouziva ho _npc_decide i soutez o cil (3.4a)."""
    turn = int(state["meta"]["turn"])
    n = state["npc"][nid]
    f = {}
    if pid in ("A", "B"):
        rival = "B" if pid == "A" else "A"
        f["vliv"] = 4.0 * (float(n["influence"].get(pid, 0.0)) - float(n["influence"].get(rival, 0.0)))
    if atype == "trade_offer" and price_ratio is not None:
        gain = price_ratio - 1.0
        if direction == "npc_buys":
            gain = -gain  # vyhodnost ceny z pohledu NPC (N-otazka)
        f["cena"] = 30.0 * gain
    if atype == "admit":
        thr = state["players"]["C"].get("law_threshold")
        # 7.4 (v1.7): prah je tvrda podminka v _union_admit, zde uz jen bonus +10
        f["prah"] = 10.0
    f["otevrenost"] = 4.0 * (_openness(npcdata, nid) - 5.0)
    if atype == "loan":
        if state["phase"] in ("boom", "euphoria"):
            f["boom"] = 20.0
        debt = sum(float(v) for v in n["debt"].values())
        if debt > 0.5 * max(1.0, float(n["wealth"])):
            f["dluh"] = -20.0
    if atype == "protect" and float(n["power"]) > 8.0:
        f["sila"] = -15.0
    if pid in ("A", "B") and any(r["owner"] == pid and r["target"] == nid and int(r["turn"]) >= turn - 6
                                 for r in state["minsky"].get("pressure_log", [])):
        f["sankce"] = -25.0
    if (atype == "trade_offer" and price_ratio is not None and float(n["law"]) >= 7.0
            and not (0.9 <= price_ratio <= 1.2)):
        f["pravo"] = -20.0

    return f, 40.0 + sum(f.values())


def _npc_decide(state, npcdata, pid, nid, atype, params, price_ratio=None,
                direction=None, events=None, trace=None) -> str:
    """3.4 (v1.6): NPC vyhodnoti cilenou nabidku.

    Vraci "prijato", "podminka", "protinavrh" nebo "odmitnuto". Vysledek s vetou
    duvodu jde do soukromeho logu hrace a do snimku (npc_decisions), ne do Zprav.
    """
    turn = int(state["meta"]["turn"])
    f, score = _npc_score(state, npcdata, pid, nid, atype, params, price_ratio, direction)
    roll = _decision_roll(state, nid)
    if roll <= score:
        outcome = "prijato"
    elif roll <= score + 20:
        outcome = "podminka"
    elif roll <= score + 35:
        outcome = "protinavrh"
    else:
        outcome = "odmitnuto"
    negatives = {k: v for k, v in f.items() if v < 0}
    if negatives:
        reason = DECISION_REASONS[min(negatives, key=negatives.get)]
    else:
        reason = DECISION_POSITIVE if outcome in ("prijato", "podminka") else DECISION_NEUTRAL

    counter = None
    if outcome == "protinavrh":
        if atype == "trade_offer":
            factor = 1.1 if direction == "npc_sells" else 0.9
            counter = {"type": "trade_offer", "player": pid, "npc": nid, "res": params["res"],
                       "qty": round(float(params["qty"]), 3),
                       "price": round(float(params["price"]) * factor, 4),
                       "expires": turn + COUNTER_VALID_TURNS}
            state.setdefault("counter_offers", []).append(counter)
            text = "Obchod s %s přijmeme za cenu %.4f při množství %.3f." % (
                params["res"], counter["price"], counter["qty"])
        elif atype == "loan":
            # 3.4 (v1.7): loan s castkou z protinavrhu projde v dalsich 3 tazich bez hodu
            counter = {"type": "loan", "player": pid, "npc": nid,
                       "amount": round(float(params["amount"]) * 0.7, 2),
                       "expires": turn + COUNTER_VALID_TURNS}
            state.setdefault("counter_offers", []).append(counter)
            text = "Půjčku přijmeme ve výši %.2f." % counter["amount"]
        elif atype == "protect":
            text = "O paktu můžeme jednat později."
        else:
            text = "O vstupu můžeme jednat později."
        state.setdefault("messages_pending", []).append(
            {"from": nid, "to": pid, "text": text, "turn": turn, "protinavrh": counter})

    record = {"turn": turn, "player": pid, "npc": nid, "action": atype, "outcome": outcome,
              "reason": reason, "score": round(score, 2), "roll": roll,
              "params": dict(params), "counter": counter}
    state.setdefault("npc_decisions", []).append(record)
    state.setdefault("private_log", {"A": [], "B": [], "C": []}).setdefault(pid, []).append(
        {"turn": turn, "npc": nid, "action": atype, "outcome": outcome, "reason": reason,
         "counter": counter})
    if events is not None:
        events.append({"kind": "npc_decision", "private": True, "player": pid, "npc": nid,
                       "action": atype, "outcome": outcome})
    if trace is not None:
        trace.add("3.4 rozhodnuti NPC", {"player": pid, "npc": nid, "action": atype,
                                         "faktory": {k: round(v, 2) for k, v in f.items()}},
                  {"skore": round(score, 2), "hod": roll, "vysledek": outcome, "duvod": reason})
    return outcome


def _counter_match(state, pid, nid, res, qty, price) -> bool:
    """3.4: trade_offer se shodnymi parametry protinavrhu projde bez hodu."""
    turn = int(state["meta"]["turn"])
    for c in list(state.get("counter_offers", [])):
        if (c["type"] == "trade_offer" and c["player"] == pid and c["npc"] == nid
                and c["res"] == res and abs(float(c["qty"]) - qty) < 1e-6
                and abs(float(c["price"]) - price) < 1e-6 and turn <= int(c["expires"])):
            state["counter_offers"].remove(c)
            return True
    return False


def _tariff_payer(state, a: str, b: str):
    """7.2 (v1.8): kdo plati clo celni unie. Vraci necelna ze dvojice clen/necleen, jinak None.

    Kandidat neni clen (S4).
    """
    C = state["players"]["C"]
    if not C.get("active"):
        return None
    members = set(C.get("members") or []) | {"C"}   # 7.2 (v1.9): obchod Unie za cleny
    in_a, in_b = a in members, b in members
    if in_a == in_b:
        return None
    return b if in_a else a


def _collect_tariff(state, payer: str, amount: float) -> None:
    """7.2 (v1.8): clo jde do fondu Unie a zapisuje se do union_tariff."""
    C = state["players"]["C"]
    C["wealth"] = float(C["wealth"]) + amount
    book = state.setdefault("_union_tariff", {})
    book[payer] = book.get(payer, 0.0) + amount


def tariff_rate(state) -> float:
    """7.2 (v1.9): platna sazba cla celni unie (vychozi 0.10, meni ji akce set_tariff)."""
    return float(state["players"]["C"].get("tariff_rate", TARIFF_RATE))


def _union_pool(state, res, needs=None, imports=None, exports=None):
    """7.2 (v1.9): pool clenu Unie pro trade_offer Unie.

    Prebytek clena je zasoba plus bilance toku minus rezerva 3 tahu spotreby (jako nabidka
    v 4.1a), deficit clena je deficit toku tohoto tahu. Bez `needs` se bere posledni
    znama potreba (pri podani akce), v prepoctu tahu potreba z planovane vyroby a dosavadni
    dovozy a vyvozy. Vraci ({clen: prebytek}, {clen: deficit}).
    """
    C = state["players"]["C"]
    surplus, deficit = {}, {}
    for m in sorted(C.get("members") or [], key=_npc_key):
        if m not in state["npc"]:
            continue
        e = state["npc"][m]
        need = float((needs[m] if needs is not None else current_need(state, m)).get(res, 0.0))
        bal = supply_of(state, m, res) - need
        if imports is not None:
            bal += imports[m][res] - exports[m][res]
        over = float(e["stock"].get(res, 0.0)) + bal - RESERVE_TURNS * need
        if over > 1e-9:
            surplus[m] = over
        if bal < -1e-9:
            deficit[m] = -bal
    return surplus, deficit


def _union_trade_offer(state, npcdata, act, events, trace) -> None:
    """3.2 a 7.2 (v1.9): trade_offer Unie za cleny s NPC necleny nebo s hracem A ci B.

    Smer urci souhrnna bilance poolu clenu (prebytky nad rezervu minus deficity toku).
    Cil musi mit opacnou bilanci; mnozstvi se orizne na pool i na bilanci cile.
    NPC nabidku vyhodnoti podle 3.4, obchod s hracem projde bez hodu. Bez vlivu.
    """
    C = state["players"]["C"]
    target, res = act.get("target"), act.get("res")
    qty = float(act.get("qty", 0))
    price = float(act.get("price_per_unit", 0))

    def reject(kind, reason):
        events.append({"kind": kind, "player": "C", "type": "trade_offer", "target": target,
                       "res": res, "reason": reason})

    if not C.get("active"):
        return reject("action_invalid", "Unie neexistuje")
    to_player = target in ("A", "B")
    if (target not in state["npc"] and not to_player) or res not in TRADEABLES or qty <= 0:
        return reject("action_invalid", "neznamy cil nebo surovina")
    if target in (C.get("members") or []):
        return reject("action_invalid", "cil je clen Unie, obchod clenu kryje vnitrni trh")
    mp = market_price(state, res)
    lo, hi = 0.7 * mp, 1.5 * mp
    if not to_player and is_fallen(state, target):
        lo = 1.3 * mp  # 7a: cileny obchod s padlou risi jen za >= 1.3x
    if not (lo <= price <= hi):
        return reject("trade_rejected", "cena mimo pasmo")
    surplus, deficit = _union_pool(state, res)
    pooled = sum(surplus.values()) - sum(deficit.values())
    if pooled > 1e-9:
        direction = "npc_buys"      # Unie prodava z prebytku clenu, cil kupuje
    elif pooled < -1e-9:
        direction = "npc_sells"     # Unie nakupuje pro deficity clenu, cil prodava
    else:
        return reject("trade_rejected", "clenove nemaji prebytek ani deficit")
    if res == "orit" and direction == "npc_buys":
        return reject("action_invalid", "Unie orit neprodava")
    bal_t = _npc_balance_for_trade(state, target, res)
    if (direction == "npc_buys" and bal_t >= 0) or (direction == "npc_sells" and bal_t <= 0):
        return reject("trade_rejected", "cil nema opacnou bilanci")
    offered_qty = qty
    qty = min(qty, abs(pooled), abs(bal_t))
    if not to_player:
        if _counter_match(state, "C", target, res, offered_qty, price):
            trace.add("3.4 protinavrh prijat", {"player": "C", "npc": target, "res": res},
                      {"qty": offered_qty, "price": price})
        else:
            outcome = _npc_decide(state, npcdata, "C", target, "trade_offer",
                                  {"res": res, "qty": offered_qty, "price": price},
                                  price_ratio=(price / mp) if mp > 0 else 1.0,
                                  direction=direction, events=events, trace=trace)
            if outcome == "podminka":
                qty = qty * 0.7  # 3.4: objem -30 %
            elif outcome in ("protinavrh", "odmitnuto"):
                return
    deal = {"id": _new_deal_id(state), "type": "trade", "owner": "C", "target": target,
            "res": res, "qty": round(qty, 3), "price": price, "direction": direction,
            "since": state["meta"]["turn"], "pool": True}
    state["deals"].append(deal)
    events.append({"kind": "trade_opened", "deal": deal})
    trace.add("3.2 trade_offer Unie za cleny", {"player": "C", "target": target, "res": res,
                                               "qty": qty, "price": price},
              {"deal_id": deal["id"], "direction": direction,
               "pool_prebytky": {k: round(v, 3) for k, v in surplus.items()},
               "pool_deficity": {k: round(v, 3) for k, v in deficit.items()}})


def _union_deal_execute(state, d, needs, imports, exports, trade_mult, trace) -> float:
    """7.2 (v1.9): provedeni obchodu Unie za cleny v prepoctu tahu. Vraci objem (qty x cena).

    Prodej: mnozstvi se odebere clenum pomerne k prebytku nad rezervu, kupec plati do fondu
    cenu a jako necleen i clo. Nakup: fond plati prodejci, ktery jako necleen odvede clo;
    nakoupene mnozstvi se rozdeli clenum pomerne k deficitu. Kupec zaplati nejvys to, co ma,
    fond tedy nejde do minusu.
    """
    C = state["players"]["C"]
    tgt, res = d["target"], d["res"]
    price = float(d["price"])
    want = float(d["qty"]) * trade_mult
    if not C.get("active") or tgt in (C.get("members") or []) or price <= 0:
        return 0.0
    rate = _tariff_for(state, tgt)
    surplus, deficit = _union_pool(state, res, needs, imports, exports)
    te = ent(state, tgt)
    shares = {}
    if d["direction"] == "npc_buys":
        pool = sum(surplus.values())
        qty = min(want, pool, max(0.0, float(te["wealth"])) / (price * (1.0 + rate)))
        if qty <= 1e-9:
            return 0.0
        value = qty * price
        tariff = rate * value
        te["wealth"] = float(te["wealth"]) - value - tariff
        C["wealth"] = float(C["wealth"]) + value
        imports[tgt][res] += qty
        for m, over in surplus.items():
            q = qty * over / pool
            exports[m][res] += q
            shares[m] = round(q, 4)
            if res == GOODS:
                state["_goods_sold"][m] = state["_goods_sold"].get(m, 0.0) + q
    else:
        pool = sum(deficit.values())
        qty = min(want, pool, max(0.0, float(C["wealth"])) / price)
        if qty <= 1e-9:
            return 0.0
        value = qty * price
        tariff = rate * value
        C["wealth"] = float(C["wealth"]) - value
        te["wealth"] = float(te["wealth"]) + value - tariff
        exports[tgt][res] += qty
        for m, short in deficit.items():
            q = qty * short / pool
            imports[m][res] += q
            shares[m] = round(q, 4)
        if res == GOODS:
            state["_goods_sold"][tgt] = state["_goods_sold"].get(tgt, 0.0) + qty
    if tariff > 0:
        _collect_tariff(state, tgt, tariff)
    trace.add("7.2 obchod Unie za cleny",
              {"deal_id": d["id"], "cil": tgt, "res": res, "smer": d["direction"]},
              {"qty": round(qty, 3), "objem": round(value, 3), "clo": round(tariff, 4),
               "clo_plati": tgt, "podily_clenu": shares, "fond": round(float(C["wealth"]), 4)})
    return value


def _tariff_for(state, payer) -> float:
    """7.2 a 3.3a (v1.10): sazba cla pro platce; kdo valku vyhlasil, plati po dobu valky +0.10."""
    rate = tariff_rate(state)
    if payer in ("A", "B") and any(w["aggressor"] == payer for w in state.get("wars", [])):
        rate += WAR_TARIFF_EXTRA
    return rate


def _pact_holder(state, nid):
    """3.2 (v1.10): kdo drzi pakt nad NPC (NPC ma nejvys jeden), jinak None."""
    return next((d["owner"] for d in state["deals"] if d["type"] == "protect" and d["target"] == nid), None)


def _war_between(state, a, b):
    return next((w for w in state.get("wars", []) if {w["aggressor"], w["defender"]} == {a, b}), None)


def _war_allowed(state, a, b):
    """3.3a (v1.10): valku nelze vyhlasit v tazich 1 az 9 ani 88 az 90, ani kdyz uz probiha."""
    turn = int(state["meta"]["turn"])
    if turn <= 9 or 88 <= turn <= 90:
        return False, "valku nelze vyhlasit v tazich 1 az 9 ani 88 az 90"
    if _war_between(state, a, b):
        return False, "valka uz probiha"
    return True, ""


def _declare_war(state, aggressor, defender, how, over, events, trace) -> None:
    m = state["minsky"]
    war = {"id": "w%d" % int(m.get("next_war_id", 1)), "aggressor": aggressor, "defender": defender,
           "since": int(state["meta"]["turn"]), "how": how, "over": over}
    m["next_war_id"] = int(m.get("next_war_id", 1)) + 1
    state.setdefault("wars", []).append(war)
    events.append({"kind": "war_declared", "war_id": war["id"], "aggressor": aggressor,
                   "defender": defender, "how": how, "over": over})
    trace.add("3.3a vyhlaseni valky", {"agresor": aggressor, "obrance": defender, "jak": how, "npc": over},
              {"war_id": war["id"], "od_tahu": war["since"]})


def _end_war(state, war, how, loser, winner, events, trace) -> None:
    """3.3a (v1.10): konec valky ustupem, kapitulaci nebo remizou (oba power 0)."""
    state["wars"] = [w for w in state.get("wars", []) if w["id"] != war["id"]]
    out = {"war_id": war["id"], "jak": how, "porazeny": loser, "vitez": winner}
    if how == "primeri":
        pred, po = {}, {}
        for x in (war["aggressor"], war["defender"]):
            pred[x] = round(sum(float(nn["influence"].get(x, 0.0)) for nn in state["npc"].values()), 3)
            for nn in state["npc"].values():
                nn["influence"][x] = float(nn["influence"].get(x, 0.0)) * (1.0 - WAR_CEASEFIRE_INFLUENCE)
            po[x] = round(sum(float(nn["influence"].get(x, 0.0)) for nn in state["npc"].values()), 3)
        out.update({"vliv_pred": pred, "vliv_po": po})
    elif how == "ustup":
        before = sum(float(x["influence"].get(loser, 0.0)) for x in state["npc"].values())
        for x in state["npc"].values():
            x["influence"][loser] = float(x["influence"].get(loser, 0.0)) * (1.0 - WAR_RETREAT_INFLUENCE)
        out.update({"vliv_pred": round(before, 3), "vliv_po": round(
            sum(float(x["influence"].get(loser, 0.0)) for x in state["npc"].values()), 3)})
    elif how == "kapitulace":
        pacts = [d["id"] for d in state["deals"] if d["type"] == "protect" and d["owner"] == loser]
        state["deals"] = [d for d in state["deals"] if d["id"] not in pacts]
        for x in state["npc"].values():
            x["influence"][loser] = float(x["influence"].get(loser, 0.0)) * (1.0 - WAR_CAPITULATION_INFLUENCE)
        lp, wp = state["players"][loser], state["players"][winner]
        take = float(lp["wealth"]) * WAR_CAPITULATION_WEALTH
        lp["wealth"] = float(lp["wealth"]) - take
        wp["wealth"] = float(wp["wealth"]) + take
        out.update({"zrusene_pakty": pacts, "wealth_vitezi": round(take, 3)})
    events.append({"kind": "war_end", "war_id": war["id"], "how": how, "loser": loser, "winner": winner,
                   "between": [war["aggressor"], war["defender"]]})
    trace.add("3.3a konec valky", {"agresor": war["aggressor"], "obrance": war["defender"]}, out)


def step_wars(state, trace, events) -> None:
    """3.3a (v1.10): za kazdy tah valky oba power -10 a wealth -5 %, nezavisla NPC vliv -1 u obou;
    power 0 znamena kapitulaci (oba 0: remiza bez vitaze)."""
    turn = int(state["meta"]["turn"])
    for war in list(state.get("wars", [])):
        a, d = war["aggressor"], war["defender"]
        # 3.3a (1b): nabidka primeri bez odpovedi do nasledujiciho tahu propadne, valka pokracuje
        for p, t in list((war.get("cancel") or {}).items()):
            if int(t) < turn:
                del war["cancel"][p]
                events.append({"kind": "war_cancel_expired", "player": p, "war_id": war["id"]})
                trace.add("3.3a nabidka primeri propadla", {"player": p, "war_id": war["id"], "z_tahu": int(t)},
                          {"valka": "pokracuje"})
        before = {x: (float(state["players"][x]["power"]), float(state["players"][x]["wealth"])) for x in (a, d)}
        for x in (a, d):
            p = state["players"][x]
            p["power"] = max(0.0, float(p["power"]) - WAR_POWER_LOSS)
            p["wealth"] = float(p["wealth"]) * (1.0 - WAR_WEALTH_LOSS)
        loss = {a: 0.0, d: 0.0}
        for nn in state["npc"].values():
            if nn["status"] == "independent":
                for x, drop in ((a, WAR_INFLUENCE_AGGRESSOR), (d, WAR_INFLUENCE_DEFENDER)):
                    old = float(nn["influence"].get(x, 0.0))
                    nn["influence"][x] = max(0.0, old - drop)
                    loss[x] += old - nn["influence"][x]
        trace.add("3.3a valka", {"war_id": war["id"], "agresor": a, "obrance": d,
                                 "vliv_ubytek": {k: round(v, 3) for k, v in loss.items()}},
                  {x: {"power_pred": round(before[x][0], 3), "power_po": round(float(state["players"][x]["power"]), 3),
                       "wealth_pred": round(before[x][1], 3), "wealth_po": round(float(state["players"][x]["wealth"]), 3)}
                   for x in (a, d)})
        pa, pd = float(state["players"][a]["power"]), float(state["players"][d]["power"])
        if pa <= 0 and pd <= 0:
            _end_war(state, war, "remiza", None, None, events, trace)
        elif pa <= 0:
            _end_war(state, war, "kapitulace", a, d, events, trace)
        elif pd <= 0:
            _end_war(state, war, "kapitulace", d, a, events, trace)


def _war_trade_mult(state, a, b) -> float:
    """3.3a (v1.10): za valky obchod hrace s NPC ve sfere nepritele x0.5."""
    for x, y in ((a, b), (b, a)):
        if x in ("A", "B") and y in state["npc"]:
            enemy = "B" if x == "A" else "A"
            if _war_between(state, x, enemy) and state["npc"][y]["status"] == "sphere_%s" % enemy:
                return WAR_SPHERE_TRADE
    return 1.0


COMPETING = {("trade_offer", "trade_offer"), ("protect", "protect"), ("invade", "invade"),
             ("admit", "protect"), ("protect", "admit")}
COMPETITION_REASON = "NPC dalo přednost nabídce druhé strany"


def _competition_score(state, npcdata, act) -> float:
    atype, nid, pid = act["type"], act["target"], act["player"]
    params, ratio, direction = {}, None, None
    if atype == "trade_offer" and act.get("res") in TRADEABLES:
        mp = market_price(state, act["res"])
        price = float(act.get("price_per_unit") or 0.0)
        ratio = price / mp if mp > 0 else 1.0
        direction = "npc_sells" if _npc_balance_for_trade(state, nid, act["res"]) > 0 else "npc_buys"
        params = {"res": act["res"], "qty": act.get("qty"), "price": price}
    return _npc_score(state, npcdata, pid, nid, atype, params, ratio, direction)[1]


def _competition(state, npcdata, actions, valid, events, trace) -> set:
    """3.4a (v1.10): soutez hracu o totez NPC v jednom tahu. Vraci indexy prohranych akci.

    Konfliktni dvojice: trade_offer na stejnou surovinu, protect proti protect, invade proti invade,
    admit proti protect. Vyssi skore podle 3.4 jde do normalniho vyhodnoceni; pri remize hod d100
    z rng_seed + turn + CRC32(ID): do 50 vyhrava akce drive v seznamu, jinak pozdejsi.
    """
    turn = int(state["meta"]["turn"])
    losers = set()
    by_target = {}
    for i in valid:
        act = actions[i]
        if act.get("target") in state["npc"] and act.get("type") in ("trade_offer", "protect", "invade", "admit"):
            by_target.setdefault(act["target"], []).append(i)
    for nid in sorted(by_target, key=_npc_key):
        idxs = by_target[nid]
        for x in range(len(idxs)):
            for y in range(x + 1, len(idxs)):
                i, j = idxs[x], idxs[y]
                if i in losers or j in losers:
                    continue
                a, b = actions[i], actions[j]
                if a["player"] == b["player"] or (a["type"], b["type"]) not in COMPETING:
                    continue
                if a["type"] == "trade_offer" and a.get("res") != b.get("res"):
                    continue
                sa, sb = _competition_score(state, npcdata, a), _competition_score(state, npcdata, b)
                if abs(sa - sb) < 1e-9:
                    roll = _decision_roll(state, nid)
                    win, how = (i if roll <= 50 else j), "remiza, hod %d" % roll
                else:
                    win, how = (i if sa > sb else j), "skore"
                lose = j if win == i else i
                losers.add(lose)
                la = actions[lose]
                state.setdefault("private_log", {"A": [], "B": [], "C": []}).setdefault(la["player"], []).append(
                    {"turn": turn, "npc": nid, "action": la["type"], "outcome": "prednost_druhe_strany",
                     "reason": COMPETITION_REASON, "counter": None})
                events.append({"kind": "competition_lost", "private": True, "player": la["player"],
                               "npc": nid, "action": la["type"], "winner": actions[win]["player"]})
                trace.add("3.4a soutez o cil", {"npc": nid, "akce": [a["player"] + " " + a["type"],
                                                                     b["player"] + " " + b["type"]]},
                          {"skore": [round(sa, 2), round(sb, 2)], "rozhodl": how,
                           "vitez": actions[win]["player"], "prohral": la["player"], "log": COMPETITION_REASON})
    return losers


def _loan_counter_match(state, pid, nid, amount) -> bool:
    """3.4 (v1.7): loan s castkou podle protinavrhu na totez NPC projde bez hodu."""
    turn = int(state["meta"]["turn"])
    for c in list(state.get("counter_offers", [])):
        if (c.get("type") == "loan" and c.get("player") == pid and c.get("npc") == nid
                and abs(float(c["amount"]) - amount) < 1e-6 and turn <= int(c["expires"])):
            state["counter_offers"].remove(c)
            return True
    return False


def _players_sanctioned(state) -> bool:
    """3.2 (v1.6): bezi sankce mezi hraci A a B?"""
    return any(d["type"] == "pressure" and d["owner"] in ("A", "B") and d["target"] in ("A", "B")
               for d in state["deals"])


def _do_loan(state, pid, target, amount, events, trace) -> None:
    """Provedeni pujcky (3.2) vcetne vlivu z pohledavky (4.4)."""
    player = state["players"][pid]
    n = state["npc"][target]
    player["wealth"] = float(player["wealth"]) - amount
    n["wealth"] = float(n["wealth"]) + amount
    owed = amount * 1.2
    n["debt"][pid] = float(n["debt"].get(pid, 0.0)) + owed
    gain = owed / 20.0
    if pid in ("A", "B"):
        if is_fallen(state, target):
            gain *= 0.1
        gain = add_influence(state, target, pid, gain)
    events.append({"kind": "loan_given", "player": pid, "target": target,
                   "amount": amount, "debt": n["debt"][pid]})
    trace.add("3.2 loan / 4.4 vliv z pohledavky",
              {"player": pid, "target": target, "amount": amount},
              {"debt": n["debt"][pid], "influence_gain": gain})


def _accept_offer(state, npcdata, pid, oid, events, trace) -> None:
    """3.5 (v1.6): prijeti nabidky NPC bez vyhodnoceni podle 3.4."""
    turn = int(state["meta"]["turn"])
    offers = state.get("offers", [])
    offer = next((o for o in offers if o["offer_id"] == oid and o["player"] == pid), None)
    if offer is None or turn > int(offer["expires"]):
        events.append({"kind": "action_invalid", "player": pid, "type": "accept_offer",
                       "reason": "nabidka neexistuje nebo propadla"})
        return
    nid = offer["npc"]
    if offer["type"] == "sell":
        deal = {"id": _new_deal_id(state), "type": "trade", "owner": pid, "target": nid,
                "res": offer["res"], "qty": float(offer["qty"]), "price": float(offer["price"]),
                "direction": "npc_sells", "since": turn, "one_shot": True, "offer_id": oid}
        state["deals"].append(deal)
    elif offer["type"] == "loan_request":
        if float(state["players"][pid]["wealth"]) < float(offer["amount"]):
            events.append({"kind": "action_invalid", "player": pid, "type": "accept_offer",
                           "reason": "nedostatek wealth"})
            return
        _do_loan(state, pid, nid, float(offer["amount"]), events, trace)
    elif offer["type"] == "protect_request":
        if pid not in ("A", "B") or _pact_holder(state, nid) is not None:
            events.append({"kind": "action_invalid", "player": pid, "type": "accept_offer",
                           "reason": "pakt nelze uzavrit"})
            return
        state["deals"].append({"id": _new_deal_id(state), "type": "protect", "owner": pid,
                               "target": nid, "since": turn, "offer_id": oid})
    state["offers"] = [o for o in offers if o["offer_id"] != oid]
    state["minsky"]["offer_ignored"].setdefault(pid, {})[nid] = 0
    events.append({"kind": "offer_accepted", "player": pid, "npc": nid, "offer": dict(offer)})
    trace.add("3.5 accept_offer", {"player": pid, "offer_id": oid, "type": offer["type"]},
              {"npc": nid})


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
    """Bilance NPC u statku pred obchodem. Urcuje smer obchodu (3.2)."""
    return supply_of(state, nid, res) - float(current_need(state, nid).get(res, 0.0))


def apply_actions(state, npcdata, actions, rng, trace: Trace) -> list[dict]:
    """Provede akce hracu. Vraci seznam udalosti pro rozhodciho.

    `actions` je seznam {"player": "A", "type": "loan", ...}, uz overeny
    rozhodcim. Engine presto kontroluje tvrde podminky, protoze aritmetika
    a prahy patri sem (pravidla cast 9).
    """
    events: list[dict] = []
    counts: dict[str, int] = {}

    # limit akci predem; do souteze o cil (3.4a) vstupuji jen akce v limitu
    valid = []
    for idx, act in enumerate(actions):
        pid = act.get("player")
        if pid not in ("A", "B", "C"):
            continue
        counts[pid] = counts.get(pid, 0) + 1
        if counts[pid] > ACTION_LIMIT[pid]:
            events.append({"kind": "action_over_limit", "player": pid, "type": act.get("type")})
            continue
        valid.append(idx)
    losers = _competition(state, npcdata, actions, valid, events, trace)
    # 3.3 (v1.10): invaze na NPC, o jehoz pakt se tento tah uchazi druhy hrac, az po paktech
    protect_by = {(actions[i]["player"], actions[i].get("target")) for i in valid
                  if actions[i].get("type") == "protect" and i not in losers}

    def deferred(i):
        act = actions[i]
        other = "B" if act["player"] == "A" else "A"
        return 1 if act.get("type") == "invade" and (other, act.get("target")) in protect_by else 0

    for idx in sorted(valid, key=lambda i: (deferred(i), i)):
        if idx in losers:
            continue
        act = actions[idx]
        pid = act["player"]
        atype = act.get("type")
        player = state["players"][pid]
        target = act.get("target")

        # --- trade_offer -------------------------------------------------
        if atype == "trade_offer":
            if pid == "C":
                _union_trade_offer(state, npcdata, act, events, trace)  # 7.2 (v1.9)
                continue
            res = act.get("res")
            qty = float(act.get("qty", 0))
            price = float(act.get("price_per_unit", 0))
            # 3.2 (v1.6): cilem muze byt i druhy hrac
            to_player = pid in ("A", "B") and target in ("A", "B") and target != pid
            if (target not in state["npc"] and not to_player) or res not in TRADEABLES or qty <= 0:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "neznamy cil nebo surovina"})
                continue
            mp = market_price(state, res)
            lo, hi = 0.7 * mp, 1.5 * mp
            if not to_player and is_fallen(state, target):
                lo = 1.3 * mp  # 7a: trade_offer s padlou risi jen za >= 1.3x
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
                               "res": res, "reason": "cil nema prebytek ani deficit"})
                continue
            offered_qty = qty
            qty = min(qty, abs(bal))
            if not to_player:
                if _counter_match(state, pid, target, res, offered_qty, price):
                    trace.add("3.4 protinavrh prijat", {"player": pid, "npc": target, "res": res},
                              {"qty": offered_qty, "price": price})
                else:
                    outcome = _npc_decide(state, npcdata, pid, target, "trade_offer",
                                          {"res": res, "qty": offered_qty, "price": price},
                                          price_ratio=(price / mp) if mp > 0 else 1.0,
                                          direction=direction, events=events, trace=trace)
                    if outcome == "podminka":
                        qty = qty * 0.7  # 3.4: objem -30 %
                    elif outcome in ("protinavrh", "odmitnuto"):
                        continue
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
                               "reason": "padla rise neprijima pujcku"})
                continue
            if float(player["wealth"]) < amount:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "nedostatek wealth"})
                continue
            if _loan_counter_match(state, pid, target, amount):
                outcome = "prijato"
                trace.add("3.4 protinavrh pujcky prijat", {"player": pid, "npc": target},
                          {"amount": amount})
            else:
                outcome = _npc_decide(state, npcdata, pid, target, "loan", {"amount": amount},
                                      events=events, trace=trace)
            if outcome == "podminka":
                amount = amount * 0.7  # 3.4: pujcka -30 %
            elif outcome in ("protinavrh", "odmitnuto"):
                continue
            _do_loan(state, pid, target, amount, events, trace)

        # --- pressure ------------------------------------------------------
        elif atype == "pressure":
            to_player = pid in ("A", "B") and target in ("A", "B") and target != pid
            if target not in state["npc"] and not to_player:
                continue
            if _active_deal(state, pid, target, "pressure"):
                continue
            removed = []
            if not to_player:
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
                      {"deal_id": deal["id"], "cancelled": removed, "mezi_hraci": to_player})
            if not to_player:
                _mark_fallen_touched(state, target)

        # --- protect --------------------------------------------------------
        elif atype == "protect":
            if target not in state["npc"]:
                continue
            if is_fallen(state, target):
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "padla rise neprijima pakt"})
                continue
            if _active_deal(state, pid, target, "protect"):
                continue
            holder = _pact_holder(state, target)
            if holder is not None:
                # 3.2 (v1.10): NPC ma nejvys jeden pakt, cizi pakt = vyrazeni bez hodu
                events.append({"kind": "action_invalid", "player": pid, "type": atype, "target": target,
                               "reason": "NPC je pod paktem %s" % holder})
                continue
            if pid in ("A", "B"):
                outcome = _npc_decide(state, npcdata, pid, target, "protect", {},
                                      events=events, trace=trace)
                if outcome in ("protinavrh", "odmitnuto"):
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

        # --- invest_tech / invest_law / invest_industry ------------------------
        elif atype in ("invest_tech", "invest_law", "invest_industry"):
            field = {"invest_tech": "tech", "invest_law": "law",
                     "invest_industry": "industry"}[atype]
            cost = COST[atype]
            tgt = target or pid
            if tgt == pid:
                if pid == "C":
                    continue  # Unie nema vlastni law, tech ani industry
                e = player
            elif tgt in state["npc"]:
                e = state["npc"][tgt]
                st = e.get("status")
                allowed = st in (f"sphere_{pid}", "union") if pid in ("A", "B") else True
                if pid == "C":
                    allowed = tgt in state["players"]["C"]["members"] or \
                              tgt in state["players"]["C"]["candidates"]
                    cost = cost / 2.0  # pravidlo 7.2: polovicni cena
                if not allowed:
                    events.append({"kind": "action_invalid", "player": pid, "type": atype,
                                   "reason": "cil mimo sferu nebo Unii"})
                    continue
            else:
                continue
            if atype == "invest_industry" and float(e.get("law") or 0.0) < 4.0:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "law cile pod 4"})
                continue
            if float(player["wealth"]) < cost:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "nedostatek wealth"})
                continue
            player["wealth"] = float(player["wealth"]) - cost
            before = float(e.get(field) or 0.0)
            if atype == "invest_industry":
                gain = 0.3 * (float(e["law"]) / 5.0)   # 3.2 (v1.2)
            else:
                gain = 0.3
            e[field] = clamp(before + gain, 0.0, 10.0)
            events.append({"kind": f"{atype}_done", "player": pid, "target": tgt,
                           field: e[field]})
            trace.add(f"3.2 {atype}", {"player": pid, "target": tgt, "cost": cost},
                      {field: e[field], "from": before})

        # --- invest_prod (3.2, v1.8) -------------------------------------------
        elif atype == "invest_prod":
            res = act.get("res")
            cost = COST["invest_prod"]
            tgt = target or pid
            if res not in BASE_RESOURCES:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "takto lze zvysit jen oil, grain nebo metal"})
                continue
            if tgt == pid:
                if pid == "C":
                    continue  # Unie nema vlastni produkci
                e = player
            elif tgt in state["npc"]:
                e = state["npc"][tgt]
                allowed = e.get("status") in (f"sphere_{pid}", "union") if pid in ("A", "B") else True
                if pid == "C":
                    allowed = tgt in state["players"]["C"]["members"] or \
                              tgt in state["players"]["C"]["candidates"]
                    cost = cost / 2.0  # 7.2: polovicni cena
                if not allowed:
                    events.append({"kind": "action_invalid", "player": pid, "type": atype,
                                   "reason": "cil mimo sferu nebo Unii"})
                    continue
            else:
                continue
            if float(e.get("prod", {}).get(res, 0.0)) <= 0:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "cil tento zdroj neprodukuje"})
                continue
            if float(e.get("tech") or 0.0) < 3.0:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "tech cile pod 3"})
                continue
            if float(player["wealth"]) < cost:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "nedostatek wealth"})
                continue
            player["wealth"] = float(player["wealth"]) - cost
            before = float(e["prod"][res])
            e["prod"][res] = before + 1.0
            events.append({"kind": "invest_prod_done", "player": pid, "target": tgt, "res": res,
                           "prod": e["prod"][res]})
            trace.add("3.2 invest_prod", {"player": pid, "target": tgt, "res": res, "cost": cost},
                      {"prod": e["prod"][res], "from": before})

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
            # 3.2 (v1.10): arm s parametrem amount, power += amount / 1.6, nejvys 40 wealth
            try:
                amount = float(act.get("amount", COST["arm"]))
            except (TypeError, ValueError):
                amount = -1.0
            if pid == "C" or not (0.0 < amount <= ARM_MAX):
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "arm jen A a B, amount od 0 do 40"})
                continue
            if float(player["wealth"]) < amount:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "nedostatek wealth"})
                continue
            before = float(player["power"])
            player["wealth"] = float(player["wealth"]) - amount
            player["power"] = before + amount / ARM_RATIO
            events.append({"kind": "arm", "player": pid, "power": player["power"]})
            trace.add("3.2 arm", {"player": pid, "amount": amount},
                      {"power": player["power"], "from": before, "gain": round(amount / ARM_RATIO, 4)})

        # --- cancel -------------------------------------------------------------
        elif atype == "cancel":
            did = act.get("deal_id")
            war = next((w for w in state.get("wars", [])
                        if w["id"] == did and pid in (w["aggressor"], w["defender"])), None)
            if war is not None:
                # 3.3a (v1.10 dodatek): cancel od obou ve stejnem tahu nebo v tazich po sobe = primeri;
                # samotny cancel je nabidka; neprijata propadne bez nasledku (1b).
                # Ustup jen vyslovne: cancel s "retreat": true, valka konci okamzite.
                if act.get("retreat") is True or str(act.get("retreat")).lower() == "true":
                    _end_war(state, war, "ustup", pid, None, events, trace)
                    continue
                turn_now = int(state["meta"]["turn"])
                other = war["defender"] if pid == war["aggressor"] else war["aggressor"]
                pend = war.setdefault("cancel", {})
                if other in pend and int(pend[other]) >= turn_now - 1:
                    _end_war(state, war, "primeri", None, None, events, trace)
                else:
                    pend[pid] = turn_now
                    events.append({"kind": "war_cancel_offered", "player": pid, "war_id": war["id"]})
                    trace.add("3.3a cancel valky", {"player": pid, "war_id": war["id"]},
                              {"ceka_na": other, "do_tahu": turn_now + 1})
                continue
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
            _union_admit(state, npcdata, target, events, trace)

        # --- accept_offer (3.5, v1.6) -------------------------------------------------
        elif atype == "accept_offer":
            _accept_offer(state, npcdata, pid, act.get("offer_id"), events, trace)

        # --- declare_war (3.3a, v1.10) -----------------------------------------------
        elif atype == "declare_war":
            if pid not in ("A", "B") or target not in ("A", "B") or target == pid:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "valku lze vyhlasit jen druhemu hraci"})
                continue
            ok, reason = _war_allowed(state, pid, target)
            if not ok:
                events.append({"kind": "action_invalid", "player": pid, "type": atype, "reason": reason})
                continue
            _declare_war(state, pid, target, "vyhlaseni", None, events, trace)

        # --- set_tariff (jen Unie, 7.2, v1.9) ---------------------------------------
        elif atype == "set_tariff":
            C = state["players"]["C"]
            if pid != "C" or not C["active"]:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "clo nastavuje jen Unie"})
                continue
            try:
                rate = float(act.get("rate"))
            except (TypeError, ValueError):
                rate = -1.0
            steps = rate / TARIFF_STEP
            if not (0.0 <= rate <= TARIFF_MAX + 1e-9) or abs(steps - round(steps)) > 1e-6:
                events.append({"kind": "action_invalid", "player": pid, "type": atype,
                               "reason": "sazba mimo 0 az 0.20 po 0.05"})
                continue
            C["tariff_next"] = round(round(steps) * TARIFF_STEP, 2)
            events.append({"kind": "tariff_set", "player": "C", "rate": C["tariff_next"],
                           "from_turn": int(state["meta"]["turn"]) + 1})
            trace.add("7.2 set_tariff", {"rate": C["tariff_next"]},
                      {"dosud": C.get("tariff_rate"), "plati_od_tahu": int(state["meta"]["turn"]) + 1})

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

    _log_rejections(state, events)
    return events


REJECTION_KINDS = ("trade_rejected", "action_invalid", "invade_blocked", "action_over_limit", "union_rejected")


def _log_rejections(state, events) -> None:
    """3.4 (v1.10.2): kazde vyrazeni akce enginem jde do soukromeho logu hrace s duvodem."""
    turn = int(state["meta"]["turn"])
    plog = state.setdefault("private_log", {"A": [], "B": [], "C": []})
    for e in events:
        if e.get("kind") not in REJECTION_KINDS:
            continue
        pid = e.get("player") or ("C" if e.get("kind") == "union_rejected" else None)
        if pid not in ("A", "B", "C"):
            continue
        plog.setdefault(pid, []).append({
            "turn": turn, "npc": e.get("target") or e.get("npc"),
            "action": e.get("type") or ("admit" if e.get("kind") == "union_rejected" else e.get("kind")),
            "outcome": "vyrazeno", "reason": e.get("reason") or e.get("kind"), "counter": None})


def _mark_fallen_touched(state, target) -> None:
    """Pravidlo 7a: kdo padlou risi behem boomu tlacil, nezisak ji do Unie."""
    if is_fallen(state, target) and state["phase"] in ("boom", "euphoria",
                                                       "overtrading", "distress", "panic"):
        if target not in state["minsky"]["fallen_touched"]:
            state["minsky"]["fallen_touched"].append(target)


def _register_invasion(state, npcdata, pid, target, events, trace) -> None:
    """Pravidlo 3.3. Podminky, valka s ochrancem, pocitadlo tahu."""
    if target in ("A", "B", "C"):
        events.append({"kind": "action_invalid", "player": pid, "type": "invade",
                       "reason": "hrace nelze dobyt ani okupovat"})
        return
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
    # 3.3a (v1.10): utok na NPC pod paktem druheho hrace vyhlasi valku automaticky, invaze nepostupuje
    other = "B" if pid == "A" else "A"
    if _active_deal(state, other, target, "protect"):
        if _war_between(state, pid, other) is None:
            ok, reason = _war_allowed(state, pid, other)
            if not ok:
                events.append({"kind": "invade_blocked", "player": pid, "target": target,
                               "reason": "NPC je pod paktem %s a %s" % (other, reason)})
                return
            _declare_war(state, pid, other, "utok na NPC pod paktem", target, events, trace)
        else:
            events.append({"kind": "invade_blocked", "player": pid, "target": target,
                           "reason": "NPC je pod paktem %s, valka probiha" % other})
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

def _withdraw_protect(state, deal, events, trace: Trace) -> None:
    """3.2 (v1.4): pakt zanika, kdyz sila ochrance klesne na 0."""
    state["deals"] = [d for d in state["deals"] if d["id"] != deal["id"]]
    events.append({"kind": "protect_withdrawn", "player": deal["owner"], "target": deal["target"],
                   "zprava": "%s stahuje posadky z %s" % (deal["owner"], deal["target"])})
    trace.add("3.2 zanik paktu", {"owner": deal["owner"], "target": deal["target"]},
              {"deal_id": deal["id"], "duvod": "sila ochrance 0"})


def upkeep_deals(state, trace: Trace, events: list) -> None:
    for d in list(state["deals"]):
        owner = d["owner"]
        tgt = d["target"]
        player = state["players"].get(owner)
        if d["type"] == "pressure" and tgt in ("A", "B"):
            # 3.2 (v1.6): sankce mezi hraci stoji oba 1 wealth za tah
            for x in (owner, tgt):
                state["players"][x]["wealth"] = max(0.0, float(state["players"][x]["wealth"]) - 1.0)
            trace.add("3.2 pressure mezi hraci", {"owner": owner, "target": tgt},
                      {"A": state["players"]["A"]["wealth"], "B": state["players"]["B"]["wealth"]})
            continue
        if tgt not in state["npc"]:
            continue
        n = state["npc"][tgt]
        if d["type"] == "protect":
            if player is None:
                continue
            if float(player["power"]) <= 0.0:
                _withdraw_protect(state, d, events, trace)
                continue
            player["power"] = max(0.0, float(player["power"]) - 2.0)
            n["power"] = float(n["power"]) + 2.0
            if owner in ("A", "B"):
                mult = 0.1 if n.get("kind") == "fallen" else 1.0
                add_influence(state, tgt, owner, 2.0 * mult)
            n["law"] = clamp(float(n["law"]) - 0.2, 0.0, 10.0)
            trace.add("3.2 protect upkeep", {"owner": owner, "target": tgt},
                      {"npc_power": n["power"], "npc_law": n["law"],
                       "owner_power": player["power"]})
            if float(player["power"]) <= 0.0:
                # Posledni udrzba srazila silu na 0: pakt po ucinku tohoto tahu zanika (K6).
                _withdraw_protect(state, d, events, trace)
        elif d["type"] == "pressure":
            if player is None:
                continue
            player["wealth"] = max(0.0, float(player["wealth"]) - 1.0)
            n["wealth"] = max(0.0, float(n["wealth"]) - 3.0)
            other = "B" if owner == "A" else "A"
            if owner in ("A", "B"):
                mult = 0.1 if n.get("kind") == "fallen" else 1.0
                add_influence(state, tgt, other, 1.0 * mult)
                state["minsky"].setdefault("pressure_log", []).append(
                    {"turn": state["meta"]["turn"], "owner": owner, "target": tgt})
            trace.add("3.2 pressure upkeep", {"owner": owner, "target": tgt},
                      {"npc_wealth": n["wealth"], f"influence_{other}": n["influence"][other]})


# --------------------------------------------------------------------------
# 4.1 zdroje a obchod
# --------------------------------------------------------------------------

def _npc_key(sid: str):
    return int(sid[1:]) if is_npc(sid) else -1


def _crossings_table(state, npcdata) -> dict:
    """4.1a (v1.5): nejkratsi cesta mezi dvema NPC po adjacency (BFS).

    Cesta vede jen pres NPC, pres uzemi A a B tranzit nevede. Sousede se prochazeji
    v poradi ID, takze pri vice nejkratsich cestach vyhraje prvni nalezena (M4).
    Vraci {(prodejce, kupec): (pocet prejezdu, [tranzitni staty])}.
    """
    npcs = npc_ids(state)
    table = {}
    for src in npcs:
        prev = {src: None}
        queue = [src]
        while queue:
            cur = queue.pop(0)
            for nb in sorted(neighbours(npcdata, cur), key=_npc_key):
                if nb in prev or nb not in state["npc"]:
                    continue
                prev[nb] = cur
                queue.append(nb)
        for dst in npcs:
            if dst == src or dst not in prev:
                continue
            path = []
            x = prev[dst]
            while x is not None and x != src:
                path.append(x)
                x = prev[x]
            path.reverse()
            table[(src, dst)] = (len(path), path)
    return table


def _auto_market(state, npcdata, resources, needs, imports, exports, trace: Trace):
    """4.1a (v1.5): globalni automaticky trh s tranzitem.

    Paruje kohokoli s kymkoli. Mezi dvema NPC plati kupec trzni cenu x (1 + 0.1 x
    pocet prejezdu), prejezd je cizi stat na nejkratsi ceste; vic nez 3 prejezdy
    se neparuji. Kazdy tranzitni stat dostane polovinu prirazky za svuj prejezd,
    druha polovina propada jako naklad dopravy a prodejce dostane zakladni cenu (M2).
    Hraci A a B maji pausal 1 prejezd bez tranzitniho prijmu (v1.9). Dvojice se radi
    podle efektivni ceny pro kupce vcetne cla, dosavadni kriteria plati pri shode ceny.
    Prodejce nabizi vse nad rezervu 3 tahu spotreby (I2). Kupec poptava deficit
    toku a doplneni rezervy; doplnuje jen stat mimo bidu s wealth >= 15 a jen
    z bohatstvi nad 15 (4.1c, M5). Padla rise prodava za 1.3x, prirazka se
    pocita z teto ceny (M3). Orit se automaticky neobchoduje.

    Vraci (objem NPC s NPC, objem hracu {A, B}, objem goods, dvojice).
    """
    last_pairs = {tuple(sorted(p)) for p in state["minsky"].get("npc_trade_last", [])}
    new_pairs: list[list[str]] = []
    vol_npc = 0.0
    vol_players = {"A": 0.0, "B": 0.0}
    goods_volume = 0.0
    npcs = npc_ids(state)
    traders = npcs + ["A", "B"]
    routes = _crossings_table(state, npcdata)
    transit = state.setdefault("_transit_income", {})

    rate = tariff_rate(state)
    for res in resources:
        if res == "orit":
            continue  # 4.1a: orit se automaticky neobchoduje
        spec = state.get("_spec_offer", {}) if res == GOODS else {}
        offer, d_flow, d_refill = {}, {}, {}
        for i in traders:
            e = ent(state, i)
            need = float(needs[i].get(res, 0.0))
            bal = supply_of(state, i, res) - need + imports[i][res] - exports[i][res]
            stock = float(e["stock"].get(res, 0.0))
            reserve = RESERVE_TURNS * need
            if i in ("A", "B"):
                # 4.1a (v1.10.2): hrac prodava jen kladny rozdil vlastni efektivni produkce a potreby;
                # cileny dovoz ani zasoba se neprodavaji, uz cilene prodane mnozstvi se odecita
                own = max(0.0, supply_of(state, i, res) - need - exports[i][res])
                offer[i] = own
            else:
                offer[i] = max(0.0, stock + bal - reserve)
            if spec.get(i, 0.0) > 0:
                # 4.0 a 4.1a (v1.9): spekulativni nabidka jde na trh vzdy, i pod rezervou (hrac jen z vlastni vyroby)
                cap = own if i in ("A", "B") else max(0.0, stock + bal)
                offer[i] = max(offer[i], min(spec[i], cap))
            d_flow[i] = max(0.0, -bal)
            can_refill = float(e["wealth"]) >= REFILL_MIN_WEALTH  # 4.1c (v1.6): jen pri wealth >= 25
            d_refill[i] = max(0.0, reserve - stock) if can_refill else 0.0

        pairs = []
        for seller in traders:
            if offer[seller] <= 0:
                continue
            for buyer in traders:
                if buyer == seller:
                    continue
                both_players = seller in ("A", "B") and buyer in ("A", "B")
                if both_players and (_players_sanctioned(state) or _war_between(state, "A", "B")):
                    continue  # 3.2 (v1.6): sankce mezi hraci prerusi jejich automaticky obchod
                dem = d_flow[buyer] + d_refill[buyer]
                if dem <= 0:
                    continue
                if seller in ("A", "B") or buyer in ("A", "B"):
                    # 4.1a (v1.9): pausal prejezdu hracu, prirazka propada, tranzit nikomu
                    k, path = (PLAYER_FLAT_CROSSINGS if PRICE_PAIRING else 0), []
                else:
                    route = routes.get((seller, buyer))
                    if route is None or route[0] > MAX_CROSSINGS:
                        continue
                    k, path = route
                key = tuple(sorted((seller, buyer)))
                if both_players:
                    same_sphere = False
                elif seller in ("A", "B"):
                    same_sphere = state["npc"][buyer]["status"] == "sphere_%s" % seller
                elif buyer in ("A", "B"):
                    same_sphere = state["npc"][seller]["status"] == "sphere_%s" % buyer
                else:
                    st_s = state["npc"][seller]["status"]
                    same_sphere = (st_s == state["npc"][buyer]["status"]
                                   and st_s in ("sphere_A", "sphere_B"))
                last = 0 if key in last_pairs else 1
                sphere = 0 if same_sphere else 1
                ids = (_npc_key(seller), _npc_key(buyer), seller, buyer)
                if PRICE_PAIRING:
                    # 4.1a (v1.9): od nejlevnejsi efektivni ceny pro kupce, dosavadni kriteria pri shode
                    mp = market_price(state, res)
                    payer = _tariff_payer(state, seller, buyer)
                    eff = mp * (1.0 + TRANSIT_SURCHARGE * k) + (_tariff_for(state, payer) * mp if payer == buyer else 0.0)
                    order = (round(eff, 9), last, sphere, -dem) + ids
                else:
                    order = (last, sphere, -dem, k) + ids   # parovani v1.8
                pairs.append((order, seller, buyer, k, tuple(path)))
        pairs.sort(key=lambda x: x[0])

        for _, seller, buyer, k, path in pairs:
            base = market_price(state, res)  # 7a (v1.6): padle rise na trhu za trzni cenu
            price = base * (1.0 + TRANSIT_SURCHARGE * k)
            if price <= 0 or offer[seller] <= 1e-9:
                continue
            # 7.2 (v1.8, v1.9): clo celni unie ze zakladni ceny podle platne sazby, plati necleen (S3)
            payer = _tariff_payer(state, seller, buyer)
            unit_tariff = _tariff_for(state, payer) * base if payer is not None else 0.0
            buyer_price = price + (unit_tariff if payer == buyer else 0.0)
            be = ent(state, buyer)
            q_flow = max(0.0, min(offer[seller], d_flow[buyer], max(0.0, float(be["wealth"])) / buyer_price))
            wealth_after = float(be["wealth"]) - q_flow * buyer_price
            q_ref = max(0.0, min(offer[seller] - q_flow, d_refill[buyer],
                                 max(0.0, wealth_after - REFILL_MIN_WEALTH) / buyer_price))
            war_mult = _war_trade_mult(state, seller, buyer)   # 3.3a (v1.10)
            q_flow, q_ref = q_flow * war_mult, q_ref * war_mult
            qty = q_flow + q_ref
            if qty <= 1e-9:
                continue
            pay = qty * price
            tariff = qty * unit_tariff
            to_seller = qty * base - (tariff if payer == seller else 0.0)
            per_transit = 0.5 * TRANSIT_SURCHARGE * base * qty
            se = ent(state, seller)
            se["wealth"] = float(se["wealth"]) + to_seller
            be["wealth"] = float(be["wealth"]) - pay - (tariff if payer == buyer else 0.0)
            if tariff > 0:
                _collect_tariff(state, payer, tariff)
            for t in path:
                state["npc"][t]["wealth"] = float(state["npc"][t]["wealth"]) + per_transit
                transit[t] = transit.get(t, 0.0) + per_transit
            exports[seller][res] += qty
            imports[buyer][res] += qty
            offer[seller] -= qty
            d_flow[buyer] -= q_flow
            d_refill[buyer] -= q_ref
            if seller in ("A", "B"):
                vol_players[seller] += pay
            if buyer in ("A", "B"):
                vol_players[buyer] += pay
            if seller in ("A", "B") and buyer in ("A", "B"):
                state["_ab_volume"] = state.get("_ab_volume", 0.0) + pay
                state["_ab_auto"] = state.get("_ab_auto", 0.0) + pay
            if is_npc(seller) and is_npc(buyer):
                vol_npc += pay
            if res == GOODS:
                goods_volume += pay
                sold_map = state.setdefault("_goods_sold", {})
                sold_map[seller] = sold_map.get(seller, 0.0) + qty
            pair = sorted((seller, buyer))
            if pair not in new_pairs:
                new_pairs.append(pair)
            trace.add("4.1a automaticky trh",
                      {"prodejce": seller, "kupec": buyer, "res": res},
                      {"qty": round(qty, 3), "z_toho_doplneni": round(q_ref, 3),
                       "cena": round(price, 3), "zaklad": round(base, 3),
                       "prejezdy": k, "tranzit": list(path),
                       "objem": round(pay, 3), "prodejci": round(to_seller, 3),
                       "tranzitu_kazdemu": round(per_transit, 4),
                       "clo": round(tariff, 4), "clo_plati": payer})

    return vol_npc, vol_players, goods_volume, new_pairs


def auto_trades_summary(items, pid: str) -> dict:
    """2 (v1.10.1): souhrn automatickeho trhu hrace z trace tahu.

    Pro kazdy statek prodano a nakoupeno: mnozstvi a prumerna cena (prodejce dostal zakladni cenu,
    kupec platil cenu s prirazkou a clo, pokud ho platil). Pouziva engine i run_turn.py pro tah 1.
    """
    book = {}
    for it in items or []:
        if it.get("rule") != "4.1a automaticky trh":
            continue
        inp, o = it["inputs"], it["outputs"]
        qty = float(o.get("qty") or 0.0)
        if qty <= 0:
            continue
        if inp.get("prodejce") == pid:
            side, money = "prodano", float(o.get("prodejci") or 0.0)
        elif inp.get("kupec") == pid:
            side, money = "nakoupeno", float(o.get("objem") or 0.0) + (
                float(o.get("clo") or 0.0) if o.get("clo_plati") == pid else 0.0)
        else:
            continue
        acc = book.setdefault(inp["res"], {}).setdefault(side, [0.0, 0.0])
        acc[0] += qty
        acc[1] += money
    return {res: {side: {"mnozstvi": round(q, 3), "prumerna_cena": round(m / q, 4)}
                  for side, (q, m) in sides.items()} for res, sides in sorted(book.items())}


def _union_market(state, resources, needs, imports, exports, trace: Trace) -> None:
    """7.2 vnitrni trh Unie: prebytek clena kryje deficit jineho clena zdarma.

    Probiha pred placenym parovanim 4.1a (C12, v1.2).
    """
    C = state["players"]["C"]
    if not (C["active"] and C["members"]):
        return
    for res in resources:
        moved = 0.0
        surplus, deficit = [], []
        for m in C["members"]:
            bal = supply_of(state, m, res) - float(needs[m].get(res, 0.0)) \
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
                moved += take
        # v1.9: mnozstvi a hodnota v trzni cene pro srovnani obchodu clenu mezi sebou a s necleny
        trace.add("7.2 vnitrni trh Unie", {"res": res, "members": list(C["members"])},
                  {"pokryto": True, "mnozstvi": round(moved, 4),
                   "hodnota": round(moved * market_price(state, res), 4)})


def step_resources(state, npcdata, trace: Trace, events: list) -> dict:
    """4.0, 4.1 a 4.1c: potreby, vyroba goods, obchod, zasoby a deficit.

    Postup v tahu:
      1. predbezne potreby: tovarny si rezervuji vstupy pro plnou vyrobu,
      2. obchody hracu (trade_offer), vnitrni trh Unie a automaticky trh 4.1a
         pro obili, ropu a kovy,
      3. vyroba goods: domacnosti maji prednost, prumysl bere zbytek vcetne
         zasob; coverage je nejmensi pomer dostupneho vstupu k potrebe (G1),
      4. konecne potreby podle skutecne vyroby, pak vnitrni trh Unie a 4.1a pro goods,
      5. vyrovnani (4.1c): prebytek jde do zasoby do stropu, deficit se kryje
         nejdriv ze zasoby, pokuta wealth -1 jen za zbytek, u oritu bez pokuty.

    Vraci mapu nepokryteho deficitu obili pro pravidlo 4.3.
    """
    turn = state["meta"]["turn"]
    ids = world_ids(state)
    imports = {i: {r: 0.0 for r in TRADEABLES} for i in ids}
    exports = {i: {r: 0.0 for r in TRADEABLES} for i in ids}
    trade_volume = 0.0
    trade_volume_weighted = 0.0   # metrika A, orit 2x (pravidlo 10.5)
    goods_volume = 0.0
    volume_by_player = {"A": 0.0, "B": 0.0, "C": 0.0}
    volume_by_npc = {i: 0.0 for i in npc_ids(state)}

    # pravidlo 5, faze crash: obchod sveta x0.5 po 6 tahu
    crash_turn = state["minsky"].get("crash_turn")
    trade_mult = 1.0
    if crash_turn is not None and state["phase"] in ("crash",) and turn - crash_turn < 6:
        trade_mult = 0.5

    state["_transit_income"] = {}
    state["_goods_sold"] = {}
    state["_union_tariff"] = {}
    # 4.0 (v1.7): poptavka po goods z bohatstvi na zacatku prepoctu zdroju (Q2)
    state["_need_wealth"] = {i: float(ent(state, i)["wealth"]) for i in ids}
    state["_ab_volume"] = 0.0
    state["_ab_auto"] = 0.0

    # 1. predbezne potreby
    potential = {i: goods_potential(ent(state, i)) for i in ids}
    # 4.0 (v1.7): vstupy se nakupuji jen pro planovanou vyrobu, ne pro plny potencial
    planned = {i: planned_goods(state, i, potential[i]) for i in ids}
    needs = {i: compute_need(state, i, planned[i]) for i in ids}

    # 2a. cilene obchody hracu (mnozstvi ze smlouvy)
    for d in state["deals"]:
        if d["type"] != "trade":
            continue
        owner, tgt, res = d["owner"], d["target"], d["res"]
        qty = float(d["qty"]) * trade_mult
        price = float(d["price"])
        if (tgt not in state["npc"] and tgt not in ("A", "B")) or res not in TRADEABLES:
            continue
        qty *= _war_trade_mult(state, owner, tgt)   # 3.3a (v1.10)
        if owner == "C":
            # 7.2 (v1.9): obchod Unie za cleny z poolu clenu
            value = _union_deal_execute(state, d, needs, imports, exports, trade_mult, trace)
            weight = 2.0 if res == "orit" else 1.0
            trade_volume += value
            trade_volume_weighted += value * weight
            if res == GOODS:
                goods_volume += value
            volume_by_player["C"] += value * weight
            if tgt in ("A", "B"):
                volume_by_player[tgt] += value * weight
            if tgt in volume_by_npc:
                volume_by_npc[tgt] += value * weight
            continue
        if d["direction"] == "npc_sells":
            seller, buyer = tgt, owner
        else:
            seller, buyer = owner, tgt
        se = ent(state, seller)
        be = ent(state, buyer)
        # 7.2 (v1.8): clo celni unie 10 % z hodnoty obchodu, plati necleen (S3)
        payer = _tariff_payer(state, seller, buyer)
        rate = _tariff_for(state, payer)
        unit_buyer = price * (1.0 + rate) if payer == buyer else price
        if unit_buyer > 0:
            qty = min(qty, max(0.0, float(be["wealth"])) / unit_buyer)
        value = qty * price
        tariff = rate * value if payer is not None else 0.0
        if seller in imports:
            exports[seller][res] += qty
        if buyer in imports:
            imports[buyer][res] += qty
        se["wealth"] = float(se["wealth"]) + value - (tariff if payer == seller else 0.0)
        be["wealth"] = float(be["wealth"]) - value - (tariff if payer == buyer else 0.0)
        if tariff > 0:
            _collect_tariff(state, payer, tariff)
        trace.add("4.1 cileny obchod", {"prodejce": seller, "kupec": buyer, "res": res, "owner": owner},
                  {"qty": round(qty, 3), "objem": round(value, 3), "clo": round(tariff, 4),
                   "clo_plati": payer})
        if res == GOODS and seller in imports:
            state["_goods_sold"][seller] = state["_goods_sold"].get(seller, 0.0) + qty
        weight = 2.0 if res == "orit" else 1.0
        trade_volume += value
        trade_volume_weighted += value * weight
        if res == GOODS:
            goods_volume += value
        if owner in volume_by_player:
            volume_by_player[owner] += value * weight
        if tgt in ("A", "B"):
            volume_by_player[tgt] += value * weight
            state["_ab_volume"] = state.get("_ab_volume", 0.0) + value
        if tgt in volume_by_npc:
            volume_by_npc[tgt] += value * weight

    # 2b. vstupy: vnitrni trh Unie, pak automaticky trh (C12)
    _union_market(state, INPUT_GOODS, needs, imports, exports, trace)
    v_in, pv_in, g_in, pairs_in = _auto_market(state, npcdata, INPUT_GOODS, needs,
                                               imports, exports, trace)

    # 3. vyroba goods (v1.7: podle planu, coverage vuci planovane vyrobe)
    for i in ids:
        e = ent(state, i)
        hh = household_need(e, state["_need_wealth"].get(i))
        pot = potential[i]
        plan = planned[i]
        if plan <= 0:
            coverage = 0.0  # nic se neplanuje, tovarny stoji (Q1)
        else:
            ratios = []
            for res, per_unit in GOODS_INPUT.items():
                avail = (supply_of(state, i, res) + imports[i][res] - exports[i][res]
                         + float(e["stock"].get(res, 0.0)) - hh[res])
                ratios.append(max(0.0, avail) / (per_unit * plan))
            coverage = clamp(min(ratios), 0.0, 1.0)
        out = plan * coverage
        e["goods_capacity"] = round(pot, 4)
        e["goods_planned"] = round(plan, 4)
        e["goods_out"] = round(out, 4)
        e["coverage"] = round(coverage, 4)
        # 4. konecne potreby podle skutecne vyroby
        needs[i] = compute_need(state, i, out)
        e["need"] = {k: round(v, 4) for k, v in needs[i].items()}
        trace.add("4.0 vyroba goods",
                  {"stat": i, "industry": e.get("industry"), "kapacita": round(pot, 3),
                   "planovano": round(plan, 3)},
                  {"coverage": e["coverage"], "goods_out": e["goods_out"]})

    # 4.0 a 4.1a (v1.9): 10 % kapacity velkych tovaren jde na trh vzdy, nejvys letosni vyroba
    state["_spec_offer"] = {i: min(SPECULATIVE_SHARE * potential[i], float(ent(state, i)["goods_out"]))
                            for i in ids if float(ent(state, i).get("industry") or 0.0) >= 4.0}

    # 4b. goods: vnitrni trh Unie, pak automaticky trh
    _union_market(state, (GOODS,), needs, imports, exports, trace)
    v_g, pv_g, g_g, pairs_g = _auto_market(state, npcdata, (GOODS,), needs,
                                           imports, exports, trace)
    npc_volume = v_in + v_g
    goods_volume += g_in + g_g
    for pid in ("A", "B"):
        # 4.1a (v1.3): automaticky prodej hrace se v metrice A pocita jako obchod hrace
        pv = pv_in[pid] + pv_g[pid]
        volume_by_player[pid] += pv
        trade_volume += pv
        trade_volume_weighted += pv
    # obchod A s B je v objemu obou hracu, do svetoveho objemu patri jen jednou
    trade_volume -= state.get("_ab_auto", 0.0)
    trade_volume_weighted -= state.get("_ab_auto", 0.0)
    pairs = list(pairs_in)
    for p in pairs_g:
        if p not in pairs:
            pairs.append(p)
    state["minsky"]["npc_trade_last"] = pairs
    trade_volume += npc_volume
    trade_volume_weighted += npc_volume

    # 5. vyrovnani se zasobami a deficit (4.1 a 4.1c)
    orit_on = state["phase"] in ORIT_PHASES
    grain_deficit = {}
    for i in ids:
        e = ent(state, i)
        stock = e["stock"]
        penalty = 0.0
        from_stock = 0.0
        by_res = {}
        for res in TRADEABLES:
            if res == "orit" and (not orit_on or is_fallen(state, i)):
                continue
            need = float(needs[i].get(res, 0.0))
            flow = supply_of(state, i, res) + imports[i][res] - exports[i][res]
            bal = flow - need
            if res == "orit":
                # spotrebovany orit, i ze zasoby: tech +0.1 a power +1 za jednotku (5)
                used = max(0.0, min(need, flow + float(stock.get("orit", 0.0))))
                if used > 0:
                    e["tech"] = clamp(float(e["tech"]) + 0.1 * used, 0.0, 10.0)
                    e["power"] = float(e["power"]) + 1.0 * used
            if bal >= 0:
                cap = ORIT_STOCK_CAP if res == "orit" else STOCK_CAP_TURNS * need
                cur = float(stock.get(res, 0.0))
                # Strop omezuje jen pridavani; zasoba nad stropem se nekrati (I5).
                if cur < cap:
                    stock[res] = round(min(cap, cur + bal), 4)
                if res == "grain":
                    grain_deficit[i] = 0.0
            else:
                short = -bal
                take = min(float(stock.get(res, 0.0)), short)
                stock[res] = round(float(stock.get(res, 0.0)) - take, 4)
                uncovered = short - take
                if res == "grain":
                    grain_deficit[i] = uncovered
                if res != "orit":
                    penalty += uncovered
                    from_stock += take
                    if uncovered > 1e-9:
                        by_res[res] = round(uncovered, 3)
        if penalty > 0:
            e["wealth"] = max(0.0, float(e["wealth"]) - penalty)
        trace.add("4.1 zdroje, zasoby a deficit",
                  {"stat": i, "imports": imports[i], "exports": exports[i]},
                  {"pokuta": round(penalty, 3), "deficit": round(penalty, 3),
                   "ze_zasoby": round(from_stock, 3), "pokuta_podle_statku": by_res,
                   "stock": {k: round(float(v), 3) for k, v in stock.items()},
                   "wealth": round(float(e["wealth"]), 3)})

    # 4.0 (v1.7): prodane goods tohoto tahu jsou "minuly tah" pro plan pristiho tahu (Q3)
    for i in ids:
        ent(state, i)["goods_sold_last"] = round(state["_goods_sold"].get(i, 0.0), 4)
    # 7.2 (v1.8): clo celni unie jako radek snimku
    state["union_tariff"] = {k: round(v, 4) for k, v in state.get("_union_tariff", {}).items()}
    if state["union_tariff"]:
        trace.add("7.2 clo celni unie", {"platci": sorted(state["union_tariff"])},
                  {"celkem": round(sum(state["union_tariff"].values()), 4),
                   "podle_platce": state["union_tariff"]})
    # 2 (v1.10.1): automaticke obchody hrace v tomto tahu pro pohled pristiho tahu
    for pid in ("A", "B"):
        state["players"][pid]["auto_last"] = auto_trades_summary(trace.items, pid)
    state["_player_imports"] = {pid: {r: round(imports[pid][r], 4) for r in TRADEABLES}
                                for pid in ("A", "B")}
    state["_trade"] = {"volume": trade_volume, "weighted": trade_volume_weighted,
                       "by_player": volume_by_player, "by_npc": volume_by_npc}
    state["_npc_trade_volume"] = npc_volume
    state["_goods_trade_volume"] = goods_volume
    # 4.1a (v1.5): tranzitni prijem tahu jako radek snimku
    state["transit_income"] = {k: round(v, 4) for k, v in
                               sorted(state.pop("_transit_income", {}).items(), key=lambda x: _npc_key(x[0]))}
    for sid, amount in state["transit_income"].items():
        trace.add("4.1a tranzitni prijem", {"stat": sid}, {"prijem": amount})
    return grain_deficit


# --------------------------------------------------------------------------
# 4.2 rust, 4.3 bida
# --------------------------------------------------------------------------

def in_poverty(state, sid: str, grain_deficit: dict) -> bool:
    e = ent(state, sid)
    return float(e["wealth"]) < 15.0 or grain_deficit.get(sid, 0.0) >= 3.0


def step_growth(state, grain_deficit, trace: Trace) -> None:
    """4.2 (v1.2): autonomni rust bohatstvi je zruseny. Zustava drift tech
    a uverova eroze prava."""
    for i in world_ids(state):
        e = ent(state, i)
        poor = in_poverty(state, i, grain_deficit)
        law = float(e["law"] or 0.0)
        tech = float(e["tech"] or 0.0)
        if poor:
            e["tech"] = clamp(tech - 0.15, 0.0, 10.0)
        elif law >= 5.0:
            e["tech"] = clamp(tech + 0.15, 0.0, 10.0)
        if is_npc(i):
            total_debt = sum(float(v) for v in e["debt"].values())
            if total_debt > 0.5 * max(1.0, float(e["wealth"])):
                e["law"] = clamp(float(e["law"]) - 0.1, 0.0, 10.0)
            # predkrizove maximum pro pravidlo 7.1 (ztrata >= 30 % => zakladatel Unie)
            e["wealth_peak"] = max(float(e.get("wealth_peak", 0.0)), float(e["wealth"]))
        trace.add("4.2 tech a pravo", {"stat": i, "law": law, "tech": tech},
                  {"tech_after": e["tech"], "law_after": e["law"]})


def step_npc_auto_invest(state, trace: Trace, events: list) -> None:
    """4.2a: bezne NPC s wealth > 40, law >= 5 a rostoucim wealth investuje kazdy treti tah,
    v cyklu deviti tahu tech, industry, prod (S6); cil invest_prod podle ceny (v1.9)."""
    turn = state["meta"]["turn"]
    if turn % 3 != 0:
        return
    # 4.2a (v1.8): stridani tri investic podle cisla tahu pro vsechna NPC (S6)
    kind = {3: "tech", 6: "industry", 0: "prod"}[turn % 9]
    for i, n in sorted(state["npc"].items()):
        if n.get("kind") == "fallen":
            continue
        if not (float(n["wealth"]) > 40.0 and float(n["law"]) >= 5.0):
            continue
        # 4.2a (v1.4): jen NPC, jehoz wealth za posledni 3 tahy vzrostlo (K4)
        hist = n.get("wealth_history") or []
        if len(hist) < 3 or float(n["wealth"]) <= float(hist[0]):
            continue
        if kind == "tech":
            n["wealth"] = float(n["wealth"]) - COST["invest_tech"]
            before = float(n["tech"])
            n["tech"] = clamp(before + 0.3, 0.0, 10.0)
            events.append({"kind": "npc_invest_tech", "npc": i, "tech": n["tech"]})
            trace.add("4.2a automatika NPC: invest_tech", {"npc": i, "cost": COST["invest_tech"]},
                      {"tech": n["tech"], "from": before})
        elif kind == "industry":
            n["wealth"] = float(n["wealth"]) - COST["invest_industry"]
            before = float(n.get("industry") or 0.0)
            n["industry"] = clamp(before + 0.3 * (float(n["law"]) / 5.0), 0.0, 10.0)
            events.append({"kind": "npc_invest_industry", "npc": i, "industry": n["industry"]})
            trace.add("4.2a automatika NPC: invest_industry",
                      {"npc": i, "cost": COST["invest_industry"]},
                      {"industry": n["industry"], "from": before})
        else:
            # 4.2a (v1.9): invest_prod do vyrabeneho zdroje s nejvyssi trzni cenou, nikdy do zdroje
            # s cenou na dolni mezi (0.7x zakladu); jen pri tech >= 3; pri shode poradi oil, grain, metal
            if float(n["tech"]) < 3.0:
                continue
            cands = []
            for idx, r in enumerate(BASE_RESOURCES):
                if float(n["prod"].get(r, 0.0)) <= 0:
                    continue
                price = market_price(state, r)
                if price <= 0.7 * base_price(state, r) + 1e-9:
                    continue
                cands.append((price, -idx, r))
            if not cands:
                trace.add("4.2a automatika NPC: invest_prod bez cile", {"npc": i},
                          {"duvod": "zadny vyrabeny zdroj nad dolni mezi ceny"})
                continue
            res = max(cands)[2]
            n["wealth"] = float(n["wealth"]) - COST["invest_prod"]
            before = float(n["prod"][res])
            n["prod"][res] = before + 1.0
            events.append({"kind": "npc_invest_prod", "npc": i, "res": res, "prod": n["prod"][res]})
            trace.add("4.2a automatika NPC: invest_prod", {"npc": i, "cost": COST["invest_prod"], "res": res},
                      {"prod": n["prod"][res], "from": before})


def step_income(state, trace: Trace) -> None:
    """4.2b (v1.4): neformalni prijem wealth += pop / 60 za tah."""
    for i in world_ids(state):
        e = ent(state, i)
        gain = float(e.get("pop") or 0.0) / INCOME_POP_DIVISOR
        e["wealth"] = float(e["wealth"]) + gain
        trace.add("4.2b neformalni prijem", {"stat": i}, {"prijem": round(gain, 3)})


def step_industry(state, grain_deficit, trace: Trace) -> None:
    """4.2c: industry +0.1 pri law >= 6, tech >= 5 a coverage >= 0.8; v bide -0.1."""
    for i in world_ids(state):
        e = ent(state, i)
        before = float(e.get("industry") or 0.0)
        if in_poverty(state, i, grain_deficit):
            after = before - 0.1
        elif (float(e["law"] or 0.0) >= 6.0 and float(e["tech"] or 0.0) >= 5.0
              and float(e.get("coverage") or 0.0) >= 0.8):
            after = before + 0.1
        else:
            continue
        # 4.2c (v1.3): industry hracu a beznych NPC nikdy neklesne pod 0.5
        floor = INDUSTRY_FLOOR  # 4.2c (v1.4): dno plati i pro padle rise
        e["industry"] = clamp(after, floor, 10.0)
        trace.add("4.2c rust prumyslu", {"stat": i, "coverage": e.get("coverage")},
                  {"industry": round(e["industry"], 3), "from": before})


def step_poverty(state, npcdata, grain_deficit, trace: Trace, events: list) -> None:
    """4.3 (v1.2): bida a prevrat.

    Tah s wealth = 0 je tahem bidy jako kazdy jiny (wealth < 15), okamzity pad
    vlady uz neexistuje. Prevrat nastane po trech tazich bidy v rade; po nem ma
    stat sest tahu imunitu. Prevrat rusi pakty, sankce a vliv, obchody a dluhy
    zustavaji, clenstvi v Unii i kandidatura zanikaji (C10). Jen u NPC (A1).
    """
    turn = state["meta"]["turn"]
    # Seznam statu v bide podle 4.3. Cte ho metrika n_bida (pravidlo 8).
    poverty_set = []
    for i in world_ids(state):
        e = ent(state, i)
        poor = in_poverty(state, i, grain_deficit)
        if not poor:
            e["poverty_streak"] = 0
            continue
        poverty_set.append(i)
        e["poverty_streak"] = int(e.get("poverty_streak", 0)) + 1
        pop_before = float(e["pop"])
        e["pop"] = max(0.0, pop_before - 3.0)
        e["power"] = max(0.0, float(e["power"]) - 1.0)
        e["wealth"] = max(0.0, float(e["wealth"]))
        events.append({"kind": "poverty", "stat": i, "streak": e["poverty_streak"]})
        trace.add("4.3 bida", {"stat": i, "streak": e["poverty_streak"]},
                  {"pop": e["pop"], "power": e["power"],
                   "pop_delta": e["pop"] - pop_before})
        if not is_npc(i) or e["poverty_streak"] < 3:
            continue
        last = e.get("last_coup_turn")
        if last is not None and turn - int(last) <= COUP_IMMUNITY_TURNS:
            trace.add("4.3 imunita po prevratu", {"stat": i, "posledni_prevrat": last},
                      {"streak": e["poverty_streak"]})
            continue
        cancelled = [d["id"] for d in state["deals"]
                     if d["target"] == i and d["type"] in ("protect", "pressure")]
        state["deals"] = [d for d in state["deals"] if d["id"] not in cancelled]
        e["influence"]["A"] = 0.0
        e["influence"]["B"] = 0.0
        e["coups"] = int(e.get("coups", 0)) + 1
        e["poverty_streak"] = 0
        e["last_coup_turn"] = turn
        C = state["players"]["C"]
        if i in C["members"]:
            # 4.3 a 7.5 (v1.5): prevrat clenstvi neprusi, clenovi klesne law o 1
            e["status"] = "union"
            e["law"] = clamp(float(e["law"]) - COUP_LAW_PENALTY, 0.0, 10.0)
            events.append({"kind": "union_member_coup", "npc": i, "law": e["law"]})
        elif i in C["candidates"]:
            e["status"] = "candidate"  # K7: kandidatura prevrat prezije (v1.5 vzdy)
        else:
            e["status"] = "independent"
        events.append({"kind": "coup", "stat": i, "coups": e["coups"]})
        trace.add("4.3 pad vlady", {"stat": i},
                  {"coups": e["coups"], "status": "independent", "zruseno": cancelled})
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
                add_influence(state, i, d["owner"], 1.0 * mult)
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


def _overtrading_turn(state):
    """Tah, ve kterem svet vstoupil do overtrading. None, pokud jeste nevstoupil."""
    for rec in state["minsky"].get("phase_log", []):
        if rec.get("to") == "overtrading":
            return rec.get("turn")
    return None


def _default_turns(state) -> int:
    """Pocet tahu s aspon jednim nesplacenim, pocitano az od vstupu do overtrading.

    Pravidlo 5 (v1.1): drivejsi zaznamy v defaults fazi nespousteji, ale pro
    "krize uvolnuje sfery" v crash se pouzivaji vsechny bez ohledu na tah.
    """
    start = _overtrading_turn(state)
    if start is None:
        return 0
    return len({d["turn"] for d in state["minsky"]["defaults"] if d["turn"] >= start})


GUARDED_PHASES = ("boom", "euphoria", "overtrading", "distress", "panic", "crash")


def _phase_entry_turn(state, phase):
    """Tah posledniho vstupu do dane faze."""
    for rec in reversed(state["minsky"].get("phase_log", [])):
        if rec.get("to") == phase:
            return rec.get("turn")
    return None


def step_minsky(state, npcdata, rng, trace: Trace, events: list) -> None:
    turn = state["meta"]["turn"]
    phase = state["phase"]
    phase_at_start = phase
    m = state["minsky"]

    # --- prechody -----------------------------------------------------------
    if phase == "pre" and turn >= 7:
        _set_phase(state, "displacement", "tah 7", turn, trace, events)
        m["orit_price"] = float(m["orit_price_start"])
        for nid, amount in (("N6", 6.0), ("N3", 1.0), ("N8", 1.0), ("N9", 1.0)):
            if nid in state["npc"]:
                state["npc"][nid]["prod"]["orit"] = amount
        for i in world_ids(state):
            if is_fallen(state, i):
                continue  # 7a: padle rise orit ignoruji
            # need.orit se od v1.2 pocita v 4.0 kazdy tah, tady jen pole produkce
            ent(state, i).setdefault("prod", {}).setdefault("orit", 0.0)
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
            # bublina musi prijit (pravidlo 5)
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
        if wealth > 0 and debts > 0.4 * wealth:
            _set_phase(state, "overtrading", "dluhy NPC > 40 % jejich wealth",
                       round(debts / wealth, 3), trace, events)
        phase = state["phase"]

    elif phase == "overtrading":
        if _default_turns(state) >= 1:
            _set_phase(state, "distress", "prvni nesplaceni", _default_turns(state),
                       trace, events)
        phase = state["phase"]

    elif phase == "distress":
        started = _phase_entry_turn(state, "distress")
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

    # --- pojistka cyklu (5, v1.2) -----------------------------------------------
    # Faze od boom dal, ktera trva dele nez 15 tahu bez splneni prahu, se posune
    # o krok. Netyka se depression a recovery.
    if state["phase"] == phase_at_start and phase_at_start in GUARDED_PHASES:
        entry = _phase_entry_turn(state, phase_at_start)
        if entry is not None and turn - entry >= CYCLE_GUARD_TURNS:
            nxt = PHASE_ORDER[PHASE_ORDER.index(phase_at_start) + 1]
            normal = [(i, float(nn["prod"].get("orit", 0.0)))
                      for i, nn in sorted(state["npc"].items()) if nn.get("kind") != "fallen"]
            top = sorted(normal, key=lambda x: (-x[1], x[0]))[0][0] if normal else None
            _set_phase(state, nxt,
                       "pojistka cyklu: %d tahu bez splneni prahu" % CYCLE_GUARD_TURNS,
                       turn - entry, trace, events)
            events.append({"kind": "cycle_guard", "npc": top, "from": phase_at_start,
                           "to": nxt, "duvod": "soukrome banky v NPC s nejvyssim prod.orit "
                                               "pujcuji na spekulaci"})
            if nxt == "crash":
                m["crash_turn"] = turn
            if nxt == "boom":
                m["boom_started_turn"] = turn
            phase = nxt

    # --- efekty faze ---------------------------------------------------------
    price_before = m.get("orit_price")
    if phase == "boom":
        m["orit_price"] = float(m["orit_price"]) * 1.15
    elif phase == "euphoria":
        m["orit_price"] = float(m["orit_price"]) * 1.2
        for i, nn in state["npc"].items():
            if sum(float(v) for v in nn["debt"].values()) > 30:
                nn["law"] = clamp(float(nn["law"]) - 0.15, 0.0, 10.0)
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
            for nn in state["npc"].values():
                owed = float(nn["debt"].get(pid, 0.0))
                if owed > 0:
                    written_off += owed * 0.6
                    nn["debt"][pid] = owed * 0.4
            if written_off > 0:
                p["wealth"] = max(0.0, float(p["wealth"]) - written_off)
                trace.add("5 panic odpis pohledavek", {"creditor": pid},
                          {"odepsano": round(written_off, 3)})
        for i, nn in state["npc"].items():
            if sum(float(v) for v in nn["debt"].values()) > 0:
                nn["wealth"] = float(nn["wealth"]) * 0.8
    elif phase == "crash":
        if m.get("crash_turn") == turn:
            m["orit_price"] = 3.0
            _migration_back(state, trace)
            # uvolneni sfer: NPC ve sphere_X, ktere X nesplacelo, zpet na independent
            for i, nn in state["npc"].items():
                for pid in ("A", "B"):
                    # 5 (v1.6): staci nenulovy dluh vuci X, ne jen nesplaceni
                    if nn["status"] == f"sphere_{pid}" and float(nn["debt"].get(pid, 0.0)) > 0:
                        nn["status"] = "independent"
                        nn["influence"][pid] = float(nn["influence"][pid]) / 2.0
                        events.append({"kind": "sphere_released", "npc": i, "from": pid})
    elif phase == "depression":
        m["orit_price"] = 5.0
    elif phase == "recovery":
        m["orit_price"] = 5.0

    # strop ceny oritu (5, v1.2)
    if m.get("orit_price") is not None and float(m["orit_price"]) > ORIT_PRICE_CAP:
        m["orit_price"] = ORIT_PRICE_CAP
        trace.add("5 strop ceny oritu", {"strop": ORIT_PRICE_CAP}, {"cena": ORIT_PRICE_CAP})

    if price_before != m.get("orit_price"):
        trace.add("5 cena oritu", {"faze": phase, "pred": price_before},
                  {"po": m.get("orit_price")})

    # papirove bohatstvi (pravidla 5 a 10.3)
    if phase in ("boom", "euphoria", "overtrading"):
        price = float(m["orit_price"])
        for i, nn in state["npc"].items():
            if float(nn["prod"].get("orit", 0.0)) > 0:
                nn["paper_wealth"] = float(nn["prod"]["orit"]) * price
        for pid in ("A", "B"):
            total = 0.0
            for nn in state["npc"].values():
                if float(nn["prod"].get("orit", 0.0)) > 0:
                    total += float(nn["debt"].get(pid, 0.0))
            state["players"][pid]["paper_wealth"] = total * (price / 10.0)
        trace.add("5 / 10.3 papirove bohatstvi", {"cena": price},
                  {"A": state["players"]["A"]["paper_wealth"],
                   "B": state["players"]["B"]["paper_wealth"]})

    # migrace v boomu
    if phase in ("boom", "euphoria", "overtrading"):
        _migration(state, rng, trace, events)

    # automaticky explore NPC od displacementu
    if phase in ORIT_PHASES:
        for i, nn in sorted(state["npc"].items()):
            if nn.get("kind") == "fallen":
                continue
            if float(nn["wealth"]) >= 20.0:
                nn["wealth"] = float(nn["wealth"]) - 2.0
                trace.add("5 explore NPC platba", {"npc": i}, {"cost": 2.0})
                if rng.random() < 0.15:
                    nn["prod"]["orit"] = float(nn["prod"].get("orit", 0.0)) + 2.0
                    events.append({"kind": "orit_found", "npc": i})
                    trace.add("5 explore NPC", {"npc": i}, {"prod_orit": nn["prod"]["orit"]})

    # fragilita
    debts = sum(sum(float(v) for v in nn["debt"].values()) for nn in state["npc"].values())
    wealth = sum(float(nn["wealth"]) for nn in state["npc"].values())
    m["fragility"] = round(debts / wealth, 4) if wealth > 0 else 0.0


def _migration(state, rng, trace, events) -> None:
    """Boom: NPC s prod.orit >= 2 dostava pop +2, dva darci po -1 (C1)."""
    receivers = [i for i, n in sorted(state["npc"].items())
                 if float(n["prod"].get("orit", 0.0)) >= 2.0]
    donors_pool = [i for i, n in sorted(state["npc"].items())
                   if float(n["prod"].get("orit", 0.0)) == 0.0
                   and n.get("kind") != "fallen"]
    for r in receivers:
        chosen = []
        # Pop darce se kontroluje az pri vyberu: pri vice prijemcich v jednom tahu
        # muze byt tentyz darce vybran opakovane a nesmi klesnout pod nulu.
        pool = [d for d in donors_pool if float(state["npc"][d]["pop"]) > 1.0]
        for _ in range(2):
            if not pool:
                break
            pick = pool.pop(rng.randrange(len(pool)))
            chosen.append(pick)
        if len(chosen) < 2:
            continue
        state["npc"][r]["pop"] = float(state["npc"][r]["pop"]) + float(len(chosen))
        cut = {}
        for dnr in chosen:
            state["npc"][dnr]["pop"] = float(state["npc"][dnr]["pop"]) - 1.0
            g = float(state["npc"][dnr]["prod"].get("grain", 0.0))
            state["npc"][dnr]["prod"]["grain"] = max(0.0, g - 0.5)
            # skutecna srazka (u darce bez obili 0); migrace zpet vraci jen ji
            cut[dnr] = cut.get(dnr, 0.0) + (g - state["npc"][dnr]["prod"]["grain"])
        state["minsky"]["migration_ledger"].append({"to": r, "from": chosen, "srazka": cut})
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
        # Docasna srazka obili konci vzdy, i kdyz uz neni koho vracet. Vraci se jen to,
        # co se opravdu strhlo (darce bez obili nic neztratil a nic nedostane).
        cut = rec.get("srazka")
        for dnr in donors:
            g = float(state["npc"][dnr]["prod"].get("grain", 0.0))
            back = float(cut.get(dnr, 0.0)) if isinstance(cut, dict) else 0.5
            state["npc"][dnr]["prod"]["grain"] = g + back
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

UNION_MAX_FOUNDERS = 4
UNION_MAX_MEMBERS = 7
UNION_MAX_CANDIDATES = 3


def _fragility(state, nid: str) -> float:
    """Zranitelnost jednoho NPC: dluh ku realnemu bohatstvi."""
    n = state["npc"][nid]
    debt = sum(float(v) for v in n["debt"].values())
    return debt / max(1.0, float(n["wealth"]))


def _components(npcdata, nodes: list[str]) -> list[list[str]]:
    """Souvisle skupiny uvnitr `nodes` podle adjacency."""
    zbyva = list(nodes)
    out = []
    while zbyva:
        seed = zbyva.pop(0)
        skupina = [seed]
        fronta = [seed]
        while fronta:
            cur = fronta.pop()
            for nb in neighbours(npcdata, cur):
                if nb in zbyva:
                    zbyva.remove(nb)
                    skupina.append(nb)
                    fronta.append(nb)
        out.append(sorted(skupina))
    return out


def _pick_founders(state, npcdata, eligible: list[str], trace: Trace):
    """7.1 (v1.6): nejvetsi souvisla skupina zpusobilych statu, bez mostu.

    Pri shode velikosti vyhrava skupina s vyssim prumernym law, pak nizsi ID (N-otazka).
    v1.7: zakladatele se vybiraji hladove. Prvni je stat s nejvyssim law, kazdy dalsi
    je zpusobily soused nektereho uz vybraneho s nejvyssim law (pri shode vyssi wealth,
    pak nizsi ID), do poctu 4. Nevybrani ze skupiny jsou kandidati do stropu 3.
    Ma-li mene nez 3, Unie nevznikne (volajici). fragility se nepouziva.

    Vraci (zakladatele nebo cela mala skupina, kandidati).
    """
    if not eligible:
        return [], []

    def avg_law(group):
        return sum(float(state["npc"][x]["law"]) for x in group) / len(group)

    skupiny = _components(npcdata, eligible)
    skupiny.sort(key=lambda g: (-len(g), -avg_law(g), min(_npc_key(x) for x in g)))
    group = skupiny[0]
    ranked = sorted(group, key=lambda x: (-float(state["npc"][x]["law"]),
                                          -float(state["npc"][x]["wealth"]), _npc_key(x)))
    if len(group) < 3:
        founders, candidates = ranked, []
    else:
        founders = [ranked[0]]
        while len(founders) < UNION_MAX_FOUNDERS:
            nbs = [x for x in ranked if x not in founders
                   and any(x in neighbours(npcdata, fo) for fo in founders)]
            if not nbs:
                break
            founders.append(nbs[0])  # ranked je serazene podle law, wealth, ID
        rest = [x for x in ranked if x not in founders]
        candidates = rest[:UNION_MAX_CANDIDATES]
    trace.add("7.1 vyber zakladatelu",
              {"zpusobili": eligible, "skupiny": [len(g) for g in skupiny],
               "nejvetsi_skupina": group},
              {"zakladatele": founders, "kandidati": candidates,
               "law": {x: float(state["npc"][x]["law"]) for x in ranked},
               "wealth": {x: round(float(state["npc"][x]["wealth"]), 2) for x in ranked}})
    return founders, candidates


def _union_can_join(state, npcdata, nid: str) -> bool:
    """7.4 (v1.1): vstup po zalozeni vyzaduje sousednost aspon s jednim clenem."""
    C = state["players"]["C"]
    if not C["members"]:
        return False
    return any(mm in neighbours(npcdata, nid) for mm in C["members"])


def step_union(state, npcdata, trace: Trace, events: list) -> None:
    C = state["players"]["C"]
    state["union_solidarity"] = {}
    turn = state["meta"]["turn"]
    m = state["minsky"]

    # 7.1 vznik v tahu crash
    if not C["active"] and state["phase"] == "crash" and m.get("crash_turn") == turn:
        eligible = []
        for i, n in sorted(state["npc"].items(), key=lambda x: _npc_key(x[0])):
            # 7.1 (v1.6): nezavisla NPC (ne sphere_X, ne occupied_X)
            if n["status"] != "independent":
                continue
            if n.get("kind") == "fallen" and i in m["fallen_touched"]:
                continue  # 7a: padla rise, kterou behem boom az panic nekdo tlacil, zpusobila neni
            # 7.1 (v1.7): padle rise jen za stejnych podminek jako ostatni (ztrata nebo nesplaceni)
            defaulted = any(d["npc"] == i for d in m["defaults"])
            peak = float(n.get("wealth_peak", n["wealth"]))
            lost = peak > 0 and float(n["wealth"]) <= (1.0 - UNION_FOUNDER_LOSS) * peak
            if defaulted or lost:
                eligible.append(i)
        founders, extra_candidates = _pick_founders(state, npcdata, eligible, trace)
        if len(founders) >= 3:
            C["active"] = True
            C["founded_turn"] = turn
            # Kopie: seznam clenu se v tomtez tahu rozsiruje o vstupy podle 7.4
            # a nesmi prepsat zaznam o zakladatelich v udalosti a v trace.
            C["members"] = list(founders)
            C["name"] = C.get("name") or "Unie"
            fund = 0.0
            for f in founders:
                take = float(state["npc"][f]["wealth"]) * 0.10
                state["npc"][f]["wealth"] -= take
                state["npc"][f]["status"] = "union"
                fund += take
            C["wealth"] = fund
            C["fund"] = fund
            if extra_candidates:
                # 7.1 (v1.6): zbytek nejvetsi skupiny se stava kandidaty do stropu 3
                C["candidates"] = list(extra_candidates)
                for c_id in extra_candidates:
                    state["npc"][c_id]["status"] = "candidate"
            events.append({"kind": "union_founded", "members": list(founders), "fund": fund,
                           "candidates": list(extra_candidates)})
            trace.add("7.1 vznik Unie", {"zakladatele": founders},
                      {"fond": round(fund, 3), "tah": turn})
        else:
            events.append({"kind": "union_failed", "candidates": founders})
            trace.add("7.1 Unie nevznikla", {"zakladatele": founders},
                      {"pocet": len(founders), "minimum": 3})

    if not C["active"]:
        return

    # 7.4 (v1.3, G15): vstupy po zalozeni az od nasledujiciho tahu
    joins_open = C.get("founded_turn") != turn

    # 7.3 vstupni prah prava
    if C["members"]:
        avg = sum(float(state["npc"][mm]["law"]) for mm in C["members"]) / len(C["members"])
        C["law_threshold"] = round(avg - 1.0, 3)
        trace.add("7.3 prah prava", {"clenove": list(C["members"])},
                  {"law_threshold": C["law_threshold"]})

    # 7.4 bolest: nezavisle NPC v bide nebo po prevratu zada samo
    for i, n in sorted(state["npc"].items()):
        if not joins_open:
            break
        if n["status"] != "independent" or n.get("kind") == "fallen":
            continue
        hurting = float(n["wealth"]) < 15.0 or int(n.get("coups", 0)) > 0
        if not hurting:
            continue
        if not _union_can_join(state, npcdata, i):
            continue  # 7.4 (v1.1): kdo nesousedi s clenem, zustava mimo
        if C["law_threshold"] is not None and float(n["law"]) >= float(C["law_threshold"]):
            if len(C["members"]) >= UNION_MAX_MEMBERS:
                events.append({"kind": "union_rejected", "npc": i,
                               "reason": "plny pocet clenu"})
                continue
            n["status"] = "union"
            if i not in C["members"]:
                C["members"].append(i)
            events.append({"kind": "union_join", "npc": i, "how": "bolest"})
        else:
            if len(C["candidates"]) >= UNION_MAX_CANDIDATES:
                events.append({"kind": "union_rejected", "npc": i,
                               "reason": "plny pocet kandidatu"})
                continue
            n["status"] = "candidate"
            if i not in C["candidates"]:
                C["candidates"].append(i)
            events.append({"kind": "union_candidate", "npc": i})
        trace.add("7.4 vstup bolesti", {"npc": i, "law": n["law"]},
                  {"status": n["status"], "clenu": len(C["members"]),
                   "kandidatu": len(C["candidates"])})

    # kandidat se stava clenem, jakmile splni prah
    for i in list(C["candidates"]):
        if not joins_open:
            break
        n = state["npc"].get(i)
        if n is None:
            continue
        if C["law_threshold"] is not None and float(n["law"]) >= float(C["law_threshold"]):
            if len(C["members"]) >= UNION_MAX_MEMBERS:
                continue
            C["candidates"].remove(i)
            if i not in C["members"]:
                C["members"].append(i)
            n["status"] = "union"
            events.append({"kind": "union_join", "npc": i, "how": "prah splnen"})

    # 7.2 (v1.6): prispevky clenu 2 % wealth za tah a solidarita nejchudsimu clenovi v bide.
    # Obojí od tahu po zalozeni; fond se smi solidaritou vyprazdnit az na 0.
    state["union_contributions"] = {}
    if C.get("founded_turn") != turn:
        for mm in sorted(C["members"], key=_npc_key):
            take = float(state["npc"][mm]["wealth"]) * UNION_CONTRIBUTION
            if take <= 0:
                continue
            state["npc"][mm]["wealth"] = float(state["npc"][mm]["wealth"]) - take
            C["wealth"] = float(C["wealth"]) + take
            state["union_contributions"][mm] = round(take, 4)
        if state["union_contributions"]:
            trace.add("7.2 prispevky do fondu", {"clenove": list(C["members"])},
                      {"prispevky": state["union_contributions"], "fond": round(float(C["wealth"]), 4)})
        poor = set(state.get("_poverty", []))
        poor_members = [mm for mm in C["members"] if mm in poor]
        if poor_members:
            mm = min(poor_members, key=lambda x: (float(state["npc"][x]["wealth"]), _npc_key(x)))
            amount = min(SOLIDARITY_MAX, float(C["wealth"]))
            if amount > 1e-9:
                C["wealth"] = float(C["wealth"]) - amount
                state["npc"][mm]["wealth"] = float(state["npc"][mm]["wealth"]) + amount
                state["union_solidarity"][mm] = round(amount, 4)
                events.append({"kind": "union_solidarity", "npc": mm, "amount": round(amount, 4)})
                trace.add("7.2 automaticka solidarita", {"npc": mm},
                          {"prijem": round(amount, 4), "fond": round(float(C["wealth"]), 4)})

    C["power"] = sum(float(state["npc"][mm]["power"]) for mm in C["members"]) \
        if C["members"] else 0.0
    C["fund"] = C["wealth"]


def _union_admit(state, npcdata, target, events, trace) -> None:
    """7.4 pritazlivost: Unie nabidne clenstvi, NPC prijme, pokud splni podminky."""
    C = state["players"]["C"]
    n = state["npc"].get(target)
    if n is None or n["status"] != "independent":
        return
    if len(C["members"]) >= UNION_MAX_MEMBERS:
        events.append({"kind": "union_rejected", "npc": target,
                       "reason": "plny pocet clenu"})
        return
    if not _union_can_join(state, npcdata, target):
        events.append({"kind": "union_rejected", "npc": target,
                       "reason": "nesousedi s zadnym clenem"})
        return
    # 7.4 (v1.10): admit i ze zony vlivu (vliv nad 8 do 12), ma-li NPC law >= law_threshold + 1
    top = max(float(n["influence"]["A"]), float(n["influence"]["B"]))
    if top > ADMIT_ZONE_MAX:
        events.append({"kind": "union_rejected", "npc": target, "reason": "vliv velmoci"})
        return
    if top > ADMIT_ZONE_MIN and (C["law_threshold"] is None
                                 or float(n["law"]) < float(C["law_threshold"]) + 1.0):
        events.append({"kind": "union_rejected", "npc": target, "reason": "zona vlivu velmoci, law pod prahem + 1"})
        return
    # 7.4 (v1.7): law >= law_threshold je tvrda podminka pritazlivosti
    if C["law_threshold"] is not None and float(n["law"]) < float(C["law_threshold"]):
        events.append({"kind": "union_rejected", "npc": target, "reason": "law pod prahem"})
        return
    # 3.4: NPC nabidku vyhodnoti az po splneni prahu
    outcome = _npc_decide(state, npcdata, "C", target, "admit", {}, events=events, trace=trace)
    if outcome in ("protinavrh", "odmitnuto"):
        events.append({"kind": "union_rejected", "npc": target, "reason": "NPC nabidku neprijalo (3.4)"})
        return
    n["status"] = "union"
    if target not in C["members"]:
        C["members"].append(target)
    take = float(n["wealth"]) * 0.10
    n["wealth"] -= take
    C["wealth"] = float(C["wealth"]) + take
    events.append({"kind": "union_join", "npc": target, "how": "admit"})
    trace.add("7.4 admit", {"npc": target}, {"fond": C["wealth"]})


# --------------------------------------------------------------------------
# 8 metriky
# --------------------------------------------------------------------------

def step_offers(state, npcdata, trace: Trace, events: list) -> None:
    """3.5 (v1.6): nabidky NPC hracum.

    Nejdriv propadnou neprijate nabidky (tri po sobe ignorovane od tehoz NPC: vliv -1).
    Pak engine pro kazdeho hrace (A, B, po vzniku i C) vybere nejvys 2 nove nabidky od NPC
    podle nejvyssiho vlivu hrace. Jedno NPC da hraci nejvys jednu nabidku, typy se zkousi
    v poradi sell, loan_request, protect_request (N-otazka).
    """
    turn = int(state["meta"]["turn"])
    m = state["minsky"]
    ignored = m.setdefault("offer_ignored", {"A": {}, "B": {}, "C": {}})
    kept = []
    for o in state.get("offers", []):
        if int(o["expires"]) <= turn:
            cnt = int(ignored.setdefault(o["player"], {}).get(o["npc"], 0)) + 1
            if cnt >= 3:
                if o["player"] in ("A", "B") and o["npc"] in state["npc"]:
                    nn = state["npc"][o["npc"]]
                    nn["influence"][o["player"]] = max(0.0, float(nn["influence"][o["player"]]) - 1.0)
                    trace.add("3.5 ignorovane nabidky", {"player": o["player"], "npc": o["npc"]},
                              {"influence": nn["influence"][o["player"]]})
                cnt = 0
            ignored[o["player"]][o["npc"]] = cnt
        else:
            kept.append(o)

    players = ["A", "B"] + (["C"] if state["players"]["C"]["active"] else [])
    imports = state.get("_player_imports", {})
    poor = set(state.get("_poverty", []))
    orit_on = state["phase"] in ORIT_PHASES
    invaded = {v["target"] for v in state.get("invasions", [])}
    new = []
    for pid in players:
        active_npcs = {o["npc"] for o in kept if o["player"] == pid}
        sells, others = [], []
        for nid in sorted(state["npc"], key=_npc_key):
            if nid in active_npcs:
                continue
            nn = state["npc"][nid]
            need = nn.get("need") or {}
            infl = float(nn["influence"].get(pid, 0.0)) if pid in ("A", "B") else 0.0
            # (1) sell: prebytek nad rezervu u statku, ktery hrac tento tah dovazel
            if pid in ("A", "B"):
                for res in ("grain", "oil", "metal", "goods"):
                    imp = float(imports.get(pid, {}).get(res, 0.0))
                    if imp <= 0:
                        continue
                    surplus = float(nn["stock"].get(res, 0.0)) - RESERVE_TURNS * float(need.get(res, 0.0))
                    if surplus <= 1e-6:
                        continue
                    op = _openness(npcdata, nid)
                    factor = 1.15 if op <= 3 else (0.9 if float(nn["wealth"]) < 25 else 1.0)
                    sells.append((-infl, _npc_key(nid), nid,
                                  {"type": "sell", "res": res, "qty": round(min(surplus, imp), 3),
                                   "price": round(market_price(state, res) * factor, 4)}))
                    break
            other = None
            # (2) loan_request: NPC v bide nebo s deficitem oritu
            if nn.get("kind") != "fallen":
                orit_short = 0.0
                if orit_on:
                    orit_short = max(0.0, float(need.get("orit", 0.0)) - eff_prod(nn, "orit")
                                     - float(nn["stock"].get("orit", 0.0)))
                if (nid in poor or orit_short > 0) and not (
                        pid == "C" and nn["status"] not in ("independent", "candidate")):
                    gap = max(0.0, 15.0 - float(nn["wealth"])) + 5.0 * orit_short
                    other = {"type": "loan_request", "amount": round(clamp(10.0 + gap, 10.0, 20.0), 2)}
            # (3) protect_request: ohrozeny soused nebo rostouci vliv soupere, jen hraci s vyssim vlivem
            if other is None and pid in ("A", "B") and nn.get("kind") != "fallen":
                rival = "B" if pid == "A" else "A"
                inf_p = float(nn["influence"].get(pid, 0.0))
                inf_r = float(nn["influence"].get(rival, 0.0))
                hist = nn.get("influence_history") or []
                rise = inf_r - float(hist[0].get(rival, 0.0)) if len(hist) >= 3 else 0.0
                threatened = any(nb in invaded for nb in neighbours(npcdata, nid))
                if inf_p > inf_r and (threatened or rise >= 4.0) and _pact_holder(state, nid) is None:
                    other = {"type": "protect_request"}
            if other is not None:
                others.append((-infl, _npc_key(nid), nid, other))
        sells.sort()
        others.sort()
        # 3.5 (v1.7): nejvys jedno sell; druhe misto loan_request nebo protect_request
        # s nejvyssim vlivem, a jen kdyz zadna neni, druhe sell. Bez sell dve jine (Q6).
        chosen, used = [], set()

        def take(lst):
            for c in lst:
                if c[2] not in used:
                    used.add(c[2])
                    chosen.append(c)
                    return True
            return False

        take(sells)
        if not take(others):
            take(sells)
        if len(chosen) < 2:
            take(others)
        for _, _, nid, offer in chosen[:2]:
            oid = "o%d" % int(m.get("next_offer_id", 1))
            m["next_offer_id"] = int(m.get("next_offer_id", 1)) + 1
            o = dict(offer)
            o.update({"offer_id": oid, "player": pid, "npc": nid, "created": turn,
                      "expires": turn + OFFER_VALID_TURNS})
            kept.append(o)
            new.append(o)
            trace.add("3.5 nabidka NPC", {"player": pid, "npc": nid, "type": offer["type"]}, dict(o))
    state["offers"] = kept
    state["offers_new"] = new


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
    # 8 (v1.1): prvni clen zastropovan na 1.5, jinak by slozene uroceni ze 4.2
    # hnalo index k nekonecnu a vyhral by i svet, kde vetsina statu hladovi.
    # 8 (v1.6): delitel bidy = pocet statu sveta (18)
    index = 100.0 * min(1.5, w_real / w0) * (1.0 - max_share) * (1.0 - n_bida / float(len(world_ids(state))))

    state["metrics"].update({
        "A_trade_share": round(a_share, 4),
        "B_resource_share": round(b_share, 4),
        "C_min_member": round(c_min, 3) if c_min is not None else None,
        "prosperity_index": round(index, 2),
        "W_real": round(w_real, 2),
        "n_bida": n_bida,
        "max_share": round(max_share, 4),
        "trade_volume": round(tr["weighted"], 3),
        "trade_volume_npc": round(state.get("_npc_trade_volume", 0.0), 3),
        "trade_volume_players": round(
            max(0.0, tr["weighted"] - state.get("_npc_trade_volume", 0.0)), 3),
        "trade_volume_goods": round(state.get("_goods_trade_volume", 0.0), 3),
        "trade_volume_AB": round(state.get("_ab_volume", 0.0), 3),
        "poverty_ids": sorted(state.get("_poverty", [])),
    })
    trace.add("8 metriky", {"W_real": round(w_real, 2), "W0": w0, "n_bida": n_bida},
              {"prosperity_index": state["metrics"]["prosperity_index"],
               "A_trade_share": state["metrics"]["A_trade_share"],
               "B_resource_share": state["metrics"]["B_resource_share"]})


# --------------------------------------------------------------------------
# pohledy hracu (BUILD.md cast 2, pravidla cast 2)
# --------------------------------------------------------------------------

HIDDEN_FIELDS = ("law", "tech", "prosperity_index", "law_threshold",
                 "poverty_streak", "wealth_peak", "last_coup_turn", "coverage")


def _goods_view(e: dict) -> dict:
    """Verejny prehled goods: vyroba, potreba a jejich rozdil (v1.2)."""
    out = float(e.get("goods_out") or 0.0)
    need = float((e.get("need") or {}).get(GOODS, 0.0))
    return {"vyroba": round(out, 3), "potreba": round(need, 3),
            "bilance": round(out - need, 3)}


def _wars_view(state, pid: str) -> list[dict]:
    """3.3a (v1.10, V14): valky v pohledu. Ucastnik vidi nabidku primeri druhe strany s navodem,
    jak ji prijmout, a vlastni cekajici nabidku."""
    turn = int(state["meta"]["turn"])
    out = []
    for w in state.get("wars", []):
        item = {k: w[k] for k in ("id", "aggressor", "defender", "since", "how", "over")}
        offers = w.get("cancel") or {}
        for who, since in offers.items():
            item.setdefault("nabidky_primeri", []).append({"od": who, "z_tahu": int(since)})
        if pid in (w["aggressor"], w["defender"]):
            other = w["defender"] if pid == w["aggressor"] else w["aggressor"]
            if other in offers:
                item["nabidka_primeri_pro_tebe"] = {
                    "od": other, "prijmi_v_tahu": int(offers[other]) + 1,
                    "jak": {"type": "cancel", "deal_id": w["id"]},
                    "vysvetleni": "Druhá strana nabízí příměří. Pošli v tomto tahu cancel s deal_id této války: "
                                  "válka skončí příměřím a oba ztratíte jen 10 % vlivu. Neodpovíš-li, nabídka "
                                  "propadne bez následku a válka pokračuje."}
            if pid in offers:
                item["tvoje_nabidka_primeri"] = {
                    "z_tahu": int(offers[pid]), "ceka_do_tahu": int(offers[pid]) + 1,
                    "vysvetleni": "Nabídl jsi příměří. Pošle-li druhá strana cancel v tomto tahu, je to příměří "
                                  "(−10 % vlivu oběma); jinak nabídka propadne bez následku a válka pokračuje."}
            # ustup je jen vyslovny
            item["ustup"] = {"jak": {"type": "cancel", "deal_id": w["id"], "retreat": True},
                             "vysvetleni": "Ústup ukončí válku okamžitě a stojí tě 30 % vlivu u všech států."}
        out.append(item)
    return out


def build_views(state, npcdata) -> dict:
    views = {}
    C = state["players"]["C"]
    orit_on = state["phase"] in ORIT_PHASES
    # jmena NPC z npc.json, aby hraci nepletli ID a jmena ve svych textech
    names = {x["id"]: x.get("name") for x in npcdata.get("npc", [])}
    for pid in ("A", "B", "C"):
        if pid == "C" and not C["active"]:
            continue
        npc_view = {}
        for i, nn in state["npc"].items():
            item = {
                "name": names.get(i),
                "wealth": round(float(nn["wealth"]) + float(nn.get("paper_wealth", 0.0)), 2),
                "power": round(float(nn["power"]), 2),
                "prod": {k: round(float(v), 3) for k, v in nn["prod"].items()},
                "need": {k: round(float(v), 3) for k, v in (nn.get("need") or {}).items()},
                "industry": round(float(nn.get("industry") or 0.0), 3),
                "goods": _goods_view(nn),
                "status": nn["status"],
                "pop": round(float(nn["pop"]), 2),
                "coups": int(nn.get("coups", 0)),
                "kind": nn.get("kind", "normal"),
            }
            if pid in ("A", "B"):
                item["influence_moje"] = round(float(nn["influence"].get(pid, 0.0)), 3)
                item["dluzi_mne"] = round(float(nn["debt"].get(pid, 0.0)), 3)
            else:
                item["dluzi_mne"] = round(float(nn["debt"].get("C", 0.0)), 3)
                if i in C["members"] or i in C["candidates"]:
                    item["law"] = round(float(nn["law"]), 3)
                    item["tech"] = round(float(nn["tech"]), 3)
            npc_view[i] = item
        me = state["players"][pid]
        mine = {
            "wealth": round(float(me["wealth"]), 2),
            "paper_wealth": round(float(me.get("paper_wealth", 0.0)), 2),
            "power": round(float(me["power"]), 2),
        }
        if pid in ("A", "B"):
            mine["prod"] = {k: round(float(v), 3) for k, v in me["prod"].items()}
            mine["need"] = {k: round(float(v), 3) for k, v in (me.get("need") or {}).items()}
            mine["industry"] = round(float(me.get("industry") or 0.0), 3)
            mine["goods"] = _goods_view(me)
            mine["pop"] = round(float(me["pop"]), 2)
            mine["law"] = round(float(me["law"]), 3)
            mine["tech"] = round(float(me["tech"]), 3)
            mine["occupied"] = list(me.get("occupied", []))
            # 2 (v1.4): hrac vidi vlastni zasoby, cizi ne
            mine["stock"] = {k: round(float(v), 3) for k, v in (me.get("stock") or {}).items()}
            # 2 (v1.10.1): co hrac minuly tah prodal a nakoupil na automatickem trhu
            mine["automaticky_obchodovano"] = dict(me.get("auto_last") or {})
        else:
            mine["members"] = list(C["members"])
            mine["candidates"] = list(C["candidates"])
            # 7.2 (v1.9): platna sazba cla a sazba ohlasena na pristi tah
            mine["clo"] = tariff_rate(state)
            mine["clo_od_pristiho_tahu"] = C.get("tariff_next")
        views[pid] = {
            "turn": state["meta"]["turn"],
            "day": state["meta"]["day"],
            "slot": state["meta"]["slot"],
            "ja": mine,
            "npc": npc_view,
            "ceny": {r: market_price(state, r) for r in TRADEABLES
                     if r != "orit" or orit_on},
            "deals": [d for d in state["deals"] if d["owner"] == pid],
            # 3.4 a 3.5 (v1.6): nabidky NPC a soukromy log rozhodnuti NPC
            "nabidky": [o for o in state.get("offers", []) if o["player"] == pid],
            "soukromy_log": list(state.get("private_log", {}).get(pid, [])),
            "news": list(state.get("news", [])),
            "valky": _wars_view(state, pid),   # 3.3a (v1.10): valky verejne, nabidka primeri (V14)
        }
        if C["active"]:
            views[pid]["clo_unie"] = tariff_rate(state)   # 7.2 (v1.9): verejna sazba cla
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

    st["npc_decisions"] = []
    st["counter_offers"] = [c for c in st.get("counter_offers", []) if int(c["expires"]) >= turn]
    # 4.1b (v1.10.2): cena tahu je spocitana uz na konci minuleho tahu a hraci ji videli v pohledu
    if int(st.get("prices_turn") or 0) == turn and st.get("prices"):
        trace.add("4.1b cena tahu z pohledu", {"tah": turn}, dict(st["prices"]))
    else:
        step_prices(st, trace)
        st["prices_turn"] = turn
    events = apply_actions(st, npcdata, actions, rng, trace)
    upkeep_deals(st, trace, events)
    step_wars(st, trace, events)   # 3.3a (v1.10)
    grain_deficit = step_resources(st, npcdata, trace, events)
    step_growth(st, grain_deficit, trace)
    step_npc_auto_invest(st, trace, events)
    step_income(st, trace)
    step_industry(st, grain_deficit, trace)
    step_poverty(st, npcdata, grain_deficit, trace, events)
    step_repayments(st, trace, events)
    step_invasions(st, npcdata, trace, events)
    step_influence(st, trace, events)
    step_minsky(st, npcdata, rng, trace, events)
    step_union(st, npcdata, trace, events)
    step_offers(st, npcdata, trace, events)
    step_metrics(st, trace)

    pop_after = sum(float(ent(st, i)["pop"]) for i in world_ids(st))
    trace.add("kontrola pop", {"pred": round(pop_before, 3)},
              {"po": round(pop_after, 3), "rozdil": round(pop_after - pop_before, 3)})

    # jednorazove obchody z prijatych nabidek (3.5) po vyuziti mizi
    st["deals"] = [d for d in st["deals"] if not d.get("one_shot")]
    # log sankci pro 3.4 a soukromy log hracu drzi jen posledni tahy
    st["minsky"]["pressure_log"] = [r for r in st["minsky"].get("pressure_log", [])
                                    if int(r["turn"]) > turn - 7]
    for p_id in ("A", "B", "C"):
        st["private_log"][p_id] = [r for r in st["private_log"].get(p_id, [])
                                   if int(r["turn"]) > turn - 9]
    for n_id, n_e in st["npc"].items():
        ih = list(n_e.get("influence_history") or [])
        ih.append({k: round(float(v), 4) for k, v in n_e["influence"].items()})
        n_e["influence_history"] = ih[-3:]
    for n_id, n_e in st["npc"].items():
        hist = list(n_e.get("wealth_history") or [])
        hist.append(round(float(n_e["wealth"]), 4))
        n_e["wealth_history"] = hist[-3:]
    st.pop("_trade", None)
    st.pop("_poverty", None)
    st.pop("_npc_trade_volume", None)
    st.pop("_goods_trade_volume", None)
    st.pop("_player_imports", None)
    st.pop("_goods_sold", None)
    st.pop("_need_wealth", None)
    st.pop("_union_tariff", None)
    st.pop("_ab_volume", None)
    st.pop("_ab_auto", None)
    st.pop("_spec_offer", None)
    # 7.2 (v1.9): sazba z set_tariff plati od dalsiho tahu
    if st["players"]["C"].get("tariff_next") is not None:
        st["players"]["C"]["tariff_rate"] = st["players"]["C"]["tariff_next"]
        st["players"]["C"]["tariff_next"] = None
    st["players"]["C"]["fund"] = st["players"]["C"]["wealth"]
    st["log"] = (st.get("log", []) + [{"turn": turn, "events": events}])[-9:]
    # 4.1b (v1.10.2): cena pristiho tahu predem, aby ji pohled ukazal a trade_offer se hodnotil proti ni
    precompute_prices(st, trace)
    return st, events, trace.items

"""run_chronicle.py

Kronika dne, tydne a finale (BUILD.md cast 5, prompts/kronikar.md).

  - denni: po tahu ve 20:00, jen kdyz existuji vsechny tri snimky dne (pravidla 10.7),
  - tydenni: herni dny 7, 14, 21, 28 misto denni, se vsemi kronikami tydne,
  - den 30: finale, kronikar navic dostane secrets/cil_*.md a metriky po dnech.

Prepinace:
    python run_chronicle.py                 kronika posledniho uplneho dne
    python run_chronicle.py --day N         kronika dne N
    python run_chronicle.py --dry-model     jen sestavi vstup do debug/, bez volani modelu
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import config
import engine

DEBUG_DIR = config.ROOT / "debug"
WEEKLY_DAYS = (7, 14, 21, 28)
FINAL_DAY = 30


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def day_turns(day: int) -> list[int]:
    return [t for t in range(3 * (day - 1) + 1, 3 * day + 1)]


def _state_for_chronicle(state) -> dict:
    s = json.loads(json.dumps(state))
    # v2.0.1: bez logu a bez poli, ktera kronikar dostava po kolech jinde (odpovedi statu, zpravy, nabidky)
    for k in ("log", "private_log", "npc_decisions", "offers", "offers_new", "counter_offers", "messages_pending"):
        s.pop(k, None)
    for n in (s.get("npc") or {}).values():
        n.pop("influence_history", None)
        n.pop("wealth_history", None)
    return s


def _cj(obj) -> str:
    """Kompaktni JSON pro vstup kronikare (v2.0.1)."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _zapisy(moves: dict) -> dict:
    """v2.0: snimky do v1.14b nesou pole private_reasoning; kronikar dostane vsude duverny_zapis vlady."""
    out = {}
    for pid, m in (moves or {}).items():
        m = dict(m or {})
        if "private_reasoning" in m:
            old = m.pop("private_reasoning")
            m.setdefault("duverny_zapis", old)
        out[pid] = m
    return out


MOVE_KEYS = ("public_statement", "duverny_zapis", "poznamky_pro_pristi_tah", "domestic_action", "message",
             "silent", "mlci", "zaloha")


def _move_for_chronicle(m: dict) -> dict:
    """v2.0.1: z tahu hrace jen to, co kronikar pouziva: projev, duverny zapis, poznamky, domaci akce, zprava,
    mlceni, zaloha a nazev zanru (bez usage, pokusu a otazek)."""
    out = {k: m[k] for k in MOVE_KEYS if m.get(k) not in (None, "", False)}
    if isinstance(m.get("genre"), dict):
        out["zanr"] = m["genre"].get("name")
    return out


def _compact_state(st) -> dict:
    """v2.0.1: kompaktni stav kola: faze, ceny, metriky, cena oritu, banky, Unie a u kazdeho statu bohatstvi,
    sila, obyvatelstvo, prumysl, status, vliv a dluhy."""
    r = lambda v, d=1: round(float(v or 0.0), d)
    staty = {}
    for pid in ("A", "B"):
        p = st["players"][pid]
        staty[pid] = {"wealth": r(p.get("wealth")), "paper_wealth": r(p.get("paper_wealth")), "power": r(p.get("power")),
                      "pop": r(p.get("pop")), "industry": r(p.get("industry"), 2), "occupied": p.get("occupied") or []}
    for nid, n in st["npc"].items():
        staty[nid] = {"wealth": r(n.get("wealth")), "paper_wealth": r(n.get("paper_wealth")), "power": r(n.get("power")),
                      "pop": r(n.get("pop")), "industry": r(n.get("industry"), 2), "status": n.get("status"),
                      "vliv": {k: r(v) for k, v in (n.get("influence") or {}).items()},
                      "dluh": {k: r(v) for k, v in (n.get("debt") or {}).items() if float(v or 0) > 0.05},
                      "prod_orit": r((n.get("prod") or {}).get("orit"))}
    C = st["players"]["C"]
    banky = {k: {"kapital": r(b.get("capital")), "padle": bool(b.get("failed"))}
             for k, b in (("K", st.get("banks_K")), ("AUR", st.get("banks_AUR")), ("U", st.get("bank_U"))) if b}
    return {"phase": st.get("phase"), "prices": st.get("prices"), "orit_price": (st.get("minsky") or {}).get("orit_price"),
            "metrics": st.get("metrics"), "banky": banky,
            "unie": {"active": bool(C.get("active")), "name": C.get("name"), "members": C.get("members") or [],
                     "candidates": C.get("candidates") or [], "fund": r(C.get("wealth")),
                     "rada": (C.get("council_votes") or [])[-3:]} if C.get("active") else {"active": False},
            "staty": staty, "deals": [{k: d.get(k) for k in ("id", "type", "owner", "target", "res", "qty", "price")}
                                      for d in st.get("deals") or []], "wars": st.get("wars") or []}


def chronicle_prompt(day: int, snapshots: list[dict], state_before, state_after,
                     prev_chronicle: str | None, week_chronicles: dict | None = None,
                     metrics_by_day: dict | None = None) -> tuple[str, str]:
    """Vraci (system, user) pro kronikare. snapshots jsou snimky history/turn_NNN.json dne."""
    kind = "finale" if day == FINAL_DAY else ("tydenni" if day in WEEKLY_DAYS else "denni")
    system_parts = [(config.PROMPTS_DIR / "kronikar.md").read_text(encoding="utf-8").strip(),
                    "# docs/faze.md\n\n" + (config.DOCS_DIR / "faze.md").read_text(encoding="utf-8").strip()]
    if kind == "finale":
        for pid in ("A", "B", "C"):
            system_parts.append("# secrets/cil_%s.md\n\n" % pid
                                + (config.SECRETS_DIR / ("cil_%s.md" % pid)).read_text(encoding="utf-8").strip())
    system = "\n\n".join(system_parts)

    # v2.0.1: za kazde kolo projevy, duverne zapisy, poznamky, Zpravy sveta, akce s vysledky, dorucene zpravy
    # a kompaktni stav; plny stav jen po poslednim kole roku
    turns = []
    events = []
    for snap in snapshots:
        st = snap.get("state") or {}
        turns.append({"turn": snap["turn"], "cas": engine.game_time(snap["turn"]),
                      "tahy": {pid: _move_for_chronicle(m) for pid, m in _zapisy(snap.get("turns", {})).items()},
                      "akce": snap.get("actions", []), "vyrazene": snap.get("rejected", []),
                      "odpovedi_statu": [{k: d.get(k) for k in ("player", "npc", "action", "outcome", "reason")}
                                         for d in st.get("npc_decisions") or []],
                      "dorucene_zpravy": snap.get("delivered_messages", []),
                      "zpravy": snap.get("news", []),
                      "stav_po_kole": _compact_state(st) if st else None})
        events.append({"turn": snap["turn"], "events": snap.get("events", [])})
    phase = state_after["phase"]
    parts = [
        "# %s (%s), fáze %s" % (engine.game_time(day_turns(day)[0], season=False).capitalize(),
                                   {"denni": "roční kronika", "tydenni": "bilance sedmi let",
                                    "finale": "finále"}[kind], phase),
        "",
        "## Kola roku: jaro, léto, zima (projevy, důvěrné zápisy vlád, poznámky hráčů do spisu, akce, vyřazené akce, "
        "odpovědi států, doručené zprávy, Zprávy světa, kompaktní stav po kole)",
        "```json", _cj(turns), "```", "",
        "## Události od enginu",
        "```json", _cj(events), "```", "",
        "## Stav před rokem (kompaktní)",
        "```json", _cj(_compact_state(state_before)), "```", "",
        "## Stav po roce (úplný)",
        "```json", _cj(_state_for_chronicle(state_after)), "```", "",
        "## Loňská kronika",
        prev_chronicle or "(žádná)",
    ]
    if week_chronicles:
        parts += ["", "## Kroniky sedmi let"]
        for d in sorted(week_chronicles):
            parts += ["", "### %s" % engine.game_time(day_turns(d)[0], season=False).capitalize(), week_chronicles[d]]
    if metrics_by_day:
        parts += ["", "## Metriky po letech (den rozvrhu = herní rok)", "```json", dump(metrics_by_day), "```"]
    return system, "\n".join(parts)


def load_history_day(day: int):
    snaps = []
    for t in day_turns(day):
        p = config.HISTORY_DIR / ("turn_%03d.json" % t)
        if not p.exists():
            return None
        snaps.append(json.loads(p.read_text(encoding="utf-8")))
    return snaps


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--day", type=int)
    ap.add_argument("--dry-model", action="store_true")
    args = ap.parse_args()
    state = json.loads(config.STATE_PATH.read_text(encoding="utf-8"))
    day = args.day or engine.day_of(int(state["meta"]["turn"]))
    snaps = load_history_day(day) if day >= 1 else None
    if not snaps:
        print("den %d nema vsechny tri snimky, kronika se preskakuje (pravidla 10.7)" % day)
        return 0
    first = day_turns(day)[0]
    before_p = config.HISTORY_DIR / ("turn_%03d.json" % (first - 1))
    state_before = json.loads(before_p.read_text(encoding="utf-8"))["state"] if before_p.exists() else state
    prev = config.CHRONICLE_DIR / ("day_%02d.md" % (day - 1))
    week = None
    if day in WEEKLY_DAYS:
        week = {d: (config.CHRONICLE_DIR / ("day_%02d.md" % d)).read_text(encoding="utf-8")
                for d in range(day - 6, day) if (config.CHRONICLE_DIR / ("day_%02d.md" % d)).exists()}
    system, user = chronicle_prompt(day, snaps, state_before, snaps[-1]["state"],
                                    prev.read_text(encoding="utf-8") if prev.exists() else None, week)
    if args.dry_model:
        DEBUG_DIR.mkdir(exist_ok=True)
        name = "day_%03d_kronikar%s.md" % (day, "_tydenni" if day in WEEKLY_DAYS else "")
        (DEBUG_DIR / name).write_text("# Vstup kronikáře, den %d\n\n## system\n\n%s\n\n## user\n\n%s\n"
                                      % (day, system, user), encoding="utf-8")
        print("zapsano debug/%s" % name)
        return 0
    # ostre volani kronikare (CHRONICLER_MODEL), vystup chronicle/day_NN.md
    from run_turn import call_model
    if day == FINAL_DAY:
        metrics = {}
        for d in range(1, FINAL_DAY + 1):
            p = config.HISTORY_DIR / ("turn_%03d.json" % (3 * d))
            if p.exists():
                metrics[d] = json.loads(p.read_text(encoding="utf-8"))["state"].get("metrics", {})
        system, user = chronicle_prompt(day, snaps, state_before, snaps[-1]["state"],
                                        prev.read_text(encoding="utf-8") if prev.exists() else None,
                                        None, metrics)
    usage = []
    text = call_model(config.CHRONICLER_MODEL, system, user, max_tokens=16000, usage_log=usage, label="kronikar")
    for u in usage:
        print("usage %s in %d, out %d, %.4f USD" % (u["model"], u["input_tokens"], u["output_tokens"], u["cost_usd"]))
    if not text.strip():
        print("kronikar nevratil text, kronika dne %d nezapsana" % day)
        return 1
    config.CHRONICLE_DIR.mkdir(exist_ok=True)
    out = config.CHRONICLE_DIR / ("day_%02d.md" % day)
    out.write_text(text.strip() + "\n", encoding="utf-8")
    import web_data
    web_data.write_chronicle_index()   # chronicle/index.json pro web
    print("zapsano %s" % out.relative_to(config.ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())

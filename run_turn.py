"""run_turn.py

Orchestrace jednoho tahu podle BUILD.md cast 3.

  1. nacte state.json; je-li meta.paused, skonci bez zmeny,
  2. engine vygeneruje pohledy (views/X.json),
  3. paralelne zavola hrace (A, B, a C, pokud je Unie aktivni); kazdy dostane svuj prompt,
     svuj tajny cil, docs/format_tahu.md, svuj pohled, poslednich 9 tahu verejneho logu
     (projevy, Zpravy sveta, verejne akce, bez private_reasoning) a soukrome zpravy pro nej
     z minuleho tahu; neplatny JSON = 2 opakovani, pak mlceni (pravidla 10.6),
  4. rozhodci prelozi tahy na akce (actions, rejected, rulings),
  5. engine prepocita svet,
  6. rozhodci podruhe jen z events napise news,
  7. validate.py; pri uspechu state.json, history/turn_NNN.json, history/index.json,
     docs/rulings.md, commit a push; pri selhani history/failed_turn_NNN.json.

Prepinace:
    python run_turn.py --once                 jeden ostry tah
    python run_turn.py --dry-model            jen sestavi prompty tahu do debug/, bez volani modelu
    python run_turn.py --only C               jen vybrani hraci (bez rozhodciho a prepoctu)
    python run_turn.py --state CESTA          jiny vstupni stav nez state.json
    python run_turn.py --no-apply             nic nezapisuje do stavu, historie ani gitu;
                                              odpovedi hracu jdou do debug/
    python run_turn.py --rollback N           vrati state.json na snimek tahu N

Soubory v debug/: hraci A a B turn_NNN_X.md, Unie unie_C.md, rozhodci turn_NNN_rozhodci.md,
odpovedi <stejny prefix>_response.json.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import datetime
import json
import os
import random
import re
import shutil
import subprocess
import sys
import zlib
from pathlib import Path

import config
import engine
from validate import validate, validate_views

DEBUG_DIR = config.ROOT / "debug"
REFEREE_RULES_PATH = config.DOCS_DIR / "pravidla_rozhodci.md"
PROMPT_FILES = {"A": "hrac_A.md", "B": "hrac_B.md", "C": "hrac_unie.md"}
SECRET_FILES = {"A": "cil_A.md", "B": "cil_B.md", "C": "cil_C.md"}
SILENT_STATEMENT = "Vláda nevydala prohlášení."
# v1.12: kratsi uvaha znamena neuplnou odpoved (tah 4: prazdna uvaha i akce pri platnem JSON)
MIN_REASONING_CHARS = 80
# delka odpovedi: strop tokenu pro hrace a rozhodciho
PLAYER_MAX_TOKENS = 5000
REFEREE_MAX_TOKENS = 4000
# premysleni: hraci adaptivne s nizkym usilim (Opus 5 budget_tokens odmita), rozhodci bez premysleni
PLAYER_THINKING = {"type": "adaptive"}
PLAYER_EFFORT = "low"
REFEREE_THINKING = {"type": "disabled"}
OVER_LIMIT_REASON = "nad limit akcí"

# Co hrac nikdy nesmi dostat (zadani 14. 9. 2026, bod 7). Klice se hledaji v pohledu
# a ve verejnem logu; law a tech se hlidaji zvlast, protoze C je u clenu a kandidatu vidi.
FORBIDDEN_KEYS = ("private_reasoning", "openness", "prosperity_index", "law_threshold",
                  "metrics", "influence", "debt", "paper_wealth_detail")


# --------------------------------------------------------------------------
# pomocne
# --------------------------------------------------------------------------

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


# pohled hrace: bez odsazeni, cisla na 1 desetinne misto; ceny a clo na 2, jinak by se
# ztratila sazba po 0.05 a pasmo ceny u trade_offer (docs/OPEN_QUESTIONS.md, v1.10)
PRECISE_KEYS = ("ceny", "clo", "clo_unie", "clo_od_pristiho_tahu", "price", "price_per_unit", "prumerna_cena")
PLAYER_NAMES = {"A": "Kalverská federace", "B": "Lidová republika Ostrogard"}


def capitals(npc: dict) -> dict:
    """v1.13 (cast 3): hlavni mesta A, B a NPC z npc.json (pole capital)."""
    out = {pid: (npc.get("players", {}).get(pid) or {}).get("capital") for pid in ("A", "B")}
    out.update({x["id"]: x.get("capital") for x in npc.get("npc", [])})
    return {k: v for k, v in out.items() if v}


def union_capital(state, npc: dict) -> str | None:
    """Zprava o Unii nese hlavni mesto prvniho clena (Unie vlastni mesto nema)."""
    members = state["players"]["C"].get("members") or []
    return capitals(npc).get(members[0]) if members else None


def names_block(state) -> str:
    """6 (v1.10.1): mapa ID na jmena statu pro rozhodciho a Zpravy sveta; v1.13 i hlavni mesta."""
    npc = json.loads(read_text(config.NPC_PATH))
    names = dict(PLAYER_NAMES)
    names["C"] = state["players"]["C"].get("name") or "Unie"
    names.update({x["id"]: x.get("name") for x in npc.get("npc", [])})
    caps = {names[k]: v for k, v in capitals(npc).items()}
    if union_capital(state, npc):
        caps[names["C"]] = union_capital(state, npc)
    return "\n".join(["## Jména států (ID → jméno)", "```json",
                      json.dumps(names, ensure_ascii=False), "```",
                      "Ve Zprávách piš jména států, nikdy ID.", "",
                      "## Hlavní města (stát → město, pro dateline)", "```json",
                      json.dumps(caps, ensure_ascii=False), "```"])


def fill_auto_block(state, views) -> None:
    """2 (v1.10.1): blok automaticky_obchodovano pro stav zapsany pred reformou doplni ze snimku tahu."""
    p = history_path(int(state["meta"]["turn"]))
    if not p.exists():
        return
    applied = None
    for pid in ("A", "B"):
        ja = (views.get(pid) or {}).get("ja")
        if ja is None or ja.get("automaticky_obchodovano"):
            continue
        if applied is None:
            applied = json.loads(read_text(p)).get("applied_rules") or []
        ja["automaticky_obchodovano"] = engine.auto_trades_summary(applied, pid)


def _round_view(obj, digits=1):
    if isinstance(obj, float):
        return round(obj, digits)
    if isinstance(obj, dict):
        return {k: _round_view(v, 2 if k in PRECISE_KEYS else digits) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_view(v, digits) for v in obj]
    return obj


def dump_view(view) -> str:
    return json.dumps(_round_view(view), ensure_ascii=False, separators=(",", ":"))


def load_state(path: Path):
    # debug soubory nesou na prvnim radku komentar s odhadem tokenu ("// vstup: ...")
    text = "\n".join(l for l in read_text(path).split("\n") if not l.startswith("//"))
    state = json.loads(text)
    npcdata = json.loads(read_text(config.NPC_PATH))
    engine.normalize(state)
    engine.precompute_needs(state)   # v1.11: potreby pro pohled tahu 1 (u pozdejsich tahu uz jsou)
    return state, npcdata


def next_turn(state) -> int:
    return int(state["meta"]["turn"]) + 1


def active_players(state) -> list[str]:
    return ["A", "B"] + (["C"] if state["players"]["C"].get("active") else [])


SLOT_HOURS = (7, 13, 20)   # sloty 07:00, 13:00 a 20:00 prazskeho casu (jen vypocet, ne cas spusteni)


def prague_now() -> datetime.datetime:
    """Prazsky cas. Hra bezi cela v letnim case, bez tzdata se proto bere UTC+2."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo(config.TIMEZONE))
    except Exception:
        return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=2)))


def expected_turns(state, now=None):
    """Kolik tahu ma byt odehrano ted: 3 x (dnesek - meta.day1_date) + dnesni sloty."""
    day1 = (state.get("meta") or {}).get("day1_date")
    if not day1:
        return None
    now = now or prague_now()
    days = (now.date() - datetime.date.fromisoformat(day1)).days
    if days < 0:
        return 0
    return max(0, 3 * days + sum(1 for h in SLOT_HOURS if now.hour >= h))


def chronicle_needed(state):
    """Den, ktery ma odehrany slot 3 a jeste nema kroniku, jinak None."""
    turn = int(state["meta"]["turn"])
    if turn <= 0 or turn % 3 != 0:
        return None
    day = engine.day_of(turn)
    return None if (config.CHRONICLE_DIR / ("day_%02d.md" % day)).exists() else day


def schedule_plan(state, force=False) -> dict:
    """Samoopravny rozvrh: co ma bezici workflow ted udelat."""
    meta = state["meta"]
    turn = int(meta["turn"])
    nxt = turn + 1
    label_turn = "tah %03d (den %d, slot %d)" % (nxt, engine.day_of(nxt), engine.slot_of(nxt))
    den = chronicle_needed(state)
    if meta.get("paused") and not force:
        return {"plan": "pauza", "turns": 0, "label": "pauza", "chronicle_day": ""}
    if force:
        return {"plan": "hrat", "turns": 1, "label": label_turn, "chronicle_day": ""}
    expected = expected_turns(state)
    if expected is None:
        return {"plan": "chyba", "turns": 0, "label": "chybi meta.day1_date", "chronicle_day": ""}
    behind = expected - turn
    if behind > 0:
        return {"plan": "hrat", "turns": min(2, behind), "label": label_turn, "chronicle_day": ""}
    if den is not None:
        return {"plan": "kronika", "turns": 0, "label": "kronika dne %d" % den, "chronicle_day": str(den)}
    return {"plan": "nic", "turns": 0, "label": "nic k tahu", "chronicle_day": ""}


def gh_output(**values) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        for k, v in values.items():
            f.write("%s=%s\n" % (k, v))


def gh_summary(text: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def history_path(turn: int) -> Path:
    return config.HISTORY_DIR / ("turn_%03d.json" % turn)


# --------------------------------------------------------------------------
# verejny log a soukrome zpravy (BUILD.md cast 3, bod 3)
# --------------------------------------------------------------------------

def public_log(turn: int) -> list[dict]:
    """Poslednich PUBLIC_LOG_TURNS tahu z history/: projevy, Zpravy sveta a verejne akce.

    private_reasoning se nepredava nikomu (ani vlastni), text soukromych zprav take ne;
    z akce message zustane jen, kdo komu psal.
    """
    out = []
    for t in range(max(1, turn - config.PUBLIC_LOG_TURNS), turn):
        p = history_path(t)
        if not p.exists():
            continue
        snap = json.loads(read_text(p))
        statements = {}
        for pid, move in (snap.get("turns") or {}).items():
            statements[pid] = move.get("public_statement", SILENT_STATEMENT)
        actions = []
        for a in snap.get("actions") or []:
            a = {k: v for k, v in a.items() if k != "text"}
            actions.append(a)
        out.append({"turn": t, "day": engine.day_of(t), "projevy": statements,
                    "zpravy": list(snap.get("news") or []), "verejne_akce": actions})
    return out


def private_messages(state, pid: str) -> list[dict]:
    """Soukrome zpravy adresovane hraci z minuleho tahu (od hracu i NPC)."""
    return [{"od": m.get("from"), "text": m.get("text", "")}
            for m in state.get("messages_pending", []) if m.get("to") == pid]


# --------------------------------------------------------------------------
# pamet hracu (v1.11, E9 az E11): jen z vlastnich uvah a dat enginu
# --------------------------------------------------------------------------

MEMORY_TURNS = 1   # tve_minule_uvahy: jen minuly tah (dlouhodobou pamet si hrac vede v poznamkach)
NOTES_FIELD = "poznamky_pro_pristi_tah"
MEMORY_PLAYERS = ("A", "B")
OPPONENT = {"A": "B", "B": "A"}
# udalosti soupere, ktere jsou verejne (bez vlivu a soukromeho logu)
PUBLIC_EVENT_KINDS = ("protect_started", "protect_withdrawn", "trade_opened", "cancel", "pressure_started",
                      "invade_progress", "occupied", "war_declared", "war_end", "war_cancel_offered",
                      "war_cancel_expired", "arm", "loan_given", "offer_accepted", "sphere", "sphere_released",
                      "invest_tech_done", "invest_law_done", "invest_industry_done", "invest_prod_done",
                      "explore", "orit_found", "union_join", "union_candidate")
# vlastni vysledky navic (odmitnuti a investice jsou v jinych polich bloku)
OWN_EVENT_KINDS = PUBLIC_EVENT_KINDS + ("competition_lost", "message")


def load_snapshot(turn: int):
    p = history_path(turn)
    return json.loads(read_text(p)) if turn >= 1 and p.exists() else None


def _r(x, d=1):
    return round(float(x or 0.0), d)


def memory_reasoning(turn: int, pid: str) -> list[dict]:
    """E9: vlastni private_reasoning z poslednich 3 tahu s cislem tahu, nikdy cizi."""
    out = []
    for t in range(max(1, turn - MEMORY_TURNS), turn):
        snap = load_snapshot(t)
        move = ((snap or {}).get("turns") or {}).get(pid) or {}
        text = move.get("private_reasoning") or ""
        if text:
            out.append({"tah": t, "uvaha": text})
    return out


def memory_notes(turn: int, pid: str) -> str:
    """Doslovne poznamky hrace pid z minuleho tahu (v tahu 1 prazdne); nikdy cizi."""
    snap = load_snapshot(turn - 1)
    move = ((snap or {}).get("turns") or {}).get(pid) or {}
    return move.get(NOTES_FIELD) or ""


def _compact(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _public_event(e: dict, pid: str, kinds=PUBLIC_EVENT_KINDS) -> dict | None:
    owner = e.get("player") or (e.get("deal") or {}).get("owner")
    if e.get("private") or owner != pid or e.get("kind") not in kinds:
        return None
    return {k: v for k, v in e.items() if k not in ("player", "private") and "influence" not in k}


SHORT_NAMES = {"A": "Kalvera", "B": "Ostrogard", "C": "Unie"}
OFFERED = {"A": "nabídla", "B": "nabídl", "C": "nabídla"}
RES_ACC = {"grain": "obilí", "oil": "ropu", "metal": "kovy", "goods": "produkt", "orit": "orit"}
RES_NOM = {"grain": "obilí", "oil": "ropa", "metal": "kovy", "goods": "produkt", "orit": "orit"}
STATUS_CZ = {"independent": "nezávislý", "sphere_A": "ve sféře Kalvery", "sphere_B": "ve sféře Ostrogardu",
             "occupied_A": "okupovaný Kalverou", "occupied_B": "okupovaný Ostrogardem",
             "union": "člen Unie", "candidate": "kandidát Unie"}
GENITIVE = {"A": "Kalvery", "B": "Ostrogardu", "C": "Unie"}
DATIVE = {"A": "Kalveře", "B": "Ostrogardu", "C": "Unii"}
INSTRUMENTAL = {"A": "Kalverou", "B": "Ostrogardem", "C": "Unií"}


def _num(x, d=1) -> str:
    return ("%.*f" % (d, float(x or 0.0))).replace(".", ",")


def _target_state(state, npcdata, viewer: str, actor: str, nid: str, kind: str, action: dict) -> str:
    """Verejny stav cile po kole, hola fakta. Cizi dluhy a cizi smlouvy se neuvadeji (pravidla cast 2)."""
    names = _state_names(state, npcdata)
    n = state["npc"].get(nid)
    if n is None:
        return ""
    parts = [STATUS_CZ.get(n["status"], n["status"]) + (", padlá říše" if n.get("kind") == "fallen" else "")]
    pact = next((d["owner"] for d in state["deals"] if d["type"] == "protect" and d["target"] == nid), None)
    parts.append("pakt s " + (INSTRUMENTAL.get(pact, names.get(pact, pact)) if pact else "nikým"))
    if kind == "trade_offer":
        mine = [d for d in state["deals"] if d["type"] == "trade" and d["owner"] == viewer and d["target"] == nid
                and not d.get("one_shot")]
        parts.append("smlouvy s %s: %s" % (INSTRUMENTAL[viewer], ", ".join(
            "%s %s (od tahu %d)" % (RES_NOM.get(d["res"], d["res"]), _num(d["qty"]), int(d["since"])) for d in mine)
            if mine else "žádné"))
    if kind in ("loan", "protect"):
        parts.append("dluh %s %s" % (DATIVE[viewer], _num(n["debt"].get(viewer, 0.0))))
    if kind == "invade":
        inv = next((v for v in state.get("invasions", []) if v["attacker"] == actor and v["target"] == nid), None)
        need = 10 if n.get("kind") == "fallen" else 6
        parts.append("invaze %s probíhá, tah %d z %d" % (GENITIVE[actor], int(inv["turns"]), need) if inv
                     else "žádná invaze")
    if kind == "pressure":
        on = any(d["type"] == "pressure" and d["owner"] == actor and d["target"] == nid for d in state["deals"])
        parts.append("sankce %s: %s" % (GENITIVE[actor], "ano" if on else "ne"))
    if kind == "admit":
        parts.append("člen Unie: %s" % ("ano" if n["status"] == "union" else "ne"))
    return "%s: %s." % (names.get(nid, nid), ", ".join(parts))


def opponent_action_lines(state, npcdata, viewer: str, actor: str, snap: dict) -> list[str]:
    """Akce soupere z minuleho kola a pod ni verejny stav cile; nikdy vysledek rozhodnuti ani duvod."""
    names = _state_names(state, npcdata)
    who = SHORT_NAMES[actor]
    out = []
    for a in snap.get("actions") or []:
        if a.get("player") != actor:
            continue
        t = a.get("type")
        tgt = a.get("target")
        tname = names.get(tgt, tgt)
        nid = tgt if tgt in state["npc"] else None
        if t == "protect":
            line = "%s %s pakt státu %s." % (who, OFFERED[actor], tname)
        elif t == "trade_offer":
            line = "%s %s státu %s %s %s za %s." % (who, OFFERED[actor], tname, RES_ACC.get(a.get("res"), a.get("res")),
                                                  _num(a.get("qty")), _num(a.get("price_per_unit"), 2))
        elif t == "loan":
            line = "%s %s půjčku státu %s ve výši %s." % (who, OFFERED[actor], tname, _num(a.get("amount")))
        elif t == "invade":
            line = "%s vedl%s invazi proti státu %s." % (who, "a" if actor != "B" else "", tname)
        elif t == "pressure":
            line = "%s uvalil%s sankce na stát %s." % (who, "a" if actor != "B" else "", tname)
        elif t == "declare_war":
            war = any(actor in (w["aggressor"], w["defender"]) and tgt in (w["aggressor"], w["defender"])
                      for w in state.get("wars", []))
            out.append("%s vyhlásil%s válku státu %s. Válka: %s." % (who, "a" if actor != "B" else "", tname,
                                                                     "ano" if war else "ne"))
            continue
        elif t == "cancel":
            did = a.get("deal_id") or ""
            if did.startswith("w"):
                war = any(w.get("id") == did for w in state.get("wars", []))
                out.append("%s poslal%s ke konci války %s. Válka trvá: %s." % (
                    who, "a" if actor != "B" else "", did, "ano" if war else "ne"))
            else:
                gone = not any(d.get("id") == did for d in state["deals"])
                out.append("%s zrušil%s závazek %s. Zrušeno: %s." % (who, "a" if actor != "B" else "", did,
                                                                     "ano" if gone else "ne"))
            continue
        elif t == "admit":
            line = "%s %s členství státu %s." % (who, OFFERED[actor], tname)
        elif t == "accept_offer":
            ev = next((e for e in snap.get("events") or [] if e.get("kind") == "offer_accepted"
                       and e.get("player") == actor and (e.get("offer") or {}).get("offer_id") == a.get("offer_id")), None)
            nid = (ev or {}).get("npc")
            line = "%s přijal%s nabídku státu %s." % (who, "a" if actor != "B" else "", names.get(nid, nid)) if nid \
                else "%s přijal%s nabídku jednoho ze států." % (who, "a" if actor != "B" else "")
        elif t == "message":
            out.append("%s poslal%s soukromou zprávu %s." % (who, "a" if actor != "B" else "",
                                                             DATIVE.get(tgt) or "státu %s" % tname))
            continue
        elif t in engine.DOMESTIC_TYPES or t in ("invest_tech", "invest_law", "invest_industry", "invest_prod"):
            what = {"invest_tech": "do technologie", "invest_law": "do institucí", "invest_industry": "do průmyslu",
                    "invest_prod": "do těžby", "arm": "do zbrojení", "explore": "do průzkumu ložisek"}.get(t, t)
            where = "u sebe" if not nid else "ve státě %s" % tname
            out.append("%s investoval%s %s %s." % (who, "a" if actor != "B" else "", what, where))
            continue
        else:
            line = "%s: %s%s." % (who, t, (" " + tname) if tname else "")
        out.append(line + (" " + _target_state(state, npcdata, viewer, actor, nid, t, a) if nid else ""))
    return out


def memory_since_last(state, pid: str, npcdata=None) -> dict:
    """E10: fakta od minuleho tahu hrace z dat enginu, bez hodnoceni."""
    turn = next_turn(state)
    last = turn - 1
    snap = load_snapshot(last)
    if snap is None:
        return {"poznamka": "Toto je tvůj první tah, minulý tah neexistuje."}
    before = (load_snapshot(last - 1) or {}).get("state")
    first = (load_snapshot(1) or {}).get("state")
    opp = OPPONENT[pid]
    me_now = state["players"][pid]

    def mine(st):
        return st["players"][pid] if st else None

    def change(field, digits=1):
        row = {"ted": _r(me_now.get(field), digits)}
        if before:
            row["zmena_od_minuleho_tahu"] = _r(float(me_now.get(field) or 0) - float(mine(before).get(field) or 0), digits)
        if first and last > 1:
            row["zmena_od_tahu_1"] = _r(float(me_now.get(field) or 0) - float(mine(first).get(field) or 0), digits)
        return row

    opp_move = (snap.get("turns") or {}).get(opp) or {}
    out = {
        "tah": last,
        "souper": {
            "stat": opp,
            "projev": opp_move.get("public_statement", SILENT_STATEMENT),
            # akce soupere a verejny stav cile po kole, bez vysledku rozhodnuti a bez duvodu
            "akce_a_verejny_stav": opponent_action_lines(state, npcdata, pid, opp, snap),
            "zpravy_sveta": list(snap.get("news") or []),
        },
        "ja": {
            "akce": [a for a in snap.get("actions") or [] if a.get("player") == pid],
            "vysledky": [x for x in (_public_event(e, pid, OWN_EVENT_KINDS) for e in snap.get("events") or []) if x],
            "odmitnuto_rozhodcim": [r for r in snap.get("rejected") or []
                                    if isinstance(r, dict) and r.get("player") == pid],
            "odmitnuto_enginem": [{k: v for k, v in r.items() if k != "turn"}
                                  for r in state.get("private_log", {}).get(pid, [])
                                  if int(r.get("turn") or 0) == last and r.get("outcome") == "vyrazeno"],
            "odlozene_investice": [{k: e.get(k) for k in ("kind", "type", "reason") if k in e}
                                   for e in snap.get("events") or []
                                   if e.get("player") == pid and e.get("kind") in ("investment_postponed",
                                                                                     "investment_cancelled")],
        },
        "wealth": change("wealth"),
        "power": change("power"),
        "law": change("law", 2),
        "tech": change("tech", 2),
        "industry": change("industry", 2),
    }
    if before:
        infl = {}
        for nid, n in state["npc"].items():
            a = float(n["influence"].get(pid, 0.0))
            b = float(before["npc"][nid]["influence"].get(pid, 0.0)) if nid in before["npc"] else 0.0
            if abs(a - b) >= 0.05:
                infl[nid] = {"ted": _r(a), "zmena": _r(a - b)}
        out["muj_vliv_u_npc"] = infl
        prices = {}
        for res, v in (state.get("prices") or {}).items():
            old = (before.get("prices") or {}).get(res)
            if old is not None and abs(float(v) - float(old)) >= 0.005:
                prices[res] = {"ted": round(float(v), 3), "zmena": round(float(v) - float(old), 3)}
        out["zmeny_cen"] = prices
        status = {}
        for nid, n in state["npc"].items():
            old = before["npc"].get(nid, {}).get("status")
            if old is not None and old != n["status"]:
                status[nid] = {"z": old, "na": n["status"]}
        for q in ("A", "B", "C"):
            if bool(state["players"][q].get("active")) != bool(before["players"][q].get("active")):
                status[q] = {"z": "aktivni" if before["players"][q].get("active") else "neaktivni",
                             "na": "aktivni" if state["players"][q].get("active") else "neaktivni"}
        out["zmeny_statusu"] = status
    out["nove_nabidky_npc"] = [o for o in state.get("offers_new", []) if o.get("player") == pid]
    return out


def memory_contracts(state, pid: str) -> dict:
    """E11: trvale obchody a pakty hrace s naklady nebo vynosem za tah."""
    items = []
    wealth = power = 0.0
    for d in state["deals"]:
        if d["owner"] != pid or d.get("one_shot"):
            continue
        if d["type"] == "trade":
            value = float(d["qty"]) * float(d["price"])
            w = value if d["direction"] == "npc_buys" else -value
            items.append({"id": d["id"], "typ": "obchod", "npc": d["target"], "res": d["res"],
                          "qty": _r(d["qty"], 2), "cena": d["price"],
                          "smer": "prodávám" if d["direction"] == "npc_buys" else "kupuji",
                          "od_tahu": d["since"], "wealth_za_tah": _r(w, 2), "power_za_tah": 0.0})
        elif d["type"] == "protect":
            items.append({"id": d["id"], "typ": "pakt", "npc": d["target"], "od_tahu": d["since"],
                          "wealth_za_tah": 0.0, "power_za_tah": -2.0})
        elif d["type"] == "pressure":
            items.append({"id": d["id"], "typ": "nátlak", "cil": d["target"], "od_tahu": d["since"],
                          "wealth_za_tah": -1.0, "power_za_tah": 0.0})
        else:
            continue
        wealth += items[-1]["wealth_za_tah"]
        power += items[-1]["power_za_tah"]
    return {"smlouvy": items, "celkem_za_tah": {"wealth": _r(wealth, 2), "power": _r(power, 2)},
            "poznamka": "Obchody v nominální výši smlouvy, bez cla; skutečné množství může být nižší."}


# --------------------------------------------------------------------------
# zanry projevu (v1.13, docs/zanry.md)
# --------------------------------------------------------------------------

GENRE_PLAYERS = ("A", "B", "C")
GENRE_SILENT = {"A": "Vláda dnes nevystoupila.", "B": "Vláda dnes nevystoupila.",
                "C": "Unie dnes nevydala prohlášení."}
LEAK_FROM_TURN = 22          # zanr 7 od 2. tydne (den 8)
LEAK_UNION_DELAY = 3         # Unie: nejdrive 3. tah po zalozeni
VARIANT_CHANCE = 1.0 / 3.0   # zanr 5: statni varianta misto dopisu

GENRES = {
    1: {"key": "komunike", "weight": {"A": 30, "B": 30, "C": 35}, "sentences": (2, 3), "questions": 0,
        "daily_max": {},
        "name": {"A": "Prohlášení federálního kabinetu", "B": "Sdělení tiskové agentury republiky",
                 "C": "Společné prohlášení členských vlád"},
        "form": {"A": "Úřední sdělení ve třetí osobě. Soupeře neoslovuješ.",
                 "B": "Úřední sdělení ve třetí osobě. Soupeře neoslovuješ.",
                 "C": "Úřední sdělení v množném čísle členských vlád („Členové Unie berou na vědomí...“). "
                      "Nikdy nejmenuješ jednotlivého člena."}},
    2: {"key": "otazka", "weight": {"A": 25, "B": 25, "C": 25}, "sentences": (2, 4), "questions": 1,
        "daily_max": {},
        "name": {p: "Odpověď zahraničnímu novináři" for p in GENRE_PLAYERS},
        "form": {p: "Odpověď na jednu otázku zahraničního novináře. Smíš uhnout." for p in GENRE_PLAYERS}},
    3: {"key": "tiskovka", "weight": {"A": 10, "B": 10, "C": 10}, "sentences": (4, 6), "questions": 2,
        "daily_max": {"A": 1, "B": 1, "C": 1},
        "name": {p: "Tisková konference" for p in GENRE_PLAYERS},
        "form": {p: "Tisková konference se dvěma otázkami, jednou k soupeři a jednou ke světu. "
                    "Odpověz na obě." for p in GENRE_PLAYERS}},
    4: {"key": "projev_domu", "weight": {"A": 10, "B": 10, "C": 8}, "sentences": (4, 6), "questions": 0,
        "daily_max": {"A": 1, "B": 1},
        "name": {"A": "Projev v Radě federace", "B": "Projev na sjezdu",
                 "C": "Projev předsedajícího na sněmu Unie"},
        "form": {"A": "Projev k vlastním lidem. Soupeře zmiňuješ jen nepřímo.",
                 "B": "Projev k vlastním lidem. Soupeře zmiňuješ jen nepřímo.",
                 "C": "Projev předsedajícího k členským vládám, ne k lidu. Předsedá: {chair}."}},
    5: {"key": "dopis", "weight": {"A": 15, "B": 15, "C": 15}, "sentences": (3, 4), "questions": 0,
        "daily_max": {},
        "name": {"A": "Otevřený dopis vládě", "B": "Otevřený dopis vládě", "C": "Dopis kandidátské zemi"},
        "form": {"A": "Zveřejněný dopis jedné vládě, kterou si vybereš. Jmenuješ jen adresáta.",
                 "B": "Zveřejněný dopis jedné vládě, kterou si vybereš. Jmenuješ jen adresáta.",
                 "C": "Zveřejněný dopis jedné zemi. Jmenuješ jen adresáta. Přípustní adresáti: {addressees}."},
        "variant_name": {"A": "Výroční zpráva obchodní komory", "B": "Úvodník stranického deníku",
                         "C": "Usnesení rady č. {resolution}"},
        "variant_form": {"A": "Suchá zpráva v tónu bankéře, jen hrubé poměry slovy.",
                         "B": "Nepodepsaný úvodník; nikdy nepřizná neúspěch.",
                         "C": "Suché usnesení nadepsané „Usnesení č. {resolution}“, s obratem „Rada rozhodla "
                              "poměrem hlasů“, bez uvedení, kdo byl proti."}},
    6: {"key": "ticho", "weight": {"A": 5, "B": 5, "C": 5}, "sentences": (0, 0), "questions": 0,
        "daily_max": {},
        "name": {"A": "Ticho", "B": "Ticho", "C": "Ticho"},
        "form": {p: "Dnes nevystupuješ: `public_statement` musí být prázdný řetězec \"\". "
                    "Engine zapíše „%s“." % GENRE_SILENT[p] for p in GENRE_PLAYERS}},
    7: {"key": "unik", "weight": {"A": 5, "B": 5, "C": 5}, "sentences": (2, 4), "questions": 1,
        "daily_max": {},
        "name": {p: "Odpověď na otázku k uniklé depeši" for p in GENRE_PLAYERS},
        "form": {p: "Zpráva světa dnes zveřejnila větu z tvé soukromé zprávy z minulého kola jako uniklou "
                    "depeši: „{leak}“. Odpovídáš na jednu otázku zahraničního novináře k tomuto úniku. "
                    "Smíš uhnout." for p in GENRE_PLAYERS}},
    8: {"key": "stanovisko", "weight": {"A": 0, "B": 0, "C": 0}, "sentences": (2, 3), "questions": 0,
        "daily_max": {},
        "name": {p: "Stanovisko k události" for p in GENRE_PLAYERS},
        "form": {p: "Stanovisko k jedné události, kterou v projevu pojmenuješ: {event}." for p in GENRE_PLAYERS}},
}

STATEMENT_RULES = (
    "Pravidla vystoupení (platí pro každou formu): jedno téma; nejvýš dva jmenované státy; žádné ceny, "
    "množství ani procenta, jen hrubé poměry slovy („třetina“, „většina“); nepoužívej slova pakt, vliv, "
    "kontrakt, jednotka, slot, tah, nabídka číslo, offer, deal (místo nich smlouva, spojenectví, dodávky, "
    "přátelé); o vlastních krocích z tohoto kola nemluv výčtem."
)
UNION_RULE = "V projevu nikdy nepíšeš, který člen jak hlasoval ani kdo byl proti."

# tvrda kontrola projevu (2d)
FORBIDDEN_PATTERNS = [
    (r"\d+[.,]\d+", "číslo s desetinnou čárkou nebo tečkou"),
    (r"%", "znak procenta"),
    (r"\bpakt(u|y|em|ů|ech|ům)?\b", "zakázané slovo pakt"),
    (r"\bvliv(u|em|y)?\b", "zakázané slovo vliv"),
    (r"\bkontrakt\w*", "zakázané slovo kontrakt"),
    (r"\bjednotk\w*", "zakázané slovo jednotka"),
    (r"\bslot\w*", "zakázané slovo slot"),
    (r"\b(tah|tahu|tahy|tahem|tazích|tahů|tahům)\b", "zakázané slovo tah"),
    (r"\bnabídk\w*\s+(číslo|č\.)", "zakázaný obrat nabídka číslo"),
    (r"\boffer\w*", "zakázané slovo offer"),
    (r"\bdeal\w*", "zakázané slovo deal"),
]

# spoustece stanoviska (8): existujici event kinds enginu
TRIGGER_KINDS = ("coup", "default", "invade_progress", "occupied", "war_declared", "war_end",
                 "union_founded", "phase")
UNION_TRIGGER_KINDS = ("poverty", "loan_given", "protect_started")


def count_sentences(text: str) -> int:
    return len([x for x in re.split(r"[.!?…]+(?=\s|$)", text.strip()) if x.strip()])


def statement_violations(text: str, genre: dict) -> list[str]:
    """2d: tvrda kontrola projevu podle zanru. Vraci seznam poruseni (prazdny = v poradku)."""
    text = text or ""
    if genre["id"] == 6:
        return [] if not text.strip() else ["forma Ticho vyžaduje prázdný public_statement"]
    out = []
    for pattern, label in FORBIDDEN_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            out.append("%s („%s“)" % (label, m.group(0)))
    lo, hi = genre["sentences"]
    n = count_sentences(text)
    if not (lo - 1 <= n <= hi + 1):
        out.append("počet vět %d mimo rozsah %d až %d" % (n, lo, hi))
    return out


def _state_names(state, npcdata) -> dict:
    names = dict(PLAYER_NAMES)
    names["C"] = state["players"]["C"].get("name") or "Unie"
    names.update({x["id"]: x.get("name") for x in npcdata.get("npc", [])})
    return names


def _event_text(e: dict, names: dict) -> str:
    n = lambda k: names.get(e.get(k), e.get(k) or "")
    kind = e.get("kind")
    if kind == "coup":
        return "pád vlády ve státě %s" % n("stat")
    if kind == "default":
        return "%s poprvé nesplácí dluh vůči státu %s" % (n("npc"), n("creditor"))
    if kind == "invade_progress":
        return "%s zahájil invazi do státu %s" % (n("player"), n("target"))
    if kind == "occupied":
        return "%s obsadil stát %s" % (n("attacker"), n("target"))
    if kind == "war_declared":
        return "%s vyhlásil válku státu %s" % (n("aggressor"), n("defender"))
    if kind == "war_end":
        a, b = (e.get("between") or ["", ""])[:2]
        return "příměří mezi státy %s a %s" % (names.get(a, a), names.get(b, b))
    if kind == "union_founded":
        return "vznik Unie"
    if kind == "phase":
        return "obrat hospodářské nálady ve světě"
    if kind == "poverty":
        return "bída v členském státě %s" % n("stat")
    if kind == "loan_given":
        return "členský stát %s přijal půjčku od státu %s" % (n("target"), n("player"))
    if kind == "protect_started":
        return "kandidátská země %s přijala ochranu státu %s" % (n("target"), n("player"))
    return kind or ""


def find_trigger(state, snap, pid: str, names: dict) -> str | None:
    """8: udalost minuleho kola, ktera prebiji los. Unie ma navic tri vlastni spoustece."""
    if not snap:
        return None
    C = state["players"]["C"]
    members, candidates = set(C.get("members") or []), set(C.get("candidates") or [])
    defaults = state.get("minsky", {}).get("defaults") or []
    for e in snap.get("events") or []:
        kind = e.get("kind")
        if kind in TRIGGER_KINDS:
            if kind == "default" and sum(1 for d in defaults if d.get("npc") == e.get("npc")
                                         and d.get("creditor") == e.get("creditor")) != 1:
                continue   # jen prvni nesplaceni
            if kind == "invade_progress" and int(e.get("turns") or 0) != 1:
                continue   # jen zahajeni invaze
            if kind == "war_end" and e.get("how") != "primeri":
                continue
            return _event_text(e, names)
        if pid == "C" and C.get("active") and kind in UNION_TRIGGER_KINDS:
            if kind == "poverty" and e.get("stat") in members:
                return _event_text(e, names)
            if kind == "loan_given" and e.get("target") in members and e.get("player") in ("A", "B"):
                return _event_text(e, names)
            if kind == "protect_started" and e.get("target") in candidates and e.get("player") in ("A", "B"):
                return _event_text(e, names)
    return None


def _genre_rng(state, turn: int, pid: str) -> random.Random:
    # deterministicky jako hod NPC (_decision_roll): rng_seed + tah + CRC32(ID)
    return random.Random(int(state["meta"]["rng_seed"]) + turn + zlib.crc32(pid.encode("utf-8")))


def _union_addressees(state, npcdata) -> list[str]:
    C = state["players"]["C"]
    members = set(C.get("members") or [])
    adj = npcdata.get("adjacency") or {}
    out = set(C.get("candidates") or [])
    for m in members:
        for x in adj.get(m, []):
            if engine.is_npc(x) and x not in members and state["npc"].get(x, {}).get("status") != "union":
                out.add(x)
    return sorted(out, key=lambda x: int(x[1:]))


def draw_genre(state, npcdata, pid: str, turn: int) -> dict:
    """2b: vazeny los zanru s omezenimi; vysledek se zapise do state["genre"][pid]."""
    names = _state_names(state, npcdata)
    slot = engine.slot_of(turn)
    day = engine.day_of(turn)
    rec = (state.get("genre") or {}).get(pid) or {}
    today = rec.get("day_counts", {}) if rec.get("day") == day else {}
    last_id = rec.get("id") if rec.get("turn") == turn - 1 else None
    C = state["players"]["C"]
    snap = load_snapshot(turn - 1)
    rng = _genre_rng(state, turn, pid)
    info = {"turn": turn}

    event = find_trigger(state, snap, pid, names)
    if event:
        gid = 8
        info["event"] = event
    else:
        pool = []
        for gid_, g in GENRES.items():
            w = g["weight"][pid]
            if w <= 0 or gid_ == last_id:
                continue
            if g["daily_max"].get(pid) is not None and today.get(str(gid_), 0) >= g["daily_max"][pid]:
                continue
            if gid_ == 6:
                if pid in ("A", "B") and slot == 1:
                    continue
                if pid == "C" and turn == int(C.get("founded_turn") or -9) + 1:
                    continue   # zakladajici tah Unie: volba jmena
            if gid_ == 7:
                sent = ((snap or {}).get("turns") or {}).get(pid, {}).get("message")
                if turn < LEAK_FROM_TURN or not (isinstance(sent, dict) and (sent.get("text") or "").strip()):
                    continue
                if pid == "C" and turn < int(C.get("founded_turn") or 10 ** 6) + LEAK_UNION_DELAY:
                    continue
            pool.append((gid_, w))
        total = sum(w for _, w in pool)
        pick = rng.uniform(0, total)
        gid = pool[-1][0]
        acc = 0.0
        for gid_, w in pool:
            acc += w
            if pick <= acc:
                gid = gid_
                break
    g = GENRES[gid]
    info.update({"id": gid, "key": g["key"], "name": g["name"][pid], "sentences": list(g["sentences"]),
                 "questions_needed": g["questions"], "questions": []})
    form = g["form"][pid]
    if gid == 4 and pid == "C":
        members = sorted(C.get("members") or [], key=lambda x: int(x[1:]))
        chair = random.Random(int(state["meta"]["rng_seed"]) + turn).choice(members) if members else None
        info["chair"] = names.get(chair, chair) if chair else "předsedající"
        form = form.format(chair=info["chair"])
    if gid == 5:
        addressees = _union_addressees(state, npcdata) if pid == "C" else []
        variant = rng.random() < VARIANT_CHANCE or (pid == "C" and not addressees)
        if variant:
            info["variant"] = True
            resolution = int(rec.get("resolution_no", 0)) + (1 if pid == "C" else 0)
            info["name"] = g["variant_name"][pid].format(resolution=resolution)
            form = g["variant_form"][pid].format(resolution=resolution)
            if pid == "C":
                info["resolution_no"] = resolution
        elif pid == "C":
            info["addressees"] = [names.get(x, x) for x in addressees]
            form = form.format(addressees=", ".join(info["addressees"]))
    if gid == 7:
        info["leak_source"] = (snap["turns"][pid]["message"] or {}).get("text", "")
    if gid == 8:
        form = form.format(event=info["event"])
    info["form"] = form

    counts = dict(today)
    counts[str(gid)] = counts.get(str(gid), 0) + 1
    new_rec = {"id": gid, "key": g["key"], "turn": turn, "day": day, "day_counts": counts,
               "resolution_no": info.get("resolution_no", rec.get("resolution_no", 0))}
    state.setdefault("genre", {})[pid] = new_rec
    return info


def genre_block(pid: str, info: dict) -> str:
    """2d: blok Forma dnesniho vystoupeni do promptu hrace."""
    lo, hi = info["sentences"]
    lines = ["## Forma dnešního vystoupení", "",
             "**%s.** %s" % (info["name"], info["form"].replace("{leak}", info.get("leak") or "<větu vybere rozhodčí>"))]
    if info["id"] != 6:
        lines.append("Délka: %d až %d %s." % (lo, hi, "věty" if hi <= 4 else "vět"))
    if info.get("questions"):
        lines.append("Otázky:")
        lines += ["- %s" % q for q in info["questions"]]
    elif info.get("questions_needed"):
        lines.append("Otázky: <otázky vygeneruje rozhodčí před tahem>")
    if info["id"] != 6:
        lines.append(STATEMENT_RULES)
    if pid == "C":
        lines.append(UNION_RULE)
    return "\n".join(lines)


FALLBACK_QUESTION = "Jak hodnotíte současné dění ve světě?"


def questions_prompt(state, npcdata, pid: str, info: dict) -> str:
    turn = info["turn"]
    names = _state_names(state, npcdata)
    snap = load_snapshot(turn - 1) or {}
    others = ("A", "B") if pid == "C" else (OPPONENT[pid],)
    speeches = {names[q]: ((snap.get("turns") or {}).get(q) or {}).get("public_statement", SILENT_STATEMENT)
                for q in others}
    n = info["questions_needed"]
    lines = ["# Úloha: otázky novinářů pro stát %s, kolo %d (den %d)" % (names[pid], turn, engine.day_of(turn)), "",
             "Napiš %d %s pro vystoupení „%s“. Každá otázka je jedna věta. Otázky vycházejí jen ze Zpráv světa "
             "a z projevu soupeře níže; nepoužívej skrytá data (právo, technologie, index prosperity, cizí vliv) "
             "ani čísla." % (n, "otázku" if n == 1 else "otázky", info["name"])]
    if info["id"] == 3:
        lines.append("První otázka míří k soupeři, druhá ke světu.")
    if pid == "C" and info["id"] in (2, 3):
        lines.append("Otázka smí mířit i na rozpory mezi členy Unie.")
    if info["id"] == 7:
        lines += ["Vyber z soukromé zprávy níže jednu větu, kterou svět zveřejní jako uniklou depeši, a vrať ji "
                  "v poli leak doslova. Otázka se ptá na tento únik.", "", "## Soukromá zpráva", "",
                  info.get("leak_source", "")]
    lines += ["", "## Zprávy světa z minulého kola", "```json", dump(list(snap.get("news") or [])), "```",
              "", "## Projev soupeře z minulého kola", "```json", dump(speeches), "```", "",
              "Vrať JSON s polem questions%s. Pole actions, rejected, rulings a news nech prázdná%s."
              % (" a leak" if info["id"] == 7 else "", "" if info["id"] == 7 else ", leak prázdný řetězec")]
    return "\n".join(lines)


def _pick_leak(source: str, proposed: str) -> str:
    norm = lambda t: re.sub(r"\s+", " ", t or "").strip()
    if proposed and norm(proposed) in norm(source):
        return norm(proposed)
    first = re.split(r"(?<=[.!?…])\s+", norm(source))
    return first[0] if first and first[0] else norm(source)


def leak_news(state, npcdata, pid: str, info: dict) -> str:
    names = _state_names(state, npcdata)
    city = union_capital(state, npcdata) if pid == "C" else capitals(npcdata).get(pid)
    text = "Uniklá depeše ze soukromé zprávy státu %s: „%s“" % (names[pid], info["leak"])
    # v1.13 (cast 3): dateline hlavniho mesta odesilatele
    return ("%s, den %d: %s" % (city, engine.day_of(info["turn"]), text)) if city else text


def fill_questions(state, npcdata, pid: str, info: dict, usage_log: list) -> None:
    """2c: mala uloha rozhodciho pred tahem hracu; jen pro zanry 2, 3 a 7."""
    n = info["questions_needed"]
    if not n:
        return
    try:
        raw = call_model(config.REFEREE_MODEL, referee_system(), questions_prompt(state, npcdata, pid, info),
                         max_tokens=REFEREE_MAX_TOKENS, usage_log=usage_log, cache=True,
                         label="rozhodci otazky %s" % pid,
                         schema=referee_schema(), thinking=REFEREE_THINKING)
        data = parse_json(raw)
    except (ValueError, json.JSONDecodeError):
        data = {}
    qs = [q.strip() for q in data.get("questions") or [] if isinstance(q, str) and q.strip()][:n]
    while len(qs) < n:
        qs.append(FALLBACK_QUESTION)
        info["fallback_question"] = True
    info["questions"] = qs
    if info["id"] == 7:
        info["leak"] = _pick_leak(info.get("leak_source", ""), data.get("leak", ""))


# --------------------------------------------------------------------------
# skladani promptu
# --------------------------------------------------------------------------

def player_prompt(state, views, pid: str, genre: dict | None = None) -> tuple[str, str]:
    """Vraci (system, user) pro hrace pid."""
    turn = next_turn(state)
    base = read_text(config.PROMPTS_DIR / PROMPT_FILES[pid])
    base = base.replace("{turn}", str(turn)).replace("{day}", str(engine.day_of(turn)))
    # v1.13: blok Forma dnesniho vystoupeni podle vylosovaneho zanru
    base = base.replace("{forma}", genre_block(pid, genre) if genre else "")
    secret = read_text(config.SECRETS_DIR / SECRET_FILES[pid])
    fmt = read_text(config.TURN_FORMAT_PATH)
    system = "\n\n".join([base.strip(), secret.strip(), fmt.strip()])
    log = public_log(turn)
    msgs = private_messages(state, pid)
    npcdata = json.loads(read_text(config.NPC_PATH))
    # vlastni poznamky z minuleho tahu doslova (A, B i Unie)
    memory = [
        "## tve_poznamky (tvé poznámky z minulého tahu, doslova; soupeř je nevidí)",
        "```text",
        memory_notes(turn, pid),
        "```",
        "",
    ]
    if pid in MEMORY_PLAYERS:
        memory += [
            "## tve_minule_uvahy (tvá vlastní úvaha z minulého tahu)",
            "```json",
            _compact(memory_reasoning(turn, pid)),
            "```",
            "",
            "## od_tveho_minuleho_tahu (fakta z enginu, bez hodnocení)",
            "```json",
            _compact(memory_since_last(state, pid, npcdata)),
            "```",
            "",
            "## tve_smlouvy (trvalé obchody a pakty, náklad nebo výnos za tah)",
            "```json",
            _compact(memory_contracts(state, pid)),
            "```",
            "",
        ]
    user = "\n".join([
        "# Tah %d, den %d" % (turn, engine.day_of(turn)),
        "",
        "## Tvůj pohled na svět",
        "```json",
        dump_view(views[pid]),
        "```",
        "",
        *memory,
        "## Veřejný log posledních %d tahů" % config.PUBLIC_LOG_TURNS,
        "```json",
        dump(log) if log else "[]",
        "```",
        "",
        "## Soukromé zprávy pro tebe z minulého tahu",
        "```json",
        dump(msgs),
        "```",
        "",
        "Odpověz jediným validním JSON objektem podle formátu tahu.",
    ])
    return system, user


def referee_system() -> str:
    # rozhodci dostava jen vytah pravidel (build_referee_rules.py) a secrets
    if not REFEREE_RULES_PATH.exists():
        raise SystemExit("chybi docs/pravidla_rozhodci.md, spust python build_referee_rules.py")
    parts = [read_text(config.PROMPTS_DIR / "rozhodci.md").strip(),
             "# docs/pravidla_rozhodci.md\n\n" + read_text(REFEREE_RULES_PATH).strip()]
    if config.RULINGS_PATH.exists():
        parts.append("# docs/rulings.md (trvalá rozhodnutí, jsi jimi vázán)\n\n"
                     + read_text(config.RULINGS_PATH).strip())
    for pid in ("A", "B", "C"):
        parts.append("# secrets/%s\n\n" % SECRET_FILES[pid] + read_text(config.SECRETS_DIR / SECRET_FILES[pid]).strip())
    return "\n\n".join(parts)


def referee_actions_prompt(state, moves: dict) -> str:
    """Uloha 1 a 2: preklad tahu na akce. Rozhodci vidi stav (bez historie logu) a tahy."""
    turn = next_turn(state)
    ctx = copy.deepcopy(state)
    ctx.pop("log", None)
    return "\n".join([
        "# Úloha: překlad tahů %d (den %d)" % (turn, engine.day_of(turn)),
        "",
        "meta.paused = %s" % str(bool(state["meta"].get("paused"))).lower(),
        "Limity akcí: A %d, B %d, C %d. Tahy 1 až 6 nejednoznačné akce doplňuj, od tahu 7 vyřazuj." % (
            engine.ACTION_LIMIT["A"], engine.ACTION_LIMIT["B"], engine.ACTION_LIMIT["C"]),
        "Mimo limit (v1.11): domestic_action A a B (jedna, typy %s, akce s \"slot\": \"domestic\") "
        "a message (jedna za tah)." % ", ".join(engine.DOMESTIC_TYPES),
        "",
        "## Tahy hráčů",
        "```json",
        dump(moves),
        "```",
        "",
        "## Stav světa před tahem",
        "```json",
        dump(ctx),
        "```",
        "",
        "Vrať jediný JSON objekt s poli actions, rejected, rulings. Pole news a questions nech prázdná a leak "
        "prázdný řetězec, zprávy píšeš ve druhé úloze.",
        "",
        names_block(state),
    ])


def referee_news_prompt(state_after, events: list) -> str:
    turn = int(state_after["meta"]["turn"])
    return "\n".join([
        "# Úloha: Zprávy světa po tahu %d (den %d)" % (turn, engine.day_of(turn)),
        "",
        "Fáze: %s. Tah je %sčtvrtý (zpráva bez důsledku)." % (state_after["phase"], "" if turn % 4 == 0 else "ne"),
        "",
        "## Události od enginu",
        "```json",
        dump([e for e in events if not e.get("private")]),
        "```",
        "",
        "Vrať jediný JSON objekt {\"news\": [\"...\"]} s 1 až 3 zprávami. Každá zpráva začíná datelinem "
        "„Hlavní město, den %d:“ (město státu, o kterém zpráva je). Pole actions, rejected, "
        "rulings a questions nech prázdná, leak prázdný řetězec." % engine.day_of(turn),
        "",
        names_block(state_after),
    ])


# --------------------------------------------------------------------------
# kontrola uniku skrytych dat (bod 7)
# --------------------------------------------------------------------------

def _walk_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path + "." + str(k), k
            yield from _walk_keys(v, path + "." + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_keys(v, "%s[%d]" % (path, i))


def check_player_input(state, views, pid: str, log: list) -> list[str]:
    """Hrac nesmi dostat cizi private_reasoning, cizi law/tech, openness, cizi stock ani index."""
    errors = list(validate_views(state, {pid: views[pid]}))
    C = state["players"]["C"]
    allowed_lt = set(C.get("members") or []) | set(C.get("candidates") or []) if pid == "C" else set()
    for where, key in _walk_keys(views[pid], "pohled"):
        if key in FORBIDDEN_KEYS and not (key == "influence_moje"):
            errors.append("%s: zakazane pole %s" % (where, key))
    for nid, item in views[pid].get("npc", {}).items():
        for k in ("law", "tech"):
            if k in item and nid not in allowed_lt:
                errors.append("pohled.npc.%s.%s" % (nid, k))
        if "stock" in item:
            errors.append("pohled.npc.%s.stock" % nid)
    if pid == "C" and "stock" in views[pid].get("ja", {}):
        errors.append("pohled C obsahuje stock")
    for where, key in _walk_keys(log, "log"):
        if key in ("private_reasoning", "openness", "prosperity_index", "metrics", "text"):
            errors.append("%s: zakazane pole %s" % (where, key))
    return errors


def check_foreign_reasoning(pid: str, turn: int, user: str) -> list[str]:
    """v1.11 (E9): v promptu hrace nesmi byt cizi private_reasoning ani cizi poznamky; vlastni poznamky
    jsou prave ty z minuleho tahu hrace pid."""
    errors = []
    for t in range(max(1, turn - config.PUBLIC_LOG_TURNS - 1), turn):
        snap = load_snapshot(t)
        for q, move in ((snap or {}).get("turns") or {}).items():
            for field, label in (("private_reasoning", "uvahu"), (NOTES_FIELD, "poznamky")):
                text = (move.get(field) or "").strip()
                if q != pid and len(text) >= 20 and text[:200] in user:
                    errors.append("prompt obsahuje %s hrace %s z tahu %d" % (label, q, t))
    own = memory_notes(turn, pid)
    m = re.search(r"## tve_poznamky[^\n]*\n```text\n(.*?)\n```", user, re.S)
    if m is None or m.group(1) != own:
        errors.append("blok tve_poznamky neodpovida poznamkam hrace %s z minuleho tahu" % pid)
    return errors


# --------------------------------------------------------------------------
# volani modelu
# --------------------------------------------------------------------------

_client = None


def client():
    global _client
    if _client is None:
        try:
            import anthropic
        except ImportError:
            raise SystemExit("Chybi balicek anthropic (pip install anthropic) a prihlaseni "
                             "(ANTHROPIC_API_KEY nebo ant auth login).")
        # klic z ARDAN_API_KEY, nahradne ANTHROPIC_API_KEY; nikdy neni v repu
        _client = anthropic.Anthropic(api_key=os.environ.get("ARDAN_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))
    return _client


# ceny v USD za milion tokenu (vstup, vystup); zapis do cache 1.25x vstupu, cteni 0.1x vstupu
PRICES = {"claude-opus-5": (5.0, 25.0), "claude-sonnet-5": (2.0, 10.0), "claude-opus-4-8": (5.0, 25.0)}


def call_cost(u: dict) -> float:
    pin, pout = PRICES.get(u["model"], (5.0, 25.0))
    return (u["input_tokens"] * pin + u["cache_creation_input_tokens"] * pin * 1.25
            + u["cache_read_input_tokens"] * pin * 0.1 + u["output_tokens"] * pout) / 1e6


# --------------------------------------------------------------------------
# JSON schemata odpovedi (strukturovany vystup, output_config.format)
# --------------------------------------------------------------------------

ACTION_TYPES = ("trade_offer", "loan", "pressure", "protect", "invade", "declare_war", "invest_tech", "invest_law",
                "invest_industry", "invest_prod", "explore", "arm", "cancel", "admit", "union_fund", "set_tariff",
                "accept_offer")
ACTION_PARAMS = {
    "target": {"type": "string"},
    "res": {"type": "string", "enum": ["grain", "oil", "metal", "goods", "orit"]},
    "qty": {"type": "number"},
    "price_per_unit": {"type": "number"},
    "amount": {"type": "number"},
    "deal_id": {"type": "string"},
    "offer_id": {"type": "string"},
    "demand": {"type": "string"},
    "rate": {"type": "number"},
    "retreat": {"type": "boolean"},
}
MESSAGE_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["target", "text"],
                  "properties": {"target": {"type": "string", "enum": ["A", "B", "C"]}, "text": {"type": "string"}}}


def player_schema(pid: str) -> dict:
    """Odpoved hrace: projev, uvaha, akce v limitu, domaci akce (A a B) a zprava."""
    action = {"type": "object", "additionalProperties": False, "required": ["type"],
              "properties": {"type": {"type": "string", "enum": list(ACTION_TYPES)}, **ACTION_PARAMS}}
    props = {
        "public_statement": {"type": "string"},
        "private_reasoning": {"type": "string", "minLength": MIN_REASONING_CHARS},
        "actions": {"type": "array", "items": action},
        "message": {"anyOf": [{"type": "null"}, MESSAGE_SCHEMA]},
        NOTES_FIELD: {"type": "string"},
    }
    if pid in MEMORY_PLAYERS:
        props["domestic_action"] = {"anyOf": [{"type": "null"}, {
            "type": "object", "additionalProperties": False, "required": ["type"],
            "properties": {"type": {"type": "string", "enum": list(engine.DOMESTIC_TYPES)},
                           "amount": {"type": "number"},
                           "res": {"type": "string", "enum": ["grain", "oil", "metal"]}}}]}
    return {"type": "object", "additionalProperties": False, "required": list(props), "properties": props}


def referee_schema() -> dict:
    """Jedno schema pro vsechny ulohy rozhodciho (preklad tahu, zpravy, otazky), aby sdilely cache;
    nepouzita pole zustavaji prazdna."""
    action = {"type": "object", "additionalProperties": False, "required": ["player", "type"],
              "properties": {"player": {"type": "string", "enum": ["A", "B", "C"]},
                             "type": {"type": "string", "enum": list(ACTION_TYPES) + ["message"]},
                             "slot": {"type": "string", "enum": ["domestic"]},
                             "text": {"type": "string"}, **ACTION_PARAMS}}
    return {
        "type": "object", "additionalProperties": False,
        "required": ["actions", "rejected", "rulings", "news", "questions", "leak"],
        "$defs": {"action": action},
        "properties": {
            "actions": {"type": "array", "items": {"$ref": "#/$defs/action"}},
            "rejected": {"type": "array", "items": {
                "type": "object", "additionalProperties": False, "required": ["player", "action", "reason"],
                "properties": {"player": {"type": "string", "enum": ["A", "B", "C"]},
                               "action": {"$ref": "#/$defs/action"}, "reason": {"type": "string"}}}},
            "rulings": {"type": "array", "items": {
                "type": "object", "additionalProperties": False,
                "required": ["situation", "ruling", "reason", "proposed"],
                "properties": {"situation": {"type": "string"}, "ruling": {"type": "string"},
                               "reason": {"type": "string"}, "proposed": {"type": "boolean"}}}},
            "news": {"type": "array", "items": {"type": "string"}},
            "questions": {"type": "array", "items": {"type": "string"}},
            "leak": {"type": "string"},
        },
    }


def call_model(model: str, system: str, user: str, max_tokens: int = 16000, usage_log: list | None = None,
               cache: bool = False, label: str = "", schema: dict | None = None,
               thinking: dict | None = None, effort: str | None = None) -> str:
    """Jedno volani Messages API. Vraci text odpovedi; pri odmitnuti prazdny retezec.
    Skutecne usage (input_tokens, output_tokens) se pripise do usage_log."""
    # prompt caching jen tam, kde se stejny system opakuje v kratke dobe (dve volani rozhodciho v tahu)
    sys_block = [{"type": "text", "text": system, **({"cache_control": {"type": "ephemeral"}} if cache else {})}]
    kwargs = dict(model=model, max_tokens=max_tokens, system=sys_block,
                  messages=[{"role": "user", "content": user}],
                  thinking=thinking or {"type": "adaptive"})
    out_cfg = {}
    if schema is not None:
        # strukturovany vystup: odpoved je validni JSON podle schematu (parser a retry zustavaji jako pojistka)
        out_cfg["format"] = {"type": "json_schema", "schema": schema}
    if effort:
        out_cfg["effort"] = effort
    if out_cfg:
        kwargs["output_config"] = out_cfg
    import anthropic

    def send(kw):
        if model in (config.PLAYER_MODEL, config.CHRONICLER_MODEL) and model.startswith("claude-opus-5"):
            # pri odmitnuti bezpecnostnim filtrem dokonci pozadavek zalozni model
            return client().beta.messages.create(betas=["server-side-fallback-2026-06-01"],
                                                 fallbacks=[{"model": "claude-opus-4-8"}], **kw)
        return client().messages.create(**kw)

    try:
        resp = send(kwargs)
    except anthropic.BadRequestError as err:
        if "format" not in kwargs.get("output_config", {}) or "schema" not in str(err).lower():
            raise
        # pojistka: API schema odmitlo, volani probehne bez strukturovaneho vystupu (parser a retry dal plati)
        print("schema odmitnuto (%s): %s; volam bez schematu" % (label, str(err)[:200]))
        kwargs["output_config"].pop("format")
        if not kwargs["output_config"]:
            kwargs.pop("output_config")
        resp = send(kwargs)
    if usage_log is not None:
        u = {"call": label, "model": resp.model, "input_tokens": resp.usage.input_tokens,
             "cache_creation_input_tokens": getattr(resp.usage, "cache_creation_input_tokens", 0) or 0,
             "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
             "output_tokens": resp.usage.output_tokens, "stop_reason": resp.stop_reason}
        u["cost_usd"] = round(call_cost(u), 5)
        usage_log.append(u)
    if resp.stop_reason == "refusal":
        return ""
    return "".join(b.text for b in resp.content if b.type == "text")


def parse_json(text: str):
    """Vytahne jediny JSON objekt z odpovedi (i kdyby byl v bloku ```json)."""
    t = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", t, re.S)
    if m:
        t = m.group(1)
    start, end = t.find("{"), t.rfind("}")
    if start < 0 or end < start:
        raise ValueError("odpoved neobsahuje JSON objekt")
    return json.loads(t[start:end + 1])


def valid_move(obj) -> bool:
    if not (isinstance(obj, dict) and isinstance(obj.get("public_statement"), str)
            and isinstance(obj.get("private_reasoning"), str) and isinstance(obj.get("actions"), list)
            and isinstance(obj.get("domestic_action"), (dict, type(None)))
            and isinstance(obj.get("message"), (dict, type(None)))
            and isinstance(obj.get(NOTES_FIELD), str)):
        return False
    # v1.12: uvaha aspon MIN_REASONING_CHARS znaku a aspon jedna akce, domaci akce nebo zprava
    if len(obj["private_reasoning"].strip()) < MIN_REASONING_CHARS:
        return False
    return bool(obj["actions"]) or obj.get("domestic_action") is not None or obj.get("message") is not None


def player_messages(actions: list, moves: dict) -> list:
    """v1.12: akce message nevytvari rozhodci; jedna na hrace primo z pole message jeho tahu."""
    out = [a for a in actions if a.get("type") != "message"]
    for pid, move in moves.items():
        msg = (move or {}).get("message")
        if not isinstance(msg, dict):
            continue
        target, text = msg.get("target"), (msg.get("text") or "").strip()
        if target in ("A", "B", "C") and target != pid and text:
            out.append({"player": pid, "type": "message", "target": target, "text": text})
    return out


def trim_player_actions(pid: str, move: dict) -> list:
    """Limit akci vynucuje skript: v tahu hrace zustane prvnich ACTION_LIMIT zahranicnich akci,
    domaci akce je jedna uz podle formatu. Vraci vyrazene akce."""
    acts = list(move.get("actions") or [])
    limit = engine.ACTION_LIMIT[pid]
    move["actions"] = acts[:limit]
    return acts[limit:]


def enforce_limits(actions: list) -> tuple[list, list]:
    """Limit akci po rozhodcim: v kazdem slotu (zahranicni, domaci, zprava) prvni akce do limitu,
    zbytek vyrazen. Vraci (platne, vyrazene)."""
    counts, keep, over = {}, [], []
    for a in actions:
        pid = a.get("player")
        slot = engine.action_slot(a)
        key = (pid, slot)
        if pid in engine.ACTION_LIMIT and counts.get(key, 0) >= engine.slot_limit(pid, slot):
            over.append(a)
            continue
        counts[key] = counts.get(key, 0) + 1
        keep.append(a)
    return keep, over


def limit_rejections(state, turn: int, over: list) -> list:
    """Vyrazene akce nad limit: zaznam do rejected a do soukromeho logu hrace."""
    out = []
    for pid, a in over:
        out.append({"player": pid, "action": a, "reason": OVER_LIMIT_REASON})
        state.setdefault("private_log", {"A": [], "B": [], "C": []}).setdefault(pid, []).append(
            {"turn": turn, "npc": a.get("target"), "action": a.get("type"), "outcome": "vyrazeno",
             "reason": OVER_LIMIT_REASON, "counter": None})
    return out


def mark_domestic(actions: list, moves: dict) -> list:
    """v1.11 (C7): domaci akce A a B nese slot domestic; C domaci akci nema. Rozhodci ji oznaci,
    engine ji uzna jen pro povoleny typ na vlastni stat (action_slot)."""
    out = []
    for a in actions:
        a = dict(a)
        if a.get("slot") == "domestic" and (a.get("player") not in MEMORY_PLAYERS
                                            or a.get("type") not in engine.DOMESTIC_TYPES
                                            or not isinstance((moves.get(a["player"]) or {}).get("domestic_action"), dict)):
            a.pop("slot")
        out.append(a)
    return out


def save_fail(turn: int, pid: str, k: int, raw: str, reason: str, usage: list) -> None:
    """Neuspesny pokus o parsovani do debug/turn_NNN_X_fail_K.txt (v1.10)."""
    DEBUG_DIR.mkdir(exist_ok=True)
    last = usage[-1] if usage else {}
    head = "# tah %d, hrac %s, pokus %d: %s; stop_reason %s, output_tokens %s\n\n" % (
        turn, pid, k, reason, last.get("stop_reason"), last.get("output_tokens"))
    (DEBUG_DIR / ("turn_%03d_%s_fail_%d.txt" % (turn, pid, k))).write_text(head + raw, encoding="utf-8")


def play(pid: str, system: str, user: str, retries: int, turn: int = 0, genre: dict | None = None) -> dict:
    """Tah hrace s opakovanim; po vycerpani mlceni podle pravidel 10.6."""
    attempts = []
    usage = []
    base_user = user
    for attempt in range(retries + 1):
        raw = call_model(config.PLAYER_MODEL, system, user, max_tokens=PLAYER_MAX_TOKENS, usage_log=usage,
                         label="hrac %s" % pid, schema=player_schema(pid),
                         thinking=PLAYER_THINKING, effort=PLAYER_EFFORT)
        attempts.append(raw)
        try:
            move = parse_json(raw)
        except (ValueError, json.JSONDecodeError) as err:
            save_fail(turn, pid, attempt + 1, raw, "neplatny JSON: %s" % err, usage)
            continue
        if not valid_move(move):
            save_fail(turn, pid, attempt + 1, raw,
                      "JSON bez public_statement, private_reasoning nebo actions, nebo domestic_action ci message "
                      "neni objekt ani null, chybi poznamky_pro_pristi_tah, nebo (v1.12) private_reasoning kratsi nez %d znaku ci zadna akce, "
                      "domaci akce ani zprava" % MIN_REASONING_CHARS,
                      usage)
            continue
        violations = statement_violations(move["public_statement"], genre) if genre else []
        if violations:
            # v1.13 (2d): tvrda kontrola projevu; duvod jde do debug/ a jako posledni odstavec do dalsiho pokusu
            save_fail(turn, pid, attempt + 1, raw, "projev porusuje formu: " + "; ".join(violations), usage)
            user = base_user + "\n\nMinulá odpověď byla odmítnuta. Porušení v projevu: " + "; ".join(violations) + "."
            continue
        if valid_move(move):
            if genre and genre["id"] == 6:
                move["public_statement"] = GENRE_SILENT[pid]
            move.setdefault("domestic_action", None)
            move.setdefault("message", None)
            move["silent"] = False
            move["attempts"] = attempt + 1
            move["usage"] = usage
            return move
    return {"public_statement": SILENT_STATEMENT, "private_reasoning": "", "actions": [], "domestic_action": None, "message": None, NOTES_FIELD: "",
            "silent": True, "attempts": len(attempts), "raw": attempts, "usage": usage}


# --------------------------------------------------------------------------
# git a rollback
# --------------------------------------------------------------------------

def git(*args) -> None:
    subprocess.run(["git", *args], cwd=config.ROOT, check=True)


def commit_and_push(message: str, paths: list[str]) -> None:
    git("add", *paths)
    git("commit", "-q", "-m", message)
    git("push", "-q")


def rollback(n: int, use_git: bool) -> int:
    src = history_path(n)
    if not src.exists():
        print("snimek %s neexistuje" % src)
        return 1
    snap = json.loads(read_text(src))
    config.STATE_PATH.write_text(dump(snap["state"]) + "\n", encoding="utf-8")
    for p in sorted(config.HISTORY_DIR.glob("turn_*.json")):
        if int(p.stem.split("_")[1]) > n:
            p.unlink()
    for p in sorted(config.CHRONICLE_DIR.glob("day_*.md")):
        if int(p.stem.split("_")[1]) > engine.day_of(n):
            p.unlink()
    write_index()
    import web_data
    web_data.rebuild_summary()
    if use_git:
        commit_and_push("rollback na tah %03d" % n, ["-A", "state.json", "history", "chronicle"])
    print("state.json vracen na tah %d" % n)
    return 0


def write_index(played_turn=None) -> None:
    """history/index.json s metadaty tahu pro web (BUILD.md cast 7), viz web_data.py."""
    import web_data
    web_data.write_index(played_turn)


def append_rulings(turn: int, rulings: list) -> None:
    keep = [r for r in rulings or [] if isinstance(r, dict) and not r.get("proposed")]
    proposed = [r for r in rulings or [] if isinstance(r, dict) and r.get("proposed")]
    if not keep and not proposed:
        return
    lines = []
    if not config.RULINGS_PATH.exists():
        lines.append("# Trvalá rozhodnutí rozhodčího\n")
    for r in keep:
        lines.append("- Tah %d: %s Rozhodnutí: %s Důvod: %s" % (
            turn, r.get("situation", ""), r.get("ruling", ""), r.get("reason", "")))
    for r in proposed:
        lines.append("- Tah %d (návrh, posoudí Adam): %s Rozhodnutí: %s Důvod: %s" % (
            turn, r.get("situation", ""), r.get("ruling", ""), r.get("reason", "")))
    with open(config.RULINGS_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# --------------------------------------------------------------------------
# hlavni beh
# --------------------------------------------------------------------------

def debug_prefix(turn: int, pid: str) -> str:
    return "unie" if pid == "C" else "turn_%03d" % turn


def write_debug_prompt(path: Path, title: str, system: str, user: str) -> None:
    DEBUG_DIR.mkdir(exist_ok=True)
    path.write_text("# %s\n\n## system\n\n%s\n\n## user\n\n%s\n" % (title, system, user), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--once", action="store_true", help="jeden ostry tah (vychozi chovani)")
    ap.add_argument("--dry-model", action="store_true", help="jen sestavit prompty do debug/, bez volani modelu")
    ap.add_argument("--only", help="jen vybrani hraci, napr. C nebo A,B (bez rozhodciho a prepoctu)")
    ap.add_argument("--state", help="vstupni stav misto state.json")
    ap.add_argument("--no-apply", action="store_true", help="nic nezapisovat do stavu, historie ani gitu")
    ap.add_argument("--no-git", action="store_true", help="bez commitu a pushe")
    ap.add_argument("--scheduled", action="store_true",
                    help="samoopravny rozvrh: odehraje 1 az 2 zameskane tahy, jinak skonci bez tahu")
    ap.add_argument("--schedule-check", action="store_true",
                    help="jen spocita rozvrh a vypise plan (bez volani modelu, pro GitHub Actions)")
    ap.add_argument("--force", action="store_true", help="hraj bez ohledu na rozvrh (rucni spusteni)")
    ap.add_argument("--fail-on-silent", action="store_true",
                    help="hrac bez platne odpovedi po vsech pokusech = chyba tahu (planovac GitHub Actions)")
    ap.add_argument("--rollback", type=int, help="vratit state.json na snimek tahu N")
    args = ap.parse_args()

    if args.rollback is not None:
        return rollback(args.rollback, use_git=not args.no_git)

    state_path = Path(args.state) if args.state else config.STATE_PATH
    state, npcdata = load_state(state_path)
    if args.schedule_check or args.scheduled:
        plan = schedule_plan(state, force=args.force)
        print("rozvrh: %s (%s), tahu k odehrani %d, ocekavano %s, stav tah %d" % (
            plan["plan"], plan["label"], plan["turns"], expected_turns(state), int(state["meta"]["turn"])))
        if args.schedule_check:
            gh_output(**plan)
            return 0
        if plan["plan"] != "hrat":
            gh_output(**plan, played="0")
            gh_summary(plan["label"])
            return 0
        cmd = [sys.executable, str(Path(__file__).resolve()), "--once", "--no-git", "--fail-on-silent"]
        if args.state:
            cmd += ["--state", args.state]
        for i in range(plan["turns"]):
            code = subprocess.run(cmd, cwd=str(config.ROOT)).returncode
            if code != 0:
                gh_summary("tah selhal (kod %d)" % code)
                return code
        after, _ = load_state(state_path)
        meta = after["meta"]
        label = "tah %03d (den %d, slot %d)" % (int(meta["turn"]), int(meta["day"]), int(meta["slot"]))
        den = chronicle_needed(after)
        gh_output(plan="hrano", played=str(plan["turns"]), label=label, turn="%03d" % int(meta["turn"]),
                  day=str(meta["day"]), slot=str(meta["slot"]), chronicle_day="" if den is None else str(den))
        gh_summary(label + (" + kronika dne %d" % den if den is not None else ""))
        print("odehrano tahu: %d, posledni %s" % (plan["turns"], label))
        return 0

    if state["meta"].get("paused"):
        print("meta.paused = true, tah se nehraje")
        gh_summary("pauza")
        return 0

    turn = next_turn(state)
    players = active_players(state)
    if args.only:
        wanted = [p.strip() for p in args.only.split(",") if p.strip()]
        missing = [p for p in wanted if p not in players]
        if missing:
            print("hrac %s v tomto stavu netahne" % ", ".join(missing))
            return 1
        players = wanted

    # 2. pohledy
    views = engine.build_views(state, npcdata)
    fill_auto_block(state, views)
    log = public_log(turn)
    # v1.13: los zanru a otazky rozhodciho (pri --dry-model bez volani modelu)
    genres = {pid: draw_genre(state, npcdata, pid, turn) for pid in players if pid in GENRE_PLAYERS}
    q_usage = []
    for pid, info in genres.items():
        if not args.dry_model:
            fill_questions(state, npcdata, pid, info, q_usage)
        print("zanr %s: %d %s%s" % (pid, info["id"], info["name"],
                                     " (otazky: %s)" % " | ".join(info["questions"]) if info["questions"] else ""))
    prompts = {}
    leaks = []
    for pid in players:
        prompts[pid] = player_prompt(state, views, pid, genres.get(pid))
        leaks += ["%s: %s" % (pid, e) for e in check_player_input(state, views, pid, log)]
        leaks += ["%s: %s" % (pid, e) for e in check_foreign_reasoning(pid, turn, prompts[pid][1])]
    if leaks:
        print("UNIK SKRYTYCH DAT, tah se nehraje:")
        for e in leaks:
            print("  " + e)
        return 1
    print("kontrola vstupu hracu %s: bez uniku" % ", ".join(players))

    # --- jen sestaveni promptu -----------------------------------------------------
    if args.dry_model:
        for pid in players:
            path = DEBUG_DIR / ("%s_%s.md" % (debug_prefix(turn, pid), pid))
            write_debug_prompt(path, "Prompt hráče %s, tah %d" % (pid, turn), *prompts[pid])
            print("zapsano %s" % path.relative_to(config.ROOT))
        if not args.only:
            placeholder = {pid: {"public_statement": "<odpověď hráče %s>" % pid,
                                 "private_reasoning": "<odpověď hráče %s>" % pid,
                                 "actions": ["<akce hráče %s>" % pid],
                                 "domestic_action": ("<domácí akce hráče %s nebo null>" % pid) if pid in MEMORY_PLAYERS else None,
                                 "message": "<zpráva hráče %s nebo null>" % pid,
                                 NOTES_FIELD: "<poznámky hráče %s>" % pid}
                           for pid in players}
            path = DEBUG_DIR / ("turn_%03d_rozhodci.md" % turn)
            write_debug_prompt(path, "Prompt rozhodčího, tah %d, úloha 1 (tahy hráčů doplní běh)" % turn,
                               referee_system(), referee_actions_prompt(state, placeholder))
            print("zapsano %s" % path.relative_to(config.ROOT))
            # uloha 2: Zpravy sveta z udalosti prepoctu tahu bez akci (stav se nezapisuje)
            after, events, _ = engine.apply_turn(state, npcdata, [])
            path = DEBUG_DIR / ("turn_%03d_rozhodci_zpravy.md" % turn)
            write_debug_prompt(path, "Prompt rozhodčího, tah %d, úloha 2 (události z přepočtu bez akcí)" % turn,
                               referee_system(), referee_news_prompt(after, events))
            print("zapsano %s" % path.relative_to(config.ROOT))
        return 0

    # 3. hraci paralelne
    retries = 0 if args.only else config.PLAYER_RETRIES   # --only: jedno volani na hrace
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(players)) as ex:
        futures = {pid: ex.submit(play, pid, *prompts[pid], retries, turn, genres.get(pid)) for pid in players}
        moves = {pid: f.result() for pid, f in futures.items()}
    # limit akci pred rozhodcim: prebytecne zahranicni akce hrace se vyradi
    over_limit = []
    for pid, m in moves.items():
        over_limit += [(pid, a) for a in trim_player_actions(pid, m)]
    for pid, info in genres.items():
        # v1.13 (2b): zanr, otazky a udalost do snimku (bez textu soukrome zpravy)
        moves[pid]["genre"] = {k: v for k, v in info.items() if k not in ("leak_source", "form", "turn")}
    silent = [pid for pid, m in moves.items() if m.get("silent")]
    if args.fail_on_silent and silent and not (args.only or args.no_apply):
        # planovac: tah se nezapise a beh selze viditelne (misto mlceni podle pravidel 10.6)
        return fail(turn, "hrac %s bez platne odpovedi po vsech pokusech" % ", ".join(silent), {"moves": moves}, args)

    if args.only or args.no_apply:
        DEBUG_DIR.mkdir(exist_ok=True)
        for pid, move in moves.items():
            path = DEBUG_DIR / ("%s_%s_response.json" % (debug_prefix(turn, pid), pid))
            path.write_text(dump(move) + "\n", encoding="utf-8")
            print("zapsano %s" % path.relative_to(config.ROOT))
        if args.only:
            return 0

    # 4. rozhodci: preklad tahu
    public_moves = {pid: {k: m.get(k) for k in ("public_statement", "private_reasoning", "actions",
                                                "domestic_action", "message")}
                    for pid, m in moves.items()}
    ref_usage = []
    ref_raw = call_model(config.REFEREE_MODEL, referee_system(), referee_actions_prompt(state, public_moves),
                         max_tokens=REFEREE_MAX_TOKENS, usage_log=ref_usage, cache=True, label="rozhodci akce",
                         schema=referee_schema(), thinking=REFEREE_THINKING)
    try:
        ref = parse_json(ref_raw)
    except (ValueError, json.JSONDecodeError) as err:
        return fail(turn, "rozhodci nevratil JSON: %s" % err, {"moves": moves, "referee_raw": ref_raw}, args)
    if ref.get("paused"):
        print("rozhodci: paused")
        return 0
    actions = [a for a in ref.get("actions") or [] if isinstance(a, dict) and a.get("player") in players]
    actions = mark_domestic(actions, moves)
    actions = player_messages(actions, moves)
    # limit akci po rozhodcim: v kazdem slotu jen prvni akce do limitu
    actions, over_ref = enforce_limits(actions)
    over_limit += [(a.get("player"), a) for a in over_ref]

    # 5. prepocet
    delivered = list(state.get("messages_pending", []))
    work = copy.deepcopy(state)
    work["messages_pending"] = []
    limit_rejected = limit_rejections(work, turn, over_limit)
    new_state, events, applied = engine.apply_turn(work, npcdata, actions)

    # 6. rozhodci: Zpravy sveta
    news_raw = call_model(config.REFEREE_MODEL, referee_system(), referee_news_prompt(new_state, events),
                          max_tokens=REFEREE_MAX_TOKENS, usage_log=ref_usage, cache=True,
                          label="rozhodci zpravy", schema=referee_schema(), thinking=REFEREE_THINKING)
    try:
        news = list(parse_json(news_raw).get("news") or [])[:3]
    except (ValueError, json.JSONDecodeError):
        news = []
    for pid, info in genres.items():
        if info["id"] == 7 and info.get("leak"):
            # v1.13 (7): unikla veta ze soukrome zpravy hrace jde do Zprav sveta
            news.insert(0, leak_news(state, npcdata, pid, info))
    new_state["news"] = news
    if new_state["meta"].get("started_at") is None:
        new_state["meta"]["started_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

    # 7. validace a zapis
    new_views = engine.build_views(new_state, npcdata)
    errors = validate(state, new_state, applied, actions=actions, views=new_views)
    snapshot = {"turn": turn, "state": new_state, "turns": moves, "actions": actions,
                "rejected": (ref.get("rejected") or []) + limit_rejected, "rulings": ref.get("rulings") or [],
                "news": news, "events": events, "delivered_messages": delivered, "applied_rules": applied,
                "usage": q_usage + [u for m in moves.values() for u in m.get("usage", [])] + ref_usage}
    if errors:
        return fail(turn, "validate: %s" % "; ".join(errors[:5]), snapshot, args)
    if args.no_apply:
        path = DEBUG_DIR / ("turn_%03d_snapshot.json" % turn)
        path.write_text(dump(snapshot) + "\n", encoding="utf-8")
        print("--no-apply: snimek jen do %s" % path.relative_to(config.ROOT))
        return 0

    config.HISTORY_DIR.mkdir(exist_ok=True)
    config.VIEWS_DIR.mkdir(exist_ok=True)
    history_path(turn).write_text(dump(snapshot) + "\n", encoding="utf-8")
    write_index(turn)
    import web_data
    web_data.update_summary(snapshot)   # history/summary.json pro web
    config.STATE_PATH.write_text(dump(new_state) + "\n", encoding="utf-8")
    for pid, v in new_views.items():
        (config.VIEWS_DIR / ("%s.json" % pid)).write_text(dump_view(v) + "\n", encoding="utf-8")
    append_rulings(turn, ref.get("rulings"))
    if not args.no_git:
        commit_and_push("tah %03d (den %d)" % (turn, engine.day_of(turn)),
                        ["state.json", "history", "views"] + (["docs/rulings.md"] if config.RULINGS_PATH.exists() else []))
    for u in snapshot["usage"]:
        print("usage %-16s %s in %d, cache_write %d, cache_read %d, out %d, %.4f USD" % (
            u["call"], u["model"], u["input_tokens"], u["cache_creation_input_tokens"],
            u["cache_read_input_tokens"], u["output_tokens"], u["cost_usd"]))
    print("cena tahu %.4f USD" % sum(u["cost_usd"] for u in snapshot["usage"]))
    print("tah %d zapsan" % turn)
    return 0


def fail(turn: int, reason: str, payload: dict, args) -> int:
    """Neuspesny tah: history/failed_turn_NNN.json, zadny zapis state.json.

    E-mail Adamovi (BUILD.md cast 3) posila routine pres Gmail konektor; skript duvod tiskne.
    """
    print("TAH %d SELHAL: %s" % (turn, reason))
    if args.no_apply:
        return 1
    config.HISTORY_DIR.mkdir(exist_ok=True)
    path = config.HISTORY_DIR / ("failed_turn_%03d.json" % turn)
    path.write_text(dump({"turn": turn, "reason": reason, **payload}) + "\n", encoding="utf-8")
    return 1


if __name__ == "__main__":
    sys.exit(main())

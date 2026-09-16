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
import re
import shutil
import subprocess
import sys
from pathlib import Path

import config
import engine
from validate import validate, validate_views

DEBUG_DIR = config.ROOT / "debug"
REFEREE_RULES_PATH = config.DOCS_DIR / "pravidla_rozhodci.md"
PROMPT_FILES = {"A": "hrac_A.md", "B": "hrac_B.md", "C": "hrac_unie.md"}
SECRET_FILES = {"A": "cil_A.md", "B": "cil_B.md", "C": "cil_C.md"}
SILENT_STATEMENT = "Vláda nevydala prohlášení."

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


def names_block(state) -> str:
    """6 (v1.10.1): mapa ID na jmena statu pro rozhodciho a Zpravy sveta."""
    npc = json.loads(read_text(config.NPC_PATH))
    names = dict(PLAYER_NAMES)
    names["C"] = state["players"]["C"].get("name") or "Unie"
    names.update({x["id"]: x.get("name") for x in npc.get("npc", [])})
    return "\n".join(["## Jména států (ID → jméno)", "```json",
                      json.dumps(names, ensure_ascii=False), "```",
                      "Ve Zprávách piš jména států, nikdy ID."])


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
# skladani promptu
# --------------------------------------------------------------------------

def player_prompt(state, views, pid: str) -> tuple[str, str]:
    """Vraci (system, user) pro hrace pid."""
    turn = next_turn(state)
    base = read_text(config.PROMPTS_DIR / PROMPT_FILES[pid])
    base = base.replace("{turn}", str(turn)).replace("{day}", str(engine.day_of(turn)))
    secret = read_text(config.SECRETS_DIR / SECRET_FILES[pid])
    fmt = read_text(config.TURN_FORMAT_PATH)
    system = "\n\n".join([base.strip(), secret.strip(), fmt.strip()])
    log = public_log(turn)
    msgs = private_messages(state, pid)
    user = "\n".join([
        "# Tah %d, den %d" % (turn, engine.day_of(turn)),
        "",
        "## Tvůj pohled na svět",
        "```json",
        dump_view(views[pid]),
        "```",
        "",
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
        "Vrať jediný JSON objekt s poli actions, rejected, rulings. Pole news nech prázdné, zprávy píšeš ve druhé úloze.",
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
        "Vrať jediný JSON objekt {\"news\": [\"...\"]} s 1 až 3 zprávami.",
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


def call_model(model: str, system: str, user: str, max_tokens: int = 16000, usage_log: list | None = None,
               cache: bool = False, label: str = "") -> str:
    """Jedno volani Messages API. Vraci text odpovedi; pri odmitnuti prazdny retezec.
    Skutecne usage (input_tokens, output_tokens) se pripise do usage_log."""
    # prompt caching jen tam, kde se stejny system opakuje v kratke dobe (dve volani rozhodciho v tahu)
    sys_block = [{"type": "text", "text": system, **({"cache_control": {"type": "ephemeral"}} if cache else {})}]
    kwargs = dict(model=model, max_tokens=max_tokens, system=sys_block,
                  messages=[{"role": "user", "content": user}],
                  thinking={"type": "adaptive"})
    if model in (config.PLAYER_MODEL, config.CHRONICLER_MODEL) and model.startswith("claude-opus-5"):
        # pri odmitnuti bezpecnostnim filtrem dokonci pozadavek zalozni model
        resp = client().beta.messages.create(betas=["server-side-fallback-2026-06-01"],
                                             fallbacks=[{"model": "claude-opus-4-8"}], **kwargs)
    else:
        resp = client().messages.create(**kwargs)
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
    return (isinstance(obj, dict) and isinstance(obj.get("public_statement"), str)
            and isinstance(obj.get("private_reasoning"), str) and isinstance(obj.get("actions"), list))


def save_fail(turn: int, pid: str, k: int, raw: str, reason: str, usage: list) -> None:
    """Neuspesny pokus o parsovani do debug/turn_NNN_X_fail_K.txt (v1.10)."""
    DEBUG_DIR.mkdir(exist_ok=True)
    last = usage[-1] if usage else {}
    head = "# tah %d, hrac %s, pokus %d: %s; stop_reason %s, output_tokens %s\n\n" % (
        turn, pid, k, reason, last.get("stop_reason"), last.get("output_tokens"))
    (DEBUG_DIR / ("turn_%03d_%s_fail_%d.txt" % (turn, pid, k))).write_text(head + raw, encoding="utf-8")


def play(pid: str, system: str, user: str, retries: int, turn: int = 0) -> dict:
    """Tah hrace s opakovanim; po vycerpani mlceni podle pravidel 10.6."""
    attempts = []
    usage = []
    for attempt in range(retries + 1):
        raw = call_model(config.PLAYER_MODEL, system, user, usage_log=usage, label="hrac %s" % pid)
        attempts.append(raw)
        try:
            move = parse_json(raw)
        except (ValueError, json.JSONDecodeError) as err:
            save_fail(turn, pid, attempt + 1, raw, "neplatny JSON: %s" % err, usage)
            continue
        if not valid_move(move):
            save_fail(turn, pid, attempt + 1, raw, "JSON bez public_statement, private_reasoning nebo actions", usage)
            continue
        if valid_move(move):
            move["silent"] = False
            move["attempts"] = attempt + 1
            move["usage"] = usage
            return move
    return {"public_statement": SILENT_STATEMENT, "private_reasoning": "", "actions": [],
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
    prompts = {}
    leaks = []
    for pid in players:
        prompts[pid] = player_prompt(state, views, pid)
        leaks += ["%s: %s" % (pid, e) for e in check_player_input(state, views, pid, log)]
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
                                 "actions": ["<akce hráče %s>" % pid]} for pid in players}
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
        futures = {pid: ex.submit(play, pid, *prompts[pid], retries, turn) for pid in players}
        moves = {pid: f.result() for pid, f in futures.items()}
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
    public_moves = {pid: {k: m[k] for k in ("public_statement", "private_reasoning", "actions")}
                    for pid, m in moves.items()}
    ref_usage = []
    ref_raw = call_model(config.REFEREE_MODEL, referee_system(), referee_actions_prompt(state, public_moves),
                         usage_log=ref_usage, cache=True, label="rozhodci akce")
    try:
        ref = parse_json(ref_raw)
    except (ValueError, json.JSONDecodeError) as err:
        return fail(turn, "rozhodci nevratil JSON: %s" % err, {"moves": moves, "referee_raw": ref_raw}, args)
    if ref.get("paused"):
        print("rozhodci: paused")
        return 0
    actions = [a for a in ref.get("actions") or [] if isinstance(a, dict) and a.get("player") in players]

    # 5. prepocet
    delivered = list(state.get("messages_pending", []))
    work = copy.deepcopy(state)
    work["messages_pending"] = []
    new_state, events, applied = engine.apply_turn(work, npcdata, actions)

    # 6. rozhodci: Zpravy sveta
    news_raw = call_model(config.REFEREE_MODEL, referee_system(), referee_news_prompt(new_state, events),
                          usage_log=ref_usage, cache=True, label="rozhodci zpravy")
    try:
        news = list(parse_json(news_raw).get("news") or [])[:3]
    except (ValueError, json.JSONDecodeError):
        news = []
    new_state["news"] = news
    if new_state["meta"].get("started_at") is None:
        new_state["meta"]["started_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")

    # 7. validace a zapis
    new_views = engine.build_views(new_state, npcdata)
    errors = validate(state, new_state, applied, actions=actions, views=new_views)
    snapshot = {"turn": turn, "state": new_state, "turns": moves, "actions": actions,
                "rejected": ref.get("rejected") or [], "rulings": ref.get("rulings") or [],
                "news": news, "events": events, "delivered_messages": delivered, "applied_rules": applied,
                "usage": [u for m in moves.values() for u in m.get("usage", [])] + ref_usage}
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

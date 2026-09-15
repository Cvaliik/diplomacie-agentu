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
    s.pop("log", None)
    return s


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

    turns = []
    events = []
    for snap in snapshots:
        turns.append({"turn": snap["turn"], "tahy": snap.get("turns", {}), "akce": snap.get("actions", []),
                      "vyrazene": snap.get("rejected", []), "zpravy": snap.get("news", [])})
        events.append({"turn": snap["turn"], "events": snap.get("events", [])})
    phase = state_after["phase"]
    parts = [
        "# Den %d (%s), fáze %s" % (day, {"denni": "denní kronika", "tydenni": "týdenní kronika",
                                          "finale": "finále"}[kind], phase),
        "",
        "## Tahy dne (projevy, skrytá zdůvodnění, akce, vyřazené akce, Zprávy světa)",
        "```json", dump(turns), "```", "",
        "## Události od enginu",
        "```json", dump(events), "```", "",
        "## Stav před dnem",
        "```json", dump(_state_for_chronicle(state_before)), "```", "",
        "## Stav po dni",
        "```json", dump(_state_for_chronicle(state_after)), "```", "",
        "## Včerejší kronika",
        prev_chronicle or "(žádná)",
    ]
    if week_chronicles:
        parts += ["", "## Kroniky týdne"]
        for d in sorted(week_chronicles):
            parts += ["", "### Den %d" % d, week_chronicles[d]]
    if metrics_by_day:
        parts += ["", "## Metriky po dnech", "```json", dump(metrics_by_day), "```"]
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
    print("zapsano %s" % out.relative_to(config.ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())

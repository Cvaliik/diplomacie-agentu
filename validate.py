"""validate.py

Invarianty po tahu (BUILD.md cast 4). Vraci seznam chyb; prazdny seznam
znamena, ze tah smi byt zapsan do state.json a history/.

Invariant o populaci je oproti doslovnemu zneni v BUILD.md upresnen:
pop menji tri pravidla (4.3 bida, 3.3 invaze a uprchlici, 5 migrace), takze
se nekontroluje nemennost souctu, ale to, ze kazda zmena je vysvetlena
zaznamem pop_delta v applied_rules. Duvod je v docs/OPEN_QUESTIONS.md C2.
"""

from __future__ import annotations

from engine import PHASE_ORDER, ent, world_ids, ACTION_LIMIT

HIDDEN_IN_VIEW = ("law_threshold", "prosperity_index", "poverty_streak", "wealth_peak")
TOLERANCE = 1e-6


def validate(prev_state, new_state, applied_rules, actions=None, views=None) -> list[str]:
    errors: list[str] = []

    # --- applied_rules musi existovat -------------------------------------
    if not applied_rules:
        errors.append("chybi applied_rules")
        return errors

    # --- tah roste o 1 -----------------------------------------------------
    t_prev = int(prev_state["meta"]["turn"])
    t_new = int(new_state["meta"]["turn"])
    if t_new != t_prev + 1:
        errors.append(f"turn neroste o 1: {t_prev} -> {t_new}")

    # --- zaporne hodnoty a meze -------------------------------------------
    for i in world_ids(new_state):
        e = ent(new_state, i)
        for field in ("wealth", "power", "pop"):
            v = float(e.get(field) or 0.0)
            if v < 0:
                errors.append(f"{i}.{field} je zaporne: {v}")
        for field in ("law", "tech"):
            v = e.get(field)
            if v is None:
                continue
            if not (0.0 - TOLERANCE <= float(v) <= 10.0 + TOLERANCE):
                errors.append(f"{i}.{field} mimo 0 az 10: {v}")
    C = new_state["players"]["C"]
    if C.get("active"):
        for field in ("wealth", "power"):
            if float(C.get(field) or 0.0) < 0:
                errors.append(f"C.{field} je zaporne: {C.get(field)}")

    # --- faze se posunula nejvyse o jeden krok a ma zaznam -----------------
    p_prev = prev_state["phase"]
    p_new = new_state["phase"]
    try:
        i_prev, i_new = PHASE_ORDER.index(p_prev), PHASE_ORDER.index(p_new)
    except ValueError:
        errors.append(f"neznama faze: {p_prev} -> {p_new}")
    else:
        if i_new < i_prev:
            errors.append(f"faze jde zpet: {p_prev} -> {p_new}")
        elif i_new - i_prev > 1:
            errors.append(f"faze preskocila o {i_new - i_prev} kroku: {p_prev} -> {p_new}")
        elif i_new - i_prev == 1:
            log = new_state["minsky"].get("phase_log", [])
            rec = [r for r in log if r.get("turn") == t_new and r.get("to") == p_new]
            if not rec:
                errors.append(f"zmena faze na {p_new} bez zaznamu v minsky.phase_log")
            elif not rec[-1].get("threshold"):
                errors.append(f"zaznam faze {p_new} nema uvedeny prah")

    # --- limit akci --------------------------------------------------------
    if actions:
        counts: dict[str, int] = {}
        for a in actions:
            pid = a.get("player")
            if pid in ACTION_LIMIT:
                counts[pid] = counts.get(pid, 0) + 1
        for pid, c in counts.items():
            if c > ACTION_LIMIT[pid]:
                errors.append(f"hrac {pid} ma {c} akci, limit je {ACTION_LIMIT[pid]}")

    # --- populace: kazda zmena musi byt vysvetlena -------------------------
    pop_prev = sum(float(ent(prev_state, i)["pop"]) for i in world_ids(prev_state))
    pop_new = sum(float(ent(new_state, i)["pop"]) for i in world_ids(new_state))
    explained = 0.0
    for r in applied_rules:
        out = r.get("outputs")
        if isinstance(out, dict) and "pop_delta" in out:
            explained += float(out["pop_delta"])
    actual = pop_new - pop_prev
    if abs(actual - explained) > 1e-3:
        errors.append(
            f"zmena souctu pop ({actual:+.3f}) neodpovida vysvetlenym zmenam "
            f"({explained:+.3f}); rozdil {actual - explained:+.3f}")

    # --- pohledy nesmi obsahovat skryta pole -------------------------------
    if views:
        errors += validate_views(new_state, views)

    return errors


def validate_views(state, views) -> list[str]:
    """Pravidla cast 2 a 9: co hrac nesmi videt."""
    errors: list[str] = []
    C = state["players"]["C"]
    members = set(C.get("members") or []) | set(C.get("candidates") or [])
    for pid, view in views.items():
        for hid in HIDDEN_IN_VIEW:
            if hid in view or hid in view.get("ja", {}):
                errors.append(f"pohled {pid} obsahuje skryte pole {hid}")
        for nid, item in view.get("npc", {}).items():
            for hid in ("law", "tech"):
                if hid in item:
                    if pid == "C" and nid in members:
                        continue  # C vidi law/tech clenu a kandidatu
                    errors.append(f"pohled {pid} vidi {nid}.{hid}")
            if "influence" in item:
                errors.append(f"pohled {pid} vidi cely influence u {nid}")
            if "debt" in item:
                errors.append(f"pohled {pid} vidi cele debt u {nid}")
            if "paper_wealth" in item:
                errors.append(f"pohled {pid} vidi paper_wealth u {nid} zvlast")
            if "poverty_streak" in item or "wealth_peak" in item:
                errors.append(f"pohled {pid} vidi interni pole u {nid}")
        if "metrics" in view:
            errors.append(f"pohled {pid} obsahuje metriky")
    return errors

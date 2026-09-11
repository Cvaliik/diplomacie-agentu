# BUILD.md: zadání pro Claude Code

Postav infrastrukturu hry "Diplomacie agentů" přesně podle tohoto repa. Herní design je hotový a zamčený: `docs/pravidla.md` (včetně části 10), `prompts/`, `secrets/`, `npc.json`, `state.json`, `docs/faze.md`. Nic z designu neměň bez explicitního souhlasu Adama; když narazíš na nejasnost, zapiš ji do `docs/OPEN_QUESTIONS.md` a pokračuj s nejkonzervativnější interpretací.

Jazyk kódu: Python 3.11+, bez externích služeb. Jazyk textů: čeština. Nepoužívej pomlčku "—" nikde v textech.

## 1. Struktura repa

```
engine.py            deterministická pravidla (docs/pravidla.md 1:1)
validate.py          invarianty po tahu
run_turn.py          orchestrace jednoho tahu
run_chronicle.py     kronika dne / týdne / finále
test_run.py          suchý běh 12 tahů bez modelů
config.py            modely, cesty, časy, přepínače
views/               pohledy hráčů generované enginem (A.json, B.json, C.json)
history/turn_NNN.json   snímek po každém tahu (úplný)
history/failed_turn_NNN.json   neúspěšný tah (nevalidovaný)
chronicle/day_NN.md  kronika
web/index.html       statická stránka (GitHub Pages ze složky web/)
```

## 2. engine.py

- Vstup: `state.json`, `npc.json`, seznam validovaných akcí od rozhodčího.
- Aplikuje pravidla v pořadí podle `docs/pravidla.md` část 4, pak 3.3 (invaze), 4.4 (vliv), 5 (Minsky), 7 (Unie), 8 (metriky). Každý krok zapíše do `snapshot.applied_rules` záznam `{rule, inputs, outputs}`.
- Náhoda výhradně z `random.Random(rng_seed + turn)`.
- Vrací: nový stav, seznam událostí pro rozhodčího (`events`), pohledy hráčů.
- Pohledy (`views/X.json`): jen to, co hráč X smí vidět podle části 2 tabulky. `wealth` NPC se ukazuje jako `wealth + paper_wealth` v jednom čísle. `law`, `tech`, cizí `influence`, cizí `debt`, `prosperity_index`, `law_threshold` se nikdy nedostanou do pohledu (C vidí `law`/`tech` jen u členů a kandidátů).
- Metriky každý tah do `state.metrics` a do snímku.

## 3. run_turn.py (jeden tah)

1. Načti `state.json`. Je-li `meta.paused`, skonči bez změny.
2. Engine vygeneruje pohledy.
3. Paralelně zavolej hráče (A, B, a C pokud `players.C.active`). Každý hráč dostane: svůj prompt (`prompts/hrac_A.md` / `hrac_B.md` / `hrac_unie.md`), svůj tajný cíl (`secrets/cil_A.md` / `cil_B.md` / `cil_C.md`), svůj pohled, posledních 9 tahů veřejného logu (projevy, Zprávy, veřejné akce; NE cizí `private_reasoning`), soukromé zprávy adresované jemu z minulého tahu, `docs/format_tahu.md`. Odpověď musí být validní JSON; při selhání 2 opakování, pak `silent` (pravidla 10.6).
4. Zavolej rozhodčího (`prompts/rozhodci.md`) s tahy a `docs/pravidla.md`: vrátí `actions`, `rejected`, `rulings`.
5. Engine přepočítá svět.
6. Zavolej rozhodčího podruhé jen se seznamem `events`: vrátí `news`.
7. `validate.py`. Při úspěchu: zapiš `state.json`, `history/turn_NNN.json` (stav, tahy včetně `private_reasoning`, rejected, rulings, news, events, applied_rules), commit a push. Při selhání: `history/failed_turn_NNN.json`, žádný commit `state.json`, e‑mail Adamovi (Gmail konektor) s důvodem.
8. Trvalá `rulings` ukládej do `docs/rulings.md`, rozhodčí je dostává v každém dalším tahu.

Modely: v `config.py` jedno místo: `PLAYER_MODEL`, `REFEREE_MODEL`, `CHRONICLER_MODEL`. Výchozí: hráči a kronikář nejsilnější dostupný model (Opus), rozhodčí Sonnet. Adam může přepnout jedním commitem.

## 4. validate.py

Musí selhat, pokud: záporné `wealth`/`power`/`pop`; `law`/`tech` mimo 0 až 10; fáze se posunula o víc než jeden krok, nebo bez záznamu prahu v `minsky.phase_log`; hráč má víc akcí než limit; součet `pop` světa se změnil jinak než migrací; `turn` neroste o 1; chybí `applied_rules`; pohledy obsahují skrytá pole.

## 5. run_chronicle.py

- Denní: po 20:00 tahu. Kontrola tří snímků dne (pravidla 10.7). Vstup podle `prompts/kronikar.md`. Výstup `chronicle/day_NN.md`.
- Týdenní: herní dny 7, 14, 21, 28 místo denní.
- Den 30: finále; kronikář dostane `secrets/cil_*.md` a `metrics` po dnech.

## 6. Routiny (Claude Code remote routines, časová zóna Europe/Prague)

- `turn-morning` 07:00, `turn-noon` 13:00, `turn-evening` 20:00: `python run_turn.py`
- `chronicle` 21:00: `python run_chronicle.py`
Každá routine: pull repa, spuštění skriptu, push. Žádná jiná logika v routině; vše je ve skriptech, aby se dalo spustit i ručně.

## 7. web/index.html

Jedna statická stránka, žádný build, žádný backend. Načítá `history/*.json` (seznam z `history/index.json`, který generuje `run_turn.py`) a `chronicle/*.md`. Mobil na prvním místě.

- Hlavička: den, tah, fáze Minskyho (anglicky / česky), název Unie po vzniku.
- Mapa: SVG z `npc.json` souřadnic. Stát = kruh, plocha podle `wealth + paper_wealth`, barva podle statusu (nezávislý šedá, sféra A světle modrá, sféra B světle červená, okupace tmavá barva okupanta, Unie zelená, kandidát zelený obrys), padlé říše se zlatým obrysem. Ikona ložiska oritu, šipky migrace, probíhající invaze jako čárkovaná spojnice s počítadlem tahů, aktivní obchody jako tenké linky.
- Slider po tazích + tlačítko přehrát (2 s na tah). Vše pod mapou se přepíná se sliderem.
- Panel tahů: pro každého hráče projev, pod ním rozbalitelné "Co si doopravdy myslel" (`private_reasoning`), seznam akcí, vyřazené akce s důvodem.
- Zprávy světa daného tahu.
- Kronika dne, ke kterému tah patří (Markdown render).
- Grafy: cena oritu, index prosperity, tři národní ukazatele (podíl obchodu A, podíl zdrojů B, nejchudší člen C). Kurzor synchronizovaný se sliderem.
- Hráči web nevidí, takže index je veřejný.

## 8. test_run.py (před prvním ostrým tahem)

Suchý běh 12 tahů se skriptovanými tahy bez volání modelů: A půjčuje N6 od tahu 8, B chrání N7, oba obchodují obilí, N6 exploruje. Musí projít: displacement v tahu 7, boom, euphoria, overtrading, distress, panic, crash, vznik Unie s aspoň 3 členy, index spočítán každý tah, validate bez chyb. Pokud Minsky neprojde všemi fázemi do tahu 12 (prahy z pravidel jsou odhad), zapiš do `docs/OPEN_QUESTIONS.md` konkrétní čísla a navrhni úpravu prahů, ale pravidla neměň.

Pak jeden ostrý tah ručně (`python run_turn.py --once`), Adam zkontroluje výstup, teprve pak zapnout routiny.

## 9. Provoz

- **Pauza:** `meta.paused = true` v `state.json`, commit. Routiny nic nedělají.
- **Rollback:** `python run_turn.py --rollback N` zkopíruje `history/turn_N.json` do `state.json`, smaže pozdější snímky a kroniky, commit.
- **Ladění promptu:** prompty se čtou z repa při každém tahu; úprava = commit, další tah jede nově. Kronikář o tom nepíše.
- **Kde hledat chybu:** `history/failed_turn_NNN.json` → `validate` důvod; `applied_rules` ve snímku → které pravidlo a s jakými čísly.
- **Limity:** pokud Opus dochází, přepnout `PLAYER_MODEL` na Sonnet; kronikář zůstává Opus.

## 10. docs/format_tahu.md

Vytvoř podle části 3.1 a 3.2 pravidel: přesné JSON schéma tahu s příklady každé akce, včetně `message` a `admit`. Hráči ho dostávají v každém tahu.

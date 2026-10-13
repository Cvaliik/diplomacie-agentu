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
tools/               kalibrační a ověřovací skripty (v2.0)
```

**Pravidlo (13. 10. 2026):** kalibrační a jednorázové ověřovací skripty (kalibrace scénářů, kontrola kol proti snímkům, patche dokumentace) se ukládají do `tools/` v repu, nikdy jen do dočasné složky (Temp, scratchpad). Kalibrační skripty v2.0 z 24. 9. 2026 ležely v Temp a ztratily se.

## 2. engine.py

- Vstup: `state.json`, `npc.json`, seznam validovaných akcí od rozhodčího.
- Aplikuje pravidla v pořadí podle `docs/pravidla.md` část 4, pak 3.3 (invaze), 4.4 (vliv), 5 (Minsky), 7 (Unie), 8 (metriky). Každý krok zapíše do `snapshot.applied_rules` záznam `{rule, inputs, outputs}`.
- Náhoda výhradně z `random.Random(rng_seed + turn)`.
- Vrací: nový stav, seznam událostí pro rozhodčího (`events`), pohledy hráčů.
- Pohledy (`views/X.json`): jen to, co hráč X smí vidět podle části 2 tabulky. `wealth` NPC se ukazuje jako `wealth + paper_wealth` v jednom čísle. Cizí `law` a `tech`, cizí `influence`, cizí `debt`, `prosperity_index`, `law_threshold` se nikdy nedostanou do pohledu (C vidí `law`/`tech` jen u členů a kandidátů). **Princip viditelnosti (v1.11): hodnoty vidí, dopady ne; skrytý je index a jeho vzorec.** Hráči A a B proto vidí své vlastní `law`, `tech` a `industry` a jejich změny, ne co způsobují.
- Metriky každý tah do `state.metrics` a do snímku.

## 3. run_turn.py (jeden tah)

1. Načti `state.json`. Je-li `meta.paused`, skonči bez změny.
2. Engine vygeneruje pohledy.
3. Paralelně zavolej hráče (A, B, a C pokud `players.C.active`). Každý hráč dostane: svůj prompt (`prompts/hrac_A.md` / `hrac_B.md` / `hrac_unie.md`), svůj tajný cíl (`secrets/cil_A.md` / `cil_B.md` / `cil_C.md`), svůj pohled, posledních 9 tahů veřejného logu (projevy, Zprávy, veřejné akce; NE cizí `duverny_zapis`), soukromé zprávy adresované jemu z minulého tahu, `docs/format_tahu.md`. Hráči A a B navíc (v1.11) bloky paměti `tvuj_minuly_zapis` (vlastní `duverny_zapis` z minulého kola; v1.11 až v1.14b `tve_minule_uvahy` z `private_reasoning`), `od_tveho_minuleho_tahu` (fakta z enginu) a `tve_smlouvy`; kontrola vstupu ověří, že v promptu není cizí důvěrný zápis ani cizí poznámky. Tah A a B má povinné pole `domestic_action` (bez domácí akce `{"type": "zadna"}`); domácí akci i zprávu `message` skládá `run_turn.py` přímo z tahu hráče (`player_domestic`, `player_messages`), rozhodčí je nepřekládá. Odpověď musí být validní JSON; při selhání 2 opakování, pak `silent` (pravidla 10.6).
4. Zavolej rozhodčího (`prompts/rozhodci.md`) s tahy a výtahem `docs/pravidla_rozhodci.md`: vrátí `actions`, `rejected`, `rulings`. Limit akcí vynucuje skript před rozhodčím i po něm (`trim_player_actions`, `enforce_limits`) a akci, kterou rozhodčí vynechal bez důvodu, převezme z tahu hráče (`restore_dropped`).
5. Engine přepočítá svět.
6. Zavolej rozhodčího podruhé jen se seznamem `events`: vrátí `news`.
7. `validate.py`. Při úspěchu: zapiš `state.json`, `history/turn_NNN.json` (stav, tahy včetně `duverny_zapis`, rejected, rulings, news, events, applied_rules), commit a push. Při selhání: `history/failed_turn_NNN.json`, žádný commit `state.json`, e‑mail Adamovi (Gmail konektor) s důvodem.
8. Trvalá `rulings` ukládej do `docs/rulings.md`, rozhodčí je dostává v každém dalším tahu.

Modely: v `config.py` jedno místo: `PLAYER_MODEL`, `REFEREE_MODEL`, `CHRONICLER_MODEL`. Výchozí: hráči a kronikář nejsilnější dostupný model (Opus), rozhodčí Sonnet. Adam může přepnout jedním commitem. **Od v2.0.3 (13. 10. 2026):** hráči a kronikář `claude-opus-5`, rozhodčí `claude-sonnet-5`. Opus 5.5 odmítá (`reasoning_extraction`) tah hráče náhodně i po v2.0.2; v kole 7 dvakrát ze dvou. Hráči a kronikář zpět na Opus 5, rozhodnutí Adama 13. 10. 2026. V letech v2.0 až v2.0.2 (24. 9. až 13. 10. 2026) byli hráči a kronikář na `claude-opus-5-5`. Opus 5.5 přijímá `thinking: adaptive` s `output_config.effort = "low"` a strukturovaný výstup (`output_config.format`) jako Opus 5. Herní prompt hráčů prošel bez zálohy u A i B (24. 9. 2026, po přejmenování na `duverny_zapis`), kronikář nad dnem 4 (13. 10. 2026, po přejmenování polí ve vstupu kronikáře). Záložní model při odmítnutí (server-side fallback) zůstává `claude-opus-4-8`, ale nikdy potichu: každé použití jde do usage (`fallback_from`), do tahu hráče (`zaloha`) a na web jako poznámka. Ceník v `run_turn.PRICES` podle platform.claude.com: Opus 5.5 vstup 4, výstup 20 USD za milion tokenů, čtení z cache 0.05 × vstupu (ostatní modely 0.1 ×).

**v2.0 důvěrný zápis a záložní model (24. 9. 2026):** pole `private_reasoning` se jmenuje `duverny_zapis` („důvěrný zápis z jednání vlády“, čte ho jen publikum); Opus 5.5 původní pole a popis odmítal jako `reasoning_extraction`. Snímky z v1.x nesou starý název, `run_turn.zapis_of()` a web čtou oba; `run_chronicle.py` (`_zapisy`) ho před předáním kronikáři přejmenuje, jinak kronikář na Opus 5.5 odmítal vstup jako `reasoning_extraction`. Když odpoví záložní model (server-side fallback), `call_model` to vypíše, usage nese `fallback_from` (a u odmítnutí `refusal_category`), tah hráče pole `zaloha` s poznámkou a web ji ukáže nad zápisem.

**v2.0.1 tokeny (13. 10. 2026):** všechna volání rozhodčího (otázky, akce, zprávy) mají stejné `thinking: adaptive` a `effort: low`, takže další volání čtou cache systému; systém hráče je `[format_tahu.md] + [persona] + [tajný cíl]`, první blok má `cache_control` a je bajtově shodný pro A, B i Unii (`player_cache_prefix`), první hráč hraje sám a ostatní po něm paralelně, aby četli z cache; veřejný log dává plně jen poslední 3 tahy, tahy 4 až 9 zpět kompaktně (`FULL_LOG_TURNS`, `news_headline`); rozhodčí dostává kompaktní stav (`referee_state`) místo celého `state.json`; kronikář dostává za každé kolo projevy, zápisy, poznámky, akce s výsledky, doručené zprávy, Zprávy světa a kompaktní stav, úplný stav jen po posledním kole roku. Odhad tokenů: `python tools/odhad_tokenu.py debug/*.md`, kontrola kol: `python tools/overit_kola.py`.

**v2.0 banky a Unie po krizi (24. 9. 2026):** engine má bankovní soustavy `banks_K`, `banks_AUR` a `bank_U` (4.6, 7.2): úvěr `step_bank_lending` po akcích hráčů, vyúčtování `step_banks` po Unii, vymáhání a moratorium ve `step_repayments`, rada Unie `_council_vote` (schválené akce v `players.C.council_pending`, provedení na začátku `apply_actions` dalšího kola) a společná obrana v `_register_invasion`. Domácí akce A rozšiřuje `engine.domestic_types("A")` o `zprisnit_uvery`, `uvolnit_uvery` a `sanace_bank`; schéma hráče i výtah pro rozhodčího z něj vycházejí. Bankovní úvěr jde rozhodčímu jako jedna souhrnná událost `bank_loan` na soustavu a kolo, ne po dlužnících.

Klíč se čte z `ARDAN_API_KEY`, náhradně `ANTHROPIC_API_KEY`; nikdy není v repu.

**v1.13 „hlas světa“ (17. 9. 2026):** věta důvodu NPC odpovídá výsledku (`engine.decision_reason`); projevy hráčů mají losované žánry (`GENRES`, `draw_genre`, `docs/zanry.md`) s otázkami rozhodčího před koly hráčů (`fill_questions`) a tvrdou kontrolou projevu (`statement_violations`, porušení jako poslední odstavec dalšího pokusu); žánr jde do `state["genre"]` a do `turns[hráč]["genre"]` ve snímku, web ho ukazuje nad projevem. Zprávy světa začínají datelinem hlavního města (`capital` v `npc.json`, `capitals()` a `names_block()` v `run_turn.py`). Důvod: projevy byly výčtem kroků v jazyce pravidel a důvody NPC odporovaly výsledku.

**v1.12 (tah 4, 17. 9. 2026):** hráč A vrátil platný JSON s projevem, ale s prázdnou úvahou a bez akcí, a zpráva B dorazila prázdná, protože ji rozhodčí přeložil na akci bez `text`. Proto `valid_move()` odmítne odpověď s `private_reasoning` kratším než `MIN_REASONING_CHARS` (80) nebo bez akce, domácí akce i zprávy (schéma hráče nese `minLength`), a akci `message` skládá `player_messages()` přímo z pole `message` tahu hráče; rozhodčí zprávy nepřekládá.

Rozhodčí dostává jen výtah pravidel `docs/pravidla_rozhodci.md` (části 1, 3, 6, 7.2, 9 a 10) a `secrets/`. Výtah generuje
`python build_referee_rules.py`; pouštět při každé změně `docs/pravidla.md`.

## 4. validate.py

Musí selhat, pokud: záporné `wealth`/`power`/`pop`; `law`/`tech` mimo 0 až 10; fáze se posunula o víc než jeden krok, nebo bez záznamu prahu v `minsky.phase_log`; hráč má víc akcí než limit; změna součtu `pop` světa není pokrytá záznamem v `applied_rules` od pravidla, které `pop` měnit smí (4.3 bída, 3.3 invaze a uprchlíci, 5 migrace); `turn` neroste o 1; chybí `applied_rules`; pohledy obsahují skrytá pole.

## 5. run_chronicle.py

- Denní: po 20:00 tahu. Kontrola tří snímků dne (pravidla 10.7). Vstup podle `prompts/kronikar.md`. Výstup `chronicle/day_NN.md`.
- Týdenní: herní dny 7, 14, 21, 28 místo denní.
- Den 30: finále; kronikář dostane `secrets/cil_*.md` a `metrics` po dnech.

## 6. Plánovač: GitHub Actions (změna stacku, dříve Claude Code routines)

Ostrý běh plánují dvě workflow, ne Claude Code routines: `.github/workflows/rozvrh.yml` (kontrola rozvrhu každých 30 minut)
a `.github/workflows/tah.yml` (jen skutečné tahy a kroniky; spouští ho rozvrh přes `gh workflow run` s `GITHUB_TOKEN` a
`permissions: actions: write`, nebo člověk ručně). `tah.yml` po checkoutu rozvrh přepočítá, aby se tah neodehrál dvakrát.

- **Časy:** cron `*/30 * * * *`. Sloty 07:00, 13:00 a 20:00 pražského času jsou jen výpočet, ne čas spuštění: `run_turn.py --schedule-check` spočítá očekávaný počet tahů jako 3 x (dnešek minus `meta.day1_date`) plus dnešní sloty a rozhodne, zda se hraje. Zaostává-li stav o dva tahy, `--scheduled` odehraje v jednom běhu dva. Prázdný běh končí před `pip install`.
- **Ruční spuštění:** `workflow_dispatch` se vstupem `mode`: `turn` (ostrý tah) nebo `dry-model` (jen prompty do artefaktu, bez API).
- **Kroky:** checkout, Python 3.11, rozvrh (`--schedule-check`, bez závislostí), `pip install anthropic`, `python run_turn.py --scheduled` s `ARDAN_API_KEY` ze `secrets.ARDAN_API_KEY`; commit `state.json`, `history/` (a `docs/rulings.md`, existuje-li) se zprávou "tah NNN (den D)", `git pull --rebase` a push na master. Po slotu 3 `python run_chronicle.py` a samostatný commit `chronicle/`, aby selhání kroniky nepřišlo o odehraný tah.
- **Oprávnění a souběh:** `permissions: contents: write`, `concurrency` na jeden běh najednou (bez rušení běžícího).
- **Klíč:** jen v proměnné prostředí kroku; žádný krok netiskne `env` ani `secrets`.
- **Pauza:** je-li `meta.paused = true`, skript skončí bez tahu s kódem 0, běh je zelený a nic se necommituje.
- **Selhání:** chyba API, nevalidní stav nebo hráč bez platné odpovědi po všech pokusech (`--fail-on-silent`) ukončí skript nenulovým kódem; tah se necommituje a běh je červený. Mimo plánovač platí dál pravidla 10.6 (hráč mlčí).

Všechna logika zůstává ve skriptech, aby se dalo hrát i ručně.

## 7. web/index.html

Jedna statická stránka, žádný build, žádný backend. Načítá `history/*.json` (seznam z `history/index.json`, který generuje `run_turn.py`) a `chronicle/*.md`. Mobil na prvním místě.

- Hlavička: den, tah, fáze Minskyho (anglicky / česky), název Unie po vzniku.
- Mapa: SVG z `npc.json` souřadnic. Stát = kruh, plocha podle `wealth + paper_wealth`, barva podle statusu (nezávislý šedá, sféra A světle modrá, sféra B světle červená, okupace tmavá barva okupanta, Unie zelená, kandidát zelený obrys), padlé říše se zlatým obrysem. Ikona ložiska oritu, šipky migrace, probíhající invaze jako čárkovaná spojnice s počítadlem tahů, aktivní obchody jako tenké linky.
- Slider po tazích + tlačítko přehrát (2 s na tah). Vše pod mapou se přepíná se sliderem.
- Panel tahů: pro každého hráče projev, pod ním rozbalitelné "Důvěrný zápis vlády" (`duverny_zapis`, ve starších snímcích `private_reasoning`), seznam akcí, vyřazené akce s důvodem.
- Zprávy světa daného tahu.
- Kronika dne, ke kterému tah patří (Markdown render).
- Grafy: cena oritu, index prosperity, tři národní ukazatele (podíl obchodu A, podíl zdrojů B, nejchudší člen C). Kurzor synchronizovaný se sliderem.
- Hráči web nevidí, takže index je veřejný.
- Panel státu (v1.11) ukazuje u všech států včetně A a B `goods` (zásoba, výroba, potřeba), `industry`, `law` a `tech`; data jsou v `history/summary.json`.

## 8. test_run.py (před prvním ostrým tahem)

Suchý běh 45 tahů se skriptovanými tahy bez volání modelů: A půjčuje N6 od tahu 8, B chrání N7, oba obchodují obilí, N6 exploruje. Musí projít (kritéria beze změny, jen delší okno): displacement v tahu 7, boom, euphoria, overtrading, distress, panic, crash, vznik Unie s aspoň 3 členy, index spočítán každý tah, validate bez chyb. Pokud Minsky neprojde všemi fázemi do tahu 45 (prahy z pravidel jsou odhad), zapiš do `docs/OPEN_QUESTIONS.md` konkrétní čísla a navrhni úpravu prahů, ale pravidla neměň.

Pak jeden ostrý tah ručně (`python run_turn.py --once`), Adam zkontroluje výstup, teprve pak zapnout routiny.

## 9. Provoz

- **Pauza:** `meta.paused = true` v `state.json`, commit. Routiny nic nedělají.
- **Rollback:** `python run_turn.py --rollback N` zkopíruje `history/turn_N.json` do `state.json`, smaže pozdější snímky a kroniky, commit.
- **Ladění promptu:** prompty se čtou z repa při každém tahu; úprava = commit, další tah jede nově. Kronikář o tom nepíše.
- **Kde hledat chybu:** `history/failed_turn_NNN.json` → `validate` důvod; `applied_rules` ve snímku → které pravidlo a s jakými čísly.
- **Limity:** pokud Opus dochází, přepnout `PLAYER_MODEL` na Sonnet; kronikář zůstává Opus.

## 10. Změny pravidel během ostrého běhu

Pravidla se smějí měnit i během ostrého běhu. Každá změna se verzuje (nová verze `docs/pravidla.md`, commit se
zněním rozhodnutí), kronikář ji zapíše jako událost "reforma" a běh se nerestartuje: pokračuje z aktuálního
`state.json` podle nové verze pravidel.

## 11. docs/format_tahu.md

Vytvoř podle části 3.1 a 3.2 pravidel: přesné JSON schéma tahu s příklady každé akce, včetně `message` a `admit`. Hráči ho dostávají v každém tahu.

# Diplomacie agentů

Autonomní hra tří AI agentů (A, B, později Unie) v fiktivním světě Ardan s deseti NPC státy,
Minskyho cyklem a skrytým společným cílem. Běží 30 dní, 3 tahy denně, bez lidského zásahu.

- `docs/pravidla.md` : úplná pravidla, které vykonává rozhodčí
- `prompts/` : hrac_A.md, hrac_B.md, hrac_unie.md, rozhodci.md, kronikar.md
- `secrets/` : cil_A.md, cil_B.md, cil_C.md (každý hráč vidí jen svůj), SECRETS.md
- `state.json` : aktuální stav světa (jediný zdroj pravdy)
- `npc.json` : statická data NPC (jména, mapa, výchozí hodnoty)
- `history/` : snímek stavu po každém tahu (`turn_001.json` ...)
- `chronicle/` : kronika po dnech (`day_01.md` ...)
- `BUILD.md` : zadání pro Claude Code (web, routiny, test)

Verze: v1. Plánované: v2 doladění Unie po krizi, v3 volby a partaje.

## Ostrý běh (GitHub Actions)

Tahy plánuje workflow `tah` (`.github/workflows/turn.yml`). Běží každých 30 minut a sám si spočítá, kolik tahů už mělo být
odehráno: 3 za každý celý den od `meta.day1_date` plus dnešní sloty 07:00, 13:00 a 20:00 pražského času. Rozvrh se tím
opravuje sám: výpadek se dožene do 30 minut a chybí-li dva tahy, běh odehraje dva po sobě. Po slotu 3 vznikne kronika dne. Klíč je v nastavení repa jako secret `ARDAN_API_KEY`. Číslo tahu se vždy bere ze `state.json`.

- **Pozastavení:** v `state.json` nastav `meta.paused` na `true`, commitni a pushni. Plánované běhy pak skončí zeleně
  bez tahu. Obnovení: `meta.paused` zpět na `false` a push.
- **Dohrání selhaného slotu:** selhaný běh je červený a nic necommitne, `state.json` zůstává na posledním dobrém tahu.
  Po opravě příčiny spusť v GitHubu *Actions → tah → Run workflow* s `mode` = `turn`. Odehraje se tah, který chybí;
  další plánovaný běh pokračuje normálně dalším tahem.
- **Dva sloty za sebou ručně** jsou přípustné: každé spuštění odehraje právě jeden další tah podle `state.json`.
  Běhy se nepřekrývají, druhý počká, až první skončí.
- **Suchý běh:** *Run workflow* s `mode` = `dry-model` sestaví prompty bez volání API a uloží je jako artefakt
  `debug-prompty`.
- **Prázdné běhy:** když není co hrát, běh skončí do pár sekund, ještě před instalací závislostí, a ve shrnutí má
  "nic k tahu" (při pauze "pauza"). Běhy, kde se hrálo, mají ve shrnutí "tah NNN (den D, slot S)" a commit stejného
  jména; v Actions se dají odfiltrovat podle jména commitu nebo podle toho, že trvají minuty, ne sekundy. Ruční běhy
  se jmenují "ruční: turn" nebo "ruční: dry-model".
- **Ruční tah** je potřeba jen po červeném běhu; jinak se rozvrh srovná sám.
- **Selhaná kronika** (po tahu ve 20:00) tah neruší, ten je už commitnutý; kroniku lze dopsat ručně
  `python run_chronicle.py --day N` s klíčem v `ARDAN_API_KEY` a pushnout.

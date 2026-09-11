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

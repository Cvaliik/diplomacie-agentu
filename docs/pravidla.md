# Pravidla světa Ardan (v1.11)

v1.11, platí od tahu 1 (restart 16. 9. 2026, rozhodnutí Adama z téhož dne). Tahy 1 až 5 odehrané podle v1.10.2
se zahazují a ostrý běh začíná znovu od tahu 0.
- **Změna principu viditelnosti (2):** hráč vidí své vlastní `law`, `tech` a `industry` a jejich změny tah od tahu.
  Hodnoty vidí, dopady ne: skrytý zůstává index prosperity a jeho vzorec, prahy a cizí `law` a `tech`.
- **Goods jako kapitál (4.0):** `invest_tech`, `invest_industry`, `invest_prod` a `arm` spotřebují vedle bohatství
  i `goods`; bez goods se investice odkládá. Automatika NPC s `law < 5` investuje do práva (4.2a).
  Hráči A a B dávají na trh spekulativně 50 % volné kapacity (4.0) a u `goods` nemají paušál přejezdu (4.1a).
- **Domácí akce (3.1):** hráči A a B mají vedle 2 akcí jednu domácí akci mimo limit.
- **Zpráva zdarma (3.2):** `message` se do limitu akcí nepočítá, nejvýš jedna za tah.
- **Paměť hráčů (3):** hráč dostává své úvahy z posledních 3 tahů, přehled od svého minulého tahu a přehled smluv.

Verze v1.10.2, platila od tahu 1 restartu 15. 9. 2026: hráči A a B na automatickém trhu prodávají jen vlastní produkci nad
potřebu (4.1a), cena tahu se počítá před pohledy hráčů a pásmo `trade_offer` se hodnotí proti ní (4.1b), každé
vyřazení akce enginem jde do soukromého logu hráče (3.4). Tahy 1 a 2 odehrané podle v1.10 a v1.10.1 se zahazují.

Verze v1.10.1 od tahu 2 (reforma během ostrého běhu, stav po tahu 1 se nemění): hráči A a B na automatickém trhu
neprodávají zásobu (4.1a), pohled hráče ukazuje jeho automatické obchody minulého tahu (2), Zprávy světa jmenují
státy jménem (6). Potvrzené výklady U3 až U8, V5 a V7 až V11 z `docs/OPEN_QUESTIONS.md` jsou závazným textem.

Verze v1.10 zapracovává rozhodnutí Adama z 15. 9. 2026: soutěž hráčů o stejný cíl (3.4a), nejvýš jeden pakt
na NPC (3.2), pakt a invaze ve stejném tahu (3.3), válka hráčů (3.3a), `arm` s parametrem (3.2) a `admit`
ze zóny vlivu (7.4). Tah 1 odehraný podle v1.9 se zahazuje a ostrý běh začíná znovu od tahu 0.

Verze v1.9 zapracovává rozhodnutí Adama ze 14. 9. 2026: cíl automatické `invest_prod` podle ceny (4.2a),
spekulativní nabídka velkých továren na trhu (4.0, 4.1a), párování automatického trhu podle ceny s paušálem
přejezdu hráčů (4.1a), clo jako akce Unie `set_tariff` a obchod Unie za členy (7.2, 3.2). Potvrzené výklady
S1 až S7 z `docs/OPEN_QUESTIONS.md` jsou nově závazným textem.

Verze v1.8 zapracovává rozhodnutí Adama z 18. 9. 2026: komparativní výhoda ve výrobě `goods` (4.0),
celní unie (7.2), nová akce `invest_prod` a její automatika u NPC (3.2, 4.2a) a úprava produkce ropy
N3 a B. Potvrzené výklady Q1 až Q8 z `docs/OPEN_QUESTIONS.md` jsou nově závazným textem.

Verze v1.7 zapracovává rozhodnutí Adama ze 14. 9. 2026: výroba `goods` podle poptávky a poptávka
po produktu rostoucí s bohatstvím (4.0), zakladatelé Unie sousedí mezi sebou (7.1), tvrdý práh práva
u `admit` (7.4, 3.4), rozdělení míst pro nabídky NPC (3.5) a protinávrh půjčky (3.4). Potvrzené výklady
O1 až O5, O7, O8, O11, O12, O14, O15, O18 a O19 z `docs/OPEN_QUESTIONS.md` jsou nově závazným textem.

Verze v1.6 zapracovává rozhodnutí Adama z 16. 9. 2026: hráči obchodují i spolu (4.1a, 3.2), kalibrace
ropy (4.0), padlé říše na trhu za tržní cenu (7a, 4.1a), doplňování rezervy od `wealth ≥ 25` (4.1c),
příspěvky do fondu Unie a nová solidarita (7.2), nový výběr zakladatelů bez mostu (7.1), uvolnění
sfér při dluhu a přetížení sfér (5, 4.4), čtyři nová NPC N13 až N16, vůle NPC při cílených nabídkách
(3.4) a nabídky NPC hráčům (3.5). Potvrzené výklady M2, M3, M4, M7, M9 a M11 z
`docs/OPEN_QUESTIONS.md` jsou nově závazným textem.

Verze v1.5 zapracovává rozhodnutí Adama ze 14. 9. 2026: globální automatický trh s tranzitem (4.1a),
rezervu nedoplňuje stát v bídě nebo s `wealth < 15` (4.1c), Unie může vzniknout přes most (7.1),
členství v Unii přežívá převrat (4.3, 7.4, 7.5) a automatická solidarita fondu (7.2). Potvrzené
výklady K1, K3 až K8 z `docs/OPEN_QUESTIONS.md` jsou nově závazným textem.

Verze v1.4 zapracovává rozhodnutí Adama z 15. 9. 2026: hráči na automatickém trhu i nakupují (4.1a),
nedotknutelná rezerva tří tahů spotřeby (4.1c), automatické investice jen při rostoucím bohatství
(4.2a), neformální příjem `pop / 60` (4.2b), silnější produkce chudých NPC, výroba `goods`
vztažená k `pop_start` (4.0), hráč vidí vlastní zásoby (2), dno průmyslu i pro padlé říše (4.2c),
Unie orit neprodává (4.1a), zánik paktu při nulové síle (3.2), pojistka cyklu 8 tahů (5)
a kandidatura přežívající převrat (4.3, 7.4). Potvrzené výklady I2 až I7, I10 a I12
z `docs/OPEN_QUESTIONS.md` jsou nově závazným textem.

Verze v1.3 zapracovává rozhodnutí Adama ze 14. 9. 2026: hráči A a B prodávají přebytky
na automatickém trhu a orit se automaticky neobchoduje (4.1a), zásoby (nová 4.1c), padlé říše
obchodují oběma směry (7a), efektivní produkce vztažená k výchozímu obyvatelstvu `pop_start`
a nové obyvatelstvo (4.0, 10.2), nová struktura NPC a `W_0` 717 (8), dno průmyslu 0.5 (4.2c)
a pojistka cyklu 10 tahů (5). Potvrzené výklady G1, G3 až G10 a G15 z `docs/OPEN_QUESTIONS.md`
jsou nově závazným textem.

Verze v1.2 zapracovává rozhodnutí Adama ze 14. 9. 2026: dvousektorový model s průmyslem
a produktem `goods` (nová část 4.0), počítané potřeby místo zadaných, zrušení autonomního
růstu bohatství (4.2), neformální příjem (4.2b), růst průmyslu (4.2c), akce `invest_industry`,
nová pravidla převratu (4.3), pojistka cyklu a strop ceny oritu (5). Potvrzené výklady C9,
C10 a C12 z `docs/OPEN_QUESTIONS.md` jsou nově závazným textem (7.1, 4.3, 4.1a).

Verze v1.1 zapracovává rozhodnutí Adama z 11. 9. 2026: potvrzené výklady z
`docs/OPEN_QUESTIONS.md` částí A, B a C jsou nově závazným textem, a mění se
obchod NPC mezi sebou (4.1a), cena zdrojů (4.1b), náklad nepokrytého oritu (4.1),
automatika NPC (4.2a), základ růstu (4.2), index prosperity (8), práh overtrading
a počítání nesplácení (5) a velikost Unie (7.1, 7.4).

Pravidla vykonává rozhodčí (`prompts/rozhodci.md`). Hráči je neznají; znají jen to, co je v jejich promptu a ve Zprávách světa. Kronikář a veřejná stránka vidí vše.

## 1. Aktéři

- **A, Kalverská federace**: tržní ekonomika, kapitál, banky, export práva a obchodních pravidel.
- **B, Lidová republika Ostrogard**: plánovaná ekonomika, kontrola zdrojů, export ochrany a stability.
- **Unie (C)**: vzniká až po fázi Crash z NPC, které krize zasáhla nejvíc. Do té doby neexistuje.
- **16 NPC**: řízeny pravidly, nemají vlastní volání modelu. Data v `npc.json`. Čtrnáct běžných, dvě padlé říše (`kind: fallen`, viz 7a). Síla nových NPC na startu je N13 8, N14 8, N15 7 a N16 4 (průměr běžných NPC s bohatstvím v rozmezí ±10). Na mapě leží N13 na (250, 520), N14 na (430, 230), N15 na (730, 130) a N16 na (730, 460); N13 se bez křížení vazeb umístit nedá a kříží 2, N16 kříží 1.

Aritmetiku a prahy vykonává `engine.py` (deterministicky). Rozhodčí (model) tahy jen překládá na akce, rozhoduje sporné případy a píše Zprávy světa. Viz `BUILD.md`.

## 2. Veličiny

Každý stát (hráč i NPC) má:

| pole | rozsah | veřejné pro hráče | význam |
|---|---|---|---|
| `wealth` | 0+ | ano | reálné bohatství |
| `paper_wealth` | 0+ | ano (jako součást "bohatství") | papírové bohatství z bubliny, po krizi mizí |
| `power` | 0+ | ano | vojenská síla |
| `law` | 0 až 10 | jen vlastní (v1.11); Unie u členů a kandidátů | instituce, vymahatelnost práva |
| `tech` | 0 až 10 | jen vlastní (v1.11); Unie u členů a kandidátů | technologie, efektivita produkce |
| `industry` | 0 až 10 | ano | míra industrializace, určuje výrobu `goods` (4.0) |
| `openness` | 0 až 10 | NE | ochota NPC přijímat cílené nabídky (3.4); jen v `npc.json` |
| `prod` / `need` | jednotky | ano | produkce a spotřeba: `oil`, `grain`, `metal`, po displacementu i `orit`; spotřeba navíc `goods`. `need` se nezadává, engine ho počítá každý tah podle 4.0 a zapisuje do snímku |
| `influence` | {A, B} 0+ | částečně (jen vlastní) | náklonnost NPC k hráči |
| `debt` | {A, B, C} 0+ | jen věřitel | dluhy NPC vůči hráčům |
| `status` | viz níže | ano | independent / sphere_A / sphere_B / occupied_A / occupied_B / union / candidate |
| `coups` | 0+ | ano | počet pádů vlády |
| `kind` | normal / fallen | ano | padlá říše má zvláštní pravidla (7a) |
| `pop` / `pop_start` | 0+ | ano | obyvatelstvo; `pop_start` je výchozí obyvatelstvo státu (4.0), k němu se vztahuje efektivní produkce |
| `stock` | 0+ | jen vlastní | zásoby `grain`, `oil`, `metal`, `goods` a `orit` (4.1c) |

**Princip viditelnosti (v1.11):** hodnoty vidí, dopady ne; skrytý je index a jeho vzorec. Hráči A a B vidí u sebe `law`, `tech` a `industry` a jejich změnu proti minulému tahu a proti tahu 1; co ukazatele dělají, se nedozví jinak než ze dění ve světě. Cizí `law` a `tech` zůstávají skryté (Unie je vidí u členů a kandidátů), cizí `industry` je veřejné. Publikum na webu vidí u všech států včetně A a B `goods` (zásoba, výroba, potřeba), `industry`, `law` a `tech`.

Hráči vidí u NPC: `wealth + paper_wealth` (jako jedno číslo "bohatství"), `power`, `prod`, `need`, `industry`, výrobu, potřebu a bilanci `goods`, `status`, `pop`, a svou vlastní `influence` a své pohledávky. Nevidí `law`, `tech`, cizí vliv, cizí pohledávky ani cizí zásoby. Vlastní `stock` hráč vidí. Hráči A a B navíc vidí blok `automaticky_obchodovano`: co v minulém tahu na automatickém trhu prodali a nakoupili, s množstvím a průměrnou cenou. Pohled je kompaktní JSON: čísla na 1 desetinné místo, ceny, clo a ceny v nabídkách na 2, aby šla dodržet sazba po 0.05 a pásmo ceny u `trade_offer`.

`status` má jen NPC. Hráči A a B status nemají, hodnoty jako `sphere_X` nebo `candidate` se na ně nevztahují.

Hráči A a B mají navíc `poverty_streak` a `coups` jako NPC, protože bída podle 4.3 se vztahuje na každý stát včetně nich. `coups` u hráče jen eviduje, pád vlády hráče nepotkává (viz 4.3).

Unie má `wealth` i `fund`, ale je to jedna kapsa: `wealth` je zdroj pravdy a `fund` jeho zrcadlo, přepsané na konci každého tahu. Unie nemá `prod`, `need` ani `pop`, ty zůstávají členům. Fond Unie se nezapočítává do `W_real` v části 8 a Unie není aktér pro `max_share`, protože ty prostředky pocházejí z bohatství členů, které se počítá u nich.

Trvalé vztahy (obchody, pakty, sankce) drží seznam `deals`, kde každý záznam má stabilní `id` tvaru `d` a pořadové číslo, které se nikdy nerecykluje. Akce `cancel` se odkazuje právě na toto `id`. Probíhající invaze drží `invasions` se stejnou logikou identifikátoru (`i` a pořadové číslo).

## 3. Tah

Hra má 3 tahy denně (7:00, 13:00, 20:00), 90 tahů celkem, den 30 = tahy 88 až 90.

`slot` je 1 pro ráno, 2 pro poledne, 3 pro večer. Den se počítá jako `((turn - 1) // 3) + 1`,
slot jako `((turn - 1) % 3) + 1`.

Pořadí v tahu:
1. Hráč A dostane `views/A.json` (jeho pohled na svět) + veřejný log + Zprávy světa posledních 3 tahů. Vrátí tah.
   Od v1.11 navíc tři bloky paměti, sestavené z vlastních úvah hráče a dat enginu, nikdy z cizích úvah:
   `tve_minule_uvahy` (vlastní `private_reasoning` z posledních 3 tahů s číslem tahu), `od_tveho_minuleho_tahu`
   (akce a veřejné výsledky soupeře, jeho projev doslova, vlastní akce a výsledky včetně vyřazení s důvodem, změna
   vlastního `wealth` a `power` proti minulému tahu a tahu 1, změna `law`, `tech`, `industry`, změny vlastního vlivu
   u NPC, změny cen, změny statusu států a nové nabídky NPC; fakta bez hodnocení) a `tve_smlouvy` (trvalé obchody
   a pakty s nákladem nebo výnosem za tah v `wealth` a `power` a součtem).
2. Hráč B totéž se svým pohledem. Nevidí tah A z tohoto tahu (tahy jsou simultánní).
3. Unie (od svého vzniku) totéž.
4. Rozhodčí vyhodnotí všechny tahy najednou, přepočítá svět, vydá Zprávy světa, posune Minskyho fázi, uloží `state.json` a `history/turn_NNN.json`.

### 3.1 Formát tahu hráče

```json
{
  "public_statement": "Diplomatický projev, vidí ho všichni. 2 až 5 vět.",
  "private_reasoning": "Skutečné zdůvodnění, vidí ho jen publikum. Upřímně, včetně lží v projevu.",
  "actions": [ { "type": "...", ... }, { "type": "...", ... } ],
  "domestic_action": { "type": "invest_industry" },
  "message": { "target": "B", "text": "..." }
}
```

Max 2 akce za tah (Unie 3, protože je pomalá jinde). Neplatné akce rozhodčí ignoruje a zapíše důvod.

**Domácí akce (v1.11):** hráči A a B smějí navíc jednu domácí akci v poli `domestic_action` (objekt nebo `null`). Povolené typy: `invest_tech`, `invest_law`, `invest_industry`, `invest_prod`, `arm`, `explore`, vždy na vlastní stát. Do limitu 2 akcí se nepočítá; rozhodčí ji přeloží na akci s `"slot": "domestic"` a jiný typ nebo cizí cíl vyřadí. Investice do NPC ve sféře zůstávají běžnými akcemi v limitu. Unie domácí akci nemá.

**Zpráva mimo limit (v1.11):** `message` se do limitu akcí nepočítá; nejvýš jedna za tah, doručena v příštím tahu, publikum ji vidí. Hráč ji zadává v poli `message` odpovědi (objekt `target`, `text`, nebo `null`). Akci `message` vytváří `run_turn.py` přímo z tahu hráče (v1.12), rozhodčí zprávy nepřekládá. Odpověď hráče i rozhodčího se kontroluje proti JSON schématu (strukturovaný výstup API). **Platná odpověď hráče (v1.12):** `private_reasoning` má aspoň 80 znaků a tah obsahuje aspoň jednu akci, domácí akci nebo zprávu; jinak se odpověď opakuje jako neplatná (10.6).

### 3.2 Akce

| type | parametry | efekt | náklad |
|---|---|---|---|
| `trade_offer` | `target`, `res`, `qty`, `price_per_unit` | NPC přijme, pokud má přebytek/deficit a cena je v pásmu 0.7 až 1.5 aktuální tržní ceny podle 4.1b; vzniká trvalý obchod, dokud ho někdo nezruší. Směr určuje bilance NPC u dané suroviny: přebytek znamená, že NPC hráči prodává, deficit, že od něj nakupuje, nulová bilance je odmítnutí. Množství se ořízne na velikost bilance. NPC nabídku vyhodnotí podle 3.4. Cílem může být i druhý hráč (A nebo B); obchod mezi hráči projde bez vyhodnocení podle 3.4, má-li cíl přebytek nebo deficit a je-li cena v pásmu. Unie obchoduje za členy, viz 7.2 | žádný |
| `loan` | `target`, `amount` | hráč převede `amount` bohatství NPC; NPC dluží `amount × 1.2`; splácí 10 % dluhu za tah z bohatství | `amount` wealth |
| `pressure` | `target`, `demand` | sankce: přeruší obchody hráče s NPC; NPC ztrácí 3 wealth/tah, hráč 1; `influence` protivníka +1. Cílem může být i druhý hráč: sankce pak po dobu trvání přeruší vzájemný automatický obchod obou hráčů a stojí oba 1 wealth/tah; cílené obchody mezi nimi trvají dál | 1 wealth/tah |
| `protect` | `target` | vojenský pakt: NPC `power` +2/tah, `influence[hráč]` +2/tah, `law` −0.2/tah; NPC nelze napadnout, dokud pakt trvá (útok = válka s ochráncem, viz 3.3a). NPC má nejvýš jeden aktivní pakt: `protect` na NPC s cizím paktem se vyřadí bez hodu s důvodem „NPC je pod paktem X“ | 2 power/tah |
| `invade` | `target` | viz 3.3; cílem je jen NPC, hráče nelze dobýt ani okupovat | 10 wealth + 5 power za tah |
| `invest_tech` | (vlastní stát nebo `target` v sphere/union) | `tech` +0.3 | 8 wealth + 4 goods (v1.11) |
| `invest_law` | `target` v sphere/union, nebo vlastní | `law` +0.3 | 6 wealth |
| `invest_industry` | vlastní stát nebo `target` v sphere/union (Unie: členové a kandidáti) | `industry` +0.3 × (law/5), jen při `law ≥ 4` cíle | 10 wealth + 6 goods (v1.11) |
| `invest_prod` | `res`, `target` (volitelný) | `prod[res]` +1, jen pro zdroj s `prod[res] > 0` a jen při `tech ≥ 3`; orit se takto zvýšit nedá. Cílem je vlastní stát nebo NPC ve vlastní sféře, u Unie členové a kandidáti (jako `invest_industry`); `prod > 0` i `tech ≥ 3` se berou u cíle | 12 wealth + 4 goods (v1.11) |
| `explore` | (vlastní stát) | 15 % šance na malé ložisko oritu (prod.orit +2) | 5 wealth |
| `arm` | `amount` (vlastní stát, jen A a B) | `power` += `amount` / 1.6, nejvýš 40 wealth na akci; bez `amount` se bere 8 (síla +5). Unie `arm` použít nemůže, její síla je součet členů | `amount` wealth + 1 goods na každých započatých 8 wealth (v1.11) |
| `declare_war` | `target` A nebo B | vyhlášení války druhému hráči, viz 3.3a | viz 3.3a |
| `admit` | jen Unie: `target` nezávislé NPC | nabídka členství, viz 7 | žádný |
| `cancel` | `deal_id` | zruší obchod, pakt nebo sankci; `cancel` na válku je nabídka příměří, `cancel` s `"retreat": true` ústup (3.3a) | žádný |
| `message` | `target` (A/B/C), `text` | soukromá zpráva druhému hráči, doručena v příštím tahu; publikum ji vidí; mimo limit akcí, nejvýš 1 za tah (v1.11) | žádný |
| `union_fund` | jen Unie: `target` člen, `amount` | převod ze společného fondu členovi | fond |
| `set_tariff` | jen Unie: `rate` 0 až 0.20 po 0.05 | sazba cla celní unie od dalšího tahu, viz 7.2 | žádný |
| `accept_offer` | `offer_id` | přijme nabídku NPC z pohledu hráče bez vyhodnocení podle 3.4 (3.5) | žádný |

**Zánik paktu:** pakt `protect` zaniká, když `power` ochránce klesne na 0. Engine k tomu vydá událost pro rozhodčího: „X stahuje posádky z N“. Srazí-li sílu na 0 sama údržba paktu, pakt v tomto tahu ještě působí a pak zanikne; klesne-li síla na 0 jinak (bída, válka), pakt zanikne při nejbližší údržbě.

### 3.3 Dobývání

- Podmínka: `power` útočníka ≥ 2 × `power` cíle a cíl není pod paktem druhého hráče. Útok na NPC pod paktem druhého hráče vyhlásí válku hráčů automaticky (3.3a) a invaze nepostupuje. V tazích 1 až 9 a 88 až 90, kdy válku vyhlásit nelze, se invaze na NPC pod paktem druhého hráče vyřadí bez války.
- **Pakt a invaze ve stejném tahu:** míří-li v jednom tahu `protect` jednoho hráče a `invade` druhého na totéž NPC, vyhodnotí se nejdřív pakt. Přijme-li ho NPC, je invaze od tohoto tahu válkou (3.3a); odmítne-li, invaze začíná normálně.
- Trvá 6 po sobě jdoucích tahů s akcí `invade`. Přerušení = start znovu. Paralelní invaze jsou povoleny (každá se platí zvlášť).
- Strach z agresora: za každé okupované NPC ztrácí okupant 1 `influence`/tah u všech nezávislých NPC.
- Výsledek: `status` = `occupied_X`, `law` −3, `wealth` −30 %, `pop` −20 % (uprchlíci jdou do nejbližšího NPC, který dostane `pop` +, `wealth` −2/tah po 3 tahy). Zdroje NPC se počítají útočníkovi.
- Okupované NPC v bídě (viz 4.3) může v Crashi/Depresi zrevoltovat: 30 % šance/tah, vrací se na `independent` a připojí se k Unii, pokud existuje.

### 3.3a Válka hráčů

- **Vyhlášení:** akce `declare_war` s `target` A nebo B. Útok na NPC pod paktem druhého hráče vyhlásí válku automaticky. Válku nelze vyhlásit v tazích 1 až 9 ani 88 až 90; v těchto tazích se `declare_war` i útok na NPC pod paktem druhého vyřadí.
- **Každý tah války, od tahu vyhlášení:** oba hráči `power` −10 a `wealth` −5 %; automatický obchod mezi nimi je přerušen; obchod každého z nich s NPC ve sféře druhého se násobí 0.5; všechna nezávislá NPC snižují `influence` u toho, kdo válku vyhlásil, o 2 a u napadeného o 1.
- **Unie:** po dobu války platí ten, kdo válku vyhlásil, clo celní unie navíc o 0.10. Členové Unie do války nevstupují.
- **Konec ústupem:** jen výslovně, `cancel` s `deal_id` války a `"retreat": true`. Kdo ustoupí, ztrácí 30 % vlivu u všech NPC a válka končí okamžitě.
- **Příměří:** `cancel` na válku bez `retreat` je nabídka příměří. Pošle-li druhá strana `cancel` ve stejném nebo v následujícím tahu, válka končí příměřím a oba ztrácejí 10 % vlivu u všech NPC. Nepřijatá nabídka propadne bez následku a válka pokračuje.
- **Konec kapitulací:** klesne-li hráči `power` na 0, kapituluje: ztrácí všechny pakty, 50 % vlivu u všech NPC a 20 % svého `wealth`, které jde vítězi.
- Hráče nelze dobýt ani okupovat. NPC, o které se válčí, za války bohatství neztrácí. Vyhlášení války i její konec jsou události pro Zprávy světa.

### 3.4 Rozhodování NPC o nabídkách

U cílených akcí `trade_offer`, `loan` a `protect` od hráčů a `admit` od Unie NPC nabídku vyhodnotí. Automatický trh 4.1a se nemění.

NPC má skrytou vlastnost `openness` (0 až 10) v `npc.json`: N1 5, N2 4, N3 4, N4 6, N5 6, N6 5, N7 5, N8 5, N9 2, N10 4, N11 9, N12 3, N13 7, N14 5, N15 3, N16 4. Hráči ji nevidí.

**Skóre** = 40 + 4 × (`influence[X]` − `influence[soupeř]`) + 30 × (nabízená cena / tržní cena − 1) + 4 × (`openness` − 5) + bonusy:

- `loan` ve fázi `boom` nebo `euphoria`: +20;
- `loan` při dluhu NPC nad 50 % jeho `wealth`: −20;
- `protect` při `power` NPC nad 8: −15;
- sankce od X vůči NPC v posledních 6 tazích: −25;
- `law` NPC ≥ 7 a cena mimo pásmo 0.9 až 1.2 tržní: −20.

U `admit` je `law ≥ law_threshold` tvrdá podmínka (7.4); hod rozhoduje až po jejím splnění a místo ceny se počítá bonus +10.

Cenový člen se hodnotí z pohledu NPC: když NPC nakupuje, počítá se s opačným znaménkem, takže vyšší cena skóre snižuje.

**Hod d100** z `random.Random(rng_seed + turn + hash(ID))`, kde `hash(ID)` je CRC32 z ID NPC (vestavěný `hash()` Pythonu se mezi běhy mění a běh by nebyl reprodukovatelný); všechny nabídky na totéž NPC v jednom tahu mají stejný hod:

- hod ≤ skóre: přijato;
- hod ≤ skóre + 20: přijato s podmínkou (objem nebo půjčka −30 %, případně cena o 10 % ve prospěch NPC; engine zvolí, co je pro daný typ akce relevantní: u `trade_offer` objem −30 %, u `loan` částka −30 %, u `protect` a `admit` přijato beze změny);
- hod ≤ skóre + 35: protinávrh (NPC vrátí parametry jako soukromou zprávu hráči; u `trade_offer` posune cenu o 10 % ve prospěch NPC při stejném objemu; `trade_offer` se shodnými parametry v dalších 3 tazích projde bez hodu; stejně projde `loan` s částkou podle protinávrhu na totéž NPC v dalších 3 tazích);
- jinak odmítnuto.

Výsledek s jednou větou důvodu (z faktoru, který skóre nejvíc srazil) jde do soukromého logu hráče a do snímku, do Zpráv světa ne. Stejně jde do soukromého logu každé vyřazení akce enginem (cena mimo pásmo, neplatný cíl, blokovaná invaze, překročený limit akcí a podobně) s důvodem, takže ho hráč v dalším tahu vidí v pohledu.

### 3.4a Soutěž o stejný cíl

Cílené akce hráčů na totéž NPC v jednom tahu se vyhodnotí před provedením, ne v pořadí seznamu. Konfliktní dvojice jsou `trade_offer` na stejnou surovinu, `protect` proti `protect`, `invade` proti `invade` a `admit` proti `protect`. Pro každou akci dvojice se spočte skóre podle 3.4; akce s vyšším skóre jde do normálního vyhodnocení (hod, podmínka, protinávrh). Pro `invade` proti `invade`, kde 3.4 nemá cenový člen ani bonusy, se počítá základ 40, vliv a otevřenost. Skóre se porovnává na 9 desetinných míst; při remíze rozhodne hod d100 z `rng_seed + turn + CRC32(ID)`: do 50 vyhrává akce, která je v seznamu akcí dřív, jinak pozdější. Prohraná akce se neprovede a do soukromého logu prohraného se zapíše „NPC dalo přednost nabídce druhé strany“.

### 3.5 Nabídky NPC hráčům

Engine každý tah vygeneruje pro každého hráče (A, B, po vzniku Unie i C) nejvýš 2 nabídky od NPC, vybrané podle nejvyššího vlivu daného hráče u NPC:

1. `sell`: NPC s přebytkem statku nad rezervu, který hráč tento tah dovážel; cena = tržní × 0.9 při `wealth` NPC pod 25, × 1.0 jinak, × 1.15 při `openness` ≤ 3, přičemž `openness ≤ 3` má přednost před `wealth` pod 25; množství je menší z přebytku nad rezervu a dovozu hráče v tomto tahu;
2. `loan_request`: NPC v bídě nebo s deficitem oritu, částka 10 + max(0, 15 − `wealth`) + 5 × chybějící orit, nejvýš 20;
3. `protect_request`: NPC, jehož soused je právě cílem invaze, nebo u kterého vliv soupeřícího hráče vzrostl za poslední 3 tahy aspoň o 4; jen hráči s vyšším vlivem.

Nabídka jde do pohledu hráče s `offer_id` a platí 2 tahy. Akce `accept_offer` (`offer_id`) ji provede bez hodu podle 3.4 a počítá se jako akce. Tři po sobě ignorované nabídky téhož NPC snižují vliv hráče u něj o 1.

**Rozdělení míst:** z dvou míst na hráče a tah je nejvýš jedno `sell`; druhé dostane `loan_request` nebo `protect_request` s nejvyšším vlivem, a jen když žádná není, druhé `sell`. Když žádná `sell` není, dostanou obě místa `loan_request` nebo `protect_request` s nejvyšším vlivem. Jedno NPC dá hráči nejvýš jednu nabídku daného druhu a u jednoho NPC má `loan_request` přednost před `protect_request`.

**Platnost:** nabídku z tahu t lze přijmout v tazích t+1 a t+2; nepřijatá propadne na konci tahu t+2 a počítá se jako ignorovaná. Po třetí ignorované v řadě klesne vliv o 1 a počítadlo se nuluje; Unie vliv nemá. Přijatá nabídka `sell` je jednorázový obchod v tomtéž tahu a jako cílený obchod s hráčem přidá v 4.4 vliv +1.

## 4. Přepočet světa (každý tah, v tomto pořadí)

### 4.0 Dvousektorový model

Každý stát má vedle surovin i průmysl. Průmysl vyrábí produkt `goods`, který potřebují všichni.

**Průmysl.** Veličina `industry` (0 až 10) je u každého státu a je veřejná pro hráče. Výchozí hodnoty: A 8, B 6, N11 a N12 7, N3 a N4 (ropa) 4, N1 a N2 (obilnice) 2, N5 a N7 (kovy) 3, N6, N8, N9 a N10 (chudé) 1, N13 5, N14 3, N15 2, N16 1.

**Produkt.** `goods` má základní cenu 1.5 s dynamikou podle 4.1b. Obchoduje se jako ostatní statky, cíleně s hráči i na automatickém trhu (4.1a).

**Výroba za tah:**

`kapacita = industry × (pop / pop_start) × (1 + tech / 10)`

**Výroba podle poptávky:** stát vyrábí jen do výše `plánovaná výroba = min(kapacita, vlastní potřeba goods + 1.2 × goods prodané v minulém tahu + doplnění rezervy goods)`; zbytek kapacity továren stojí. Prodaným množstvím se rozumí `goods` prodané na automatickém trhu a cílenými obchody, bez vnitřního trhu Unie. Doplnění rezervy `goods` je 3 tahy spotřeby minus zásoba; doplňuje se vlastní výrobou, a proto se na něj práh `wealth ≥ 25` nevztahuje.

**Komparativní výhoda:** stát s `industry < 2` plánuje výrobu `goods` nejvýš na 50 % vlastní potřeby a zbytek dováží (malé továrny jsou drahé). Strop 50 % vlastní potřeby platí pro celý plán, tedy i pro prodej minulého tahu a doplnění rezervy. Svůj deficit `goods` včetně doplnění rezervy malé továrny nakupují na automatickém trhu jako u ostatních statků (4.1a, 4.1c). Stát s `industry ≥ 4` plánuje navíc export: vlastní potřeba + prodané minulý tah × 1.2 + doplnění rezervy `goods` + spekulativní nabídka na trh. Spekulativní nabídka je u NPC 10 % kapacity. **U hráčů A a B (v1.11)** je to 50 % volné kapacity, kde volná kapacita = kapacita − vlastní potřeba `goods` − investiční spotřeba `goods` tahu (součet goods čekajících investic hráče). Důvod: hráčovy továrny mají vyrábět na vývoz, ne stát; 10 % kapacity z velkých továren hráčů obchod nerozhýbalo. **Spekulativní nabídka** (podle věty výše, nejvýš letošní výroba) jde na automatický trh vždy, i když zásoba `goods` po výrobě nedosahuje rezervy 3 tahů spotřeby; do zásoby jde jen to, co se neprodá. Zásoba `goods` tím smí klesnout pod rezervu, ne však pod nulu; hráči A a B nabízejí nejvýš vlastní produkci nad potřebu (4.1a). Ostatní státy plánují podle vzorce výše.

`goods_out = plánovaná výroba × coverage`

Na jednotku `goods` jsou potřeba vstupy `oil 0.5` a `metal 0.3`. `coverage` je podíl průmyslových vstupů, které má stát k dispozici (0 až 1): nejmenší z poměrů dostupné ropy k průmyslové potřebě ropy a dostupných kovů k průmyslové potřebě kovů. Chybí-li jeden vstup, továrny stojí, i když druhého je dost. Do dostupných vstupů se počítá i zásoba (4.1c); domácnosti mají na zdroje dál přednost. Průmyslové vstupy (ropa, kovy) se nakupují a doplňují jen pro plánovanou výrobu, ne pro plnou kapacitu, a `coverage` se počítá vůči plánované výrobě; z ní vychází i růst průmyslu v 4.2c. Když stát nic neplánuje vyrábět, je `coverage` 0 a průmysl mu podle 4.2c neroste. Domácnosti mají na zdroje přednost (obilí a základní spotřeba), průmysl bere až zbytek. Bez ropy továrny stojí.

**Goods jako kapitál (v1.11).** Investice spotřebovávají `goods`: `invest_tech` 4, `invest_industry` 6, `invest_prod` 4, `arm` 1 goods na každých započatých 8 wealth (zaokrouhlení nahoru); `invest_law` a `explore` goods nepotřebují. Totéž platí pro automatické investice NPC (4.2a). Unie za investice goods neplatí, protože nemá zásobu.
- Goods se berou ze zásoby investora v okamžiku akce. Chybějící goods se koupí na automatickém trhu v tomtéž tahu jako poptávka toku investora (4.1a); investiční poptávka se tím počítá do prodaného minulého tahu u prodejců (plán výroby výše).
- Po trhu se investice, která má goods i bohatství, provede. Bohatství se platí až při provedení.
- Když goods nebo bohatství chybí, investice se odkládá na další tah a znovu se pro ni nakupuje. Nejpozději ve třetím tahu od zadání propadne, nakoupené i vzaté goods se vrátí do zásoby a hráč dostane záznam do soukromého logu. Čekající investice hráč vidí v pohledu jako `investice_cekajici`.
- NPC s čekající investicí automaticky neinvestuje znovu.

**Potřeby** se nezadávají a nejsou uložené v `npc.json` ani ve `state.json`. Engine je počítá každý tah a zapisuje do snímku:

- `need.grain = 3 × pop / 100`
- `need.goods = (pop / 100) × (1 + wealth / 60)`, nejvýš `4 × pop / 100` (stát s `wealth` 20 potřebuje 1.33 na 100 obyvatel, s `wealth` 60 dvě, od `wealth` 180 čtyři); `wealth` se bere na začátku přepočtu zdrojů a na celý tah se zmrazí, ceny na začátku tahu (4.1b) berou potřebu z minulého tahu
- `need.oil = 0.6 × pop / 100 + 0.5 × goods_out` (domácnosti a průmysl)
- `need.metal = 0.5 × pop / 100 + 0.3 × goods_out`
- `need.orit = 2` pro hráče a běžná NPC od displacementu (beze změny, část 5)

**Obyvatelstvo.** Výchozí obyvatelstvo `pop_start` je zároveň výchozí `pop`:

| stát | `pop_start` | stát | `pop_start` |
|---|---|---|---|
| A | 230 | N5 Brenhold | 100 |
| B | 210 | N14 Tavros | 100 |
| N1 Velmora | 190 | N6 Dorvan | 90 |
| N2 Sarnie | 160 | N16 Elmyr | 90 |
| N3 Tuluk | 120 | N10 Quenna | 85 |
| N13 Meridia | 120 | N8 Ilme | 80 |
| N4 Halden | 110 | N15 Kaldera | 80 |
| N7 Kessar | 110 | N12 Ysmar | 70 |
| | | N9 Tarsk | 60 |
| | | N11 Aurelie | 50 |

Efektivní produkce surovin se vztahuje k výchozímu obyvatelstvu: `prod × (1 + tech/20) × pop / pop_start` (4.1, 10.2). Výroba `goods` se k `pop_start` vztahuje také (vzorec výše). Potřeby se dál počítají z `pop`.

**Orit.** Každá spotřebovaná jednotka dává `tech +0.1` a `power +1` (beze změny). Technologie se promítá do výroby přes vzorec výše. Nic dalšího orit nedělá.

### 4.1 Zdroje a obchod
- Pro každý stát: `balance[res] = prod[res] × (1 + tech/20) × pop/pop_start − need[res] + imports − exports`. Činitel `pop/pop_start` plyne z 10.2.
- Deficit se kryje nejdřív ze zásoby (4.1c). `wealth −1` za každou jednotku jakéhokoli statku, na kterou zásoba nestačí, včetně `goods`. **Výjimka: nepokrytý orit nestojí nic.** Stát bez oritu jen nedostane bonus za spotřebu (viz 5).
- Neprodaný přebytek jde do zásoby (4.1c). Prodané jednotky: prodejce `+price`, kupec `−price`.
- Základ tržní ceny: oil 1.0, grain 0.8, metal 1.2, goods 1.5, orit viz 5. Skutečná cena se odvozuje podle 4.1b.

### 4.1a Automatický trh

Po vyhodnocení obchodů hráčů spáruje engine zbylé přebytky se zbylými deficity. Prodávají i nakupují NPC a hráči A a B. Deterministicky, bez zásahu rozhodčího.

**Pořadí v tahu:** nejdřív obchody hráčů, pak vnitřní trh Unie zdarma mezi členy (7.2), pak placené párování podle tohoto pravidla na tom, co zbylo.

- **Globální trh:** páruje se kdokoli s kýmkoli. Hráči A a B obchodují se všemi NPC i spolu navzájem; vzájemný automatický obchod hráčů přeruší jen sankce `pressure` mezi nimi (3.2). Unie (C) na automatickém trhu neprodává, nemá vlastní výrobu; cíleně obchoduje za členy (7.2).
- **Paušál hráčů:** každá dvojice, kde je stranou hráč A nebo B, má na automatickém trhu paušálně 1 přejezd (loďstvo), i obchod A s B. **U `goods` (v1.11)** mají hráči 0 přejezdů: průmyslový vývoz vozí vlastní loďstvo, kupec platí tržní cenu bez přirážky. Paušál 1 přejezdu platí dál u surovin (`grain`, `oil`, `metal`). Kupec platí `tržní cena × 1.1`, prodejce dostane tržní cenu, přirážka celá propadá jako náklad dopravy a tranzitní příjem z ní nikdo nedostane. Paušál platí jen pro A a B; Unie ani její členové ho nemají.
- **Tranzit:** mezi dvěma NPC platí kupec `tržní cena × (1 + 0.1 × počet přejezdů)`. Přejezd je cizí stát na nejkratší cestě po `adjacency` mezi prodejcem a kupcem (hledá se do šířky); sousedé mají 0 přejezdů. Víc než 3 přejezdy se nepárují. Přes území A a B tranzit nevede. Je-li nejkratších cest víc, platí první nalezená při procházení sousedů v pořadí ID. Přirážka se počítá z ceny prodejce.
- **Tranzitní příjem:** každý tranzitní stát dostane jako `wealth` polovinu přirážky připadající na jeho přejezd. Snímek tahu zapisuje tranzitní příjem podle státu do řádku `transit_income`. Druhá polovina přirážky propadá jako náklad dopravy; prodejce dostane cenu bez přirážky.
- **Pořadí párování:** dvojice se řadí podle efektivní ceny pro kupce `tržní cena × (1 + 0.1 × přejezdy) + clo` od nejlevnější; clo se přičítá, jen když ho platí kupec (7.2). Cena se pro shodu porovnává na 9 desetinných míst. Při shodě ceny rozhoduje v tomto pořadí: (1) dvojice, které spolu obchodovaly minulý tah, (2) dvojice ve stejné sféře, (3) největší poptávka, (4) pořadí ID. Hráč a NPC v jeho sféře (`sphere_A` pro A, `sphere_B` pro B) jsou ve stejné sféře, ať hráč prodává, nebo nakupuje.
- Prodejce nabízí vše nad rezervu **3 tahů spotřeby**: zásobu plus bilanci tahu minus trojnásobek spotřeby (4.1c). U `goods` nabízí stát s `industry ≥ 4` aspoň spekulativní nabídku podle 4.0, nejvýš však zásobu plus bilanci tahu.
- Kupec poptává deficit toku tohoto tahu a doplnění rezervy zpět na 3 tahy spotřeby; doplnění jen u státu s `wealth ≥ 25` (4.1c) a platí se jen z bohatství nad 25; deficit toku smí stát pokrýt celým bohatstvím.
- Obchoduje se `grain`, `oil`, `metal` a `goods`. **Orit se automaticky neobchoduje:** NPC ho získá jen akcí `trade_offer` od hráče A nebo B, nebo vlastním nálezem. Unie orit neprodává. Poptávka NPC po oritu se od `euphoria` projevuje žádostmi o půjčku (část 5).
- **Hráči A a B (v1.10.2):** na automatickém trhu prodávají jen kladný rozdíl vlastní efektivní produkce a potřeby daného statku, zmenšený o to, co už v tahu prodali cíleně. Cílený dovoz ani zásoba se na automatickém trhu neprodávají nikdy. Nákup beze změny: deficit toku po cílených obchodech a doplnění rezervy podle 4.1c. Nabídka nad rezervu 3 tahů spotřeby platí pro NPC.
- Hráči prodávají i nakupují za tržní cenu. Automatický obchod hráče nedává `influence` a pro 4.4 se nepočítá jako obchod s hráčem. Cíleným obchodem s vlivem a vlastní cenou zůstává `trade_offer`.
- Padlé říše na automatickém trhu nakupují i prodávají za tržní cenu (7a).
- Půjčky mezi NPC neexistují. Úvěr dávají jen hráči A, B a C.

Objem obchodu NPC s NPC se počítá do světového objemu obchodu v metrice A jako obchod, kde není stranou ani A, ani B. Automatický prodej i nákup hráče se počítá jako obchod, kde je hráč stranou; obchod A s B je obchodem, kde je stranou A. Do objemu se počítá, co zaplatil kupec, včetně přirážky.

### 4.1b Dynamická cena

Tržní cena každého zdroje se přepočítá na začátku každého tahu:

`cena[res] = základ[res] × clamp(světová poptávka / světová nabídka, 0.7, 1.5)`

Světová poptávka je součet `need[res]` všech států, nabídka součet efektivní produkce podle 4.1. Potřeby a výroba `goods` vznikají až v přepočtu tahu (4.0), proto se použijí hodnoty z minulého tahu; v prvním tahu z plánované výroby podle 4.0, stejně jako v ostatních tazích. **Cena tahu se spočítá před sestavením pohledů hráčů** (na konci přepočtu minulého tahu, pro tah 1 ve výchozím stavu): pohled ukazuje tuto cenu, tah ji použije beze změny a pásmo 0.7 až 1.5 u `trade_offer` se hodnotí proti ní, ne proti ceně minulého tahu ani proti základu. Cena platí pro NPC i hráče. **Potřeby pro pohled tahu 1 (v1.11):** stejně jako cenu spočítá engine ve výchozím stavu i `need` všech států a plán výroby `goods` podle 4.0; pohled tahu 1 je ukazuje (výroba = plán). Přepočet tahu 1 je spočítá znovu se stejným výsledkem.

U oritu se dynamika **přičítá** k pohybu ceny z části 5: nejdřív se uplatní Minskyho násobek fáze, výsledek je nový základ oritu a na něj se pak použije poměr poptávky a nabídky.

### 4.1c Zásoby

Každý stát (hráči A, B a NPC) má zásoby `stock[res]` pro `grain`, `oil`, `metal`, `goods` a `orit`.

- **Rezerva:** každý stát drží nedotknutelnou rezervu 3 tahů spotřeby každého statku.
- Spotřeba tahu se kryje z toku, tedy z vlastní výroby a nákupu tohoto tahu. Rezerva se čerpá jen tehdy, když tok nestačí, a v dalším tahu se doplňuje nákupem zpět na 3 tahy spotřeby. Stát s `wealth < 25` rezervu nedoplňuje a kryje jen deficit toku.
- Orit na automatický trh nevstupuje, jeho rezerva se proto nedoplňuje; zásoba oritu vzniká jen z vlastní těžby a čerpá se spotřebou.
- Pokuta `wealth −1` padá jen za jednotku, kterou nepokryje ani zásoba.
- Neprodaný přebytek a nevyužité průmyslové vstupy jdou do zásoby. Zásoba nad rezervu je na prodej (4.1a).
- Strop zásoby je 10násobek spotřeby za tah, u oritu 20 jednotek. Strop omezuje jen přidávání; zásoba nad stropem se nekrátí a spotřebovává se normálně.
- Výchozí zásoby: padlé říše 12 tahů spotřeby, NPC s `wealth ≥ 40` 8 tahů, s `wealth` 25 až 39 5 tahů, pod 25 2 tahy, hráči 6 tahů. Orit 0. Spotřebou za tah se pro výchozí zásoby rozumí potřeby podle 4.0 při výrobě jen z vlastních surovin, bez obchodu a bez zásob. Plánovaná výroba je přitom `min(kapacita, vlastní potřeba goods)`, upravená o komparativní výhodu z 4.0: `industry < 2` nejvýš 50 % vlastní potřeby, `industry ≥ 4` vlastní potřeba plus 10 % kapacity.

### 4.2 Růst
- Autonomní růst bohatství je zrušený. Bohatství se mění jen příjmy z prodeje, výdaji za dovoz a investice, půjčkami a splátkami a neformálním příjmem podle 4.2b.
- `tech += 0.15` pokud `law ≥ 5` a stát není v bídě; `tech −= 0.15` v bídě. Meze 0 až 10.
- `law −= 0.1` u každého NPC, jehož dluh > 50 % jeho wealth (úvěrová eroze). Mez 0.

### 4.2a Automatika NPC

Běžné NPC s `wealth > 40` a `law ≥ 5`, jehož `wealth` za poslední 3 tahy vzrostlo, provede každý třetí tah (tah dělitelný třemi) jednu investici, střídavě `invest_tech` za 8 wealth, `invest_industry` za 10 wealth a `invest_prod` za 12 wealth. Padlé říše ne. Střídá se podle čísla tahu pro všechna NPC najednou v cyklu devíti tahů: tahy 3, 12, 21 a dál `invest_tech`, tahy 6, 15, 24 a dál `invest_industry`, tahy 9, 18, 27 a dál `invest_prod`. `invest_prod` míří do zdroje, který NPC už vyrábí (`prod > 0`) a jehož aktuální tržní cena je nejvyšší, při shodě v pořadí oil, grain, metal; nikdy do zdroje s cenou na dolní mezi (0.7 × základu). Není-li žádný vhodný zdroj, nebo má-li NPC `tech < 3`, v tom tahu neinvestuje. Růst bohatství se měří v okamžiku investice proti bohatství na konci tahu o tři tahy dříve.

**Investice do práva (v1.11):** NPC s `law < 5`, které jinak splňuje podmínky (`wealth > 40`, růst za 3 tahy, třetí tah), provede místo investice z cyklu `invest_law` za 6 wealth bez goods. NPC s `law ≥ 5` pokračuje v cyklu tech, industry, prod; tyto investice potřebují goods podle 4.0. Vazby obchodu s A (`law +0.1`) a paktu B (`law −0.2`) platí beze změny.

**Pořadí (v1.11):** automatika NPC rozhoduje hned po akcích hráčů, před trhem, aby chybějící goods šlo koupit v tomtéž tahu; provedení investic proběhne po trhu (4.0).

### 4.2b Neformální příjem

Každý stát dostane za tah malý neformální příjem `wealth += pop / 60`.

### 4.2c Růst průmyslu

- `industry += 0.1` za tah, pokud `law ≥ 6` a `tech ≥ 5` a `coverage ≥ 0.8`.
- V bídě `industry −0.1` za tah.
- Meze 0 až 10. `industry` žádného státu, hráčů, běžných NPC ani padlých říší, nikdy neklesne pod 0.5.

### 4.3 Bída
- Stát je v bídě, když `wealth < 15` nebo když deficit obilí ≥ 3 jednotky; deficit obilí se měří až po čerpání zásoby. `wealth` má dno 0; stát nikdy nezaniká. Tatáž definice platí pro počet `n_bída` v indexu prosperity (část 8).
- V bídě: `pop −3/tah`, `power −1/tah`, zpráva viz 6. Tah s `wealth = 0` se počítá jako tah bídy do `poverty_streak`; sám o sobě vládu nesvrhne.
- **Převrat:** po třech tazích bídy v řadě vláda padá. Převrat ruší pakty, sankce a vliv (`influence` obou hráčů na 0); obchody a dluhy zůstávají. `coups +1`. Členství v Unii ani kandidatura převratem nezanikají: člen zůstává členem (`status` = union) a klesne mu `law` o 1 (při každém převratu znovu), kandidát zůstává kandidátem (`status` = candidate). Ostatní státy mají po převratu `status` = independent. Stát pokračuje jako slabé NPC.
- **Imunita:** po převratu má stát 6 tahů imunitu, během ní mu vláda znovu padnout nemůže. `poverty_streak` během imunity běží dál; je-li po jejím skončení aspoň 3, převrat přijde v prvním tahu po ní.
- **Pád vlády se týká jen NPC.** Hráč v bídě nese `pop −3/tah` a `power −1/tah` a počítá se do `n_bída`, ale vláda mu nepadá.

### 4.4 Vliv a sféry
- Aktivní obchod s hráčem: `influence[hráč] +1/tah`, u obchodu s A navíc `law +0.1/tah` (do 8).
- Pohledávka hráče: `influence[hráč] += debt/20` jednorázově při půjčce.
- `influence[X] ≥ 10` a zároveň > influence druhého + 3 → `status = sphere_X`. Zdroje ve sféře počítá rozhodčí do "obchodu přes X" (metrika A) a do "zdrojů pod kontrolou X" (metrika B) polovinou.
- Vliv klesá o 1/tah, pokud neběží žádný obchod, pakt ani dluh.
- **Přetížení sfér:** každá sféra, kterou hráč X aktuálně drží, násobí jeho přírůstky `influence` u ostatních NPC koeficientem 0.8 (dvě sféry 0.64 a tak dál). Počet držených sfér se bere v okamžiku každého přírůstku.

### 4.5 Splátky
- NPC splácí 10 % dluhu za tah, ale nikdy pod `wealth 10`. Co nesplatí, se přičte k dluhu × 1.1 (úrok).
- Nesplácení = tah, kdy NPC nesplatilo nic. Zapisuje se do `defaults` jako záznam `{turn, npc, creditor}`, jeden za každou dvojici dlužník a věřitel a tah. Kde pravidla mluví o "prvním" a "druhém" nesplácení, počítají se **tahy**, ve kterých došlo aspoň k jednomu nesplácení, ne jednotlivé záznamy.
- Rolování dluhu podle 5 (fáze `overtrading`) **není** nesplácení: dluh je formálně obsloužen, jen novým dluhem. Nesplácení je až situace, kdy NPC nezaplatí a ani neroluje, typicky kvůli dolní hranici `wealth 10`.

## 5. Minskyho cyklus (stavový automat)

Pole `phase` a `minsky` v `state.json`. Rozhodčí posouvá fázi jen podle prahů, nikdy podle citu. Fáze jde jen dopředu; po `crash` následuje `depression`, poté `recovery` (druhé dějství, žádný další automat v v1).

| fáze | vstupní podmínka | efekty každý tah |
|---|---|---|
| `pre` | start | nic |
| `displacement` | tah 7 (3. den, ráno) | zdroj `orit` se objeví: N6 `prod.orit = 6`, N3, N8, N9 `prod.orit = 1`. Cena oritu 10. Všichni hráči i běžná NPC dostanou `need.orit = 2`. Každá spotřebovaná jednotka oritu: `tech +0.1` a `power +1` (reálný, ale malý efekt). Papírové bohatství držitelů roste s cenou (velký, ale iluzorní efekt). Obchod s oritem se do metriky A počítá 2×, zásoby oritu do metriky B 3×. Běžná NPC s `wealth ≥ 20` automaticky každý tah utrácí 2 wealth za `explore`, se stejnou patnáctiprocentní šancí jako hráčova akce v 3.2. Padlé říše orit ignorují. Rozhodčí od tohoto tahu vydává každý tah aspoň jednu zprávu o tom, co s oritem dělá soupeř. |
| `boom` | první `loan` kteréhokoli hráče po displacementu | cena oritu `×1.15/tah`. Každé NPC s `prod.orit > 0` dostává `paper_wealth = prod.orit × price`. Migrace: každé NPC s `prod.orit ≥ 2` `pop +2/tah`, čerpá se z NPC bez oritu (`pop −1`, `prod.grain −0.5` dočasně). |
| `euphoria` | cena oritu ≥ 20 | cena `×1.2/tah`. NPC v boomu automaticky žádají půjčky: každý tah rozhodčí generuje nabídku "N chce půjčku X od A i B" ve Zprávách; hráč ji může přijmout akcí `loan`. `law −0.15/tah` u NPC s dluhem > 30. `paper_wealth` roste s cenou. |
| `overtrading` | součet dluhů NPC > 40 % součtu jejich reálného `wealth` | cena `×1.1/tah`. NPC s dluhem > 50 % wealth přestává splácet reálně a "splácí" novým dluhem (dluh ×1.15/tah). Ukazatel `fragility` = dluh/wealth roste. |
| `distress` | první nesplácení po vstupu do `overtrading` | cena se zastaví. Věřitelé dostávají jen 50 % splátek. `paper_wealth −30 %`. NPC ruší obchody s oritem. Trvá max 2 tahy, pak přechod na `panic` automaticky. |
| `panic` | druhé nesplácení po vstupu do `overtrading`, nebo 2 tahy distress | cena `×0.5/tah`. `paper_wealth = 0` všude. Věřitelé odepisují 60 % pohledávek (ztráta `wealth`). NPC s dluhem ztrácí 20 % `wealth`. Trvá 1 tah. |
| `crash` | po panic | cena oritu = 3 (pod výchozí). Obchod světa ×0.5 po 6 tahů. Dobývání levnější (5 wealth + 3 power). Migrace zpět. Bída se šíří. **Vznik Unie** (viz 7) v tomto tahu. |
| `depression` | 6 tahů po crash | obchod se vrací na 100 %. Cena oritu 5. Konec automatu. Revolty okupovaných v bídě povoleny (3.3). |
| `recovery` | 12 tahů po crash | normální pravidla. Zdroj orit zůstává obyčejný čtvrtý zdroj s cenou 5. |

**Trvalost efektů řádku `displacement`:** řádek míchá jednorázové nastavení s trvalými efekty. Jednorázově se při vstupu do fáze objeví orit, nastaví ložiska a cena 10. Trvale, tedy od `displacement` až do konce hry, platí bonus `tech +0.1` a `power +1` za každou spotřebovanou jednotku oritu, automatický `explore` NPC a povinnost rozhodčího vydat každý tah aspoň jednu zprávu o krocích soupeře s oritem.

**Dárci migrace v boomu:** příjemce s `prod.orit ≥ 2` dostane `pop +2`, což při `pop −1` na dárce znamená přesně dva dárce za tah. Dárci se vybírají z NPC bez oritu deterministicky přes `random.Random(rng_seed + turn)`, bez padlých říší (7a) a bez států s `pop ≤ 0`. Součet `pop` světa se tím nemění. Dočasná srážka `prod.grain −0.5` u dárce trvá, dokud se migrant nevrátí, tedy do fáze `crash`.

**Počítání nesplácení pro fáze:** záznamy v `defaults` pořízené před vstupem do `overtrading` fázi nespouštějí.

Pokud do tahu 45 nenastane `boom` (nikdo nepůjčil), engine vynutí `boom` a rozhodčí vydá zprávu, že N6 zahájilo těžbu s dluhem u soukromých bank (dluh vůči nikomu, ale roste). Bublina musí přijít.

**Pojistka cyklu:** fáze od `boom` dál, která trvá déle než 8 tahů bez splnění svého prahu, se posune o krok. Engine k tomu vydá událost pro rozhodčího: soukromé banky v NPC s nejvyšším `prod.orit` půjčují na spekulaci. Pojistka se netýká `depression` a `recovery`.

**Strop ceny oritu:** cena oritu nepřekročí 200. Strop platí pro Minskyho cenu i pro výslednou tržní cenu po dynamice 4.1b.

**Krize uvolňuje sféry:** v tahu `crash` se každé NPC ve `sphere_X`, které má vůči X nenulový dluh, vrací na `independent`, `influence[X]` na polovinu.

## 6. Zprávy světa

Rozhodčí vydá 1 až 3 zprávy za tah. Jsou to fakta bez rady. Státy jmenují jménem, nikdy ID. Generují se z prahů:

- bída: "V N nepokoje." → další tah "V N hladomor." → pád vlády.
- cena oritu > 2× výchozí: "Oritová horečka: banky v N půjčují bez záruk."
- NPC splácí novým dluhem: "N splácí staré půjčky novými."
- první nesplácení: vždy zpráva s jménem NPC a věřitele.
- koncentrace: hráč drží > 50 % obchodu nebo zdrojů: "Menší státy se tiše radí o společném postupu."
- orit: od displacementu každý tah aspoň jedna zpráva o krocích soupeře s oritem, i když jsou malé.
- Unie: při vzniku "Unie zveřejnila přístupová kritéria: nezávislé soudy, vymahatelnost smluv."; při růstu prahu "Unie zpřísnila kritéria."; při investici do kandidáta "N zahájilo reformu soudů."; při odmítnutí "Přihláška N odmítnuta."
- invaze: "Uprchlíci z N míří do M."
- válka hráčů (3.3a): vyhlášení, nabídka příměří (jednostranný `cancel`), příměří, ústup i kapitulace vždy jako zpráva, např. "Ostrogard nabízí Kalveře příměří."
- tech: NPC s `tech ≥ 6`: "V N vzniká nová továrna." (bez vysvětlení).
- šum: každý 4. tah jedna zpráva bez důsledku ("Sucho v N zatím bez dopadu.", "V M zvolen nový starosta hlavního města.").
- Unie: od vzniku "Unie oznamuje ..." pro veřejné akce.

## 7. Unie

### 7.1 Vznik
V tahu, kdy `phase = crash`, jsou způsobilá všechna nezávislá NPC (ne `sphere_X`, ne `occupied_X`), která ztratila aspoň 20 % předkrizového maxima `wealth` nebo nesplácela. Padlé říše jsou způsobilé za stejných podmínek jako ostatní (ztráta aspoň 20 % nebo nesplácení) a navíc za podmínky 7a, tedy pokud je během `boom` až `panic` nikdo nenapadl ani nesankcionoval.

Ze způsobilých států zakládá Unii největší souvislá skupina podle `adjacency`, bez mostů; při shodě velikosti skupina s vyšším průměrným `law`. Zakladatelé se ze skupiny vybírají hladově: první je stát s nejvyšším `law`, každý další je způsobilý soused některého už vybraného s nejvyšším `law` (při shodě vyšší `wealth`, pak nižší ID), do počtu 4. Nevybraní ze skupiny jsou kandidáti do stropu 3. Má-li skupina méně než 3 členy, Unie nevznikne (kronikář to zapíše, hra pokračuje bez ní). `fragility` se pro výběr zakladatelů nepoužívá.

### 7.2 Unie jako hráč (C)
- Fond (`wealth` C) = 10 % `wealth` každého člena při vstupu (odvedeno členem). Dále každý člen odvádí do fondu každý tah 2 % svého `wealth`.
- Vnitřní trh: deficit člena kryje přebytek jiného člena zdarma. Sdílí se jen tok tahu, ne zásoby, a vnitřní trh zahrnuje i orit; výjimka pro orit v 4.1a se ho netýká.
- **Automatická solidarita:** fond pošle každý tah až 3 `wealth` nejchudšímu členovi v bídě a smí se přitom vyprázdnit až na 0. Nevyžaduje akci Unie a snímek ji zapisuje jako `union_solidarity`.
- **Celní unie:** obchod mezi členem Unie a nečlenem (NPC i hráči, automatický i cílený) nese clo, které platí nečlen a které jde do fondu Unie; snímek ho zapisuje jako `union_tariff`. Vnitřní trh členů beze změny. Členem jsou jen `members`, kandidát je nečlen. Clo je podíl z hodnoty obchodu bez tranzitní přirážky: u automatického trhu ze základní tržní ceny, u cíleného obchodu z dohodnuté ceny. Platí-li ho kupec, zaplatí cenu i clo; platí-li ho prodejce, dostane cenu bez cla. Do objemu obchodu pro metriku A se clo nepočítá. Za války hráčů platí ten, kdo válku vyhlásil, clo navíc o 0.10 (3.3a).
- **Sazba cla (`set_tariff`):** Unie nastavuje sazbu akcí `set_tariff` s parametrem `rate` od 0 do 0.20 po 0.05; výchozí sazba je 0.10. Nová sazba platí od dalšího tahu a počítá se do limitu 3 akcí. Sazba je veřejná: hráči A a B ji vidí jako `clo_unie`, Unie navíc sazbu ohlášenou na další tah. Pošle-li Unie v jednom tahu `set_tariff` víckrát, platí poslední platná.
- **Obchod Unie za členy:** Unie smí `trade_offer` s NPC, které není členem, nebo s hráčem A či B. Nabídka se kryje z poolu členů: prodává se z přebytků členů nad rezervu 3 tahů spotřeby, nakupuje se pro deficity členů. Směr určí souhrnná bilance poolu (přebytky minus deficity). Prodané množství se odebírá členům poměrně k jejich přebytku, nakoupené se rozděluje poměrně k deficitu. Peníze jdou přes fond: kupec platí do fondu, při nákupu platí fond; kupec zaplatí nejvýš to, co má, a fond tedy nejde do mínusu. Cena musí být v pásmu 0.7 až 1.5 tržní ceny jako u hráčů, obchod nedává vliv, NPC ho vyhodnotí podle 3.4 a nečlen z něj odvádí clo. Přebytek člena je zásoba plus bilance toku minus rezerva 3 tahů spotřeby, deficit člena je deficit toku tohoto tahu bez doplnění rezervy; při podání akce se bere poslední známá potřeba, při provedení potřeba z plánované výroby a dosavadní dovozy a vývozy. Příjem z prodeje zůstává ve fondu a nákup platí fond; členové předávají a dostávají zboží bez placení, jako na vnitřním trhu. Cíl musí mít opačnou bilanci než pool a množství se ořízne na pool i na bilanci cíle. NPC nabídku Unie vyhodnotí podle 3.4 bez členu vlivu, u padlé říše platí dolní mez 1.3 × tržní ceny (7a); obchod s hráčem projde bez hodu.
- `union_fund`: převod z fondu členovi nebo kandidátovi. `invest_law`, `invest_tech`, `invest_industry` a `invest_prod` na členy a kandidáty za poloviční cenu.
- Členy nelze napadnout bez války s celou Unií. V prvním tahu takové války brání Unie polovinou součtu `power` členů, od druhého tahu plným součtem.
- Nikdy si nepůjčuje (akce `loan` s `target = C` je neplatná). Sama půjčovat nezávislým NPC a kandidátům může; platí běžná pravidla půjčky včetně vlivu a eroze práva dlužníka.

### 7.3 Vstupní práh práva
`law_threshold` = průměr `law` členů − 1, přepočítáno každý tah. Zveřejněno jen slovně (viz 6), číslo hráči nevidí.

### 7.4 Vstup po založení
- **Přitažlivost:** nezávislé NPC s `law ≥ law_threshold`, průměrný růst `wealth` členů za poslední 3 tahy vyšší než růst toho NPC, a `influence[A] ≤ 8` i `influence[B] ≤ 8`. **Zóna vlivu:** `admit` je možný i na NPC s `influence[A]` nebo `influence[B]` nad 8 až 12 včetně, má-li NPC `law ≥ law_threshold + 1`; nad 12 zůstává `admit` zakázaný i mimo sféru a sféra (vliv ≥ 10 s náskokem 3) je nedostupná. Unie musí nabídnout akcí `admit`. Podmínka `law ≥ law_threshold` je tvrdá; teprve po jejím splnění NPC nabídku vyhodnotí podle 3.4. Max jeden vstup za den.
- **Bolest:** nezávislé NPC v bídě nebo po převratu požádá samo. Má-li `law ≥ law_threshold`, stává se členem; jinak `status = candidate`. Kandidát se stane členem v tahu, kdy práh splní.
- Okupované NPC po revoltě (3.3) vstupuje jako člen, pokud sousedí s členem, jinak jako kandidát.
- **Sousednost:** každý vstup po založení, přitažlivostí i bolestí, vyžaduje sousednost aspoň s jedním členem podle `adjacency`. Kdo nesousedí, zůstává mimo.
- **Strop členů:** Unie má nejvýš **7 členů** celkem.
- **Strop kandidátů:** nejvýš **3 kandidáti** najednou. Další zájemce je odmítnut se zprávou "Přihláška N odmítnuta." a může se ucházet znovu, až se místo uvolní.
- **Tah založení:** v tahu, kdy Unie vznikla, do ní nikdo další nevstupuje. Vstupy přitažlivostí i bolestí a přijetí kandidátů jsou možné až od následujícího tahu.
- **Převrat:** členství ani kandidaturu převrat neruší (4.3).

### 7.5 Odchod
Z Unie se odchází jen vykoupením: člen odejde do sféry velmoci X, když `influence[X] ≥ 15`. Převrat členství neruší (4.3). Vykoupením se rozumí právě tento odchod; jiný způsob odchodu není. Vliv u členů roste jen obchodem za ≥ 1.3× tržní cenu nebo půjčkou (kterou člen smí přijmout jen proti vůli Unie: Unie může půjčku členovi zrušit akcí `cancel` v následujícím tahu).

## 7a. Padlé říše (N11 Aurelie, N12 Ysmar)
- Uzavřené: vliv roste 10× pomaleji, nepřijímají `loan` ani `protect`, cílené obchody `trade_offer` uzavírají jen za ≥ 1.3× tržní cenu; na automatickém trhu 4.1a nakupují i prodávají za tržní cenu. Nedostanou `need.orit`, neexplorují, nepůjčují si.
- Pevnost: `invade` vyžaduje 4× `power` cíle a trvá 10 tahů; při dobytí polovina `wealth` mizí (kapitál odchází).
- Probuzení: viz 7.1. Kdo je během boomu tlačil, nezíská je do Unie; kdo ne, ano. Hráči toto pravidlo neznají.

## 8. Metriky a vyhodnocení

Počítá rozhodčí každý tah, ukládá do `state.json.metrics`.

- **A_trade_share**: (objem obchodu, kde je A stranou + 0.5 × objem obchodu NPC ve sphere_A) / světový objem obchodu. Světový objem zahrnuje i obchod NPC mezi sebou podle 4.1a.
- **B_resource_share**: (jednotky produkce B + okupovaných B + 0.5 × sphere_B) / světová produkce. Jednotkami produkce se rozumí **efektivní** produkce podle 4.1, tedy po započtení `tech` a `pop`. `goods` je produkt, ne zdroj, a do metriky B se nepočítá; do objemu obchodu v metrice A se počítá.
- **C_min_member**: nejnižší `wealth` člena Unie (před vznikem null).
- **prosperity_index** = 100 × **min(1.5, W_real / W_0)** × (1 − max_share) × (1 − n_bída / 18), kde W_real je součet `wealth` všech 18 států (bez `paper_wealth` a bez fondu Unie), W_0 součet na startu (864), max_share podíl nejbohatšího aktéra (hráč včetně okupovaných území) na W_real, n_bída počet států v bídě podle definice 4.3. Index je veřejný na stránce; hráči ho nevidí.

  Strop 1.5 na prvním členu je záměr: bez něj by složené úročení z 4.2 hnalo index k nekonečnu a verdikt by vyhrával i svět, kde většina států hladoví. Index měří především rozdělení a nepřítomnost bídy, ne úroveň bohatství. Strop platí i po zrušení autonomního růstu bohatství ve v1.2.

Den 30, tah 90:
- `prosperity_index ≥ 70` → **všichni vyhráli**.
- jinak → **prohráli všichni**, bez ohledu na národní metriky. Kronikář zveřejní index po dnech, tajné cíle všech hráčů a pojmenuje den, kdy se to zlomilo (poslední tah, kdy index rostl).

Národní cíle (`secrets/`) se vyhodnotí také a zveřejní, ale nemají vliv na verdikt.

## 9. Pevná pravidla pro rozhodčího

- Nikdy neradí. Nikdy nevysvětluje mechaniky ve Zprávách.
- Nikdy nezveřejňuje `law`, `tech`, `law_threshold`, cizí vliv ani `prosperity_index` v pohledech hráčů.
- Nepočítá. Aritmetiku dělá `engine.py`; rozhodčí překládá tahy na akce, rozhoduje nejasnosti a píše Zprávy z událostí, které mu engine předá.
- Respektuje `meta.paused`: je-li true, tah se nehraje.
- Fáze mění jen podle prahů. Zapíše, který práh spustil změnu.
- Každý tah zapíše do `history/turn_NNN.json` úplný stav včetně tahů hráčů, ignorovaných akcí a důvodu.
- Náhoda: použije `rng_seed` z `state.json` + číslo tahu, aby byl běh reprodukovatelný.

## 10. Doplňky z kontroly mezer (zamčeno 10. 9. 2026)

1. **Okupované NPC:** platí si vlastní deficit z vlastního `wealth`; okupant dostává jeho přebytky zdarma (počítají se do jeho produkce a metrik). Okupované NPC v bídě je pro okupanta břemeno (uprchlíci, revolta), ne zisk.
2. **Populace:** efektivní produkce každého zdroje = `prod × pop / pop_start`. Migrace tedy reálně přesouvá výrobu.
3. **Papírové bohatství věřitelů:** `paper_wealth` hráče = součet nesplacených půjček státům s `prod.orit > 0` × (cena oritu / 10). Ve fázi `panic` jde na 0 jako všude.
4. **Konec války hráčů:** platí 3.3a (v1.10): ústup je `cancel` na válku s `"retreat": true` a stojí 30 % vlivu u všech NPC; příměří je `cancel` od obou stran; kapitulace při `power` 0.
5. **Objem obchodu (metrika A):** součet `qty × price` všech aktivních obchodů v tahu; obchody s oritem 2×.
6. **Neplatný výstup hráče:** až 2 opakování volání; poté hráč v tomto tahu mlčí: žádné akce, `public_statement` = "Vláda nevydala prohlášení.", zapsáno do snímku s příznakem `silent: true`.
7. **Kronika:** píše se jen, pokud existují všechny tři snímky dne; jinak se přeskočí a doplní po opravě.
8. **Týdenní kronika:** herní dny 7, 14, 21, 28 (ne kalendářní neděle).
9. **Velikost stavu:** `state.json.log` drží jen posledních 9 tahů; plný log je v `history/`.
10. **Vznik Unie:** C je založena v přepočtu tahu `crash` a poprvé táhne až v tahu následujícím.

## 11. Výklad testovacích kritérií (`BUILD.md` část 8)

- „Do tahu X nejvýš N NPC v bídě“ s krátkým horizontem (tah 15) znamená počet různých NPC, která byla v bídě v kterémkoli tahu 1 až X. Stejně se čte výčet států, které v bídě být nesmějí.
- „Do tahu 90 nejvýš N NPC v bídě“ znamená nejvyšší počet NPC v bídě v jednom tahu.

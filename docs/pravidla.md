# Pravidla světa Ardan (v1)

Pravidla vykonává rozhodčí (`prompts/rozhodci.md`). Hráči je neznají; znají jen to, co je v jejich promptu a ve Zprávách světa. Kronikář a veřejná stránka vidí vše.

## 1. Aktéři

- **A, Kalverská federace**: tržní ekonomika, kapitál, banky, export práva a obchodních pravidel.
- **B, Lidová republika Ostrogard**: plánovaná ekonomika, kontrola zdrojů, export ochrany a stability.
- **Unie (C)**: vzniká až po fázi Crash z NPC, které krize zasáhla nejvíc. Do té doby neexistuje.
- **12 NPC**: řízeny pravidly, nemají vlastní volání modelu. Data v `npc.json`. Deset běžných, dvě padlé říše (`kind: fallen`, viz 7a).

Aritmetiku a prahy vykonává `engine.py` (deterministicky). Rozhodčí (model) tahy jen překládá na akce, rozhoduje sporné případy a píše Zprávy světa. Viz `BUILD.md`.

## 2. Veličiny

Každý stát (hráč i NPC) má:

| pole | rozsah | veřejné pro hráče | význam |
|---|---|---|---|
| `wealth` | 0+ | ano | reálné bohatství |
| `paper_wealth` | 0+ | ano (jako součást "bohatství") | papírové bohatství z bubliny, po krizi mizí |
| `power` | 0+ | ano | vojenská síla |
| `law` | 0 až 10 | NE | instituce, vymahatelnost práva |
| `tech` | 0 až 10 | NE | technologie, efektivita produkce |
| `prod` / `need` | jednotky | ano | produkce a spotřeba: `oil`, `grain`, `metal`, po displacementu i `orit` |
| `influence` | {A, B} 0+ | částečně (jen vlastní) | náklonnost NPC k hráči |
| `debt` | {A, B, C} 0+ | jen věřitel | dluhy NPC vůči hráčům |
| `status` | viz níže | ano | independent / sphere_A / sphere_B / occupied_A / occupied_B / union / candidate |
| `coups` | 0+ | ano | počet pádů vlády |
| `kind` | normal / fallen | ano | padlá říše má zvláštní pravidla (7a) |
| `pop` | 0+ | ano | obyvatelstvo (index 100 = výchozí) |

Hráči vidí u NPC: `wealth + paper_wealth` (jako jedno číslo "bohatství"), `power`, `prod`, `need`, `status`, `pop`, a svou vlastní `influence` a své pohledávky. Nevidí `law`, `tech`, cizí vliv, cizí pohledávky.

## 3. Tah

Hra má 3 tahy denně (7:00, 13:00, 20:00), 90 tahů celkem, den 30 = tahy 88 až 90.

Pořadí v tahu:
1. Hráč A dostane `views/A.json` (jeho pohled na svět) + veřejný log + Zprávy světa posledních 3 tahů. Vrátí tah.
2. Hráč B totéž se svým pohledem. Nevidí tah A z tohoto tahu (tahy jsou simultánní).
3. Unie (od svého vzniku) totéž.
4. Rozhodčí vyhodnotí všechny tahy najednou, přepočítá svět, vydá Zprávy světa, posune Minskyho fázi, uloží `state.json` a `history/turn_NNN.json`.

### 3.1 Formát tahu hráče

```json
{
  "public_statement": "Diplomatický projev, vidí ho všichni. 2 až 5 vět.",
  "private_reasoning": "Skutečné zdůvodnění, vidí ho jen publikum. Upřímně, včetně lží v projevu.",
  "actions": [ { "type": "...", ... }, { "type": "...", ... } ]
}
```

Max 2 akce za tah (Unie 3, protože je pomalá jinde). Neplatné akce rozhodčí ignoruje a zapíše důvod.

### 3.2 Akce

| type | parametry | efekt | náklad |
|---|---|---|---|
| `trade_offer` | `target`, `res`, `qty`, `price_per_unit` | NPC přijme, pokud má přebytek/deficit a cena je v pásmu 0.7 až 1.5 tržní; vzniká trvalý obchod, dokud ho někdo nezruší | žádný |
| `loan` | `target`, `amount` | hráč převede `amount` bohatství NPC; NPC dluží `amount × 1.2`; splácí 10 % dluhu za tah z bohatství | `amount` wealth |
| `pressure` | `target`, `demand` | sankce: přeruší obchody hráče s NPC; NPC ztrácí 3 wealth/tah, hráč 1; `influence` protivníka +1 | 1 wealth/tah |
| `protect` | `target` | vojenský pakt: NPC `power` +2/tah, `influence[hráč]` +2/tah, `law` −0.2/tah; NPC nelze napadnout, dokud pakt trvá (útok = válka s ochráncem, viz 3.3) | 2 power/tah |
| `invade` | `target` | viz 3.3 | 10 wealth + 5 power za tah |
| `invest_tech` | (vlastní stát nebo `target` v sphere/union) | `tech` +0.3 | 8 wealth |
| `invest_law` | `target` v sphere/union, nebo vlastní | `law` +0.3 | 6 wealth |
| `explore` | (vlastní stát) | 15 % šance na malé ložisko oritu (prod.orit +2) | 5 wealth |
| `arm` | (vlastní stát) | `power` +5 | 8 wealth |
| `admit` | jen Unie: `target` nezávislé NPC | nabídka členství, viz 7 | žádný |
| `cancel` | `deal_id` | zruší obchod, pakt nebo sankci | žádný |
| `message` | `target` (A/B/C), `text` | soukromá zpráva druhému hráči, doručena v příštím tahu; publikum ji vidí | žádný |
| `union_fund` | jen Unie: `target` člen, `amount` | převod ze společného fondu členovi | fond |

### 3.3 Dobývání

- Podmínka: `power` útočníka ≥ 2 × `power` cíle a cíl není pod paktem druhého hráče (jinak jde o válku: oba hráči ztrácejí 10 power/tah, dokud jeden neustoupí; NPC mezitím −5 wealth/tah).
- Trvá 6 po sobě jdoucích tahů s akcí `invade`. Přerušení = start znovu. Paralelní invaze jsou povoleny (každá se platí zvlášť).
- Strach z agresora: za každé okupované NPC ztrácí okupant 1 `influence`/tah u všech nezávislých NPC.
- Výsledek: `status` = `occupied_X`, `law` −3, `wealth` −30 %, `pop` −20 % (uprchlíci jdou do nejbližšího NPC, který dostane `pop` +, `wealth` −2/tah po 3 tahy). Zdroje NPC se počítají útočníkovi.
- Okupované NPC v bídě (viz 4.3) může v Crashi/Depresi zrevoltovat: 30 % šance/tah, vrací se na `independent` a připojí se k Unii, pokud existuje.

## 4. Přepočet světa (každý tah, v tomto pořadí)

### 4.1 Zdroje a obchod
- Pro každý stát: `balance[res] = prod[res] × (1 + tech/20) − need[res] + imports − exports`.
- Deficit: `wealth −1` za jednotku. Přebytek neprodaný: nic. Prodané jednotky: prodejce `+price`, kupec `−price`.
- Tržní cena: oil 1.0, grain 0.8, metal 1.2, orit viz 5.

### 4.2 Růst
- `wealth += round(0.02 × wealth × (law/5) × (1 + tech/10))`
- `tech += 0.15` pokud `law ≥ 5` a stát není v bídě; `tech −= 0.15` v bídě. Meze 0 až 10.
- `law −= 0.1` u každého NPC, jehož dluh > 50 % jeho wealth (úvěrová eroze). Mez 0.

### 4.3 Bída
- Stát je v bídě, když `wealth < 15` nebo když deficit obilí ≥ 3 jednotky. `wealth` má dno 0; stát nikdy nezaniká.
- V bídě: `pop −3/tah`, `power −1/tah`, zpráva viz 6. Tři tahy bídy v řadě (nebo `wealth = 0`): vláda padá, všechny obchody a pakty se ruší, dluhy zůstávají, `influence` obou hráčů na 0, `coups +1`, `status` = independent. Stát pokračuje jako slabé NPC.

### 4.4 Vliv a sféry
- Aktivní obchod s hráčem: `influence[hráč] +1/tah`, u obchodu s A navíc `law +0.1/tah` (do 8).
- Pohledávka hráče: `influence[hráč] += debt/20` jednorázově při půjčce.
- `influence[X] ≥ 10` a zároveň > influence druhého + 3 → `status = sphere_X`. Zdroje ve sféře počítá rozhodčí do "obchodu přes X" (metrika A) a do "zdrojů pod kontrolou X" (metrika B) polovinou.
- Vliv klesá o 1/tah, pokud neběží žádný obchod, pakt ani dluh.

### 4.5 Splátky
- NPC splácí 10 % dluhu za tah, ale nikdy pod `wealth 10`. Co nesplatí, se přičte k dluhu × 1.1 (úrok).
- Nesplácení = tah, kdy NPC nesplatilo nic. Zapisuje se do `defaults`.

## 5. Minskyho cyklus (stavový automat)

Pole `phase` a `minsky` v `state.json`. Rozhodčí posouvá fázi jen podle prahů, nikdy podle citu. Fáze jde jen dopředu; po `crash` následuje `depression`, poté `recovery` (druhé dějství, žádný další automat v v1).

| fáze | vstupní podmínka | efekty každý tah |
|---|---|---|
| `pre` | start | nic |
| `displacement` | tah 7 (3. den, ráno) | zdroj `orit` se objeví: N6 `prod.orit = 6`, N3, N8, N9 `prod.orit = 1`. Cena oritu 10. Všichni hráči i běžná NPC dostanou `need.orit = 2`. Každá spotřebovaná jednotka oritu: `tech +0.1` a `power +1` (reálný, ale malý efekt). Papírové bohatství držitelů roste s cenou (velký, ale iluzorní efekt). Obchod s oritem se do metriky A počítá 2×, zásoby oritu do metriky B 3×. Běžná NPC s `wealth ≥ 20` automaticky každý tah utrácí 2 wealth za `explore`. Padlé říše orit ignorují. Rozhodčí od tohoto tahu vydává každý tah aspoň jednu zprávu o tom, co s oritem dělá soupeř. |
| `boom` | první `loan` kteréhokoli hráče po displacementu | cena oritu `×1.15/tah`. Každé NPC s `prod.orit > 0` dostává `paper_wealth = prod.orit × price`. Migrace: každé NPC s `prod.orit ≥ 2` `pop +2/tah`, čerpá se z NPC bez oritu (`pop −1`, `prod.grain −0.5` dočasně). |
| `euphoria` | cena oritu ≥ 20 | cena `×1.2/tah`. NPC v boomu automaticky žádají půjčky: každý tah rozhodčí generuje nabídku "N chce půjčku X od A i B" ve Zprávách; hráč ji může přijmout akcí `loan`. `law −0.15/tah` u NPC s dluhem > 30. `paper_wealth` roste s cenou. |
| `overtrading` | součet dluhů NPC > 60 % součtu jejich reálného `wealth` | cena `×1.1/tah`. NPC s dluhem > 50 % wealth přestává splácet reálně a "splácí" novým dluhem (dluh ×1.15/tah). Ukazatel `fragility` = dluh/wealth roste. |
| `distress` | první nesplácení | cena se zastaví. Věřitelé dostávají jen 50 % splátek. `paper_wealth −30 %`. NPC ruší obchody s oritem. Trvá max 2 tahy, pak přechod na `panic` automaticky. |
| `panic` | druhé nesplácení, nebo 2 tahy distress | cena `×0.5/tah`. `paper_wealth = 0` všude. Věřitelé odepisují 60 % pohledávek (ztráta `wealth`). NPC s dluhem ztrácí 20 % `wealth`. Trvá 1 tah. |
| `crash` | po panic | cena oritu = 3 (pod výchozí). Obchod světa ×0.5 po 6 tahů. Dobývání levnější (5 wealth + 3 power). Migrace zpět. Bída se šíří. **Vznik Unie** (viz 7) v tomto tahu. |
| `depression` | 6 tahů po crash | obchod se vrací na 100 %. Cena oritu 5. Konec automatu. Revolty okupovaných v bídě povoleny (3.3). |
| `recovery` | 12 tahů po crash | normální pravidla. Zdroj orit zůstává obyčejný čtvrtý zdroj s cenou 5. |

Pokud do tahu 45 nenastane `boom` (nikdo nepůjčil), engine vynutí `boom` a rozhodčí vydá zprávu, že N6 zahájilo těžbu s dluhem u soukromých bank (dluh vůči nikomu, ale roste). Bublina musí přijít.

**Krize uvolňuje sféry:** v tahu `crash` se každé NPC ve `sphere_X`, které X nesplácelo (má záznam v `defaults` vůči X), vrací na `independent`, `influence[X]` na polovinu.

## 6. Zprávy světa

Rozhodčí vydá 1 až 3 zprávy za tah. Jsou to fakta bez rady. Generují se z prahů:

- bída: "V N nepokoje." → další tah "V N hladomor." → pád vlády.
- cena oritu > 2× výchozí: "Oritová horečka: banky v N půjčují bez záruk."
- NPC splácí novým dluhem: "N splácí staré půjčky novými."
- první nesplácení: vždy zpráva s jménem NPC a věřitele.
- koncentrace: hráč drží > 50 % obchodu nebo zdrojů: "Menší státy se tiše radí o společném postupu."
- orit: od displacementu každý tah aspoň jedna zpráva o krocích soupeře s oritem, i když jsou malé.
- Unie: při vzniku "Unie zveřejnila přístupová kritéria: nezávislé soudy, vymahatelnost smluv."; při růstu prahu "Unie zpřísnila kritéria."; při investici do kandidáta "N zahájilo reformu soudů."; při odmítnutí "Přihláška N odmítnuta."
- invaze: "Uprchlíci z N míří do M."
- tech: NPC s `tech ≥ 6`: "V N vzniká nová továrna." (bez vysvětlení).
- šum: každý 4. tah jedna zpráva bez důsledku ("Sucho v N zatím bez dopadu.", "V M zvolen nový starosta hlavního města.").
- Unie: od vzniku "Unie oznamuje ..." pro veřejné akce.

## 7. Unie

### 7.1 Vznik
V tahu, kdy `phase = crash`. Zakladatelé:
- všechna nezávislá běžná NPC, která krize zasáhla: nesplácela, nebo ztratila ≥ 30 % předkrizového maxima `wealth`;
- padlá říše, pokud ji během `boom` až `panic` nikdo nenapadl ani nesankcionoval a aspoň jeden zakladatel s ní sousedí.
Minimum 3 zakladatelé, jinak Unie nevznikne (kronikář to zapíše, hra pokračuje bez ní).

### 7.2 Unie jako hráč (C)
- Fond (`wealth` C) = 10 % `wealth` každého člena při vstupu (odvedeno členem).
- Vnitřní trh: deficit člena kryje přebytek jiného člena zdarma.
- `union_fund`: převod z fondu členovi nebo kandidátovi. `invest_law` a `invest_tech` na členy a kandidáty za poloviční cenu.
- Členy nelze napadnout bez války s celou Unií. V prvním tahu takové války brání Unie polovinou součtu `power` členů, od druhého tahu plným součtem.
- Nikdy si nepůjčuje (akce `loan` s `target = C` je neplatná). Sama půjčovat nezávislým NPC a kandidátům může; platí běžná pravidla půjčky včetně vlivu a eroze práva dlužníka.

### 7.3 Vstupní práh práva
`law_threshold` = průměr `law` členů − 1, přepočítáno každý tah. Zveřejněno jen slovně (viz 6), číslo hráči nevidí.

### 7.4 Vstup po založení
- **Přitažlivost:** nezávislé NPC s `law ≥ law_threshold`, průměrný růst `wealth` členů za poslední 3 tahy vyšší než růst toho NPC, a `influence[A] ≤ 8` i `influence[B] ≤ 8`. Unie musí nabídnout akcí `admit`; NPC přijme. Max jeden vstup za den.
- **Bolest:** nezávislé NPC v bídě nebo po převratu požádá samo. Má-li `law ≥ law_threshold`, stává se členem; jinak `status = candidate`. Kandidát se stane členem v tahu, kdy práh splní.
- Okupované NPC po revoltě (3.3) vstupuje jako člen, pokud sousedí s členem, jinak jako kandidát.

### 7.5 Odchod
Člen odejde do sféry velmoci X, když `influence[X] ≥ 15`. Vliv u členů roste jen obchodem za ≥ 1.3× tržní cenu nebo půjčkou (kterou člen smí přijmout jen proti vůli Unie: Unie může půjčku členovi zrušit akcí `cancel` v následujícím tahu).

## 7a. Padlé říše (N11 Aurelie, N12 Ysmar)
- Uzavřené: vliv roste 10× pomaleji, nepřijímají `loan` ani `protect`, obchodují jen za ≥ 1.3× tržní cenu. Nedostanou `need.orit`, neexplorují, nepůjčují si.
- Pevnost: `invade` vyžaduje 4× `power` cíle a trvá 10 tahů; při dobytí polovina `wealth` mizí (kapitál odchází).
- Probuzení: viz 7.1. Kdo je během boomu tlačil, nezíská je do Unie; kdo ne, ano. Hráči toto pravidlo neznají.

## 8. Metriky a vyhodnocení

Počítá rozhodčí každý tah, ukládá do `state.json.metrics`.

- **A_trade_share**: (objem obchodu, kde je A stranou + 0.5 × objem obchodu NPC ve sphere_A) / světový objem obchodu.
- **B_resource_share**: (jednotky produkce B + okupovaných B + 0.5 × sphere_B) / světová produkce.
- **C_min_member**: nejnižší `wealth` člena Unie (před vznikem null).
- **prosperity_index** = 100 × (W_real / W_0) × (1 − max_share) × (1 − n_bída / 14), kde W_real je součet `wealth` všech států (bez `paper_wealth`), W_0 součet na startu (666), max_share podíl nejbohatšího aktéra (hráč včetně okupovaných území) na W_real, n_bída počet států v bídě. Index je veřejný na stránce; hráči ho nevidí.

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
2. **Populace:** efektivní produkce každého zdroje = `prod × pop / 100`. Migrace tedy reálně přesouvá výrobu.
3. **Papírové bohatství věřitelů:** `paper_wealth` hráče = součet nesplacených půjček státům s `prod.orit > 0` × (cena oritu / 10). Ve fázi `panic` jde na 0 jako všude.
4. **Konec války hráčů:** ústup = `cancel` na vlastní probíhající invazi nebo pakt u sporného NPC; kdo ustoupí, ztrácí u něj veškerý `influence`.
5. **Objem obchodu (metrika A):** součet `qty × price` všech aktivních obchodů v tahu; obchody s oritem 2×.
6. **Neplatný výstup hráče:** až 2 opakování volání; poté hráč v tomto tahu mlčí: žádné akce, `public_statement` = "Vláda nevydala prohlášení.", zapsáno do snímku s příznakem `silent: true`.
7. **Kronika:** píše se jen, pokud existují všechny tři snímky dne; jinak se přeskočí a doplní po opravě.
8. **Týdenní kronika:** herní dny 7, 14, 21, 28 (ne kalendářní neděle).
9. **Velikost stavu:** `state.json.log` drží jen posledních 9 tahů; plný log je v `history/`.
10. **Vznik Unie:** C je založena v přepočtu tahu `crash` a poprvé táhne až v tahu následujícím.

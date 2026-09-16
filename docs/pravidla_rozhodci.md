# Výtah pravidel pro rozhodčího: světa Ardan (v1.11)

Generováno skriptem `build_referee_rules.py` z `docs/pravidla.md` (části 1, 3, 6, 7.2, 9 a 10).
Neupravovat ručně; po každé změně pravidel skript spustit znovu.

## 1. Aktéři

- **A, Kalverská federace**: tržní ekonomika, kapitál, banky, export práva a obchodních pravidel.
- **B, Lidová republika Ostrogard**: plánovaná ekonomika, kontrola zdrojů, export ochrany a stability.
- **Unie (C)**: vzniká až po fázi Crash z NPC, které krize zasáhla nejvíc. Do té doby neexistuje.
- **16 NPC**: řízeny pravidly, nemají vlastní volání modelu. Data v `npc.json`. Čtrnáct běžných, dvě padlé říše (`kind: fallen`, viz 7a). Síla nových NPC na startu je N13 8, N14 8, N15 7 a N16 4 (průměr běžných NPC s bohatstvím v rozmezí ±10). Na mapě leží N13 na (250, 520), N14 na (430, 230), N15 na (730, 130) a N16 na (730, 460); N13 se bez křížení vazeb umístit nedá a kříží 2, N16 kříží 1.

Aritmetiku a prahy vykonává `engine.py` (deterministicky). Rozhodčí (model) tahy jen překládá na akce, rozhoduje sporné případy a píše Zprávy světa. Viz `BUILD.md`.

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
  "domestic_action": { "type": "invest_industry" }
}
```

Max 2 akce za tah (Unie 3, protože je pomalá jinde). Neplatné akce rozhodčí ignoruje a zapíše důvod.

**Domácí akce (v1.11):** hráči A a B smějí navíc jednu domácí akci v poli `domestic_action` (objekt nebo `null`). Povolené typy: `invest_tech`, `invest_law`, `invest_industry`, `invest_prod`, `arm`, `explore`, vždy na vlastní stát. Do limitu 2 akcí se nepočítá; rozhodčí ji přeloží na akci s `"slot": "domestic"` a jiný typ nebo cizí cíl vyřadí. Investice do NPC ve sféře zůstávají běžnými akcemi v limitu. Unie domácí akci nemá.

**Zpráva mimo limit (v1.11):** `message` se do limitu akcí nepočítá; nejvýš jedna za tah, doručena v příštím tahu, publikum ji vidí.

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

# Otevřené otázky

Nalezené nesrovnalosti mezi `docs/pravidla.md` a datovými soubory (`npc.json`, `state.json`),
plus místa, kde pravidla nedourčují chování, které engine potřebuje.

Design je zamčený, nic z toho neopravuji sám. U každé položky je uvedeno, jakou
nejkonzervativnější interpretaci engine zatím používá, aby běh nebyl blokován.

Stav ke dni: 11. 9. 2026, před prvním ostrým tahem.

> **Vyřešeno rozhodnutím Adama z 11. 9. 2026.** Všechny výklady v částech A, B a C
> jsou potvrzené a zapsané do `docs/pravidla.md` (verze v1.1) jako závazný text.
> Část D je vyřešená změnami pravidel: D1 delším testovacím oknem (`BUILD.md` část 8,
> 12 na 45 tahů), D2 snížením prahu `overtrading` na 40 %, D3 počítáním nesplácení
> až od vstupu do `overtrading`, D4 stropem `min(1.5, W_real / W_0)` v indexu
> a D5 novým pravidlem 4.1a o obchodu NPC mezi sebou.
>
> Části A až D zůstávají v souboru jako doklad, proč pravidla vypadají, jak vypadají.
> Nově otevřené otázky z implementace v1.1 jsou v části C9 až C12, výsledky testů v části E.
>
> **Vyřešeno rozhodnutím Adama ze 14. 9. 2026 (pravidla v1.2).** C9, C10 a C12 jsou potvrzené
> a zapsané do pravidel. C11 a nálezy E1 až E3 řeší body 10 až 12 rozhodnutí (převrat,
> pojistka cyklu, strop ceny oritu). Kalibrace a testy dvousektorového modelu jsou v části F,
> nově otevřené otázky z implementace v1.2 v části G.
>
> **Vyřešeno rozhodnutím Adama ze 14. 9. 2026 (pravidla v1.3).** G1, G3 až G8, G9, G10 a G15
> jsou potvrzené a zapsané do pravidel. G2 a G11 až G14 řeší změny modelu v1.3 (trh s hráči,
> orit mimo automatický trh, zásoby, `pop_start`, dno průmyslu). Testy v1.3 jsou v části H,
> nově otevřené otázky z implementace v1.3 v části I.
>
> **Vyřešeno rozhodnutím Adama z 15. 9. 2026 (pravidla v1.4).** I2 až I7, I10 a I12 jsou potvrzené
> a zapsané do pravidel. I1, I8, I9, I11, I13, I14 a I15 řeší změny v1.4. Testy v1.4 jsou v části J,
> nově otevřené otázky z implementace v1.4 v části K.

## Co naopak sedí (ověřeno skriptem)

- ID států: `npc.json` a `state.json` mají shodně N1 až N12, z toho 10 `normal` a 2 `fallen`.
- Všechny hodnoty `wealth`, `power`, `law`, `tech`, `pop`, `prod`, `need` jsou v obou souborech identické.
- `metrics.W0 = 666` odpovídá skutečnému součtu `wealth` na startu (A 100 + B 80 + NPC 486).
- Počet států pro `n_bída / 14` v indexu prosperity: 12 NPC + A + B = 14. Souhlasí.
- `adjacency` je úplná (A, B, N1 až N12) a plně symetrická, žádná hrana nevede do neexistujícího státu.
- Cíle displacementu (N6, N3, N8, N9) existují a všechny jsou `kind: normal`, takže je neblokuje pravidlo 7a.
- Na startu není žádný stát v bídě podle definice 4.3.

---

## A. Chybějící pole ve `state.json`

### A1. Hráči A a B nemají `poverty_streak` ani `coups`

Pravidlo 4.3 definuje bídu pro "stát", nerozlišuje hráče a NPC, a index prosperity (část 8)
počítá `n_bída` ze 14 států, tedy včetně A a B. Aby mohl být hráč v bídě, potřebuje počítadlo
tří tahů v řadě. NPC obě pole mají, hráči ne.

Navíc 4.3 říká, že po třech tazích bídy "vláda padá, všechny obchody a pakty se ruší, dluhy
zůstávají, `influence` obou hráčů na 0, `coups +1`, `status` = independent". U hráče nedává
smysl ani `influence` obou hráčů, ani návrat na `independent`.

**Otázka:** Může být hráč v bídě, a pokud ano, co se stane po třech tazích? Padá mu vláda?

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** hráč se do `n_bída` započítává (index by jinak nesouhlasil s dělitelem 14),
efekty bídy `pop −3` a `power −1` se na něj vztahují, ale pád vlády se u hráče neprovádí.
Engine si `poverty_streak` a `coups` u hráčů drží ve stejně pojmenovaných polích, která
do `state.json` doplní při prvním zápisu.

### A2. Unie má zároveň `wealth` i `fund`

Pravidlo 7.2 říká doslova "Fond (`wealth` C) = 10 % `wealth` každého člena při vstupu".
Podle toho jsou fond a bohatství Unie totéž. `state.json` má ale obě pole zvlášť,
obě nastavená na 0, a není určeno, které je zdrojem pravdy.

**Otázka:** Je `fund` jen zrcadlo `wealth`, nebo dvě oddělené kapsy?

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** `wealth` je zdroj pravdy, `fund` se na konci každého tahu přepíše
na stejnou hodnotu. Akce `union_fund` čerpá z `wealth`.

### A3. Unie nemá `prod`, `need`, `pop`, `occupied`

Unie je v části 7.2 plnohodnotný hráč, ale nemá vlastní produkci ani obyvatelstvo,
protože ty zůstávají členům (vnitřní trh v 7.2). Pravidlo 8 přitom počítá `W_real` jako
"součet `wealth` všech států".

**Otázka:** Započítává se fond Unie do `W_real`? A je Unie "aktér" pro `max_share`,
tedy může svou velikostí index srážet stejně jako velmoc?

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** fond Unie se do `W_real` **nezapočítává** (prostředky pocházejí
z bohatství členů, které se počítá u nich, započtení by je zdvojilo) a Unie **není** aktér
pro `max_share`. Obojí je volba ve prospěch vyššího indexu, tedy mírnější, a právě index
rozhoduje verdikt "všichni vyhráli / všichni prohráli". Stojí za potvrzení.

### A4. Hráči nemají `status`

Tabulka v části 2 uvádí `status` jako pole "každého státu", ale hodnoty
(`independent`, `sphere_X`, `occupied_X`, `union`, `candidate`) dávají smysl jen u NPC.

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** hráči status nemají, engine ho u nich nečte ani nezapisuje.

---

## B. Nedourčené struktury

### B1. Formát `minsky.defaults`

Pravidlo 4.5 říká, že nesplácení se zapisuje do `defaults`. Pravidlo 5 pak potřebuje dvě
různá čtení téhož pole: přechod na `distress` při "prvním nesplácení" a na `panic` při
"druhém nesplácení" (globálně, napříč světem), a ve fázi `crash` se ptá, které NPC nesplácelo
konkrétnímu věřiteli X ("má záznam v `defaults` vůči X").

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** `defaults` je seznam záznamů `{"turn": N, "npc": "N6", "creditor": "A"}`,
jeden za každou dvojici dlužník a věřitel a tah. Počítadlo pro fázi bere počet **tahů**,
ve kterých došlo aspoň k jednomu nesplácení, ne počet záznamů. Jinak by jediný tah,
kdy nesplácejí tři NPC, přeskočil `distress` rovnou do `panic`.

### B2. Formát `deals`, `invasions`, `messages_pending`, `news`, `log`

Všechna pole jsou na startu prázdná a schéma není nikde popsané. Akce `cancel` přitom
bere `deal_id`, takže obchody, pakty i sankce musí mít stabilní identifikátor.

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** engine používá jednotný seznam `deals` se záznamy
`{"id": "d7", "type": "trade|protect|pressure", "owner": "A", "target": "N6", ...}`.
Identifikátor je `d` plus pořadové číslo, nikdy se nerecykluje. Schéma je popsané
v hlavičce `engine.py`.

### B3. `meta.slot`

Část 3 popisuje tři tahy denně (7:00, 13:00, 20:00), ale `slot` je `null` a číselník chybí.

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** `slot` je 1, 2, 3 pro ráno, poledne, večer. Den je `((turn - 1) // 3) + 1`,
slot je `((turn - 1) % 3) + 1`. Sedí na zadání: tah 7 vychází na den 3 ráno (displacement)
a den 30 na tahy 88 až 90.

---

## C. Nedourčené mechaniky

### C1. Migrace v boomu nemá určené dárce

Pravidlo 5, fáze `boom`: "každé NPC s `prod.orit ≥ 2` `pop +2/tah`, čerpá se z NPC bez oritu
(`pop −1`, `prod.grain −0.5` dočasně)". Není řečeno, **kolik** dárců a **kteří**.

Po displacementu má `prod.orit ≥ 2` jediný stát, N6 (hodnota 6). N3, N8 a N9 mají 1,
takže migraci nedostávají. N6 tedy potřebuje +2 `pop`, což při `pop −1` na dárce znamená
přesně dva dárce za tah.

**Otázka:** Jak se dárci vybírají? Sousedé? Nejchudší? Náhodně?

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** dva dárci za tah, vybraní deterministicky z NPC bez oritu
přes `random.Random(rng_seed + turn)`, s vyloučením padlých říší (7a jsou uzavřené)
a států s `pop ≤ 0`. Součet `pop` světa tak zůstává zachovaný, což vyžaduje `validate.py`.

Slovo "dočasně" u `prod.grain −0.5` nemá určenou dobu trvání. Engine ho bere jako "dokud se
migrant nevrátí", tedy do fáze `crash`, kde pravidlo 5 říká "migrace zpět".

### C2. `validate.py` má hlídat zachování `pop`, ale tři pravidla `pop` mění

`BUILD.md` část 4 žádá, aby validace selhala, když "součet `pop` světa se změnil jinak než
migrací". Jenže `pop` mění i bída (4.3: `pop −3/tah`) a dobytí (3.3: `pop −20 %`, uprchlíci
jdou do sousedního NPC). Invariant, jak je napsaný, by spadl u prvního hladomoru.

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** validace hlídá, že každá změna součtu `pop` je pokrytá záznamem
v `applied_rules` od pravidla, které `pop` měnit smí (4.3 bída, 3.3 invaze a uprchlíci,
5 migrace). Nevysvětlený rozdíl je chyba. Znění invariantu v `BUILD.md` by se mělo upřesnit.

### C3. Směr obchodu u `trade_offer`

Parametry jsou `target`, `res`, `qty`, `price_per_unit`, ale není určeno, zda hráč nakupuje
nebo prodává. Pravidlo říká jen "NPC přijme, pokud má přebytek/deficit".

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** směr určuje bilance NPC u dané suroviny. Přebytek znamená, že NPC
prodává hráči, deficit, že od hráče nakupuje. Nulová bilance znamená odmítnutí.

### C4. Automatický `explore` NPC stojí jinak než hráčův

Fáze `displacement`: "Běžná NPC s `wealth ≥ 20` automaticky každý tah utrácí 2 wealth
za `explore`", zatímco hráčova akce `explore` stojí 5 wealth za 15 % šanci (3.2).

**Otázka:** Má levnější varianta NPC i nižší šanci, nebo jde o stejných 15 % za 2 wealth?

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** stejných 15 %. Formulace "utrácí 2 wealth za `explore`" se čte
jako tatáž akce za jinou cenu.

### C5. Co přesně jsou "jednotky produkce" v metrice B

Pravidlo 8: `B_resource_share` je "(jednotky produkce B + okupovaných B + 0.5 × sphere_B)
/ světová produkce". Není určeno, zda jde o surové `prod`, nebo o efektivní produkci
po započtení `tech` (4.1) a `pop` (10.2).

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** efektivní produkce, tedy `prod × (1 + tech/20) × pop/100`.
Metrika pak reaguje na migraci a technologii, což odpovídá smyslu pravidla 10.2
("migrace reálně přesouvá výrobu").

### C6. `need.orit = 2` pro všechny je trvalý odliv bohatství

Fáze `displacement` dává `need.orit = 2` všem hráčům i běžným NPC, ale produkci oritu
jen čtyřem státům. Podle 4.1 stojí každá nepokrytá jednotka 1 wealth za tah, takže
od tahu 7 platí prakticky celý svět 2 wealth za tah navíc, dokud si orit nekoupí.

Není to nesrovnalost, pravidlo je jednoznačné. Uvádím to proto, že jde o citelný tlak
na `W_real`, a tedy přímo na index prosperity, podle kterého se vyhodnocuje celá hra.
Engine to implementuje přesně podle pravidla. Čísla z běhu jsou v oddílu D.

### C7. Rolování dluhu v Ponziho zóně: je to nesplácení?

Fáze `overtrading` říká, že NPC s dluhem nad 50 % `wealth` "přestává splácet reálně
a splácí novým dluhem". Pravidlo 4.5 zároveň definuje nesplácení jako "tah, kdy NPC
nesplatilo nic". Doslovným čtením je každý rolovaný tah nesplácením, což by spustilo
`distress` hned v prvním tahu `overtrading` a celá Ponziho zóna by trvala jeden tah.

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** rolování **není** nesplácení. Formálně dluh obsloužen je,
jen novým dluhem, což přesně odpovídá obrazu v `docs/faze.md` ("Státy si půjčují na
splátky starých půjček"). Nesplácení je až situace, kdy NPC nezaplatí a ani neroluje,
typicky kvůli dolní hranici `wealth 10` z pravidla 4.5.

### C8. Trvalé efekty z řádku `displacement`

Řádek `displacement` v tabulce pravidla 5 míchá jednorázové nastavení (orit se objeví,
ložiska, cena 10) s efekty, které musí platit dál (`tech +0.1` a `power +1` za každou
spotřebovanou jednotku, automatický `explore` NPC, povinná zpráva rozhodčího o soupeři).
Kdyby ty druhé platily jen během `displacement`, přestaly by platit v okamžiku, kdy
začne `boom`, a spotřeba oritu by rázem nic neznamenala.

**Potvrzeno 11. 9. 2026, zapsáno do pravidel v1.1:** jednorázové nastavení proběhne při vstupu do fáze, trvalé efekty
platí od `displacement` dál až do konce hry.

---

## D. Prahy Minskyho cyklu versus dvanáctitahový test

Doplněno po běhu `test_run.py` dne 11. 9. 2026. Prahy v pravidlech neměním,
níže jsou naměřená čísla a návrhy.

### D1. Cyklus se do tahu 12 vejít nemůže

Scénář ze zadání (A půjčuje N6 od tahu 8, B chrání N7, oba obchodují obilím) prošel
takto:

| kritérium | výsledek |
|---|---|
| displacement v tahu 7 | prošlo |
| boom | prošlo, tah 8 (první `loan`) |
| euphoria | neprošlo, do tahu 12 nenastala |
| overtrading, distress, panic, crash | neprošly |
| vznik Unie s aspoň 3 členy | neprošlo, crash nenastal |
| index prosperity každý tah | prošlo |
| validate bez chyb | prošlo, 0 chyb ve všech 12 tazích |

Důvod je aritmetický, ne chyba implementace. Displacement je pevně v tahu 7, takže na
šest dalších přechodů zbývá pět tahů. Cena oritu startuje na 10 a v boomu roste o 15 %
za tah: 11.50, 13.22, 15.21, 17.49, **20.11**. Prahu 20 pro `euphoria` dosáhne až
v tahu 12, takže fáze se přepne v tahu 13. Jen první ze šesti zbylých přechodů tedy
okno o jeden tah přeteče.

**Návrh:** problém je v testovacím okně, ne v prazích. Doporučuji upravit `BUILD.md`
část 8 z 12 tahů na 45, a ne sahat na pravidla. Diagnostický běh (níže) ukazuje,
že při tomto nastavení proběhne celý cyklus včetně vzniku Unie do tahu 42.

### D2. Kdy fáze nastanou při agresivním půjčování

Druhý běh, kde oba hráči půjčují na limit akcí, tedy horní odhad rychlosti cyklu:

| fáze | tah | den | co ji spustilo |
|---|---|---|---|
| displacement | 7 | 3 | pevný tah |
| boom | 8 | 3 | první `loan` |
| euphoria | 13 | 5 | cena oritu 24.14 |
| overtrading | 39 | 13 | dluh/wealth 0.621 |
| distress | 40 | 14 | nesplácení |
| panic | 41 | 14 | nesplácení |
| crash | 42 | 14 | po panice |
| depression | 48 | 16 | 6 tahů po crash |
| recovery | 54 | 18 | 12 tahů po crash |

Unie vznikla v tahu 42 s 11 členy. Validace nehlásila chybu ani v jednom z 90 tahů.

Mezi `euphoria` a `overtrading` je 26 tahů, skoro devět herních dní, protože práh
"dluhy NPC nad 60 % jejich reálného wealth" je při limitu dvou akcí na tah vysoký.
Při realistické hře, kde hráči nepůjčují každý tah, se `overtrading` nemusí spustit vůbec.

**Návrh:** snížit práh `overtrading` z 60 % na 35 až 40 %. Hodnota 0.43 nastala v tahu 30,
což by dalo krizi kolem tahu 33 a nechalo skoro dvě třetiny hry na druhé dějství.

### D3. Práh `distress` je splněný dřív, než na něj dojde řada

První záznam o nesplácení padl v tahu **11**, tedy ještě v boomu. Fáze ale jdou jen
dopředu, takže na `distress` došlo až v tahu 40, **29 tahů** po splnění jeho vlastní
podmínky. Prahy `distress` ("první nesplácení") a `panic` ("druhé nesplácení") jsou
v praxi splněné mnohonásobně dřív, než cyklus doputuje k `overtrading`, takže obě fáze
trvají mechanicky jeden tah a nic nerozhodují.

**Návrh:** vztáhnout obě podmínky k okamžiku vstupu do `overtrading`, tedy "první
nesplácení po vstupu do overtrading". Tím se z nich stanou skutečné spouštěče.
Formulace v pravidlech se tím nemění věcně, jen se doplní počátek počítání.

### D4. Index prosperity není shora omezený, a tím ztrácí verdikt smysl

Tohle je nález mimo zadání testu, ale míří přímo na vyhodnocení hry.

Růst v pravidle 4.2 je složené úročení: `wealth += 0.02 × wealth × (law/5) × (1 + tech/10)`.
Při `law` kolem 7 a `tech` kolem 6 je to zhruba 5 % za tah, tedy přes 90 tahů
řádově osmdesátinásobek. Člen `W_real / W_0` v indexu proto roste bez omezení.

Naměřeno v diagnostickém běhu:

| tah | index | W_real | států v bídě (ze 14) |
|---|---|---|---|
| 1 | 83.72 | 655.8 | 0 |
| 12 | 17.89 | 449.2 | 8 |
| 30 | 12.29 | 932.8 | 11 |
| 60 | 64.97 | 5 873.9 | 11 |
| 90 | **411.33** | 43 669.8 | **11** |

V tahu 90 je index 411 při prahu vítězství 70, a přitom je **11 ze 14 států v bídě**.
Verdikt "všichni vyhráli" by padl ve světě, kde skoro nikdo nemá co jíst. Členy
`(1 − max_share)` a `(1 − n_bída/14)` to neutáhnou, protože jsou oba omezené intervalem
0 až 1, zatímco `W_real / W_0` míří k nekonečnu.

**Otázka pro tebe, tohle je designové rozhodnutí, ne detail implementace:**
má být index měřítkem *úrovně* bohatství, nebo jeho *rozdělení a udržitelnosti*?

**Návrhy, kterýkoli řeší symptom:**
1. Zastropovat první člen, například `min(1.5, W_real / W_0)`. Nejmenší zásah,
   index pak měří hlavně rovnost a nepřítomnost bídy.
2. Měřit `W_real` na obyvatele a proti světové populaci, ne proti startovní hodnotě.
3. Zvednout práh vítězství ze 70 na hodnotu odvozenou od tahu, například `70 × (W_real / W_0)`.

Doporučuji variantu 1: zachovává smysl "zbohatli jsme, ale ne na úkor ostatních"
a je to jednořádková změna v části 8.

### D5. Svět bez obchodu krvácí

Vedlejší pozorování z obou běhů. Každé NPC potřebuje `oil 2`, `grain 3`, `metal 1`,
ale žádné neprodukuje všechny tři, a pravidla neznají obchod mezi NPC navzájem,
jen hráč s NPC. Nepokrytá jednotka stojí podle 4.1 jedno `wealth` za tah.

Bez zásahu hráčů proto svět ztrácí zhruba 10 `wealth` za tah hned od tahu 1
(666 na 655.8 po prvním tahu) a čtyři státy padnou do bídy do tahu 7, ještě než
se objeví orit. Od tahu 7 přidá `need.orit = 2` u všech dalších plošný odliv (viz C6).

Není to chyba, plyne to přímo z pravidel. Ale znamená to, že hráči mají mnohem míň
prostoru na mocenské hry, než by se z pravidel zdálo: dvě akce za tah proti dvanácti
NPC, které hladovějí od začátku. Stojí za zvážení, jestli je to záměr, nebo jestli
mají NPC mezi sebou obchodovat automaticky.

---

## C9 až C12. Nově otevřené otázky z implementace v1.1

Tyto body vznikly při zapracování rozhodnutí z 11. 9. Neopravuji je,
engine u nich používá uvedený výklad.

### C9. Jak spojit "nejvyšší fragility" se "souvislým územím" u zakladatelů Unie

Pravidlo 7.1 (v1.1) žádá zároveň dvě věci: zakladatelé musí tvořit souvislé území
a zároveň se vybírají čtyři s nejvyšší `fragility`. Když jsou čtyři nejkřehčí státy
rozházené po mapě, nejdou splnit obě podmínky najednou.

**Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.2 (7.1):** nejdřív se najdou souvislé skupiny způsobilých států a vybere se
největší (při shodě ta s nižším průměrným `wealth`). Uvnitř ní se začne nejkřehčím
státem a postupně se přidává vždy nejkřehčí soused už vybrané skupiny, dokud nejsou
čtyři. Výběr tak zůstane souvislý a zároveň co nejkřehčí.

### C10. Vyřazuje převrat člena z Unie?

Pravidlo 4.3 při pádu vlády nastaví `status = independent`, ale nikde neříká, co se
stane s členstvím v Unii. Bez vyřazení zůstal stát v seznamu členů a zároveň byl
`independent`, takže se v dalším tahu připojil znovu a v seznamu byl dvakrát.

**Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.2 (4.3):** převrat vyřazuje z členů i z kandidátů, protože `independent`
a členství se vylučují. Stát se může ucházet znovu podle 7.4.

### C11. Stát na nule má převrat každý tah

Pravidlo 4.3 zní "Tři tahy bídy v řadě (nebo `wealth = 0`): vláda padá". Druhá
podmínka nemá počítadlo ani pauzu, takže stát držený na nule má převrat **každý tah**,
a protože pád vlády ruší všechny obchody a pakty, nemůže se z nuly nikdy dostat.

V devadesátitahovém běhu to dělá **695 až 724 převratů** místo teoretického maxima
360 při čtení "jen tři tahy bídy". Je to hlavní motor spirály popsané v E3.

**Otázka:** má mít podmínka `wealth = 0` stejné počítadlo tří tahů jako bída,
nebo aspoň pauzu, než může vláda padnout znovu?

**Vyřešeno 14. 9. 2026 bodem 10 rozhodnutí (pravidla v1.2, 4.3):** tah s `wealth = 0` se počítá jako tah bídy, převrat přijde až po třech tazích bídy v řadě a po něm má stát šest tahů imunitu. Původní výklad enginu byl: zatím doslovné znění, tedy převrat každý tah. Doporučuji změnit,
návrh je v E3.

### C12. Pořadí vnitřního trhu Unie a obchodu NPC mezi sebou

Pravidlo 4.1a říká, že obchod NPC mezi sebou přijde "po vyhodnocení obchodů hráčů".
Vnitřní trh Unie (7.2) je ale taky obchod mezi NPC a pravidla neurčují, co z toho jde první.

**Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.2 (4.1a):** nejdřív obchody hráčů, pak vnitřní trh Unie zdarma mezi členy,
pak placené párování 4.1a na tom, co zbylo. Členové tak nejdřív využijí vlastní trh
a teprve zbytek řeší nákupem od sousedů, což je pro ně výhodnější a odpovídá smyslu 7.2.

---

## E. Výsledky testů po zapracování v1.1

Běh `test_run.py` z 11. 9. 2026. Kritéria se měří v okně 45 tahů podle nového
znění `BUILD.md` části 8, tabulky pokračují do tahu 90.

**Souhrn:** varianta (b) splnila všechna kritéria včetně vzniku Unie.
Varianta (a) se zastavila v `euphoria`. Validace nehlásila chybu ani v jednom
z 90 tahů v žádné z variant (a: 0 chyb, b: 0 chyb).

### E.a Varianta (a): scénář ze zadání

A půjčuje N6 od tahu 8, B chrání N7, oba obchodují obilím.

#### E.a.1 Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 8 | 3 | prvni loan po displacementu |
| `euphoria` | 13 | 5 | cena oritu >= 20 |
| `overtrading` | - | - | nenastala |
| `distress` | - | - | nenastala |
| `panic` | - | - | nenastala |
| `crash` | - | - | nenastala |
| `depression` | - | - | nenastala |
| `recovery` | - | - | nenastala |

Cyklus se zastavil v `euphoria`. Důvod: práh `overtrading` je 40 % součtu reálného
`wealth` NPC, tedy zhruba 160 při jediném věřiteli. A má na startu 100 `wealth`
a půjčuje 10 za tah, takže mu peníze dojdou dřív, než dluh NPC toho prahu dosáhne.
Jeden půjčující hráč krizi nevyvolá.

Vedlejší důsledek: `euphoria` nemá jiný východ než `overtrading`, takže cena oritu
roste o 20 % za tah donekonečna. V tahu 90 je **26 323 936**. Viz E3.

#### E.a.2 Index a ceny

| tah | index | W_real | v bídě (ze 14) | ceny zdrojů |
|---|---|---|---|---|
| 1 | 83.98 | 655.5 | 0 | grain 0.77, metal 0.84, oil 0.86 |
| 12 | 17.46 | 456.6 | 9 | grain 0.95, metal 0.84, oil 0.84, orit 26.24 |
| 30 | 8.88 | 384.7 | 10 | grain 1.20, metal 1.80, oil 1.18, orit 312.37 |
| 45 | 7.52 | 511.0 | 11 | grain 1.20, metal 1.80, oil 1.50, orit 4812.68 |
| 60 | 10.93 | 786.5 | 11 | grain 1.20, metal 1.80, oil 1.50, orit 74149.09 |
| 90 | 8.30 | 1992.5 | 12 | grain 1.20, metal 1.80, oil 1.50, orit 26323936.45 |

#### E.a.3 Unie

Unie nevznikla, fáze `crash` do tahu 90 nenastala.

#### E.a.4 Obchod

| tah | objem NPC s NPC | objem hráčů | podíl NPC |
|---|---|---|---|
| 6 | 8.59 | 4.80 | 64.1 % |
| 30 | 2.83 | 0.00 | 100.0 % |
| 60 | 3.00 | 0.00 | 100.0 % |
| 90 | 0.00 | 0.00 | 0.0 % |

### E.b Varianta (b): realistické půjčování

Hráč půjčí jen v tahu, kdy nějaké NPC žádá půjčku (euforie) nebo má deficit oritu,
nejvýš jedna půjčka na hráče a tah.

#### E.b.1 Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 8 | 3 | prvni loan po displacementu |
| `euphoria` | 13 | 5 | cena oritu >= 20 |
| `overtrading` | 19 | 7 | dluhy NPC > 40 % jejich wealth |
| `distress` | 20 | 7 | prvni nesplaceni |
| `panic` | 21 | 7 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 22 | 8 | po jednom tahu paniky |
| `depression` | 28 | 10 | 6 tahu po crash |
| `recovery` | 34 | 12 | 12 tahu po crash |

Celý cyklus proběhl a vešel se do okna: od displacementu v tahu 7 po `crash` v tahu 22,
tedy do osmého herního dne. Unie vznikla ve stejném tahu se čtyřmi zakladateli.

#### E.b.2 Index a ceny

| tah | index | W_real | v bídě (ze 14) | ceny zdrojů |
|---|---|---|---|---|
| 1 | 83.98 | 655.5 | 0 | grain 0.77, metal 0.84, oil 0.86 |
| 12 | 18.44 | 456.1 | 9 | grain 0.95, metal 0.84, oil 0.86, orit 26.24 |
| 30 | 10.67 | 409.1 | 10 | grain 1.20, metal 1.72, oil 1.36, orit 3.66 |
| 45 | 8.13 | 500.4 | 11 | grain 1.20, metal 1.80, oil 1.50, orit 3.50 |
| 60 | 7.10 | 725.0 | 12 | grain 1.20, metal 1.80, oil 1.50, orit 5.34 |
| 90 | 9.16 | 1867.0 | 12 | grain 1.20, metal 1.80, oil 1.50, orit 7.50 |

#### E.b.3 Unie

Zakladatelé (tah 22): **N1, N11, N6, N5**

| tah | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|
| 22 | 4 | N1, N11, N6, N5 | 2 | N7, N8 |
| 60 | 1 | N11 | 2 | N1, N8 |
| 90 | 1 | N11 | 2 | N1, N8 |

#### E.b.4 Obchod

| tah | objem NPC s NPC | objem hráčů | podíl NPC |
|---|---|---|---|
| 6 | 8.59 | 4.80 | 64.1 % |
| 30 | 6.03 | 0.00 | 100.0 % |
| 60 | 0.00 | 0.00 | 0.0 % |
| 90 | 0.00 | 0.00 | 0.0 % |

### E1. Dva hráči jsou pro krizi nutní

> **Vyřešeno 14. 9. 2026 bodem 11:** pojistka cyklu posune fázi od `boom` dál po 15 tazích bez prahu.

Rozdíl mezi variantami je jen v tom, kdo půjčuje. S jedním věřitelem (a) krize
nepřijde, se dvěma (b) přijde v tahu 19. Práh `overtrading` je tedy nastavený tak,
že bublinu musí nafouknout **oba** hráči. Pokud jeden z nich půjčovat odmítne,
Minskyho cyklus se zasekne v euforii a pojistka z části 5 ("pokud do tahu 45
nenastane `boom`") na to nedosáhne, protože ta hlídá jen `boom`, ne pozdější fáze.

**Návrh:** rozšířit pojistku i na `euphoria`, například "pokud cyklus uvázne
v jedné fázi víc než 15 tahů, engine ho posune dál a rozhodčí vydá zprávu".

### E2. Euforie bez východu žene cenu do nesmyslných čísel

> **Vyřešeno 14. 9. 2026 bodem 12:** cena oritu má strop 200.

Ve variantě (a) stojí orit v tahu 90 přes 26 milionů, protože `euphoria` násobí cenu
1.2 za tah a nemá strop. Je to přímý důsledek E1, ale stojí za vlastní pojistku:
`paper_wealth` se počítá z ceny oritu, takže s ní roste i on.

**Návrh:** zastropovat cenu oritu, například na dvacetinásobek výchozí hodnoty (200).

### E3. Stát na nule padá každý tah a tím se svět zasekne

> **Vyřešeno 14. 9. 2026 bodem 10:** převrat až po třech tazích bídy, šest tahů imunita, obchody a dluhy převrat přežijí.

Nejsilnější dynamika obou běhů, viz C11. Stát s `wealth = 0` má podle doslovného
znění 4.3 převrat každý tah, a protože pád vlády ruší všechny obchody a pakty,
nemá jak se z nuly dostat. V obou variantách napočítáno **695** (a) a **724** (b)
převratů za 90 tahů.

Důsledky jsou vidět ve všech tabulkách:

- obchod úplně ustal, ve variantě (a) v tahu 76, ve variantě (b) už v tahu 43,
  protože zrušené obchody se každý tah ruší znovu;
- Unie se rozpadla ze čtyř členů na jednoho, protože členům padaly vlády;
- v tahu 90 je **12 ze 14 států v bídě** a oba hráči mají `wealth` 0;
- jediné, kdo bohatne, jsou padlé říše: N11 má 1 221 a N12 798, dohromady
  přes polovinu světového bohatství. Jsou uzavřené (7a), takže je spirála míjí:
  nepotřebují orit, nepůjčují si a prodávají jen za 1.3násobek ceny.

Index proto skončí na 8.30 (a) a 9.16 (b) proti prahu vítězství 70. Strop
`min(1.5, W_real / W_0)` funguje podle záměru, ale verdikt teď spolehlivě padá
na druhou stranu: svět je chudý a nerovný, ne bohatý a nerovný.

**Návrh, v pořadí podle síly účinku:**

1. Dát podmínce `wealth = 0` stejné počítadlo tří tahů jako bídě, nebo pauzu
   aspoň tří tahů mezi dvěma převraty téhož státu (řeší C11 i E3).
2. Nerušit při pádu vlády obchody, které stát zásobují obilím, jinak se hladomor
   nedá zvrátit.
3. Zvážit, jestli mají padlé říše zůstat úplně mimo krizi. Momentálně jsou to
   jediní vítězové a hráči na ně nedosáhnou.

Žádnou z těchto změn jsem neprovedl, jsou to návrhy k rozhodnutí.

---

## F. Kalibrace a testy pravidel v1.2 (14. 9. 2026)

### Souhrn

| scénář | kritérium | výsledek |
|---|---|---|
| (0) nikdo netáhne | do tahu 15 žádné NPC v bídě | **neprošlo**, první N9 v tahu 2 |
| (0) | `W_real` v tahu 30 aspoň 90 % startu | prošlo, 93.4 % |
| (0) | validate 0 chyb | prošlo |
| (a) scénář ze zadání | crash mezi dnem 7 a 11 | **neprošlo**, crash v tahu 46, den 16 |
| (a) | Unie s aspoň 3 zakladateli | prošlo, N1, N11, N8, N2 (tah 46) |
| (a) | validate 0 chyb | prošlo |
| (b) realistické půjčování | crash mezi dnem 7 a 11 | **neprošlo**, crash v tahu 18, den 6 |
| (b) | Unie s aspoň 3 zakladateli | prošlo, N4, N7, N9, N12 (tah 18) |
| (b) | validate 0 chyb | prošlo |

### F1. Kalibrace: žádná změna

**V `npc.json` ani `state.json` jsem nad rámec hodnot určených rozhodnutím nic neměnil.**
Kritérium scénáře (0) nejde v povolených mezích splnit, takže každá změna by data posunula,
aniž by cíl splnila.

Prohledal jsem všech 24 kombinací povoleného rozsahu, stejnou hodnotu pro všechna čtyři chudá NPC
(N6, N8, N9, N10): výchozí `wealth` 20, 25 a 30, `industry` 1 a 2, `prod` bez bonusu nebo +1 `oil`,
`grain` či `metal`. Výsledek:

- **Neprošla ani jedna kombinace.** Nejlépe dopadla `wealth 30` s bonusem `grain` nebo `metal`:
  první chudé NPC padne do bídy v tahu 7, tedy stále před tahem 15.
- **Ve všech 24 kombinacích padají do tahu 15 do bídy i státy, na které kalibrace nesmí:**
  N1, N2, N3 a N5 vždy, N7 ve 22 z 24, N4 ve dvou. Tohle kritérium tedy blokuje, ne chudá NPC.
- `W_real` v tahu 30 kritérium splňuje už bez kalibrace (93.4 %) a ve všech kombinacích zůstává
  mezi 91.8 % a 101.4 %.

Proč padají i bohatší NPC, ukázal rozklad prvního tahu. Každé NPC potřebuje `goods 2` a skoro žádné
je nevyrobí: obilnice N1 a N2 nemají ropu, takže jejich továrny stojí, a N1 tak ztrácí 3 za tah
na deficitu `oil` a `goods`. Kovové N5 a N7 si do tahu 6 polepšují, ale od displacementu v tahu 7
kupují přes 4.1a orit (viz G12) a za čtyři tahy utratí většinu bohatství.

Kontrafakt jen v paměti, pravidla se nemění: kdyby NPC orit v 4.1a nekupovala, do tahu 15 by v bídě
stále byla N2 (tah 8), N1 (tah 14) a N5 (tah 15). Kritérium by tedy neprošlo ani tak. Nákup oritu
je navíc přesun bohatství mezi NPC, ne jeho zánik: bez něj by `W_real` v tahu 30 byl nižší (81.9 %).

### F2. Opravené chyby enginu (ne pravidla)

1. **Záporná populace při migraci.** Ve variantě (a) hlásila validace v tahu 31 `N1.pop = −1`.
   Dárce migrace se kontroloval jen jednou za tah, takže při víc příjemcích mohl být vybrán
   opakovaně a odečíst víc lidí, než měl. Chyba byla v enginu od v1, projevila se až teď, když
   orit našlo víc států. Dárce se nově kontroluje při každém výběru.
2. **Seznam zakladatelů Unie v událostech.** Záznam o zakladatelích sdílel seznam s aktuálními členy,
   takže do něj propadly i vstupy podle 7.4 v tahu založení. Výběr zakladatelů byl správný, chybné
   bylo jen hlášení. Opraveno.

Obě tabulky níže jsou z běhu po opravě.

### F.0 Scénář (0): nikdo netáhne

Hráči mlčí, žádné akce.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 45 | 15 | tah 45 bez pujcky, vynuceny boom |
| `euphoria` | 50 | 17 | cena oritu >= 20 |
| `overtrading` | 65 | 22 | pojistka cyklu: 15 tahu bez splneni prahu |
| `distress` | 80 | 27 | pojistka cyklu: 15 tahu bez splneni prahu |
| `panic` | 82 | 28 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 83 | 28 | po jednom tahu paniky |
| `depression` | 89 | 30 | 6 tahu po crash |

Pojistka cyklu: overtrading v tahu 65, distress v tahu 80. Nejvyšší tržní cena oritu za běh: 140.00.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 84.21 | 662.8 | 0 | 0.66 | 1.27 | 0.84 | 1.05 | - |
| 12 | 33.50 | 583.2 | 7 | 0.66 | 0.72 | 0.84 | 1.13 | 15.00 |
| 30 | 29.47 | 622.0 | 8 | 0.70 | 0.70 | 0.84 | 1.05 | 7.00 |
| 45 | 22.87 | 616.5 | 9 | 0.71 | 0.70 | 0.84 | 1.05 | 7.00 |
| 60 | 20.39 | 600.2 | 9 | 0.69 | 0.70 | 0.84 | 1.05 | 87.18 |
| 90 | 11.04 | 623.3 | 11 | 0.66 | 0.70 | 0.84 | 1.05 | 4.83 |

#### Unie

Zakladatelé (tah 83, den 28): **N1, N11, N6, N3**

| tah | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|
| 60 | 0 | - | 0 | - |
| 83 | 7 | N1, N11, N6, N3, N4, N5, N7 | 2 | N8, N9 |
| 90 | 4 | N2, N4, N10, N7 | 3 | N3, N6, N8 |

#### Obchod

| tah | NPC s NPC | hráči | z toho goods (všichni) |
|---|---|---|---|
| 6 | 16.08 | 0.00 | 5.12 |
| 30 | 8.12 | 0.00 | 0.00 |
| 60 | 0.52 | 0.00 | 0.52 |
| 90 | 0.00 | 0.00 | 0.00 |

#### Převraty a padlé říše

Převratů celkem za 90 tahů: **112**.

| tah | N11 Aurelie | N12 Ysmar |
|---|---|---|
| 30 | 53.1 | 70.1 |
| 60 | 17.1 | 85.0 |
| 90 | 2.5 | 80.2 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.0 / 6.40 | 6.0 / 12.67 | 2.0 / 0.00 | 1.0 / 0.55 | 7.0 / 0.00 |
| 30 | 8.0 / 8.00 | 6.0 / 12.67 | 0.0 / 0.00 | 0.5 / 0.62 | 7.0 / 0.00 |
| 60 | 8.0 / 8.00 | 6.0 / 12.67 | 0.0 / 0.00 | 0.5 / 0.00 | 7.0 / 0.00 |
| 90 | 8.0 / 8.00 | 6.0 / 12.67 | 0.0 / 0.00 | 0.0 / 0.00 | 4.1 / 0.00 |

Bohatství hráčů v tahu 90: A 280.0, B 260.0.

### F.a Varianta (a): scénář ze zadání

A půjčuje N6 od tahu 8, B chrání N7, oba obchodují obilím.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 8 | 3 | prvni loan po displacementu |
| `euphoria` | 13 | 5 | cena oritu >= 20 |
| `overtrading` | 28 | 10 | pojistka cyklu: 15 tahu bez splneni prahu |
| `distress` | 43 | 15 | pojistka cyklu: 15 tahu bez splneni prahu |
| `panic` | 45 | 15 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 46 | 16 | po jednom tahu paniky |
| `depression` | 52 | 18 | 6 tahu po crash |
| `recovery` | 58 | 20 | 12 tahu po crash |

Pojistka cyklu: overtrading v tahu 28, distress v tahu 43. Nejvyšší tržní cena oritu za běh: 140.04.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 84.57 | 662.8 | 0 | 0.66 | 1.27 | 0.84 | 1.05 | - |
| 12 | 31.71 | 564.5 | 7 | 0.73 | 0.71 | 0.84 | 1.15 | 26.24 |
| 30 | 22.16 | 511.4 | 8 | 0.70 | 0.70 | 0.84 | 1.16 | 140.00 |
| 45 | 12.90 | 266.0 | 8 | 0.66 | 0.70 | 0.84 | 1.19 | 140.00 |
| 60 | 11.15 | 235.3 | 8 | 0.70 | 0.70 | 0.84 | 1.05 | 3.50 |
| 90 | 7.40 | 221.2 | 9 | 0.62 | 0.70 | 0.84 | 1.05 | 7.19 |

#### Unie

Zakladatelé (tah 46, den 16): **N1, N11, N8, N2**

| tah | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|
| 46 | 4 | N1, N11, N8, N2 | 2 | N10, N7 |
| 60 | 2 | N11, N1 | 1 | N8 |
| 90 | 0 | - | 0 | - |

#### Obchod

| tah | NPC s NPC | hráči | z toho goods (všichni) |
|---|---|---|---|
| 6 | 16.08 | 4.80 | 5.12 |
| 30 | 7.70 | 4.80 | 0.00 |
| 60 | 3.64 | 4.80 | 0.00 |
| 90 | 3.15 | 4.80 | 0.00 |

#### Převraty a padlé říše

Převratů celkem za 90 tahů: **101**.

| tah | N11 Aurelie | N12 Ysmar |
|---|---|---|
| 30 | 53.1 | 70.1 |
| 60 | 13.8 | 61.1 |
| 90 | 2.9 | 52.1 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.0 / 6.40 | 6.0 / 12.67 | 2.0 / 0.00 | 1.0 / 0.55 | 7.0 / 0.00 |
| 30 | 7.9 / 8.00 | 6.0 / 12.67 | 0.0 / 0.00 | 0.5 / 0.94 | 7.0 / 0.00 |
| 60 | 6.4 / 5.99 | 6.0 / 12.67 | 0.0 / 0.00 | 0.5 / 0.85 | 6.8 / 0.00 |
| 90 | 6.4 / 6.08 | 6.0 / 12.67 | 0.0 / 0.00 | 0.5 / 0.27 | 3.8 / 0.00 |

Bohatství hráčů v tahu 90: A 83.2, B 50.0.

### F.b Varianta (b): realistické půjčování

Hráč půjčí jen v tahu, kdy NPC žádá půjčku nebo má deficit oritu, nejvýš jedna půjčka na hráče a tah.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 9 | 3 | prvni loan po displacementu |
| `euphoria` | 14 | 5 | cena oritu >= 20 |
| `overtrading` | 15 | 5 | dluhy NPC > 40 % jejich wealth |
| `distress` | 16 | 6 | prvni nesplaceni |
| `panic` | 17 | 6 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 18 | 6 | po jednom tahu paniky |
| `depression` | 24 | 8 | 6 tahu po crash |
| `recovery` | 30 | 10 | 12 tahu po crash |

Pojistka cyklu: nezasáhla. Nejvyšší tržní cena oritu za běh: 32.57.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 84.57 | 662.8 | 0 | 0.66 | 1.27 | 0.84 | 1.05 | - |
| 12 | 31.93 | 558.6 | 7 | 0.72 | 0.76 | 0.84 | 1.05 | 22.81 |
| 30 | 13.67 | 449.9 | 9 | 0.63 | 0.70 | 0.84 | 1.22 | 3.50 |
| 45 | 8.45 | 368.8 | 10 | 0.64 | 0.70 | 0.84 | 1.89 | 3.50 |
| 60 | 5.88 | 248.2 | 10 | 0.74 | 0.70 | 0.84 | 2.25 | 3.50 |
| 90 | 0.25 | 67.8 | 13 | 1.19 | 0.70 | 0.84 | 2.15 | 3.50 |

#### Unie

Zakladatelé (tah 18, den 6): **N4, N7, N9, N12**

| tah | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|
| 18 | 4 | N4, N7, N9, N12 | 1 | N6 |
| 60 | 1 | N12 | 2 | N6, N4 |
| 90 | 1 | N12 | 2 | N6, N4 |

#### Obchod

| tah | NPC s NPC | hráči | z toho goods (všichni) |
|---|---|---|---|
| 6 | 16.08 | 4.80 | 5.12 |
| 30 | 13.58 | 4.80 | 1.32 |
| 60 | 1.98 | 1.43 | 0.00 |
| 90 | 1.24 | 0.00 | 0.00 |

#### Převraty a padlé říše

Převratů celkem za 90 tahů: **99**.

| tah | N11 Aurelie | N12 Ysmar |
|---|---|---|
| 30 | 53.1 | 62.7 |
| 60 | 17.1 | 53.7 |
| 90 | 2.7 | 44.7 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.0 / 6.40 | 6.0 / 12.67 | 2.0 / 0.00 | 1.0 / 0.55 | 7.0 / 0.00 |
| 30 | 6.6 / 5.30 | 4.4 / 8.20 | 0.0 / 0.00 | 0.5 / 0.62 | 7.0 / 0.00 |
| 60 | 3.6 / 1.70 | 1.4 / 0.97 | 0.0 / 0.00 | 0.5 / 0.85 | 7.0 / 0.00 |
| 90 | 0.6 / 0.00 | 0.0 / 0.00 | 0.0 / 0.00 | 0.4 / 0.84 | 4.1 / 0.00 |

Bohatství hráčů v tahu 90: A 0.0, B 0.0.

### F3. Co z běhů plyne

1. **Převraty jsou pod kontrolou.** 99 až 112 za 90 tahů proti 695 až 724 ve v1.1. Bod 10 zabral.
2. **Crash nesedí do okna dne 7 až 11 v žádné variantě, ale z opačných stran.** Ve (b) přijde o den
   dřív (den 6): reálné bohatství NPC se po displacementu zhroutí, takže dluh nad 40 % jejich `wealth`
   je splněný hned v tahu po euforii a `distress`, `panic` a `crash` následují tah po tahu.
   V (a) přijde o pět dní později (den 16): jediný věřitel dluh nenafoukne a `distress` přišel až
   přes pojistku cyklu.
3. **Hráči a NPC žijí ve dvou oddělených ekonomikách.** Ve (0) mají A a B v tahu 90 bohatství 280
   a 260 a jejich továrny běží, zatímco 11 ze 14 států je v bídě. Přebytek `goods` hráčů se k NPC
   bez akce `trade_offer` nedostane, protože obchod 4.1a je jen mezi NPC (G11).
4. **Průmysl NPC bez zásahu vymírá.** `industry` N1 klesne do tahu 30 na 0, protože bída ho srazí
   o 0.1 za tah a bez ropy se nemá jak obnovit (G14). N11 nevyrobí za celou hru ani jednotku `goods`,
   protože nemá ropu ani souseda, který by mu ji prodal, a z 90 upadne na jednotky.
5. **Ve (b) se zhroutí i hráči.** Půjčují, dokud mají, a v tahu 30 jim zbývají 2 až 3 bohatství.
   Bída jim pak srazí i průmysl: v tahu 90 má A `industry` 0.6 a B 0.

---

## G. Nově otevřené otázky z implementace v1.2

Neopravuji je. Engine u každé používá uvedený výklad. Nejdůležitější jsou G11 a G12,
protože vysvětlují většinu kolapsu v části F.

### G11. Přebytek `goods` hráčů se k NPC nedostane, ale snižuje jejich cenu

> **Vyřešeno v1.3 (4.1a): přebytky hráčů A a B vstupují do automatického trhu.**

Obchod 4.1a je jen mezi NPC. Hráči A a B vyrábějí `goods` s přebytkem, ale NPC ho bez akce
`trade_offer` nekoupí. Dynamická cena 4.1b přitom počítá výrobu hráčů do světové nabídky,
takže `goods` stojí na dolní mezi 1.05, zatímco NPC platí za každou chybějící jednotku pokutu 1.
Svět je podle ceny zásobený a podle NPC hladoví.

**Otázka:** mají se hráči účastnit 4.1a jako prodejci, aspoň pro `goods`? Nebo má nabídka
v 4.1b počítat jen statky, které jsou NPC skutečně dostupné?

### G12. NPC kupují přes 4.1a orit, i když jeho nedostatek nic nestojí

> **Vyřešeno v1.3 (4.1a): orit se automaticky neobchoduje.**

Od displacementu mají běžná NPC `need.orit = 2` a 4.1a jim ten deficit „pokrývá“ nákupem
za cenu kolem 10 až 15, dokud mají peníze. Nepokrytý orit přitom od v1.1 nic nestojí. Ve (0)
utratí NPC za orit do tahu 30 celkem 289, z toho N7 91 a N3 85. N7 zaplatí za jediný tah 28.66.

**Otázka:** má 4.1a orit kupovat jen do výše, kterou si NPC může dovolit, nebo orit z 4.1a
vyřadit, protože nepokrytí nemá cenu?

### G1. Co přesně je `coverage`

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.3 (4.0).**

Pravidlo 4.0 říká „podíl průmyslových vstupů, které má stát k dispozici“, ale vstupy jsou dva.
**Výklad enginu:** nejmenší z obou poměrů (dostupná ropa k potřebě ropy, dostupné kovy k potřebě
kovů), tedy chybí-li jeden vstup, továrny stojí, i když druhého je dost.

### G2. Obchod ve dvou kolech a nevyužité vstupy

> **Částečně vyřešeno v1.3 (4.1c): nevyužité průmyslové vstupy jdou do zásoby. Dvě kola obchodu engine drží dál.**

Výroba `goods` závisí na nakoupených vstupech a obchod `goods` na výrobě. **Výklad enginu:**
nejdřív se obchoduje obilí, ropa, kovy a orit, pak se spočítá výroba, pak se obchoduje `goods`.
V prvním kole si továrny rezervují vstupy pro plnou výrobu. Když pak kvůli chybějícímu druhému
vstupu vyrábějí méně, nakoupený přebytek propadne, protože zásoby se v v1 nedrží.

### G3. Z čeho se počítá cena na začátku tahu

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.3 (4.1b).**

Pravidlo 4.1b přepočítává cenu na začátku tahu, ale potřeby a výroba `goods` vznikají až v přepočtu.
**Výklad enginu:** použijí se hodnoty z minulého tahu, v prvním tahu předběžný odhad při plném
využití továren.

### G4. Na koho smí mířit `invest_industry`

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.3 (3.2).**

Rozhodnutí určuje cenu, účinek a slevu pro Unii, ne cíl. **Výklad enginu:** stejně jako
`invest_tech`, tedy vlastní stát nebo NPC ve vlastní sféře; Unie členy a kandidáty. Podmínka
`law ≥ 4` se bere u cíle.

### G5. Střídání investic v 4.2a

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.3 (4.2a).**

**Výklad enginu:** střídá se podle čísla tahu pro všechna NPC najednou. Tahy 3, 9, 15 a dál jsou
`invest_tech`, tahy 6, 12, 18 a dál `invest_industry`. Alternativa by bylo střídání pro každé NPC
zvlášť podle jeho poslední investice.

### G6. Běží počítadlo bídy během imunity?

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.3 (4.3).**

**Výklad enginu:** ano. Stát v imunitě dál sbírá tahy bídy, a pokud je po skončení imunity
`poverty_streak` aspoň 3, převrat přijde hned v prvním tahu po ní.

### G7. Platí strop 200 i pro tržní cenu oritu?

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.3 (5).**

Strop je v části 5, dynamika 4.1b se k ceně přičítá a mohla by ji dostat až na 300.
**Výklad enginu:** strop platí pro Minskyho cenu i pro výslednou tržní cenu.

### G8. Patří `goods` do metriky B?

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.3 (8).**

`B_resource_share` měří „zdroje pod kontrolou“. **Výklad enginu:** `goods` je produkt, ne zdroj,
do metriky B se nepočítá. Do objemu obchodu v metrice A se počítá.

### G9. Statická `need` v `npc.json`

> **Vyřešeno 14. 9. 2026: statická `need` odstraněna i z `npc.json`, zapsáno do pravidel v1.3 (4.0).**

Rozhodnutí odstraňuje statická `need` jen ze `state.json`. V `npc.json` zůstala a neodpovídají
počítaným potřebám. Engine je nečte. **Otázka:** odstranit je i z `npc.json`?

### G10. Strop indexu prosperity

> **Rozhodnuto 14. 9. 2026: strop zůstává, zapsáno do pravidel v1.3 (8).**

Rozhodnutí říká „Strop růstu z minulého zadání tím odpadá.“ Není jisté, zda jde o konstatování
(autonomní růst zmizel, takže strop je bezpředmětný), nebo o pokyn strop `min(1.5, W_real / W_0)`
z části 8 zrušit. **Výklad enginu:** strop jsem ponechal, protože část 8 výslovně měnit nemám a při
současném vývoji `W_real` nikdy nepřekročí start. **Otázka:** zrušit?

### G13. Populace 200 zdvojnásobuje i surovinovou produkci hráčů

> **Vyřešeno v1.3 (4.0, 10.2): efektivní produkce se vztahuje k `pop_start`.**

Podle 10.2 je efektivní produkce `prod × pop / 100`. Hráči s `pop = 200` proto těží dvakrát víc
surovin než v v1.1, nejen víc spotřebovávají. **Otázka:** je to záměr?

### G14. Průmysl na nule se sám neobnoví

> **Vyřešeno v1.3 (4.2c) pro hráče a běžná NPC dnem 0.5. U padlých říší trvá, viz I11.**

S `industry = 0` je potenciál výroby nula a engine bere `coverage` jako 0, takže podmínka
`coverage ≥ 0.8` z 4.2c nemůže nastat. Stát se z nuly dostane jen investicí.
**Otázka:** má mít 4.2c u nulového průmyslu výjimku?

### G15. Vstup do Unie v tahu jejího založení

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.3 (7.4); engine upraven, vstupy až od dalšího tahu.**

Podle 10.10 Unie poprvé táhne až v tahu po založení. Vstupy „bolestí“ podle 7.4 ale nejsou akcí Unie,
takže je engine provádí už v tahu založení. Ve (0) tak k zakladatelům ve stejném tahu přistoupili
další členové. **Otázka:** mají vstupy čekat do dalšího tahu?

---

## H. Testy pravidel v1.3 (14. 9. 2026)

### Souhrn

| scénář | kritérium | výsledek |
|---|---|---|
| (0) nikdo netáhne | do tahu 15 nejvýš dvě NPC v bídě | **neprošlo**, 5 NPC: N1, N6, N8, N9, N10 |
| (0) | do tahu 15 v bídě žádné z N1 až N5, N7, N11, N12 | **neprošlo**, N1 |
| (0) | `W_real` v tahu 30 aspoň 90 % startu | prošlo, 100.2 % z 717 |
| (0) | do tahu 90 nejvýš 5 NPC v bídě | **neprošlo**, nejvíc 10 najednou (tah 71), různých za běh 11 |
| (a) scénář ze zadání | crash mezi dnem 7 a 11 | **neprošlo**, tah 36, den 12 |
| (a) | Unie s aspoň 3 zakladateli | prošlo, N6, N1, N11, N5 (tah 36) |
| (a) | validate 0 chyb | prošlo |
| (b) realistické půjčování | crash mezi dnem 7 a 11 | prošlo, tah 26, den 9 |
| (b) | Unie s aspoň 3 zakladateli | prošlo, N6, N1, N8, N5 (tah 26) |
| (b) | validate 0 chyb | prošlo |

Validace hlásí 0 chyb ve všech třech scénářích a všech 90 tazích. Výklad kritérií (0) je v I12:
„do tahu 15“ počítá různá NPC, která byla v bídě kdykoli v tazích 1 až 15; „do tahu 90“
nejvyšší počet NPC v bídě v jednom tahu.

### H1. Scénář (0) neprošel: nekalibruji, proč NPC padají

Podle zadání jsem nic nekalibroval. Rozpis níže je průměr za tah od začátku hry do tahu, kdy
NPC poprvé padlo do bídy. Sloupec „ostatní“ je rozdíl skutečné změny `wealth` a součtu známých
položek; je všude nulový, účty se tedy uzavírají.

| NPC | v bídě od | spouštěč | prodej | nákup | pokuty | příjem 4.2b | investice 4.2a | průzkum | ostatní | **čistě** | pokuty podle statku (součet) | zásoby grain / goods / oil: start → pád |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N8 | tah 6 | `wealth` 14.5 | +0.00 | -1.33 | -0.72 | +0.80 | +0.00 | +0.00 | +0.00 | **-1.25** | oil 3.2, metal 1.1 | 4.8 / 3.2 / 1.6 → 9.3 / 0.0 / 0.0 |
| N6 | tah 9 | `wealth` 13.9 | +0.13 | -1.93 | +0.00 | +0.90 | +0.00 | +0.00 | -0.00 | **-0.90** | - | 5.4 / 3.6 / 1.8 → 0.0 / 0.0 / 0.0 |
| N9 | tah 9 | `wealth` 14.7 | +0.00 | -0.94 | -0.26 | +0.60 | +0.00 | +0.00 | +0.00 | **-0.59** | metal 2.3 | 3.6 / 2.4 / 1.2 → 6.3 / 0.0 / 4.9 |
| N1 | tah 11 | `wealth` 14.8 | +0.13 | -2.07 | -0.52 | +1.90 | -1.64 | -0.55 | +0.00 | **-2.74** | oil 5.7 | 45.6 / 30.4 / 15.2 → 57.0 / 23.8 / 1.9 |
| N10 | tah 13 | `wealth` 15.0 | +0.47 | -0.93 | -0.55 | +0.85 | +0.00 | -0.62 | +0.00 | **-0.77** | oil 7.1 | 12.8 / 8.5 / 4.2 → 22.5 / 0.0 / 0.0 |
| N2 | tah 16 | `wealth` 11.0 | +0.15 | -1.82 | -0.86 | +1.60 | +0.00 | -0.88 | -0.00 | **-1.81** | oil 13.8 | 38.4 / 25.6 / 12.8 → 48.0 / 0.0 / 0.0 |
| N5 | tah 18 | `wealth` 13.8 | +2.28 | -3.74 | +0.00 | +1.00 | -0.44 | -0.56 | +0.00 | **-1.45** | - | 24.0 / 16.0 / 8.0 → 8.5 / 20.0 / 0.0 |
| N4 | tah 26 | `wealth` 14.5 | +3.02 | -3.06 | +0.00 | +1.10 | -1.38 | -1.23 | -0.00 | **-1.56** | - | 26.4 / 17.6 / 8.8 → 6.7 / 22.0 / 25.8 |
| N7 | tah 59 | `wealth` 14.4 | +3.55 | -3.93 | +0.00 | +1.10 | +0.00 | -1.12 | -0.00 | **-0.40** | - | 16.5 / 11.0 / 5.5 → 0.0 / 22.0 / 0.0 |
| N12 | tah 65 | `wealth` 12.9 | +0.22 | -1.72 | -0.24 | +0.70 | +0.00 | +0.00 | +0.00 | **-1.03** | grain 15.4 | 25.2 / 16.8 / 32.4 → 0.0 / 16.8 / 1.7 |
| N3 | tah 67 | `wealth` 14.9 | +3.84 | -2.80 | -1.48 | +1.20 | +0.00 | -1.43 | -0.00 | **-0.67** | grain 98.9 | 28.8 / 19.2 / 9.6 → 0.0 / 24.0 / 60.0 |

Co z rozpisu plyne:

1. **Pokuty už nejsou problém, zásoby je tlumí.** Průměrná pokuta je 0 až 1.5 za tah.
   Rozhoduje nákup na trhu, který je u každého padajícího NPC vyšší než jeho příjem.
2. **Peníze NPC odtékají k hráčům.** Hráči na automatickém trhu jen prodávají, nikdy nekupují
   (I13). Za prvních 15 tahů prodal A za 12.2 a B za 79.9. Ve (0) hráči nic neutrácejí, takže
   `W_real` v tahu 30 drží 100 % startu, ale bohatství se přelévá k A a B.
3. **Obilnice svůj přebytek neprodají.** N1 prodává za 0.13 za tah a jeho zásoba obilí přitom
   roste z 45.6 na 57. Kupci totiž nejdřív čerpají vlastní zásobu (I1), takže poptávka po obilí
   přijde až ve chvíli, kdy sousedům zásoby dojdou.
4. **Automatika 4.2a urychluje pád.** N1 má `wealth` nad 40, a proto každý třetí tah investuje
   (průměrně −1.64 za tah), přestože je jeho peněžní tok záporný.
5. **Chudá NPC (N6, N8, N9, N10) nemají z čeho žít.** Neformální příjem 0.6 až 0.9 za tah
   nepokryje nákup ropy a `goods`, a výchozí zásoby na 2 až 5 tahů vydrží jen do tahů 6 až 13.

### H2. Opravená chyba enginu (ne pravidla)

**Záporná síla.** Ve variantách (a) a (b) hlásila validace od tahu 53 zápornou sílu B. Údržba
paktu `protect` (2 síly za tah) a válka (10 sil za tah) sílu odečítaly bez dna. Síla má teď dno 0.
Co se má s paktem stát, když ochránci síla dojde, pravidla neurčují, viz I15.

### H.0 Scénář (0): nikdo netáhne

Hráči mlčí, žádné akce.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 45 | 15 | tah 45 bez pujcky, vynuceny boom |
| `euphoria` | 50 | 17 | cena oritu >= 20 |
| `overtrading` | 60 | 20 | pojistka cyklu: 10 tahu bez splneni prahu |
| `distress` | 70 | 24 | pojistka cyklu: 10 tahu bez splneni prahu |
| `panic` | 72 | 24 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 73 | 25 | po jednom tahu paniky |
| `depression` | 79 | 27 | 6 tahu po crash |
| `recovery` | 85 | 29 | 12 tahu po crash |

Pojistka cyklu: do `overtrading` v tahu 60, do `distress` v tahu 70. Nejvyšší tržní cena oritu: 140.00.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 88.05 | 733.6 | 0 | 0.80 | 1.50 | 1.24 | 1.05 | - |
| 12 | 58.49 | 740.8 | 4 | 0.78 | 1.09 | 0.84 | 1.06 | 10.37 |
| 30 | 27.17 | 718.6 | 8 | 0.83 | 1.00 | 0.84 | 1.05 | 7.00 |
| 45 | 23.25 | 667.8 | 7 | 0.89 | 0.96 | 0.84 | 1.05 | 7.00 |
| 60 | 14.93 | 656.0 | 8 | 0.99 | 0.95 | 0.84 | 1.05 | 87.18 |
| 90 | 6.43 | 671.1 | 10 | 1.13 | 0.80 | 0.84 | 1.05 | 4.28 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 5 | N1, N6, N8, N9, N10 |
| 30 | 8 | N1, N2, N4, N5, N6, N8, N9, N10 |
| 90 | 9 | N1, N2, N4, N6, N7, N8, N9, N10, N12 |

#### Unie

Zakladatelé (tah 73, den 25): **N1, N11, N6, N3**

| tah | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|
| 60 | 0 | - | 0 | - |
| 73 | 4 | N1, N11, N6, N3 | 0 | - |
| 90 | 1 | N11 | 3 | N3, N1, N8 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický prodej) | z toho goods (všichni) |
|---|---|---|---|
| 6 | 14.75 | 3.20 | 4.12 |
| 30 | 13.18 | 5.58 | 1.65 |
| 60 | 11.07 | 5.33 | 0.99 |
| 90 | 4.03 | 3.23 | 0.00 |

#### Zásoby světa (součet 14 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 327.1 | 130.5 | 83.5 | 262.1 | 0.0 |
| 30 | 177.7 | 105.5 | 90.9 | 127.4 | 89.9 |
| 60 | 165.6 | 115.5 | 88.9 | 127.4 | 60.0 |
| 90 | 158.7 | 116.4 | 60.1 | 117.5 | 40.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **86**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 118.3 | 93.9 | 76.4 | 264.0 |
| 60 | 134.5 | 34.4 | 2.0 | 406.2 |
| 90 | 95.6 | 0.0 | 1.1 | 509.9 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 29.44 | 6.0 / 17.64 | 2.0 / 4.94 | 1.0 / 0.99 | 7.1 / 6.30 |
| 30 | 8.1 / 1.40 | 6.0 / 4.50 | 0.5 / 0.00 | 0.5 / 0.00 | 7.6 / 2.00 |
| 60 | 6.9 / 0.89 | 6.0 / 4.50 | 0.5 / 0.00 | 0.5 / 0.00 | 7.6 / 2.00 |
| 90 | 3.9 / 0.07 | 6.0 / 4.50 | 0.5 / 0.00 | 0.5 / 0.00 | 9.4 / 9.30 |

### H.a Varianta (a): scénář ze zadání

A půjčuje N6 od tahu 8, B chrání N7, oba obchodují obilím.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 8 | 3 | prvni loan po displacementu |
| `euphoria` | 13 | 5 | cena oritu >= 20 |
| `overtrading` | 23 | 8 | pojistka cyklu: 10 tahu bez splneni prahu |
| `distress` | 33 | 11 | pojistka cyklu: 10 tahu bez splneni prahu |
| `panic` | 35 | 12 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 36 | 12 | po jednom tahu paniky |
| `depression` | 42 | 14 | 6 tahu po crash |
| `recovery` | 48 | 16 | 12 tahu po crash |

Pojistka cyklu: do `overtrading` v tahu 23, do `distress` v tahu 33. Nejvyšší tržní cena oritu: 140.00.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 88.39 | 733.6 | 0 | 0.80 | 1.50 | 1.24 | 1.05 | - |
| 12 | 71.02 | 718.5 | 2 | 1.07 | 1.07 | 0.84 | 1.08 | 13.91 |
| 30 | 28.32 | 738.9 | 8 | 0.99 | 1.05 | 0.84 | 1.05 | 140.00 |
| 45 | 26.88 | 736.6 | 7 | 0.56 | 0.94 | 0.84 | 1.05 | 3.50 |
| 60 | 25.82 | 748.6 | 6 | 0.56 | 0.90 | 0.84 | 1.05 | 3.50 |
| 90 | 12.83 | 820.7 | 9 | 0.56 | 0.81 | 0.94 | 1.05 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 3 | N8, N9, N10 |
| 30 | 7 | N1, N2, N4, N5, N8, N9, N10 |
| 90 | 8 | N3, N5, N6, N7, N8, N9, N10, N12 |

#### Unie

Zakladatelé (tah 36, den 12): **N6, N1, N11, N5**

| tah | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|
| 36 | 4 | N6, N1, N11, N5 | 0 | - |
| 60 | 3 | N11, N5, N1 | 2 | N6, N8 |
| 90 | 2 | N11, N1 | 2 | N6, N8 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický prodej) | z toho goods (všichni) |
|---|---|---|---|
| 6 | 14.75 | 8.00 | 4.12 |
| 30 | 24.03 | 11.27 | 4.53 |
| 60 | 8.93 | 8.74 | 1.30 |
| 90 | 1.24 | 10.74 | 0.48 |

#### Zásoby světa (součet 14 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 327.1 | 130.5 | 83.5 | 262.1 | 0.0 |
| 30 | 115.6 | 91.9 | 106.7 | 142.0 | 115.3 |
| 60 | 160.9 | 116.5 | 75.4 | 135.0 | 119.8 |
| 90 | 129.6 | 107.0 | 65.7 | 131.9 | 80.3 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **78**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 149.5 | 90.5 | 2.1 | 265.1 |
| 60 | 171.1 | 21.6 | 1.2 | 424.6 |
| 90 | 162.1 | 0.3 | 1.7 | 563.3 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 29.44 | 6.0 / 17.64 | 2.0 / 4.94 | 1.0 / 0.99 | 7.1 / 6.30 |
| 30 | 7.5 / 1.09 | 6.0 / 4.50 | 1.3 / 0.00 | 1.0 / 1.76 | 7.6 / 2.00 |
| 60 | 4.5 / 0.15 | 6.0 / 4.50 | 0.5 / 0.00 | 0.5 / 0.10 | 7.6 / 2.00 |
| 90 | 1.5 / 0.00 | 6.0 / 4.50 | 0.6 / 0.56 | 0.5 / 0.00 | 9.2 / 9.10 |

### H.b Varianta (b): realistické půjčování

Hráč půjčí jen v tahu, kdy NPC žádá půjčku nebo má deficit oritu, nejvýš jedna půjčka na hráče a tah.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 9 | 3 | prvni loan po displacementu |
| `euphoria` | 14 | 5 | cena oritu >= 20 |
| `overtrading` | 23 | 8 | dluhy NPC > 40 % jejich wealth |
| `distress` | 24 | 8 | prvni nesplaceni |
| `panic` | 25 | 9 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 26 | 9 | po jednom tahu paniky |
| `depression` | 32 | 11 | 6 tahu po crash |
| `recovery` | 38 | 13 | 12 tahu po crash |

Pojistka cyklu: nezasáhla. Nejvyšší tržní cena oritu: 79.91.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 88.39 | 733.6 | 0 | 0.80 | 1.50 | 1.24 | 1.05 | - |
| 12 | 72.40 | 708.1 | 2 | 1.02 | 1.06 | 0.84 | 1.08 | 13.69 |
| 30 | 27.16 | 553.1 | 7 | 0.56 | 1.00 | 0.84 | 1.05 | 2.10 |
| 45 | 31.84 | 546.6 | 5 | 0.56 | 0.92 | 0.84 | 1.05 | 3.50 |
| 60 | 26.36 | 550.3 | 6 | 0.56 | 0.89 | 0.90 | 1.05 | 3.50 |
| 90 | 17.47 | 621.7 | 9 | 0.56 | 0.86 | 0.84 | 1.10 | 4.32 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 1 | N6 |
| 30 | 6 | N1, N2, N5, N6, N8, N10 |
| 90 | 9 | N2, N3, N4, N5, N6, N7, N9, N10, N12 |

#### Unie

Zakladatelé (tah 26, den 9): **N6, N1, N8, N5**

| tah | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|
| 26 | 4 | N6, N1, N8, N5 | 0 | - |
| 60 | 0 | - | 0 | - |
| 90 | 0 | - | 0 | - |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický prodej) | z toho goods (všichni) |
|---|---|---|---|
| 6 | 14.75 | 8.00 | 4.12 |
| 30 | 16.50 | 7.95 | 2.74 |
| 60 | 8.92 | 13.38 | 3.15 |
| 90 | 0.07 | 12.18 | 0.00 |

#### Zásoby světa (součet 14 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 327.1 | 130.5 | 83.5 | 262.1 | 0.0 |
| 30 | 194.8 | 95.7 | 111.0 | 146.9 | 120.5 |
| 60 | 188.8 | 122.7 | 101.0 | 137.8 | 93.8 |
| 90 | 133.2 | 140.3 | 102.8 | 115.2 | 60.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **68**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 163.6 | 107.0 | 3.1 | 78.7 |
| 60 | 219.6 | 38.0 | 27.4 | 156.6 |
| 90 | 270.9 | 0.1 | 49.3 | 249.6 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 29.44 | 6.0 / 17.64 | 2.0 / 4.94 | 1.0 / 0.99 | 7.1 / 6.30 |
| 30 | 7.4 / 1.02 | 6.0 / 4.50 | 1.8 / 0.00 | 0.5 / 0.00 | 7.6 / 2.00 |
| 60 | 4.5 / 0.11 | 6.0 / 4.50 | 1.2 / 0.00 | 0.5 / 0.00 | 7.6 / 2.00 |
| 90 | 4.4 / 0.39 | 6.0 / 4.50 | 1.5 / 4.05 | 0.5 / 0.00 | 7.6 / 3.81 |

### H3. Co z běhů plyne

1. **Varianta (b) poprvé splnila všechna kritéria:** crash v tahu 26 (den 9), Unie se čtyřmi
   zakladateli, validace bez chyb.
2. **Varianta (a) minula okno o jeden den** (crash v tahu 36, den 12). `distress` v ní přišel
   přes pojistku cyklu, tedy deset tahů po `overtrading`; jediný věřitel sám nesplácení nevyvolá.
3. **Převratů dál ubylo:** 86, 78 a 68 za 90 tahů proti 99 až 112 ve v1.2.
4. **Index zůstává daleko od prahu 70.** V tahu 90 je 6.43 (0), 12.83 (a) a 17.47 (b). Hlavní brzdou
   je počet NPC v bídě a koncentrace bohatství u hráčů, ne jeho celkový úbytek.

---

## I. Nově otevřené otázky z implementace v1.3

Neopravuji je, engine u každé používá uvedený výklad. Nejdůležitější jsou I13 a I1,
protože vysvětlují většinu pádů ve scénáři (0).

### I13. Hráči na trhu jen prodávají

> **Vyřešeno v1.4 (4.1a): hráči na trhu i nakupují.**

Rozhodnutí pouští do automatického trhu přebytky hráčů jako nabídku, ale nákup hráčů neupravuje.
**Výklad enginu:** hráči prodávají, nekupují. Peníze NPC proto na trhu tečou jedním směrem, k A a B.
Hráč s vlastním deficitem se navíc na trhu nezásobí: A potřebuje obilí za 6.9 za tah, vlastní
efektivní produkce je 3.9, a bez `trade_offer` jen čerpá zásobu a pak platí pokutu.
**Otázka:** mají hráči na trhu i nakupovat?

### I1. Kupec nejdřív čerpá vlastní zásobu

> **Vyřešeno v1.4 (4.1c): nedotknutelná rezerva, kupec poptává deficit toku a doplnění rezervy.**

„Deficit se kryje nejdřív ze zásoby“ platí pro pokutu; pro trh není jisté, zda kupec nakupuje až
po vyčerpání zásoby, nebo nakupuje, aby zásobu udržel. **Výklad enginu:** doslovně, nakupuje až to,
co zásoba nepokryje. Důsledek: dokud mají sousedé zásoby, prodejci svůj přebytek neprodají
(N1 ve (0) prodává za 0.13 za tah a zásoba obilí mu roste).

### I2. Kolik prodejce nabízí

> **Potvrzeno 15. 9. 2026, zapsáno do pravidel v1.4 (4.1a).**

**Výklad enginu:** nabídka = zásoba + bilance tahu − 3 × spotřeba. Prodává se tedy i starší zásoba
nad rezervu tří tahů, nejen přebytek tohoto tahu.

### I3. Počítá se zásoba do vstupů pro průmysl?

> **Potvrzeno 15. 9. 2026, zapsáno do pravidel v1.4 (4.0).**

**Výklad enginu:** ano. Dostupná ropa a kovy pro `coverage` zahrnují zásobu, domácnosti mají dál
přednost.

### I4. Z jaké spotřeby se počítají výchozí zásoby

> **Potvrzeno 15. 9. 2026, zapsáno do pravidel v1.4 (4.1c).**

Rozhodnutí určuje zásoby v tazích spotřeby, ale spotřeba ropy a kovů závisí na výrobě `goods`,
a ta na obchodu. **Výklad enginu:** spotřeba podle 4.0 při výrobě jen z vlastních surovin, bez
obchodu a bez zásob. Hodnoty jsou zapsané ve `state.json`.

### I5. Padlé říše začínají nad stropem

> **Potvrzeno 15. 9. 2026, zapsáno do pravidel v1.4 (4.1c).**

Výchozí zásoba padlých říší je 12 tahů spotřeby, strop 10 tahů. **Výklad enginu:** strop omezuje
jen přidávání; zásoba nad stropem se nekrátí a spotřebovává se normálně.

### I6. Deficit obilí pro bídu

> **Potvrzeno 15. 9. 2026, zapsáno do pravidel v1.4 (4.3).**

Bída nastává i při deficitu obilí aspoň 3 (4.3). **Výklad enginu:** počítá se deficit, který
nepokryje ani zásoba.

### I7. Stejná sféra u prodejce, který je hráčem

> **Potvrzeno 15. 9. 2026, zapsáno do pravidel v1.4 (4.1a).**

Pořadí párování dává přednost dvojicím ve stejné sféře. **Výklad enginu:** prodejce A a kupec
ve `sphere_A` (u B obdobně) jsou ve stejné sféře.

### I8. Výroba `goods` dál počítá s `pop / 100`

> **Vyřešeno v1.4 (4.0): výroba `goods` s `pop / pop_start`.**

Rozhodnutí mění efektivní produkci surovin na `pop / pop_start`, vzorec výroby `goods` v 4.0
ponechává `pop / 100`. **Výklad enginu:** doslovně. Stát s velkým obyvatelstvem (A 230, N1 190)
má proto vyšší potenciál továren i vyšší průmyslovou potřebu vstupů.
**Otázka:** má i výroba `goods` přejít na `pop / pop_start`?

### I9. Vidí hráči zásoby?

> **Vyřešeno v1.4 (2): hráč vidí vlastní `stock`, cizí ne.**

Pravidla viditelnost `stock` neurčují. **Výklad enginu:** do pohledů hráčů se nepřidávají.

### I10. Vnitřní trh Unie a zásoby

> **Potvrzeno 15. 9. 2026, zapsáno do pravidel v1.4 (7.2).**

**Výklad enginu:** vnitřní trh Unie (7.2) sdílí jen tok tahu, ne zásoby, a orit dál zahrnuje;
výjimka „orit mimo trh“ se týká jen 4.1a.

### I11. Dno průmyslu se netýká padlých říší

> **Vyřešeno v1.4 (4.2c): dno 0.5 platí i pro padlé říše.**

Rozhodnutí dává dno 0.5 hráčům a běžným NPC. **Výklad enginu:** padlé říše mohou klesnout k nule
a z nuly se samy nedostanou (G14 u nich trvá).

### I12. Výklad kritérií scénáře (0)

> **Potvrzeno 15. 9. 2026, zapsáno do pravidel v1.4 (11).**

**Výklad testu:** „do tahu 15 nejvýš dvě NPC v bídě“ = počet různých NPC, která byla v bídě
v kterémkoli tahu 1 až 15 (stejně se čte „žádné z N1 až N5, N7, N11, N12“). „Do tahu 90 nejvýš
5 NPC“ = nejvyšší počet NPC v bídě v jednom tahu. Tabulka H vypisuje obě míry.

### I14. Unie jako zdroj oritu

> **Vyřešeno v1.4 (4.1a): Unie orit neprodává.**

4.1a říká, že NPC získá orit akcí `trade_offer` od hráče nebo Unie. Unie ale nemá výrobu ani zásoby,
takže orit prodat nemůže. **Otázka:** má to tak zůstat?

### I15. Pakt, když ochránci dojde síla

> **Vyřešeno v1.4 (3.2): pakt při nulové síle ochránce zaniká.**

Údržba paktu stojí 2 síly za tah. **Výklad enginu:** síla hráče má dno 0 a pakt dál platí; chráněné
NPC tak dostává +2 síly za tah i od ochránce bez síly. **Otázka:** má se pakt při nulové síle zrušit?

---

## J. Testy pravidel v1.4 (15. 9. 2026)

### Souhrn

| scénář | kritérium | výsledek |
|---|---|---|
| (0) nikdo netáhne | do tahu 15 nejvýš dvě NPC v bídě | **neprošlo**, 3 NPC: N6, N8, N10 |
| (0) | do tahu 15 v bídě žádné z N1 až N5, N7, N11, N12 | prošlo, žádné |
| (0) | `W_real` v tahu 30 aspoň 90 % startu | prošlo, 144.0 % z 717 |
| (0) | do tahu 90 nejvýš 5 NPC v bídě | **neprošlo**, nejvíc 6 najednou (tah 46: N2, N4, N5, N7, N8, N10), různých za běh 8 |
| (a) scénář ze zadání | crash mezi dnem 7 a 11 | prošlo, tah 32, den 11 |
| (a) | Unie s aspoň 3 zakladateli | **neprošlo**, nevznikla, souvislou skupinu tvořila jen 2 NPC |
| (a) | validate 0 chyb | prošlo |
| (b) realistické půjčování | crash mezi dnem 7 a 11 | prošlo, tah 25, den 9 |
| (b) | Unie s aspoň 3 zakladateli | prošlo, N1, N6, N8, N5 (tah 25) |
| (b) | validate 0 chyb | prošlo |

Validace hlásí 0 chyb ve všech třech scénářích a všech 90 tazích. Výchozí zásoby jsem podle
potvrzeného I4 přepočítal s novou produkcí chudých NPC a novým vzorcem výroby `goods`; vyšly
beze změny, protože výrobu `goods` všech států při výpočtu bez obchodu omezuje ropa, ne potenciál
továren. Chyby enginu tentokrát testy neodhalily.

### J1. Scénář (0) neprošel těsně: proč NPC padají

Nekalibroval jsem. Scénář (0) minul obě kritéria bídy o jedno NPC: do tahu 15 byla v bídě tři
místo dvou (všechna chudá, žádné chráněné) a v nejhorším tahu šest místo pěti. Rozpis je průměr
za tah od začátku do prvního tahu v bídě; „ostatní“ je všude nulové, účty se uzavírají.

| NPC | v bídě od | tahů v bídě | prodej | nákup | z toho doplnění rezervy | pokuty | příjem 4.2b | investice 4.2a | průzkum | ostatní | **čistě** | pokuty podle statku (součet) | zásoby grain / goods / oil: start → pád |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N8 | tah 3 | 88 | +0.00 | -3.64 | -1.87 | -0.45 | +1.33 | +0.00 | +0.00 | +0.00 | **-2.75** | oil 1.4 | 4.8 / 3.2 / 1.6 → 12.6 / 4.8 / 0.0 |
| N6 | tah 5 | 47 | +0.87 | -3.23 | -1.08 | -0.65 | +1.50 | +0.00 | +0.00 | -0.00 | **-1.51** | oil 3.2 | 5.4 / 3.6 / 1.8 → 8.1 / 5.4 / 0.0 |
| N10 | tah 12 | 79 | +0.20 | -1.49 | +0.00 | -0.64 | +1.42 | +0.00 | -0.33 | -0.00 | **-0.85** | oil 7.6 | 12.8 / 8.5 / 4.2 → 21.7 / 8.5 / 0.0 |
| N2 | tah 16 | 75 | +1.65 | -3.98 | +0.00 | -1.20 | +2.67 | +0.00 | -0.88 | -0.00 | **-1.74** | oil 19.2 | 38.4 / 25.6 / 12.8 → 48.0 / 12.8 / 0.0 |
| N7 | tah 16 | 47 | +1.42 | -3.15 | -0.15 | -0.80 | +1.83 | +0.00 | -0.75 | +0.00 | **-1.45** | oil 12.9 | 16.5 / 11.0 / 5.5 → 16.5 / 17.8 / 0.0 |
| N4 | tah 36 | 17 | +3.70 | -4.00 | -0.27 | +0.00 | +1.83 | -1.22 | -1.44 | +0.00 | **-1.13** | - | 26.4 / 17.6 / 8.8 → 10.2 / 22.0 / 26.6 |
| N5 | tah 46 | 2 | +2.98 | -3.89 | -0.50 | +0.00 | +1.67 | -0.17 | -1.13 | -0.00 | **-0.55** | - | 24.0 / 16.0 / 8.0 → 9.0 / 20.0 / 3.5 |
| N11 | tah 84 | 7 | +0.00 | -1.66 | -1.07 | +0.00 | +0.83 | +0.00 | +0.00 | -0.09 | **-0.92** | - | 18.0 / 12.0 / 16.8 → 18.0 / 12.0 / 0.0 |

Co z rozpisu plyne:

1. **Hlavní ztrátou chudých NPC je nákup ropy a doplňování rezervy.** N8 a N6 platí za nákup 3.2
   až 3.6 za tah, z toho 1.1 až 1.9 za doplnění rezervy, zatímco neformální příjem je 1.3 až 1.5.
   Pokuty jsou u všech padajících NPC nejvýš 1.2 za tah a skoro celé za ropu.
2. **Doplnění rezervy srazí chudá NPC do bídy (K2).** Rezerva se doplňuje, dokud má stát `wealth`
   nad 10, ale hranice bídy je 15. N8 tak nakupuje do rezervy i s bohatstvím mezi 10 a 15 a v bídě
   zůstane 88 z 90 tahů, N10 79 a N2 75.
3. **Ropa je jediný statek, za který padající NPC platí pokuty.** U všech pěti NPC s pokutami
   (N8, N6, N10, N2, N7) jde celá pokuta za ropu a jejich zásoba ropy je v tahu pádu nulová.
   NPC bez pokut (N4, N5, N11) padají čistě na tom, že nakupují víc, než prodají a vydělají.
4. **Tok peněz k hráčům se zmenšil, ale nezmizel.** Za prvních 30 tahů zůstalo NPC jako celku
   saldo −164, hráčům +108 (A) a +56 (B), při obratu přes 1 300. Ve v1.3 šel tok jedním směrem.

### J2. Toky peněz ve scénáři (0), tahy 1 až 30

| účastník | prodal | nakoupil | saldo |
|---|---|---|---|
| A | 471.5 | 363.5 | +108.0 |
| B | 146.8 | 90.5 | +56.4 |
| NPC celkem | 759.1 | 923.5 | -164.4 |

### J.0 Scénář (0): nikdo netáhne

Hráči mlčí, žádné akce. Toky peněz jsou v J2.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 45 | 15 | tah 45 bez pujcky, vynuceny boom |
| `euphoria` | 50 | 17 | cena oritu >= 20 |
| `overtrading` | 58 | 20 | pojistka cyklu: 8 tahu bez splneni prahu |
| `distress` | 66 | 22 | pojistka cyklu: 8 tahu bez splneni prahu |
| `panic` | 68 | 23 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 69 | 23 | po jednom tahu paniky |
| `depression` | 75 | 25 | 6 tahu po crash |
| `recovery` | 81 | 27 | 12 tahu po crash |

Pojistka cyklu: do `overtrading` v tahu 58, do `distress` v tahu 66. Nejvyšší tržní cena oritu: 129.77. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 89.34 | 744.8 | 0 | 0.79 | 1.49 | 0.97 | 1.05 | - |
| 12 | 72.20 | 837.8 | 3 | 0.77 | 1.23 | 0.84 | 1.05 | 10.97 |
| 30 | 70.66 | 1032.4 | 4 | 0.72 | 1.08 | 0.84 | 1.05 | 7.00 |
| 45 | 73.74 | 1186.4 | 4 | 0.73 | 1.12 | 0.95 | 1.05 | 7.00 |
| 60 | 75.33 | 1335.0 | 4 | 0.74 | 1.09 | 0.94 | 1.05 | 73.25 |
| 90 | 64.44 | 1474.9 | 5 | 0.76 | 1.01 | 0.87 | 1.05 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 3 | N6, N8, N10 |
| 30 | 4 | N2, N7, N8, N10 |
| 90 | 5 | N2, N6, N8, N10, N11 |

#### Unie

Zakladatelé (tah 69, den 23): **N1, N11, N6, N5**

| tah | vztah k založení | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|---|
| 60 | tah 60 | 0 | - | 0 | - |
| 69 | vznik | 4 | N1, N11, N6, N5 | 0 | - |
| 75 | +6 tahů | 3 | N1, N11, N5 | 3 | N7, N8, N6 |
| 87 | +18 tahů | 2 | N1, N5 | 3 | N7, N8, N6 |
| 90 | tah 90 | 2 | N1, N5 | 3 | N7, N8, N6 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) |
|---|---|---|---|
| 6 | 11.25 | 38.30 | 11.92 |
| 30 | 5.93 | 32.37 | 9.44 |
| 60 | 5.70 | 26.66 | 4.66 |
| 90 | 3.63 | 26.43 | 3.02 |

#### Zásoby světa (součet 14 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 328.1 | 142.0 | 92.0 | 237.7 | 0.0 |
| 30 | 266.5 | 79.1 | 134.8 | 256.7 | 137.1 |
| 60 | 240.3 | 74.9 | 143.2 | 261.0 | 100.0 |
| 90 | 233.1 | 61.7 | 120.9 | 261.0 | 100.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **51**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 88.1 | 75.4 | 323.0 | 241.4 |
| 60 | 102.5 | 87.2 | 396.4 | 362.2 |
| 90 | 11.1 | 89.2 | 380.4 | 489.3 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 12.80 | 6.0 / 8.40 | 2.0 / 2.60 | 1.0 / 1.10 | 7.1 / 12.60 |
| 30 | 10.0 / 20.00 | 6.0 / 8.40 | 2.3 / 0.00 | 0.5 / 0.00 | 7.4 / 2.00 |
| 60 | 10.0 / 20.00 | 6.0 / 8.40 | 2.3 / 0.00 | 0.5 / 0.00 | 7.4 / 2.00 |
| 90 | 10.0 / 20.00 | 6.0 / 8.40 | 3.2 / 2.80 | 0.5 / 0.00 | 6.7 / 1.22 |

### J.a Varianta (a): scénář ze zadání

A půjčuje N6 od tahu 8, B chrání N7, oba obchodují obilím.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 8 | 3 | prvni loan po displacementu |
| `euphoria` | 13 | 5 | cena oritu >= 20 |
| `overtrading` | 21 | 7 | pojistka cyklu: 8 tahu bez splneni prahu |
| `distress` | 29 | 10 | pojistka cyklu: 8 tahu bez splneni prahu |
| `panic` | 31 | 11 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 32 | 11 | po jednom tahu paniky |
| `depression` | 38 | 13 | 6 tahu po crash |
| `recovery` | 44 | 15 | 12 tahu po crash |

Pojistka cyklu: do `overtrading` v tahu 21, do `distress` v tahu 29. Nejvyšší tržní cena oritu: 129.77. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 89.34 | 744.8 | 0 | 0.79 | 1.49 | 0.97 | 1.05 | - |
| 12 | 85.25 | 828.8 | 1 | 1.07 | 1.12 | 0.84 | 1.05 | 13.27 |
| 30 | 71.15 | 951.5 | 3 | 0.98 | 1.10 | 0.84 | 1.05 | 129.77 |
| 45 | 56.29 | 976.3 | 4 | 0.69 | 1.07 | 0.84 | 1.05 | 3.50 |
| 60 | 72.38 | 1153.8 | 2 | 0.67 | 1.15 | 0.84 | 1.05 | 3.50 |
| 90 | 56.22 | 1439.3 | 4 | 0.64 | 1.13 | 0.85 | 1.05 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 0 | - |
| 30 | 3 | N2, N4, N10 |
| 90 | 4 | N5, N8, N10, N12 |

#### Unie

**Unie nevznikla** v tahu 32. Způsobilých bylo 6 (N10, N2, N4, N5, N11, N12), ale tvořila 4 oddělené skupiny o velikostech 2, 2, 1, 1; největší souvislá skupina (N10, N2) nesplní minimum tří zakladatelů.

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) |
|---|---|---|---|
| 6 | 21.61 | 30.97 | 12.56 |
| 30 | 14.44 | 29.57 | 10.83 |
| 60 | 9.39 | 31.56 | 10.00 |
| 90 | 5.32 | 33.24 | 8.70 |

#### Zásoby světa (součet 14 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 328.1 | 142.0 | 92.0 | 237.7 | 0.0 |
| 30 | 138.3 | 86.5 | 149.9 | 271.6 | 155.2 |
| 60 | 183.2 | 79.2 | 150.3 | 277.1 | 160.0 |
| 90 | 187.0 | 50.6 | 136.3 | 278.2 | 160.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **35**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 65.9 | 82.8 | 150.0 | 302.2 |
| 60 | 64.1 | 79.2 | 34.0 | 504.2 |
| 90 | 37.7 | 10.9 | 65.2 | 684.1 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 12.80 | 6.0 / 8.40 | 2.0 / 2.60 | 1.0 / 1.10 | 7.1 / 12.60 |
| 30 | 10.0 / 20.00 | 6.0 / 8.40 | 2.3 / 0.00 | 0.7 / 0.00 | 7.4 / 2.00 |
| 60 | 10.0 / 19.74 | 6.0 / 8.40 | 2.3 / 0.00 | 0.7 / 0.00 | 7.4 / 2.00 |
| 90 | 10.0 / 19.74 | 6.0 / 8.40 | 2.3 / 0.00 | 0.7 / 0.00 | 7.4 / 6.53 |

### J.b Varianta (b): realistické půjčování

Hráč půjčí jen v tahu, kdy NPC žádá půjčku nebo má deficit oritu, nejvýš jedna půjčka na hráče a tah.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 9 | 3 | prvni loan po displacementu |
| `euphoria` | 14 | 5 | cena oritu >= 20 |
| `overtrading` | 22 | 8 | pojistka cyklu: 8 tahu bez splneni prahu |
| `distress` | 23 | 8 | prvni nesplaceni |
| `panic` | 24 | 8 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 25 | 9 | po jednom tahu paniky |
| `depression` | 31 | 11 | 6 tahu po crash |
| `recovery` | 37 | 13 | 12 tahu po crash |

Pojistka cyklu: do `overtrading` v tahu 22. Nejvyšší tržní cena oritu: 66.59. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 89.34 | 744.8 | 0 | 0.79 | 1.49 | 0.97 | 1.05 | - |
| 12 | 80.89 | 822.6 | 2 | 1.01 | 1.12 | 0.84 | 1.05 | 14.25 |
| 30 | 51.02 | 739.6 | 5 | 0.56 | 1.09 | 0.84 | 1.05 | 2.10 |
| 45 | 68.79 | 928.8 | 4 | 0.56 | 1.13 | 0.88 | 1.05 | 3.50 |
| 60 | 75.82 | 1099.3 | 4 | 0.58 | 1.09 | 0.84 | 1.05 | 3.50 |
| 90 | 68.63 | 1375.4 | 4 | 0.76 | 1.06 | 0.84 | 1.05 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 1 | N1 |
| 30 | 5 | N1, N6, N7, N8, N10 |
| 90 | 4 | N1, N6, N8, N10 |

#### Unie

Zakladatelé (tah 25, den 9): **N1, N6, N8, N5**

| tah | vztah k založení | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|---|
| 25 | vznik | 4 | N1, N6, N8, N5 | 0 | - |
| 31 | +6 tahů | 1 | N5 | 2 | N8, N6 |
| 43 | +18 tahů | 1 | N5 | 1 | N6 |
| 60 | tah 60 | 1 | N5 | 1 | N6 |
| 90 | tah 90 | 1 | N5 | 1 | N6 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) |
|---|---|---|---|
| 6 | 21.61 | 30.97 | 12.56 |
| 30 | 7.52 | 32.06 | 10.92 |
| 60 | 8.23 | 26.07 | 4.87 |
| 90 | 12.72 | 26.89 | 4.85 |

#### Zásoby světa (součet 14 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 328.1 | 142.0 | 92.0 | 237.7 | 0.0 |
| 30 | 216.6 | 89.4 | 153.2 | 272.0 | 143.0 |
| 60 | 206.1 | 83.1 | 148.6 | 285.9 | 120.0 |
| 90 | 188.8 | 59.5 | 138.7 | 292.4 | 120.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **46**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 114.2 | 98.4 | 88.0 | 140.9 |
| 60 | 130.7 | 111.2 | 105.9 | 321.3 |
| 90 | 90.7 | 113.1 | 69.4 | 494.4 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 12.80 | 6.0 / 8.40 | 2.0 / 2.60 | 1.0 / 1.10 | 7.1 / 12.60 |
| 30 | 10.0 / 20.00 | 6.0 / 8.40 | 1.3 / 0.00 | 0.5 / 0.00 | 7.4 / 2.00 |
| 60 | 10.0 / 20.00 | 6.0 / 8.40 | 0.5 / 0.00 | 0.5 / 0.00 | 7.4 / 2.00 |
| 90 | 10.0 / 20.00 | 6.0 / 8.40 | 0.5 / 0.00 | 0.5 / 0.00 | 7.4 / 2.00 |

### J3. Co z běhů plyne

1. **Index se poprvé dostal k prahu vítězství.** V tahu 60 je 75.33 (0), 72.38 (a) a 75.82 (b), v tahu 90
   64.44, 56.22 a 68.63. Proti v1.3 (6 až 17) je to zlom: obchod oběma směry a příjem `pop / 60` udrží
   většinu světa mimo bídu.
2. **Varianta (b) splnila všechna kritéria** (crash den 9, Unie se čtyřmi zakladateli).
3. **Varianta (a) splnila okno crashe (den 11), ale Unie nevznikla** kvůli souvislosti území
   z pravidla 7.1: způsobilá NPC tvořila čtyři oddělené skupiny, největší o dvou státech (K9).
4. **Unie se rozpadá převraty.** Ve (b) má za 6 tahů po vzniku jediného člena, ve (0) za 18 tahů
   dva. Kandidatura převrat přežije, členství ne (K10).
5. **Převratů dál ubylo:** 51, 35 a 46 za 90 tahů proti 68 až 86 ve v1.3. Žádný pakt nezanikl.

---

## K. Nově otevřené otázky z implementace v1.4

Neopravuji je, engine u každé používá uvedený výklad. Nejdůležitější jsou K2 a K9: K2 rozhoduje
o chudých NPC ve scénáři (0), K9 o kritériu Unie ve variantě (a).

### K2. Doplňování rezervy pod hranicí bídy

Rezerva se doplňuje „pokud `wealth > 10`“, hranice bídy je 15. **Výklad enginu:** deficit toku smí
stát pokrýt celým bohatstvím, doplnění rezervy jen z bohatství nad 10. Důsledek: chudé NPC s bohatstvím
mezi 10 a 15 dál nakupuje do rezervy a drží se v bídě (N8 ve (0) 88 z 90 tahů).
**Otázka:** zvednout práh doplnění na 15, nebo doplnění v bídě pozastavit?

### K9. Unie a souvislost území

Ve variantě (a) bylo v tahu krachu způsobilých šest NPC (N10, N2, N4, N5, N11, N12), ale tvořila
čtyři oddělené skupiny o velikostech 2, 2, 1 a 1. Pravidlo 7.1 žádá souvislé území a minimum tří
zakladatelů, Unie proto nevznikla a kritérium (a) neprošlo. **Otázka:** má se při rozdělení na
malé skupiny dovolit spojení přes jednoho souseda, nebo je nevznik Unie v takové situaci záměr?

### K1. Obchodují A a B spolu na trhu?

Hráči jsou pro trh sousedy všech NPC. **Výklad enginu:** navzájem sousedy nejsou, takže A a B spolu
na automatickém trhu neobchodují; mezi sebou mají jen `trade_offer`, a ta míří na NPC.

### K3. Stejná sféra, když nakupuje hráč

I7 řeší prodejce-hráče. **Výklad enginu:** symetricky i pro kupce-hráče, tedy NPC ve `sphere_A`
prodávající hráči A je ve stejné sféře.

### K4. Kdy se měří růst bohatství pro 4.2a

**Výklad enginu:** porovnává se bohatství v okamžiku investice (po obchodu, pokutách a příjmu
tohoto tahu) s bohatstvím na konci tahu o tři tahy dříve.

### K5. Platí v 4.2a dál `law ≥ 5`?

Rozhodnutí formuluje podmínku jako „`wealth > 40` a `wealth` za poslední 3 tahy vzrostlo“.
**Výklad enginu:** nová podmínka doplňuje původní, `law ≥ 5` zůstává.

### K6. Kdy přesně pakt zaniká

**Výklad enginu:** srazí-li údržba paktu sílu ochránce na 0, pakt v tomto tahu ještě působí a pak
zanikne. Klesne-li síla na 0 jinak (bída, válka), pakt zanikne při nejbližší údržbě.

### K7. Status kandidáta po převratu

Převrat nastavuje `status = independent`. **Výklad enginu:** kandidát, jehož kandidatura převrat
přežije, má dál `status = candidate`.

### K8. Rezerva oritu

Rezerva platí pro „každý statek“, orit se ale na trhu nekupuje, takže ho do rezervy doplnit nejde.
**Výklad enginu:** orit do nabídky ani poptávky automatického trhu nevstupuje vůbec, rezerva oritu
se tedy nedoplňuje a zásoba oritu se jen tvoří z vlastní těžby a čerpá spotřebou.

### K10. Unie se rozpadá dřív, než stihne táhnout

Ve (b) klesne Unie za šest tahů po vzniku ze čtyř členů na jednoho, protože členům padají vlády
a převrat členství ruší. Není to nesrovnalost, pravidla 4.3 a 7.4 jsou jasná. Uvádím to, protože
Unie s jedním členem nemá vnitřní trh ani sílu, a tak ztrácí roli, kterou jí dávají tajné cíle.

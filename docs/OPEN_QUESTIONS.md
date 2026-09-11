# Otevřené otázky

Nalezené nesrovnalosti mezi `docs/pravidla.md` a datovými soubory (`npc.json`, `state.json`),
plus místa, kde pravidla nedourčují chování, které engine potřebuje.

Design je zamčený, nic z toho neopravuji sám. U každé položky je uvedeno, jakou
nejkonzervativnější interpretaci engine zatím používá, aby běh nebyl blokován.

Stav ke dni: 11. 9. 2026, před prvním ostrým tahem.

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

**Zatímní interpretace:** hráč se do `n_bída` započítává (index by jinak nesouhlasil s dělitelem 14),
efekty bídy `pop −3` a `power −1` se na něj vztahují, ale pád vlády se u hráče neprovádí.
Engine si `poverty_streak` a `coups` u hráčů drží ve stejně pojmenovaných polích, která
do `state.json` doplní při prvním zápisu.

### A2. Unie má zároveň `wealth` i `fund`

Pravidlo 7.2 říká doslova "Fond (`wealth` C) = 10 % `wealth` každého člena při vstupu".
Podle toho jsou fond a bohatství Unie totéž. `state.json` má ale obě pole zvlášť,
obě nastavená na 0, a není určeno, které je zdrojem pravdy.

**Otázka:** Je `fund` jen zrcadlo `wealth`, nebo dvě oddělené kapsy?

**Zatímní interpretace:** `wealth` je zdroj pravdy, `fund` se na konci každého tahu přepíše
na stejnou hodnotu. Akce `union_fund` čerpá z `wealth`.

### A3. Unie nemá `prod`, `need`, `pop`, `occupied`

Unie je v části 7.2 plnohodnotný hráč, ale nemá vlastní produkci ani obyvatelstvo,
protože ty zůstávají členům (vnitřní trh v 7.2). Pravidlo 8 přitom počítá `W_real` jako
"součet `wealth` všech států".

**Otázka:** Započítává se fond Unie do `W_real`? A je Unie "aktér" pro `max_share`,
tedy může svou velikostí index srážet stejně jako velmoc?

**Zatímní interpretace:** fond Unie se do `W_real` **nezapočítává** (prostředky pocházejí
z bohatství členů, které se počítá u nich, započtení by je zdvojilo) a Unie **není** aktér
pro `max_share`. Obojí je volba ve prospěch vyššího indexu, tedy mírnější, a právě index
rozhoduje verdikt "všichni vyhráli / všichni prohráli". Stojí za potvrzení.

### A4. Hráči nemají `status`

Tabulka v části 2 uvádí `status` jako pole "každého státu", ale hodnoty
(`independent`, `sphere_X`, `occupied_X`, `union`, `candidate`) dávají smysl jen u NPC.

**Zatímní interpretace:** hráči status nemají, engine ho u nich nečte ani nezapisuje.

---

## B. Nedourčené struktury

### B1. Formát `minsky.defaults`

Pravidlo 4.5 říká, že nesplácení se zapisuje do `defaults`. Pravidlo 5 pak potřebuje dvě
různá čtení téhož pole: přechod na `distress` při "prvním nesplácení" a na `panic` při
"druhém nesplácení" (globálně, napříč světem), a ve fázi `crash` se ptá, které NPC nesplácelo
konkrétnímu věřiteli X ("má záznam v `defaults` vůči X").

**Zatímní interpretace:** `defaults` je seznam záznamů `{"turn": N, "npc": "N6", "creditor": "A"}`,
jeden za každou dvojici dlužník a věřitel a tah. Počítadlo pro fázi bere počet **tahů**,
ve kterých došlo aspoň k jednomu nesplácení, ne počet záznamů. Jinak by jediný tah,
kdy nesplácejí tři NPC, přeskočil `distress` rovnou do `panic`.

### B2. Formát `deals`, `invasions`, `messages_pending`, `news`, `log`

Všechna pole jsou na startu prázdná a schéma není nikde popsané. Akce `cancel` přitom
bere `deal_id`, takže obchody, pakty i sankce musí mít stabilní identifikátor.

**Zatímní interpretace:** engine používá jednotný seznam `deals` se záznamy
`{"id": "d7", "type": "trade|protect|pressure", "owner": "A", "target": "N6", ...}`.
Identifikátor je `d` plus pořadové číslo, nikdy se nerecykluje. Schéma je popsané
v hlavičce `engine.py`.

### B3. `meta.slot`

Část 3 popisuje tři tahy denně (7:00, 13:00, 20:00), ale `slot` je `null` a číselník chybí.

**Zatímní interpretace:** `slot` je 1, 2, 3 pro ráno, poledne, večer. Den je `((turn - 1) // 3) + 1`,
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

**Zatímní interpretace:** dva dárci za tah, vybraní deterministicky z NPC bez oritu
přes `random.Random(rng_seed + turn)`, s vyloučením padlých říší (7a jsou uzavřené)
a států s `pop ≤ 0`. Součet `pop` světa tak zůstává zachovaný, což vyžaduje `validate.py`.

Slovo "dočasně" u `prod.grain −0.5` nemá určenou dobu trvání. Engine ho bere jako "dokud se
migrant nevrátí", tedy do fáze `crash`, kde pravidlo 5 říká "migrace zpět".

### C2. `validate.py` má hlídat zachování `pop`, ale tři pravidla `pop` mění

`BUILD.md` část 4 žádá, aby validace selhala, když "součet `pop` světa se změnil jinak než
migrací". Jenže `pop` mění i bída (4.3: `pop −3/tah`) a dobytí (3.3: `pop −20 %`, uprchlíci
jdou do sousedního NPC). Invariant, jak je napsaný, by spadl u prvního hladomoru.

**Zatímní interpretace:** validace hlídá, že každá změna součtu `pop` je pokrytá záznamem
v `applied_rules` od pravidla, které `pop` měnit smí (4.3 bída, 3.3 invaze a uprchlíci,
5 migrace). Nevysvětlený rozdíl je chyba. Znění invariantu v `BUILD.md` by se mělo upřesnit.

### C3. Směr obchodu u `trade_offer`

Parametry jsou `target`, `res`, `qty`, `price_per_unit`, ale není určeno, zda hráč nakupuje
nebo prodává. Pravidlo říká jen "NPC přijme, pokud má přebytek/deficit".

**Zatímní interpretace:** směr určuje bilance NPC u dané suroviny. Přebytek znamená, že NPC
prodává hráči, deficit, že od hráče nakupuje. Nulová bilance znamená odmítnutí.

### C4. Automatický `explore` NPC stojí jinak než hráčův

Fáze `displacement`: "Běžná NPC s `wealth ≥ 20` automaticky každý tah utrácí 2 wealth
za `explore`", zatímco hráčova akce `explore` stojí 5 wealth za 15 % šanci (3.2).

**Otázka:** Má levnější varianta NPC i nižší šanci, nebo jde o stejných 15 % za 2 wealth?

**Zatímní interpretace:** stejných 15 %. Formulace "utrácí 2 wealth za `explore`" se čte
jako tatáž akce za jinou cenu.

### C5. Co přesně jsou "jednotky produkce" v metrice B

Pravidlo 8: `B_resource_share` je "(jednotky produkce B + okupovaných B + 0.5 × sphere_B)
/ světová produkce". Není určeno, zda jde o surové `prod`, nebo o efektivní produkci
po započtení `tech` (4.1) a `pop` (10.2).

**Zatímní interpretace:** efektivní produkce, tedy `prod × (1 + tech/20) × pop/100`.
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

**Zatímní interpretace:** rolování **není** nesplácení. Formálně dluh obsloužen je,
jen novým dluhem, což přesně odpovídá obrazu v `docs/faze.md` ("Státy si půjčují na
splátky starých půjček"). Nesplácení je až situace, kdy NPC nezaplatí a ani neroluje,
typicky kvůli dolní hranici `wealth 10` z pravidla 4.5.

### C8. Trvalé efekty z řádku `displacement`

Řádek `displacement` v tabulce pravidla 5 míchá jednorázové nastavení (orit se objeví,
ložiska, cena 10) s efekty, které musí platit dál (`tech +0.1` a `power +1` za každou
spotřebovanou jednotku, automatický `explore` NPC, povinná zpráva rozhodčího o soupeři).
Kdyby ty druhé platily jen během `displacement`, přestaly by platit v okamžiku, kdy
začne `boom`, a spotřeba oritu by rázem nic neznamenala.

**Zatímní interpretace:** jednorázové nastavení proběhne při vstupu do fáze, trvalé efekty
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

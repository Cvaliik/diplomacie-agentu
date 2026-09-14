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
>
> **Vyřešeno rozhodnutím Adama ze 14. 9. 2026 (pravidla v1.5).** K1 a K3 až K8 jsou potvrzené
> a zapsané do pravidel. K2, K9 a K10 řeší změny v1.5. Testy v1.5 jsou v části L,
> nově otevřené otázky z implementace v1.5 v části M.
>
> **Vyřešeno rozhodnutím Adama z 16. 9. 2026 (pravidla v1.6).** M2, M3, M4, M7, M9 a M11 jsou potvrzené
> a zapsané do pravidel. M1 ruší obchod hráčů mezi sebou, M5 nahrazuje práh rezervy 25, M6 ruší nový
> výběr zakladatelů bez mostu, M8 řeší příspěvky do fondu a M10 obchod padlých říší za tržní cenu.
> Testy v1.6 jsou v části N, nově otevřené otázky z implementace v1.6 v části O.
>
> **Vyřešeno rozhodnutím Adama ze 14. 9. 2026 (pravidla v1.7).** O1 až O5, O7, O8, O11, O12, O14, O15,
> O18 a O19 jsou potvrzené a zapsané do pravidel. O6 (u půjčky), O9, O13, O16 a O17 řeší změny v1.7.
> Testy v1.7 jsou v části P, nově otevřené otázky z implementace v1.7 v části Q.
>
> **Vyřešeno rozhodnutím Adama z 18. 9. 2026 (pravidla v1.8).** Q1 až Q8 jsou potvrzené a zapsané do pravidel,
> u Q10 až Q12 zůstává stávající chování enginu. Q9 řeší úprava ropy N3 a B. Testy v1.8 jsou v části R,
> nově otevřené otázky z implementace v1.8 v části S.

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

> **Vyřešeno v1.5 (4.1c): stát v bídě nebo s `wealth < 15` rezervu nedoplňuje.**

Rezerva se doplňuje „pokud `wealth > 10`“, hranice bídy je 15. **Výklad enginu:** deficit toku smí
stát pokrýt celým bohatstvím, doplnění rezervy jen z bohatství nad 10. Důsledek: chudé NPC s bohatstvím
mezi 10 a 15 dál nakupuje do rezervy a drží se v bídě (N8 ve (0) 88 z 90 tahů).
**Otázka:** zvednout práh doplnění na 15, nebo doplnění v bídě pozastavit?

### K9. Unie a souvislost území

> **Vyřešeno v1.5 (7.1): skupiny se mohou spojit přes jeden most.**

Ve variantě (a) bylo v tahu krachu způsobilých šest NPC (N10, N2, N4, N5, N11, N12), ale tvořila
čtyři oddělené skupiny o velikostech 2, 2, 1 a 1. Pravidlo 7.1 žádá souvislé území a minimum tří
zakladatelů, Unie proto nevznikla a kritérium (a) neprošlo. **Otázka:** má se při rozdělení na
malé skupiny dovolit spojení přes jednoho souseda, nebo je nevznik Unie v takové situaci záměr?

### K1. Obchodují A a B spolu na trhu?

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.5 (4.1a). Souvislost s globálním trhem viz M1.**

Hráči jsou pro trh sousedy všech NPC. **Výklad enginu:** navzájem sousedy nejsou, takže A a B spolu
na automatickém trhu neobchodují; mezi sebou mají jen `trade_offer`, a ta míří na NPC.

### K3. Stejná sféra, když nakupuje hráč

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.5 (4.1a).**

I7 řeší prodejce-hráče. **Výklad enginu:** symetricky i pro kupce-hráče, tedy NPC ve `sphere_A`
prodávající hráči A je ve stejné sféře.

### K4. Kdy se měří růst bohatství pro 4.2a

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.5 (4.2a).**

**Výklad enginu:** porovnává se bohatství v okamžiku investice (po obchodu, pokutách a příjmu
tohoto tahu) s bohatstvím na konci tahu o tři tahy dříve.

### K5. Platí v 4.2a dál `law ≥ 5`?

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.5 (4.2a).**

Rozhodnutí formuluje podmínku jako „`wealth > 40` a `wealth` za poslední 3 tahy vzrostlo“.
**Výklad enginu:** nová podmínka doplňuje původní, `law ≥ 5` zůstává.

### K6. Kdy přesně pakt zaniká

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.5 (3.2).**

**Výklad enginu:** srazí-li údržba paktu sílu ochránce na 0, pakt v tomto tahu ještě působí a pak
zanikne. Klesne-li síla na 0 jinak (bída, válka), pakt zanikne při nejbližší údržbě.

### K7. Status kandidáta po převratu

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.5 (4.3).**

Převrat nastavuje `status = independent`. **Výklad enginu:** kandidát, jehož kandidatura převrat
přežije, má dál `status = candidate`.

### K8. Rezerva oritu

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.5 (4.1c).**

Rezerva platí pro „každý statek“, orit se ale na trhu nekupuje, takže ho do rezervy doplnit nejde.
**Výklad enginu:** orit do nabídky ani poptávky automatického trhu nevstupuje vůbec, rezerva oritu
se tedy nedoplňuje a zásoba oritu se jen tvoří z vlastní těžby a čerpá spotřebou.

### K10. Unie se rozpadá dřív, než stihne táhnout

> **Vyřešeno v1.5 (4.3, 7.5): převrat členství neruší.**

Ve (b) klesne Unie za šest tahů po vzniku ze čtyř členů na jednoho, protože členům padají vlády
a převrat členství ruší. Není to nesrovnalost, pravidla 4.3 a 7.4 jsou jasná. Uvádím to, protože
Unie s jedním členem nemá vnitřní trh ani sílu, a tak ztrácí roli, kterou jí dávají tajné cíle.

---

## L. Testy pravidel v1.5 (14. 9. 2026)

### Souhrn

| scénář | kritérium | výsledek |
|---|---|---|
| (0) nikdo netáhne | do tahu 15 nejvýš dvě NPC v bídě | **neprošlo**, 3 NPC: N2, N8, N10 |
| (0) | do tahu 15 v bídě žádné z N1 až N5, N7, N11, N12 | **neprošlo**, N2 |
| (0) | `W_real` v tahu 30 aspoň 90 % startu | prošlo, 130.3 % z 717 |
| (0) | do tahu 90 nejvýš 5 NPC v bídě | **neprošlo**, nejvíc 9 najednou (tah 72), různých za běh 9 |
| (a) scénář ze zadání | crash mezi dnem 7 a 11 | prošlo, tah 32, den 11 |
| (a) | Unie s aspoň 3 zakladateli | prošlo, N2, N10, N11 (tah 32) |
| (a) | validate 0 chyb | prošlo |
| (b) realistické půjčování | crash mezi dnem 7 a 11 | prošlo, tah 24, den 8 |
| (b) | Unie s aspoň 3 zakladateli | prošlo, N6, N1, N8, N5 (tah 24) |
| (b) | validate 0 chyb | prošlo |

Validace hlásí 0 chyb ve všech třech scénářích a všech 90 tazích. Chyby enginu testy neodhalily.
Data se ve v1.5 neměnila.

### L1. Scénář (0) neprošel a proti v1.4 se zhoršil: proč NPC padají

Nekalibroval jsem. Rozpis je průměr za tah od začátku do prvního tahu v bídě. „Prodej“ je to, co
prodejce skutečně dostal, „nákup“ to, co kupec zaplatil včetně tranzitní přirážky; „ostatní“ je
všude nulové, účty se uzavírají.

| NPC | v bídě od | tahů v bídě | prodej (dostal) | nákup (zaplatil) | z toho doplnění | z toho přirážka | tranzitní příjem | pokuty | příjem 4.2b | investice 4.2a | průzkum | solidarita | ostatní | **čistě** | pokuty podle statku (součet) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N8 | tah 3 | 88 | +0.00 | -3.65 | -1.87 | -0.01 | +0.04 | -0.45 | +1.33 | +0.00 | +0.00 | +0.00 | +0.00 | **-2.73** | oil 1.4 |
| N10 | tah 11 | 80 | +0.11 | -1.46 | +0.00 | +0.00 | +0.00 | -0.62 | +1.42 | +0.00 | -0.36 | +0.00 | -0.00 | **-0.92** | oil 6.8 |
| N2 | tah 12 | 79 | +0.64 | -3.74 | +0.00 | -0.00 | +0.01 | -1.07 | +2.67 | +0.00 | -0.67 | +0.00 | -0.00 | **-2.16** | oil 12.8 |
| N11 | tah 31 | 60 | +0.41 | -3.73 | -0.31 | -0.54 | +0.00 | +0.00 | +0.83 | +0.00 | +0.00 | +0.00 | +0.00 | **-2.49** | - |
| N12 | tah 31 | 60 | +1.34 | -4.66 | -0.24 | -0.26 | +0.00 | +0.00 | +1.17 | +0.00 | +0.00 | +0.00 | -0.00 | **-2.15** | - |
| N4 | tah 40 | 33 | +3.44 | -4.02 | -0.27 | -0.01 | +0.15 | +0.00 | +1.83 | -0.90 | -1.55 | +0.00 | +0.00 | **-1.05** | - |
| N7 | tah 46 | 45 | +2.61 | -3.00 | -0.15 | -0.00 | +0.01 | -0.92 | +1.83 | +0.00 | -1.04 | +0.00 | +0.00 | **-0.51** | oil 42.4 |
| N5 | tah 68 | 23 | +3.81 | -2.33 | -0.06 | -0.05 | +0.00 | -0.87 | +1.67 | -1.06 | -1.59 | +0.00 | -0.00 | **-0.37** | oil 59.2 |
| N6 | tah 72 | 19 | +1.31 | -2.08 | -0.06 | -0.00 | +0.11 | -0.88 | +1.50 | +0.00 | -0.06 | +0.00 | -0.00 | **-0.10** | oil 63.5 |

Co z rozpisu plyne:

1. **N2 padá dřív než ve v1.4 (tah 12 místo 16), protože na globálním trhu prodá méně.** Jeho prodej
   klesl z 1.65 na 0.64 za tah: kupci mají na výběr všechny prodejce do tří přejezdů, ne jen sousedy.
   Nákup (3.74) a pokuty za ropu (1.07) přitom zůstaly, takže čistě ztrácí 2.16 za tah. N2 je chráněné
   NPC, a proto (0) neprošlo i v podmínce, kterou ve v1.4 splnilo.
2. **Nově padají padlé říše.** N11 a N12 jsou v bídě od tahu 31 a zůstanou v ní 60 tahů. Globální trh
   jim otevřel nákup odkudkoli; utrácejí 3.73 a 4.66 za tah, z toho 0.54 a 0.26 na přirážkách, a
   prodávají málo, protože za 1.3násobek ceny prohrávají s ostatními prodejci.
3. **Omezení doplňování rezervy (změna 2) chudým NPC nepomohlo.** Doplnění se zastaví, až bohatství
   klesne pod 15, tedy ve chvíli, kdy je stát už v bídě. N8 padá v tahu 3 jako ve v1.4.
4. **Pokuty dál tvoří jen ropa** a tranzitní příjem je u padajících NPC zanedbatelný (nejvýš 0.15 za tah).

### L2. Toky peněz ve scénáři (0), tahy 1 až 30

| účastník | prodal (dostal) | nakoupil (zaplatil) | saldo |
|---|---|---|---|
| A | 371.1 | 352.6 | +18.5 |
| B | 198.8 | 91.1 | +107.7 |
| NPC celkem | 936.1 | 1094.8 | -158.7 |

Z tranzitních přirážek dostaly tranzitní státy 16.2 a 16.2 propadlo jako náklad dopravy (M2).

### L.0 Scénář (0): nikdo netáhne

Hráči mlčí, žádné akce. Toky peněz jsou v L2.

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
| 1 | 89.25 | 744.1 | 0 | 0.79 | 1.49 | 0.97 | 1.05 | - |
| 12 | 71.89 | 831.7 | 3 | 0.77 | 1.21 | 0.84 | 1.05 | 9.94 |
| 30 | 70.28 | 934.0 | 3 | 0.75 | 1.10 | 0.84 | 1.05 | 7.00 |
| 45 | 54.30 | 1070.3 | 6 | 0.76 | 1.10 | 0.84 | 1.05 | 7.00 |
| 60 | 51.30 | 1188.9 | 6 | 0.76 | 1.09 | 0.84 | 1.05 | 73.25 |
| 90 | 36.85 | 1419.1 | 8 | 0.76 | 1.07 | 1.02 | 1.05 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 3 | N2, N8, N10 |
| 30 | 3 | N2, N8, N10 |
| 90 | 8 | N2, N5, N6, N7, N8, N10, N11, N12 |

#### Unie

Zakladatelé (tah 69, den 23): **N1, N8, N2, N7**.

| tah | vztah k založení | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|---|
| 60 | tah 60 | 0 | - | 0 | - |
| 69 | vznik | 4 | N1, N8, N2, N7 | 0 | - |
| 75 | +6 tahů | 6 | N1, N8, N2, N7, N10, N4 | 1 | N6 |
| 87 | +18 tahů | 7 | N1, N8, N2, N7, N10, N4, N6 | 0 | - |
| 90 | tah 90 | 7 | N1, N8, N2, N7, N10, N4, N6 | 0 | - |

Fond při založení 4.71, automatická solidarita za celý běh 0.00.

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) |
|---|---|---|---|
| 6 | 19.41 | 33.69 | 12.95 |
| 30 | 15.26 | 30.50 | 10.09 |
| 60 | 7.32 | 28.14 | 6.50 |
| 90 | 3.11 | 23.04 | 0.79 |

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 26 | 5 | 2 | 0 |
| 30 | 22 | 6 | 2 | 0 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N6 | 5.18 | 8.21 |
| N4 | 4.91 | 6.16 |
| N1 | 4.55 | 5.49 |
| N3 | 1.13 | 3.01 |
| N7 | 0.19 | 1.13 |
| N2 | 0.16 | 0.16 |
| N8 | 0.11 | 0.11 |

#### Zásoby světa (součet 14 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 328.1 | 142.0 | 92.0 | 237.7 | 0.0 |
| 30 | 269.5 | 68.9 | 150.5 | 276.4 | 139.8 |
| 60 | 275.2 | 73.2 | 156.9 | 281.7 | 140.0 |
| 90 | 272.4 | 50.8 | 147.2 | 281.6 | 140.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **70**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 15.3 | 15.1 | 233.5 | 292.7 |
| 60 | 0.0 | 1.3 | 225.8 | 477.4 |
| 90 | 0.0 | 1.3 | 170.9 | 605.7 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 12.80 | 6.0 / 8.40 | 2.0 / 2.60 | 1.0 / 1.10 | 7.1 / 12.60 |
| 30 | 10.0 / 20.00 | 6.0 / 8.40 | 2.9 / 2.80 | 1.0 / 0.00 | 7.4 / 2.00 |
| 60 | 10.0 / 20.00 | 6.0 / 8.40 | 3.8 / 2.80 | 1.0 / 0.00 | 4.4 / 0.00 |
| 90 | 10.0 / 20.00 | 6.0 / 8.40 | 4.7 / 3.43 | 0.5 / 0.00 | 1.4 / 0.00 |

### L.a Varianta (a): scénář ze zadání

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

Pojistka cyklu: do `overtrading` v tahu 21, do `distress` v tahu 29. Nejvyšší tržní cena oritu: 129.77. Zaniklých paktů: 1.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 89.25 | 744.1 | 0 | 0.79 | 1.49 | 0.97 | 1.05 | - |
| 12 | 78.13 | 822.6 | 2 | 1.09 | 1.21 | 0.84 | 1.05 | 12.79 |
| 30 | 80.67 | 917.8 | 2 | 0.97 | 1.09 | 0.84 | 1.05 | 129.77 |
| 45 | 60.60 | 914.0 | 4 | 0.56 | 1.07 | 0.84 | 1.05 | 3.50 |
| 60 | 57.28 | 1116.4 | 6 | 0.56 | 1.06 | 0.84 | 1.05 | 3.50 |
| 90 | 68.83 | 1500.2 | 4 | 0.56 | 1.04 | 0.84 | 1.05 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 3 | N2, N10, N11 |
| 30 | 2 | N2, N10 |
| 90 | 4 | N7, N8, N10, N12 |

#### Unie

Zakladatelé (tah 32, den 11): **N2, N10, N11**. Unie vznikla přes most **N8**, který se stal kandidátem.

| tah | vztah k založení | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|---|
| 32 | vznik | 3 | N2, N10, N11 | 1 | N8 |
| 38 | +6 tahů | 3 | N2, N10, N11 | 1 | N8 |
| 50 | +18 tahů | 3 | N2, N10, N11 | 1 | N8 |
| 60 | tah 60 | 3 | N10, N11, N1 | 1 | N8 |
| 90 | tah 90 | 3 | N10, N11, N1 | 1 | N8 |

Fond při založení 4.32, automatická solidarita za celý běh 0.00.

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) |
|---|---|---|---|
| 6 | 17.82 | 40.00 | 14.72 |
| 30 | 15.76 | 32.81 | 10.80 |
| 60 | 11.48 | 25.39 | 7.26 |
| 90 | 10.96 | 18.16 | 2.63 |

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 23 | 5 | 1 | 1 |
| 30 | 20 | 5 | 0 | 0 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N6 | 4.67 | 14.11 |
| N4 | 3.41 | 6.97 |
| N8 | 1.93 | 4.60 |
| N1 | 3.99 | 3.99 |
| N3 | 3.04 | 3.33 |
| N7 | 0.36 | 1.24 |
| N2 | 0.17 | 0.53 |

#### Zásoby světa (součet 14 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 328.1 | 142.0 | 92.0 | 237.7 | 0.0 |
| 30 | 105.2 | 82.2 | 167.6 | 287.0 | 140.0 |
| 60 | 223.2 | 59.1 | 196.0 | 266.2 | 140.0 |
| 90 | 239.3 | 56.5 | 187.6 | 303.7 | 154.1 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **43**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 27.4 | 63.0 | 147.1 | 243.0 |
| 60 | 24.7 | 5.4 | 228.7 | 370.4 |
| 90 | 24.7 | 5.4 | 329.9 | 536.5 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 12.80 | 6.0 / 8.40 | 2.0 / 2.60 | 1.0 / 1.10 | 7.1 / 12.60 |
| 30 | 10.0 / 20.00 | 6.0 / 8.40 | 2.8 / 0.00 | 1.0 / 0.00 | 5.7 / 0.00 |
| 60 | 10.0 / 8.62 | 6.0 / 8.40 | 3.7 / 0.00 | 1.0 / 0.00 | 5.7 / 0.00 |
| 90 | 10.0 / 6.83 | 6.0 / 8.40 | 3.8 / 5.33 | 1.0 / 2.00 | 5.7 / 0.00 |

### L.b Varianta (b): realistické půjčování

Hráč půjčí jen v tahu, kdy NPC žádá půjčku nebo má deficit oritu, nejvýš jedna půjčka na hráče a tah.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 9 | 3 | prvni loan po displacementu |
| `euphoria` | 14 | 5 | cena oritu >= 20 |
| `overtrading` | 21 | 7 | dluhy NPC > 40 % jejich wealth |
| `distress` | 22 | 8 | prvni nesplaceni |
| `panic` | 23 | 8 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 24 | 8 | po jednom tahu paniky |
| `depression` | 30 | 10 | 6 tahu po crash |
| `recovery` | 36 | 12 | 12 tahu po crash |

Pojistka cyklu: nezasáhla. Nejvyšší tržní cena oritu: 55.49. Zaniklých paktů: 1.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 89.25 | 744.1 | 0 | 0.79 | 1.49 | 0.97 | 1.05 | - |
| 12 | 76.47 | 806.5 | 2 | 1.03 | 1.21 | 0.84 | 1.05 | 13.59 |
| 30 | 37.11 | 671.1 | 6 | 0.56 | 1.09 | 0.84 | 1.05 | 2.10 |
| 45 | 42.20 | 817.8 | 6 | 0.56 | 1.10 | 0.84 | 1.05 | 3.50 |
| 60 | 41.59 | 963.6 | 7 | 0.56 | 1.05 | 0.84 | 1.05 | 3.50 |
| 90 | 42.00 | 1264.3 | 7 | 0.80 | 1.04 | 0.84 | 1.05 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 2 | N1, N10 |
| 30 | 6 | N1, N5, N6, N8, N10, N12 |
| 90 | 7 | N1, N4, N5, N6, N8, N10, N12 |

#### Unie

Zakladatelé (tah 24, den 8): **N6, N1, N8, N5**.

| tah | vztah k založení | členů | kdo | kandidátů | kdo |
|---|---|---|---|---|---|
| 24 | vznik | 4 | N6, N1, N8, N5 | 0 | - |
| 30 | +6 tahů | 4 | N6, N1, N8, N5 | 0 | - |
| 42 | +18 tahů | 4 | N6, N1, N8, N5 | 0 | - |
| 60 | tah 60 | 4 | N6, N1, N8, N5 | 2 | N10, N7 |
| 90 | tah 90 | 4 | N6, N1, N8, N5 | 2 | N10, N7 |

Fond při založení 6.29, automatická solidarita za celý běh 1.29.

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) |
|---|---|---|---|
| 6 | 17.82 | 40.00 | 14.72 |
| 30 | 12.07 | 24.06 | 4.58 |
| 60 | 6.06 | 27.36 | 5.50 |
| 90 | 7.49 | 25.14 | 3.27 |

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 23 | 5 | 1 | 1 |
| 30 | 22 | 5 | 0 | 0 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N4 | 5.75 | 6.15 |
| N3 | 2.34 | 4.47 |
| N6 | 3.42 | 4.05 |
| N1 | 2.76 | 2.96 |
| N8 | 1.45 | 1.59 |
| N7 | 0.52 | 0.69 |
| N2 | 0.16 | 0.16 |

#### Zásoby světa (součet 14 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 328.1 | 142.0 | 92.0 | 237.7 | 0.0 |
| 30 | 218.2 | 60.8 | 184.4 | 277.3 | 161.7 |
| 60 | 221.5 | 74.3 | 158.3 | 289.4 | 154.9 |
| 90 | 192.3 | 71.0 | 152.0 | 289.4 | 148.3 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **64**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 26.3 | 0.9 | 146.0 | 103.2 |
| 60 | 12.4 | 3.5 | 128.6 | 333.3 |
| 90 | 19.0 | 3.5 | 41.4 | 556.4 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 12.80 | 6.0 / 8.40 | 2.0 / 2.60 | 1.0 / 1.10 | 7.1 / 12.60 |
| 30 | 10.0 / 8.75 | 6.0 / 8.40 | 1.8 / 0.00 | 0.5 / 0.27 | 6.6 / 0.90 |
| 60 | 10.0 / 20.00 | 6.0 / 8.40 | 0.5 / 0.00 | 0.5 / 0.00 | 5.2 / 0.00 |
| 90 | 10.0 / 20.00 | 6.0 / 8.40 | 0.5 / 0.00 | 0.5 / 0.00 | 2.4 / 0.00 |

### L3. Co z běhů plyne

1. **Varianty (a) i (b) splnily všechna kritéria.** Ve (a) vznikla Unie díky mostu N8, který spojil
   skupiny N2 s N10 a N11.
2. **Unie přežívá.** Ve (b) má po 6 i 18 tazích a v tahu 90 pořád všechny čtyři zakladatele, ve (0)
   se do 18 tahů po vzniku rozroste na sedm členů (strop).
3. **Automatická solidarita se skoro nikdy nespustí (M8).** Fond při založení má 4.3 až 6.3 a musí
   v něm zůstat 5, takže k odeslání zbývá nejvýš 1.3; za celý běh poslal fond 0 (0), 0 (a) a 1.3 (b).
4. **Tranzit je okrajový.** V tazích 6 a 30 má 0 přejezdů 73 až 81 % obchodů, 3 přejezdy nejvýš jeden.
   Nejvyšší tranzitní příjem za 90 tahů má N6 ve variantě (a), 14.1.
5. **Index proti v1.4 klesl ve (0) a (b).** V tahu 90 je 36.85 (0), 68.83 (a) a 42.00 (b), ve v1.4 to bylo
   64.44, 56.22 a 68.63. Víc NPC v bídě na konci hry (8, 4 a 7) a padlé říše v bídě táhnou index dolů.
6. **Převratů přibylo:** 70, 43 a 64 proti 51, 35 a 46 ve v1.4. Členové Unie v bídě mají převraty
   opakovaně a s každým jim klesne `law` o 1 (M9).

---

## M. Nově otevřené otázky z implementace v1.5

Neopravuji je, engine u každé používá uvedený výklad. Nejdůležitější jsou M8 a M10, protože
rozhodují o tom, jestli nová pravidla vůbec působí (solidarita) a proč padají padlé říše.

### M8. Solidarita s malým fondem nefunguje

> **Vyřešeno v1.6 (7.2): příspěvky 2 % za tah, solidarita smí fond vyprázdnit.**

Fond Unie vzniká z 10 % bohatství zakladatelů, v testech 4.3 až 6.3. Solidarita smí poslat jen
to, co ve fondu zůstane nad 5, takže poslat nemá skoro co (za 90 tahů 0, 0 a 1.3). **Výklad enginu:**
solidarita běží od tahu po založení, dostává ji nejdřív nejchudší člen. **Otázka:** snížit
podmínku zůstatku fondu, nebo fond při založení posílit?

### M10. Padlé říše padají díky globálnímu nákupu

> **Vyřešeno v1.6 (7a): na trhu nakupují i prodávají za tržní cenu.**

Ve (0) jsou N11 a N12 v bídě od tahu 31 po zbytek hry. Nakupují na globálním trhu za tržní cenu
s přirážkou, ale prodávají za 1.3násobek, a tak s ostatními prodejci prohrávají. **Otázka:** mají
padlé říše nakupovat globálně, nebo jen od sousedů?

### M1. „Kohokoli s kýmkoli“ a potvrzené K1

> **Zrušeno v1.6 (4.1a): hráči obchodují i spolu.**

Změna 1 páruje kohokoli s kýmkoli a hráči „obchodují se všemi“, zároveň je potvrzené K1, podle
kterého A a B spolu na automatickém trhu neobchodují. **Výklad enginu:** K1 platí, hráči obchodují
se všemi NPC, spolu ne.

### M2. Druhá polovina přirážky

> **Potvrzeno 16. 9. 2026, zapsáno do pravidel v1.6 (4.1a).**

Tranzitní stát dostane polovinu přirážky za svůj přejezd; o druhé polovině pravidlo mlčí.
**Výklad enginu:** propadá jako náklad dopravy, prodejce dostane základní cenu. Ve (0) za tahy 1 až 30
propadlo 16.2.

### M3. Přirážka u padlé říše

> **Potvrzeno 16. 9. 2026, zapsáno do pravidel v1.6 (4.1a); padlé říše už na trhu za 1.3× neprodávají.**

**Výklad enginu:** padlá říše prodává za 1.3násobek tržní ceny a přirážka za přejezdy se počítá
z této ceny.

### M4. Víc nejkratších cest

> **Potvrzeno 16. 9. 2026, zapsáno do pravidel v1.6 (4.1a).**

**Výklad enginu:** cesta se hledá do šířky se sousedy v pořadí ID a platí první nalezená nejkratší.
Na ní závisí, kdo dostane tranzitní příjem.

### M5. Kdy je stát „v bídě“ pro doplňování rezervy

> **Nahrazeno v1.6 (4.1c): rezervu doplňuje jen stát s `wealth ≥ 25`.**

Trh probíhá před vyhodnocením bídy tohoto tahu. **Výklad enginu:** v bídě je stát, který byl v bídě
minulý tah (`poverty_streak > 0`), nebo má v okamžiku trhu `wealth < 15`. Doplnění se navíc platí
jen z bohatství nad 15.

### M6. Kdy a jak se staví most

> **Zrušeno v1.6 (7.1): výběr zakladatelů bez mostu.**

**Výklad enginu:** most se hledá jen tehdy, když žádná souvislá skupina způsobilých států nemá aspoň
tři. Vybere se nezávislé NPC, které spojí nejvíc způsobilých států, při shodě skupina s nižším průměrným
`wealth`, pak nižší ID. Mostem může být i padlá říše. Kandidátem se most stane, jen když přes něj
vybraní zakladatelé opravdu vedou.

### M7. Co je „vykoupení“

> **Potvrzeno 16. 9. 2026, zapsáno do pravidel v1.6 (7.5).**

Změna 4 říká, že z Unie se odchází „jen vykoupením (7.5)“. **Výklad enginu:** vykoupením je stávající
odchod podle 7.5, tedy `influence[X] ≥ 15`.

### M9. Opakovaný převrat člena

> **Potvrzeno 16. 9. 2026, zapsáno do pravidel v1.6 (4.3).**

**Výklad enginu:** s každým převratem klesne členovi `law` o 1, i opakovaně, a vliv obou hráčů se
jako u každého převratu vynuluje. Člen s nízkým `law` tak může trvale ležet pod prahem Unie (7.3),
aniž by z ní odešel.

### M11. Přirážka v metrice A

> **Potvrzeno 16. 9. 2026, zapsáno do pravidel v1.6 (4.1a).**

**Výklad enginu:** do objemu obchodu (metrika A) se počítá to, co kupec zaplatil, tedy včetně přirážky.

---

## N. Testy pravidel v1.6 (16. 9. 2026)

### Souhrn

| scénář | kritérium | výsledek |
|---|---|---|
| (0) nikdo netáhne | do tahu 15 nejvýš dvě NPC v bídě | **neprošlo**, 6 NPC: N2, N8, N10, N11, N13, N16 |
| (0) | do tahu 15 v bídě žádné z N1 až N5, N7, N11 až N14 | **neprošlo**, N2, N11, N13 |
| (0) | `W_real` v tahu 30 aspoň 90 % startu | prošlo, 140.5 % z 864 |
| (0) | do tahu 90 nejvýš 6 NPC v bídě z 16 | **neprošlo**, nejvíc 10 najednou (tah 57), různých za běh 10 |
| (a) scénář ze zadání | crash mezi dnem 7 a 11 | prošlo, tah 33, den 11 |
| (a) | Unie s aspoň 3 zakladateli | prošlo, N11, N12, N4, N5 (tah 33) |
| (a) | validate 0 chyb | prošlo |
| (b) realistické půjčování | crash mezi dnem 7 a 11 | prošlo, tah 25, den 9 |
| (b) | Unie s aspoň 3 zakladateli | prošlo, N11, N12, N1, N4 (tah 25) |
| (b) | validate 0 chyb | prošlo |

Validace hlásí 0 chyb ve všech třech scénářích a všech 90 tazích. Svět má 18 států, `W_0` je 864.

### N1. Scénář (0) neprošel: proč NPC padají

Nekalibroval jsem. Rozpis je průměr za tah od začátku do prvního tahu v bídě; „ostatní“ je všude
nulové, účty se uzavírají.

| NPC | v bídě od | tahů v bídě | prodej (dostal) | nákup (zaplatil) | z toho doplnění | z toho přirážka | tranzit | pokuty | příjem 4.2b | investice | průzkum | solidarita | příspěvek Unii | ostatní | **čistě** | pokuty podle statku |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N8 | tah 6 | 85 | +0.11 | -2.57 | +0.00 | -0.17 | +0.00 | -0.11 | +1.33 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | **-1.23** | oil 0.7 |
| N16 | tah 7 | 84 | +0.00 | -2.69 | +0.00 | -0.22 | +0.00 | +0.00 | +1.50 | +0.00 | +0.00 | +0.00 | +0.00 | -0.00 | **-1.19** | - |
| N11 | tah 10 | 81 | +0.00 | -8.50 | -0.92 | -1.39 | +0.00 | +0.00 | +0.83 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | **-7.67** | - |
| N13 | tah 10 | 80 | +1.31 | -6.44 | -1.27 | -0.19 | +0.00 | +0.00 | +2.00 | +0.00 | -0.40 | +0.00 | +0.00 | +0.00 | **-3.52** | - |
| N10 | tah 13 | 78 | +0.08 | -1.66 | -0.04 | -0.05 | +0.00 | -0.31 | +1.42 | +0.00 | -0.31 | +0.00 | +0.00 | -0.00 | **-0.78** | oil 4.1 |
| N2 | tah 14 | 77 | +0.60 | -4.31 | -0.08 | -0.18 | +0.01 | -0.20 | +2.67 | +0.00 | -0.57 | +0.00 | +0.00 | -0.00 | **-1.80** | oil 2.8 |
| N12 | tah 17 | 74 | +1.52 | -6.70 | -0.77 | -0.00 | +0.00 | +0.00 | +1.17 | +0.00 | +0.00 | +0.00 | +0.00 | -0.00 | **-4.01** | - |
| N5 | tah 22 | 39 | +3.85 | -4.77 | -0.90 | -0.07 | +0.00 | +0.00 | +1.67 | -0.82 | -1.09 | +0.00 | +0.00 | -0.00 | **-1.16** | - |
| N4 | tah 50 | 41 | +5.17 | -4.82 | -0.44 | -0.01 | +0.06 | +0.00 | +1.84 | -1.44 | -1.64 | +0.00 | +0.00 | +0.00 | **-0.83** | - |
| N7 | tah 54 | 37 | +1.68 | -3.50 | -0.38 | -0.01 | +0.07 | -0.01 | +1.84 | +0.00 | -0.52 | +0.00 | +0.00 | +0.00 | **-0.43** | oil 0.4 |

Co z rozpisu plyne:

1. **Pokuty za ropu prakticky zmizely.** Kalibrace ropy zabrala: ve světové bilanci jsou pokuty za ropu
   i obilí ve všech tazích nulové a u padajících NPC nejvýš 0.31 za tah.
2. **Nově padají průmyslová NPC bez ropy (O17).** N11 nakupuje za 8.50 za tah a neprodá nic, N13 nakupuje
   za 6.44 a prodá za 1.31, N12 nakupuje za 6.70 a prodá za 1.52. Kupují vstupy a doplňují rezervy pro
   továrny, jejichž produkt se neprodá: cena `goods` je po celou hru na dolní mezi 1.05, trh je jím přesycený.
   Tři z nich (N11, N12, N13) jsou chráněná NPC.
3. **Chudá NPC (N8, N16, N10) utrácejí víc, než vydělají.** Nákup 1.7 až 2.7 za tah proti neformálnímu
   příjmu 1.3 až 1.5; doplňování rezervy je u nich nulové, práh 25 zabral.
4. **N2 padá v tahu 14** s nákupem 4.31 za tah proti prodeji 0.60 a příjmu 2.67.

### N.0 Scénář (0): nikdo netáhne

Hráči mlčí, žádné akce.

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

Pojistka cyklu: do `overtrading` v tahu 58, do `distress` v tahu 66. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 90.28 | 896.5 | 0 | 0.75 | 1.09 | 0.90 | 1.05 | - |
| 12 | 71.99 | 1023.1 | 4 | 0.74 | 1.03 | 0.86 | 1.05 | 9.19 |
| 30 | 57.47 | 1214.2 | 8 | 0.74 | 0.94 | 0.86 | 1.05 | 7.00 |
| 45 | 63.41 | 1356.4 | 7 | 0.73 | 0.91 | 0.89 | 1.05 | 7.00 |
| 60 | 43.89 | 1507.8 | 10 | 0.74 | 0.90 | 0.86 | 1.05 | 73.25 |
| 90 | 46.46 | 1761.2 | 9 | 0.71 | 0.80 | 0.90 | 1.05 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 6 | N2, N8, N10, N11, N13, N16 |
| 30 | 8 | N2, N5, N8, N10, N11, N12, N13, N16 |
| 90 | 9 | N2, N4, N7, N8, N10, N11, N12, N13, N16 |

#### Unie: zakladatelé, členové, fond a solidarita

Způsobilých států: 14, souvislé skupiny o velikostech 12, 2.

| zakladatel / kandidát při vzniku | role | `law` | `wealth` |
|---|---|---|---|
| N11 | zakladatel | 9.0 | 6.84 |
| N12 | zakladatel | 8.0 | 0.43 |
| N13 | zakladatel | 6.0 | 2.74 |
| N4 | zakladatel | 6.0 | 0.92 |
| N1 | kandidát | 5.0 | 32.54 |
| N7 | kandidát | 4.0 | 8.63 |
| N10 | kandidát | 4.0 | 3.44 |

| tah | vztah k založení | členů | kdo | kandidátů | kdo | fond | solidarita v tahu | solidarita od vzniku |
|---|---|---|---|---|---|---|---|---|
| 60 | tah 60 | 0 | - | 0 | - | - | 0.00 | - |
| 69 | vznik | 4 | N11, N12, N13, N4 | 3 | N1, N7, N10 | 1.09 | 0.00 | 0.00 |
| 75 | +6 tahů | 4 | N11, N12, N13, N4 | 3 | N1, N7, N10 | 0.00 | 0.21 | 2.37 |
| 87 | +18 tahů | 7 | N11, N12, N13, N4, N1, N7, N10 | 1 | N8 | 0.00 | 1.30 | 15.11 |
| 90 | tah 90 | 7 | N11, N12, N13, N4, N1, N7, N10 | 1 | N8 | 0.00 | 1.35 | 19.12 |

#### Sféry před krachem a po něm

| hráč | tah 68 (před krachem) | tah 69 (krach) |
|---|---|---|
| A | 0 | 0 |
| B | 0 | 0 |

#### Světová bilance ropy a obilí

| tah | ropa výroba | ropa domácnosti | ropa průmysl | ropa pokuty | obilí výroba | obilí domácnosti | obilí pokuty |
|---|---|---|---|---|---|---|---|
| 1 | 52.4 | 12.3 | 44.4 | 0.00 | 65.6 | 61.6 | 0.00 |
| 30 | 57.2 | 9.7 | 43.7 | 0.00 | 53.4 | 48.7 | 0.00 |
| 60 | 55.3 | 8.0 | 41.4 | 0.00 | 43.6 | 39.8 | 0.00 |
| 90 | 45.0 | 6.5 | 29.6 | 0.00 | 36.6 | 32.4 | 0.00 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) | A s B |
|---|---|---|---|---|
| 6 | 34.02 | 32.15 | 9.52 | 0.00 |
| 30 | 17.27 | 24.19 | 2.95 | 0.00 |
| 60 | 9.40 | 21.23 | 0.20 | 0.00 |
| 90 | 3.62 | 18.30 | 0.00 | 0.00 |

Obchod A s B v tazích 6, 30 a 60: 0.00, 0.00 a 0.00. Za celý běh proběhl v 4 tazích v objemu 22.23.

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 33 | 4 | 6 | 0 |
| 30 | 33 | 4 | 4 | 2 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N6 | 6.94 | 6.95 |
| N1 | 5.01 | 5.02 |
| N7 | 3.08 | 3.93 |
| N4 | 2.66 | 2.82 |
| N3 | 1.95 | 1.96 |
| N2 | 0.39 | 0.46 |
| N8 | 0.01 | 0.01 |

#### Rozhodování NPC podle 3.4

Žádná cílená akce, žádné vyhodnocení.

#### Nabídky NPC podle 3.5

| hráč | typ | vygenerováno | přijato skriptem |
|---|---|---|---|
| A | `sell` | 180 | 0 |
| B | `sell` | 180 | 0 |
| C | `loan_request` | 44 | 0 |

#### Zásoby světa (součet 18 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 401.4 | 166.1 | 133.1 | 291.2 | 0.0 |
| 30 | 344.9 | 147.0 | 193.7 | 347.8 | 180.0 |
| 60 | 329.6 | 211.6 | 177.2 | 356.9 | 180.0 |
| 90 | 327.0 | 263.3 | 168.3 | 359.9 | 157.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **97**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 3.5 | 0.5 | 304.7 | 320.5 |
| 60 | 6.8 | 0.4 | 338.5 | 515.1 |
| 90 | 5.3 | 5.4 | 352.2 | 670.1 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 12.80 | 6.0 / 8.40 | 2.0 / 2.60 | 1.0 / 1.08 | 7.1 / 12.60 |
| 30 | 10.0 / 20.00 | 6.0 / 8.40 | 2.6 / 5.20 | 1.0 / 1.54 | 5.8 / 0.00 |
| 60 | 10.0 / 20.00 | 6.0 / 8.40 | 2.6 / 5.31 | 1.0 / 2.04 | 2.8 / 0.00 |
| 90 | 10.0 / 20.00 | 6.0 / 8.40 | 2.9 / 5.80 | 1.0 / 2.00 | 0.5 / 0.00 |

### N.a Varianta (a): scénář ze zadání

A půjčuje N6 od tahu 8, B chrání N7, oba obchodují obilím. Skript přijímá `sell`, které kryjí deficit hráče, a `loan_request` v boom a euphoria.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 9 | 3 | prvni loan po displacementu |
| `euphoria` | 14 | 5 | cena oritu >= 20 |
| `overtrading` | 22 | 8 | pojistka cyklu: 8 tahu bez splneni prahu |
| `distress` | 30 | 10 | pojistka cyklu: 8 tahu bez splneni prahu |
| `panic` | 32 | 11 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 33 | 11 | po jednom tahu paniky |
| `depression` | 39 | 13 | 6 tahu po crash |
| `recovery` | 45 | 15 | 12 tahu po crash |

Pojistka cyklu: do `overtrading` v tahu 22, do `distress` v tahu 30. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 90.28 | 896.5 | 0 | 0.75 | 1.09 | 0.90 | 1.05 | - |
| 12 | 66.42 | 1004.7 | 5 | 0.94 | 1.07 | 0.87 | 1.05 | 14.95 |
| 30 | 57.17 | 1109.0 | 7 | 0.73 | 0.99 | 0.84 | 1.05 | 129.77 |
| 45 | 53.29 | 1090.8 | 6 | 0.56 | 0.97 | 1.00 | 1.05 | 3.50 |
| 60 | 58.83 | 1129.1 | 3 | 0.56 | 1.02 | 1.07 | 1.05 | 3.50 |
| 90 | 48.89 | 1448.8 | 6 | 0.56 | 0.95 | 0.95 | 1.05 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 5 | N8, N10, N11, N13, N16 |
| 30 | 7 | N5, N8, N10, N11, N12, N13, N16 |
| 90 | 5 | N1, N8, N10, N11, N16 |

#### Unie: zakladatelé, členové, fond a solidarita

Způsobilých států: 12, souvislé skupiny o velikostech 12.

| zakladatel / kandidát při vzniku | role | `law` | `wealth` |
|---|---|---|---|
| N11 | zakladatel | 9.0 | 1.52 |
| N12 | zakladatel | 8.0 | 0.32 |
| N4 | zakladatel | 6.1 | 37.20 |
| N5 | zakladatel | 6.0 | 2.30 |
| N13 | kandidát | 6.0 | 0.03 |
| N2 | kandidát | 5.8 | 20.47 |
| N14 | kandidát | 5.0 | 36.53 |

| tah | vztah k založení | členů | kdo | kandidátů | kdo | fond | solidarita v tahu | solidarita od vzniku |
|---|---|---|---|---|---|---|---|---|
| 33 | vznik | 4 | N11, N12, N4, N5 | 3 | N13, N2, N14 | 4.13 | 0.00 | 0.00 |
| 39 | +6 tahů | 6 | N11, N12, N4, N5, N1, N2 | 2 | N13, N14 | 0.00 | 1.41 | 8.97 |
| 51 | +18 tahů | 7 | N11, N12, N4, N5, N1, N2, N13 | 3 | N14, N10, N16 | 4.68 | 3.00 | 41.45 |
| 60 | tah 60 | 7 | N11, N12, N4, N5, N2, N13, N14 | 3 | N10, N16, N8 | 14.12 | 0.00 | 59.45 |
| 90 | tah 90 | 7 | N11, N12, N4, N5, N2, N13, N14 | 3 | N10, N16, N8 | 36.14 | 3.00 | 113.45 |

#### Sféry před krachem a po něm

| hráč | tah 32 (před krachem) | tah 33 (krach) |
|---|---|---|
| A | 0 | 0 |
| B | 1 | 1 |

#### Světová bilance ropy a obilí

| tah | ropa výroba | ropa domácnosti | ropa průmysl | ropa pokuty | obilí výroba | obilí domácnosti | obilí pokuty |
|---|---|---|---|---|---|---|---|
| 1 | 52.4 | 12.3 | 44.4 | 0.00 | 65.6 | 61.6 | 0.00 |
| 30 | 55.3 | 10.2 | 44.0 | 0.06 | 56.8 | 51.1 | 0.00 |
| 60 | 58.4 | 8.8 | 50.8 | 0.52 | 99.6 | 44.1 | 0.00 |
| 90 | 52.5 | 7.7 | 42.2 | 0.00 | 90.0 | 38.4 | 0.00 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) | A s B |
|---|---|---|---|---|
| 6 | 32.40 | 151.21 | 8.07 | 0.00 |
| 30 | 20.89 | 96.23 | 0.57 | 0.00 |
| 60 | 25.49 | 70.64 | 1.83 | 0.00 |
| 90 | 21.54 | 23.82 | 0.53 | 4.97 |

Obchod A s B v tazích 6, 30 a 60: 0.00, 0.00 a 0.00. Za celý běh proběhl v 29 tazích v objemu 130.07.

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 29 | 7 | 4 | 0 |
| 30 | 28 | 3 | 3 | 2 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N4 | 5.95 | 37.81 |
| N6 | 9.60 | 19.18 |
| N3 | 4.51 | 14.81 |
| N7 | 3.68 | 14.77 |
| N1 | 5.74 | 6.02 |
| N2 | 0.19 | 0.36 |
| N8 | 0.02 | 0.02 |

#### Rozhodování NPC podle 3.4

| akce | přijato | s podmínkou | protinávrh | odmítnuto |
|---|---|---|---|---|
| `trade_offer` | 0 | 0 | 2 | 0 |
| `loan` | 64 | 13 | 1 | 4 |
| `protect` | 0 | 0 | 0 | 1 |

#### Nabídky NPC podle 3.5

| hráč | typ | vygenerováno | přijato skriptem |
|---|---|---|---|
| A | `sell` | 180 | 96 |
| B | `sell` | 180 | 177 |
| C | `loan_request` | 103 | 0 |

#### Zásoby světa (součet 18 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 401.4 | 166.1 | 133.1 | 291.2 | 0.0 |
| 30 | 341.6 | 139.0 | 208.8 | 375.7 | 178.6 |
| 60 | 413.3 | 160.6 | 186.6 | 385.6 | 200.0 |
| 90 | 416.3 | 168.9 | 161.5 | 357.0 | 200.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **64**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 1.5 | 0.5 | 161.0 | 300.7 |
| 60 | 14.9 | 16.1 | 81.4 | 22.0 |
| 90 | 17.2 | 15.4 | 177.9 | 6.3 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 12.80 | 6.0 / 8.40 | 2.0 / 2.60 | 1.0 / 1.08 | 7.1 / 12.60 |
| 30 | 10.0 / 20.00 | 6.0 / 8.40 | 4.5 / 9.95 | 1.0 / 2.02 | 5.8 / 0.00 |
| 60 | 10.0 / 19.48 | 6.0 / 8.40 | 8.1 / 15.31 | 0.9 / 0.00 | 3.3 / 0.00 |
| 90 | 10.0 / 19.48 | 3.3 / 2.14 | 5.5 / 0.95 | 0.9 / 1.74 | 2.8 / 0.00 |

### N.b Varianta (b): realistické půjčování

Hráč půjčí jen v tahu, kdy NPC žádá půjčku nebo má deficit oritu, nejvýš jedna půjčka na hráče a tah. Nabídky přijímá stejně jako (a).

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

Pojistka cyklu: do `overtrading` v tahu 22. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 90.28 | 896.5 | 0 | 0.75 | 1.09 | 0.90 | 1.05 | - |
| 12 | 75.07 | 1000.8 | 3 | 0.94 | 1.06 | 0.87 | 1.05 | 14.95 |
| 30 | 42.88 | 902.7 | 8 | 0.56 | 1.01 | 0.93 | 1.05 | 2.10 |
| 45 | 41.66 | 1134.9 | 10 | 0.56 | 0.94 | 0.86 | 1.05 | 3.50 |
| 60 | 75.58 | 1304.2 | 5 | 0.62 | 0.88 | 0.90 | 1.05 | 3.50 |
| 90 | 71.59 | 1623.0 | 5 | 0.63 | 0.89 | 0.95 | 1.05 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 4 | N10, N11, N13, N16 |
| 30 | 8 | N2, N5, N6, N8, N10, N11, N12, N13 |
| 90 | 5 | N5, N6, N10, N13, N16 |

#### Unie: zakladatelé, členové, fond a solidarita

Způsobilých států: 14, souvislé skupiny o velikostech 14.

| zakladatel / kandidát při vzniku | role | `law` | `wealth` |
|---|---|---|---|
| N11 | zakladatel | 9.0 | 0.08 |
| N12 | zakladatel | 8.0 | 0.77 |
| N1 | zakladatel | 6.6 | 36.70 |
| N4 | zakladatel | 6.0 | 52.54 |
| N2 | kandidát | 5.5 | 19.17 |
| N5 | kandidát | 5.2 | 10.42 |
| N14 | kandidát | 5.0 | 38.45 |

| tah | vztah k založení | členů | kdo | kandidátů | kdo | fond | solidarita v tahu | solidarita od vzniku |
|---|---|---|---|---|---|---|---|---|
| 25 | vznik | 4 | N11, N12, N1, N4 | 3 | N2, N5, N14 | 9.01 | 0.00 | 0.00 |
| 31 | +6 tahů | 4 | N11, N12, N1, N4 | 3 | N2, N5, N14 | 0.00 | 2.59 | 17.59 |
| 43 | +18 tahů | 7 | N11, N12, N1, N4, N2, N5, N14 | 3 | N10, N13, N16 | 0.00 | 2.20 | 35.22 |
| 60 | tah 60 | 7 | N11, N12, N1, N4, N2, N5, N14 | 3 | N10, N13, N16 | 3.08 | 3.00 | 72.75 |
| 90 | tah 90 | 7 | N11, N12, N1, N4, N5, N14, N7 | 3 | N10, N13, N16 | 24.88 | 3.00 | 123.75 |

#### Sféry před krachem a po něm

| hráč | tah 24 (před krachem) | tah 25 (krach) |
|---|---|---|
| A | 1 | 0 |
| B | 0 | 0 |

#### Světová bilance ropy a obilí

| tah | ropa výroba | ropa domácnosti | ropa průmysl | ropa pokuty | obilí výroba | obilí domácnosti | obilí pokuty |
|---|---|---|---|---|---|---|---|
| 1 | 52.4 | 12.3 | 44.4 | 0.00 | 65.6 | 61.6 | 0.00 |
| 30 | 57.1 | 10.5 | 46.1 | 0.36 | 115.3 | 52.4 | 0.00 |
| 60 | 50.0 | 7.4 | 36.5 | 0.00 | 47.8 | 36.9 | 0.00 |
| 90 | 49.7 | 7.1 | 37.5 | 0.00 | 45.7 | 35.7 | 0.00 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) | A s B |
|---|---|---|---|---|
| 6 | 32.40 | 151.21 | 8.07 | 0.00 |
| 30 | 19.20 | 26.61 | 4.70 | 0.00 |
| 60 | 5.64 | 19.74 | 0.00 | 0.00 |
| 90 | 13.91 | 12.99 | 0.00 | 6.96 |

Obchod A s B v tazích 6, 30 a 60: 0.00, 0.00 a 0.00. Za celý běh proběhl v 21 tazích v objemu 124.98.

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 29 | 7 | 4 | 0 |
| 30 | 26 | 3 | 5 | 3 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N6 | 12.97 | 22.69 |
| N4 | 7.89 | 13.47 |
| N3 | 7.62 | 10.30 |
| N7 | 4.06 | 8.07 |
| N1 | 6.17 | 7.15 |
| N2 | 0.31 | 0.77 |
| N8 | 0.01 | 0.32 |

#### Rozhodování NPC podle 3.4

| akce | přijato | s podmínkou | protinávrh | odmítnuto |
|---|---|---|---|---|
| `trade_offer` | 0 | 0 | 2 | 0 |
| `loan` | 41 | 27 | 21 | 75 |
| `protect` | 0 | 0 | 0 | 1 |

#### Nabídky NPC podle 3.5

| hráč | typ | vygenerováno | přijato skriptem |
|---|---|---|---|
| A | `sell` | 180 | 96 |
| B | `sell` | 180 | 95 |
| C | `loan_request` | 132 | 0 |

#### Zásoby světa (součet 18 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 401.4 | 166.1 | 133.1 | 291.2 | 0.0 |
| 30 | 399.2 | 147.8 | 216.2 | 373.1 | 200.0 |
| 60 | 387.6 | 197.8 | 213.8 | 378.5 | 185.2 |
| 90 | 388.1 | 190.0 | 209.1 | 372.2 | 180.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **75**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 8.7 | 6.8 | 170.8 | 166.8 |
| 60 | 17.6 | 17.2 | 204.5 | 394.3 |
| 90 | 16.9 | 16.5 | 275.4 | 550.5 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 12.80 | 6.0 / 8.40 | 2.0 / 2.60 | 1.0 / 1.08 | 7.1 / 12.60 |
| 30 | 10.0 / 20.00 | 6.0 / 8.40 | 4.2 / 8.19 | 0.5 / 0.76 | 5.8 / 0.00 |
| 60 | 10.0 / 20.00 | 6.0 / 8.40 | 7.2 / 14.19 | 0.5 / 0.00 | 3.3 / 0.00 |
| 90 | 10.0 / 20.00 | 6.0 / 8.40 | 9.0 / 16.11 | 0.5 / 0.00 | 3.0 / 0.00 |

### N2. Co z běhů plyne

1. **Varianty (a) i (b) splnily všechna kritéria.** Crash ve (a) v tahu 33 (den 11, na hraně okna),
   ve (b) v tahu 25 (den 9).
2. **Vůle NPC půjčky výrazně brzdí, okno krachu to ale nerozbilo.** Ve (b) bylo z 164 půjček přijato
   41, s podmínkou 27, protinávrhem 21 a odmítnuto
   75. Ve (a), kde A půjčuje stále téže N6, bylo z 82 půjček odmítnuto
   4. Oba počáteční obchody obilím (A s N1, B s N2) skončily protinávrhem, takže se
   neotevřely.
3. **Zakladateli jsou vždy padlé říše.** Výběr podle nejvyššího `law` dává N11 (`law` 9) a N12 (`law` 8)
   do zakladatelů ve všech třech scénářích, přestože jsou v tahu krachu skoro bez peněz a navzájem
   nesousedí (O16).
4. **Solidarita funguje.** Od vzniku do tahu 90 poslal fond 19.12 (0), 113.45 (a)
   a 123.75 (b). Fond se v prvních tazích vyprázdní a pak se z příspěvků plní.
5. **Nabídky NPC jsou na stropu.** A i B dostanou každý tah 2 nabídky `sell` (180 za běh). Skripty přijaly
   ve (a) A 96 a B 177, ve (b) A 96
   a B 95. Na `loan_request` hráčům A a B nezbyde místo: obě místa za tah vždy obsadí `sell`, protože
   u každého NPC se typ `sell` zkouší první (O13). `loan_request` tak dostává jen Unie; skripty za Unii netáhnou.
6. **Obchod A s B je vzácný a nepravidelný.** V tazích 6, 30 a 60 byl ve všech scénářích nulový; počet tahů
   s obchodem a jeho objem za celý běh uvádí tabulka Obchod u každého scénáře (ve (b) 21 tahů, 124.98).
   V ověřeném tahu 6 vykoupila nabídku ropy hráče B NPC s větší poptávkou dřív, protože párování jde podle poptávky.
7. **Sféry kolem krachu jsou nanejvýš jedna,** přetížení sfér se tak v testech skoro neprojeví.
8. **Index v tahu 90:** 46.46 (0), 48.89 (a), 71.59 (b);
   převratů 97, 64 a 75.

---

## O. Nově otevřené otázky z implementace v1.6

Neopravuji je, engine u každé používá uvedený výklad. Nejdůležitější jsou O17 (proč padají průmyslová
NPC) a O16 (padlé říše jako zakladatelé).

### O17. Továrny vyrábějí i to, co se neprodá

> **Vyřešeno v1.7 (4.0): výroba podle poptávky.**

Průmysl nakupuje vstupy a doplňuje rezervy pro plnou výrobu podle `coverage`, bez ohledu na to, zda se
`goods` prodá. Cena `goods` je v testech trvale na dolní mezi 1.05, trh je přesycený, a průmyslová NPC bez
ropy (N11, N12, N13) na nákupu vstupů zkrachují. **Otázka:** má výroba reagovat na poptávku (například
vyrábět jen do výše domácí potřeby plus prodaného množství minulého tahu)?

### O16. Zakladatelé podle `law`

> **Vyřešeno v1.7 (7.1): hladový výběr sousedících zakladatelů, padlé říše jen se ztrátou nebo nesplácením.**

Výběr čtyř s nejvyšším `law` dává do zakladatelů vždy N11 a N12, i když jsou v krizi bez peněz.
Zakladatelé navíc nemusí sousedit mezi sebou, stačí, že patří do téže souvislé skupiny; N11 a N12 leží
na opačných koncích mapy. **Otázka:** mají zakladatelé sousedit i mezi sebou? A mají být padlé říše
způsobilé jen podle 7a, bez ztráty bohatství a nesplácení (**výklad enginu:** ano)?

### O1. `hash(ID)` není reprodukovatelný

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (3.4).**

Vestavěná funkce `hash()` řetězců dává v Pythonu při každém spuštění jiný výsledek. **Výklad enginu:**
místo ní stabilní CRC32 z ID NPC. Všechny nabídky na totéž NPC v jednom tahu tak dostanou stejný hod.

### O2. Síla nových NPC

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (1).**

Tabulka nových NPC `power` neuvádí. **Výklad enginu:** průměr síly běžných NPC s bohatstvím v rozmezí ±10:
N13 8, N14 8, N15 7, N16 4.

### O3. Mapa nových NPC

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (1).**

N13 má sousedit s A, N1, N8 a N11, které jsou už navzájem propojené; bez křížení vazeb to na rovině nejde.
**Výklad:** pozice s nejmenším počtem křížení. N13 (250, 520) kříží 2 vazby, N14 (430, 230) 0, N15 (730, 130) 0,
N16 (730, 460) 1.

### O4. Cena ve skóre 3.4, když NPC kupuje

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (3.4).**

Člen `30 × (nabízená cena / tržní cena − 1)` zvýhodňuje vyšší cenu. **Výklad enginu:** počítá se z pohledu NPC;
když NPC nakupuje, vyšší cena skóre snižuje.

### O5. Co je „podmínka“ u jednotlivých akcí

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (3.4).**

**Výklad enginu:** `trade_offer` objem −30 %, `loan` částka −30 %. U `protect` a `admit` nic relevantního není,
přijetí s podmínkou je tedy přijetí beze změny.

### O6. Protinávrhy

> **Částečně vyřešeno v1.7 (3.4): půjčka s částkou z protinávrhu projde bez hodu. Parametry protinávrhu u `trade_offer` zůstávají výkladem enginu, viz Q7.**

**Výklad enginu:** u `trade_offer` cena o 10 % ve prospěch NPC při stejném objemu, a ten projde v dalších 3 tazích
bez hodu. U `loan` NPC navrhne částku −30 % jen zprávou, automatické přijetí pravidlo neurčuje. U `protect`
a `admit` jen zpráva.

### O7. `trade_offer` mezi hráči

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (3.2).**

Vůli podle 3.4 mají jen NPC. **Výklad enginu:** `trade_offer` na druhého hráče projde, má-li cíl přebytek nebo
deficit a je-li cena v pásmu, bez hodu.

### O8. Sankce mezi hráči a cílené obchody

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (3.2).**

**Výklad enginu:** sankce mezi hráči přeruší jen jejich automatický obchod; cílené obchody mezi nimi trvají.

### O9. 3.4 u Unie a práh práva

> **Vyřešeno v1.7 (7.4): práh práva je u `admit` tvrdá podmínka.**

**Výklad enginu:** vůli NPC podléhají i půjčky Unie; člen vlivu je u Unie 0. U `admit` je splnění `law_threshold`
jen faktor skóre (+10 / −30), ne tvrdá podmínka, přestože 7.4 ho u přitažlivosti dál uvádí jako podmínku.

### O11. Nabídka `sell`

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (3.5).**

**Výklad enginu:** množství = menší z přebytku NPC nad rezervu a dovozu hráče v tomto tahu. Při `openness ≤ 3`
platí cena 1.15× i tehdy, když má NPC `wealth` pod 25.

### O12. Výše `loan_request`

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (3.5).**

„10 až 20 podle deficitu“. **Výklad enginu:** 10 + max(0, 15 − `wealth`) + 5 × chybějící orit, se stropem 20.

### O13. Výběr a pořadí nabídek

> **Vyřešeno v1.7 (3.5): nejvýš jedno `sell` na hráče a tah.**

**Výklad enginu:** jedno NPC dá hráči nejvýš jednu nabídku, typy se zkoušejí v pořadí `sell`, `loan_request`,
`protect_request`. Unie dostává jen `loan_request`, a to od nezávislých NPC a kandidátů.

### O14. Platnost a ignorování nabídek

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (3.5).**

**Výklad enginu:** nabídka z tahu t jde přijmout v tazích t+1 a t+2. Neprijatá propadne na konci tahu t+2 a počítá
se jako ignorovaná; po třetí v řadě od téhož NPC klesne vliv o 1 a počítadlo se nuluje. Unie vliv nemá.

### O15. Přijatá nabídka `sell`

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (3.5).**

**Výklad enginu:** jednorázový obchod v tomtéž tahu; jako cílený obchod s hráčem přidá v 4.4 vliv +1.

### O18. Z čeho se doplňuje rezerva

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (4.1a).**

**Výklad enginu:** doplnění se platí jen z bohatství nad 25, deficit toku smí stát pokrýt celým bohatstvím.

### O19. Kdy se počítají držené sféry

> **Potvrzeno 14. 9. 2026, zapsáno do pravidel v1.7 (4.4).**

**Výklad enginu:** přetížení sfér se počítá z počtu sfér v okamžiku každého přírůstku vlivu.

---

## P. Testy pravidel v1.7 (14. 9. 2026)

### Souhrn

| scénář | kritérium | výsledek |
|---|---|---|
| (0) nikdo netáhne | do tahu 15 nejvýš dvě NPC v bídě | prošlo, 0 NPC: žádné |
| (0) | do tahu 15 v bídě žádné z N1 až N5, N7, N11 až N14 | prošlo, žádné |
| (0) | `W_real` v tahu 30 aspoň 90 % startu | prošlo, 141.3 % z 864 |
| (0) | do tahu 90 nejvýš 6 NPC v bídě z 16 | prošlo, nejvíc 0 najednou, různých za běh 0 |
| (a) scénář ze zadání | crash mezi dnem 7 a 11 | prošlo, tah 33, den 11 |
| (a) | Unie s aspoň 3 zakladateli | prošlo, N4, N7, N16, N3 (tah 33) |
| (a) | validate 0 chyb | prošlo |
| (b) realistické půjčování | crash mezi dnem 7 a 11 | prošlo, tah 25, den 9 |
| (b) | Unie s aspoň 3 zakladateli | prošlo, N1, N13, N8, N2 (tah 25) |
| (b) | validate 0 chyb | prošlo |

**Všechny tři scénáře poprvé splnily všechna kritéria.** Validace hlásí 0 chyb ve všech 90 tazích.
Výchozí zásoby jsem podle potvrzeného I4 přepočítal s novou potřebou `goods` (Q5); kalibraci jsem nedělal.

### P1. Scénář (0): rozpis N11, N13, N8 a N16

Žádné NPC do bídy nepadlo, rozpis je proto průměr za tah přes celých 90 tahů. „Ostatní“ je všude nulové,
účty se uzavírají.

| NPC | v bídě od | tahů v bídě | období rozpisu | prodej (dostal) | nákup (zaplatil) | z toho doplnění | z toho přirážka | pokuty | příjem 4.2b | investice | průzkum | solidarita | příspěvek Unii | ostatní | **čistě** | kapacita / plán / výroba goods | `wealth` na konci období |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N8 | nepadlo | 0 | tahy 1 až 90 | +1.09 | -1.39 | +0.00 | -0.07 | +0.00 | +1.33 | +0.00 | -1.07 | +0.00 | +0.00 | +0.00 | **-0.03** | 2.00 / 1.04 / 1.04 | 19.1 |
| N11 | nepadlo | 0 | tahy 1 až 90 | +0.29 | -0.00 | -0.00 | -0.00 | +0.00 | +0.83 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | **+1.12** | 20.00 / 2.00 / 2.00 | 191.1 |
| N13 | nepadlo | 0 | tahy 1 až 90 | +0.00 | -1.26 | +0.00 | -0.16 | +0.00 | +2.00 | -0.11 | -0.98 | +0.00 | +0.00 | -0.00 | **-0.35** | 20.00 / 1.56 / 1.56 | 18.9 |
| N16 | nepadlo | 0 | tahy 1 až 90 | +0.11 | -1.60 | +0.00 | -0.08 | +0.00 | +1.50 | +0.00 | -0.07 | +0.00 | +0.00 | -0.00 | **-0.05** | 1.96 / 1.16 / 1.16 | 17.4 |

Co z rozpisu plyne:

1. **N11 už nekrachuje na nákupu vstupů.** Kapacita jeho továren je 20, plánuje ale vyrábět jen 2 pro vlastní
   potřebu, takže vstupy skoro nekupuje (nákup 0.00 za tah) a čistě vydělává 1.12 za tah.
2. **N13, N8 a N16 jsou těsně pod nulou.** Čistý tok je −0.35, −0.03 a −0.05 za tah a jejich bohatství v tahu 90
   je 18.9, 19.1 a 17.4, tedy blízko hranice bídy 15 (Q11). V devadesátitahové hře do bídy nepadnou.
3. **U N13 je rozdíl proti v1.6 největší.** Místo nákupu vstupů za 6.44 za tah dnes utratí 1.26 a továrny s kapacitou
   20 plánují jen 1.56.

### P2. Co z běhů plyne

1. **Výroba teď sleduje poptávku a trh s `goods` se vyrovnal.** Ve (0) je v tahu 90 kapacita 178.8,
   plán 44.8 a spotřeba 44.8; 75 % kapacity stojí. Cena `goods` se z dolní meze 1.05
   zvedla na 1.50. Prodává se ale skoro nic (0.0 v tahu 90), každý stát si vyrobí sám, co spotřebuje.
2. **Ropa spadla na dolní mez.** Od tahu 2 (0), 2 (a) a 2 (b) stojí ropa 0.70, protože
   průmysl už nekupuje vstupy pro plnou kapacitu (Q9).
3. **Bída a převraty výrazně ubyly.** Převratů je 0 (0), 34 (a) a 26 (b), ve v1.6 97, 64 a 75.
   Index v tahu 90 je 95.92 (0), 91.89 (a) a 84.54 (b).
4. **Bohatství se hromadí u hráčů.** Ve (0) mají A a B v tahu 90 737 a 553,
   nejbohatší aktér drží 36 % světového bohatství a `W_real` je 2.36násobek startu,
   takže index drží strop 1.5 (Q10).
5. **Zakladatelé Unie spolu sousedí a padlé říše mezi nimi nejsou.** Ve všech třech scénářích má každý zakladatel
   souseda mezi ostatními zakladateli a žádná padlá říše nebyla způsobilá.
6. **Fond Unie se hromadí.** V tahu 90 má fond 48.18 (0), 106.37 (a) a 184.38 (b); solidarita posílá jen členům
   v bídě, a ti skoro nejsou (Q12).
7. **Nabídky se rozdělily.** Hráči A a B teď dostávají i `loan_request` (ve (b) 83 a
   83 za běh) vedle `sell` (97 a 97).
8. **Vůle NPC u půjček ve (b):** přijato 16, s podmínkou 11, protinávrh 5,
   odmítnuto 6. Okno krachu to nerozbilo.

### P.0 Scénář (0): nikdo netáhne

Hráči mlčí, žádné akce.

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

Pojistka cyklu: do `overtrading` v tahu 58, do `distress` v tahu 66. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 89.26 | 898.2 | 0 | 0.75 | 1.09 | 0.90 | 1.05 | - |
| 12 | 95.78 | 1036.9 | 0 | 0.72 | 0.70 | 0.84 | 1.50 | 8.05 |
| 30 | 102.25 | 1221.0 | 0 | 0.64 | 0.70 | 0.84 | 1.50 | 7.00 |
| 45 | 103.45 | 1441.5 | 0 | 0.61 | 0.70 | 0.84 | 1.50 | 7.00 |
| 60 | 99.47 | 1656.1 | 0 | 0.59 | 0.70 | 0.84 | 1.49 | 73.25 |
| 90 | 95.92 | 2043.1 | 0 | 0.58 | 0.70 | 0.84 | 1.50 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 0 | - |
| 30 | 0 | - |
| 90 | 0 | - |

#### Unie: zakladatelé, členové, fond a solidarita

Způsobilých států: 9, souvislé skupiny o velikostech 5, 2, 2.

| zakladatel / kandidát při vzniku | role | `law` | `wealth` |
|---|---|---|---|
| N4 | zakladatel | 6.0 | 32.83 |
| N7 | zakladatel | 4.0 | 18.94 |
| N2 | zakladatel | 4.0 | 18.25 |
| N10 | zakladatel | 4.0 | 19.51 |
| N15 | kandidát | 3.0 | 19.51 |

| tah | vztah k založení | členů | kdo | kandidátů | kdo | fond | solidarita v tahu | solidarita od vzniku |
|---|---|---|---|---|---|---|---|---|
| 60 | tah 60 | 0 | - | 0 | - | - | 0.00 | - |
| 69 | vznik | 4 | N4, N7, N2, N10 | 1 | N15 | 8.95 | 0.00 | 0.00 |
| 75 | +6 tahů | 4 | N4, N7, N2, N10 | 1 | N15 | 19.62 | 0.00 | 0.00 |
| 87 | +18 tahů | 4 | N4, N7, N2, N10 | 1 | N15 | 42.27 | 0.00 | 0.00 |
| 90 | tah 90 | 4 | N4, N7, N2, N10 | 1 | N15 | 48.18 | 0.00 | 0.00 |

#### Sféry před krachem a po něm

| hráč | tah 68 (před krachem) | tah 69 (krach) |
|---|---|---|
| A | 0 | 0 |
| B | 0 | 0 |

#### Světová bilance goods

| tah | kapacita továren | plánovaná výroba | skutečná výroba | spotřeba | prodáno | cena |
|---|---|---|---|---|---|---|
| 1 | 89.0 | 37.6 | 37.6 | 38.6 | 1.3 | 1.05 |
| 30 | 148.6 | 43.4 | 43.4 | 43.4 | 0.1 | 1.50 |
| 60 | 172.4 | 44.2 | 44.2 | 44.0 | 0.0 | 1.49 |
| 90 | 178.8 | 44.8 | 44.8 | 44.8 | 0.0 | 1.50 |

#### Světová bilance ropy a obilí

| tah | ropa výroba | ropa domácnosti | ropa průmysl | ropa pokuty | obilí výroba | obilí domácnosti | obilí pokuty |
|---|---|---|---|---|---|---|---|
| 1 | 52.4 | 12.3 | 18.8 | 0.00 | 65.6 | 61.6 | 0.00 |
| 30 | 60.2 | 12.3 | 21.7 | 0.00 | 77.8 | 61.6 | 0.00 |
| 60 | 63.0 | 12.3 | 22.1 | 0.00 | 83.0 | 61.6 | 0.00 |
| 90 | 63.0 | 12.3 | 22.4 | 0.00 | 84.5 | 61.6 | 0.00 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) | A s B |
|---|---|---|---|---|
| 6 | 12.70 | 17.52 | 1.98 | 2.66 |
| 30 | 10.34 | 13.74 | 0.13 | 2.06 |
| 60 | 9.63 | 13.45 | 0.00 | 2.02 |
| 90 | 7.27 | 9.86 | 0.00 | 2.02 |

Obchod A s B v tazích 6, 30 a 60: 2.66, 2.06 a 2.02. Za celý běh proběhl v 90 tazích v objemu 197.96.

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 36 | 3 | 2 | 0 |
| 30 | 29 | 6 | 4 | 0 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N6 | 3.29 | 11.48 |
| N7 | 2.67 | 8.01 |
| N1 | 0.99 | 3.57 |
| N2 | 1.06 | 2.52 |
| N4 | 0.46 | 1.64 |

#### Rozhodování NPC podle 3.4

Žádná cílená akce, žádné vyhodnocení.

#### Nabídky NPC podle 3.5

| hráč | typ | vygenerováno | přijato skriptem |
|---|---|---|---|
| A | `loan_request` | 24 | 0 |
| A | `sell` | 156 | 0 |
| B | `loan_request` | 24 | 0 |
| B | `sell` | 156 | 0 |

#### Zásoby světa (součet 18 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 401.4 | 154.7 | 121.5 | 258.2 | 0.0 |
| 30 | 377.8 | 167.7 | 142.9 | 264.2 | 257.8 |
| 60 | 384.0 | 179.7 | 162.1 | 265.5 | 263.2 |
| 90 | 393.0 | 210.0 | 163.5 | 265.8 | 280.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **0**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 129.5 | 113.0 | 337.6 | 268.1 |
| 60 | 161.5 | 134.9 | 557.9 | 424.7 |
| 90 | 191.1 | 157.2 | 736.6 | 553.1 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 6.13 | 6.0 / 4.90 | 2.0 / 2.60 | 1.0 / 1.10 | 7.1 / 1.25 |
| 30 | 10.0 / 9.30 | 6.0 / 8.40 | 3.5 / 3.28 | 1.0 / 1.19 | 10.0 / 1.57 |
| 60 | 10.0 / 9.20 | 6.0 / 8.40 | 5.0 / 3.22 | 1.0 / 1.19 | 10.0 / 1.84 |
| 90 | 10.0 / 9.20 | 6.0 / 8.40 | 5.9 / 3.10 | 1.0 / 1.19 | 10.0 / 2.00 |

### P.a Varianta (a): scénář ze zadání

A půjčuje N6 od tahu 8, B chrání N7, oba obchodují obilím. Skript přijímá `sell`, které kryjí deficit hráče, a `loan_request` v boom a euphoria.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 9 | 3 | prvni loan po displacementu |
| `euphoria` | 14 | 5 | cena oritu >= 20 |
| `overtrading` | 22 | 8 | pojistka cyklu: 8 tahu bez splneni prahu |
| `distress` | 30 | 10 | pojistka cyklu: 8 tahu bez splneni prahu |
| `panic` | 32 | 11 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 33 | 11 | po jednom tahu paniky |
| `depression` | 39 | 13 | 6 tahu po crash |
| `recovery` | 45 | 15 | 12 tahu po crash |

Pojistka cyklu: do `overtrading` v tahu 22, do `distress` v tahu 30. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 89.26 | 898.2 | 0 | 0.75 | 1.09 | 0.90 | 1.05 | - |
| 12 | 97.42 | 1011.6 | 0 | 0.93 | 0.70 | 0.84 | 1.42 | 17.35 |
| 30 | 86.04 | 1205.0 | 4 | 0.92 | 0.70 | 0.84 | 1.48 | 129.77 |
| 45 | 61.78 | 926.7 | 5 | 0.56 | 0.70 | 0.84 | 1.48 | 3.50 |
| 60 | 91.92 | 1156.4 | 2 | 0.56 | 0.70 | 0.84 | 1.51 | 3.50 |
| 90 | 91.89 | 1504.8 | 2 | 0.56 | 0.70 | 0.84 | 1.51 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 2 | N1, N16 |
| 30 | 4 | N1, N5, N10, N14 |
| 90 | 2 | N8, N10 |

#### Unie: zakladatelé, členové, fond a solidarita

Způsobilých států: 12, souvislé skupiny o velikostech 12.

| zakladatel / kandidát při vzniku | role | `law` | `wealth` |
|---|---|---|---|
| N4 | zakladatel | 6.0 | 30.05 |
| N7 | zakladatel | 4.0 | 19.66 |
| N16 | zakladatel | 4.0 | 19.40 |
| N3 | zakladatel | 3.0 | 62.43 |
| N13 | kandidát | 6.0 | 19.86 |
| N1 | kandidát | 5.1 | 3.81 |
| N14 | kandidát | 5.0 | 1.28 |

| tah | vztah k založení | členů | kdo | kandidátů | kdo | fond | solidarita v tahu | solidarita od vzniku |
|---|---|---|---|---|---|---|---|---|
| 33 | vznik | 4 | N4, N7, N16, N3 | 3 | N13, N1, N14 | 13.15 | 0.00 | 0.00 |
| 39 | +6 tahů | 7 | N4, N7, N16, N3, N5, N13, N1 | 3 | N14, N10, N15 | 14.51 | 3.00 | 18.00 |
| 51 | +18 tahů | 7 | N4, N7, N16, N5, N13, N1, N14 | 2 | N10, N15 | 21.28 | 3.00 | 51.00 |
| 60 | tah 60 | 7 | N4, N7, N16, N5, N13, N1, N14 | 3 | N10, N15, N8 | 34.09 | 0.00 | 60.00 |
| 90 | tah 90 | 7 | N4, N7, N16, N5, N13, N1, N14 | 3 | N10, N15, N8 | 106.37 | 0.00 | 72.00 |

#### Sféry před krachem a po něm

| hráč | tah 32 (před krachem) | tah 33 (krach) |
|---|---|---|
| A | 1 | 0 |
| B | 0 | 0 |

#### Světová bilance goods

| tah | kapacita továren | plánovaná výroba | skutečná výroba | spotřeba | prodáno | cena |
|---|---|---|---|---|---|---|
| 1 | 89.0 | 37.6 | 37.6 | 38.6 | 1.3 | 1.05 |
| 30 | 142.5 | 45.2 | 45.2 | 44.8 | 1.6 | 1.48 |
| 60 | 133.5 | 36.2 | 36.2 | 36.4 | 1.8 | 1.51 |
| 90 | 133.6 | 35.6 | 35.6 | 35.8 | 2.0 | 1.51 |

#### Světová bilance ropy a obilí

| tah | ropa výroba | ropa domácnosti | ropa průmysl | ropa pokuty | obilí výroba | obilí domácnosti | obilí pokuty |
|---|---|---|---|---|---|---|---|
| 1 | 52.4 | 12.3 | 18.8 | 0.00 | 65.6 | 61.6 | 0.00 |
| 30 | 64.3 | 11.5 | 22.6 | 0.00 | 50.9 | 57.4 | 0.00 |
| 60 | 56.8 | 9.4 | 18.1 | 0.00 | 117.4 | 47.1 | 0.00 |
| 90 | 56.9 | 9.3 | 17.8 | 0.00 | 125.4 | 46.7 | 0.00 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) | A s B |
|---|---|---|---|---|
| 6 | 8.99 | 141.15 | 2.19 | 2.69 |
| 30 | 18.19 | 20.35 | 2.40 | 2.48 |
| 60 | 3.69 | 13.20 | 2.74 | 0.00 |
| 90 | 3.50 | 13.26 | 3.06 | 0.00 |

Obchod A s B v tazích 6, 30 a 60: 2.69, 2.48 a 0.00. Za celý běh proběhl v 32 tazích v objemu 77.41.

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 35 | 3 | 2 | 0 |
| 30 | 31 | 3 | 4 | 0 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N6 | 7.62 | 11.53 |
| N7 | 4.94 | 7.32 |
| N4 | 1.05 | 2.95 |
| N1 | 2.34 | 2.58 |
| N2 | 1.78 | 1.94 |
| N8 | 0.59 | 0.71 |
| N3 | 0.30 | 0.30 |

#### Rozhodování NPC podle 3.4

| akce | přijato | s podmínkou | protinávrh | odmítnuto |
|---|---|---|---|---|
| `trade_offer` | 0 | 0 | 2 | 0 |
| `loan` | 70 | 11 | 1 | 1 |
| `protect` | 0 | 0 | 0 | 1 |

#### Nabídky NPC podle 3.5

| hráč | typ | vygenerováno | přijato skriptem |
|---|---|---|---|
| A | `loan_request` | 83 | 0 |
| A | `sell` | 97 | 95 |
| B | `loan_request` | 84 | 13 |
| B | `sell` | 96 | 93 |
| C | `loan_request` | 73 | 0 |

#### Zásoby světa (součet 18 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 401.4 | 154.7 | 121.5 | 258.2 | 0.0 |
| 30 | 167.4 | 179.1 | 157.9 | 272.8 | 213.9 |
| 60 | 309.3 | 214.8 | 171.1 | 275.9 | 227.6 |
| 90 | 291.1 | 219.9 | 172.3 | 271.0 | 235.4 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **34**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 170.5 | 118.1 | 249.1 | 212.0 |
| 60 | 200.1 | 155.4 | 262.9 | 257.9 |
| 90 | 225.1 | 178.3 | 467.7 | 376.7 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 6.13 | 6.0 / 4.90 | 2.0 / 2.60 | 1.0 / 1.10 | 7.1 / 1.25 |
| 30 | 10.0 / 10.52 | 6.0 / 8.40 | 1.5 / 1.22 | 1.0 / 1.98 | 10.0 / 1.90 |
| 60 | 10.0 / 10.71 | 5.8 / 7.72 | 0.5 / 0.58 | 1.0 / 1.22 | 10.0 / 2.00 |
| 90 | 10.0 / 11.06 | 5.8 / 7.72 | 0.5 / 0.64 | 1.0 / 1.20 | 10.0 / 2.00 |

### P.b Varianta (b): realistické půjčování

Hráč půjčí jen v tahu, kdy NPC žádá půjčku nebo má deficit oritu, nejvýš jedna půjčka na hráče a tah. Nabídky přijímá stejně jako (a).

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

Pojistka cyklu: do `overtrading` v tahu 22. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 89.26 | 898.2 | 0 | 0.75 | 1.09 | 0.90 | 1.05 | - |
| 12 | 93.46 | 996.9 | 0 | 0.95 | 0.70 | 0.84 | 1.49 | 17.91 |
| 30 | 85.47 | 1025.2 | 1 | 0.56 | 0.70 | 0.84 | 1.49 | 2.10 |
| 45 | 89.11 | 1182.7 | 2 | 0.56 | 0.70 | 0.84 | 1.50 | 3.50 |
| 60 | 96.47 | 1335.0 | 2 | 0.56 | 0.70 | 0.84 | 1.50 | 3.50 |
| 90 | 84.54 | 1666.3 | 3 | 0.56 | 0.70 | 0.84 | 1.50 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 1 | N10 |
| 30 | 1 | N16 |
| 90 | 3 | N3, N10, N16 |

#### Unie: zakladatelé, členové, fond a solidarita

Způsobilých států: 14, souvislé skupiny o velikostech 14.

| zakladatel / kandidát při vzniku | role | `law` | `wealth` |
|---|---|---|---|
| N1 | zakladatel | 6.6 | 70.18 |
| N13 | zakladatel | 5.2 | 1.59 |
| N8 | zakladatel | 2.6 | 34.45 |
| N2 | zakladatel | 5.4 | 38.61 |
| N4 | kandidát | 5.1 | 15.36 |
| N5 | kandidát | 5.0 | 5.19 |
| N14 | kandidát | 5.0 | 16.18 |

| tah | vztah k založení | členů | kdo | kandidátů | kdo | fond | solidarita v tahu | solidarita od vzniku |
|---|---|---|---|---|---|---|---|---|
| 25 | vznik | 4 | N1, N13, N8, N2 | 3 | N4, N5, N14 | 14.48 | 0.00 | 0.00 |
| 31 | +6 tahů | 7 | N1, N13, N8, N2, N4, N5, N14 | 2 | N10, N16 | 24.33 | 0.00 | 12.00 |
| 43 | +18 tahů | 6 | N13, N8, N2, N4, N5, N14 | 2 | N10, N16 | 58.18 | 0.00 | 12.00 |
| 60 | tah 60 | 6 | N13, N8, N2, N4, N5, N14 | 2 | N10, N16 | 103.62 | 0.00 | 12.00 |
| 90 | tah 90 | 6 | N13, N8, N2, N4, N5, N14 | 3 | N10, N16, N3 | 184.38 | 0.00 | 12.00 |

#### Sféry před krachem a po něm

| hráč | tah 24 (před krachem) | tah 25 (krach) |
|---|---|---|
| A | 1 | 0 |
| B | 1 | 0 |

#### Světová bilance goods

| tah | kapacita továren | plánovaná výroba | skutečná výroba | spotřeba | prodáno | cena |
|---|---|---|---|---|---|---|
| 1 | 89.0 | 37.6 | 37.6 | 38.6 | 1.3 | 1.05 |
| 30 | 130.6 | 41.5 | 41.5 | 41.3 | 0.6 | 1.49 |
| 60 | 147.4 | 39.8 | 39.8 | 39.8 | 0.0 | 1.50 |
| 90 | 147.3 | 39.7 | 39.7 | 39.7 | 0.0 | 1.50 |

#### Světová bilance ropy a obilí

| tah | ropa výroba | ropa domácnosti | ropa průmysl | ropa pokuty | obilí výroba | obilí domácnosti | obilí pokuty |
|---|---|---|---|---|---|---|---|
| 1 | 52.4 | 12.3 | 18.8 | 0.00 | 65.6 | 61.6 | 0.00 |
| 30 | 60.4 | 11.5 | 20.7 | 0.00 | 148.3 | 57.4 | 0.00 |
| 60 | 62.9 | 10.9 | 19.9 | 0.00 | 133.5 | 54.5 | 0.00 |
| 90 | 60.9 | 10.8 | 19.9 | 0.00 | 133.4 | 54.1 | 0.00 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) | A s B |
|---|---|---|---|---|
| 6 | 8.99 | 141.15 | 2.19 | 2.69 |
| 30 | 4.42 | 8.20 | 0.93 | 2.25 |
| 60 | 2.57 | 9.45 | 0.00 | 2.02 |
| 90 | 2.42 | 9.30 | 0.00 | 2.02 |

Obchod A s B v tazích 6, 30 a 60: 2.69, 2.25 a 2.02. Za celý běh proběhl v 90 tazích v objemu 184.58.

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 35 | 3 | 2 | 0 |
| 30 | 24 | 0 | 1 | 0 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N6 | 4.92 | 4.92 |
| N7 | 4.18 | 4.31 |
| N1 | 2.20 | 2.20 |
| N2 | 1.39 | 1.52 |
| N4 | 0.89 | 0.89 |

#### Rozhodování NPC podle 3.4

| akce | přijato | s podmínkou | protinávrh | odmítnuto |
|---|---|---|---|---|
| `trade_offer` | 0 | 0 | 2 | 0 |
| `loan` | 16 | 11 | 5 | 6 |
| `protect` | 0 | 0 | 0 | 1 |

#### Nabídky NPC podle 3.5

| hráč | typ | vygenerováno | přijato skriptem |
|---|---|---|---|
| A | `loan_request` | 83 | 1 |
| A | `sell` | 97 | 96 |
| B | `loan_request` | 83 | 0 |
| B | `sell` | 97 | 96 |
| C | `loan_request` | 70 | 0 |

#### Zásoby světa (součet 18 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 401.4 | 154.7 | 121.5 | 258.2 | 0.0 |
| 30 | 384.0 | 207.8 | 170.6 | 268.9 | 170.7 |
| 60 | 410.1 | 214.7 | 172.9 | 270.7 | 220.0 |
| 90 | 419.1 | 211.8 | 173.8 | 270.7 | 220.6 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **26**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 152.8 | 126.0 | 243.3 | 177.2 |
| 60 | 177.8 | 150.9 | 369.1 | 367.6 |
| 90 | 202.8 | 175.9 | 469.2 | 539.3 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 6.13 | 6.0 / 4.90 | 2.0 / 2.60 | 1.0 / 1.10 | 7.1 / 1.25 |
| 30 | 10.0 / 9.59 | 6.0 / 8.08 | 5.0 / 3.84 | 1.0 / 1.13 | 10.0 / 1.76 |
| 60 | 10.0 / 9.20 | 6.0 / 8.40 | 9.9 / 3.21 | 1.0 / 1.19 | 10.0 / 1.97 |
| 90 | 10.0 / 9.20 | 6.0 / 8.40 | 10.0 / 3.09 | 1.0 / 1.17 | 10.0 / 2.00 |

---

## Q. Nově otevřené otázky z implementace v1.7

Neopravuji je, engine u každé používá uvedený výklad. Nejdůležitější jsou Q9 a Q10, protože ukazují,
kam se po vyrovnání trhu s produktem přesunula nerovnováha.

### Q9. Ropa na dolní mezi ceny

> **Řešeno v1.8 snížením produkce ropy N3 (11 na 10) a B (10 na 9). Ropa ale v testech dál leží na dolní mezi, viz S8.**

S výrobou podle poptávky kupuje průmysl ropu jen pro plánovanou výrobu. Světová poptávka po ropě tím spadla
a cena ropy je ve všech scénářích od tahu 2 trvale na dolní mezi 0.70. Jen v tahu 1 stojí 1.09, protože ceny
prvního tahu počítají s předběžným odhadem při plném využití továren (4.1b). Kalibrace ropy z v1.6 počítala
s průmyslem, který kupuje vstupy pro plnou kapacitu. **Otázka:** vrátit se ke kalibraci ropy, nebo je levná
ropa v klidném světě záměr?

### Q10. Bohatství se hromadí u hráčů

> **Potvrzeno 18. 9. 2026: stávající chování enginu zůstává.**

Ve (0), kde hráči netáhnou, mají A a B v tahu 90 dohromady přes polovinu světového bohatství a `W_real` je víc
než dvojnásobek startu; index tak drží strop 1.5. **Otázka:** má bohatství hráčů, kteří nic nedělají, takto
růst, nebo potřebují hráči výdaje (například údržbu armády)?

### Q11. Pomalu chudnoucí NPC

> **Potvrzeno 18. 9. 2026: stávající chování enginu zůstává.**

N13, N8 a N16 mají ve (0) záporný čistý tok a v tahu 90 bohatství 17 až 19. V hře delší než 90 tahů by padly
do bídy. Pro devadesátitahovou hru to nevadí; uvádím pro případné prodloužení.

### Q12. Fond Unie se nepoužívá

> **Potvrzeno 18. 9. 2026: stávající chování enginu zůstává; fond nově plní i clo (7.2).**

Solidarita posílá jen členům v bídě, a těch je teď málo; fond v tahu 90 dosahuje desítek až 184. Příspěvky 2 %
se z něj nevracejí. **Otázka:** má mít fond i jiné automatické využití, nebo je to rezerva pro Unii jako hráče?

### Q1. Plánovaná výroba nula

> **Potvrzeno 18. 9. 2026, zapsáno do pravidel v1.8 (4.0).**

**Výklad enginu:** když stát nic neplánuje vyrábět, je `coverage` 0, a v 4.2c mu tedy průmysl neroste.

### Q2. Z jakého bohatství se počítá potřeba `goods`

> **Potvrzeno 18. 9. 2026, zapsáno do pravidel v1.8 (4.0).**

**Výklad enginu:** z `wealth` na začátku přepočtu zdrojů; hodnota se na celý tah zmrazí, aby se potřeba neměnila
uprostřed obchodu. Ceny na začátku tahu (4.1b) berou potřebu z minulého tahu.

### Q3. Co je „prodané množství v minulém tahu“

> **Potvrzeno 18. 9. 2026, zapsáno do pravidel v1.8 (4.0).**

**Výklad enginu:** `goods` prodané na automatickém trhu a cílenými obchody; bezplatné převody vnitřního trhu Unie
se nepočítají.

### Q4. Doplnění rezervy `goods` v plánu výroby

> **Potvrzeno 18. 9. 2026, zapsáno do pravidel v1.8 (4.0).**

**Výklad enginu:** 3 tahy spotřeby minus zásoba `goods`. Doplňuje se vlastní výrobou, proto na něj neplatí práh
`wealth ≥ 25`, který se týká nákupu.

### Q5. Přepočet výchozích zásob

> **Potvrzeno 18. 9. 2026, zapsáno do pravidel v1.8 (4.1c).**

Podle potvrzeného I4 jsem výchozí zásoby přepočítal s novou potřebou `goods`. **Výklad:** výroba bez obchodu je
`min(kapacita, vlastní potřeba goods)`. Změnily se zásoby `goods` všech států kromě N3 a u N11, N12, N14 a N15
i zásoby ropy a kovů, protože jejich továrny už nepotřebují vstupy pro plnou kapacitu.

### Q6. Nabídky bez `sell`

> **Potvrzeno 18. 9. 2026, zapsáno do pravidel v1.8 (3.5).**

Pravidlo 3.5 neříká, co s druhým místem, když žádná `sell` není. **Výklad enginu:** obě místa dostanou `loan_request`
nebo `protect_request` s nejvyšším vlivem. Jedno NPC dá hráči nejvýš jednu nabídku daného druhu a u jednoho NPC
má `loan_request` přednost před `protect_request`.

### Q7. Parametry protinávrhu u `trade_offer`

> **Potvrzeno 18. 9. 2026, zapsáno do pravidel v1.8 (3.4).**

O6 nebylo u obchodu potvrzeno. **Výklad enginu:** protinávrh posune cenu o 10 % ve prospěch NPC při stejném objemu.

### Q8. Shoda při hladovém výběru zakladatelů

> **Potvrzeno 18. 9. 2026, zapsáno do pravidel v1.8 (7.1).**

**Výklad enginu:** při shodě `law` i `wealth` rozhoduje nižší ID.

---

## R. Testy pravidel v1.8 (18. 9. 2026)

### Souhrn

| scénář | kritérium | výsledek |
|---|---|---|
| (0) nikdo netáhne | do tahu 15 nejvýš dvě NPC v bídě | prošlo, 0 NPC: žádné |
| (0) | do tahu 15 v bídě žádné z N1 až N5, N7, N11 až N14 | prošlo, žádné |
| (0) | `W_real` v tahu 30 aspoň 90 % startu | prošlo, 144.8 % z 864 |
| (0) | do tahu 90 nejvýš 6 NPC v bídě z 16 | prošlo, nejvíc 3 najednou, různých za běh 3 |
| (a) scénář ze zadání | crash mezi dnem 7 a 11 | prošlo, tah 33, den 11 |
| (a) | Unie s aspoň 3 zakladateli | prošlo, N5, N14, N3, N4 (tah 33) |
| (a) | validate 0 chyb | prošlo |
| (b) realistické půjčování | crash mezi dnem 7 a 11 | prošlo, tah 25, den 9 |
| (b) | Unie s aspoň 3 zakladateli | prošlo, N1, N13, N8, N2 (tah 25) |
| (b) | validate 0 chyb | prošlo |

Validace hlásí 0 chyb ve všech třech scénářích a všech 90 tazích. Výchozí zásoby jsem podle 4.1c a I4 přepočítal
s komparativní výhodou (S7); změnily se jen zásoby ropy a kovů N11 a N12. Kalibraci jsem nedělal.

### R1. Scénář (0): rozpis N11, N13, N8 a N16

Rozpis je průměr za tah od začátku do prvního tahu v bídě, u NPC, které nepadlo, přes celých 90 tahů.
„Prodej“ je hrubý příjem před clem, „clo“ je clo, které NPC zaplatilo; „ostatní“ je všude nulové, účty se uzavírají.

| NPC | v bídě od | tahů v bídě | období rozpisu | prodej | nákup | clo | pokuty | příjem 4.2b | investice | průzkum | solidarita | příspěvek Unii | tranzit | ostatní | **čistě** | pokuty podle statku | kapacita / plán / výroba goods | `wealth` na konci období |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N8 | tah 18 | 73 | tahy 1 až 18 | +0.00 | -1.73 | +0.00 | +0.00 | +1.33 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | **-0.39** | - | 1.15 / 0.50 / 0.50 | 14.9 |
| N16 | tah 47 | 14 | tahy 1 až 47 | +0.35 | -1.95 | +0.00 | +0.00 | +1.49 | +0.00 | -0.04 | +0.00 | +0.00 | +0.00 | -0.00 | **-0.16** | - | 0.82 / 0.43 / 0.43 | 14.6 |
| N10 | tah 56 | 14 | tahy 1 až 56 | +0.03 | -1.30 | +0.00 | +0.00 | +1.24 | +0.00 | -0.14 | +0.00 | +0.00 | +0.00 | -0.00 | **-0.18** | - | 0.15 / 0.07 / 0.07 | 14.8 |
| N11 | nepadlo | 0 | tahy 1 až 90 | +0.20 | -0.45 | +0.00 | +0.00 | +0.83 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | +0.00 | **+0.58** | - | 20.00 / 3.68 / 3.68 | 141.8 |
| N13 | nepadlo | 0 | tahy 1 až 90 | +0.00 | -1.62 | +0.00 | +0.00 | +2.05 | +0.00 | -0.69 | +0.00 | -0.09 | +0.00 | +0.00 | **-0.35** | - | 20.00 / 3.58 / 3.58 | 18.8 |

1. **N8 padá do bídy v tahu 18** a je v ní celkem 73 tahů. Čistý tok je -0.39 za tah (nákup -1.73, prodej +0.00, pokuty +0.00), `wealth` na konci období 14.9.
2. **N16 padá do bídy v tahu 47** a je v ní celkem 14 tahů. Čistý tok je -0.16 za tah (nákup -1.95, prodej +0.35, pokuty +0.00), `wealth` na konci období 14.6.
3. **N13 do bídy nepadá.** Čistý tok je -0.35 za tah (nákup -1.62, prodej +0.00, pokuty +0.00), `wealth` na konci období 18.8.
4. **N11 do bídy nepadá.** Čistý tok je +0.58 za tah (nákup -0.45, prodej +0.20, pokuty +0.00), `wealth` na konci období 141.8.

### R2. Co z běhů plyne

1. **Všechny tři scénáře splnily všechna kritéria.** Proti v1.7 ale přibyla bída: nejvíc NPC v bídě najednou
   je 3 (0), 7 (a) a 5 (b), převratů 15, 51 a 33
   proti 0, 34 a 26 ve v1.7. Index v tahu 90 je 89.35, 76.68 a
   83.61 proti 95.92, 91.89 a 84.54.
2. **Obchod s goods zůstal malý (S10).** Ve (0) v tahu 6: hráč s NPC 4.86; v tahu 90: hráč s NPC 1.16.
   Ve (b) v tahu 90: NPC s NPC 0.23, hráč s NPC 0.43. Velké továrny sice plánují 10 % kapacity navíc (plán ve (0) v tahu 90
   57.8 proti spotřebě 44.8), ale přebytek končí v zásobách a cena `goods` po prvních tazích
   klesá (1.27 v tahu 6, 1.16 v tahu 90).
3. **Clo přináší fondu málo.** Od vzniku Unie do tahu 90 vybrala 8.48 (0), 9.50 (a)
   a 22.76 (b).
4. **`invest_prod` míří hlavně do obilí (S9).** Za běh 14 (0), 9 (a) a 6 (b) investic, všechny od NPC.
   Světová výroba obilí ve (0) vzrostla z 65.6 na 156.8 a cena obilí v tahu 90 je
   0.56, tedy na dolní mezi.
5. **Ropa dál leží na dolní mezi (S8).** Cena 0.70 poprvé v tahu 2 (0), 2 (a) a 2 (b);
   světová výroba ropy ve (0) vzrostla z 50.0 na 66.3, i díky `invest_prod`.

### R.0 Scénář (0): nikdo netáhne

Hráči mlčí, žádné akce.

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

Pojistka cyklu: do `overtrading` v tahu 58, do `distress` v tahu 66. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 89.31 | 898.2 | 0 | 0.75 | 1.14 | 0.90 | 1.05 | - |
| 12 | 98.45 | 1056.3 | 0 | 0.71 | 0.72 | 0.84 | 1.26 | 9.18 |
| 30 | 99.22 | 1251.0 | 1 | 0.62 | 0.70 | 0.84 | 1.20 | 7.00 |
| 45 | 97.28 | 1477.6 | 1 | 0.59 | 0.70 | 0.84 | 1.17 | 7.00 |
| 60 | 82.42 | 1692.9 | 3 | 0.57 | 0.70 | 0.84 | 1.15 | 73.25 |
| 90 | 89.35 | 2009.0 | 1 | 0.56 | 0.70 | 0.84 | 1.16 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 0 | - |
| 30 | 1 | N8 |
| 90 | 1 | N8 |

#### Unie: zakladatelé, členové, fond, solidarita a clo

Způsobilých států: 11, souvislé skupiny o velikostech 9, 2.

| zakladatel / kandidát při vzniku | role | `law` | `wealth` |
|---|---|---|---|
| N4 | zakladatel | 6.0 | 35.13 |
| N7 | zakladatel | 4.0 | 19.58 |
| N2 | zakladatel | 4.0 | 19.12 |
| N16 | zakladatel | 4.0 | 16.67 |
| N13 | kandidát | 6.0 | 16.81 |
| N1 | kandidát | 5.0 | 37.62 |
| N10 | kandidát | 4.0 | 14.88 |

| tah | vztah k založení | členů | kdo | kandidátů | kdo | fond | solidarita od vzniku | clo v tahu | clo od vzniku |
|---|---|---|---|---|---|---|---|---|---|
| 60 | tah 60 | 0 | - | 0 | - | - | - | 0.00 | - |
| 69 | vznik | 4 | N4, N7, N2, N16 | 3 | N13, N1, N10 | 9.05 | 0.00 | 0.00 | 0.00 |
| 75 | +6 tahů | 7 | N4, N7, N2, N16, N13, N1, N10 | 1 | N8 | 30.85 | 0.00 | 0.42 | 2.18 |
| 87 | +18 tahů | 7 | N4, N7, N2, N16, N13, N1, N10 | 1 | N8 | 77.34 | 0.00 | 0.42 | 7.22 |
| 90 | tah 90 | 7 | N4, N7, N2, N16, N13, N1, N10 | 1 | N8 | 89.31 | 0.00 | 0.42 | 8.48 |

#### Sféry před krachem a po něm

| hráč | tah 68 (před krachem) | tah 69 (krach) |
|---|---|---|
| A | 0 | 0 |
| B | 0 | 0 |

#### Světová bilance goods

| tah | kapacita továren | plánovaná výroba | skutečná výroba | spotřeba | prodáno | cena |
|---|---|---|---|---|---|---|
| 1 | 89.0 | 41.2 | 41.2 | 38.6 | 3.8 | 1.05 |
| 30 | 146.1 | 55.6 | 55.6 | 44.3 | 2.4 | 1.20 |
| 60 | 177.6 | 58.4 | 58.4 | 44.8 | 1.2 | 1.15 |
| 90 | 172.2 | 57.8 | 57.8 | 44.8 | 1.0 | 1.16 |

#### Obchod s goods podle dvojic

| tah | NPC s NPC | hráč s NPC | A s B |
|---|---|---|---|
| 6 | 0.00 | 4.86 | 0.00 |
| 30 | 0.00 | 2.87 | 0.00 |
| 60 | 0.00 | 1.33 | 0.00 |
| 90 | 0.00 | 1.16 | 0.00 |

#### Světová výroba zdrojů a `invest_prod`

| tah | ropa | obilí | kovy | orit |
|---|---|---|---|---|
| 1 | 50.0 | 65.6 | 49.2 | 0.0 |
| 30 | 62.2 | 78.3 | 57.6 | 115.0 |
| 60 | 72.5 | 82.2 | 63.2 | 223.2 |
| 90 | 66.3 | 156.8 | 60.0 | 296.0 |

Za celý běh **14** investic `invest_prod` (NPC: grain 10, NPC: oil 4).

#### Světová bilance ropy a obilí

| tah | ropa výroba | ropa domácnosti | ropa průmysl | ropa pokuty | obilí výroba | obilí domácnosti | obilí pokuty |
|---|---|---|---|---|---|---|---|
| 1 | 50.0 | 12.3 | 20.6 | 0.00 | 65.6 | 61.6 | 0.00 |
| 30 | 62.2 | 12.1 | 27.8 | 0.00 | 78.3 | 60.5 | 0.00 |
| 60 | 72.5 | 11.7 | 29.2 | 0.00 | 82.2 | 58.4 | 0.00 |
| 90 | 66.3 | 11.7 | 28.9 | 0.00 | 156.8 | 58.4 | 0.00 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) | A s B |
|---|---|---|---|---|
| 6 | 17.46 | 17.87 | 4.86 | 4.37 |
| 30 | 14.20 | 15.34 | 2.87 | 3.74 |
| 60 | 12.47 | 13.98 | 1.33 | 3.17 |
| 90 | 4.90 | 9.42 | 1.16 | 3.14 |

Obchod A s B za celý běh proběhl v 90 tazích v objemu 316.27.

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 35 | 4 | 3 | 0 |
| 30 | 28 | 7 | 4 | 0 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N6 | 6.56 | 16.38 |
| N7 | 4.32 | 9.68 |
| N1 | 2.57 | 7.49 |
| N4 | 0.38 | 1.54 |
| N2 | 0.82 | 1.35 |

#### Rozhodování NPC podle 3.4

Žádná cílená akce, žádné vyhodnocení.

#### Nabídky NPC podle 3.5

| hráč | typ | vygenerováno | přijato skriptem |
|---|---|---|---|
| A | `loan_request` | 83 | 0 |
| A | `sell` | 97 | 0 |
| B | `loan_request` | 83 | 0 |
| B | `sell` | 97 | 0 |
| C | `loan_request` | 12 | 0 |

#### Zásoby světa (součet 18 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 401.4 | 164.5 | 128.8 | 259.3 | 0.0 |
| 30 | 380.8 | 196.7 | 144.0 | 355.7 | 203.0 |
| 60 | 398.1 | 211.6 | 160.4 | 376.5 | 220.0 |
| 90 | 406.6 | 251.4 | 196.8 | 390.2 | 220.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **15**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 122.3 | 111.3 | 343.3 | 244.3 |
| 60 | 132.5 | 134.5 | 576.7 | 383.4 |
| 90 | 141.8 | 156.7 | 741.9 | 491.1 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 7.41 | 6.0 / 5.74 | 2.0 / 2.60 | 1.0 / 0.61 | 7.1 / 2.51 |
| 30 | 10.0 / 14.11 | 6.0 / 8.40 | 2.9 / 3.78 | 1.0 / 0.59 | 10.0 / 3.50 |
| 60 | 10.0 / 12.58 | 6.0 / 8.40 | 4.1 / 3.87 | 1.0 / 0.68 | 10.0 / 3.60 |
| 90 | 10.0 / 12.39 | 6.0 / 8.40 | 5.0 / 4.69 | 1.0 / 0.60 | 10.0 / 3.68 |

### R.a Varianta (a): scénář ze zadání

A půjčuje N6 od tahu 8, B chrání N7, oba obchodují obilím. Skript přijímá `sell`, které kryjí deficit hráče, a `loan_request` v boom a euphoria.

#### Fáze

| fáze | tah | den | spouštěč |
|---|---|---|---|
| `pre` | 1 | 1 | start |
| `displacement` | 7 | 3 | tah 7 |
| `boom` | 9 | 3 | prvni loan po displacementu |
| `euphoria` | 14 | 5 | cena oritu >= 20 |
| `overtrading` | 22 | 8 | pojistka cyklu: 8 tahu bez splneni prahu |
| `distress` | 30 | 10 | pojistka cyklu: 8 tahu bez splneni prahu |
| `panic` | 32 | 11 | druhe nesplaceni nebo 2 tahy distress |
| `crash` | 33 | 11 | po jednom tahu paniky |
| `depression` | 39 | 13 | 6 tahu po crash |
| `recovery` | 45 | 15 | 12 tahu po crash |

Pojistka cyklu: do `overtrading` v tahu 22, do `distress` v tahu 30. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 89.31 | 898.2 | 0 | 0.75 | 1.14 | 0.90 | 1.05 | - |
| 12 | 98.28 | 1022.2 | 0 | 0.89 | 0.73 | 0.84 | 1.22 | 19.66 |
| 30 | 82.60 | 1165.8 | 4 | 0.75 | 0.70 | 0.84 | 1.21 | 129.77 |
| 45 | 55.87 | 878.2 | 6 | 0.56 | 0.70 | 0.84 | 1.12 | 3.50 |
| 60 | 66.58 | 1025.5 | 5 | 0.56 | 0.70 | 0.84 | 1.14 | 3.50 |
| 90 | 76.68 | 1288.8 | 5 | 0.56 | 0.70 | 0.84 | 1.12 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 2 | N10, N16 |
| 30 | 4 | N10, N13, N15, N16 |
| 90 | 5 | N8, N9, N10, N15, N16 |

#### Unie: zakladatelé, členové, fond, solidarita a clo

Způsobilých států: 13, souvislé skupiny o velikostech 13.

| zakladatel / kandidát při vzniku | role | `law` | `wealth` |
|---|---|---|---|
| N5 | zakladatel | 6.0 | 17.99 |
| N14 | zakladatel | 5.0 | 16.07 |
| N3 | zakladatel | 2.6 | 97.61 |
| N4 | zakladatel | 5.8 | 21.91 |
| N13 | kandidát | 6.0 | 1.53 |
| N2 | kandidát | 5.3 | 44.96 |
| N7 | kandidát | 4.0 | 19.49 |

| tah | vztah k založení | členů | kdo | kandidátů | kdo | fond | solidarita od vzniku | clo v tahu | clo od vzniku |
|---|---|---|---|---|---|---|---|---|---|
| 33 | vznik | 4 | N5, N14, N3, N4 | 3 | N13, N2, N7 | 15.36 | 0.00 | 0.00 | 0.00 |
| 39 | +6 tahů | 7 | N5, N14, N3, N4, N13, N2, N7 | 3 | N15, N6, N8 | 30.56 | 12.00 | 0.15 | 1.12 |
| 51 | +18 tahů | 7 | N5, N14, N3, N4, N13, N2, N7 | 3 | N15, N6, N8 | 83.74 | 12.00 | 0.07 | 2.56 |
| 60 | tah 60 | 7 | N5, N14, N3, N4, N13, N2, N7 | 3 | N15, N6, N8 | 121.73 | 12.00 | 0.18 | 3.50 |
| 90 | tah 90 | 7 | N5, N14, N3, N4, N13, N2, N7 | 3 | N15, N6, N8 | 251.38 | 12.00 | 0.20 | 9.50 |

#### Sféry před krachem a po něm

| hráč | tah 32 (před krachem) | tah 33 (krach) |
|---|---|---|
| A | 1 | 0 |
| B | 1 | 1 |

#### Světová bilance goods

| tah | kapacita továren | plánovaná výroba | skutečná výroba | spotřeba | prodáno | cena |
|---|---|---|---|---|---|---|
| 1 | 89.0 | 41.2 | 41.2 | 38.6 | 3.8 | 1.05 |
| 30 | 140.9 | 57.6 | 55.6 | 45.5 | 2.9 | 1.21 |
| 60 | 145.8 | 49.3 | 49.3 | 37.3 | 0.5 | 1.14 |
| 90 | 151.8 | 50.4 | 50.4 | 37.8 | 0.4 | 1.12 |

#### Obchod s goods podle dvojic

| tah | NPC s NPC | hráč s NPC | A s B |
|---|---|---|---|
| 6 | 0.00 | 5.09 | 0.00 |
| 30 | 0.53 | 2.99 | 0.00 |
| 60 | 0.00 | 0.53 | 0.00 |
| 90 | 0.00 | 0.49 | 0.00 |

#### Světová výroba zdrojů a `invest_prod`

| tah | ropa | obilí | kovy | orit |
|---|---|---|---|---|
| 1 | 50.0 | 65.6 | 49.2 | 0.0 |
| 30 | 58.8 | 62.8 | 57.6 | 116.7 |
| 60 | 54.3 | 122.0 | 46.8 | 175.6 |
| 90 | 54.3 | 121.9 | 46.8 | 259.4 |

Za celý běh **9** investic `invest_prod` (NPC: grain 8, NPC: oil 1).

#### Světová bilance ropy a obilí

| tah | ropa výroba | ropa domácnosti | ropa průmysl | ropa pokuty | obilí výroba | obilí domácnosti | obilí pokuty |
|---|---|---|---|---|---|---|---|
| 1 | 50.0 | 12.3 | 20.6 | 0.00 | 65.6 | 61.6 | 0.00 |
| 30 | 58.8 | 11.6 | 27.8 | 0.61 | 62.8 | 58.2 | 0.00 |
| 60 | 54.3 | 9.5 | 24.7 | 0.00 | 122.0 | 47.6 | 0.00 |
| 90 | 54.3 | 9.5 | 25.2 | 0.00 | 121.9 | 47.5 | 0.00 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) | A s B |
|---|---|---|---|---|
| 6 | 32.31 | 125.86 | 5.09 | 3.63 |
| 30 | 16.78 | 50.32 | 3.52 | 0.00 |
| 60 | 1.24 | 9.62 | 0.53 | 2.29 |
| 90 | 1.37 | 9.66 | 0.49 | 2.14 |

Obchod A s B za celý běh proběhl v 72 tazích v objemu 191.88.

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 38 | 5 | 3 | 0 |
| 30 | 27 | 6 | 7 | 0 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N6 | 8.63 | 10.98 |
| N7 | 6.76 | 7.43 |
| N1 | 3.19 | 4.65 |
| N4 | 1.05 | 1.26 |
| N2 | 0.46 | 0.46 |
| N8 | 0.12 | 0.19 |

#### Rozhodování NPC podle 3.4

| akce | přijato | s podmínkou | protinávrh | odmítnuto |
|---|---|---|---|---|
| `trade_offer` | 0 | 0 | 2 | 0 |
| `loan` | 53 | 18 | 10 | 2 |
| `protect` | 0 | 0 | 0 | 1 |

#### Nabídky NPC podle 3.5

| hráč | typ | vygenerováno | přijato skriptem |
|---|---|---|---|
| A | `loan_request` | 83 | 0 |
| A | `sell` | 97 | 95 |
| B | `loan_request` | 83 | 13 |
| B | `sell` | 97 | 96 |
| C | `loan_request` | 116 | 0 |

#### Zásoby světa (součet 18 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 401.4 | 164.5 | 128.8 | 259.3 | 0.0 |
| 30 | 266.6 | 204.6 | 165.9 | 387.8 | 188.9 |
| 60 | 370.6 | 189.1 | 198.0 | 405.3 | 186.6 |
| 90 | 377.2 | 190.3 | 198.4 | 408.6 | 172.6 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **51**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 144.2 | 121.8 | 248.3 | 177.0 |
| 60 | 154.1 | 147.7 | 208.0 | 228.9 |
| 90 | 159.8 | 171.6 | 296.0 | 371.5 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 7.41 | 6.0 / 5.74 | 2.0 / 2.60 | 1.0 / 0.61 | 7.1 / 2.51 |
| 30 | 10.0 / 14.12 | 6.0 / 8.40 | 4.5 / 5.04 | 1.0 / 1.32 | 10.0 / 3.67 |
| 60 | 10.0 / 11.76 | 6.0 / 8.40 | 8.4 / 4.67 | 0.5 / 0.44 | 10.0 / 3.78 |
| 90 | 10.0 / 11.73 | 6.0 / 8.40 | 10.0 / 5.10 | 0.5 / 0.44 | 10.0 / 3.83 |

### R.b Varianta (b): realistické půjčování

Hráč půjčí jen v tahu, kdy NPC žádá půjčku nebo má deficit oritu, nejvýš jedna půjčka na hráče a tah. Nabídky přijímá stejně jako (a).

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

Pojistka cyklu: do `overtrading` v tahu 22. Zaniklých paktů: 0.

#### Index a ceny

| tah | index | W_real | v bídě | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|---|---|---|
| 1 | 89.31 | 898.2 | 0 | 0.75 | 1.14 | 0.90 | 1.05 | - |
| 12 | 97.03 | 1015.7 | 0 | 0.89 | 0.72 | 0.84 | 1.25 | 19.66 |
| 30 | 66.84 | 974.4 | 4 | 0.56 | 0.70 | 0.84 | 1.17 | 2.10 |
| 45 | 77.88 | 1126.2 | 3 | 0.56 | 0.70 | 0.84 | 1.17 | 3.50 |
| 60 | 86.15 | 1289.7 | 3 | 0.56 | 0.70 | 0.84 | 1.13 | 3.50 |
| 90 | 83.61 | 1630.2 | 3 | 0.56 | 0.70 | 0.84 | 1.11 | 3.50 |

#### NPC v bídě

| tah | počet | NPC v bídě |
|---|---|---|
| 15 | 0 | - |
| 30 | 4 | N6, N10, N15, N16 |
| 90 | 3 | N9, N10, N16 |

#### Unie: zakladatelé, členové, fond, solidarita a clo

Způsobilých států: 14, souvislé skupiny o velikostech 14.

| zakladatel / kandidát při vzniku | role | `law` | `wealth` |
|---|---|---|---|
| N1 | zakladatel | 6.5 | 50.36 |
| N13 | zakladatel | 5.4 | 1.50 |
| N8 | zakladatel | 1.6 | 20.14 |
| N2 | zakladatel | 5.4 | 50.31 |
| N4 | kandidát | 6.0 | 24.05 |
| N5 | kandidát | 5.2 | 13.65 |
| N14 | kandidát | 5.0 | 20.79 |

| tah | vztah k založení | členů | kdo | kandidátů | kdo | fond | solidarita od vzniku | clo v tahu | clo od vzniku |
|---|---|---|---|---|---|---|---|---|---|
| 25 | vznik | 4 | N1, N13, N8, N2 | 3 | N4, N5, N14 | 12.23 | 0.00 | 0.00 | 0.00 |
| 31 | +6 tahů | 7 | N1, N13, N8, N2, N4, N5, N14 | 3 | N10, N15, N16 | 25.44 | 12.00 | 0.60 | 4.02 |
| 43 | +18 tahů | 6 | N1, N13, N8, N4, N5, N14 | 3 | N10, N15, N16 | 69.75 | 12.00 | 0.31 | 9.27 |
| 60 | tah 60 | 6 | N1, N13, N8, N4, N5, N14 | 3 | N10, N15, N16 | 127.60 | 12.00 | 0.28 | 14.07 |
| 90 | tah 90 | 6 | N1, N13, N8, N4, N5, N14 | 3 | N10, N15, N16 | 233.95 | 12.00 | 0.31 | 22.76 |

#### Sféry před krachem a po něm

| hráč | tah 24 (před krachem) | tah 25 (krach) |
|---|---|---|
| A | 1 | 0 |
| B | 0 | 0 |

#### Světová bilance goods

| tah | kapacita továren | plánovaná výroba | skutečná výroba | spotřeba | prodáno | cena |
|---|---|---|---|---|---|---|
| 1 | 89.0 | 41.2 | 41.2 | 38.6 | 3.8 | 1.05 |
| 30 | 135.4 | 51.7 | 51.7 | 40.3 | 1.8 | 1.17 |
| 60 | 155.2 | 50.8 | 50.8 | 38.3 | 0.6 | 1.13 |
| 90 | 165.0 | 52.1 | 52.1 | 38.6 | 0.6 | 1.11 |

#### Obchod s goods podle dvojic

| tah | NPC s NPC | hráč s NPC | A s B |
|---|---|---|---|
| 6 | 0.00 | 5.09 | 0.00 |
| 30 | 0.39 | 1.68 | 0.00 |
| 60 | 0.23 | 0.45 | 0.00 |
| 90 | 0.23 | 0.43 | 0.00 |

#### Světová výroba zdrojů a `invest_prod`

| tah | ropa | obilí | kovy | orit |
|---|---|---|---|---|
| 1 | 50.0 | 65.6 | 49.2 | 0.0 |
| 30 | 59.3 | 146.7 | 51.6 | 98.4 |
| 60 | 56.9 | 123.5 | 50.1 | 192.2 |
| 90 | 57.0 | 123.7 | 50.4 | 272.8 |

Za celý běh **6** investic `invest_prod` (NPC: grain 4, NPC: oil 2).

#### Světová bilance ropy a obilí

| tah | ropa výroba | ropa domácnosti | ropa průmysl | ropa pokuty | obilí výroba | obilí domácnosti | obilí pokuty |
|---|---|---|---|---|---|---|---|
| 1 | 50.0 | 12.3 | 20.6 | 0.00 | 65.6 | 61.6 | 0.00 |
| 30 | 59.3 | 11.4 | 25.8 | 0.00 | 146.7 | 56.8 | 0.00 |
| 60 | 56.9 | 10.3 | 25.4 | 0.00 | 123.5 | 51.3 | 0.00 |
| 90 | 57.0 | 10.3 | 26.1 | 0.00 | 123.7 | 51.3 | 0.00 |

#### Obchod

| tah | NPC s NPC | hráči (cílené i automatický obchod) | z toho goods (všichni) | A s B |
|---|---|---|---|---|
| 6 | 32.31 | 125.86 | 5.09 | 3.63 |
| 30 | 6.36 | 10.11 | 2.07 | 3.30 |
| 60 | 4.33 | 13.90 | 0.68 | 2.89 |
| 90 | 4.38 | 14.04 | 0.67 | 2.89 |

Obchod A s B za celý běh proběhl v 90 tazích v objemu 293.23.

#### Obchody podle počtu přejezdů

| tah | 0 přejezdů | 1 přejezd | 2 přejezdy | 3 přejezdy |
|---|---|---|---|---|
| 6 | 38 | 5 | 3 | 0 |
| 30 | 24 | 2 | 2 | 0 |

#### Tranzitní příjem podle státu

| stát | tahy 1 až 30 | tahy 1 až 90 |
|---|---|---|
| N6 | 9.55 | 15.66 |
| N7 | 6.34 | 6.56 |
| N1 | 4.25 | 5.68 |
| N2 | 0.56 | 0.64 |
| N4 | 0.21 | 0.21 |

#### Rozhodování NPC podle 3.4

| akce | přijato | s podmínkou | protinávrh | odmítnuto |
|---|---|---|---|---|
| `trade_offer` | 0 | 0 | 2 | 0 |
| `loan` | 20 | 11 | 3 | 18 |
| `protect` | 0 | 0 | 0 | 1 |

#### Nabídky NPC podle 3.5

| hráč | typ | vygenerováno | přijato skriptem |
|---|---|---|---|
| A | `loan_request` | 83 | 1 |
| A | `sell` | 97 | 96 |
| B | `loan_request` | 83 | 0 |
| B | `sell` | 97 | 96 |
| C | `loan_request` | 104 | 0 |

#### Zásoby světa (součet 18 států)

| tah | grain | oil | metal | goods | orit |
|---|---|---|---|---|---|
| 1 | 401.4 | 164.5 | 128.8 | 259.3 | 0.0 |
| 30 | 349.8 | 213.0 | 178.9 | 379.6 | 196.9 |
| 60 | 364.6 | 229.4 | 195.7 | 393.0 | 216.3 |
| 90 | 365.4 | 226.9 | 197.7 | 397.5 | 220.0 |

#### Převraty, padlé říše a hráči

Převratů celkem za 90 tahů: **33**. Bohatství:

| tah | N11 Aurelie | N12 Ysmar | A | B |
|---|---|---|---|---|
| 30 | 139.5 | 117.5 | 231.9 | 156.7 |
| 60 | 148.4 | 146.9 | 396.6 | 308.7 |
| 90 | 156.1 | 177.5 | 539.8 | 464.4 |

#### Průmysl

| tah | A industry / goods_out | B industry / goods_out | N1 industry / goods_out | N6 industry / goods_out | N11 industry / goods_out |
|---|---|---|---|---|---|
| 1 | 8.1 / 7.41 | 6.0 / 5.74 | 2.0 / 2.60 | 1.0 / 0.61 | 7.1 / 2.51 |
| 30 | 10.0 / 13.00 | 6.0 / 8.21 | 4.6 / 4.14 | 0.5 / 0.48 | 10.0 / 3.64 |
| 60 | 10.0 / 11.69 | 6.0 / 8.40 | 8.4 / 4.78 | 0.5 / 0.40 | 10.0 / 3.73 |
| 90 | 10.0 / 11.68 | 6.0 / 8.40 | 10.0 / 4.93 | 0.5 / 0.39 | 10.0 / 3.80 |

---

## S. Nově otevřené otázky z implementace v1.8

**Uzavřeno rozhodnutím ze 14. 9. 2026 (v1.9):** S1 až S7 potvrzeny podle enginu a zapsány do `docs/pravidla.md`;
S8 a S9 řeší cíl automatické `invest_prod` podle ceny (4.2a), S10 spekulativní nabídka na trhu (4.0, 4.1a). Jak změny
dopadly, ukazuje oddíl T; co zůstává otevřené, je v U.

### S9. `invest_prod` do největší produkce vytváří přebytek

NPC investuje do zdroje, kde má největší produkci, tedy obilnice do obilí. Obilí se tím hromadí a jeho cena padá
na dolní mez (ve (0) výroba z 65.6 na 156.8, cena 0.56). **Otázka:** investovat
spíš do zdroje s nejvyšší cenou nebo s největším deficitem státu?

### S10. Komparativní výhoda obchod s `goods` zatím nerozhýbala

Malé továrny kryjí jen polovinu potřeby a velké nabízejí 10 % kapacity navíc, obchod s `goods` přesto zůstává
v jednotkách za tah a přebytek velkých továren končí v zásobách. **Otázka:** má spekulativní nabídka mířit na trh
i tehdy, když zásoba `goods` už přesahuje rezervu, a mají malé továrny svůj deficit aktivně nakupovat?

### S8. Ropa dál na dolní mezi

Snížení ropy N3 a B cenu nezvedlo, ropa je na 0.70 od tahu 2 a automatika `invest_prod` její výrobu dál zvyšuje.
**Otázka:** ubrat ropu víc, nebo zakázat automatickou investici do zdroje, jehož cena je na dolní mezi?

### S1. Strop malých továren

**Výklad enginu:** strop 50 % vlastní potřeby platí pro celý plán, tedy i pro prodej minulého tahu a doplnění rezervy.

### S2. Plán velkých továren

**Výklad enginu:** doplnění rezervy `goods` zůstává a 10 % kapacity se přičte navíc.

### S3. Základ a zaúčtování cla

**Výklad enginu:** clo je 10 % z hodnoty obchodu bez tranzitní přirážky (u automatického trhu ze základní ceny, u cíleného
obchodu z dohodnuté ceny). Platí-li ho kupec, zaplatí cenu i clo; platí-li ho prodejce, dostane cenu bez cla. Do objemu
obchodu pro metriku A se clo nepočítá.

### S4. Kdo je pro clo člen

**Výklad enginu:** členem jsou jen `members`, kandidát je nečlen. Clo se proto vybírá až od tahu po vzniku Unie.

### S5. Cíl `invest_prod`

Rozhodnutí neurčuje cíl. **Výklad enginu:** stejně jako `invest_industry` (G4), tedy vlastní stát nebo NPC ve vlastní sféře,
Unie členy a kandidáty. Podmínka `tech ≥ 3` se bere u cíle.

### S6. Pořadí investic NPC

**Výklad enginu:** investice se střídají podle čísla tahu pro všechna NPC najednou v cyklu devíti tahů: tahy 3, 12, 21 a dál
`invest_tech`, tahy 6, 15, 24 a dál `invest_industry`, tahy 9, 18, 27 a dál `invest_prod`. Při shodě největší produkce rozhoduje
pořadí oil, grain, metal. NPC s `tech < 3` v tahu `invest_prod` neinvestuje vůbec.

### S7. Výchozí zásoby a komparativní výhoda

**Výklad:** plán výroby bez obchodu pro výchozí zásoby (Q5) jsem upravil i o komparativní výhodu: `industry < 2` nejvýš
50 % vlastní potřeby, `industry ≥ 4` vlastní potřeba plus 10 % kapacity. Změnily se zásoby ropy a kovů N11 a N12.

---

## T. Test pravidel v1.9: scénáře (0) a (b), 90 tahů

Oba scénáře běží na enginu v1.9. Řádek o podílu hráčů porovnává párování v1.8 (bez paušálu, stará kritéria) a v1.9 na stejném
skriptu; ostatní změny v1.9 jsou v obou bězích zapnuté. Objem je to, co zaplatil kupec, součet za 90 tahů. Obchod členů Unie mezi sebou
je vnitřní trh v tržní ceně (zdarma, hodnota jen pro srovnání), s nečleny automatický a cílený obchod, kde je stranou právě jeden člen.

### Souhrn

| ukazatel | (0) nikdo netahne | (b) realistické půjčování |
|---|---|---|
| kritéria scénáře | prošla | prošla |
| crash | tah 69, den 23 | tah 33, den 11 |
| vznik Unie | tah 69: N13, N1, N8, N2 | tah 33: N13, N8, N2, N7 |
| index tah 30 / 60 / 90 | 93.11 / 99.83 / 109.10 | 95.90 / 85.63 / 97.77 |
| W_real tah 90 | 1817.5 | 1366.1 |
| nejvíc NPC v bídě naráz | 3 (tah 70) | 4 (tah 34) |
| převratů | 18 | 18 |
| ceny tah 90 | oil 0.70, grain 0.56, metal 0.84, goods 1.18 | oil 0.71, grain 0.56, metal 0.84, goods 1.12 |
| investic do zdrojů za běh | 10 | 9 |
| objem obchodu `goods` za běh | 210.3 | 260.4 |
| validate | 0 chyb | 0 chyb |
| podíl hráčů na objemu automatického trhu, před a po změně 3 | 56.5 % před (objem 2430), 32.7 % po (objem 2564) | 64.5 % před (objem 2500), 41.2 % po (objem 2689) |
| obchod členů Unie mezi sebou vs. s nečleny | mezi sebou 386.4, s nečleny 145.6 | mezi sebou 398.2, s nečleny 56.8 |

### Bilance goods, ropy a obilí (svět, v tahu)

| scénář | tah | goods kapacita / plán / výroba / spotřeba / prodáno / cena | ropa výroba / domácnosti / průmysl / pokuty / cena | obilí výroba / domácnosti / pokuty / cena |
|---|---|---|---|---|
| (0) | 1 | 89.0 / 41.2 / 41.2 / 38.6 / 3.8 / 1.05 | 50.0 / 12.3 / 20.6 / 0.0 / 1.14 | 65.6 / 61.6 / 0.0 / 0.75 |
| (0) | 30 | 146.7 / 55.5 / 55.5 / 44.0 / 2.1 / 1.19 | 59.2 / 11.8 / 27.8 / 0.0 / 0.70 | 79.9 / 59.0 / 0.0 / 0.59 |
| (0) | 60 | 168.0 / 59.3 / 59.3 / 46.3 / 1.6 / 1.17 | 61.4 / 11.3 / 29.6 / 0.0 / 0.70 | 83.1 / 56.5 / 0.0 / 0.56 |
| (0) | 90 | 166.8 / 60.4 / 60.4 / 47.6 / 1.0 / 1.18 | 61.8 / 11.2 / 30.2 / 0.0 / 0.70 | 83.3 / 56.0 / 0.0 / 0.56 |
| (b) | 1 | 89.0 / 41.2 / 41.2 / 38.6 / 3.8 / 1.05 | 50.0 / 12.3 / 20.6 / 0.0 / 1.14 | 65.6 / 61.6 / 0.0 / 0.75 |
| (b) | 30 | 149.0 / 52.8 / 52.8 / 39.5 / 2.8 / 1.13 | 58.1 / 12.2 / 26.4 / 0.0 / 0.70 | 81.9 / 61.1 / 0.0 / 0.60 |
| (b) | 60 | 163.1 / 54.6 / 54.6 / 40.8 / 1.4 / 1.12 | 56.9 / 11.3 / 27.3 / 0.0 / 0.70 | 84.9 / 56.4 / 0.0 / 0.56 |
| (b) | 90 | 173.8 / 58.3 / 58.3 / 43.5 / 1.5 / 1.12 | 57.0 / 11.3 / 29.2 / 0.0 / 0.71 | 85.1 / 56.4 / 0.0 / 0.56 |

---

## U. Nově otevřené otázky z implementace v1.9

Neopravuji je, engine u každé používá uvedený výklad. Nejdůležitější jsou U1 a U2, protože ukazují, že ceny ropy a obilí
zůstávají na dolní mezi i po změnách 1 a 2 a obchod s `goods` zůstává malý.

### U1. Ropa a obilí dál na dolní mezi

Automatika do nich už neinvestuje (do zdroje na dolní mezi nesmí), ceny se ale nezvedly: ropa 0.70 až 0.71 a obilí 0.56 v tahu 90
v obou scénářích. Výroba převyšuje potřebu už v tahu 1 (ropa 50.0 proti 32.9, obilí 65.6 proti 61.6) a v tahu 90 dál (ropa 61.8
proti 41.4, obilí 83.3 proti 56.0 v (0)). **Otázka:** snížit výchozí produkci ropy a obilí, nebo zvednout potřebu?

### U2. Spekulativní nabídka `goods` obchod nerozhýbala

Prodáno je 1 až 4 `goods` za tah a objem obchodu `goods` za 90 tahů je 210 v (0) a 260 v (b). Výroba světa převyšuje spotřebu
(tah 90: 60.4 proti 47.6 v (0), 58.3 proti 43.5 v (b)), trh ale přebytek neodebírá. Proč kupci nekupují víc, jsem podrobně
nerozebral. **Otázka:** mám rozebrat poptávku po `goods` podle států, než se rozhodne o další úpravě?

### U3. Pool Unie

**Výklad enginu:** přebytek člena je zásoba plus bilance toku minus rezerva 3 tahů spotřeby (stejně jako nabídka v 4.1a), deficit
člena je deficit toku tohoto tahu, bez doplnění rezervy. Při podání akce se bere poslední známá potřeba, při provedení potřeba
z plánované výroby a dosavadní dovozy a vývozy.

### U4. Peníze obchodu Unie

Rozhodnutí říká "peníze jdou přes fond". **Výklad enginu:** příjem z prodeje zůstává ve fondu a nákup platí fond; členové
předávají a dostávají zboží bez placení, jako na vnitřním trhu. Clo odvádí nečlen do fondu. Druhá možnost je, že fond příjem
rozdělí členům poměrně k prodanému množství a nákup jim naúčtuje.

### U5. Protistrana obchodu Unie

**Výklad enginu:** cíl musí mít opačnou bilanci než pool (když Unie prodává, cíl musí mít deficit), množství se ořízne na pool i
na bilanci cíle. NPC nabídku vyhodnotí podle 3.4 bez členu vlivu, u padlé říše platí dolní mez 1.3 × tržní ceny (7a). Obchod
s hráčem projde bez hodu jako obchod mezi hráči.

### U6. Spekulativní nabídka a zásoba

**Výklad enginu:** spekulativní nabídka je nejvýš 10 % kapacity a zároveň nejvýš letošní výroba `goods`; na trh smí jít, i když tím
zásoba klesne pod rezervu, ne však pod nulu. Malé továrny nakupovaly deficit `goods` včetně doplnění rezervy už ve v1.8 (od
`wealth ≥ 25`), druhá věta změny 2 proto engine neměnila, jen je zapsána do pravidel.

### U7. Paušál a pořadí párování

**Výklad enginu:** paušál 1 přejezd má každá dvojice s hráčem A nebo B, i obchod A s B (ne 1 za každého hráče). Počet přejezdů
mezi kritéria při shodě ceny už nepatří, rozhodnutí ho nevyjmenovává; cena se pro shodu porovnává na 9 desetinných míst.
Podíl hráčů na automatickém trhu po změně 3 je 32.7 % v (0) a 41.2 % v (b), paušál proto zůstává 1.

### U8. Clo v pohledech a dvojí `set_tariff`

**Výklad enginu:** platná sazba je veřejná, hráči A a B ji vidí jako `clo_unie`, Unie navíc sazbu ohlášenou na další tah. Pošle-li
Unie v jednom tahu `set_tariff` dvakrát, platí poslední platná.

### U9. Chyba migrace (opraveno v enginu)

Migrace strhávala dárci `prod.grain` −0.5 jen do nuly, ale migrace zpět vracela vždy 0.5. Dárci bez obilí tak obilí dostávali:
ve (b) N7 z 0 na 36, N15 z 0 na 22.5, světová výroba obilí 190.7 místo 85.1 v tahu 90. Opraveno podle pravidla 5 (srážka je
dočasná): záznam migrace nese skutečnou srážku a vrací se jen ta. Týká se i výsledků oddílů R a dříve.

### U10. Syntetický stav Unie má 4 členy

Bod 9 zadání počítá se 3 členy. Ve scénáři (b) vzniká Unie v tahu 33 se čtyřmi zakladateli (N13, N8, N2, N7) a třemi kandidáty.
`debug/state_post_crisis.json` je proto skutečný stav po tahu 33, se 4 členy; ruční úpravou členství by vznikl stav, který engine
nevytváří.

### U11. Ostré volání Unie neproběhlo

Na tomto počítači chybí balíček `anthropic` a přihlášení k API (`ANTHROPIC_API_KEY` ani `ant auth login`). `run_turn.py --only C
--state debug/state_post_crisis.json --no-apply` skončil před voláním modelu, `debug/unie_C_response.json` proto neexistuje.
Instalaci balíčku a klíč musí dodat Adam.

### U12. E-mail při selhání tahu

BUILD.md část 3 chce e-mail Adamovi přes Gmail konektor. Skript konektor volat nemůže; `run_turn.py` zapíše
`history/failed_turn_NNN.json` a důvod vytiskne, e-mail musí poslat routine. Routiny zatím nevznikly.

# Žánry vystoupení hráčů (v1.13)

Každé kolo engine (`run_turn.py`) vylosuje každému hráči formu veřejného vystoupení (`public_statement`) a hráč ji
musí dodržet. Strojová podoba je tabulka `GENRES` v `run_turn.py`. Platí pro Kalveru (A), Ostrogard (B) i Unii (C).

## Katalog

| č. | klíč | forma a délka | A | B | C | váha A/B | váha C | limit |
|---|---|---|---|---|---|---|---|---|
| 1 | komunike | úřední sdělení, 2 až 3 věty; A a B ve třetí osobě bez oslovení soupeře; C v množném čísle členských vlád („Členové Unie berou na vědomí...“), nikdy nejmenuje jednotlivého člena | Prohlášení federálního kabinetu | Sdělení tiskové agentury republiky | Společné prohlášení členských vlád | 30 | 35 (výchozí) | |
| 2 | otazka | odpověď na jednu otázku zahraničního novináře, 2 až 4 věty, smí uhnout; otázku vytvoří rozhodčí, u Unie smí mířit i na rozpory mezi členy | Odpověď zahraničnímu novináři | stejně | stejně | 25 | 25 | |
| 3 | tiskovka | dvě otázky, jedna k soupeři a jedna ke světu, 4 až 6 vět, odpovědět na obě | Tisková konference | stejně | stejně | 10 | 10 | nejvýš 1 za den |
| 4 | projev_domu | A a B: projev k vlastním lidem, soupeř jen nepřímo; C: projev předsedajícího k členským vládám, ne k lidu; 4 až 6 vět | Projev v Radě federace | Projev na sjezdu | Projev předsedajícího na sněmu Unie | 10 | 8 | A a B nejvýš 1 za den |
| 5 | dopis | zveřejněný dopis jedné vládě, 3 až 4 věty, jmenuje jen adresáta; u Unie jen přípustný adresát ze seznamu enginu (kandidát nebo nečlen sousedící s členem) | Otevřený dopis vládě | Otevřený dopis vládě | Dopis kandidátské zemi | 15 | 15 | |
| 5v | dopis, státní varianta (s pravděpodobností 1/3 místo dopisu) | A: suchá zpráva, hrubé poměry, tón bankéře; B: nepodepsaný úvodník, nikdy nepřizná neúspěch; C: suché číslované usnesení („Usnesení č. N“, „Rada rozhodla poměrem hlasů“, bez uvedení, kdo byl proti); 3 až 4 věty | Výroční zpráva obchodní komory | Úvodník stranického deníku | Usnesení rady č. N | | | |
| 6 | ticho | hráč projev nepíše, `public_statement` je prázdný řetězec; engine zapíše „Vláda dnes nevystoupila.“ (A, B) nebo „Unie dnes nevydala prohlášení.“ (C) | Ticho | Ticho | Ticho | 5 | 5 | A a B nikdy v 1. kole dne; C nikdy v zakládajícím kole (volba jména) |
| 7 | unik | rozhodčí zveřejní ve Zprávách světa jednu větu ze soukromé zprávy hráče z minulého kola jako uniklou depeši; hráč dostane formu žánru 2 s otázkou na únik | Odpověď na otázku k uniklé depeši | stejně | stejně | 5 | 5 | od kola 22 (2. týden) a jen když hráč minulé kolo zprávu poslal; C navíc nejdřív ve 3. kole po založení |
| 8 | stanovisko | 2 až 3 věty k jedné události, kterou musí pojmenovat; nelosuje se, přebíjí los | Stanovisko k události | stejně | stejně | 0 | 0 | jen při spouštěči |

## Los

- Vážený náhodný výběr z `random.Random(rng_seed + kolo + CRC32(ID hráče))`, deterministický jako hod NPC (3.4).
- Stejný žánr dvakrát po sobě u téhož hráče je zakázán. Limity „nejvýš 1 za den“ hlídá `state["genre"][hráč]`
  (`day`, `day_counts`); Unie tam má i pořadové číslo usnesení (`resolution_no`).
- Varianta dopisu (1/3) se losuje ze stejného generátoru. Nemá-li Unie přípustného adresáta, dostane usnesení.
- Předsedajícího Unie (žánr 4) losuje engine ze současných členů z `random.Random(rng_seed + kolo)`.
- Vylosovaný žánr jde do `state["genre"]` a do snímku `history/turn_NNN.json` jako `turns[hráč]["genre"]`
  (číslo, název, otázky, událost, předsedající, adresáti, únik).

## Spouštěče stanoviska (žánr 8)

Engine hledá v událostech minulého kola (`history/turn_NNN.json`, pole `events`) tyto existující druhy událostí.
První nalezená přebije los pro A, B i C.

| událost | event kind | podmínka |
|---|---|---|
| puč | `coup` | |
| první nesplácení | `default` | první záznam dvojice dlužník a věřitel v `minsky.defaults` |
| invaze | `invade_progress`, `occupied` | u `invade_progress` jen zahájení (`turns` = 1) |
| vyhlášení války | `war_declared` | |
| příměří | `war_end` | `how` = `primeri` |
| vznik Unie | `union_founded` | |
| změna Minskyho fáze | `phase` | ve stanovisku jako „obrat hospodářské nálady ve světě“ |
| sucho s dopadem | není | engine žádnou událost sucha nemá; spouštěč se nepoužije, dokud ji engine nezavede |

Unie má navíc tři vlastní spouštěče (jen pro C):

| událost | event kind | podmínka |
|---|---|---|
| člen Unie v bídě | `poverty` | `stat` je člen |
| člen přijal půjčku velmoci | `loan_given` | `target` je člen, `player` je A nebo B |
| kandidát přijal ochranu velmoci | `protect_started` | `target` je kandidát, `player` je A nebo B |

## Otázky novinářů

Pro žánry 2, 3 a 7 zavolá `run_turn.py` před koly hráčů malou úlohu rozhodčího (strukturovaný výstup
`{"questions": [...]}`, u žánru 7 navíc `leak`). Podklad: Zprávy světa a projev soupeře z minulého kola (u Unie
projevy obou velmocí), u žánru 7 soukromá zpráva hráče. Otázky nesmějí obsahovat skrytá data (právo, technologie,
index, cizí vliv). Vrátí-li rozhodčí méně otázek, doplní engine obecnou otázku „Jak hodnotíte současné dění ve
světě?“. Uniklá věta musí být doslova ze zprávy, jinak engine vezme její první větu.

## Pravidla vystoupení (všechny žánry)

- Jedno téma; nejvýš dva jmenované státy.
- Žádné ceny, množství a procenta, jen hrubé poměry slovy („třetina“, „většina“).
- Zakázaná slova: pakt, vliv, kontrakt, jednotka, slot, tah, nabídka číslo, offer, deal; místo nich smlouva,
  spojenectví, dodávky, přátelé.
- O vlastních krocích tohoto kola se nemluví výčtem.
- Unie navíc (měkká instrukce, bez kontroly): v projevu nikdy nepíše, který člen jak hlasoval ani kdo byl proti.

## Tvrdá kontrola

Po odpovědi hráče `statement_violations()` v `run_turn.py` odmítne projev, který obsahuje:

- číslo s desetinnou čárkou nebo tečkou (`\d+[.,]\d+`) nebo znak `%`;
- zakázané slovo bez ohledu na velikost písmen: pakt (pakt, paktu, pakty, paktem, paktů, paktech, paktům),
  vliv (vliv, vlivu, vlivem, vlivy), kontrakt*, jednotk*, slot*, tah (tah, tahu, tahy, tahem, tazích, tahů,
  tahům), „nabídka číslo“ (nabídk* číslo, nabídk* č.), offer*, deal*;
- počet vět mimo rozsah žánru ±1 (věta končí `.`, `!`, `?` nebo `…` před mezerou nebo koncem textu);
- u žánru 6 jakýkoli neprázdný text.

Porušení znamená neplatnou odpověď: důvod jde do `debug/turn_NNN_X_fail_K.txt` a jako poslední odstavec
(jen výčet porušení) do dalšího pokusu. Po vyčerpání pokusů hráč mlčí (10.6).

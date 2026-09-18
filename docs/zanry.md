# Žánry vystoupení hráčů (v1.13, úpravy v1.14)

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
| 6 | ticho | od v1.14 se nelosuje (váha 0): mlčení je volba hráče, viz níže; pevná věta „Vláda dnes nevystoupila.“ (A, B) nebo „Unie dnes nevydala prohlášení.“ (C) | Ticho | Ticho | Ticho | 0 | 0 | |
| 7 | unik | rozhodčí zveřejní ve Zprávách světa jednu větu ze soukromé zprávy hráče z minulého kola jako uniklou depeši; hráč dostane formu žánru 2 s otázkou na únik | Odpověď na otázku k uniklé depeši | stejně | stejně | 5 | 5 | od kola 22 (2. týden) a jen když hráč minulé kolo zprávu poslal; C navíc nejdřív ve 3. kole po založení |
| 8 | stanovisko | 2 až 3 věty k jedné události, kterou musí pojmenovat; nelosuje se, přebíjí los | Stanovisko k události | stejně | stejně | 0 | 0 | jen při spouštěči |

## Podíly po vyřazení ticha (v1.14)

Váhy ostatních žánrů zůstaly, los je poměrný, takže se po vyřazení ticha přepočítaly samy:

| č. | žánr | podíl A a B | podíl C |
|---|---|---|---|
| 1 | komunike | 31,6 % (30 z 95) | 35,7 % (35 z 98) |
| 2 | otazka | 26,3 % (25 z 95) | 25,5 % (25 z 98) |
| 3 | tiskovka | 10,5 % (10 z 95) | 10,2 % (10 z 98) |
| 4 | projev_domu | 10,5 % (10 z 95) | 8,2 % (8 z 98) |
| 5 | dopis | 15,8 % (15 z 95) | 15,3 % (15 z 98) |
| 7 | unik | 5,3 % (5 z 95), jen když je aktivní | 5,1 % (5 z 98), jen když je aktivní |

Když není únik aktivní, dělí se o jeho podíl ostatní žánry ve stejném poměru.

## Mlčení (v1.14)

Hráč smí v kterémkoli žánru mlčet: vrátí prázdný `public_statement`. Odpověď je platná, tvrdá kontrola se na prázdný
projev nepoužije a engine zapíše pevnou větu žánru ticho. Snímek tahu to označí `turns[hráč]["mlci"] = true` a web
u věty uvede, že se vláda rozhodla mlčet. Pokyn v promptu: mluvit jen tehdy, když má hráč závazek, podmínku, hrozbu,
nabídku nebo ujištění, které mění, co ostatní čekají od dalšího kola.

## Zimní kolo (v1.14)

Ve slotu 3 (zima) je délka vylosovaného žánru o dvě věty delší (například komunike 4 až 5 vět) a rozsah tvrdé
kontroly ±1 se posouvá s ní. Prompt dostane větu: „Je konec roku. Vystoupení hodnotí celý rok: co se změnilo a co
z toho pro příští rok plyne.“

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

## Obsah vět (v1.14, všechny žánry)

- Každé vystoupení nese závazek, po kterém někdo čeká něco jiného než před ním: slib, podmínka, hrozba, nabídka,
  ujištění. Ne stejný tvar dvakrát po sobě; hrozba nejvýš jednou za rok.
- Adresát se střídá: soupeř, jmenovaný stát, vlastní lidé, situace (ceny, trh, krize, orit, instituce). Soupeře
  adresuj nejvýš v každém čtvrtém vystoupení.
- Každá věta nese nový fakt, důsledek nebo podmínku. Věta, která říká zřejmé („prodáme tam, kde je poptávka“) nebo
  mlží („za cenu, kterou si můžeme dovolit“), se škrtá. Test: šla by věta přečíst kterýmkoli státem v kterýkoli rok?
  Pak je prázdná.
- Celé věty jako tiskový mluvčí: spojky, vedlejší věty, normální slovosled, žádná hesla bez slovesa. První věta říká,
  co děláš nebo co chceš, ne co se stalo; událost a Zprávy světa publikum zná.
- Čísla nahrazují jména a lhůty slovy v herním čase.
- Zakázané tvary: přísloví, aforismy, protiklady typu „X je krátké, Y je dlouhé“, řečnické otázky, věty začínající
  „Pojmenuji“, „Svět mluví“, „Dnešní událost“.
- Před projevem si hráč v úvaze jednou větou řekne, co slibuje, komu a co zamlčuje.

Tato pravidla jsou pokyn v promptu (`CONTENT_RULES` v `run_turn.py`), tvrdá kontrola je nehlídá.

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
- prázdný projev (mlčení) je od v1.14 platný vždy a kontrolou neprochází.

Porušení znamená neplatnou odpověď: důvod jde do `debug/turn_NNN_X_fail_K.txt` a jako poslední odstavec
(jen výčet porušení) do dalšího pokusu. Po vyčerpání pokusů hráč mlčí (10.6).

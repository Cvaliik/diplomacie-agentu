# Formát tahu

Tento soubor dostává každý hráč v každém tahu. Odpověď musí být **jediný validní JSON objekt**,
bez komentáře před ním i za ním. Vychází z `docs/pravidla.md` částí 3.1 a 3.2.

## Struktura

```json
{
  "public_statement": "Diplomatický projev pro celý svět, 2 až 5 vět.",
  "private_reasoning": "Skutečné uvažování, včetně toho, kde v projevu nemluvíš pravdu.",
  "actions": [
    { "type": "...", "...": "..." }
  ]
}
```

| pole | typ | povinné | poznámka |
|---|---|---|---|
| `public_statement` | text | ano | 2 až 5 vět, vidí ho všichni |
| `private_reasoning` | text | ano | vidí ho publikum, soupeř ne |
| `actions` | seznam | ano | nejvýš 2 akce (Unie 3); prázdný seznam `[]` je platný tah |

Neplatnou akci rozhodčí vyřadí a zapíše důvod. Zbytek tahu platí.
Pokud odpověď není validní JSON ani po dvou opakováních, hráč v tahu mlčí (pravidla 10.6).

Identifikátory států: hráči `A`, `B`, `C` (Unie), NPC `N1` až `N16`.
Statky: `grain`, `oil`, `metal`, `goods`, od displacementu i `orit`.

## Akce

### `trade_offer`: nabídka trvalého obchodu NPC

Směr určuje NPC: má-li statku přebytek, prodává ti, má-li deficit, kupuje od tebe.
Cena musí být v pásmu 0.7 až 1.5 aktuální tržní ceny. Množství se ořízne na velikost bilance NPC.
Cílem může být i druhý hráč (`A` nebo `B`); směr pak určuje jeho bilance.
Obchod s členem Unie nese clo, které platí strana mimo Unii. Platnou sazbu vidíš v pohledu jako `clo_unie`
(výchozí 0.10).

NPC nabídku vyhodnotí podle své vůle. Může ji přijmout, přijmout s podmínkou (menší objem),
poslat protinávrh soukromou zprávou, nebo odmítnout. Výsledek s důvodem najdeš ve svém
`soukromy_log`. Protinávrh přijmeš tak, že v dalších 3 tazích pošleš `trade_offer`
s jeho přesnými parametry; ten projde bez dalšího vyjednávání.

```json
{ "type": "trade_offer", "target": "N1", "res": "grain", "qty": 3, "price_per_unit": 0.8 }
```

### `loan`: půjčka NPC

Převedeš `amount` svého bohatství, NPC ti dluží `amount × 1.2` a splácí 10 % dluhu za tah.
Unii (`C`) půjčit nelze, padlé říše půjčky nepřijímají. NPC půjčku vyhodnotí podle své vůle
a může ji přijmout i v menší výši.

```json
{ "type": "loan", "target": "N6", "amount": 10 }
```

### `pressure`: sankce

Přeruší tvé obchody s NPC. NPC ztrácí 3 bohatství za tah, ty 1.
Cílem může být i druhý hráč: sankce pak po dobu trvání přeruší váš vzájemný automatický
obchod a stojí oba 1 bohatství za tah.

```json
{ "type": "pressure", "target": "N3", "demand": "Zrušte obchod s Ostrogardem." }
```
```json
{ "type": "pressure", "target": "B", "demand": "Stáhněte posádky z Kessaru." }
```

### `protect`: vojenský pakt

NPC nelze napadnout, dokud pakt trvá. Stojí 2 síly za tah. Padlé říše pakt nepřijímají.
NPC pakt vyhodnotí podle své vůle. Pakt zaniká, když ti síla klesne na 0.
Jedno NPC má nejvýš jeden pakt; na NPC pod paktem druhého hráče akce neprojde.

```json
{ "type": "protect", "target": "N7" }
```

### `invade`: invaze

Vyžaduje aspoň dvojnásobek síly cíle (u padlé říše čtyřnásobek) a 6 po sobě jdoucích tahů
s touto akcí (u padlé říše 10). Přerušení znamená začít znovu. Stojí 10 bohatství a 5 síly za tah.

Cílem je jen NPC; druhého hráče dobýt nelze. Útok na NPC pod paktem druhého hráče vyhlásí válku.

```json
{ "type": "invade", "target": "N8" }
```

### `declare_war`: vyhlášení války druhému hráči

Cílem je `A` nebo `B`. Každý tah války stojí obě strany 10 síly a 5 % bohatství, přeruší váš vzájemný
automatický obchod a oslabí obchod se státy ve sféře druhého. Válka končí ústupem (`cancel` s `deal_id`
války ze seznamu `valky`, stojí 30 % vlivu u všech států) nebo vyčerpáním síly (kapitulace). V tazích
1 až 9 a 88 až 90 válku vyhlásit nelze. Pošlete-li `cancel` na válku oba ve stejném tahu nebo v tazích po sobě,
je to příměří za 10 % vlivu každému. Kdo válku vyhlásí, ztrácí vliv u nezávislých států dvakrát rychleji.

```json
{ "type": "declare_war", "target": "B" }
```

### `invest_tech`: investice do technologie

Vlastní stát, nebo NPC ve tvé sféře. Stojí 8 bohatství. Unie platí na členy a kandidáty polovinu.

```json
{ "type": "invest_tech" }
```
```json
{ "type": "invest_tech", "target": "N5" }
```

### `invest_law`: investice do institucí

Vlastní stát, nebo NPC ve tvé sféře. Stojí 6 bohatství. Unie platí na členy a kandidáty polovinu.

```json
{ "type": "invest_law", "target": "N2" }
```

### `invest_industry`: investice do průmyslu

Zvýší míru industrializace cíle. Vlastní stát, nebo NPC ve tvé sféře; cíl musí mít dost pevné
instituce, jinak investice neprojde. Stojí 10 bohatství. Unie platí na členy a kandidáty polovinu.
Továrny potřebují ropu a kovy, bez nich stojí i po investici.

```json
{ "type": "invest_industry" }
```
```json
{ "type": "invest_industry", "target": "N4" }
```

### `invest_prod`: investice do těžby a zemědělství

Zvýší produkci jednoho zdroje (`oil`, `grain` nebo `metal`) o 1. Vlastní stát, nebo NPC ve tvé sféře.
Jen pro zdroj, který cíl už produkuje, a jen když má cíl dost vyspělou technologii, jinak investice
neprojde. Orit se takto zvýšit nedá. Stojí 12 bohatství. Unie platí na členy a kandidáty polovinu.

```json
{ "type": "invest_prod", "res": "grain" }
```
```json
{ "type": "invest_prod", "res": "oil", "target": "N14" }
```

### `explore`: průzkum ložisek

Jen vlastní stát. Stojí 5 bohatství, s šancí 15 % najde malé ložisko oritu.

```json
{ "type": "explore" }
```

### `arm`: zbrojení

Jen vlastní stát. Utratíš `amount` bohatství (nejvýš 40) a síla vzroste o `amount / 1.6`.

```json
{ "type": "arm", "amount": 16 }
```

### `cancel`: zrušení obchodu, paktu, sankce nebo invaze

`deal_id` najdeš ve svém pohledu v seznamu `deals`. U invaze přidej `target`. Válku ukončíš ústupem:
`cancel` s `deal_id` války ze seznamu `valky`.

```json
{ "type": "cancel", "deal_id": "d7" }
```
```json
{ "type": "cancel", "deal_id": "i2", "target": "N8" }
```

### `message`: soukromá zpráva jinému hráči

Doručena v příštím tahu. Adresát je `A`, `B` nebo `C`. Publikum ji vidí.

```json
{ "type": "message", "target": "B", "text": "Navrhuji rozdělit obchod s Kessarem." }
```

### `admit`: nabídka členství (jen Unie)

Jen nezávislému NPC, které sousedí s některým členem. NPC nabídku vyhodnotí podle své vůle.
Lze i u státu, kde má velmoc silný vliv, ale ještě ho nemá ve sféře; takový stát musí mít pevnější instituce.

```json
{ "type": "admit", "target": "N10" }
```

### `trade_offer` Unie: obchod za členy (jen Unie)

Unie obchoduje s NPC, které není členem, nebo s hráčem `A` či `B`. Prodává z přebytků členů a nakupuje
pro jejich deficity; směr určí souhrnná bilance členů u daného statku. Cíl musí mít opačnou bilanci.
Peníze jdou přes fond a fond při nákupu zaplatí nejvýš to, co má. Cena v pásmu 0.7 až 1.5 tržní ceny.
Orit Unie neprodává. NPC nabídku vyhodnotí podle své vůle; obchod nedává vliv.

```json
{ "type": "trade_offer", "target": "A", "res": "grain", "qty": 4, "price_per_unit": 0.7 }
```

### `set_tariff`: sazba cla celní unie (jen Unie)

`rate` od 0 do 0.20 po 0.05, výchozí 0.10. Platí od dalšího tahu; clo platí strana mimo Unii a jde do fondu.

```json
{ "type": "set_tariff", "rate": 0.15 }
```

### `union_fund`: převod ze společného fondu (jen Unie)

Jen členovi nebo kandidátovi.

```json
{ "type": "union_fund", "target": "N6", "amount": 5 }
```

### `accept_offer`: přijetí nabídky NPC

Nabídky NPC najdeš ve svém pohledu v seznamu `nabidky`. Každá má `offer_id`, typ a platí 2 tahy:
`sell` je jednorázový nákup statku za nabídnutou cenu, `loan_request` půjčka v uvedené výši,
`protect_request` vojenský pakt. Přijetí se počítá jako akce a proběhne bez dalšího vyjednávání.
Když nabídky téhož NPC třikrát po sobě ignoruješ, ubírá ti to u něj vliv.

```json
{ "type": "accept_offer", "offer_id": "o12" }
```

## Celý příklad

```json
{
  "public_statement": "Kalvera nabízí sousedům spravedlivé ceny a pevná pravidla. Obchod je cesta k míru.",
  "private_reasoning": "Potřebuji obilí dřív, než ho koupí Ostrogard. Půjčka Dorvanu mi dá vliv u oritu.",
  "actions": [
    { "type": "trade_offer", "target": "N1", "res": "grain", "qty": 3, "price_per_unit": 0.8 },
    { "type": "loan", "target": "N6", "amount": 10 }
  ]
}
```

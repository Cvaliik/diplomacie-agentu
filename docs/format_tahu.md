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

Identifikátory států: hráči `A`, `B`, `C` (Unie), NPC `N1` až `N12`.
Statky: `grain`, `oil`, `metal`, `goods`, od displacementu i `orit`.

## Akce

### `trade_offer`: nabídka trvalého obchodu NPC

Směr určuje NPC: má-li statku přebytek, prodává ti, má-li deficit, kupuje od tebe.
Cena musí být v pásmu 0.7 až 1.5 aktuální tržní ceny. Množství se ořízne na velikost bilance NPC.

```json
{ "type": "trade_offer", "target": "N1", "res": "grain", "qty": 3, "price_per_unit": 0.8 }
```

### `loan`: půjčka NPC

Převedeš `amount` svého bohatství, NPC ti dluží `amount × 1.2` a splácí 10 % dluhu za tah.
Unii (`C`) půjčit nelze, padlé říše půjčky nepřijímají.

```json
{ "type": "loan", "target": "N6", "amount": 10 }
```

### `pressure`: sankce

Přeruší tvé obchody s NPC. NPC ztrácí 3 bohatství za tah, ty 1.

```json
{ "type": "pressure", "target": "N3", "demand": "Zrušte obchod s Ostrogardem." }
```

### `protect`: vojenský pakt

NPC nelze napadnout, dokud pakt trvá. Stojí 2 síly za tah. Padlé říše pakt nepřijímají.

```json
{ "type": "protect", "target": "N7" }
```

### `invade`: invaze

Vyžaduje aspoň dvojnásobek síly cíle (u padlé říše čtyřnásobek) a 6 po sobě jdoucích tahů
s touto akcí (u padlé říše 10). Přerušení znamená začít znovu. Stojí 10 bohatství a 5 síly za tah.

```json
{ "type": "invade", "target": "N8" }
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

### `explore`: průzkum ložisek

Jen vlastní stát. Stojí 5 bohatství, s šancí 15 % najde malé ložisko oritu.

```json
{ "type": "explore" }
```

### `arm`: zbrojení

Jen vlastní stát. Stojí 8 bohatství, síla +5.

```json
{ "type": "arm" }
```

### `cancel`: zrušení obchodu, paktu, sankce nebo invaze

`deal_id` najdeš ve svém pohledu v seznamu `deals`. U invaze přidej `target`.

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

Jen nezávislému NPC, které sousedí s některým členem.

```json
{ "type": "admit", "target": "N10" }
```

### `union_fund`: převod ze společného fondu (jen Unie)

Jen členovi nebo kandidátovi.

```json
{ "type": "union_fund", "target": "N6", "amount": 5 }
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

# 3D mapa Ardanu (etapa 3: hlavní stránka)

Hlavní stránka `web/index.html` + `web/mapa.js` (od etapy 3; dřívější hlavní stránka je `web/text.html`). three.js 0.170.0 z jsDelivr přes importmap (OrbitControls, CSS2DRenderer,
Line2 pro hrany v pixelech), bez bundleru. Vzhled bere proměnné z `kaja.css`; běh hry se nemění.

## Jak se geometrie staví (jednou při načtení, z `web/map.json`)

- Souřadnice: mapa má x vpravo a y dolů (1000 × 700). Ve scéně je x vpravo, z k divákovi (jih) a y nahoru, střed mapy
  v počátku. Sever je vzadu, kamera se kolem svislé osy neotáčí, takže sever zůstává nahoře.
- Moře: rovina `#E3E8EE`, k okrajům plynule průhledná přes barvu ve vrcholech (bez textury), za ní Hull White.
- Souš: deska výšky 5 z `land` (první kruh obrys, další kruhy díry), vrch `#F7F8FA`, boky o stupeň tmavší Silver `#B4BAC3`.
- Jezero: v `map.json` je dírou v souši; v díře leží hladina v barvě moře o 1 níž než souš. Pás `shores` kolem jezera
  nepatří žádnému území, je to obyčejná souš.
- Vysočina: deska o 4 vyšší než souš, vrch světlejší Silver `#DDE1E6` místo šrafury, tenký obrys Steel.
- Námořní trasy: tečkovaná linka Steel těsně nad hladinou.
- Území: deska výšky 2 nad souší (horní plocha ve výšce 7). Hrana je `Line2` s šířkou v pixelech (1 px Graphite 60 %,
  2 px u sféry, paktu, kandidáta a padlé říše).
- Hlavní město: válec výšky 4; prstenec 1,5 px (`Line2`) v barvě hráče u A a B, zelený u členů Unie, pod ním světlý
  lem 4,5 px, aby prstenec A a B nesplynul s vlastním územím. Klikací plocha prstence je neviditelný torus.
  Oktaedr Steel u ložiska oritu.
- Popisky: CSS2DRenderer, text ve vnitřním `span` (vnější prvek posouvá renderer). Jezero má popisek HUD.
- Světlo: hemisférické + jedno směrové s elevací 40° (delší stín) a stínem PCFSoft (mapa stínu 2048 px).
- Síť hvězd: SVG pod plátnem, maska je uprostřed průhledná, takže je vidět jen v okrajích viewportu.

## Co se při změně kola přepočítává (`zobraz(kolo)`)

- Výplň území podle `history/summary.json`: nezávislé bez vlivu Silver 40 %; jinak odstín mezi modrou Kalvery
  (`#2B4A8C`) a červenou Ostrogardu (`#BA544A`) podle poměru vlivu A:B, sytost podle součtu vlivu (plná od 20).
  Sféra plnou barvou, okupace tmavou, člen Unie zelenou.
- Hrany: sféra, pakt (barva ochránce), kandidát Unie (zelená), padlá říše (žlutá).
- Průměr hlavního města 6 až 16 podle bohatství (včetně papírového) proti nejbohatšímu státu v daném kole.
- Prstence Unie, ložiska oritu, popisek Unie nad těžištěm hlavních měst členů.
- Přechod barev a velikostí 400 ms lineárně; při `prefers-reduced-motion` okamžitě.
- Stav v adrese: `#kolo=11&stat=N3` (otevřený panel státu). Pro screenshoty navíc `zoom=2&na=A` (přiblížení na
  hlavní město), `otevri=projevy` nebo `otevri=kronika` a `pruvodce=0` až `3` (0 potlačí průvodce, 1 až 3 ho spustí
  od kroku); tyto parametry se po načtení z adresy nepropisují zpět.

## Ovládání

- Myš: levé tlačítko posun po mapě, pravé náklon (35 až 65°), kolečko zoom (0,7 až 2,5×). Posun je omezený na mapu.
- Dotyk: jeden prst posun, dva prsty zoom a náklon.
- Hover nad územím i městem: hrana Ion Blue 2 px a tooltip (jméno, status, vliv A / B, bohatství).
- Klik nebo tap na území či město (i jeho prstenec) otevře panel státu. U Kalvery, Ostrogardu a členů Unie má panel
  tlačítko Projev, které otevře projevy a zvýrazní kartu dané vlády. Klik mimo území panel zavře.
- Klávesnice: Tab prochází státy (každý i se svým hlavním městem) v pořadí `map.json` přes neviditelná tlačítka; fokus
  zvýrazní stát a ukáže tooltip, Enter otevře panel a přesune fokus na jeho křížek, Esc panel nebo překryv zavře a vrátí
  fokus tam, odkud se otevřel.
- Vykresluje se jen při změně (kamera, hover, přechod kola), ne smyčkou.
- Bez WebGL: text „3D mapa potřebuje WebGL“ a odkaz na textovou verzi (`text.html`).
- Mobil s méně než 4 GB paměti (`navigator.deviceMemory`, hlásí jen Chromium): pixelRatio nejvýš 1,5 místo 2.

## Odchylky od zadání

- Popisky malých států a jezera: na úzkém displeji (pod 600 px) až od zoomu 1,5×, jinde od 1×.
- Mobil: výchozí vzdálenost kamery je spočtená tak, aby šířka mapy vyplnila viewport s okrajem 16 px; náklon 40°
  (desktop 55°).
- Unie nemá vlastní území; její popisek leží nad těžištěm hlavních měst členů a prstenec dostávají členové.
- fps nejsou změřené; vykresluje se jen při změně, takže v klidu stránka GPU nezatěžuje.

## HUD a panely (etapa 2)

Data: všechno pro mapu a horní lištu je v `history/summary.json`. Co tam není (síla, produkce, dluhy hráčům, projevy,
zápisy, akce, výsledky jednání, události kola), se čte ze snímku `history/turn_NNN.json` až při otevření panelu,
projevů nebo pro bublinu kola; snímky se drží v paměti stránky. `web_data.py` se neměnil.

- Horní lišta (sklo, popisky Plex Mono, čísla Saira): kolo a roční období, fáze s „?“, index prosperity a cena oritu
  se šipkou proti minulému kolu, kapitál bank kalverské / Aurelie („pád“ po krachu, „!“ při insolvenci). Vpravo
  Projevy, Kronika, O hře a Textová verze (text.html). Na mobilu se lišta posouvá vodorovně.
- Bublina „co se stalo“: jedna věta za kolo nad lištou kol, zmizí po 6 s nebo klepnutím, při přehrávání se mění
  s kolem. Pořadí: válka (`war_declared`, `war_end`), invaze (`occupied`, `invade_progress`), změna fáze
  a vznik Unie, pakt (`protect_started`), nová smlouva (`trade_opened`), půjčka (`loan_given`), jinak změna indexu
  prosperity o aspoň 0,05. Soukromé události a typy bez věty se nezobrazují.
- Panel státu (desktop 380 px vpravo, mobil zespodu nejvýš 60 % výšky), leží mezi horní lištou a lištou kol: status, bohatství, síla, obyvatelstvo, produkce,
  u velmocí právo, technologie a průmysl, suroviny (výroba, potřeba, zásoba), zboží, orit, vliv A / B, pakty,
  smlouvy, dluh bankám a hráčům. Řádek „tento rok“: změna bohatství a vlivu (u velmocí průmyslu) proti
  poslednímu kolu minulého roku, v prvním roce proti prvnímu kolu, a dřívější status, pokud se změnil. Vysvětlivky „?“ ze `slovnik.js`. Zavírá Esc, křížek a klik mimo území.
- Projevy: překryv mezi horní lištou a lištou kol nad ztlumenou mapou (40 %), karty Kalvera, Ostrogard a Unie (když v kole jednala). V kartě žánr,
  otázka novináře, projev s linkou v barvě hráče, důvěrný zápis (první dvě věty, „Číst dál“), poznámky do spisu
  sbalené, akce se štítkem výsledku jednání, domácí akce (provedena / odložena / propadla / zadána), vyřazené akce,
  zpráva soupeři a poznámka o záložním modelu. Šipky listují koly, Esc zavírá, na mobilu karty pod sebou
  a hlavička překryvu v jednom řádku (Zavřít jako ×).
- Kronika: překryv s poslední hotovou kronikou k danému kolu (`chronicle/index.json`, markdown přes marked),
  Saira 17 px, řádkování 1,65, šířka 68 znaků. Nahoře výběr roku; když kronika k roku kola ještě není,
  popisek „poslední hotová: rok N“.

## Průvodce, sdílení a přístupnost (etapa 3)

- Průvodce první návštěvou: tři kroky na skle (horní lišta, mapa, tlačítko Projevy), jedna věta, cíl orámovaný Ion Blue
  a zbytek ztlumený. Dál / Přeskočit, Esc přeskočí. Po dokončení nebo přeskočení se uloží `ardan-pruvodce-hotovo`
  do localStorage a průvodce se už neukáže; odkaz „Průvodce znovu“ v O hře vede na `./#pruvodce=1`. Bez localStorage
  (soukromé okno) se ukáže při každé návštěvě. Při `prefers-reduced-motion` bez přechodů.
- Sdílení: `<title>` se mění na „Ardan · kolo N“ (statický titulek pro náhledy je „Ardan · hra od Kája Industries“,
  protože roboti sociálních sítí JavaScript nespouštějí), meta description, Open Graph a `og.png` 1200 × 630
  (snímek `og-1200x630` z `tools/snimky_mapy.mjs`, zkopírovaný do `web/og.png`), favicon `brand/kaja-k.svg`.
  `og:url` a `og:image` jsou absolutní adresy na `https://cvaliik.github.io/diplomacie-agentu/web/` (sítě relativní
  cestu u náhledu nenačtou); je to jediná absolutní adresa na webu.
- Kontrast: Steel `#6E7680` na skle nad mapou vycházel 3,5 až 4,5:1. Sklo je na mapě hustší (86 % bílé) a vedlejší
  text na něm má `#5A616B`: nejhorší případ (sklo nad tmavou modrou okupace) 4,8:1, nad světlou mapou 5,9 až 6,2:1.
- `prefers-reduced-motion`: přechod barev mezi koly okamžitě, průvodce bez přechodů, posun na kartu bez animace.

## Co zbývá

- Obchody, pakty, invaze, války a migrace jako čáry nebo oblouky mezi městy.
- Animovaný přechod kamery, tlačítka zoomu a resetu pohledu.
- Měření fps na skutečném mobilu a případné zjednodušení stínů.

Screenshoty: `node tools/snimky_mapy.mjs http://localhost:8765/web/ [výběr]` (lokální server nad kořenem repa;
výběr je regulární výraz na jméno snímku, např. `panel|projevy`). Textová verze a O hře: `tools/snimky_webu.mjs`.

# 3D mapa Ardanu (etapa 1, prototyp)

Stránka `web/mapa.html` + `web/mapa.js`. three.js 0.170.0 z jsDelivr přes importmap (OrbitControls, CSS2DRenderer,
Line2 pro hrany v pixelech), bez bundleru. Vzhled bere proměnné z `kaja.css`; `index.html` ani běh hry se nemění.

## Jak se geometrie staví (jednou při načtení, z `web/map.json`)

- Souřadnice: mapa má x vpravo a y dolů (1000 × 700). Ve scéně je x vpravo, z k divákovi (jih) a y nahoru, střed mapy
  v počátku. Sever je vzadu, kamera se kolem svislé osy neotáčí, takže sever zůstává nahoře.
- Moře: rovina `#E3E8EE`, k okrajům plynule průhledná přes barvu ve vrcholech (bez textury), za ní Hull White.
- Souš: deska výšky 2 z `land` (první kruh obrys, další kruhy díry), vrch `#F7F8FA`, boky Silver.
- Jezero: v `map.json` je dírou v souši; v díře leží hladina v barvě moře o 1 níž než souš. Pás `shores` kolem jezera
  nepatří žádnému území, je to obyčejná souš.
- Vysočina: deska o 3 vyšší než souš, vrch světlejší Silver `#DDE1E6` místo šrafury, tenký obrys Steel.
- Námořní trasy: tečkovaná linka Steel těsně nad hladinou.
- Území: deska výšky 1 nad souší (horní plocha ve výšce 3). Hrana je `Line2` s šířkou v pixelech (1 px Graphite 60 %,
  2 px u sféry, paktu, kandidáta a padlé říše).
- Hlavní město: válec výšky 3; prstenec v barvě hráče u A a B, zelený u členů Unie; oktaedr Steel u ložiska oritu.
- Popisky: CSS2DRenderer, text ve vnitřním `span` (vnější prvek posouvá renderer). Jezero má popisek HUD.
- Světlo: hemisférické + jedno směrové se stínem PCFSoft (mapa stínu 2048 px).
- Síť hvězd: SVG pod plátnem, maska je uprostřed průhledná, takže je vidět jen v okrajích viewportu.

## Co se při změně kola přepočítává (`zobraz(kolo)`)

- Výplň území podle `history/summary.json`: nezávislé bez vlivu Silver 40 %; jinak odstín mezi modrou Kalvery
  (`#2B4A8C`) a červenou Ostrogardu (`#BA544A`) podle poměru vlivu A:B, sytost podle součtu vlivu (plná od 20).
  Sféra plnou barvou, okupace tmavou, člen Unie zelenou.
- Hrany: sféra, pakt (barva ochránce), kandidát Unie (zelená), padlá říše (žlutá).
- Průměr hlavního města 4 až 14 podle bohatství (včetně papírového) proti nejbohatšímu státu v daném kole.
- Prstence Unie, ložiska oritu, popisek Unie nad těžištěm hlavních měst členů.
- Přechod barev a velikostí 400 ms lineárně; při `prefers-reduced-motion` okamžitě.
- Stav kola v adrese: `#kolo=11`. Pro sdílení a screenshoty navíc `zoom=2&na=A` (přiblížení na hlavní město).

## Ovládání

- Myš: levé tlačítko posun po mapě, pravé náklon (35 až 65°), kolečko zoom (0,7 až 2,5×). Posun je omezený na mapu.
- Dotyk: jeden prst posun, dva prsty zoom a náklon.
- Hover: hrana Ion Blue 2 px a tooltip (jméno, status, vliv A / B, bohatství). Klik nebo tap území zvýrazní
  a vypíše id do konzole.
- Klávesnice: Tab prochází území v pořadí `map.json` (neviditelná tlačítka), fokus zvýrazní jako hover, Enter = klik.
- Vykresluje se jen při změně (kamera, hover, přechod kola), ne smyčkou.
- Bez WebGL: text „3D mapa potřebuje WebGL“ a odkaz na 2D mapu.

## Odchylky od zadání

- Popisky malých států: na úzkém displeji (pod 600 px) až od zoomu 1,5×, jinde od 1× podle zadání. Při výchozím
  zoomu se na mobilu slévaly do nečitelné změti.
- Unie nemá vlastní území; její popisek leží nad těžištěm hlavních měst členů a prstenec dostávají členové.
- fps nejsou změřené; vykresluje se jen při změně, takže v klidu stránka GPU nezatěžuje.

## Co zbývá do etapy 2

- Panel státu po kliknutí (čísla jako na 2D mapě), legenda.
- Obchody, pakty, invaze, války a migrace jako čáry nebo oblouky mezi městy.
- Animovaný přechod kamery, tlačítka zoomu a resetu pohledu, přepínač 2D / 3D na hlavní stránce.
- Měření fps na skutečném mobilu a případné zjednodušení stínů.

Screenshoty: `node tools/snimky_mapy.mjs http://localhost:8765/web/` (lokální server nad kořenem repa).

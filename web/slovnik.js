/* Slovník pojmů pro web: jediné místo s větami, index.html z něj bere vysvětlivky, o-hre.html seznam pojmů. */
"use strict";

window.ARDAN_SLOVNIK = [
  ["vliv", "jak moc stát poslouchá danou velmoc; roste obchodem, pakty a půjčkami."],
  ["sféra", "stát, kde jedna velmoc má vliv tak silný, že rozhoduje o jeho politice."],
  ["pakt", "velmoc stát chrání; útok na něj je válka. Stát za to platí částí své svobody."],
  ["smlouva", "trvalá dodávka za pevnou cenu, dokud ji některá strana nezruší."],
  ["půjčka", "peníze teď, dluh a závislost potom."],
  ["protinávrh", "stát nabídku neodmítl, ale chce lepší podmínky."],
  ["zboží (goods)", "výrobek továren; lidé ho spotřebují, zbytek se prodá, a každá investice ho potřebuje."],
  ["domácí akce", "investice vlády do vlastního práva, technologie, průmyslu, těžby nebo armády; jedna za tah."],
  ["právo", "pevnost institucí."],
  ["technologie", "výtěžnost polí a vrtů."],
  ["průmysl", "kolik zboží stát umí vyrobit."],
  ["Unie", "spolek menších států s vlastními pravidly; vzniká až po krizi."],
  ["kandidát", "stát, který chce do Unie, ale ještě nesplňuje podmínky."],
  ["padlá říše", "kdysi velmoc, dnes bohatý, opatrný stát mimo hru o vliv."],
  ["orit", "vzácná surovina, kolem které se točí horečka i krach."],
  ["index prosperity", "jak se vede Ardanu jako celku; vlády ho nevidí."]
];

/* Hospodářský cyklus: pět fází pro čtenáře (oddíl Cyklus na stránce O hře). */
window.ARDAN_CYKLUS = {
  uvod: "Ardan prochází hospodářským cyklem.",
  faze: {
    klid: "Klid: nikdo nic netuší.",
    objev: "Objev: najde se orit, vzácná surovina, a začne horečka.",
    horecka: "Horečka: ceny rostou, půjčuje se, každý chce být u toho.",
    krach: "Krach: bublina praskne, dluhy zůstanou.",
    kocovina: "Kocovina: svět počítá škody a hledá, kdo za to může."
  },
  /* fáze enginu (Minskyho cyklus) na fázi pro čtenáře */
  podle_enginu: {
    pre: "klid", displacement: "objev", boom: "horecka", euphoria: "horecka", overtrading: "horecka",
    distress: "krach", panic: "krach", crash: "krach", depression: "kocovina", recovery: "kocovina"
  }
};

window.ardanPojem = (klic) => {
  const radek = window.ARDAN_SLOVNIK.find(([k]) => k === klic);
  return radek ? radek[1] : "";
};

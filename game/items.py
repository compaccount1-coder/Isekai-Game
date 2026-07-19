"""Ausrüstungssystem: Waffen, Rüstungen, Accessoires mit Seltenheitsstufen."""

import random
from dataclasses import dataclass, field

SELTENHEIT_STUFEN = [
    ("Gewöhnlich", 1.0, 0.40, 10),
    ("Ungewöhnlich", 1.3, 0.28, 25),
    ("Selten", 1.7, 0.18, 60),
    ("Episch", 2.3, 0.10, 150),
    ("Legendär", 3.2, 0.04, 400),
]  # (name, stat_multiplikator, drop_gewicht, basis_wert)

WAFFEN_BASIS = [
    "Schwert", "Dolch", "Stab", "Bogen", "Axt", "Streitkolben", "Speer", "Kriegshammer",
    "Klinge", "Zepter", "Armbrust", "Kampfstab", "Katana", "Rapier",
]
RUESTUNG_BASIS = [
    "Rüstung", "Robe", "Lederkleidung", "Kettenhemd", "Plattenpanzer", "Umhang",
    "Gewand", "Brustpanzer", "Schuppenpanzer", "Mantel",
]
ACCESSOIRE_BASIS = [
    "Ring", "Amulett", "Talisman", "Anhänger", "Armreif", "Siegelring", "Kette", "Brosche",
]

PRAEFIXE_NACH_SELTENHEIT = {
    "Gewöhnlich": ["Einfaches", "Grundlegendes", "Solides", "Schlichtes"],
    "Ungewöhnlich": ["Verstärktes", "Feines", "Geschärftes", "Robustes"],
    "Selten": ["Verzaubertes", "Glühendes", "Meisterhaft gefertigtes", "Uraltes"],
    "Episch": ["Runenbeschworenes", "Drachengeschmiedetes", "Sternenmetall-", "Verfluchtes"],
    "Legendär": ["Göttliches", "Weltenbrecher-", "Ewiges", "Mythisches"],
}

NAMENSZUSAETZE_SELTEN = [
    "des Sonnenaufgangs", "der tausend Winter", "des letzten Königs", "der verlorenen Ära",
    "des Abgrunds", "der ewigen Flamme", "des stillen Todes", "der vergessenen Götter",
    "des Sturms", "der endlosen Nacht", "des ersten Helden", "der zerbrochenen Krone",
]

STAT_PRO_TYP = {
    "Waffe": ("STR", "DEX"),
    "Ruestung": ("CON", "DEX"),
    "Accessoire": ("INT", "WIS", "CHA"),
}


@dataclass
class Item:
    name: str
    typ: str  # "Waffe", "Ruestung", "Accessoire"
    seltenheit: str
    stat_boni: dict[str, int]
    wert: int  # Gold-Wert beim Verkauf

    def stat_gesamt(self) -> int:
        return sum(self.stat_boni.values())

    def anzeige(self) -> str:
        boni = ", ".join(f"{k} +{v}" for k, v in self.stat_boni.items())
        return f"{self.name} [{self.seltenheit}] ({boni}, Wert: {self.wert}g)"


def _wuerfle_seltenheit(mindest_seltenheit: str | None = None) -> tuple[str, float, int]:
    stufen = SELTENHEIT_STUFEN
    if mindest_seltenheit:
        namen = [s[0] for s in SELTENHEIT_STUFEN]
        start = namen.index(mindest_seltenheit)
        stufen = SELTENHEIT_STUFEN[start:]
    gewichte = [s[2] for s in stufen]
    stufe = random.choices(stufen, weights=gewichte, k=1)[0]
    return stufe[0], stufe[1], stufe[3]


def generiere_item(mindest_level: int = 1, typ: str | None = None, mindest_seltenheit: str | None = None) -> Item:
    typ = typ or random.choice(["Waffe", "Ruestung", "Accessoire"])
    seltenheit, multiplikator, basiswert = _wuerfle_seltenheit(mindest_seltenheit)

    if typ == "Waffe":
        basis = random.choice(WAFFEN_BASIS)
    elif typ == "Ruestung":
        basis = random.choice(RUESTUNG_BASIS)
    else:
        basis = random.choice(ACCESSOIRE_BASIS)

    praefix = random.choice(PRAEFIXE_NACH_SELTENHEIT[seltenheit])
    name = f"{praefix} {basis}"
    if seltenheit in ("Episch", "Legendär") and random.random() < 0.7:
        name += f" {random.choice(NAMENSZUSAETZE_SELTEN)}"

    moegliche_stats = STAT_PRO_TYP[typ]
    anzahl_stats = 1 if seltenheit in ("Gewöhnlich", "Ungewöhnlich") else min(2, len(moegliche_stats))
    gewaehlte_stats = random.sample(moegliche_stats, anzahl_stats)

    basis_bonus = max(1, mindest_level // 8)
    stat_boni = {
        stat: max(1, int(round(basis_bonus * multiplikator * random.uniform(0.8, 1.3))))
        for stat in gewaehlte_stats
    }

    wert = int(basiswert * multiplikator * (1 + mindest_level * 0.15))

    return Item(name=name, typ=typ, seltenheit=seltenheit, stat_boni=stat_boni, wert=wert)


def schmiede_upgrade(item: Item, kosten_faktor: float = 1.0) -> tuple[Item, int]:
    """Verstärkt ein vorhandenes Item beim Schmied. Gibt (neues Item, Kosten) zurück."""
    kosten = int(item.wert * 0.8 * kosten_faktor) + 20
    neue_boni = {k: v + max(1, v // 4) for k, v in item.stat_boni.items()}
    verbessertes_item = Item(
        name=f"{item.name} +1" if "+" not in item.name else _erhoehe_plus(item.name),
        typ=item.typ,
        seltenheit=item.seltenheit,
        stat_boni=neue_boni,
        wert=int(item.wert * 1.35),
    )
    return verbessertes_item, kosten


def _erhoehe_plus(name: str) -> str:
    basis, _, stufe = name.rpartition("+")
    try:
        return f"{basis}+{int(stufe) + 1}"
    except ValueError:
        return f"{name}+1"


# ---------------------------------------------------------------------------
# Tränke (Verbrauchsgegenstände)
# ---------------------------------------------------------------------------

TRANK_QUALITAETEN = [
    ("Kleiner", 1.0, 15),
    ("", 1.8, 25),
    ("Großer", 3.0, 45),
    ("Meisterhafter", 5.0, 90),
]


@dataclass
class Trank:
    name: str
    typ: str  # "Heilung" oder "Mana"
    wirkung: int
    wert: int

    def anzeige(self) -> str:
        ziel = "HP" if self.typ == "Heilung" else "MP"
        return f"{self.name} (+{self.wirkung} {ziel}, Wert: {self.wert}g)"


def generiere_trank(level: int, typ: str | None = None) -> Trank:
    typ = typ or random.choice(["Heilung", "Mana"])
    praefix, multiplikator, basiswert = random.choice(TRANK_QUALITAETEN)
    grundwort = "Heiltrank" if typ == "Heilung" else "Manatrank"
    name = f"{praefix} {grundwort}".strip()
    wirkung = int((20 + level * 3) * multiplikator * random.uniform(0.85, 1.15))
    wert = int(basiswert * (1 + level * 0.08))
    return Trank(name=name, typ=typ, wirkung=wirkung, wert=wert)

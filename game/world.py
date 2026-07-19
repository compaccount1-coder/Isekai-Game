"""Weltgenerierung: Königreiche, Städte, Gilden - bei jedem Spielstart neu gewürfelt."""

import random
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Namensbausteine für prozedurale Generierung
# ---------------------------------------------------------------------------

KOENIGREICH_PRAEFIX = [
    "Sil", "Val", "Thorn", "Aer", "Drak", "Mor", "Lys", "Kar", "Eld", "Vyr",
    "Nor", "Fael", "Ash", "Grim", "Sol", "Wyn", "Bel", "Rav", "Tal", "Xer",
]
KOENIGREICH_SUFFIX = [
    "vania", "mark", "heim", "gard", "reich", "hold", "wald", "furt", "stein", "burg",
    "moor", "fels", "tal", "krone", "land", "grund", "spitze", "ruh", "hort", "schlund",
]

STADT_PRAEFIX = [
    "Rabe", "Wolf", "Eisen", "Silber", "Gold", "Dorn", "Nebel", "Sturm", "Schatten", "Sonnen",
    "Mond", "Stern", "Fels", "Fluss", "Berg", "Wald", "See", "Feuer", "Eis", "Wind",
]
STADT_SUFFIX = [
    "hafen", "burg", "furt", "stadt", "dorf", "brück", "tor", "wacht", "hügel", "grat",
    "au", "kron", "feld", "hain", "gau", "born",
]

STADT_TYPEN = [
    ("Hauptstadt", "das politische und militärische Zentrum des Königreichs"),
    ("Handelsstadt", "ein geschäftiges Zentrum des Handels, in dem Waren aus aller Welt umgeschlagen werden"),
    ("Grenzstadt", "eine befestigte Siedlung an der gefährlichen Grenze zur Wildnis"),
    ("Hafenstadt", "ein belebter Hafen mit Schiffen aus fernen Ländern"),
    ("Bergarbeiterstadt", "eine Siedlung, die vom Abbau seltener Erze und Edelsteine lebt"),
    ("Tempelstadt", "ein heiliger Ort, der von Priestern und Pilgern bevölkert wird"),
    ("Freistadt", "eine unabhängige Stadt, die keinem Königreich untersteht"),
    ("Magiermetropole", "ein Zentrum arkaner Forschung mit türmereichem Stadtbild"),
]

KOENIGREICH_CHARAKTER = [
    "gerecht und vom Volk geliebt",
    "tyrannisch und von Furcht regiert",
    "dekadent und von inneren Intrigen zerfressen",
    "militaristisch und stets kriegsbereit",
    "isolationistisch und misstrauisch gegenüber Fremden",
    "expansionistisch und hungrig nach neuem Land",
    "von einer Priesterkaste theokratisch regiert",
    "in einen schwelenden Bürgerkrieg verstrickt",
    "wohlhabend durch florierenden Handel",
    "verarmt nach Jahren der Missernten",
]

GILDEN_TYPEN = [
    ("Abenteurergilde", "vermittelt Aufträge für Monsterjagden, Eskorten und Erkundungen"),
    ("Magiergilde", "erforscht arkane Geheimnisse und bildet Zauberkundige aus"),
    ("Assassinengilde", "operiert im Verborgenen und erledigt Aufträge, über die niemand spricht"),
    ("Händlergilde", "kontrolliert einen Großteil des regionalen Handels"),
    ("Schmiedegilde", "fertigt die feinsten Waffen und Rüstungen der Region"),
    ("Kriegergilde", "trainiert Kämpfer und organisiert Turniere"),
    ("Heilergilde", "betreibt Krankenhäuser und bildet Heiler aus"),
    ("Söldnergilde", "vermietet bewaffnete Kämpfer an den Meistbietenden"),
    ("Diebesgilde", "kontrolliert das Unterweltgeschäft der Stadt"),
    ("Entdeckergilde", "finanziert Expeditionen in unerforschte Gebiete"),
]

GILDEN_RAENGE = [
    "Neuling", "Mitglied", "Erfahren", "Veteran", "Elite", "Meister", "Gildenältester",
]

HAUS_NAMEN = [
    "Ravenmoor", "Silberklinge", "Sturmfels", "Nachtdorn", "Goldherz", "Eisenkrone",
    "Drachenblut", "Schattenwind", "Sonnentempel", "Wolfsbann", "Aschgard", "Vyrenfall",
]


@dataclass
class Stadt:
    name: str
    typ: str
    beschreibung: str
    gilden: list[str] = field(default_factory=list)


@dataclass
class Koenigreich:
    name: str
    herrscherhaus: str
    charakter: str
    hauptstadt: str
    weitere_staedte: list[Stadt] = field(default_factory=list)
    macht: int = 50  # 0-100, relative Stärke
    beziehung_zum_spieler: int = 0  # -100 bis 100


@dataclass
class Welt:
    koenigreiche: list[Koenigreich]
    alle_gilden: dict[str, list[str]]  # Gildenname -> [Städte, in denen sie vertreten ist]

    def zufaelliges_koenigreich(self, ausser: "Koenigreich | None" = None) -> Koenigreich:
        kandidaten = [k for k in self.koenigreiche if k is not ausser]
        return random.choice(kandidaten)

    def zufaellige_stadt(self) -> tuple[Koenigreich, str]:
        k = random.choice(self.koenigreiche)
        alle_staedte = [k.hauptstadt] + [s.name for s in k.weitere_staedte]
        return k, random.choice(alle_staedte)

    def zusammenfassung(self) -> str:
        zeilen = [f"Die bekannte Welt umfasst {len(self.koenigreiche)} Königreiche:"]
        for k in self.koenigreiche:
            zeilen.append(f"  • {k.name} ({k.herrscherhaus}), Hauptstadt {k.hauptstadt} - {k.charakter}")
        return "\n".join(zeilen)


def _generiere_namen(praefixe: list[str], suffixe: list[str]) -> str:
    return random.choice(praefixe) + random.choice(suffixe)


def _generiere_stadt(bereits_verwendet: set[str]) -> Stadt:
    name = _generiere_namen(STADT_PRAEFIX, STADT_SUFFIX)
    while name in bereits_verwendet:
        name = _generiere_namen(STADT_PRAEFIX, STADT_SUFFIX)
    bereits_verwendet.add(name)
    typ, beschreibung = random.choice(STADT_TYPEN)
    anzahl_gilden = random.randint(1, 4)
    gilden = random.sample([g[0] for g in GILDEN_TYPEN], anzahl_gilden)
    return Stadt(name=name, typ=typ, beschreibung=beschreibung, gilden=gilden)


def generiere_welt(anzahl_koenigreiche: int = 5) -> Welt:
    """Erzeugt eine zufällige Welt. Jeder Spieldurchlauf sieht anders aus."""
    verwendete_namen: set[str] = set()
    koenigreiche = []

    for _ in range(anzahl_koenigreiche):
        name = _generiere_namen(KOENIGREICH_PRAEFIX, KOENIGREICH_SUFFIX)
        while name in verwendete_namen:
            name = _generiere_namen(KOENIGREICH_PRAEFIX, KOENIGREICH_SUFFIX)
        verwendete_namen.add(name)

        hauptstadt = _generiere_stadt(verwendete_namen)
        anzahl_weitere = random.randint(2, 4)
        weitere = [_generiere_stadt(verwendete_namen) for _ in range(anzahl_weitere)]

        koenigreiche.append(
            Koenigreich(
                name=f"Königreich {name}",
                herrscherhaus=f"Haus {random.choice(HAUS_NAMEN)}",
                charakter=random.choice(KOENIGREICH_CHARAKTER),
                hauptstadt=hauptstadt.name,
                weitere_staedte=[hauptstadt] + weitere,
                macht=random.randint(20, 100),
            )
        )

    alle_gilden: dict[str, list[str]] = {g[0]: [] for g in GILDEN_TYPEN}
    for k in koenigreiche:
        for stadt in k.weitere_staedte:
            for g in stadt.gilden:
                alle_gilden[g].append(stadt.name)

    return Welt(koenigreiche=koenigreiche, alle_gilden=alle_gilden)

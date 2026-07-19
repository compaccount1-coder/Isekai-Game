"""Begleiter: Abenteurergruppen, mit denen der Protagonist gemeinsam Dungeons erobert."""

import random
from dataclasses import dataclass

from game.classes import KLASSEN, ROLLEN, klassen_nach_rolle

BEGLEITER_NAMEN = [
    "Joric", "Sennah", "Baldwin", "Yris", "Corran", "Thessaly", "Aldous", "Perrin",
    "Vesna", "Halric", "Odalys", "Garrow", "Livia", "Bastien", "Marrow", "Ysolde",
]

BEGLEITER_EIGENSCHAFTEN = [
    "zuverlässig", "waghalsig", "schweigsam", "geldgierig", "loyal bis zum Ende",
    "streitlustig", "abergläubisch", "gutmütig", "ehrgeizig", "vorsichtig",
]


@dataclass
class Begleiter:
    name: str
    klasse_id: str
    eigenschaft: str
    loyalitaet: int = 50  # 0-100
    level: int = 1
    xp: int = 0

    @property
    def klassenname(self) -> str:
        return KLASSEN[self.klasse_id].tiers[0].name

    @property
    def rolle(self) -> str:
        return KLASSEN[self.klasse_id].rolle

    def anzeige(self) -> str:
        return f"{self.name} (Lv.{self.level} {self.klassenname} - {self.rolle}, {self.eigenschaft})"

    def xp_hinzufuegen(self, menge: int) -> bool:
        """Begleiter leveln automatisch mit - keine Verwaltung durch den
        Spieler nötig, sie kümmern sich eigenständig um Fähigkeiten und
        Ausrüstung im Hintergrund. Gibt True zurück, wenn ein Level-up
        stattgefunden hat."""
        self.xp += menge
        schwelle = 40 * self.level
        if self.xp >= schwelle:
            self.xp -= schwelle
            self.level += 1
            return True
        return False


def generiere_begleiter(vorhandene_rollen: list[str] | None = None) -> Begleiter:
    """Erzeugt einen zufälligen Begleiter. Sind bereits Rollen in der Gruppe
    vorhanden, wird eine fehlende Rolle bevorzugt (Gruppenbalance), aber nicht
    erzwungen - reiner Zufall bleibt möglich."""
    name = random.choice(BEGLEITER_NAMEN)
    eigenschaft = random.choice(BEGLEITER_EIGENSCHAFTEN)

    if vorhandene_rollen and random.random() < 0.65:
        fehlende_rollen = [r for r in ROLLEN if r not in vorhandene_rollen]
        if fehlende_rollen:
            ziel_rolle = random.choice(fehlende_rollen)
            klasse = random.choice(klassen_nach_rolle(ziel_rolle))
            return Begleiter(name=name, klasse_id=klasse.id, eigenschaft=eigenschaft)

    klasse_id = random.choice(list(KLASSEN.keys()))
    return Begleiter(name=name, klasse_id=klasse_id, eigenschaft=eigenschaft)


def gruppen_rollen(begleiter: list[Begleiter]) -> list[str]:
    return [KLASSEN[b.klasse_id].rolle for b in begleiter]


def ist_ausgewogene_gruppe(begleiter: list[Begleiter]) -> bool:
    """Eine Gruppe gilt als ausgewogen, wenn Nahkampf, Fernkampf und
    Unterstützung jeweils mindestens einmal vertreten sind."""
    vorhandene = set(gruppen_rollen(begleiter))
    return set(ROLLEN).issubset(vorhandene)

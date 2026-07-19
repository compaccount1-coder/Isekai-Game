"""Abenteurer-Ränge: F bis S. Ein zentrales Fortschrittsziel neben dem Level."""

RANG_REIHENFOLGE = ["F", "E", "D", "C", "B", "A", "S"]

# rang -> (Mindestlevel, Mindestzahl abgeschlossener Quests) für den Aufstieg IN diesen Rang
RANG_ANFORDERUNGEN = {
    "E": (5, 3),
    "D": (12, 8),
    "C": (22, 15),
    "B": (35, 25),
    "A": (50, 40),
    "S": (70, 60),
}

# Belohnungs-Multiplikator je Rang - höhere Ränge -> lukrativere Quests
RANG_MULTIPLIKATOR = {"F": 1.0, "E": 1.8, "D": 3.0, "C": 5.0, "B": 8.0, "A": 13.0, "S": 21.0}


def rang_index(rang: str) -> int:
    return RANG_REIHENFOLGE.index(rang)


def naechster_rang(rang: str) -> str | None:
    idx = rang_index(rang)
    if idx + 1 < len(RANG_REIHENFOLGE):
        return RANG_REIHENFOLGE[idx + 1]
    return None


def kann_aufsteigen(charakter) -> bool:
    ziel = naechster_rang(charakter.rang)
    if ziel is None:
        return False
    mindest_level, mindest_quests = RANG_ANFORDERUNGEN[ziel]
    return charakter.level >= mindest_level and charakter.abgeschlossene_quests >= mindest_quests


def anforderung_text(charakter) -> str:
    ziel = naechster_rang(charakter.rang)
    if ziel is None:
        return "Höchster Rang bereits erreicht."
    mindest_level, mindest_quests = RANG_ANFORDERUNGEN[ziel]
    return (
        f"Rang {ziel} erfordert: Level {mindest_level} (aktuell {charakter.level}), "
        f"{mindest_quests} abgeschlossene Quests (aktuell {charakter.abgeschlossene_quests})"
    )

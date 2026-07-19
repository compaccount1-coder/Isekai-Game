"""Fantasy-Völker der Welt: für NPCs, Fraktionen und Konfliktereignisse."""

import random
from dataclasses import dataclass


@dataclass
class Volk:
    name: str
    beschreibung: str
    verbuendet_mit: list[str]  # Namen anderer Völker, mit denen Spannungen/Bündnisse typisch sind


VOELKER: dict[str, Volk] = {
    "menschen": Volk("Menschen", "Anpassungsfähig und ehrgeizig, dominieren sie die meisten Königreiche.", []),
    "hochelfen": Volk("Hochelfen", "Uralte Hüter arkanen Wissens, leben zurückgezogen in glitzernden Türmen.", ["waldelfen"]),
    "waldelfen": Volk("Waldelfen", "Ein mit der Natur verwobenes Volk, misstrauisch gegenüber Städtern.", ["hochelfen"]),
    "dunkelelfen": Volk("Dunkelelfen", "Ein Volk, das in unterirdischen Reichen von Macht und Intrigen lebt.", []),
    "zwerge": Volk("Zwerge", "Meister der Schmiedekunst, leben in gewaltigen Bergfestungen.", []),
    "halblinge": Volk("Halblinge", "Ein friedliches, geselliges Volk, das Abenteuer eigentlich meidet.", []),
    "orks": Volk("Orks", "Ein stolzes Kriegervolk, oft fälschlich als reine Barbaren verschrien.", []),
    "drakonier": Volk("Drakonier", "Drachenblütige Wesen mit Schuppenhaut und angeborener Elementarmagie.", []),
    "feenwesen": Volk("Feenwesen", "Launische, uralte Geister zwischen den Welten.", []),
    "untote": Volk("Untote", "Von Nekromantie oder Fluch ins Leben zurückgerufene Wesen.", []),
    "daemonen": Volk("Dämonen", "Invasoren aus einer feindseligen, jenseitigen Ebene.", []),
}


def zufaelliges_volk(ausschluss: list[str] | None = None) -> Volk:
    ausschluss = ausschluss or []
    kandidaten = [v for k, v in VOELKER.items() if k not in ausschluss]
    return random.choice(kandidaten)


DAEMONEN_NAMEN = [
    "Malphusor der Verschlinger", "Xantheia, Herrin der Qualen", "Grimwrath, der Seelenbrenner",
    "Nyxara die Flüsternde", "Baelroth, Fürst der Asche", "Vex'thul der Unersättliche",
]

MONSTER_NACH_DUNGEON_THEMA = {
    "Krypta": ["Skelettwächter", "Ghul", "Grabraub-Golem", "Leichenfledderer-Geist"],
    "Höhlensystem": ["Höhlentroll", "Riesenspinnenschwarm", "Steinelementar", "Blindes Tiefen-Wesen"],
    "Verlassener Turm": ["Verirrter Homunkulus", "Arkaner Wächter", "Verfluchter Bibliothekar-Geist"],
    "Dämonisches Portal": ["Kleiner Dämon", "Portalwächter", "Besessener Kultist"],
    "Vergessener Tempel": ["Tempelwächter-Statue", "Verirrter Priester-Geist", "Heiliger Automat außer Kontrolle"],
    "Elfenruine": ["Verfallener Baumhüter", "Wilder Naturgeist", "Verwunschener Dornenwolf"],
    "Zwergenmine": ["Entgleister Grubenwurm", "Verlassener Kampf-Konstrukt", "Gieriger Erzgeist"],
}

DUNGEON_NAMEN_TEIL1 = [
    "Verfluchte", "Vergessene", "Blutgetränkte", "Uralte", "Verlassene", "Verschollene",
    "Flüsternde", "Zerbrochene", "Namenlose", "Eingestürzte",
]
DUNGEON_NAMEN_TEIL2 = [
    "Krypta", "Katakomben", "Höhle", "Festung", "Zitadelle", "Ruine", "Grotte", "Kathedrale", "Mine", "Turmspitze",
]


@dataclass
class Dungeon:
    name: str
    thema: str
    gefahrenstufe: int  # 1-10
    monster: list[str]


def generiere_dungeon(spieler_level: int) -> Dungeon:
    thema = random.choice(list(MONSTER_NACH_DUNGEON_THEMA.keys()))
    name = f"{random.choice(DUNGEON_NAMEN_TEIL1)} {random.choice(DUNGEON_NAMEN_TEIL2)}"
    gefahrenstufe = min(10, max(1, spieler_level // 10 + random.randint(-1, 2)))
    monster = random.sample(MONSTER_NACH_DUNGEON_THEMA[thema], k=min(2, len(MONSTER_NACH_DUNGEON_THEMA[thema])))
    return Dungeon(name=name, thema=thema, gefahrenstufe=gefahrenstufe, monster=monster)

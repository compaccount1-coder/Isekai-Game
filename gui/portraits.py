"""Klassen-Portraits: acht CC0-Portraits (siehe assets/portraits/, verarbeitet
aus "RPG Characters Avatars" von System G6/Qoma), auf die elf Klassen
verteilt - thematisch verwandte Klassen (Magier/Beschwörer, Nekromant/
Assassine, Paladin/Kleriker) teilen sich bewusst ein Portrait, statt für die
drei "fehlenden" Gesichter eigene, stilistisch abweichende Bilder zu
improvisieren. Fertig gerahmte (Schatten + Goldring) Kreis-Portraits werden
pro (Klasse, Radius) einmalig gerendert und danach nur noch geblittet."""

import os

import pygame

from gui import theme

_ORDNER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "portraits")

_DATEI_JE_KLASSE = {
    "krieger": "portrait_01.png",
    "magier": "portrait_02.png",
    "beschwoerer": "portrait_02.png",
    "waldlaeufer": "portrait_03.png",
    "nekromant": "portrait_04.png",
    "assassine": "portrait_04.png",
    "paladin": "portrait_05.png",
    "kleriker": "portrait_05.png",
    "alchemist": "portrait_06.png",
    "moench": "portrait_07.png",
    "barde": "portrait_08.png",
}

_BILD_CACHE: dict[str, pygame.Surface] = {}
_GERAHMT_CACHE: dict[tuple[str, int], pygame.Surface] = {}


def _bild_fuer_klasse(klasse_id: str) -> pygame.Surface:
    dateiname = _DATEI_JE_KLASSE.get(klasse_id, "portrait_01.png")
    if dateiname not in _BILD_CACHE:
        _BILD_CACHE[dateiname] = pygame.image.load(os.path.join(_ORDNER, dateiname)).convert_alpha()
    return _BILD_CACHE[dateiname]


def gerahmt(klasse_id: str, radius: int = 40) -> pygame.Surface:
    """Fertig gerahmtes Kreis-Portrait (Bild + weicher Schatten + Goldring)
    einer Klasse in der gewünschten Größe - passt sich damit optisch den
    übrigen UI-Elementen (Panels, Buttons) an, die denselben Gold-Akzent und
    Schlagschatten-Stil verwenden."""
    schluessel = (klasse_id, radius)
    if schluessel in _GERAHMT_CACHE:
        return _GERAHMT_CACHE[schluessel]

    durchmesser = radius * 2
    bild = _bild_fuer_klasse(klasse_id)
    skaliert = pygame.transform.smoothscale(bild, (durchmesser, durchmesser))

    rand = max(6, radius // 5)
    breite = durchmesser + rand * 2
    gesamt = pygame.Surface((breite, breite), pygame.SRCALPHA)
    mitte = breite // 2

    schatten = pygame.Surface((breite, breite), pygame.SRCALPHA)
    pygame.draw.circle(schatten, (0, 0, 0, 100), (mitte + 2, mitte + 3), radius + 3)
    gesamt.blit(schatten, (0, 0))
    gesamt.blit(skaliert, (rand, rand))
    pygame.draw.circle(gesamt, theme.FARBEN["akzent"], (mitte, mitte), radius + rand // 2, width=max(2, rand // 2))
    pygame.draw.circle(gesamt, theme.FARBEN["akzent_hell"], (mitte, mitte), radius - 1, width=1)

    _GERAHMT_CACHE[schluessel] = gesamt
    return gesamt

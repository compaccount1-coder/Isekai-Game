"""Klassen-Portraits: acht CC0-Portraits (siehe assets/portraits/, verarbeitet
aus "RPG Characters Avatars" von System G6/Qoma), auf die elf Klassen
verteilt - thematisch verwandte Klassen (Magier/Beschwörer, Nekromant/
Assassine, Paladin/Kleriker) teilen sich bewusst ein Portrait, statt für die
drei "fehlenden" Gesichter eigene, stilistisch abweichende Bilder zu
improvisieren (ausprobierte Alternativpakete passten stilistisch nicht zum
fotorealistischen Look dieses Sets). Um trotzdem echte Abwechslung zu
erzeugen - vor allem zwischen mehreren Begleitern derselben Klasse und
zwischen den drei geteilten Klassenpaaren - unterstützt gerahmt() eine
optionale `variante` (z.B. der Name eines Begleiters): sie wählt anhand eines
stabilen Hashs aus ein paar Ringfarben und spiegelt das Bild ggf. horizontal,
sodass niemals zwei unterschiedliche Individuen exakt pixelgleich aussehen.
Fertig gerahmte (Schatten + Ring) Kreis-Portraits werden pro
(Klasse, Radius, Spiegelung, Ringfarbe) einmalig gerendert und danach nur
noch geblittet."""

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

# Die jeweils zweite Klasse jedes geteilten Portrait-Paars wird standardmäßig
# gespiegelt dargestellt - so sind Magier/Beschwörer, Nekromant/Assassine und
# Paladin/Kleriker nie pixelgleich, obwohl sie dasselbe Ausgangsbild nutzen.
_SPIEGELN_JE_KLASSE = {"beschwoerer", "assassine", "kleriker"}

# (Ringfarbe, helle Ringfarbe) - Gold zuerst als Standard/kanonische Farbe
# (Protagonist, Klassenauswahl), die übrigen als kosmetische Variante je
# nach `variante`-Schlüssel (siehe gerahmt()).
_RING_VARIANTEN = [
    (theme.FARBEN["akzent"], theme.FARBEN["akzent_hell"]),
    ((176, 176, 190), (216, 216, 226)),   # Silber
    ((192, 132, 84), (222, 168, 118)),    # Bronze
    ((104, 154, 188), (146, 196, 226)),   # Stahlblau
    ((160, 120, 186), (196, 160, 218)),   # Amethyst
    ((132, 168, 120), (176, 210, 154)),   # Waldgrün
]

_BILD_CACHE: dict[str, pygame.Surface] = {}
_GERAHMT_CACHE: dict[tuple, pygame.Surface] = {}


def _stabiler_wert(text: str) -> int:
    """Deterministisches Hash über die eingebaute hash()-Funktion, deren
    Ergebnis für Strings zwischen zwei Programmläufen absichtlich variiert
    (PYTHONHASHSEED) - für eine rein kosmetische, aber reproduzierbare
    Variante pro Name ungeeignet."""
    wert = 0
    for zeichen in text:
        wert = (wert * 31 + ord(zeichen)) & 0xFFFFFFFF
    return wert


def _bild_fuer_klasse(klasse_id: str, gespiegelt: bool) -> pygame.Surface:
    dateiname = _DATEI_JE_KLASSE.get(klasse_id, "portrait_01.png")
    schluessel = f"{dateiname}:{gespiegelt}"
    if schluessel not in _BILD_CACHE:
        bild = pygame.image.load(os.path.join(_ORDNER, dateiname)).convert_alpha()
        if gespiegelt:
            bild = pygame.transform.flip(bild, True, False)
        _BILD_CACHE[schluessel] = bild
    return _BILD_CACHE[schluessel]


def gerahmt(klasse_id: str, radius: int = 40, variante: str | None = None) -> pygame.Surface:
    """Fertig gerahmtes Kreis-Portrait (Bild + weicher Schatten + Ring) einer
    Klasse in der gewünschten Größe. Ohne `variante` erscheint der
    kanonische Gold-Ring in Originalausrichtung (für den Protagonisten und
    die Klassenauswahl); mit `variante` (z.B. ein Begleiter-Name) wird
    daraus ein stabiler, aber optisch abweichender "Individual-Look"
    (andere Ringfarbe, ggf. gespiegelt) abgeleitet."""
    basis_spiegel = klasse_id in _SPIEGELN_JE_KLASSE
    ring_farbe, ring_hell = _RING_VARIANTEN[0]
    zusatz_spiegel = False
    if variante:
        wert = _stabiler_wert(f"{klasse_id}:{variante}")
        ring_farbe, ring_hell = _RING_VARIANTEN[wert % len(_RING_VARIANTEN)]
        zusatz_spiegel = bool(wert & 0x40)
    gespiegelt = basis_spiegel != zusatz_spiegel  # zweimal gespiegelt = wieder normal

    schluessel = (klasse_id, radius, gespiegelt, ring_farbe)
    if schluessel in _GERAHMT_CACHE:
        return _GERAHMT_CACHE[schluessel]

    durchmesser = radius * 2
    bild = _bild_fuer_klasse(klasse_id, gespiegelt)
    skaliert = pygame.transform.smoothscale(bild, (durchmesser, durchmesser))

    rand = max(6, radius // 5)
    breite = durchmesser + rand * 2
    gesamt = pygame.Surface((breite, breite), pygame.SRCALPHA)
    mitte = breite // 2

    schatten = pygame.Surface((breite, breite), pygame.SRCALPHA)
    pygame.draw.circle(schatten, (0, 0, 0, 100), (mitte + 2, mitte + 3), radius + 3)
    gesamt.blit(schatten, (0, 0))
    gesamt.blit(skaliert, (rand, rand))
    pygame.draw.circle(gesamt, ring_farbe, (mitte, mitte), radius + rand // 2, width=max(2, rand // 2))
    pygame.draw.circle(gesamt, ring_hell, (mitte, mitte), radius - 1, width=1)

    _GERAHMT_CACHE[schluessel] = gesamt
    return gesamt

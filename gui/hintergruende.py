"""Prozedural erzeugte Hintergrund-Szenen je Ort. Es stehen keine echten
Foto-Assets zur Verfügung, daher werden stimmungsvolle Mehrfarb-Verläufe und
geometrische Silhouetten direkt mit Pygame gezeichnet - veredelt durch eine
gemeinsame Nachbearbeitung (Vignette, feines Korn, abgedunkelter unterer
Rand für Textkontrast), die jede Szene wie aus einem Guss wirken lässt statt
wie ein einzelnes flaches Farbverlauf-Rechteck. Jede Szene wird beim ersten
Zugriff einmal gerendert und danach nur noch geblittet."""

import math
import random
import time

import pygame

from gui import theme

_CACHE: dict[str, pygame.Surface] = {}
_VIGNETTE_CACHE: dict[tuple[int, int], pygame.Surface] = {}
_KORN_CACHE: pygame.Surface | None = None
_PARTIKEL_CACHE: dict[str, list[tuple[float, float, float, float]]] = {}
_GLUTPUNKT: pygame.Surface | None = None


def _verlauf(breite: int, hoehe: int, *stops: tuple) -> pygame.Surface:
    """Mehrstufiger vertikaler Verlauf. `stops` sind (Position 0..1, Farbe)-
    Paare, sortiert von oben nach unten - erlaubt reichere Himmel-/
    Lichtstimmungen als ein einfacher Zweifarben-Verlauf."""
    surface = pygame.Surface((breite, hoehe))
    for y in range(hoehe):
        t = y / max(1, hoehe - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1 or i == len(stops) - 2:
                lokal_t = 0 if p1 == p0 else max(0.0, min(1.0, (t - p0) / (p1 - p0)))
                farbe = tuple(int(c0[k] + (c1[k] - c0[k]) * lokal_t) for k in range(3))
                break
        pygame.draw.line(surface, farbe, (0, y), (breite, y))
    return surface


def _glut(surface: pygame.Surface, mitte: tuple, radius: int, farbe: tuple, alpha: int = 60):
    """Weicher, additiver Lichtschein (Kerzen, Fenster, Mondlicht usw.).
    BLEND_RGBA_ADD skaliert Farbwerte NICHT automatisch nach Alpha, sobald
    die Zielfläche kein eigenes Alpha führt (unsere Hintergründe sind
    schlicht RGB) - die gewünschte Intensität wird daher vorab selbst in
    die Farbwerte eingerechnet. Mehrere ineinander gezeichnete Kreise mit
    zur Mitte hin steigender (vorskalierter) Helligkeit ergeben einen
    weichen Verlauf statt einer hart begrenzten, "ausgestanzten" Scheibe."""
    fleck = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    schritte = max(14, min(40, radius // 4))
    for i in range(schritte, 0, -1):
        t = i / schritte
        r = max(1, int(radius * t))
        helligkeit = (1 - t) ** 1.6
        farbwert = tuple(min(255, int(c * (alpha / 255) * helligkeit)) for c in farbe)
        pygame.draw.circle(fleck, (*farbwert, 255), (radius, radius), r)
    surface.blit(fleck, (mitte[0] - radius, mitte[1] - radius), special_flags=pygame.BLEND_RGBA_ADD)


def _sterne(surface: pygame.Surface, breite: int, hoehe_bis: int, anzahl: int, rng: random.Random):
    for _ in range(anzahl):
        x = rng.randint(0, breite)
        y = rng.randint(0, hoehe_bis)
        helligkeit = rng.randint(120, 230)
        groesse = rng.choice([1, 1, 1, 2])
        pygame.draw.circle(surface, (helligkeit, helligkeit, min(255, helligkeit + 25)), (x, y), groesse)


def _bergkette(surface: pygame.Surface, breite: int, hoehe: int, basis_y: int, farbe: tuple, rng: random.Random, zackigkeit=(60, 220)):
    """Eine Silhouetten-Bergkette - mehrfach mit unterschiedlicher Tiefe/
    Farbe aufgerufen ergibt einen atmosphärischen Parallax-Eindruck."""
    punkte = [(0, basis_y + 40)]
    x = -40
    while x < breite + 40:
        x += rng.randint(70, 150)
        punkte.append((x, basis_y - rng.randint(*zackigkeit)))
    punkte.append((breite + 40, basis_y + 40))
    pygame.draw.polygon(surface, farbe, punkte)


def _vignette(breite: int, hoehe: int) -> pygame.Surface:
    """Radiale Abdunkelung zu den Rändern hin - der klassische Kino-/AAA-
    Menü-Effekt, der den Blick zur Bildmitte lenkt und die Ränder beruhigt.
    Aus dünnen, nach außen zunehmend dunkleren Ringen aufgebaut (statt
    gefüllter Kreise), damit sich die Abdunkelung sauber aufaddiert statt
    die Fläche in einem Schritt zu überschreiben. Wird einmal pro Auflösung
    berechnet und für alle Orte wiederverwendet."""
    schluessel = (breite, hoehe)
    if schluessel in _VIGNETTE_CACHE:
        return _VIGNETTE_CACHE[schluessel]
    surface = pygame.Surface((breite, hoehe), pygame.SRCALPHA)
    mitte = (breite // 2, int(hoehe * 0.42))
    max_dist = ((breite / 2) ** 2 + (hoehe / 2) ** 2) ** 0.5
    innerer_radius = max_dist * 0.32
    schritte = 44
    ring_dicke = max(3, int((max_dist - innerer_radius) / schritte) + 2)
    for i in range(schritte):
        t = i / (schritte - 1)
        radius = innerer_radius + (max_dist - innerer_radius) * t
        alpha = int(135 * (t ** 1.7))
        pygame.draw.circle(surface, (0, 0, 0, alpha), mitte, int(radius), width=ring_dicke)
    _VIGNETTE_CACHE[schluessel] = surface
    return surface


def _koernung(breite: int, hoehe: int) -> pygame.Surface:
    """Feines Bild-Korn (Film-Grain) - winzige Helligkeitsschwankungen, die
    einer rein digital-glatten Fläche einen greifbareren, weniger
    "clipart-flachen" Charakter geben. Eine kleine Kachel wird einmal
    erzeugt und über die volle Fläche gekachelt."""
    global _KORN_CACHE
    if _KORN_CACHE is None:
        rng = random.Random(99)
        kachel = pygame.Surface((96, 96), pygame.SRCALPHA)
        for _ in range(90):
            x, y = rng.randint(0, 95), rng.randint(0, 95)
            helligkeit = rng.choice([255, 0, 0, 0])
            alpha = rng.randint(3, 7)
            kachel.set_at((x, y), (helligkeit, helligkeit, helligkeit, alpha))
        _KORN_CACHE = kachel
    surface = pygame.Surface((breite, hoehe), pygame.SRCALPHA)
    for y in range(0, hoehe, 96):
        for x in range(0, breite, 96):
            surface.blit(_KORN_CACHE, (x, y))
    return surface


def _nachbearbeitung(surface: pygame.Surface) -> pygame.Surface:
    breite, hoehe = surface.get_size()
    surface.blit(_koernung(breite, hoehe), (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    # Unterer Bildbereich abdunkeln - dort sitzen später fast immer Panels/
    # Buttons, ein ruhigerer, dunklerer Grund verbessert deren Lesbarkeit
    # unabhängig davon, wie hell die jeweilige Szene sonst ist.
    scrim = pygame.Surface((breite, hoehe), pygame.SRCALPHA)
    scrim_start = int(hoehe * 0.55)
    for y in range(scrim_start, hoehe):
        t = (y - scrim_start) / max(1, hoehe - scrim_start)
        pygame.draw.line(scrim, (0, 0, 0, int(150 * t)), (0, y), (breite, y))
    surface.blit(scrim, (0, 0))
    surface.blit(_vignette(breite, hoehe), (0, 0))
    return surface


def _titel(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (0.0, (8, 7, 18)), (0.55, (22, 14, 34)), (1.0, (34, 20, 30)))
    rng = random.Random(7)
    _sterne(surface, breite, int(hoehe * 0.75), 160, rng)
    _glut(surface, (int(breite * 0.5), int(hoehe * 0.24)), 220, (200, 170, 255), alpha=22)
    _glut(surface, (int(breite * 0.5), int(hoehe * 0.24)), 90, (230, 210, 255), alpha=30)
    _bergkette(surface, breite, hoehe, int(hoehe * 0.82), (16, 11, 22), rng, zackigkeit=(40, 140))
    _bergkette(surface, breite, hoehe, int(hoehe * 0.88), (6, 4, 10), rng, zackigkeit=(80, 240))
    return surface


def _hub(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (0.0, (18, 20, 34)), (0.6, (36, 32, 46)), (1.0, (46, 36, 40)))
    rng = random.Random(11)
    _sterne(surface, breite, int(hoehe * 0.5), 90, rng)
    boden = pygame.Rect(0, int(hoehe * 0.86), breite, int(hoehe * 0.14))
    pygame.draw.rect(surface, (24, 22, 20), boden)
    pygame.draw.rect(surface, (44, 36, 30), (0, boden.y, breite, 3))
    # Stadt-Silhouette am Horizont, mit warmen Fensterlichtern
    x = 0
    while x < breite:
        b = rng.randint(40, 100)
        h = rng.randint(60, 200)
        farbe = (30 + rng.randint(-6, 6), 26, 34)
        pygame.draw.rect(surface, farbe, (x, boden.y - h, b, h + 10))
        if rng.random() < 0.5:
            _glut(surface, (x + b // 2, boden.y - h + 12), 10, (255, 200, 120), alpha=70)
        x += b + rng.randint(4, 20)
    return surface


def _taverne(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (0.0, (52, 30, 18)), (0.5, (44, 24, 15)), (1.0, (16, 9, 7)))
    rng = random.Random(2)
    for _ in range(7):
        x = rng.randint(80, breite - 80)
        y = rng.randint(int(hoehe * 0.2), int(hoehe * 0.55))
        _glut(surface, (x, y), rng.randint(70, 140), (255, 175, 90), alpha=30)
    balken_y = int(hoehe * 0.12)
    pygame.draw.rect(surface, (30, 17, 10), (0, balken_y, breite, 14))
    tresen = pygame.Rect(0, int(hoehe * 0.82), breite, int(hoehe * 0.18))
    pygame.draw.rect(surface, (40, 24, 15), tresen)
    pygame.draw.rect(surface, (70, 46, 26), (0, tresen.y, breite, 6))
    pygame.draw.rect(surface, (26, 15, 9), (0, tresen.y + 6, breite, 4))
    for x in range(60, breite, 220):
        pygame.draw.ellipse(surface, (48, 30, 18), (x, tresen.y - 46, 52, 50))
        pygame.draw.ellipse(surface, (66, 42, 24), (x, tresen.y - 46, 52, 50), width=3)
    return surface


def _marktplatz(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (0.0, (150, 118, 62)), (0.5, (110, 88, 48)), (1.0, (48, 38, 24)))
    boden = pygame.Rect(0, int(hoehe * 0.78), breite, int(hoehe * 0.22))
    pygame.draw.rect(surface, (74, 60, 38), boden)
    pygame.draw.rect(surface, (94, 78, 48), (0, boden.y, breite, 4))
    rng = random.Random(3)
    x = 20
    stoff_farben = [(150, 40, 40), (40, 90, 130), (170, 150, 60), (60, 110, 70)]
    while x < breite - 60:
        b = rng.randint(120, 190)
        farbe = rng.choice(stoff_farben)
        spitze = (x + b // 2, boden.y - 130)
        pygame.draw.polygon(surface, farbe, [(x, boden.y), (x + b, boden.y), spitze])
        pygame.draw.polygon(surface, tuple(max(0, c - 30) for c in farbe), [(x, boden.y), (x + b // 2, boden.y), spitze])
        pygame.draw.line(surface, tuple(min(255, c + 50) for c in farbe), (x, boden.y), spitze, 2)
        pygame.draw.rect(surface, (30, 24, 16), (x + b // 2 - 4, boden.y - 40, 8, 40))
        x += b + rng.randint(30, 60)
    return surface


def _gildenviertel(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (0.0, (52, 52, 66)), (0.6, (40, 40, 52)), (1.0, (20, 20, 28)))
    boden = pygame.Rect(0, int(hoehe * 0.82), breite, int(hoehe * 0.18))
    pygame.draw.rect(surface, (36, 36, 44), boden)
    for x in range(60, breite, 160):
        pygame.draw.rect(surface, (78, 78, 90), (x, int(hoehe * 0.2), 40, boden.y - int(hoehe * 0.2)))
        pygame.draw.rect(surface, (100, 100, 116), (x, int(hoehe * 0.2), 40, 14))
        pygame.draw.rect(surface, (100, 100, 116), (x, boden.y - 14, 40, 14))
        pygame.draw.line(surface, (118, 118, 132), (x + 4, int(hoehe * 0.2) + 14), (x + 4, boden.y - 14), 2)
    _glut(surface, (breite // 2, int(hoehe * 0.15)), 220, (150, 140, 210), alpha=22)
    return surface


def _wildnis(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (0.0, (70, 120, 96)), (0.5, (40, 82, 62)), (1.0, (14, 32, 20)))
    _glut(surface, (int(breite * 0.78), int(hoehe * 0.2)), 100, (255, 240, 200), alpha=55)
    boden = pygame.Rect(0, int(hoehe * 0.8), breite, int(hoehe * 0.2))
    pygame.draw.rect(surface, (22, 40, 24), boden)
    rng = random.Random(4)
    for schicht, basis_y, skala, dunkel, alpha in ((0, boden.y + 10, 1.5, 44, 255), (1, boden.y - 10, 1.05, 20, 255), (2, boden.y - 60, 0.8, 4, 130)):
        x = -20
        while x < breite + 20:
            hoehe_baum = int(rng.randint(90, 170) * skala)
            breite_baum = int(rng.randint(50, 90) * skala)
            gruen = (20 + dunkel // 2, 60 + dunkel, 30)
            baum = pygame.Surface((breite_baum, hoehe_baum), pygame.SRCALPHA)
            pygame.draw.polygon(baum, (*gruen, alpha), [(0, hoehe_baum), (breite_baum, hoehe_baum), (breite_baum // 2, 0)])
            surface.blit(baum, (x, basis_y - hoehe_baum))
            x += breite_baum + rng.randint(10, 40)
    return surface


def _tempelbezirk(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (0.0, (210, 218, 232)), (0.5, (160, 172, 196)), (1.0, (90, 106, 138)))
    _glut(surface, (breite // 2, int(hoehe * 0.2)), 260, (255, 255, 240), alpha=70)
    _glut(surface, (breite // 2, int(hoehe * 0.2)), 100, (255, 255, 250), alpha=60)
    boden = pygame.Rect(0, int(hoehe * 0.82), breite, int(hoehe * 0.18))
    pygame.draw.rect(surface, (150, 150, 165), boden)
    pygame.draw.rect(surface, (180, 180, 196), (0, boden.y, breite, 4))
    for x in range(50, breite, 150):
        pygame.draw.rect(surface, (225, 225, 235), (x, int(hoehe * 0.3), 32, boden.y - int(hoehe * 0.3)))
        pygame.draw.rect(surface, (200, 200, 215), (x, int(hoehe * 0.3), 32, boden.y - int(hoehe * 0.3)), width=2)
        pygame.draw.rect(surface, (240, 240, 250), (x - 6, int(hoehe * 0.28), 44, 10))
    return surface


def _adelsviertel(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (0.0, (78, 44, 96)), (0.55, (52, 30, 68)), (1.0, (22, 13, 32)))
    boden = pygame.Rect(0, int(hoehe * 0.82), breite, int(hoehe * 0.18))
    pygame.draw.rect(surface, (40, 24, 50), boden)
    pygame.draw.rect(surface, (60, 38, 74), (0, boden.y, breite, 4))
    for x in range(70, breite, 180):
        pygame.draw.polygon(surface, (110, 80, 140), [
            (x, boden.y), (x, int(hoehe * 0.28)), (x + 30, int(hoehe * 0.18)), (x + 60, int(hoehe * 0.28)), (x + 60, boden.y),
        ])
        pygame.draw.line(surface, (150, 118, 180), (x, int(hoehe * 0.28)), (x + 30, int(hoehe * 0.18)), 2)
        pygame.draw.line(surface, (150, 118, 180), (x + 30, int(hoehe * 0.18)), (x + 60, int(hoehe * 0.28)), 2)
        _glut(surface, (x + 30, int(hoehe * 0.28) - 6), 16, (255, 210, 120), alpha=90)
    return surface


def _uebungsplatz(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (0.0, (170, 148, 100)), (0.5, (128, 108, 70)), (1.0, (58, 48, 32)))
    boden = pygame.Rect(0, int(hoehe * 0.8), breite, int(hoehe * 0.2))
    pygame.draw.rect(surface, (100, 80, 50), boden)
    pygame.draw.rect(surface, (124, 100, 64), (0, boden.y, breite, 4))
    rng = random.Random(5)
    for x in range(80, breite, 220):
        pygame.draw.rect(surface, (70, 50, 30), (x - 4, boden.y - 70, 8, 70))
        pygame.draw.circle(surface, (200, 190, 170), (x, boden.y - 90), 24)
        pygame.draw.circle(surface, (150, 60, 60), (x, boden.y - 90), 8)
        pygame.draw.circle(surface, (220, 212, 196), (x, boden.y - 90), 24, width=2)
    return surface


_BUILDER = {
    "titel": _titel,
    "hub": _hub,
    "taverne": _taverne,
    "marktplatz": _marktplatz,
    "gildenviertel": _gildenviertel,
    "wildnis": _wildnis,
    "tempelbezirk": _tempelbezirk,
    "adelsviertel": _adelsviertel,
    "uebungsplatz": _uebungsplatz,
}


def hintergrund_fuer(ort_id: str | None) -> pygame.Surface:
    schluessel = ort_id or "hub"
    if schluessel not in _CACHE:
        builder = _BUILDER.get(schluessel, _hub)
        surface = builder(theme.BREITE, theme.HOEHE)
        _CACHE[schluessel] = _nachbearbeitung(surface)
    return _CACHE[schluessel]


# ---------------------------------------------------------------------------
# Leichte Ambient-Animation: der statische, einmalig gerenderte Hintergrund
# bekommt darüber ein paar sacht treibende, pulsierende Lichtpunkte - macht
# selbst ruhige Menüszenen spürbar "lebendig" statt komplett bewegungslos,
# ohne dass die (teure) Hintergrundgrafik selbst pro Frame neu gezeichnet
# werden müsste.
# ---------------------------------------------------------------------------

_PARTIKEL_ANZAHL = 12
_TREIBSTRECKE = 160  # Pixel, die ein Punkt zurücklegt, bevor er von vorn beginnt


def _glutpunkt() -> pygame.Surface:
    global _GLUTPUNKT
    if _GLUTPUNKT is None:
        groesse = 10
        s = pygame.Surface((groesse, groesse), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 236, 200, 255), (groesse // 2, groesse // 2), groesse // 2)
        _GLUTPUNKT = s
    return _GLUTPUNKT


def _partikel_basis(schluessel: str) -> list[tuple[float, float, float, float]]:
    """(x, y_start, geschwindigkeit, phase) je Partikel - pro Ort fest, damit
    nur die verstrichene Zeit die Bewegung antreibt und sie bei jedem
    Bildaufbau gleich aussieht."""
    if schluessel not in _PARTIKEL_CACHE:
        rng = random.Random(abs(hash(schluessel)) % (2**32))
        _PARTIKEL_CACHE[schluessel] = [
            (
                rng.uniform(60, theme.BREITE - 60),
                rng.uniform(0, _TREIBSTRECKE),
                rng.uniform(7, 16),
                rng.uniform(0, 6.283),
            )
            for _ in range(_PARTIKEL_ANZAHL)
        ]
    return _PARTIKEL_CACHE[schluessel]


def zeichnen(surface: pygame.Surface, ort_id: str | None):
    """Zeichnet den (gecachten) Hintergrund plus die animierte Funkel-Schicht
    obendrauf - der übliche Aufruf anstelle des reinen
    `surface.blit(hintergrund_fuer(ort_id), (0, 0))`."""
    surface.blit(hintergrund_fuer(ort_id), (0, 0))
    schluessel = ort_id or "hub"
    t = time.perf_counter()
    punkt = _glutpunkt()
    unten = int(theme.HOEHE * 0.62)  # Partikel bleiben im oberen/mittleren Bildbereich, nicht hinter Panels
    for x, y_start, geschwindigkeit, phase in _partikel_basis(schluessel):
        y = unten - ((t * geschwindigkeit * 6 + y_start) % _TREIBSTRECKE)
        helligkeit = 0.5 + 0.5 * math.sin(t * 0.9 + phase)
        alpha = int(20 + 55 * helligkeit)
        punkt.set_alpha(alpha)
        surface.blit(punkt, (int(x) - punkt.get_width() // 2, int(y) - punkt.get_height() // 2))

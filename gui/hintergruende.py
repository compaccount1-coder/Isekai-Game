"""Prozedural erzeugte Hintergrund-Szenen je Ort. Es stehen keine echten
Grafik-Assets zur Verfügung, daher werden stimmungsvolle Farbverläufe und
einfache geometrische Silhouetten direkt mit Pygame gezeichnet - jede Szene
wird beim ersten Zugriff einmal gerendert und danach nur noch geblittet."""

import random

import pygame

from gui import theme

_CACHE: dict[str, pygame.Surface] = {}


def _verlauf(breite: int, hoehe: int, oben: tuple, unten: tuple) -> pygame.Surface:
    surface = pygame.Surface((breite, hoehe))
    for y in range(hoehe):
        t = y / max(1, hoehe - 1)
        farbe = tuple(int(oben[i] + (unten[i] - oben[i]) * t) for i in range(3))
        pygame.draw.line(surface, farbe, (0, y), (breite, y))
    return surface


def _glut(surface: pygame.Surface, mitte: tuple, radius: int, farbe: tuple, alpha: int = 60):
    fleck = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(fleck, (*farbe, alpha), (radius, radius), radius)
    surface.blit(fleck, (mitte[0] - radius, mitte[1] - radius), special_flags=pygame.BLEND_RGBA_ADD)


def _sterne(surface: pygame.Surface, breite: int, hoehe_bis: int, anzahl: int, rng: random.Random):
    for _ in range(anzahl):
        x = rng.randint(0, breite)
        y = rng.randint(0, hoehe_bis)
        helligkeit = rng.randint(120, 230)
        groesse = rng.choice([1, 1, 1, 2])
        pygame.draw.circle(surface, (helligkeit, helligkeit, min(255, helligkeit + 25)), (x, y), groesse)


def _titel(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (10, 8, 22), (28, 16, 36))
    rng = random.Random(7)
    _sterne(surface, breite, int(hoehe * 0.75), 140, rng)
    _glut(surface, (int(breite * 0.5), int(hoehe * 0.28)), 160, (200, 170, 255), alpha=25)
    # Ferne Bergsilhouette
    punkte = [(0, hoehe)]
    x = 0
    while x < breite:
        x += rng.randint(80, 160)
        punkte.append((x, hoehe - rng.randint(60, 220)))
    punkte.append((breite, hoehe))
    pygame.draw.polygon(surface, (16, 12, 26), punkte)
    return surface


def _hub(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (16, 18, 30), (40, 34, 46))
    rng = random.Random(11)
    _sterne(surface, breite, int(hoehe * 0.5), 80, rng)
    boden = pygame.Rect(0, int(hoehe * 0.86), breite, int(hoehe * 0.14))
    pygame.draw.rect(surface, (24, 22, 20), boden)
    # Stadt-Silhouette am Horizont
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
    surface = _verlauf(breite, hoehe, (58, 34, 20), (20, 11, 8))
    rng = random.Random(2)
    for _ in range(6):
        x = rng.randint(80, breite - 80)
        y = rng.randint(int(hoehe * 0.25), int(hoehe * 0.6))
        _glut(surface, (x, y), rng.randint(70, 130), (255, 175, 90), alpha=32)
    tresen = pygame.Rect(0, int(hoehe * 0.82), breite, int(hoehe * 0.18))
    pygame.draw.rect(surface, (40, 24, 15), tresen)
    pygame.draw.rect(surface, (66, 42, 24), (0, tresen.y, breite, 6))
    # Fässer als grobe Silhouetten
    for x in range(60, breite, 220):
        pygame.draw.ellipse(surface, (48, 30, 18), (x, tresen.y - 46, 52, 50))
    return surface


def _marktplatz(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (120, 96, 52), (58, 46, 28))
    boden = pygame.Rect(0, int(hoehe * 0.78), breite, int(hoehe * 0.22))
    pygame.draw.rect(surface, (74, 60, 38), boden)
    rng = random.Random(3)
    x = 20
    stoff_farben = [(150, 40, 40), (40, 90, 130), (170, 150, 60), (60, 110, 70)]
    while x < breite - 60:
        b = rng.randint(120, 190)
        farbe = rng.choice(stoff_farben)
        spitze = (x + b // 2, boden.y - 130)
        pygame.draw.polygon(surface, farbe, [(x, boden.y), (x + b, boden.y), spitze])
        pygame.draw.polygon(surface, tuple(max(0, c - 30) for c in farbe), [(x, boden.y), (x + b // 2, boden.y), spitze])
        pygame.draw.rect(surface, (30, 24, 16), (x + b // 2 - 4, boden.y - 40, 8, 40))
        x += b + rng.randint(30, 60)
    return surface


def _gildenviertel(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (58, 58, 70), (26, 26, 34))
    boden = pygame.Rect(0, int(hoehe * 0.82), breite, int(hoehe * 0.18))
    pygame.draw.rect(surface, (36, 36, 44), boden)
    saeulen_x = range(60, breite, 160)
    for x in saeulen_x:
        pygame.draw.rect(surface, (78, 78, 90), (x, int(hoehe * 0.2), 40, boden.y - int(hoehe * 0.2)))
        pygame.draw.rect(surface, (94, 94, 108), (x, int(hoehe * 0.2), 40, 14))
        pygame.draw.rect(surface, (94, 94, 108), (x, boden.y - 14, 40, 14))
    _glut(surface, (breite // 2, int(hoehe * 0.15)), 200, (140, 130, 200), alpha=18)
    return surface


def _wildnis(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (60, 110, 90), (18, 40, 26))
    _glut(surface, (int(breite * 0.78), int(hoehe * 0.2)), 90, (255, 240, 200), alpha=55)
    boden = pygame.Rect(0, int(hoehe * 0.8), breite, int(hoehe * 0.2))
    pygame.draw.rect(surface, (24, 42, 24), boden)
    rng = random.Random(4)
    for schicht, basis_y, skala, dunkel in ((0, boden.y + 10, 1.4, 40), (1, boden.y - 10, 1.0, 20)):
        x = -20
        while x < breite + 20:
            hoehe_baum = int(rng.randint(90, 170) * skala)
            breite_baum = int(rng.randint(50, 90) * skala)
            gruen = (20 + dunkel // 2, 60 + dunkel, 30)
            pygame.draw.polygon(surface, gruen, [
                (x, basis_y), (x + breite_baum, basis_y), (x + breite_baum // 2, basis_y - hoehe_baum),
            ])
            x += breite_baum + rng.randint(10, 40)
    return surface


def _tempelbezirk(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (200, 210, 225), (110, 130, 160))
    _glut(surface, (breite // 2, int(hoehe * 0.22)), 220, (255, 255, 240), alpha=70)
    boden = pygame.Rect(0, int(hoehe * 0.82), breite, int(hoehe * 0.18))
    pygame.draw.rect(surface, (150, 150, 165), boden)
    for x in range(50, breite, 150):
        pygame.draw.rect(surface, (225, 225, 235), (x, int(hoehe * 0.3), 32, boden.y - int(hoehe * 0.3)))
    return surface


def _adelsviertel(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (70, 40, 90), (28, 16, 40))
    boden = pygame.Rect(0, int(hoehe * 0.82), breite, int(hoehe * 0.18))
    pygame.draw.rect(surface, (40, 24, 50), boden)
    for x in range(70, breite, 180):
        pygame.draw.polygon(surface, (110, 80, 140), [
            (x, boden.y), (x, int(hoehe * 0.28)), (x + 30, int(hoehe * 0.18)), (x + 60, int(hoehe * 0.28)), (x + 60, boden.y),
        ])
        pygame.draw.circle(surface, (255, 210, 120), (x + 30, int(hoehe * 0.28) - 6), 6)
    return surface


def _uebungsplatz(breite: int, hoehe: int) -> pygame.Surface:
    surface = _verlauf(breite, hoehe, (150, 130, 90), (70, 58, 38))
    boden = pygame.Rect(0, int(hoehe * 0.8), breite, int(hoehe * 0.2))
    pygame.draw.rect(surface, (100, 80, 50), boden)
    rng = random.Random(5)
    for x in range(80, breite, 220):
        pygame.draw.rect(surface, (70, 50, 30), (x - 4, boden.y - 70, 8, 70))
        pygame.draw.circle(surface, (200, 190, 170), (x, boden.y - 90), 24)
        pygame.draw.circle(surface, (150, 60, 60), (x, boden.y - 90), 8)
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
        _CACHE[schluessel] = builder(theme.BREITE, theme.HOEHE)
    return _CACHE[schluessel]

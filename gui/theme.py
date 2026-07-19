"""Farben, Schriftarten und Layout-Konstanten für die grafische Oberfläche."""

import pygame

BREITE, HOEHE = 1280, 800

FARBEN = {
    "hintergrund": (18, 16, 24),
    "panel": (30, 26, 38),
    "panel_rand": (94, 80, 112),
    "text": (235, 230, 240),
    "text_dim": (168, 158, 182),
    "akzent": (198, 156, 76),
    "gefahr": (206, 74, 74),
    "erfolg": (108, 176, 96),
    "hp_voll": (176, 48, 58),
    "hp_leer": (54, 22, 26),
    "mp_voll": (64, 112, 198),
    "mp_leer": (24, 36, 60),
    "button": (52, 44, 64),
    "button_hover": (78, 62, 96),
    "button_deaktiviert": (36, 34, 40),
    "button_rand": (140, 116, 88),
}

ORT_FARBEN = {
    "taverne": (66, 42, 26),
    "marktplatz": (90, 76, 38),
    "gildenviertel": (46, 46, 56),
    "wildnis": (26, 54, 32),
    "tempelbezirk": (40, 52, 66),
    "adelsviertel": (54, 32, 62),
    "uebungsplatz": (56, 40, 28),
    "titel": (14, 12, 20),
}

_FONT_CACHE: dict[tuple[int, bool], "pygame.font.Font"] = {}


def font(groesse: int, fett: bool = False) -> "pygame.font.Font":
    schluessel = (groesse, fett)
    if schluessel not in _FONT_CACHE:
        _FONT_CACHE[schluessel] = pygame.font.SysFont("georgia,garamond,timesnewroman,serif", groesse, bold=fett)
    return _FONT_CACHE[schluessel]

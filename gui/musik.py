"""Hintergrundmusik: zwei Stimmungen (Erkundung/Kampf), die automatisch je
nach aktueller Szene gewechselt werden (siehe die musik.spiele()-Aufrufe in
scenes.py), plus Lautstärkeregelung aus den Einstellungen. Fehlt ein
Audiogerät (z.B. in Tests/CI), bleibt das Spiel trotzdem lauffähig - init()
und spiele() scheitern dann still statt abzustürzen."""

import os

import pygame

_ORDNER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "musik")
_TRACKS = {
    "erkundung": os.path.join(_ORDNER, "erkundung.mp3"),
    "kampf": os.path.join(_ORDNER, "kampf.mp3"),
}

_aktuell: str | None = None
_lautstaerke = 0.5
_bereit = False


def init():
    global _bereit
    if _bereit:
        return
    try:
        pygame.mixer.init()
        _bereit = True
    except pygame.error:
        _bereit = False


def lautstaerke_setzen(wert: float):
    global _lautstaerke
    _lautstaerke = max(0.0, min(1.0, wert))
    if _bereit:
        pygame.mixer.music.set_volume(_lautstaerke)


def spiele(stimmung: str):
    """Wechselt zur gewünschten Stimmung, falls sie nicht schon läuft - jede
    Spiel-Szene ruft das bei ihrer Erstellung auf, ohne wissen zu müssen, ob
    bereits dieselbe Musik läuft (kein hörbarer Neustart bei jedem
    Szenenwechsel innerhalb derselben Stimmung)."""
    global _aktuell
    if not _bereit or stimmung == _aktuell or stimmung not in _TRACKS:
        return
    try:
        pygame.mixer.music.load(_TRACKS[stimmung])
        pygame.mixer.music.set_volume(_lautstaerke)
        pygame.mixer.music.play(loops=-1, fade_ms=900)
        _aktuell = stimmung
    except pygame.error:
        pass

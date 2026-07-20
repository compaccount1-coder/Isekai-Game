"""Hintergrundmusik: zwei Stimmungen (Erkundung/Kampf), je mit einer kleinen
Playlist statt eines einzelnen Endlos-Loops, damit man innerhalb derselben
Stimmung nicht immer denselben Titel hört. Die Szenen wechseln nur die
Stimmung (siehe musik.spiele() in scenes.py); welcher Titel daraus läuft und
wann zum nächsten gewechselt wird, regelt dieses Modul selbst über
aktualisieren(), das die App-Hauptschleife einmal pro Frame aufruft. Fehlt
ein Audiogerät (z.B. in Tests/CI), bleibt das Spiel trotzdem lauffähig -
init() und spiele() scheitern dann still statt abzustürzen."""

import os
import random

import pygame

_ORDNER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "musik")

_PLAYLISTS: dict[str, list[str]] = {
    "erkundung": [
        os.path.join(_ORDNER, "erkundung.mp3"),
        os.path.join(_ORDNER, "erkundung_wald.mp3"),
        os.path.join(_ORDNER, "erkundung_felder.mp3"),
        os.path.join(_ORDNER, "erkundung_taverne.mp3"),
    ],
    "kampf": [
        os.path.join(_ORDNER, "kampf.mp3"),
        os.path.join(_ORDNER, "kampf_konfrontation.mp3"),
        os.path.join(_ORDNER, "kampf_endgegner.mp3"),
    ],
}

_aktuelle_stimmung: str | None = None
_warteschlange: list[str] = []
_letzter_titel: str | None = None
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
    """Wechselt zur gewünschten Stimmung, falls sie nicht schon aktiv ist,
    und startet sofort einen zufälligen Titel aus deren Playlist. Jede
    Spiel-Szene ruft das bei ihrer Erstellung auf, ohne wissen zu müssen, ob
    bereits dieselbe Stimmung läuft (kein hörbarer Neustart bei jedem
    Szenenwechsel innerhalb derselben Stimmung)."""
    global _aktuelle_stimmung, _warteschlange
    if not _bereit or stimmung == _aktuelle_stimmung or stimmung not in _PLAYLISTS:
        return
    _aktuelle_stimmung = stimmung
    _warteschlange = []
    _naechsten_titel_spielen(fade_ms=900)


def _neue_warteschlange() -> list[str]:
    """Eine neu gemischte Runde durch die komplette Playlist - mit einer
    kleinen Korrektur, damit der zuletzt gespielte Titel nicht durch puren
    Zufall gleich nochmal an erster Stelle landet."""
    titel = list(_PLAYLISTS[_aktuelle_stimmung])
    random.shuffle(titel)
    if len(titel) > 1 and titel[0] == _letzter_titel:
        titel[0], titel[1] = titel[1], titel[0]
    return titel


def _naechsten_titel_spielen(fade_ms: int = 700):
    global _warteschlange, _letzter_titel
    if not _bereit or _aktuelle_stimmung is None:
        return
    if not _warteschlange:
        _warteschlange = _neue_warteschlange()
    titel = _warteschlange.pop(0)
    try:
        pygame.mixer.music.load(titel)
        pygame.mixer.music.set_volume(_lautstaerke)
        pygame.mixer.music.play(loops=0, fade_ms=fade_ms)
        _letzter_titel = titel
    except pygame.error:
        pass


def aktualisieren():
    """Einmal pro Frame aus der App-Hauptschleife aufgerufen: erkennt das
    Ende des aktuellen Titels (pygame löst dafür kein Event ohne Weiteres
    aus, daher die einfache Busy-Prüfung) und startet automatisch den
    nächsten Titel derselben Stimmung."""
    if not _bereit or _aktuelle_stimmung is None:
        return
    if not pygame.mixer.music.get_busy():
        _naechsten_titel_spielen()

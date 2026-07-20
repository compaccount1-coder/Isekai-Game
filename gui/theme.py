"""Farben, Schriftarten und Layout-Konstanten für die grafische Oberfläche."""

from pathlib import Path

import pygame

BREITE, HOEHE = 1280, 800

# Gedeckte, warme Fantasy-Palette: tiefes Nachtblau-Violett als Basis, Gold als
# durchgängiger Akzent (spiegelt sich auch in den UI-Ornamenten, siehe
# assets/ui/), gedämpfte Rot-/Grün-/Blautöne für Gefahr/Erfolg/Magie statt
# grellem Primärfarben-Kontrast.
FARBEN = {
    "hintergrund": (14, 12, 20),
    "panel": (32, 27, 42),
    "panel_oben": (40, 34, 52),
    "panel_unten": (26, 22, 35),
    "panel_rand": (120, 98, 60),
    "text": (237, 228, 210),
    "text_dim": (168, 156, 148),
    "akzent": (208, 172, 104),
    "akzent_hell": (232, 200, 138),
    "akzent_dunkel": (156, 122, 66),
    "gefahr": (196, 74, 68),
    "erfolg": (120, 176, 108),
    "hp_voll": (176, 54, 60),
    "hp_leer": (46, 20, 24),
    "mp_voll": (72, 118, 196),
    "mp_leer": (22, 32, 54),
    "button_oben": (66, 56, 80),
    "button_unten": (46, 39, 58),
    "button_hover_oben": (92, 76, 106),
    "button_hover_unten": (64, 52, 78),
    "button_deaktiviert_oben": (40, 38, 44),
    "button_deaktiviert_unten": (30, 28, 34),
    "button_rand": (150, 122, 74),
    "button_rand_dim": (74, 68, 66),
    "schatten": (0, 0, 0),
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

_ASSETS = Path(__file__).resolve().parent.parent / "assets"
_SCHRIFT_KOERPER = str(_ASSETS / "fonts" / "EBGaramond.ttf")
_SCHRIFT_TITEL = str(_ASSETS / "fonts" / "Cinzel.ttf")
_SCHRIFT_TITEL_DEKORATIV = str(_ASSETS / "fonts" / "CinzelDecorative-Bold.ttf")
_EMOJI_FALLBACK_NAMEN = "segoeuisymbol,seguisym,applecoloremoji,notosanssymbols,arial"

_FONT_CACHE: dict[tuple[str, int, bool], "_MischFont"] = {}


class _MischFont:
    """Kombiniert eine der handverlesenen Schriftarten (Cinzel/EB Garamond -
    reine Text-Schriften ohne jede Symbol-/Emoji-Abdeckung) mit einer
    System-Schrift als Fallback für die Icons, die im gesamten Spiel als
    Emoji direkt im Text stehen (⚔️💀🏆📦 usw.). Bietet dieselbe
    Render-Schnittstelle wie pygame.font.Font (render/size/get_linesize/
    get_height), damit keiner der zahlreichen bestehenden Aufrufe im
    Projekt angepasst werden musste - nur theme.font()/font_titel() selbst
    wurden geändert."""

    def __init__(self, primaer: "pygame.font.Font"):
        self._primaer = primaer
        self._fallback = pygame.font.SysFont(_EMOJI_FALLBACK_NAMEN, primaer.get_height())
        self._unbekannt_referenz = self._roh_bytes(primaer, chr(0xE000))
        self._unterstuetzt_cache: dict[str, bool] = {}

    @staticmethod
    def _sicher_render(font_obj, text, antialias=True, farbe=(255, 255, 255)):
        """Manche Codepunkte (z.B. Variationsselektoren wie U+FE0F, die in
        zusammengesetzten Emoji wie "⚔️" stecken) haben in JEDER Schriftart
        die Breite 0 - pygame.font.render() wirft dafür einen Fehler statt
        eine leere Fläche zurückzugeben. Wird hier abgefangen, statt die
        ganze Anzeige abstürzen zu lassen."""
        try:
            return font_obj.render(text, antialias, farbe)
        except pygame.error:
            return pygame.Surface((0, font_obj.get_height()), pygame.SRCALPHA)

    @classmethod
    def _roh_bytes(cls, font_obj, ch):
        bild = cls._sicher_render(font_obj, ch)
        return bild.get_size(), pygame.image.tostring(bild, "RGBA")

    def _primaer_kann(self, ch: str) -> bool:
        if ch not in self._unterstuetzt_cache:
            self._unterstuetzt_cache[ch] = ch.isspace() or self._roh_bytes(self._primaer, ch) != self._unbekannt_referenz
        return self._unterstuetzt_cache[ch]

    def _segmente(self, text: str) -> list[tuple[str, bool]]:
        segmente = []
        aktuell, aktuell_ok = "", None
        for ch in text:
            ok = self._primaer_kann(ch)
            if aktuell_ok is None:
                aktuell_ok = ok
            if ok != aktuell_ok:
                segmente.append((aktuell, aktuell_ok))
                aktuell, aktuell_ok = "", ok
            aktuell += ch
        if aktuell:
            segmente.append((aktuell, aktuell_ok))
        return segmente or [("", True)]

    def render(self, text: str, antialias: bool, farbe) -> "pygame.Surface":
        if not text:
            return pygame.Surface((1, self._primaer.get_height()), pygame.SRCALPHA)
        segmente = self._segmente(text)
        if len(segmente) == 1 and segmente[0][1]:
            return self._sicher_render(self._primaer, text, antialias, farbe)
        teile = [self._sicher_render(self._primaer if ok else self._fallback, t, antialias, farbe) for t, ok in segmente]
        breite = sum(t.get_width() for t in teile)
        hoehe = max((t.get_height() for t in teile), default=self._primaer.get_height())
        ergebnis = pygame.Surface((max(1, breite), hoehe), pygame.SRCALPHA)
        x = 0
        for t in teile:
            ergebnis.blit(t, (x, (hoehe - t.get_height()) // 2))
            x += t.get_width()
        return ergebnis

    def size(self, text: str) -> tuple[int, int]:
        segmente = self._segmente(text)
        breite, hoehe = 0, self._primaer.get_height()
        for t, ok in segmente:
            font_obj = self._primaer if ok else self._fallback
            try:
                b, h = font_obj.size(t)
            except pygame.error:
                b, h = 0, font_obj.get_height()
            breite += b
            hoehe = max(hoehe, h)
        return (breite, hoehe)

    def get_linesize(self) -> int:
        return self._primaer.get_linesize()

    def get_height(self) -> int:
        return self._primaer.get_height()


def font(groesse: int, fett: bool = False) -> "_MischFont":
    """Fließtext-Schrift (EB Garamond) - für Fallschirme, Beschreibungen,
    Log-Text usw. Bleibt bewusst unter demselben Namen wie zuvor, damit
    jeder bestehende Aufruf im Projekt ohne Änderung von der neuen,
    handgesetzten Schriftart statt der System-Schriftart profitiert."""
    schluessel = ("koerper", groesse, fett)
    if schluessel not in _FONT_CACHE:
        f = pygame.font.Font(_SCHRIFT_KOERPER, groesse)
        f.set_bold(fett)
        _FONT_CACHE[schluessel] = _MischFont(f)
    return _FONT_CACHE[schluessel]


def font_titel(groesse: int, fett: bool = True) -> "_MischFont":
    """Auszeichnungsschrift (Cinzel) für Überschriften, Orts- und
    Situationstitel - dort, wo bewusst ein "gemeißelter", herrschaftlicher
    Eindruck statt Fließtext gewünscht ist."""
    schluessel = ("titel", groesse, fett)
    if schluessel not in _FONT_CACHE:
        f = pygame.font.Font(_SCHRIFT_TITEL, groesse)
        f.set_bold(fett)
        _FONT_CACHE[schluessel] = _MischFont(f)
    return _FONT_CACHE[schluessel]


def font_dekorativ(groesse: int) -> "_MischFont":
    """Stark verzierte Prunkschrift (Cinzel Decorative), ausschließlich für
    den großen Spieltitel auf dem Startbildschirm gedacht."""
    schluessel = ("dekorativ", groesse, False)
    if schluessel not in _FONT_CACHE:
        _FONT_CACHE[schluessel] = _MischFont(pygame.font.Font(_SCHRIFT_TITEL_DEKORATIV, groesse))
    return _FONT_CACHE[schluessel]

"""Wiederverwendbare UI-Bausteine: Buttons, Textfelder, Balken, Textumbruch,
sowie gemeinsame Zeichenhilfen (Verläufe, weiche Schatten, Eck-Ornamente)."""

import time
from pathlib import Path

import pygame

from gui import theme

_ASSETS_UI = Path(__file__).resolve().parent.parent / "assets" / "ui"
_BILD_CACHE: dict[str, "pygame.Surface"] = {}


def _bild(name: str) -> "pygame.Surface":
    if name not in _BILD_CACHE:
        _BILD_CACHE[name] = pygame.image.load(str(_ASSETS_UI / name)).convert_alpha()
    return _BILD_CACHE[name]


# ---------------------------------------------------------------------------
# Grundlegende Zeichenhilfen - werden von Button/panel/Statusleiste etc.
# genutzt, damit jedes UI-Element denselben "polierten" Look teilt statt
# flacher Ein-Farb-Rechtecke mit dünnem Rand.
# ---------------------------------------------------------------------------

def _mische(farbe_a, farbe_b, anteil: float):
    anteil = max(0.0, min(1.0, anteil))
    return tuple(int(a + (b - a) * anteil) for a, b in zip(farbe_a, farbe_b))


def schatten(surface, rect, radius=10, versatz=(0, 4)):
    """Simuliert einen weichen Schlagschatten über mehrere, zunehmend größere
    und transparentere Schichten - ohne echten (teuren) Weichzeichner
    auszukommen, aber deutlich weicher als ein einzelnes hartes Rechteck."""
    rect = pygame.Rect(rect)
    for wachstum, alpha in ((7, 18), (4, 30), (2, 42)):
        s = pygame.Surface((rect.width + wachstum * 2, rect.height + wachstum * 2), pygame.SRCALPHA)
        pygame.draw.rect(s, (*theme.FARBEN["schatten"], alpha), s.get_rect(), border_radius=radius + wachstum // 2)
        surface.blit(s, (rect.x - wachstum + versatz[0], rect.y - wachstum + versatz[1]))


def verlauf_rect(surface, rect, farbe_oben, farbe_unten, radius=8, bands=12):
    """Füllt ein (optional abgerundetes) Rechteck mit einem vertikalen
    Farbverlauf - in Bändern statt pro Pixel gezeichnet, das bleibt auch bei
    vielen gleichzeitig sichtbaren Buttons/Panels günstig genug für 60 FPS."""
    rect = pygame.Rect(rect)
    temp = pygame.Surface(rect.size, pygame.SRCALPHA)
    band_h = max(1, -(-rect.height // bands))
    for i in range(bands):
        t = i / max(1, bands - 1)
        farbe = tuple(int(a + (b - a) * t) for a, b in zip(farbe_oben, farbe_unten))
        y0 = i * band_h
        if y0 >= rect.height:
            break
        y1 = min(rect.height, y0 + band_h)
        pygame.draw.rect(temp, farbe, (0, y0, rect.width, y1 - y0))
    if radius:
        maske = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(maske, (255, 255, 255, 255), maske.get_rect(), border_radius=radius)
        temp.blit(maske, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surface.blit(temp, rect.topleft)


def ecken_ornament(surface, rect, groesse=26):
    """Setzt das kleine goldene Eck-Ornament (siehe assets/ui/) an alle vier
    Ecken eines Rechtecks - das schlichte "Programmierer-Rechteck" bekommt
    damit einen handgemachten, fantasy-typischen Rahmen-Akzent."""
    basis = _bild("corner_ornament.png")
    skaliert = pygame.transform.smoothscale(basis, (groesse, groesse))
    tl, tr = skaliert, pygame.transform.flip(skaliert, True, False)
    bl, br = pygame.transform.flip(skaliert, False, True), pygame.transform.flip(skaliert, True, True)
    surface.blit(tl, (rect.left - 2, rect.top - 2))
    surface.blit(tr, (rect.right - groesse + 2, rect.top - 2))
    surface.blit(bl, (rect.left - 2, rect.bottom - groesse + 2))
    surface.blit(br, (rect.right - groesse + 2, rect.bottom - groesse + 2))


def trennlinie(surface, mitte_x, y, breite=340):
    """Zeichnet die dekorative, goldene Trennlinie (siehe assets/ui/) mittig
    unter Überschriften - ersetzt frühere schmucklose Textblöcke ohne jede
    visuelle Abgrenzung zum darunterliegenden Inhalt."""
    basis = _bild("divider.png")
    hoehe = max(1, int(basis.get_height() * (breite / basis.get_width())))
    skaliert = pygame.transform.smoothscale(basis, (breite, hoehe))
    surface.blit(skaliert, skaliert.get_rect(center=(mitte_x, y)))


class Button:
    def __init__(self, rect, text, groesse=22, enabled=True, subtitle=None, subtitle_groesse=15, icon=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = theme.font_titel(groesse, fett=False)
        self.enabled = enabled
        self.subtitle = subtitle
        self.subtitle_font = theme.font(subtitle_groesse) if subtitle else None
        self.icon = icon  # optionale pygame.Surface (z.B. ein Klassen-Portrait), links im Button
        self.hover = False
        # 0 = normaler Zustand, 1 = voll "aufgehellt" - nähert sich beim
        # Zeichnen sanft an, statt beim Drüberfahren hart umzuspringen.
        self._hover_anteil = 0.0
        self._letzte_zeit = time.perf_counter()

    def handle_event(self, event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def _hover_aktualisieren(self) -> float:
        jetzt = time.perf_counter()
        dt = min(0.1, max(0.0, jetzt - self._letzte_zeit))
        self._letzte_zeit = jetzt
        ziel = 1.0 if (self.hover and self.enabled) else 0.0
        self._hover_anteil += (ziel - self._hover_anteil) * min(1.0, 12.0 * dt)
        if abs(ziel - self._hover_anteil) < 0.01:
            self._hover_anteil = ziel
        return self._hover_anteil

    def draw(self, surface):
        radius = min(12, self.rect.height // 3)
        hover_anteil = self._hover_aktualisieren()
        if not self.enabled:
            oben, unten, rand = theme.FARBEN["button_deaktiviert_oben"], theme.FARBEN["button_deaktiviert_unten"], theme.FARBEN["button_rand_dim"]
        else:
            schatten(surface, self.rect, radius=radius, versatz=(0, 3))
            # Farben statt hart zwischen normal/hover umzuschalten weich
            # überblenden - macht aus dem Drüberfahren eine kleine Geste
            # statt eines abrupten Umschaltens.
            oben = _mische(theme.FARBEN["button_oben"], theme.FARBEN["button_hover_oben"], hover_anteil)
            unten = _mische(theme.FARBEN["button_unten"], theme.FARBEN["button_hover_unten"], hover_anteil)
            rand = _mische(theme.FARBEN["button_rand"], theme.FARBEN["akzent_hell"], hover_anteil)
        verlauf_rect(surface, self.rect, oben, unten, radius=radius)
        pygame.draw.rect(surface, rand, self.rect, width=2, border_radius=radius)
        if self.enabled:
            # Dünner heller Glanzstreifen an der Oberkante - macht aus dem
            # Verlauf ein "poliertes" statt nur zweifarbiges Rechteck.
            glanz = pygame.Rect(self.rect.x + radius, self.rect.y + 2, max(0, self.rect.width - radius * 2), 2)
            glanz_surf = pygame.Surface(glanz.size, pygame.SRCALPHA)
            glanz_surf.fill((255, 255, 255, 30))
            surface.blit(glanz_surf, glanz.topleft)

        icon_zone = 0
        if self.icon:
            icon_rect = self.icon.get_rect(midleft=(self.rect.x + 14, self.rect.centery))
            surface.blit(self.icon, icon_rect)
            # Textbereich um die Icon-Zone verkleinern und die Zentrierachse
            # entsprechend nach rechts verschieben - sonst überlappt bei
            # langen, fast vollbreiten Texten (z.B. Begleiter-Zeilen) das
            # Icon den Zeilenanfang.
            icon_zone = icon_rect.width + 20

        text_farbe = theme.FARBEN["text"] if self.enabled else theme.FARBEN["text_dim"]
        mitte_y = self.rect.centery - (10 if self.subtitle else 0)
        text_mitte_x = self.rect.centerx + icon_zone // 2
        # Lange Texte (z.B. ausführliche Quest-Beschreibungen) würden als eine
        # Zeile seitlich über den Button hinauslaufen - stattdessen auf so
        # viele Zeilen umbrechen, wie innerhalb der Button-Breite passen, und
        # als Block vertikal zentriert darstellen.
        max_breite = self.rect.width - 24 - icon_zone
        zeilen = zeilenumbruch(self.text, self.font, max_breite) if self.font.size(self.text)[0] > max_breite else [self.text]
        zeilenhoehe = self.font.get_linesize()
        block_hoehe = zeilenhoehe * len(zeilen)
        start_y = mitte_y - block_hoehe // 2
        for i, zeile in enumerate(zeilen):
            label = self.font.render(zeile, True, text_farbe)
            label_rect = label.get_rect(center=(text_mitte_x, start_y + zeilenhoehe * i + zeilenhoehe // 2))
            surface.blit(label, label_rect)

        if self.subtitle:
            sub = self.subtitle_font.render(self.subtitle, True, theme.FARBEN["text_dim"])
            sub_rect = sub.get_rect(center=(self.rect.centerx, self.rect.centery + 13))
            surface.blit(sub, sub_rect)


class TextEingabe:
    def __init__(self, rect, groesse=26, placeholder="", max_laenge=24):
        self.rect = pygame.Rect(rect)
        self.font = theme.font(groesse)
        self.text = ""
        self.placeholder = placeholder
        self.max_laenge = max_laenge
        self._cursor_sichtbar = True
        self._cursor_timer = 0.0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode and event.unicode.isprintable() and len(self.text) < self.max_laenge:
                self.text += event.unicode

    def update(self, dt):
        self._cursor_timer += dt
        if self._cursor_timer >= 0.5:
            self._cursor_timer = 0.0
            self._cursor_sichtbar = not self._cursor_sichtbar

    def draw(self, surface):
        verlauf_rect(surface, self.rect, (18, 15, 24), (10, 8, 14), radius=8)
        pygame.draw.rect(surface, theme.FARBEN["akzent"], self.rect, width=2, border_radius=8)
        anzeige = self.text if self.text else self.placeholder
        farbe = theme.FARBEN["text"] if self.text else theme.FARBEN["text_dim"]
        label = self.font.render(anzeige, True, farbe)
        alter_clip = surface.get_clip()
        surface.set_clip(self.rect.inflate(-16, -4))
        surface.blit(label, (self.rect.x + 12, self.rect.y + (self.rect.height - label.get_height()) // 2))
        surface.set_clip(alter_clip)
        if self.text and self._cursor_sichtbar:
            x = self.rect.x + 12 + label.get_width() + 2
            y = self.rect.y + 8
            pygame.draw.line(surface, theme.FARBEN["text"], (x, y), (x, self.rect.bottom - 8), 2)


def zeilenumbruch(text: str, font: "pygame.font.Font", max_breite: int) -> list[str]:
    zeilen = []
    for absatz in text.split("\n"):
        if not absatz:
            zeilen.append("")
            continue
        woerter = absatz.split(" ")
        aktuell = ""
        for wort in woerter:
            test = f"{aktuell} {wort}".strip()
            if font.size(test)[0] <= max_breite:
                aktuell = test
            else:
                if aktuell:
                    zeilen.append(aktuell)
                aktuell = wort
        if aktuell:
            zeilen.append(aktuell)
    return zeilen


def balken(surface, rect, anteil, farbe_voll, farbe_leer):
    rect = pygame.Rect(rect)
    radius = min(4, rect.height // 2)
    pygame.draw.rect(surface, farbe_leer, rect, border_radius=radius)
    breite = int(rect.width * max(0.0, min(1.0, anteil)))
    if breite > 0:
        hell = tuple(min(255, int(c * 1.35)) for c in farbe_voll)
        verlauf_rect(surface, (rect.x, rect.y, breite, rect.height), hell, farbe_voll, radius=radius)
    pygame.draw.rect(surface, (10, 8, 12), rect, width=1, border_radius=radius)


class SchwebeText:
    """Ein Text, der langsam nach oben treibt und dabei ausblendet - für
    Schadens-/Heilzahlen im Kampf. update() gibt False zurück, sobald er
    verblasst ist; der Aufrufer sollte ihn dann aus seiner Liste entfernen."""

    def __init__(self, text: str, x: float, y: float, farbe, lebensdauer: float = 1.0, aufstieg: float = 46.0):
        self.text = text
        self.x = x
        self.start_y = y
        self.farbe = farbe
        self.lebensdauer = lebensdauer
        self.aufstieg = aufstieg
        self.alter = 0.0

    def update(self, dt: float) -> bool:
        self.alter += dt
        return self.alter < self.lebensdauer

    def draw(self, surface, font):
        fortschritt = min(1.0, self.alter / self.lebensdauer)
        y = self.start_y - self.aufstieg * fortschritt
        alpha = int(255 * (1.0 - fortschritt) ** 1.5)
        label = font.render(self.text, True, self.farbe)
        label.set_alpha(alpha)
        surface.blit(label, label.get_rect(center=(int(self.x), int(y))))


class AnimierterWert:
    """Ein Zahlenwert (0..1), der sich pro Aufruf sanft dem tatsächlichen
    Zielwert annähert statt sofort zu springen - für HP-/MP-Balken, die sich
    nach Schaden oder Heilung weich statt abrupt verändern sollen. Verfolgt
    die Zeit selbst über die Systemuhr, statt dass jeder Aufrufer sein
    eigenes dt durchreichen müsste."""

    def __init__(self, start: float, geschwindigkeit: float = 4.5):
        self.wert = start
        self.geschwindigkeit = geschwindigkeit
        self._letzte_zeit = time.perf_counter()

    def aktualisiert(self, ziel: float) -> float:
        jetzt = time.perf_counter()
        dt = min(0.1, max(0.0, jetzt - self._letzte_zeit))
        self._letzte_zeit = jetzt
        differenz = ziel - self.wert
        if abs(differenz) < 0.002:
            self.wert = ziel
        else:
            self.wert += differenz * min(1.0, self.geschwindigkeit * dt)
        return self.wert


_ANIMIERTE_WERTE: dict[object, AnimierterWert] = {}


def animierter_balken(surface, rect, schluessel, ziel_anteil, farbe_voll, farbe_leer, geschwindigkeit=4.5):
    """Wie balken(), aber der Füllstand nähert sich Veränderungen weich an,
    statt bei jedem Treffer/jeder Heilung sofort zu springen. `schluessel`
    muss je Balken eindeutig und über mehrere Frames hinweg stabil sein
    (z.B. (id(objekt), "hp")) - der Animationszustand wird darüber gemerkt."""
    if schluessel not in _ANIMIERTE_WERTE:
        _ANIMIERTE_WERTE[schluessel] = AnimierterWert(ziel_anteil, geschwindigkeit)
    angezeigt = _ANIMIERTE_WERTE[schluessel].aktualisiert(max(0.0, min(1.0, ziel_anteil)))
    balken(surface, rect, angezeigt, farbe_voll, farbe_leer)


def panel(surface, rect, farbe=None, ornament=False):
    rect = pygame.Rect(rect)
    schatten(surface, rect, radius=12, versatz=(0, 5))
    if farbe:
        verlauf_rect(surface, rect, farbe, farbe, radius=12)
    else:
        verlauf_rect(surface, rect, theme.FARBEN["panel_oben"], theme.FARBEN["panel_unten"], radius=12)
    pygame.draw.rect(surface, theme.FARBEN["panel_rand"], rect, width=2, border_radius=12)
    if ornament:
        ecken_ornament(surface, rect, groesse=24)


def text_block(surface, text, font, farbe, rect, zeilenabstand=6, scroll=0) -> int:
    """Zeichnet umgebrochenen Text in einen Rechteck-Bereich (mit Clipping und
    optionalem vertikalem Scroll-Offset). Gibt die Gesamthöhe des Textes zurück,
    damit der Aufrufer weiß, ob/wie weit gescrollt werden kann."""
    zeilen = zeilenumbruch(text, font, rect.width)
    zeilenhoehe = font.get_height() + zeilenabstand
    gesamthoehe = len(zeilen) * zeilenhoehe

    alter_clip = surface.get_clip()
    surface.set_clip(rect)
    y = rect.y - scroll
    for zeile in zeilen:
        if y + zeilenhoehe >= rect.y and y <= rect.bottom:
            label = font.render(zeile, True, farbe)
            surface.blit(label, (rect.x, y))
        y += zeilenhoehe
    surface.set_clip(alter_clip)
    return gesamthoehe

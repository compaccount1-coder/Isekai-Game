"""Wiederverwendbare UI-Bausteine: Buttons, Textfelder, Balken, Textumbruch."""

import pygame

from gui import theme


class Button:
    def __init__(self, rect, text, groesse=24, enabled=True, subtitle=None, subtitle_groesse=16):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = theme.font(groesse)
        self.enabled = enabled
        self.subtitle = subtitle
        self.subtitle_font = theme.font(subtitle_groesse) if subtitle else None
        self.hover = False

    def handle_event(self, event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface):
        if not self.enabled:
            farbe = theme.FARBEN["button_deaktiviert"]
        elif self.hover:
            farbe = theme.FARBEN["button_hover"]
        else:
            farbe = theme.FARBEN["button"]
        pygame.draw.rect(surface, farbe, self.rect, border_radius=8)
        pygame.draw.rect(surface, theme.FARBEN["button_rand"], self.rect, width=2, border_radius=8)

        text_farbe = theme.FARBEN["text"] if self.enabled else theme.FARBEN["text_dim"]
        mitte_y = self.rect.centery - (10 if self.subtitle else 0)
        label = self.font.render(self.text, True, text_farbe)
        label_rect = label.get_rect(center=(self.rect.centerx, mitte_y))
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
        pygame.draw.rect(surface, (12, 10, 16), self.rect, border_radius=6)
        pygame.draw.rect(surface, theme.FARBEN["akzent"], self.rect, width=2, border_radius=6)
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
    pygame.draw.rect(surface, farbe_leer, rect, border_radius=4)
    breite = int(rect.width * max(0.0, min(1.0, anteil)))
    if breite > 0:
        pygame.draw.rect(surface, farbe_voll, (rect.x, rect.y, breite, rect.height), border_radius=4)
    pygame.draw.rect(surface, (0, 0, 0), rect, width=1, border_radius=4)


def panel(surface, rect, farbe=None):
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, farbe or theme.FARBEN["panel"], rect, border_radius=10)
    pygame.draw.rect(surface, theme.FARBEN["panel_rand"], rect, width=2, border_radius=10)


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

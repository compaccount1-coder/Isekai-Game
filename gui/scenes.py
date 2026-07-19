"""Alle Bildschirme (Szenen) der grafischen Oberfläche: Titel, Charakter-
erstellung, Haupt-Hub, Ort-Menüs und Ergebnis-/Ende-Anzeigen."""

import random

import pygame

from game import locations as locations_module
from game import savegame
from gui import orte, spiellauf, theme, widgets
from game.character import Charakter
from game.classes import KLASSEN
from game.story import ISEKAI_INTROS, PERSOENLICHKEITEN, erzeuge_ende
from game.world import generiere_welt
from gui.orte import Submenu
from gui.widgets import Button


class Szene:
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


def _statusleiste(surface, charakter):
    rect = pygame.Rect(40, 40, theme.BREITE - 80, 150)
    widgets.panel(surface, rect)
    f_gross = theme.font(23, fett=True)
    f_klein = theme.font(16)

    name_label = f_gross.render(f"{charakter.name} - {charakter.tier.name} (Lv. {charakter.level})", True, theme.FARBEN["text"])
    surface.blit(name_label, (rect.x + 20, rect.y + 12))

    info_label = f_klein.render(
        f"Rang {charakter.rang}  |  {charakter.gold}g  |  Tag {charakter.tage_vergangen}  |  Ruf {charakter.ruf:+d}",
        True, theme.FARBEN["text_dim"],
    )
    surface.blit(info_label, (rect.x + 20, rect.y + 44))

    hp_label = f_klein.render(f"HP {charakter.hp_aktuell}/{charakter.hp_max}", True, theme.FARBEN["text"])
    surface.blit(hp_label, (rect.x + 20, rect.y + 80))
    widgets.balken(surface, (rect.x + 130, rect.y + 82, 280, 18), charakter.hp_aktuell / max(1, charakter.hp_max), theme.FARBEN["hp_voll"], theme.FARBEN["hp_leer"])

    mp_label = f_klein.render(f"MP {charakter.mp_aktuell}/{charakter.mp_max}", True, theme.FARBEN["text"])
    surface.blit(mp_label, (rect.x + 440, rect.y + 80))
    widgets.balken(surface, (rect.x + 540, rect.y + 82, 280, 18), charakter.mp_aktuell / max(1, charakter.mp_max), theme.FARBEN["mp_voll"], theme.FARBEN["mp_leer"])

    if charakter.begleiter:
        beg_text = " | ".join(f"{b.name} (Lv.{b.level} {b.rolle})" for b in charakter.begleiter)
    else:
        beg_text = "Reist allein."
    beg_label = f_klein.render(f"Gruppe: {beg_text}", True, theme.FARBEN["text_dim"])
    surface.blit(beg_label, (rect.x + 20, rect.y + 112))


class TitleScene(Szene):
    def __init__(self, app):
        super().__init__(app)
        mitte_x = theme.BREITE // 2
        self.neues_spiel_button = Button((mitte_x - 160, 430, 320, 60), "Neues Spiel", groesse=26)
        fortsetzen_moeglich = savegame.spielstand_vorhanden()
        self.fortsetzen_button = Button((mitte_x - 160, 508, 320, 60), "Fortsetzen", groesse=26, enabled=fortsetzen_moeglich)
        self.beenden_button = Button((mitte_x - 160, 586, 320, 60), "Beenden", groesse=26)

    def handle_event(self, event):
        if self.neues_spiel_button.handle_event(event):
            self.app.wechsle_szene(CharErstellungScene(self.app))
        elif self.fortsetzen_button.handle_event(event):
            try:
                charakter, welt = savegame.laden()
                self.app.wechsle_szene(HubScene(self.app, charakter, welt))
            except (OSError, ValueError, KeyError):
                self.fortsetzen_button.enabled = False
        elif self.beenden_button.handle_event(event):
            self.app.laeuft = False

    def draw(self, surface):
        surface.fill(theme.ORT_FARBEN["titel"])
        titel = theme.font(60, fett=True).render("ISEKAI CHRONICLES", True, theme.FARBEN["akzent"])
        surface.blit(titel, (theme.BREITE // 2 - titel.get_width() // 2, 210))
        untertitel = theme.font(20).render("Eine Geschichte voller unendlicher Möglichkeiten", True, theme.FARBEN["text_dim"])
        surface.blit(untertitel, (theme.BREITE // 2 - untertitel.get_width() // 2, 300))
        self.neues_spiel_button.draw(surface)
        self.fortsetzen_button.draw(surface)
        self.beenden_button.draw(surface)


class CharErstellungScene(Szene):
    def __init__(self, app):
        super().__init__(app)
        self.intro = random.choice(ISEKAI_INTROS)
        self.name_eingabe = widgets.TextEingabe((theme.BREITE // 2 - 220, 175, 440, 46), placeholder="Wie lautete dein Name in deinem vorherigen Leben?")
        self.klasse_id: str | None = None
        self.klassen_buttons: list[tuple[str, Button]] = []
        self._baue_klassen_buttons()
        self.bestaetigen_button = Button((theme.BREITE // 2 - 150, theme.HOEHE - 84, 300, 54), "Ins Abenteuer starten!", groesse=22, enabled=False)

    def _baue_klassen_buttons(self):
        klassen = list(KLASSEN.items())
        spalten = 3
        breite, hoehe = 380, 68
        abstand_x, abstand_y = 20, 14
        gesamt_breite = spalten * breite + (spalten - 1) * abstand_x
        start_x = (theme.BREITE - gesamt_breite) // 2
        start_y = 250
        for i, (kid, klasse) in enumerate(klassen):
            spalte = i % spalten
            zeile = i // spalten
            rect = (start_x + spalte * (breite + abstand_x), start_y + zeile * (hoehe + abstand_y), breite, hoehe)
            btn = Button(rect, klasse.tiers[0].name, groesse=19, subtitle=klasse.rolle, subtitle_groesse=14)
            self.klassen_buttons.append((kid, btn))

    def handle_event(self, event):
        self.name_eingabe.handle_event(event)
        for kid, btn in self.klassen_buttons:
            if btn.handle_event(event):
                self.klasse_id = kid
        self.bestaetigen_button.enabled = self.klasse_id is not None
        if self.bestaetigen_button.handle_event(event) and self.klasse_id:
            self._starten()

    def _starten(self):
        name = self.name_eingabe.text.strip() or "Namenloser Wanderer"
        persoenlichkeit = random.sample(PERSOENLICHKEITEN, k=2)
        charakter = Charakter(name=name, klasse_id=self.klasse_id, persoenlichkeit=persoenlichkeit)
        welt = generiere_welt(anzahl_koenigreiche=random.randint(4, 6))
        self.app.wechsle_szene(HubScene(self.app, charakter, welt))

    def update(self, dt):
        self.name_eingabe.update(dt)

    def draw(self, surface):
        surface.fill(theme.ORT_FARBEN["titel"])
        titel = theme.font(28, fett=True).render("Wähle deinen Weg in dieser neuen Welt", True, theme.FARBEN["akzent"])
        surface.blit(titel, (theme.BREITE // 2 - titel.get_width() // 2, 40))
        intro_zeilen = widgets.zeilenumbruch(self.intro, theme.font(15), theme.BREITE - 240)
        y = 90
        for zeile in intro_zeilen:
            label = theme.font(15).render(zeile, True, theme.FARBEN["text_dim"])
            surface.blit(label, (theme.BREITE // 2 - label.get_width() // 2, y))
            y += 19

        self.name_eingabe.draw(surface)

        for kid, btn in self.klassen_buttons:
            btn.draw(surface)
            if kid == self.klasse_id:
                pygame.draw.rect(surface, theme.FARBEN["akzent"], btn.rect, width=3, border_radius=8)

        if self.klasse_id:
            archetyp = KLASSEN[self.klasse_id].archetyp
            zeilen = widgets.zeilenumbruch(archetyp, theme.font(15), theme.BREITE - 240)
            y = theme.HOEHE - 150
            for zeile in zeilen:
                label = theme.font(15).render(zeile, True, theme.FARBEN["text"])
                surface.blit(label, (theme.BREITE // 2 - label.get_width() // 2, y))
                y += 19

        self.bestaetigen_button.draw(surface)


class HubScene(Szene):
    def __init__(self, app, charakter, welt):
        super().__init__(app)
        self.charakter = charakter
        self.welt = welt
        self.ort_ids = orte.hub_orte(charakter)
        self.buttons: list[Button] = []
        self._baue_buttons()
        try:
            savegame.speichern(charakter, welt)
        except OSError:
            pass

    def _baue_buttons(self):
        self.buttons = []
        start_y = 240
        breite = 760
        hoehe = 62
        abstand = 14
        x = (theme.BREITE - breite) // 2
        for i, ort_id in enumerate(self.ort_ids):
            ort = locations_module.ORTE[ort_id]
            rect = (x, start_y + i * (hoehe + abstand), breite, hoehe)
            self.buttons.append(Button(rect, f"{ort.icon}  {ort.name}", groesse=23, subtitle=orte.ORT_BESCHREIBUNGEN[ort_id], subtitle_groesse=14))

    def handle_event(self, event):
        for i, button in enumerate(self.buttons):
            if button.handle_event(event):
                ort_id = self.ort_ids[i]
                optionen = orte.optionen_fuer_ort(ort_id, self.charakter, self.welt)
                ort = locations_module.ORTE[ort_id]
                farbe = theme.ORT_FARBEN.get(ort_id, theme.FARBEN["hintergrund"])
                self.app.wechsle_szene(OrtScene(self.app, self.charakter, self.welt, f"{ort.icon} {ort.name}", optionen, farbe))
                return

    def draw(self, surface):
        surface.fill(theme.FARBEN["hintergrund"])
        _statusleiste(surface, self.charakter)
        kopf = theme.font(24).render(f"Wohin geht {self.charakter.name}?", True, theme.FARBEN["text"])
        surface.blit(kopf, (theme.BREITE // 2 - kopf.get_width() // 2, 205))
        for button in self.buttons:
            button.draw(surface)


class OrtScene(Szene):
    """Zeigt die Options-Buttons eines Ortes (oder Untermenüs davon) an und
    löst die gewählte Aktion aus - entweder ein weiteres Untermenü oder ein
    Ereignis, das dann zur Anzeige/Tagesabschluss-Kette übergeben wird."""

    def __init__(self, app, charakter, welt, titel, optionen, hintergrundfarbe, zurueck=None):
        super().__init__(app)
        self.charakter = charakter
        self.welt = welt
        self.titel = titel
        self.optionen = optionen
        self.hintergrundfarbe = hintergrundfarbe
        self.zurueck = zurueck
        self.buttons: list[Button] = []
        self.zurueck_button: Button | None = None
        self._baue_buttons()

    def _baue_buttons(self):
        self.buttons = []
        start_y = 230
        breite = 820
        hoehe = 54
        abstand = 12
        x = (theme.BREITE - breite) // 2
        for i, (label, _) in enumerate(self.optionen):
            rect = (x, start_y + i * (hoehe + abstand), breite, hoehe)
            self.buttons.append(Button(rect, label, groesse=19))
        if self.zurueck:
            self.zurueck_button = Button((40, theme.HOEHE - 76, 160, 46), "◀ Zurück", groesse=19)

    def handle_event(self, event):
        for i, button in enumerate(self.buttons):
            if button.handle_event(event):
                self._waehle(i)
                return
        if self.zurueck_button and self.zurueck_button.handle_event(event):
            self.app.wechsle_szene(self.zurueck())

    def _waehle(self, idx):
        _, aktion = self.optionen[idx]
        ergebnis = aktion()
        if isinstance(ergebnis, Submenu):
            zurueck_ziel = self
            self.app.wechsle_szene(
                OrtScene(self.app, self.charakter, self.welt, ergebnis.titel, ergebnis.optionen, self.hintergrundfarbe, zurueck=lambda: zurueck_ziel)
            )
        else:
            _starte_ereignis_anzeige(self.app, self.charakter, self.welt, self.titel, ergebnis)

    def draw(self, surface):
        surface.fill(self.hintergrundfarbe)
        _statusleiste(surface, self.charakter)
        titel_zeilen = widgets.zeilenumbruch(self.titel, theme.font(25, fett=True), theme.BREITE - 160)
        y = 200
        for zeile in titel_zeilen:
            label = theme.font(25, fett=True).render(zeile, True, theme.FARBEN["akzent"])
            surface.blit(label, (theme.BREITE // 2 - label.get_width() // 2, y))
            y += 30
        for button in self.buttons:
            button.draw(surface)
        if self.zurueck_button:
            self.zurueck_button.draw(surface)


class MeldungScene(Szene):
    """Generische Anzeige: Titel + scrollbarer Text + ein Weiter-Button, der
    eine übergebene Callback-Funktion aufruft. Wird für Ereignis-Ergebnisse,
    Story-Beats und das Spielende verwendet."""

    def __init__(self, app, titel, text, weiter_text, on_weiter, hintergrundfarbe=None):
        super().__init__(app)
        self.titel = titel
        self.text = text
        self.hintergrundfarbe = hintergrundfarbe or theme.FARBEN["hintergrund"]
        self.on_weiter = on_weiter
        self.scroll = 0
        self._textrect = pygame.Rect(80, 150, theme.BREITE - 160, theme.HOEHE - 260)
        self.weiter_button = Button((theme.BREITE // 2 - 120, theme.HOEHE - 86, 240, 56), weiter_text, groesse=23)

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y * 30)
        if self.weiter_button.handle_event(event):
            self.on_weiter()

    def draw(self, surface):
        surface.fill(self.hintergrundfarbe)
        titel_label = theme.font(30, fett=True).render(self.titel, True, theme.FARBEN["akzent"])
        surface.blit(titel_label, (80, 60))
        widgets.panel(surface, self._textrect)
        innen = self._textrect.inflate(-40, -40)
        gesamthoehe = widgets.text_block(surface, self.text, theme.font(19), theme.FARBEN["text"], innen, scroll=self.scroll)
        self.scroll = max(0, min(self.scroll, max(0, gesamthoehe - innen.height)))
        self.weiter_button.draw(surface)


def _starte_ereignis_anzeige(app, charakter, welt, ort_titel, ereignis):
    text, gestorben = spiellauf.verarbeite_ereignis(charakter, ereignis)
    icon = "💥 " if ereignis.ist_wichtig else ""

    def weiter():
        if gestorben:
            _zeige_ende(app, charakter, welt, "tod")
            return
        zusatztext, ende_grund = spiellauf.tagesende(charakter, welt)
        if zusatztext.strip():
            app.wechsle_szene(
                MeldungScene(app, "📅 Der Tag geht weiter", zusatztext, "Weiter", lambda: _nach_tagesende(app, charakter, welt, ende_grund))
            )
        else:
            _nach_tagesende(app, charakter, welt, ende_grund)

    app.wechsle_szene(MeldungScene(app, f"{icon}{ort_titel}", text, "Weiter", weiter))


def _nach_tagesende(app, charakter, welt, ende_grund):
    if ende_grund:
        _zeige_ende(app, charakter, welt, ende_grund)
    else:
        app.wechsle_szene(HubScene(app, charakter, welt))


def _zeige_ende(app, charakter, welt, grund):
    ende_text = erzeuge_ende(charakter, welt, grund)
    app.wechsle_szene(MeldungScene(app, "📖 Das Ende deiner Geschichte", ende_text, "Zum Titelbildschirm", lambda: app.wechsle_szene(TitleScene(app))))

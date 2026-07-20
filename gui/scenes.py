"""Alle Bildschirme (Szenen) der grafischen Oberfläche: Titel, Charakter-
erstellung, Haupt-Hub, Ort-Menüs und Ergebnis-/Ende-Anzeigen."""

import random

import pygame

from game import locations as locations_module
from game import savegame
from gui import einstellungen, hintergruende, musik, orte, portraits, spiellauf, theme, widgets
from game.character import MAX_AKTIONEN_PRO_TAG, Charakter
from game.classes import KLASSEN, skill_ist_aoe, skill_ist_signatur
from game.combat import Kampfstart
from game.story import ISEKAI_INTROS, PERSOENLICHKEITEN, erzeuge_ende
from game.world import generiere_welt
from gui.orte import Submenu
from gui.widgets import Button


class Szene:
    # Ob ESC auf dieser Szene das Pause-Menü öffnet (siehe App.starten) -
    # für den Titelbildschirm und das Pause-Menü selbst abgeschaltet.
    pausierbar = True

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
    widgets.panel(surface, rect, ornament=True)
    f_gross = theme.font_titel(22)
    f_klein = theme.font(16)

    portrait = portraits.gerahmt(charakter.klasse_id, radius=48, variante=charakter.name)
    surface.blit(portrait, portrait.get_rect(midleft=(rect.x + 20, rect.centery)))
    text_x = rect.x + 30 + portrait.get_width()

    name_label = f_gross.render(f"{charakter.name} - {charakter.tier.name} (Lv. {charakter.level})", True, theme.FARBEN["akzent_hell"])
    surface.blit(name_label, (text_x, rect.y + 12))

    info_label = f_klein.render(
        f"Rang {charakter.rang}  |  {charakter.gold}g  |  Tag {charakter.tage_vergangen}  |  Ruf {charakter.ruf:+d}",
        True, theme.FARBEN["text_dim"],
    )
    surface.blit(info_label, (text_x, rect.y + 44))

    hp_label = f_klein.render(f"HP {charakter.hp_aktuell}/{charakter.hp_max}", True, theme.FARBEN["text"])
    surface.blit(hp_label, (text_x, rect.y + 80))
    widgets.animierter_balken(surface, (text_x + 110, rect.y + 82, 260, 18), (id(charakter), "hp"), charakter.hp_aktuell / max(1, charakter.hp_max), theme.FARBEN["hp_voll"], theme.FARBEN["hp_leer"])

    mp_label = f_klein.render(f"MP {charakter.mp_aktuell}/{charakter.mp_max}", True, theme.FARBEN["text"])
    surface.blit(mp_label, (text_x + 400, rect.y + 80))
    widgets.animierter_balken(surface, (text_x + 500, rect.y + 82, 260, 18), (id(charakter), "mp"), charakter.mp_aktuell / max(1, charakter.mp_max), theme.FARBEN["mp_voll"], theme.FARBEN["mp_leer"])

    if charakter.begleiter:
        beg_text = " | ".join(
            f"{b.name} (Lv.{b.level} {b.rolle}) HP {b.hp_aktuell}/{b.hp_max}{' [K.O.]' if b.niedergeschlagen else ''}"
            for b in charakter.begleiter
        )
    else:
        beg_text = "Reist allein."
    beg_label = f_klein.render(f"Gruppe: {beg_text}", True, theme.FARBEN["text_dim"])
    surface.blit(beg_label, (text_x, rect.y + 112))


class TitleScene(Szene):
    pausierbar = False

    def __init__(self, app):
        super().__init__(app)
        musik.spiele("erkundung")
        mitte_x = theme.BREITE // 2
        self.neues_spiel_button = Button((mitte_x - 160, 430, 320, 60), "Neues Spiel", groesse=26)
        fortsetzen_moeglich = bool(savegame.alle_spielstaende())
        self.fortsetzen_button = Button((mitte_x - 160, 508, 320, 60), "Fortsetzen", groesse=26, enabled=fortsetzen_moeglich)
        self.beenden_button = Button((mitte_x - 160, 586, 320, 60), "Beenden", groesse=26)

    def handle_event(self, event):
        if self.neues_spiel_button.handle_event(event):
            self.app.wechsle_szene(CharErstellungScene(self.app))
        elif self.fortsetzen_button.handle_event(event):
            self.app.wechsle_szene(SpielstandAuswahlScene(self.app))
        elif self.beenden_button.handle_event(event):
            self.app.laeuft = False

    def draw(self, surface):
        hintergruende.zeichnen(surface, "titel")
        titel = theme.font_dekorativ(58).render("ISEKAI CHRONICLES", True, theme.FARBEN["akzent_hell"])
        titel_schatten = theme.font_dekorativ(58).render("ISEKAI CHRONICLES", True, (0, 0, 0))
        surface.blit(titel_schatten, (theme.BREITE // 2 - titel.get_width() // 2 + 3, 213))
        surface.blit(titel, (theme.BREITE // 2 - titel.get_width() // 2, 210))
        untertitel = theme.font_titel(19, fett=False).render("Eine Geschichte voller unendlicher Möglichkeiten", True, theme.FARBEN["text_dim"])
        surface.blit(untertitel, (theme.BREITE // 2 - untertitel.get_width() // 2, 300))
        widgets.trennlinie(surface, theme.BREITE // 2, 345, breite=360)
        self.neues_spiel_button.draw(surface)
        self.fortsetzen_button.draw(surface)
        self.beenden_button.draw(surface)
        hinweis = theme.font(14).render("F11 = Vollbild an/aus", True, theme.FARBEN["text_dim"])
        surface.blit(hinweis, (theme.BREITE - hinweis.get_width() - 20, theme.HOEHE - 32))


class SpielstandAuswahlScene(Szene):
    """Listet alle vorhandenen Speicherstände (Name, Level, Klasse, Rang,
    Tag) zur Auswahl auf - erreichbar über "Fortsetzen" im Titelbildschirm.
    Ersetzt das frühere blinde Laden eines einzigen fixen Slots, jetzt, wo
    jeder neue Charakter seinen eigenen Slot bekommt (siehe
    game.savegame.neuer_slot)."""

    pausierbar = False

    def __init__(self, app):
        super().__init__(app)
        self.eintraege = savegame.spielstand_infos()
        self.buttons: list[Button] = []
        self._baue_buttons()
        self.zurueck_button = Button((40, theme.HOEHE - 76, 160, 46), "◀ Zurück", groesse=19)

    def _baue_buttons(self):
        self.buttons = []
        start_y = 240
        breite, abstand = 820, 14
        anzahl = max(1, len(self.eintraege))
        verfuegbar = theme.HOEHE - start_y - 100
        hoehe = min(74, max(48, (verfuegbar - (anzahl - 1) * abstand) // anzahl))
        x = (theme.BREITE - breite) // 2
        for i, (slot, charakter) in enumerate(self.eintraege):
            rect = (x, start_y + i * (hoehe + abstand), breite, hoehe)
            text = f"{charakter.name} - Lv. {charakter.level} {charakter.tier.name}"
            unterzeile = f"Rang {charakter.rang}  |  Tag {charakter.tage_vergangen}  |  {charakter.gold}g"
            self.buttons.append(Button(rect, text, groesse=21, subtitle=unterzeile, subtitle_groesse=15))

    def handle_event(self, event):
        for i, button in enumerate(self.buttons):
            if button.handle_event(event):
                slot, _ = self.eintraege[i]
                try:
                    charakter, welt = savegame.laden(slot)
                    self.app.wechsle_szene(HubScene(self.app, charakter, welt))
                except (OSError, ValueError, KeyError):
                    self.eintraege = savegame.spielstand_infos()
                    self._baue_buttons()
                return
        if self.zurueck_button.handle_event(event):
            self.app.wechsle_szene(TitleScene(self.app))

    def draw(self, surface):
        hintergruende.zeichnen(surface, "titel")
        titel = theme.font_titel(28).render("Welches Abenteuer soll weitergehen?", True, theme.FARBEN["akzent_hell"])
        surface.blit(titel, (theme.BREITE // 2 - titel.get_width() // 2, 190))
        widgets.trennlinie(surface, theme.BREITE // 2, 232, breite=320)

        if not self.eintraege:
            hinweis = theme.font(18).render("Keine Speicherstände vorhanden.", True, theme.FARBEN["text_dim"])
            surface.blit(hinweis, (theme.BREITE // 2 - hinweis.get_width() // 2, 280))
        for button in self.buttons:
            button.draw(surface)
        self.zurueck_button.draw(surface)


class CharErstellungScene(Szene):
    def __init__(self, app):
        super().__init__(app)
        musik.spiele("erkundung")
        self.intro = random.choice(ISEKAI_INTROS)
        self.name_eingabe = widgets.TextEingabe((theme.BREITE // 2 - 220, 178, 440, 42), groesse=22, placeholder="Name eingeben...")
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
            btn = Button(rect, klasse.tiers[0].name, groesse=19, subtitle=klasse.rolle, subtitle_groesse=14, icon=portraits.gerahmt(kid, radius=24))
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
        slot = savegame.neuer_slot(name)
        charakter = Charakter(name=name, klasse_id=self.klasse_id, persoenlichkeit=persoenlichkeit, spielstand_slot=slot)
        welt = generiere_welt(anzahl_koenigreiche=random.randint(4, 6))
        self.app.wechsle_szene(HubScene(self.app, charakter, welt))

    def update(self, dt):
        self.name_eingabe.update(dt)

    def draw(self, surface):
        hintergruende.zeichnen(surface, "titel")
        titel = theme.font_titel(28).render("Wähle deinen Weg in dieser neuen Welt", True, theme.FARBEN["akzent_hell"])
        surface.blit(titel, (theme.BREITE // 2 - titel.get_width() // 2, 40))
        intro_zeilen = widgets.zeilenumbruch(self.intro, theme.font(15), theme.BREITE - 240)
        y = 90
        for zeile in intro_zeilen:
            label = theme.font(15).render(zeile, True, theme.FARBEN["text_dim"])
            surface.blit(label, (theme.BREITE // 2 - label.get_width() // 2, y))
            y += 19

        namens_label = theme.font(16).render("Wie lautete dein Name in deinem vorherigen Leben?", True, theme.FARBEN["text_dim"])
        surface.blit(namens_label, (theme.BREITE // 2 - namens_label.get_width() // 2, 155))
        self.name_eingabe.draw(surface)

        for kid, btn in self.klassen_buttons:
            btn.draw(surface)
            if kid == self.klasse_id:
                pygame.draw.rect(surface, theme.FARBEN["akzent_hell"], btn.rect, width=3, border_radius=8)

        if self.klasse_id:
            portrait = portraits.gerahmt(self.klasse_id, radius=32)
            surface.blit(portrait, portrait.get_rect(center=(theme.BREITE // 2, 610)))
            archetyp = KLASSEN[self.klasse_id].archetyp
            zeilen = widgets.zeilenumbruch(archetyp, theme.font(15), theme.BREITE - 240)
            y = 655
            for zeile in zeilen:
                label = theme.font(15).render(zeile, True, theme.FARBEN["text"])
                surface.blit(label, (theme.BREITE // 2 - label.get_width() // 2, y))
                y += 19

        self.bestaetigen_button.draw(surface)


class HubScene(Szene):
    def __init__(self, app, charakter, welt):
        super().__init__(app)
        musik.spiele("erkundung")
        self.charakter = charakter
        self.welt = welt
        self.ort_ids = orte.hub_orte(charakter)
        self.buttons: list[Button] = []
        self._baue_buttons()
        try:
            savegame.speichern(charakter, welt, slot=charakter.spielstand_slot or "spielstand")
        except OSError:
            pass

    def _baue_buttons(self):
        self.buttons = []
        start_y = 258
        breite = 760
        abstand = 14
        anzahl = len(self.ort_ids)
        # Feste 62px-Buttons würden bei vielen Orten (Adelsviertel erst ab
        # Ruf 20+, plus die immer vorhandenen Inventar-/Gruppe-Einträge) unten
        # aus dem Fenster laufen - die Höhe passt sich daher an den
        # verfügbaren Platz an, statt Buttons abzuschneiden.
        verfuegbar = theme.HOEHE - start_y - 30
        hoehe = min(62, max(40, (verfuegbar - (anzahl - 1) * abstand) // max(1, anzahl)))
        x = (theme.BREITE - breite) // 2
        for i, ort_id in enumerate(self.ort_ids):
            ort = locations_module.ORTE[ort_id]
            rect = (x, start_y + i * (hoehe + abstand), breite, hoehe)
            untertitel_groesse = 14 if hoehe >= 55 else 12
            self.buttons.append(Button(rect, f"{ort.icon}  {ort.name}", groesse=23 if hoehe >= 55 else 19, subtitle=orte.ORT_BESCHREIBUNGEN[ort_id], subtitle_groesse=untertitel_groesse))

    def handle_event(self, event):
        for i, button in enumerate(self.buttons):
            if button.handle_event(event):
                ort_id = self.ort_ids[i]
                optionen = orte.optionen_fuer_ort(ort_id, self.charakter, self.welt)
                ort = locations_module.ORTE[ort_id]
                zurueck = lambda: HubScene(self.app, self.charakter, self.welt)
                self.app.wechsle_szene(
                    OrtScene(self.app, self.charakter, self.welt, f"{ort.icon} {ort.name}", optionen, ort_id, zurueck=zurueck)
                )
                return

    def draw(self, surface):
        hintergruende.zeichnen(surface, "hub")
        _statusleiste(surface, self.charakter)
        if self.charakter.aktionen_uebrig <= 0:
            kopf_text = f"😴 {self.charakter.name} ist erschöpft - Zeit, in der Taverne zu schlafen."
        else:
            kopf_text = f"Wohin geht {self.charakter.name}? (Aktionen übrig: {self.charakter.aktionen_uebrig}/{MAX_AKTIONEN_PRO_TAG})"
        kopf = theme.font_titel(23).render(kopf_text, True, theme.FARBEN["akzent_hell"])
        surface.blit(kopf, (theme.BREITE // 2 - kopf.get_width() // 2, 205))
        for button in self.buttons:
            button.draw(surface)


class OrtScene(Szene):
    """Zeigt die Options-Buttons eines Ortes (oder Untermenüs davon) an und
    löst die gewählte Aktion aus - entweder ein weiteres Untermenü oder ein
    Ereignis, das dann zur Anzeige/Tagesabschluss-Kette übergeben wird."""

    def __init__(self, app, charakter, welt, titel, optionen, ort_id, zurueck=None):
        super().__init__(app)
        musik.spiele("erkundung")
        self.charakter = charakter
        self.welt = welt
        self.titel = titel
        self.optionen = optionen
        self.ort_id = ort_id
        self.zurueck = zurueck
        self.buttons: list[Button] = []
        self.zurueck_button: Button | None = None
        self._baue_buttons()

    def _titel_zeilen(self):
        return widgets.zeilenumbruch(self.titel, theme.font_titel(25), theme.BREITE - 160)

    def _baue_buttons(self):
        self.buttons = []
        # Startet erst unterhalb des (ggf. mehrzeiligen) Titels - ein fester
        # Wert hier führte bei der neuen, etwas höheren Schriftart dazu, dass
        # der erste Button den Titeltext leicht überdeckte.
        titel_zeilenhoehe = theme.font_titel(25).get_linesize()
        y = 200 + len(self._titel_zeilen()) * titel_zeilenhoehe + 22
        breite = 820
        hoehe_min = 54
        abstand = 12
        x = (theme.BREITE - breite) // 2
        # Muss mit der Schriftart übereinstimmen, die Button.draw() tatsächlich
        # zum Rendern verwendet (font_titel) - sonst weicht die hier
        # vorausberechnete Zeilenzahl/Höhe von der echten Darstellung ab und
        # Text würde wieder über den Button-Rand hinaus clippen.
        font = theme.font_titel(19, fett=False)
        for eintrag in self.optionen:
            # Manche Orte (z.B. Gruppe) hängen ein drittes Element (ein
            # Portrait-Icon) an - alle anderen bleiben beim einfachen
            # (Text, Aktion)-Paar.
            label, _, *rest = eintrag
            icon = rest[0] if rest else None
            # Muss mit dem Textbereich übereinstimmen, den Button.draw() bei
            # vorhandenem Icon tatsächlich zur Verfügung hat (siehe dort) -
            # sonst weicht die hier vorausberechnete Zeilenzahl wieder ab.
            icon_zone = (icon.get_width() + 20) if icon else 0
            # Lange Beschreibungen (z.B. Quest-Einträge) brauchen mehr als
            # eine Zeile - die Button-Höhe richtet sich danach, damit der
            # Text nicht über den Rand hinaus clippt.
            zeilen = widgets.zeilenumbruch(label, font, breite - 24 - icon_zone)
            hoehe = max(hoehe_min, len(zeilen) * font.get_linesize() + 16)
            rect = (x, y, breite, hoehe)
            self.buttons.append(Button(rect, label, groesse=19, icon=icon))
            y += hoehe + abstand
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
        _, aktion, *_rest = self.optionen[idx]
        ergebnis = aktion()
        if isinstance(ergebnis, Submenu):
            zurueck_ziel = self
            self.app.wechsle_szene(
                OrtScene(self.app, self.charakter, self.welt, ergebnis.titel, ergebnis.optionen, self.ort_id, zurueck=lambda: zurueck_ziel)
            )
        elif isinstance(ergebnis, Kampfstart):
            self.app.wechsle_szene(KampfScene(self.app, self.charakter, self.welt, self.titel, ergebnis, self.ort_id))
        else:
            _starte_ereignis_anzeige(self.app, self.charakter, self.welt, self.titel, ergebnis, self.ort_id)

    def draw(self, surface):
        hintergruende.zeichnen(surface, self.ort_id)
        _statusleiste(surface, self.charakter)
        titel_font = theme.font_titel(25)
        y = 200
        for zeile in self._titel_zeilen():
            label = titel_font.render(zeile, True, theme.FARBEN["akzent_hell"])
            surface.blit(label, (theme.BREITE // 2 - label.get_width() // 2, y))
            y += titel_font.get_linesize()
        for button in self.buttons:
            button.draw(surface)
        if self.zurueck_button:
            self.zurueck_button.draw(surface)


class KampfScene(Szene):
    """Interaktive Kampfanzeige: der Spieler wählt jede Runde selbst die
    Fähigkeit seines Charakters über Buttons, statt dass der Kampf automatisch
    abläuft. Mehrere Kämpfe in Folge (z.B. ein Dungeon) werden durch Verketten
    weiterer KampfScene-Instanzen über bei_abschluss abgebildet."""

    def __init__(self, app, charakter, welt, ort_titel, kampfstart, ort_id=None):
        super().__init__(app)
        musik.spiele("kampf")
        self.charakter = charakter
        self.welt = welt
        self.ort_titel = ort_titel
        self.kampfstart = kampfstart
        self.kampf = kampfstart.kampf
        self.ort_id = ort_id
        self.scroll = 0
        self._auto_scroll = True
        # Die Logzeile muss unterhalb sowohl der Gegner-HP-Balken (mittig) als
        # auch der Begleiter-HP-Balken (links) beginnen - je nachdem, welche
        # der beiden Spalten mehr Zeilen braucht.
        zeilen = max(len(self.kampf.gegner_lebend()), len(self.charakter.begleiter), 1)
        self._textrect = pygame.Rect(80, 310 + max(0, zeilen - 1) * 34, theme.BREITE - 160, 0)
        self._textrect.height = theme.HOEHE - 170 - self._textrect.y
        # Zwei-Schritt-Ablauf: erst Fähigkeit wählen, danach - falls nötig -
        # ein Ziel (Gegner oder Verbündeter). self.gewaehlte_aktion ist nur
        # zwischen diesen beiden Schritten gesetzt.
        self.gewaehlte_aktion: str | None = None
        self.aktions_buttons: list[tuple[str, Button]] = []
        self.ziel_buttons: list[tuple[object, Button]] = []
        self.schwebetexte: list[widgets.SchwebeText] = []
        self._baue_aktionsbuttons()

    def update(self, dt):
        self.schwebetexte = [t for t in self.schwebetexte if t.update(dt)]

    def _position_fuer(self, ziel) -> tuple[int, int]:
        """Ungefähre Bildschirmposition eines Kampfteilnehmers - muss mit den
        Positionen in draw() übereinstimmen, an denen dessen HP-Balken
        gezeichnet wird, damit Schadens-/Heilzahlen dort auftauchen, wo sie
        inhaltlich hingehören."""
        if ziel is self.charakter:
            return (40 + 130 + 140, 40 + 82 + 9)
        for i, b in enumerate(self.charakter.begleiter):
            if b is ziel:
                return (80 + 130, 236 + i * 34 + 6)
        for i, g in enumerate(self.kampf.gegner_lebend() or self.kampf.gegnergruppe):
            if g is ziel:
                return (theme.BREITE // 2, 236 + i * 34 + 6)
        return (theme.BREITE // 2, 236)

    def _schwebetexte_erzeugen(self):
        for ziel, betrag in self.kampf.letzte_zahlen:
            x, y = self._position_fuer(ziel)
            if betrag < 0:
                text, farbe = f"-{-betrag}", theme.FARBEN["gefahr"]
            else:
                text, farbe = f"+{betrag}", theme.FARBEN["erfolg"]
            # Mehrere Zahlen für dasselbe Ziel in derselben Runde (z.B.
            # Flächenschaden + Reflexion) leicht versetzt platzieren, damit
            # sie sich nicht exakt überlappen.
            x += len([t for t in self.schwebetexte if abs(t.x - x) < 4]) * 18
            self.schwebetexte.append(widgets.SchwebeText(text, x, y, farbe))

    def _baue_aktionsbuttons(self):
        self.gewaehlte_aktion = None
        self.ziel_buttons = []
        self.aktions_buttons = []
        aktionen = self.kampf.verfuegbare_aktionen()
        breite, hoehe, abstand = 280, 50, 12
        spalten = 3
        gesamt_breite = min(len(aktionen), spalten) * breite + (min(len(aktionen), spalten) - 1) * abstand
        start_x = (theme.BREITE - gesamt_breite) // 2
        start_y = theme.HOEHE - 150
        for i, aktion in enumerate(aktionen):
            spalte = i % spalten
            zeile = i // spalten
            rect = (start_x + spalte * (breite + abstand), start_y + zeile * (hoehe + abstand), breite, hoehe)
            if aktion == "Angriff":
                label = "Angriff (Grundangriff)"
            else:
                lvl = self.charakter.gelernte_skills[aktion].level
                aoe = " [Alle Gegner]" if skill_ist_aoe(aktion) else ""
                signatur = " ⭐Signatur" if skill_ist_signatur(aktion) else ""
                label = f"{aktion} (Lv.{lvl}){aoe}{signatur}"
            self.aktions_buttons.append((aktion, Button(rect, label, groesse=17)))

    def _baue_zielbuttons(self, aktion: str, ziel_typ: str):
        self.aktions_buttons = []
        self.ziel_buttons = []
        if ziel_typ == "gegner":
            ziele = self.kampf.gegner_lebend()
            texte = [f"{g.name} - {g.hp}/{g.hp_max} HP" for g in ziele]
        else:
            ziele = self.kampf.verbuendete_lebend()
            texte = [
                (f"Dich selbst ({self.charakter.name}) - HP {self.charakter.hp_aktuell}/{self.charakter.hp_max}" if z is self.charakter
                 else f"{z.name} ({z.rolle}) - HP {z.hp_aktuell}/{z.hp_max}")
                for z in ziele
            ]
        breite, hoehe, abstand = 480, 50, 12
        start_x = (theme.BREITE - breite) // 2
        start_y = theme.HOEHE - 150
        for i, (ziel, text) in enumerate(zip(ziele, texte)):
            rect = (start_x, start_y + i * (hoehe + abstand), breite, hoehe)
            self.ziel_buttons.append((ziel, Button(rect, text, groesse=17)))

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y * 30)
            self._auto_scroll = False
        if self.gewaehlte_aktion is None:
            for aktion, button in self.aktions_buttons:
                if button.handle_event(event):
                    ziel_typ = self.kampf.ziel_typ(aktion)
                    if ziel_typ is None:
                        self._runde(aktion)
                    else:
                        self.gewaehlte_aktion = aktion
                        self._baue_zielbuttons(aktion, ziel_typ)
                    return
        else:
            for ziel, button in self.ziel_buttons:
                if button.handle_event(event):
                    aktion = self.gewaehlte_aktion
                    ziel_typ = self.kampf.ziel_typ(aktion)
                    if ziel_typ == "gegner":
                        self._runde(aktion, gegner_ziel=ziel)
                    else:
                        self._runde(aktion, verbuendeter_ziel=ziel)
                    return

    def _runde(self, aktion, gegner_ziel=None, verbuendeter_ziel=None):
        self.kampf.runde_ausfuehren(aktion, gegner_ziel=gegner_ziel, verbuendeter_ziel=verbuendeter_ziel)
        self._schwebetexte_erzeugen()
        self._auto_scroll = True
        if self.kampf.beendet:
            ergebnis = self.kampf.ergebnis()
            folge = self.kampfstart.bei_abschluss(ergebnis)
            if isinstance(folge, Kampfstart):
                # Ein Dungeon/eine Quest besteht oft aus mehreren Kämpfen in
                # Folge - statt nahtlos in den nächsten Kampf zu wechseln
                # (was sich wie ein automatisches Durchspielen anfühlt),
                # zeigt eine kurze Zwischenmeldung das Ergebnis dieses Kampfes
                # und wartet auf einen bewussten "Weiter"-Klick.
                titel = f"✅ {ergebnis.gegner} besiegt!" if ergebnis.sieg else f"⚠️ Rückzug vor {ergebnis.gegner}"
                naechster_kampfstart = folge

                def weiter_zum_naechsten_kampf():
                    self.app.wechsle_szene(KampfScene(self.app, self.charakter, self.welt, self.ort_titel, naechster_kampfstart, self.ort_id))

                self.app.wechsle_szene(
                    MeldungScene(self.app, titel, "\n".join(ergebnis.log), "Weiter zum nächsten Gegner", weiter_zum_naechsten_kampf, self.ort_id)
                )
            else:
                _starte_ereignis_anzeige(self.app, self.charakter, self.welt, self.ort_titel, folge, self.ort_id)
        else:
            self._baue_aktionsbuttons()

    def draw(self, surface):
        hintergruende.zeichnen(surface, self.ort_id)
        _statusleiste(surface, self.charakter)

        gegner_lebend = self.kampf.gegner_lebend()
        namen = ", ".join(g.name for g in gegner_lebend) if gegner_lebend else ", ".join(g.name for g in self.kampf.gegnergruppe)
        titel = theme.font_titel(24).render(f"⚔️ {namen}", True, theme.FARBEN["akzent_hell"])
        surface.blit(titel, (theme.BREITE // 2 - titel.get_width() // 2, 205))

        y = 236
        for gegner in (gegner_lebend or self.kampf.gegnergruppe):
            hp_text = theme.font(15).render(f"{gegner.name}: {gegner.hp}/{gegner.hp_max} HP", True, theme.FARBEN["text"])
            surface.blit(hp_text, (theme.BREITE // 2 - hp_text.get_width() // 2, y))
            balken_rect = pygame.Rect(theme.BREITE // 2 - 200, y + 18, 400, 12)
            widgets.animierter_balken(surface, balken_rect, (id(gegner), gegner.name, "hp"), gegner.hp / max(1, gegner.hp_max), theme.FARBEN["hp_voll"], theme.FARBEN["hp_leer"])
            y += 34

        # Begleiter-HP links neben den Gegnern - die Statusleiste oben zeigt
        # sie nur als schmale Textzeile, im Kampf selbst braucht man echte
        # Balken, um Heil-/Schutzentscheidungen treffen zu können.
        by = 236
        for begleiter in self.charakter.begleiter:
            ko = begleiter.niedergeschlagen
            zustand = " [K.O.]" if ko else ""
            beg_text = theme.font(15).render(f"{begleiter.name} ({begleiter.rolle}): {begleiter.hp_aktuell}/{begleiter.hp_max} HP{zustand}", True, theme.FARBEN["text_dim"] if ko else theme.FARBEN["text"])
            surface.blit(beg_text, (80, by))
            balken_rect = pygame.Rect(80, by + 18, 260, 12)
            widgets.animierter_balken(surface, balken_rect, (id(begleiter), "hp"), begleiter.hp_aktuell / max(1, begleiter.hp_max), theme.FARBEN["hp_voll"], theme.FARBEN["hp_leer"])
            by += 34

        schwebe_font = theme.font_titel(22)
        for schwebetext in self.schwebetexte:
            schwebetext.draw(surface, schwebe_font)

        widgets.panel(surface, self._textrect, ornament=True)
        innen = self._textrect.inflate(-30, -30)
        log_text = "\n".join(self.kampf.log)
        gesamthoehe = widgets.text_block(surface, log_text, theme.font(16), theme.FARBEN["text"], innen, scroll=self.scroll)
        if self._auto_scroll:
            self.scroll = max(0, gesamthoehe - innen.height)
        self.scroll = max(0, min(self.scroll, max(0, gesamthoehe - innen.height)))

        if self.kampf.beendet:
            warte_label = theme.font(18).render("...", True, theme.FARBEN["text_dim"])
            surface.blit(warte_label, (theme.BREITE // 2 - warte_label.get_width() // 2, theme.HOEHE - 130))
        elif self.gewaehlte_aktion is not None:
            hinweis = theme.font_titel(17).render(f"{self.gewaehlte_aktion} - Ziel wählen:", True, theme.FARBEN["akzent_hell"])
            surface.blit(hinweis, (theme.BREITE // 2 - hinweis.get_width() // 2, theme.HOEHE - 172))
            for _, button in self.ziel_buttons:
                button.draw(surface)
        else:
            for _, button in self.aktions_buttons:
                button.draw(surface)


class MeldungScene(Szene):
    """Generische Anzeige: Titel + scrollbarer Text + ein Weiter-Button, der
    eine übergebene Callback-Funktion aufruft. Wird für Ereignis-Ergebnisse,
    Story-Beats und das Spielende verwendet."""

    def __init__(self, app, titel, text, weiter_text, on_weiter, ort_id=None):
        super().__init__(app)
        self.titel = titel
        self.text = text
        self.ort_id = ort_id
        self.on_weiter = on_weiter
        self.scroll = 0
        self._textrect = pygame.Rect(80, 150, theme.BREITE - 160, theme.HOEHE - 260)
        # Größe passt sich dem Text an ("Weiter" vs. "Weiter zum nächsten
        # Gegner") - ein fester 240px-Button ließ längere Beschriftungen auf
        # drei gequetschte Zeilen umbrechen und über den Rand hinauslaufen.
        knopf_font = theme.font_titel(23, fett=False)
        breite = max(240, min(460, knopf_font.size(weiter_text)[0] + 60))
        zeilen = widgets.zeilenumbruch(weiter_text, knopf_font, breite - 24)
        hoehe = max(56, len(zeilen) * knopf_font.get_linesize() + 20)
        rect = (theme.BREITE // 2 - breite // 2, theme.HOEHE - 30 - hoehe, breite, hoehe)
        self.weiter_button = Button(rect, weiter_text, groesse=23)

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y * 30)
        if self.weiter_button.handle_event(event):
            self.on_weiter()

    def draw(self, surface):
        hintergruende.zeichnen(surface, self.ort_id)
        titel_label = theme.font_titel(30).render(self.titel, True, theme.FARBEN["akzent_hell"])
        surface.blit(titel_label, (80, 60))
        widgets.trennlinie(surface, 80 + titel_label.get_width() // 2, 60 + titel_label.get_height() + 12, breite=min(420, titel_label.get_width() + 60))
        widgets.panel(surface, self._textrect, ornament=True)
        innen = self._textrect.inflate(-40, -40)
        gesamthoehe = widgets.text_block(surface, self.text, theme.font(19), theme.FARBEN["text"], innen, scroll=self.scroll)
        self.scroll = max(0, min(self.scroll, max(0, gesamthoehe - innen.height)))
        self.weiter_button.draw(surface)


class PauseScene(Szene):
    """Über ESC erreichbares Pause-Menü - legt sich als abgedunkelte
    Überlagerung über die eingefrorene Spiel-Szene (die im Hintergrund
    weiter sichtbar, aber nicht mehr interaktiv ist), mit Rückkehr ins
    Spiel, Einstellungen (u.a. Vollbild) und Rückkehr zum Titelbildschirm."""

    pausierbar = False

    def __init__(self, app, spiel_szene):
        super().__init__(app)
        self.spiel_szene = spiel_szene
        self.bestaetige_titel_rueckkehr = False
        self._meldung = ""
        self._meldung_timer = 0.0
        mitte_x = theme.BREITE // 2
        self.fortsetzen_button = Button((mitte_x - 160, 310, 320, 58), "Fortsetzen", groesse=23)
        self.speichern_button = Button((mitte_x - 160, 382, 320, 58), "Speichern", groesse=23)
        self.einstellungen_button = Button((mitte_x - 160, 454, 320, 58), "Einstellungen", groesse=23)
        self.titel_button = Button((mitte_x - 160, 526, 320, 58), "Zum Titelbildschirm", groesse=23)
        self.bestaetigen_button = Button((mitte_x - 210, 470, 200, 52), "Ja, verlassen", groesse=19)
        self.abbrechen_button = Button((mitte_x + 10, 470, 200, 52), "Abbrechen", groesse=19)

    def _charakter_und_welt(self):
        return getattr(self.spiel_szene, "charakter", None), getattr(self.spiel_szene, "welt", None)

    def update(self, dt):
        if self._meldung_timer > 0:
            self._meldung_timer -= dt
            if self._meldung_timer <= 0:
                self._meldung = ""

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.bestaetige_titel_rueckkehr:
                self.bestaetige_titel_rueckkehr = False
            else:
                self.app.wechsle_szene(self.spiel_szene)
            return
        if self.bestaetige_titel_rueckkehr:
            if self.bestaetigen_button.handle_event(event):
                self.app.wechsle_szene(TitleScene(self.app))
            elif self.abbrechen_button.handle_event(event):
                self.bestaetige_titel_rueckkehr = False
            return
        if self.fortsetzen_button.handle_event(event):
            self.app.wechsle_szene(self.spiel_szene)
        elif self.speichern_button.handle_event(event):
            charakter, welt = self._charakter_und_welt()
            if charakter is not None and welt is not None:
                try:
                    savegame.speichern(charakter, welt, slot=charakter.spielstand_slot or "spielstand")
                    self._meldung = "💾 Gespeichert!"
                except OSError:
                    self._meldung = "Speichern fehlgeschlagen."
                self._meldung_timer = 2.0
        elif self.einstellungen_button.handle_event(event):
            self.app.wechsle_szene(EinstellungenScene(self.app, self.spiel_szene))
        elif self.titel_button.handle_event(event):
            self.bestaetige_titel_rueckkehr = True

    def draw(self, surface):
        self.spiel_szene.draw(surface)
        schleier = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        schleier.fill((8, 6, 12, 190))
        surface.blit(schleier, (0, 0))

        panel_rect = pygame.Rect(theme.BREITE // 2 - 260, 195, 520, 410)
        widgets.panel(surface, panel_rect, ornament=True)
        titel = theme.font_dekorativ(34).render("Pause", True, theme.FARBEN["akzent_hell"])
        surface.blit(titel, (theme.BREITE // 2 - titel.get_width() // 2, 222))
        widgets.trennlinie(surface, theme.BREITE // 2, 277, breite=260)

        if self.bestaetige_titel_rueckkehr:
            frage = widgets.zeilenumbruch(
                "Wirklich zum Titelbildschirm? Fortschritt seit dem letzten Ort-Besuch geht verloren.",
                theme.font(17), 440,
            )
            y = 340
            for zeile in frage:
                label = theme.font(17).render(zeile, True, theme.FARBEN["text"])
                surface.blit(label, (theme.BREITE // 2 - label.get_width() // 2, y))
                y += 24
            self.bestaetigen_button.draw(surface)
            self.abbrechen_button.draw(surface)
        else:
            charakter, welt = self._charakter_und_welt()
            self.speichern_button.enabled = charakter is not None and welt is not None
            self.fortsetzen_button.draw(surface)
            self.speichern_button.draw(surface)
            self.einstellungen_button.draw(surface)
            self.titel_button.draw(surface)
            if self._meldung:
                meldung_label = theme.font(16).render(self._meldung, True, theme.FARBEN["erfolg"])
                surface.blit(meldung_label, (theme.BREITE // 2 - meldung_label.get_width() // 2, panel_rect.bottom - 30))


_ANZEIGEMODI = [("fenster", "Fenster"), ("vollbild", "Vollbildschirm"), ("randlos", "Vollbild (randlos)")]
_LAUTSTAERKEN = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
_TEXTGROESSEN = [("normal", "Normal"), ("gross", "Groß")]


class EinstellungenScene(Szene):
    """Einstellungen, erreichbar über das Pause-Menü: Anzeigemodus (Fenster/
    Vollbild/randloses Vollbild-Fenster), Fenstergröße, Musik-Lautstärke und
    Textgröße. Jede Zeile ist ein einzelner Knopf, der ihren Wert bei jedem
    Klick zum nächsten weiterschaltet - alle Werte werden sofort über
    gui.einstellungen persistiert, gelten also auch beim nächsten Start."""

    pausierbar = False

    def __init__(self, app, spiel_szene):
        super().__init__(app)
        self.spiel_szene = spiel_szene
        mitte_x = theme.BREITE // 2
        breite, abstand, hoehe = 460, 68, 58
        start_y = 258
        self.anzeigemodus_button = Button((mitte_x - breite // 2, start_y, breite, hoehe), "", groesse=19)
        self.fenstergroesse_button = Button((mitte_x - breite // 2, start_y + abstand, breite, hoehe), "", groesse=19)
        self.musik_button = Button((mitte_x - breite // 2, start_y + abstand * 2, breite, hoehe), "", groesse=19)
        self.textgroesse_button = Button((mitte_x - breite // 2, start_y + abstand * 3, breite, hoehe), "", groesse=19)
        self.zurueck_button = Button((mitte_x - 160, start_y + abstand * 4 + 12, 320, 54), "◀ Zurück", groesse=21)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.wechsle_szene(PauseScene(self.app, self.spiel_szene))
            return
        einst = self.app.einstellungen
        if self.anzeigemodus_button.handle_event(event):
            werte = [w for w, _ in _ANZEIGEMODI]
            naechster = werte[(werte.index(einst["anzeigemodus"]) + 1) % len(werte)]
            self.app.anzeigemodus_setzen(naechster)
        elif self.fenstergroesse_button.handle_event(event) and einst["anzeigemodus"] == "fenster":
            aktuelle = tuple(einst["fenstergroesse"])
            groessen = einstellungen.FENSTERGROESSEN
            idx = groessen.index(aktuelle) if aktuelle in groessen else 0
            self.app.fenstergroesse_setzen(groessen[(idx + 1) % len(groessen)])
        elif self.musik_button.handle_event(event):
            idx = min(range(len(_LAUTSTAERKEN)), key=lambda i: abs(_LAUTSTAERKEN[i] - einst["musik_lautstaerke"]))
            self.app.musik_lautstaerke_setzen(_LAUTSTAERKEN[(idx + 1) % len(_LAUTSTAERKEN)])
        elif self.textgroesse_button.handle_event(event):
            werte = [w for w, _ in _TEXTGROESSEN]
            naechster = werte[(werte.index(einst["textgroesse"]) + 1) % len(werte)]
            self.app.textgroesse_setzen(naechster)
        elif self.zurueck_button.handle_event(event):
            self.app.wechsle_szene(PauseScene(self.app, self.spiel_szene))

    def draw(self, surface):
        self.spiel_szene.draw(surface)
        schleier = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        schleier.fill((8, 6, 12, 190))
        surface.blit(schleier, (0, 0))

        panel_rect = pygame.Rect(theme.BREITE // 2 - 280, 165, 560, 480)
        widgets.panel(surface, panel_rect, ornament=True)
        titel = theme.font_dekorativ(30).render("Einstellungen", True, theme.FARBEN["akzent_hell"])
        surface.blit(titel, (theme.BREITE // 2 - titel.get_width() // 2, 195))
        widgets.trennlinie(surface, theme.BREITE // 2, 242, breite=280)

        einst = self.app.einstellungen
        anzeigemodus_name = dict(_ANZEIGEMODI)[einst["anzeigemodus"]]
        self.anzeigemodus_button.text = f"Anzeigemodus: {anzeigemodus_name}"
        self.anzeigemodus_button.draw(surface)

        breite, hoehe = einst["fenstergroesse"]
        self.fenstergroesse_button.text = f"Fenstergröße: {breite}×{hoehe}"
        self.fenstergroesse_button.enabled = einst["anzeigemodus"] == "fenster"
        self.fenstergroesse_button.subtitle = None if self.fenstergroesse_button.enabled else "nur im Fenstermodus wählbar"
        self.fenstergroesse_button.subtitle_font = theme.font(13)
        self.fenstergroesse_button.draw(surface)

        self.musik_button.text = f"Musik-Lautstärke: {round(einst['musik_lautstaerke'] * 100)}%"
        self.musik_button.draw(surface)

        textgroesse_name = dict(_TEXTGROESSEN)[einst["textgroesse"]]
        self.textgroesse_button.text = f"Textgröße: {textgroesse_name}"
        self.textgroesse_button.draw(surface)

        self.zurueck_button.draw(surface)

        hinweis = theme.font(13).render("F11 wirkt als Kurzbefehl für Fenster/Vollbildschirm jederzeit ebenso.", True, theme.FARBEN["text_dim"])
        surface.blit(hinweis, (theme.BREITE // 2 - hinweis.get_width() // 2, self.zurueck_button.rect.bottom + 16))


def _starte_ereignis_anzeige(app, charakter, welt, ort_titel, ereignis, ort_id=None):
    text, gestorben = spiellauf.verarbeite_ereignis(charakter, ereignis)
    icon = "💥 " if ereignis.ist_wichtig else ""

    def weiter():
        if gestorben:
            _zeige_ende(app, charakter, welt, "tod")
            return

        if ereignis.beendet_tag:
            zusatztext = spiellauf.tagesende(charakter, welt)
        else:
            if ereignis.kostet_aktion:
                charakter.aktionen_uebrig = max(0, charakter.aktionen_uebrig - 1)
            zusatztext = ""

        ende_grund = spiellauf.pruefe_spielende(charakter)
        if zusatztext.strip():
            app.wechsle_szene(
                MeldungScene(app, "📅 Der Tag geht weiter", zusatztext, "Weiter", lambda: _nach_tagesende(app, charakter, welt, ende_grund), ort_id)
            )
        else:
            _nach_tagesende(app, charakter, welt, ende_grund)

    app.wechsle_szene(MeldungScene(app, f"{icon}{ort_titel}", text, "Weiter", weiter, ort_id))


def _nach_tagesende(app, charakter, welt, ende_grund):
    if ende_grund:
        _zeige_ende(app, charakter, welt, ende_grund)
    else:
        app.wechsle_szene(HubScene(app, charakter, welt))


def _zeige_ende(app, charakter, welt, grund):
    ende_text = erzeuge_ende(charakter, welt, grund)
    app.wechsle_szene(MeldungScene(app, "📖 Das Ende deiner Geschichte", ende_text, "Zum Titelbildschirm", lambda: app.wechsle_szene(TitleScene(app)), "titel"))

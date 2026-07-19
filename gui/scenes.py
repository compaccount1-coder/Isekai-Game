"""Alle Bildschirme (Szenen) der grafischen Oberfläche: Titel, Charakter-
erstellung, Haupt-Hub, Ort-Menüs und Ergebnis-/Ende-Anzeigen."""

import random

import pygame

from game import locations as locations_module
from game import savegame
from gui import hintergruende, orte, spiellauf, theme, widgets
from game.character import MAX_AKTIONEN_PRO_TAG, Charakter
from game.classes import KLASSEN, skill_ist_aoe, skill_ist_signatur
from game.combat import Kampfstart
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
        beg_text = " | ".join(
            f"{b.name} (Lv.{b.level} {b.rolle}) HP {b.hp_aktuell}/{b.hp_max}{' [K.O.]' if b.niedergeschlagen else ''}"
            for b in charakter.begleiter
        )
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
        surface.blit(hintergruende.hintergrund_fuer("titel"), (0, 0))
        titel = theme.font(60, fett=True).render("ISEKAI CHRONICLES", True, theme.FARBEN["akzent"])
        surface.blit(titel, (theme.BREITE // 2 - titel.get_width() // 2, 210))
        untertitel = theme.font(20).render("Eine Geschichte voller unendlicher Möglichkeiten", True, theme.FARBEN["text_dim"])
        surface.blit(untertitel, (theme.BREITE // 2 - untertitel.get_width() // 2, 300))
        self.neues_spiel_button.draw(surface)
        self.fortsetzen_button.draw(surface)
        self.beenden_button.draw(surface)
        hinweis = theme.font(14).render("F11 = Vollbild an/aus", True, theme.FARBEN["text_dim"])
        surface.blit(hinweis, (theme.BREITE - hinweis.get_width() - 20, theme.HOEHE - 32))


class CharErstellungScene(Szene):
    def __init__(self, app):
        super().__init__(app)
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
        surface.blit(hintergruende.hintergrund_fuer("titel"), (0, 0))
        titel = theme.font(28, fett=True).render("Wähle deinen Weg in dieser neuen Welt", True, theme.FARBEN["akzent"])
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
        surface.blit(hintergruende.hintergrund_fuer("hub"), (0, 0))
        _statusleiste(surface, self.charakter)
        if self.charakter.aktionen_uebrig <= 0:
            kopf_text = f"😴 {self.charakter.name} ist erschöpft - Zeit, in der Taverne zu schlafen."
        else:
            kopf_text = f"Wohin geht {self.charakter.name}? (Aktionen übrig: {self.charakter.aktionen_uebrig}/{MAX_AKTIONEN_PRO_TAG})"
        kopf = theme.font(24).render(kopf_text, True, theme.FARBEN["text"])
        surface.blit(kopf, (theme.BREITE // 2 - kopf.get_width() // 2, 205))
        for button in self.buttons:
            button.draw(surface)


class OrtScene(Szene):
    """Zeigt die Options-Buttons eines Ortes (oder Untermenüs davon) an und
    löst die gewählte Aktion aus - entweder ein weiteres Untermenü oder ein
    Ereignis, das dann zur Anzeige/Tagesabschluss-Kette übergeben wird."""

    def __init__(self, app, charakter, welt, titel, optionen, ort_id, zurueck=None):
        super().__init__(app)
        self.charakter = charakter
        self.welt = welt
        self.titel = titel
        self.optionen = optionen
        self.ort_id = ort_id
        self.zurueck = zurueck
        self.buttons: list[Button] = []
        self.zurueck_button: Button | None = None
        self._baue_buttons()

    def _baue_buttons(self):
        self.buttons = []
        y = 230
        breite = 820
        hoehe_min = 54
        abstand = 12
        x = (theme.BREITE - breite) // 2
        font = theme.font(19)
        for label, _ in self.optionen:
            # Lange Beschreibungen (z.B. Quest-Einträge) brauchen mehr als
            # eine Zeile - die Button-Höhe richtet sich danach, damit der
            # Text nicht über den Rand hinaus clippt.
            zeilen = widgets.zeilenumbruch(label, font, breite - 24)
            hoehe = max(hoehe_min, len(zeilen) * font.get_linesize() + 16)
            rect = (x, y, breite, hoehe)
            self.buttons.append(Button(rect, label, groesse=19))
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
        _, aktion = self.optionen[idx]
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
        surface.blit(hintergruende.hintergrund_fuer(self.ort_id), (0, 0))
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


class KampfScene(Szene):
    """Interaktive Kampfanzeige: der Spieler wählt jede Runde selbst die
    Fähigkeit seines Charakters über Buttons, statt dass der Kampf automatisch
    abläuft. Mehrere Kämpfe in Folge (z.B. ein Dungeon) werden durch Verketten
    weiterer KampfScene-Instanzen über bei_abschluss abgebildet."""

    def __init__(self, app, charakter, welt, ort_titel, kampfstart, ort_id=None):
        super().__init__(app)
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
        self._baue_aktionsbuttons()

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
        surface.blit(hintergruende.hintergrund_fuer(self.ort_id), (0, 0))
        _statusleiste(surface, self.charakter)

        gegner_lebend = self.kampf.gegner_lebend()
        namen = ", ".join(g.name for g in gegner_lebend) if gegner_lebend else ", ".join(g.name for g in self.kampf.gegnergruppe)
        titel = theme.font(24, fett=True).render(f"⚔️ {namen}", True, theme.FARBEN["akzent"])
        surface.blit(titel, (theme.BREITE // 2 - titel.get_width() // 2, 205))

        y = 236
        for gegner in (gegner_lebend or self.kampf.gegnergruppe):
            hp_text = theme.font(15).render(f"{gegner.name}: {gegner.hp}/{gegner.hp_max} HP", True, theme.FARBEN["text"])
            surface.blit(hp_text, (theme.BREITE // 2 - hp_text.get_width() // 2, y))
            balken_rect = pygame.Rect(theme.BREITE // 2 - 200, y + 18, 400, 12)
            widgets.balken(surface, balken_rect, gegner.hp / max(1, gegner.hp_max), theme.FARBEN["hp_voll"], theme.FARBEN["hp_leer"])
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
            widgets.balken(surface, balken_rect, begleiter.hp_aktuell / max(1, begleiter.hp_max), theme.FARBEN["hp_voll"], theme.FARBEN["hp_leer"])
            by += 34

        widgets.panel(surface, self._textrect)
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
            hinweis = theme.font(17).render(f"{self.gewaehlte_aktion} - Ziel wählen:", True, theme.FARBEN["akzent"])
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
        self.weiter_button = Button((theme.BREITE // 2 - 120, theme.HOEHE - 86, 240, 56), weiter_text, groesse=23)

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, self.scroll - event.y * 30)
        if self.weiter_button.handle_event(event):
            self.on_weiter()

    def draw(self, surface):
        surface.blit(hintergruende.hintergrund_fuer(self.ort_id), (0, 0))
        titel_label = theme.font(30, fett=True).render(self.titel, True, theme.FARBEN["akzent"])
        surface.blit(titel_label, (80, 60))
        widgets.panel(surface, self._textrect)
        innen = self._textrect.inflate(-40, -40)
        gesamthoehe = widgets.text_block(surface, self.text, theme.font(19), theme.FARBEN["text"], innen, scroll=self.scroll)
        self.scroll = max(0, min(self.scroll, max(0, gesamthoehe - innen.height)))
        self.weiter_button.draw(surface)


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

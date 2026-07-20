"""Haupt-Anwendung: Fenster, Spielschleife und Szenenwechsel."""

import pygame

from game import savegame
from gui import einstellungen, musik, theme

# Zusätzlich zum ereignisgesteuerten Autosave (bei jedem Hub-Besuch, siehe
# HubScene) sichert diese Zeitspanne auch lange, ununterbrochene Abschnitte
# außerhalb des Hubs ab (z.B. einen langen Dungeon-Lauf) - lang genug, um
# nicht bei jeder Combat-Runde unnötig auf die Platte zu schreiben, kurz
# genug, dass im Ernstfall nie viel Fortschritt verloren geht.
AUTOSAVE_INTERVALL_SEKUNDEN = 180.0

# Kurze Abblende beim Szenenwechsel statt eines harten Schnitts - bewusst
# knapp gehalten, damit sich die vielen Menüwechsel in diesem Spiel trotzdem
# noch reaktionsschnell anfühlen und nicht zäh wirken.
FADE_DAUER_SEKUNDEN = 0.14


class App:
    """Zeichnet jede Szene auf eine feste logische Fläche (theme.BREITE x
    theme.HOEHE) und skaliert diese danach auf das tatsächliche Fenster bzw.
    den Bildschirm - so funktionieren Vollbild, randloses Vollbild-Fenster
    und Fenster-Größenänderung, ohne dass jede Szene ihr Layout selbst
    anpassen müsste. Mausereignisse werden dafür von physischen Fenster-
    zurück in logische Koordinaten umgerechnet, bevor sie an die aktuelle
    Szene weitergereicht werden. Anzeige-/Audio-Einstellungen werden beim
    Start geladen (siehe gui.einstellungen) und bei jeder Änderung sofort
    wieder gespeichert."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Isekai Chronicles")
        self.logische_flaeche = pygame.Surface((theme.BREITE, theme.HOEHE))
        self.einstellungen = einstellungen.laden()
        self.fenster = None
        self._anzeigemodus_anwenden()
        theme.TEXT_SKALA = 1.15 if self.einstellungen["textgroesse"] == "gross" else 1.0
        musik.init()
        musik.lautstaerke_setzen(self.einstellungen["musik_lautstaerke"])
        self.clock = pygame.time.Clock()
        self.laeuft = True
        self.szene = None
        self._autosave_timer = 0.0
        self._naechste_szene = None
        self._fade = 0.0
        self._fade_ausblenden = False

    # -- Anzeige-Einstellungen -------------------------------------------

    def _anzeigemodus_anwenden(self):
        modus = self.einstellungen["anzeigemodus"]
        if modus == "vollbild":
            self.fenster = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        elif modus == "randlos":
            info = pygame.display.Info()
            self.fenster = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
        else:
            breite, hoehe = self.einstellungen["fenstergroesse"]
            self.fenster = pygame.display.set_mode((breite, hoehe), pygame.RESIZABLE)

    def anzeigemodus_setzen(self, modus: str):
        self.einstellungen["anzeigemodus"] = modus
        self._anzeigemodus_anwenden()
        einstellungen.speichern(self.einstellungen)

    def fenstergroesse_setzen(self, groesse: tuple[int, int]):
        self.einstellungen["fenstergroesse"] = list(groesse)
        if self.einstellungen["anzeigemodus"] == "fenster":
            self._anzeigemodus_anwenden()
        einstellungen.speichern(self.einstellungen)

    def musik_lautstaerke_setzen(self, wert: float):
        self.einstellungen["musik_lautstaerke"] = wert
        musik.lautstaerke_setzen(wert)
        einstellungen.speichern(self.einstellungen)

    def textgroesse_setzen(self, wert: str):
        self.einstellungen["textgroesse"] = wert
        theme.TEXT_SKALA = 1.15 if wert == "gross" else 1.0
        einstellungen.speichern(self.einstellungen)

    def vollbild_umschalten(self):
        """Kurzbefehl (F11): schaltet nur zwischen Fenster und echtem
        Vollbild um - die volle Auswahl (inkl. randlosem Vollbild-Fenster
        und Fenstergrößen) steht im Einstellungen-Bildschirm bereit."""
        neuer_modus = "fenster" if self.einstellungen["anzeigemodus"] == "vollbild" else "vollbild"
        self.anzeigemodus_setzen(neuer_modus)

    # -- Skalierung/Koordinatenumrechnung ---------------------------------

    def _skalierung(self):
        fenster_breite, fenster_hoehe = self.fenster.get_size()
        skala = max(0.01, min(fenster_breite / theme.BREITE, fenster_hoehe / theme.HOEHE))
        ziel_breite, ziel_hoehe = int(theme.BREITE * skala), int(theme.HOEHE * skala)
        offset_x = (fenster_breite - ziel_breite) // 2
        offset_y = (fenster_hoehe - ziel_hoehe) // 2
        return skala, offset_x, offset_y, ziel_breite, ziel_hoehe

    def _physisch_zu_logisch(self, pos):
        skala, offset_x, offset_y, _, _ = self._skalierung()
        return ((pos[0] - offset_x) / skala, (pos[1] - offset_y) / skala)

    # -- Szenen-/Spielschleife --------------------------------------------

    def wechsle_szene(self, neue_szene):
        """Wechselt zur neuen Szene über eine kurze Abblende (siehe
        _fade_aktualisieren) statt eines harten Schnitts. Die allererste
        Szene (self.szene ist noch None) erscheint ohne Überblendung."""
        if self.szene is None:
            self.szene = neue_szene
            return
        self._naechste_szene = neue_szene
        self._fade_ausblenden = True

    def _fade_aktualisieren(self, dt):
        if not self._fade_ausblenden and self._fade <= 0.0:
            return
        schritt = dt / FADE_DAUER_SEKUNDEN
        if self._fade_ausblenden:
            self._fade = min(1.0, self._fade + schritt)
            if self._fade >= 1.0 and self._naechste_szene is not None:
                self.szene = self._naechste_szene
                self._naechste_szene = None
                self._fade_ausblenden = False
        else:
            self._fade = max(0.0, self._fade - schritt)

    def starten(self, erste_szene):
        self.szene = erste_szene
        while self.laeuft:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.laeuft = False
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.vollbild_umschalten()
                    continue
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    # Pause-Menü: nur Szenen, die sich selbst als pausierbar
                    # markieren (siehe Szene.pausierbar), lösen es aus - das
                    # Pause-Menü selbst regelt ESC (zurück/weiter) eigenständig.
                    if getattr(self.szene, "pausierbar", False):
                        from gui.scenes import PauseScene
                        self.szene = PauseScene(self, self.szene)
                        continue
                if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                    event = pygame.event.Event(event.type, {**event.dict, "pos": self._physisch_zu_logisch(event.pos)})
                self.szene.handle_event(event)
            if not self.laeuft:
                break
            self.szene.update(dt)
            self._autosave_pruefen(dt)
            self._fade_aktualisieren(dt)
            musik.aktualisieren()
            self.logische_flaeche.fill(theme.FARBEN["hintergrund"])
            self.szene.draw(self.logische_flaeche)
            if self._fade > 0.0:
                schleier = pygame.Surface((theme.BREITE, theme.HOEHE), pygame.SRCALPHA)
                schleier.fill((0, 0, 0, int(255 * self._fade)))
                self.logische_flaeche.blit(schleier, (0, 0))
            self._praesentieren()
        pygame.quit()

    def _autosave_pruefen(self, dt):
        self._autosave_timer += dt
        if self._autosave_timer < AUTOSAVE_INTERVALL_SEKUNDEN:
            return
        self._autosave_timer = 0.0
        charakter = getattr(self.szene, "charakter", None)
        welt = getattr(self.szene, "welt", None)
        if charakter is None or welt is None:
            return
        try:
            savegame.speichern(charakter, welt, slot=charakter.spielstand_slot or "spielstand")
        except OSError:
            pass

    def _praesentieren(self):
        skala, offset_x, offset_y, ziel_breite, ziel_hoehe = self._skalierung()
        self.fenster.fill((0, 0, 0))
        skaliert = pygame.transform.smoothscale(self.logische_flaeche, (ziel_breite, ziel_hoehe))
        self.fenster.blit(skaliert, (offset_x, offset_y))
        pygame.display.flip()

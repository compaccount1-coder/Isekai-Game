"""Haupt-Anwendung: Fenster, Spielschleife und Szenenwechsel."""

import pygame

from gui import theme


class App:
    """Zeichnet jede Szene auf eine feste logische Fläche (theme.BREITE x
    theme.HOEHE) und skaliert diese danach auf das tatsächliche Fenster bzw.
    den Bildschirm - so funktionieren Vollbild und Fenster-Größenänderung,
    ohne dass jede Szene ihr Layout selbst anpassen müsste. Mausereignisse
    werden dafür von physischen Fenster- zurück in logische Koordinaten
    umgerechnet, bevor sie an die aktuelle Szene weitergereicht werden."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Isekai Chronicles")
        self.logische_flaeche = pygame.Surface((theme.BREITE, theme.HOEHE))
        self.fenster = pygame.display.set_mode((theme.BREITE, theme.HOEHE), pygame.RESIZABLE)
        self.vollbild = False
        self.clock = pygame.time.Clock()
        self.laeuft = True
        self.szene = None

    def vollbild_umschalten(self):
        self.vollbild = not self.vollbild
        if self.vollbild:
            self.fenster = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.fenster = pygame.display.set_mode((theme.BREITE, theme.HOEHE), pygame.RESIZABLE)

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

    def wechsle_szene(self, neue_szene):
        self.szene = neue_szene

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
            self.logische_flaeche.fill(theme.FARBEN["hintergrund"])
            self.szene.draw(self.logische_flaeche)
            self._praesentieren()
        pygame.quit()

    def _praesentieren(self):
        skala, offset_x, offset_y, ziel_breite, ziel_hoehe = self._skalierung()
        self.fenster.fill((0, 0, 0))
        skaliert = pygame.transform.smoothscale(self.logische_flaeche, (ziel_breite, ziel_hoehe))
        self.fenster.blit(skaliert, (offset_x, offset_y))
        pygame.display.flip()

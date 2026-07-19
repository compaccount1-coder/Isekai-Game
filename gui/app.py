"""Haupt-Anwendung: Fenster, Spielschleife und Szenenwechsel."""

import pygame

from gui import theme


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Isekai Chronicles")
        self.surface = pygame.display.set_mode((theme.BREITE, theme.HOEHE))
        self.clock = pygame.time.Clock()
        self.laeuft = True
        self.szene = None

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
                self.szene.handle_event(event)
            if not self.laeuft:
                break
            self.szene.update(dt)
            self.surface.fill(theme.FARBEN["hintergrund"])
            self.szene.draw(self.surface)
            pygame.display.flip()
        pygame.quit()

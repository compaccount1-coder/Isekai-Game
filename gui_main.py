#!/usr/bin/env python3
"""Grafischer Einstiegspunkt für Isekai Chronicles (Pygame-Oberfläche).
Nutzt dieselbe Spiellogik wie main.py (game/*), nur mit einem echten
Fenster statt Terminal-Eingaben."""

from gui.app import App
from gui.scenes import TitleScene


def main():
    app = App()
    app.starten(TitleScene(app))


if __name__ == "__main__":
    main()

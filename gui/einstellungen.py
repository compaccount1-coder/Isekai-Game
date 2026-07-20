"""Persistente Anzeige-/Audio-Einstellungen (Anzeigemodus, Fenstergröße,
Musik-Lautstärke, Textgröße) - unabhängig vom Spielstand, gilt geräteweit
statt pro Charakter. Liegt im selben "saves"-Ordner wie Spielstände (siehe
game.savegame), der bereits von git ignoriert wird."""

import json
import os

_ORDNER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")
_PFAD = os.path.join(_ORDNER, "einstellungen.json")

FENSTERGROESSEN = [(1280, 800), (1600, 1000), (1920, 1200)]

STANDARD = {
    "anzeigemodus": "fenster",  # "fenster" | "vollbild" | "randlos"
    "fenstergroesse": [1280, 800],
    "musik_lautstaerke": 0.5,
    "textgroesse": "normal",  # "normal" | "gross"
}


def laden() -> dict:
    if not os.path.exists(_PFAD):
        return dict(STANDARD)
    try:
        with open(_PFAD, "r", encoding="utf-8") as f:
            daten = json.load(f)
        ergebnis = dict(STANDARD)
        ergebnis.update({k: v for k, v in daten.items() if k in STANDARD})
        return ergebnis
    except (OSError, ValueError, json.JSONDecodeError):
        return dict(STANDARD)


def speichern(werte: dict) -> None:
    try:
        os.makedirs(_ORDNER, exist_ok=True)
        with open(_PFAD, "w", encoding="utf-8") as f:
            json.dump(werte, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

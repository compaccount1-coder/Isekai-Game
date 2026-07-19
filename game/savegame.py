"""Speicherstand-System: JSON-Serialisierung von Charakter und Welt. Da beide
(und alle enthaltenen Typen wie Item, Trank, Begleiter, Königreich) einfache
Dataclasses aus Grundtypen sind, lässt sich das Speichern generisch über
dataclasses.asdict() lösen - für das Laden wird die Struktur gezielt wieder
in die richtigen Dataclass-Typen zurückgebaut."""

import json
import os
from dataclasses import asdict

from game.character import Charakter, GelernterSkill
from game.companions import Begleiter
from game.items import Item, Trank
from game.world import Koenigreich, Stadt, Welt

SPEICHER_ORDNER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")


def _item_aus_dict(d: dict | None) -> Item | None:
    return Item(**d) if d else None


def _stadt_aus_dict(d: dict) -> Stadt:
    return Stadt(**d)


def _koenigreich_aus_dict(d: dict) -> Koenigreich:
    d = dict(d)
    d["weitere_staedte"] = [_stadt_aus_dict(s) for s in d["weitere_staedte"]]
    return Koenigreich(**d)


def _welt_aus_dict(d: dict) -> Welt:
    return Welt(
        koenigreiche=[_koenigreich_aus_dict(k) for k in d["koenigreiche"]],
        alle_gilden=d["alle_gilden"],
    )


def _charakter_aus_dict(d: dict) -> Charakter:
    d = dict(d)
    d["inventar"] = [_item_aus_dict(i) for i in d["inventar"]]
    d["waffe"] = _item_aus_dict(d["waffe"])
    d["ruestung"] = _item_aus_dict(d["ruestung"])
    d["accessoire"] = _item_aus_dict(d["accessoire"])
    d["begleiter"] = [Begleiter(**b) for b in d["begleiter"]]
    d["traenke"] = [Trank(**t) for t in d["traenke"]]
    d["gelernte_skills"] = {k: GelernterSkill(**v) for k, v in d["gelernte_skills"].items()}
    return Charakter(**d)


def speicherpfad(slot: str = "spielstand") -> str:
    os.makedirs(SPEICHER_ORDNER, exist_ok=True)
    return os.path.join(SPEICHER_ORDNER, f"{slot}.json")


def speichern(charakter: Charakter, welt: Welt, slot: str = "spielstand") -> None:
    daten = {"charakter": asdict(charakter), "welt": asdict(welt)}
    with open(speicherpfad(slot), "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)


def laden(slot: str = "spielstand") -> tuple[Charakter, Welt]:
    with open(speicherpfad(slot), "r", encoding="utf-8") as f:
        daten = json.load(f)
    return _charakter_aus_dict(daten["charakter"]), _welt_aus_dict(daten["welt"])


def spielstand_vorhanden(slot: str = "spielstand") -> bool:
    return os.path.exists(speicherpfad(slot))


def spielstand_loeschen(slot: str = "spielstand") -> None:
    pfad = speicherpfad(slot)
    if os.path.exists(pfad):
        os.remove(pfad)


def alle_spielstaende() -> list[str]:
    if not os.path.isdir(SPEICHER_ORDNER):
        return []
    return sorted(f[:-5] for f in os.listdir(SPEICHER_ORDNER) if f.endswith(".json"))

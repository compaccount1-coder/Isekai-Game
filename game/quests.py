"""Quest-System: Vielfältige Aufträge vom Gildenbrett, skaliert nach Abenteurer-Rang."""

import random
from dataclasses import dataclass

from game.combat import Kampfstart, erwartete_kampfkraft, kampf_starten, zufaelliger_gegner
from game.events import Ereignis
from game.items import generiere_item
from game.ranks import RANG_MULTIPLIKATOR, RANG_REIHENFOLGE
from game.world import Welt

QUEST_ORTE = [
    "den nahen Wäldern", "der verlassenen Mine", "den Sümpfen im Süden", "dem alten Steinbruch",
    "den Handelsrouten", "der Grenzregion", "den Ruinen am Fluss", "dem Bergpass",
]

QUEST_VORLAGEN = {
    "Jagd": [
        "Erlege die Kreatur, die {ort} unsicher macht",
        "Räume ein Monsternest in {ort} aus",
        "Jage einen Wiederkehrer, der Reisende in {ort} überfällt",
    ],
    "Eskorte": [
        "Begleite einen Händlerkonvoi sicher durch {ort}",
        "Eskortiere einen Gesandten nach {ort}",
        "Beschütze eine Pilgergruppe auf dem Weg durch {ort}",
    ],
    "Bergung": [
        "Bringe ein verlorenes Familienerbstück aus {ort} zurück",
        "Berge wichtige Fracht aus einem havarierten Wagen bei {ort}",
        "Finde ein vermisstes Gildenmitglied in {ort}",
    ],
    "Untersuchung": [
        "Untersuche mysteriöse Vorfälle in {ort}",
        "Finde die Ursache für das Verschwinden von Vieh nahe {ort}",
        "Kläre einen Vorfall auf, den die Wachen in {ort} nicht lösen konnten",
    ],
    "Ausrottung": [
        "Vernichte ein wachsendes Monsterlager in {ort}",
        "Beende die Plage, die {ort} heimsucht",
        "Vertreibe eine Räuberbande aus {ort}",
    ],
}

QUEST_TYP_GEFAHR = {"Jagd": 0.85, "Eskorte": 0.55, "Bergung": 0.5, "Untersuchung": 0.45, "Ausrottung": 1.05}


@dataclass
class Quest:
    titel: str
    typ: str
    rang: str
    belohnung_gold: int
    belohnung_xp: int
    gefahr_faktor: float


def generiere_quest(rang: str) -> Quest:
    typ = random.choice(list(QUEST_VORLAGEN.keys()))
    vorlage = random.choice(QUEST_VORLAGEN[typ])
    titel = vorlage.format(ort=random.choice(QUEST_ORTE))

    mult = RANG_MULTIPLIKATOR[rang]
    belohnung_gold = int(random.randint(15, 35) * mult)
    belohnung_xp = int(random.randint(20, 40) * mult)

    return Quest(
        titel=titel, typ=typ, rang=rang,
        belohnung_gold=belohnung_gold, belohnung_xp=belohnung_xp,
        gefahr_faktor=QUEST_TYP_GEFAHR[typ],
    )


def generiere_quest_brett(charakter_rang: str, anzahl: int = 5) -> list[Quest]:
    """Erzeugt ein Quest-Brett - Quests bis zum eigenen Rang, mit Schwerpunkt
    auf dem aktuellen Rang. Abenteurer können nur Quests ihres eigenen Rangs
    oder darunter annehmen."""
    max_idx = RANG_REIHENFOLGE.index(charakter_rang)
    verfuegbare_raenge = RANG_REIHENFOLGE[: max_idx + 1]
    quests = []
    for _ in range(anzahl):
        # Deutliches Übergewicht auf dem eigenen Rang, aber auch niedrigere möglich
        if len(verfuegbare_raenge) > 1 and random.random() < 0.35:
            rang = random.choice(verfuegbare_raenge[:-1])
        else:
            rang = verfuegbare_raenge[-1]
        quests.append(generiere_quest(rang))
    return quests


def quest_abschliessen(charakter, quest: Quest) -> "Ereignis | Kampfstart":
    """Löst eine Quest auf - über eine Kampfbegegnung, skaliert nach
    Gefahr-Faktor des Quest-Typs. Gibt entweder direkt ein Ereignis zurück
    (z.B. wenn der Charakter gar nicht mehr antreten kann) oder einen
    Kampfstart, dessen Abschluss-Callback das endgültige Ereignis liefert."""
    basis_staerke = erwartete_kampfkraft(charakter.level)
    staerke = int(basis_staerke * quest.gefahr_faktor * random.uniform(0.65, 0.95))
    gegner_name, _ = zufaelliger_gegner(charakter.level)
    intro = f"📜 {charakter.name} macht sich auf: \"{quest.titel}\" ({quest.typ}, Rang {quest.rang})."

    if not charakter.lebendig:
        return Ereignis(text="Die Quest kann nicht angetreten werden.")

    kampf = kampf_starten(charakter, gegner_name, staerke)

    def bei_abschluss(ergebnis):
        log = [intro] + ergebnis.log
        if not charakter.lebendig:
            log.append("Die Quest endet in einer Katastrophe...")
            return Ereignis(text=f"Quest gescheitert: {quest.titel}", log=log)

        if ergebnis.sieg:
            charakter.gold += quest.belohnung_gold
            meldungen = charakter.xp_hinzufuegen(quest.belohnung_xp)
            charakter.abgeschlossene_quests += 1
            charakter.ruf += int(3 * RANG_MULTIPLIKATOR[quest.rang] / 2)
            log.append(f"✅ Quest erfüllt! Belohnung: {quest.belohnung_gold}g, {quest.belohnung_xp} XP.")
            log.extend(meldungen)
            if random.random() < 0.15 + 0.03 * RANG_REIHENFOLGE.index(quest.rang):
                item = generiere_item(charakter.level)
                log.append(charakter.fund_verarbeiten(item))
            return Ereignis(text=f"Quest erfolgreich: {quest.titel}", log=log, ist_wichtig=True)
        else:
            log.append(f"❌ Quest gescheitert: {quest.titel} war zu gefährlich.")
            return Ereignis(text=f"Quest gescheitert: {quest.titel}", log=log)

    return Kampfstart(kampf, bei_abschluss)

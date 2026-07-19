"""Baut die Options-Listen für jeden Ort auf Basis der bestehenden Spiellogik
in game.locations - die GUI übernimmt nur die Auswahl-Oberfläche (Buttons statt
Zahlen-Eingabe), die eigentlichen Ereignisse entstehen weiterhin in game.*."""

import random
from dataclasses import dataclass
from typing import Callable

from game.classes import KLASSEN, TANK_PFADE
from game.endgame import (
    daemonenjagd_verfuegbar,
    demonenkoenig_verfuegbar,
    jage_daemonenfuersten,
    konfrontiere_daemonenkoenig,
    verbleibende_fuersten,
)
from game.events import Ereignis, ereignis_dungeon, ereignis_gilde, zufallsereignis
from game.items import generiere_trank, schmiede_upgrade
from game.locations import (
    ORTE,
    TAVERNEN_NAMEN,
    _adel_audienz,
    _adel_intrige,
    _gilde_klatsch,
    _markt_anwesen_kaufen,
    _markt_feilschen,
    _markt_kutsche_kaufen,
    _markt_verkaufen,
    _rangaufstieg_pruefung,
    _taverne_ausruhen,
    _taverne_geruecht,
    _taverne_gruppenangebot,
    _taverne_trinkspiel,
    _tempel_priester,
    _tempel_segen,
    _tempel_spende,
    _wildnis_erkunden,
    _wildnis_reisende,
)
from game.quests import generiere_quest_brett, quest_abschliessen
from game.ranks import kann_aufsteigen, naechster_rang

Aktion = Callable[[], "Ereignis | Submenu"]


@dataclass
class Submenu:
    """Wird von einer Options-Aktion zurückgegeben, wenn eine weitere
    Auswahlebene nötig ist (z.B. welcher Trank, welche Quest, welcher
    Dämonenfürst), statt direkt ein Ereignis zu erzeugen."""
    titel: str
    optionen: list[tuple[str, Aktion]]


ORT_BESCHREIBUNGEN = {
    "taverne": "Ausruhen, Gerüchte hören, eine Gruppe finden",
    "marktplatz": "Handeln, Tränke, Anwesen, Kutsche",
    "gildenviertel": "Quest-Brett, Rangaufstieg, Klatsch",
    "wildnis": "Erkunden, kämpfen, Dungeons",
    "tempelbezirk": "Segen, Gespräche, Ruhe",
    "uebungsplatz": "Fähigkeiten trainieren",
    "adelsviertel": "Politik, Audienzen, Intrigen",
}


def hub_orte(charakter) -> list[str]:
    ids = ["taverne", "marktplatz", "gildenviertel", "wildnis", "tempelbezirk", "uebungsplatz"]
    if charakter.ruf > 20:
        ids.append("adelsviertel")
    return ids


# ---------------------------------------------------------------------------
# Taverne
# ---------------------------------------------------------------------------

def optionen_taverne(charakter) -> list[tuple[str, Aktion]]:
    taverne = random.choice(TAVERNEN_NAMEN)
    opts = [
        (f"Ausruhen in '{taverne}' (HP & MP)", lambda: _taverne_ausruhen(charakter, taverne)),
        ("Gerüchte am Tresen aufschnappen", lambda: _taverne_geruecht(charakter, taverne)),
        ("An einem Trinkspiel teilnehmen", lambda: _taverne_trinkspiel(charakter, taverne)),
    ]
    if len(charakter.begleiter) < 3:
        opts.append(("Nach Mitstreitern für die Gruppe Ausschau halten", lambda: _taverne_gruppenangebot(charakter)))
    return opts


# ---------------------------------------------------------------------------
# Marktplatz
# ---------------------------------------------------------------------------

def _markt_traenke_submenu(charakter) -> Submenu:
    angebote = [generiere_trank(charakter.level) for _ in range(3)]

    def kaufen(trank):
        def aktion():
            if charakter.gold < trank.wert:
                return Ereignis(text=f"🧪 {trank.anzeige()} übersteigt {charakter.name}s Mittel.")
            charakter.gold -= trank.wert
            charakter.traenke.append(trank)
            return Ereignis(text=f"🧪 {charakter.name} kauft {trank.anzeige()}.")
        return aktion

    opts = [(f"{t.anzeige()}", kaufen(t)) for t in angebote]
    opts.append(("Nichts kaufen", lambda: Ereignis(text=f"{charakter.name} verlässt den Stand ohne Kauf.")))
    return Submenu(f"🧪 Der Alchemiestand bietet an ({charakter.gold}g verfügbar)", opts)


def _markt_inventar_submenu(charakter) -> Submenu:
    if not charakter.inventar:
        return Submenu("🎒 Inventar ist leer", [("Zurück", lambda: Ereignis(text=f"{charakter.name}s Inventar ist leer - nichts zu verwalten."))])

    def item_submenu(item):
        def oeffnen():
            opts = [
                ("Ausrüsten", lambda: Ereignis(text=charakter.ausruesten(item))),
                (f"Verkaufen für {item.wert}g", lambda: Ereignis(text=f"💰 {charakter.name} verkauft {item.name} für {charakter.verkaufen(item)}g.")),
            ]
            return Submenu(item.anzeige(), opts)
        return oeffnen

    opts = []
    for item in charakter.inventar:
        hinweis = " ⭐" if charakter.item_ist_besser(item) else ""
        opts.append((f"{item.anzeige()}{hinweis}", item_submenu(item)))
    opts.append((f"Alles verkaufen ({sum(i.wert for i in charakter.inventar)}g)", lambda: _markt_verkaufen(charakter)))
    return Submenu(
        f"🎒 Inventar von {charakter.name} ({len(charakter.inventar)} Gegenstände, ⭐ = besser als aktuelle Ausrüstung)",
        opts,
    )


def _markt_schmied_submenu(charakter) -> Submenu:
    teile = [(s, getattr(charakter, s)) for s in ("waffe", "ruestung", "accessoire") if getattr(charakter, s)]
    if not teile:
        return Submenu("🔨 Schmiede", [("Zurück", lambda: Ereignis(text=f"{charakter.name} hat noch keine Ausrüstung, die sich verbessern ließe."))])

    def verbessern(slot, item):
        def aktion():
            meldung = charakter.schmiede_verbessern(slot)
            if meldung:
                return Ereignis(text=meldung)
            return Ereignis(text=f"🔨 Das Gold reicht nicht, um {item.name} zu verbessern.")
        return aktion

    opts = []
    for slot, item in teile:
        _, kosten = schmiede_upgrade(item)
        opts.append((f"{item.anzeige()} verbessern - {kosten}g", verbessern(slot, item)))
    return Submenu(f"🔨 Der Schmied begutachtet {charakter.name}s Ausrüstung. (Gold: {charakter.gold})", opts)


def optionen_marktplatz(charakter, welt) -> list[tuple[str, Aktion]]:
    opts = [
        ("Um Ausrüstung feilschen", lambda: _markt_feilschen(charakter)),
        ("Tränke kaufen", lambda: _markt_traenke_submenu(charakter)),
        ("Inventar verwalten (ausrüsten/verkaufen)", lambda: _markt_inventar_submenu(charakter)),
        ("Zum Schmied gehen (Ausrüstung verbessern)", lambda: _markt_schmied_submenu(charakter)),
    ]
    if not charakter.anwesen:
        opts.append(("Ein Anwesen für die Gruppe kaufen", lambda: _markt_anwesen_kaufen(charakter, welt)))
    if not charakter.hat_kutsche:
        opts.append(("Eine eigene Kutsche kaufen", lambda: _markt_kutsche_kaufen(charakter)))
    return opts


# ---------------------------------------------------------------------------
# Gildenviertel
# ---------------------------------------------------------------------------

def _quest_brett_submenu(charakter) -> Submenu:
    quests = generiere_quest_brett(charakter.rang)

    def waehlen(quest):
        def aktion():
            _, log, erfolg = quest_abschliessen(charakter, quest)
            return Ereignis(text=f"📜 {charakter.name} nimmt die Quest an: \"{quest.titel}\"", log=log, ist_wichtig=erfolg)
        return aktion

    opts = [
        (f"[Rang {q.rang}] {q.titel} ({q.typ}) - {q.belohnung_gold}g, {q.belohnung_xp} XP", waehlen(q))
        for q in quests
    ]
    opts.append(("Keine Quest annehmen", lambda: Ereignis(text=f"{charakter.name} entscheidet sich, heute keine Quest anzunehmen.")))
    return Submenu(f"📜 Quest-Brett der Gilde - {charakter.name}s Rang: {charakter.rang}", opts)


def _daemonenjagd_submenu(charakter) -> Submenu:
    if demonenkoenig_verfuegbar(charakter):
        def konfrontieren():
            ergebnis = konfrontiere_daemonenkoenig(charakter)
            if ergebnis.sieg:
                charakter.daemonenkoenig_besiegt = True
            return Ereignis(
                text="👑💀 Die letzte Schlacht beginnt!", log=ergebnis.log,
                xp=ergebnis.xp_gewonnen, gold=ergebnis.gold_gewonnen, ist_wichtig=True,
            )
        opts = [
            (f"👑💀 {charakter.name} und die Gruppe konfrontieren den Dämonenkönig!", konfrontieren),
            ("Sich noch nicht bereit fühlen", lambda: Ereignis(text=f"{charakter.name} sammelt noch einmal Kraft, bevor die letzte Schlacht beginnt.")),
        ]
        return Submenu("Alle Unterlinge sind gefallen. Der Dämonenkönig selbst erwartet euch.", opts)

    fuersten = verbleibende_fuersten(charakter)

    def jagen(ziel):
        def aktion():
            ergebnis = jage_daemonenfuersten(charakter, ziel)
            return Ereignis(
                text=f"👹 Die Jagd auf {ergebnis.name} beginnt!", log=ergebnis.log,
                xp=ergebnis.xp_gewonnen, gold=ergebnis.gold_gewonnen, ist_wichtig=ergebnis.sieg,
            )
        return aktion

    opts = [(f"{name} - {beschr}", jagen((name, beschr))) for name, beschr in fuersten]
    opts.append(("Zurückkehren", lambda: Ereignis(text=f"{charakter.name} verschiebt die Jagd auf ein andermal.")))
    besiegt = len(charakter.besiegte_daemonenfuersten)
    return Submenu(f"👹 Dämonenjagd - {besiegt}/{besiegt + len(fuersten)} Unterlinge des Dämonenkönigs gefallen", opts)


def optionen_gildenviertel(charakter, welt) -> list[tuple[str, Aktion]]:
    opts = [("Quest-Brett ansehen", lambda: _quest_brett_submenu(charakter))]
    if not charakter.gilde:
        opts.append(("Einer Gilde beitreten", lambda: ereignis_gilde(charakter, welt)))
    else:
        opts.append(("Auftrag vom Gildenmeister annehmen", lambda: ereignis_gilde(charakter, welt)))
    opts.append(("Klatsch und Gerüchte hören", lambda: _gilde_klatsch(charakter)))
    opts.append(("Gezielt einen Dungeon-Einsatz suchen", lambda: ereignis_dungeon(charakter)))
    if kann_aufsteigen(charakter):
        opts.append((f"⭐ Rangaufstiegsprüfung ablegen (Rang {naechster_rang(charakter.rang)})", lambda: _rangaufstieg_pruefung(charakter)))
    if daemonenjagd_verfuegbar(charakter) and not charakter.daemonenkoenig_besiegt:
        opts.append(("👹 Dämonenjagd - das ultimative Ziel", lambda: _daemonenjagd_submenu(charakter)))
    return opts


# ---------------------------------------------------------------------------
# Wildnis
# ---------------------------------------------------------------------------

def optionen_wildnis(charakter, welt) -> list[tuple[str, Aktion]]:
    return [
        ("Das Gebiet erkunden (Kämpfe, Funde, alles ist möglich)", lambda: _wildnis_erkunden(charakter, welt)),
        ("Gezielt einen Dungeon aufsuchen", lambda: ereignis_dungeon(charakter)),
        ("Auf Reisende und Gesellschaft hoffen", lambda: _wildnis_reisende(charakter)),
    ]


# ---------------------------------------------------------------------------
# Tempelbezirk
# ---------------------------------------------------------------------------

def optionen_tempelbezirk(charakter) -> list[tuple[str, Aktion]]:
    return [
        ("Beten und einen Segen erhalten (HP & MP)", lambda: _tempel_segen(charakter)),
        ("Für die Armen spenden", lambda: _tempel_spende(charakter)),
        ("Mit einem Priester sprechen", lambda: _tempel_priester(charakter)),
    ]


# ---------------------------------------------------------------------------
# Adelsviertel
# ---------------------------------------------------------------------------

def optionen_adelsviertel(charakter, welt) -> list[tuple[str, Aktion]]:
    return [
        ("Um eine Audienz bitten", lambda: _adel_audienz(charakter, welt)),
        ("Sich im Hof umhören", lambda: _adel_intrige(charakter)),
    ]


# ---------------------------------------------------------------------------
# Übungsplatz
# ---------------------------------------------------------------------------

def _trainieren(charakter) -> Ereignis:
    skill_meldung = None
    if charakter.gelernte_skills:
        for _ in range(random.randint(1, 2)):
            m = charakter.zufaelligen_skill_ueben()
            if m:
                skill_meldung = m
    text = f"🎯 {charakter.name} verbringt den Tag mit hartem Training auf dem Übungsplatz."
    if skill_meldung:
        text += f" {skill_meldung}"
    return Ereignis(text=text, xp=int(18 * charakter.level))


def _spezialisierung_submenu(charakter) -> Submenu:
    pfad = TANK_PFADE[charakter.klasse_id]
    offensiv_tier = charakter.klasse.tier_fuer_level(30)

    def waehle(tank: bool):
        def aktion():
            if tank:
                charakter.spezialisierung = "Tank"
                text = (
                    f"🛡️ {charakter.name} wählt den Weg des Beschützers und wird zu: {pfad['tier30'].name}! "
                    f"Von nun an zieht {charakter.name} im Kampf gezielt Aufmerksamkeit auf sich und trotzt "
                    f"Schlägen, die andere niederstrecken würden."
                )
                return Ereignis(text=text, ist_wichtig=True)
            charakter.spezialisierung = "Offensiv"
            return Ereignis(text=f"⚔️ {charakter.name} bleibt dem Weg der Klinge treu und wird zu: {offensiv_tier.name}!", ist_wichtig=True)
        return aktion

    opts = [
        (f"Dem Weg der Klinge treu bleiben: {offensiv_tier.name}", waehle(False)),
        (f"Zum Beschützer der Gruppe werden: {pfad['tier30'].name}", waehle(True)),
    ]
    return Submenu(f"⚔️ {charakter.name} steht an einem Wendepunkt der Ausbildung.", opts)


def optionen_uebungsplatz(charakter) -> list[tuple[str, Aktion]]:
    opts = []
    if charakter.level >= 30 and charakter.klasse_id in TANK_PFADE and charakter.spezialisierung is None:
        opts.append(("⚔️ Deine Spezialisierung wählen", lambda: _spezialisierung_submenu(charakter)))
    opts.append(("Fähigkeiten trainieren", lambda: _trainieren(charakter)))
    return opts


def optionen_fuer_ort(ort_id: str, charakter, welt) -> list[tuple[str, Aktion]]:
    if ort_id == "taverne":
        return optionen_taverne(charakter)
    elif ort_id == "marktplatz":
        return optionen_marktplatz(charakter, welt)
    elif ort_id == "gildenviertel":
        return optionen_gildenviertel(charakter, welt)
    elif ort_id == "wildnis":
        return optionen_wildnis(charakter, welt)
    elif ort_id == "tempelbezirk":
        return optionen_tempelbezirk(charakter)
    elif ort_id == "adelsviertel":
        return optionen_adelsviertel(charakter, welt)
    else:
        return optionen_uebungsplatz(charakter)

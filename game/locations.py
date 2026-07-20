"""Ortswahl-System: der Spieler entscheidet aktiv, wohin der Charakter geht und
was er dort tut. Enthält Taverne, Marktplatz (Handel, Anwesen, Kutsche, Tränke),
Gildenviertel (Quest-Brett, Rangaufstieg), Wildnis, Tempelbezirk, Adelsviertel
und Übungsplatz."""

import random
from dataclasses import dataclass

from game.character import MAX_AKTIONEN_PRO_TAG, Charakter
from game.classes import AUFSTIEGSPFADE, skill_ist_aoe, skill_ist_signatur
from game.combat import Kampfstart, erwartete_kampfkraft, kampf_starten
from game.companions import (
    generiere_rekruten,
    gruppen_rollen,
    ist_ausgewogene_gruppe,
    rekrutierungskosten,
)
from game.endgame import (
    daemonenjagd_verfuegbar,
    demonenkoenig_verfuegbar,
    jage_daemonenfuersten,
    konfrontiere_daemonenkoenig,
    verbleibende_fuersten,
)
from game.events import Ereignis, ereignis_dungeon, ereignis_gilde, zufallsereignis
from game.gildenmeister import gildenmeister_gespraech, gildenmeister_name, naechste_entscheidung
from game.items import generiere_item, generiere_trank, schmiede_upgrade
from game.quests import generiere_quest_brett, quest_abschliessen
from game.ranks import anforderung_text, kann_aufsteigen, naechster_rang
from game.world import Welt

NPC_VORNAMEN = [
    "Aria", "Faelan", "Thrain", "Sylvara", "Korgan", "Elowen", "Baldric", "Nyssa", "Draven", "Isolde",
    "Kael", "Wren", "Osric", "Talia", "Bram", "Mira", "Fenris", "Rosalind", "Torvald", "Seraphine",
]

TAVERNEN_NAMEN = [
    "Zum Goldenen Krug", "Der Müde Wanderer", "Die Trunkene Ziege", "Zum Schwarzen Eber",
    "Die Letzte Rast", "Zum Singenden Kessel", "Der Krähenhort", "Die Verlorene Münze",
]

GERUECHTE = [
    "man erzählt sich von einem Drachen, der in den Bergen im Norden gesichtet wurde",
    "ein Adliger soll heimlich mit einer verfeindeten Fraktion verhandeln",
    "in den Kanälen der Unterstadt sollen sich Kultisten versammeln",
    "eine alte Ruine im Wald soll über Nacht wieder zum Leben erwacht sein",
    "ein legendärer Schatz soll unter der alten Brücke verborgen liegen",
    "die Ernte in den umliegenden Dörfern fällt dieses Jahr ungewöhnlich schlecht aus",
    "ein maskierter Fremder verteilt seit Wochen Gold an die Armen der Stadt",
    "die Wachen suchen händeringend nach einem entflohenen Gefangenen",
]

# Gerüchte rund um die Dämonenkönig-Handlung, gestaffelt nach Rang - je höher
# der Rang, desto konkreter und bedrohlicher wird das, was man am Tresen hört.
GERUECHTE_DAEMON_FRUEH = [
    "raunt man sich zu, dass im Süden ganze Ländereien plötzlich verdorren - manche murmeln das Wort 'Dämon'",
    "erzählt ein Fernhändler von einer Karawane, die spurlos verschwand, nur die Wagen blieben zurück",
    "will ein Wachmann Schatten gesehen haben, die sich gegen den Wind bewegten",
]
GERUECHTE_DAEMON_MITTEL = [
    "spricht man kaum noch flüsternd über Abraxos, den Dämonenkönig - fast jeder kennt inzwischen den Namen",
    "berichten Überlebende aus dem Süden von disziplinierten Dämonenkriegern, die eindeutig einem Befehl folgen",
    "heißt es, eine ganze Gilde habe sich aufgelöst, weil zu viele ihrer Mitglieder nicht von der Jagd auf einen Fürsten zurückkehrten",
]
GERUECHTE_DAEMON_SPAET = [
    "erzählt man sich von ganzen Heeren, die im Namen des Dämonenkönigs durch verwüstete Grenzregionen marschieren",
    "heißt es, selbst Königreiche würden im Geheimen Boten austauschen, um sich auf das Unausweichliche vorzubereiten",
    "schwört ein alter Veteran, in seiner Jugend habe man Abraxos schon einmal beinahe besiegt - 'beinahe reichte nicht'",
]

ANWESEN_NAMEN_ZUSATZ = ["Herrenhaus", "Stadthaus", "Gutshof", "Turmvilla", "Anwesen"]


class EingabeErschoepft(Exception):
    """Wird ausgelöst, wenn keine gültige Eingabe mehr zu bekommen ist (z.B.
    stdin geschlossen/erschöpft). Statt endlos mit Standardwerten weiterzulaufen,
    lässt das Hauptprogramm die Sitzung dadurch sauber enden."""


def menu_waehlen(titel: str, optionen: list[str]) -> int:
    """Zeigt ein nummeriertes Menü und gibt den gewählten Index (0-basiert) zurück."""
    print(f"\n{titel}")
    for i, opt in enumerate(optionen, 1):
        print(f"  [{i}] {opt}")
    ungueltige_versuche = 0
    while True:
        try:
            wahl = input("Wahl: ").strip()
        except EOFError:
            raise EingabeErschoepft
        if wahl.isdigit() and 1 <= int(wahl) <= len(optionen):
            return int(wahl) - 1
        ungueltige_versuche += 1
        if ungueltige_versuche >= 20:
            raise EingabeErschoepft
        print("Ungültige Wahl, versuch's nochmal.")


@dataclass
class Ort:
    name: str
    icon: str


ORTE = {
    "taverne": Ort("Taverne", "🍺"),
    "marktplatz": Ort("Marktplatz", "🏪"),
    "gildenviertel": Ort("Gildenviertel", "🏛️"),
    "wildnis": Ort("Wildnis", "🌲"),
    "tempelbezirk": Ort("Tempelbezirk", "⛩️"),
    "adelsviertel": Ort("Adelsviertel", "🏰"),
    "uebungsplatz": Ort("Übungsplatz", "🎯"),
    "inventar": Ort("Inventar", "🎒"),
    "gruppe": Ort("Gruppe", "👥"),
}


ORT_BESCHREIBUNGEN = {
    "taverne": "Ausruhen, Gerüchte hören, eine Gruppe finden",
    "marktplatz": "Handeln, Tränke, Anwesen, Kutsche",
    "gildenviertel": "Quest-Brett, Rangaufstieg, Klatsch",
    "wildnis": "Erkunden, kämpfen, Dungeons",
    "tempelbezirk": "Segen, Gespräche, Ruhe",
    "uebungsplatz": "Fähigkeiten trainieren",
    "adelsviertel": "Politik, Audienzen, Intrigen",
    "inventar": "Ausrüstung wechseln, verkaufen (kostenlos)",
    "gruppe": "Begleiter entlassen oder anheuern (kostenlos)",
}


def verfuegbare_orte(charakter: Charakter) -> list[str]:
    """Sind die Aktionen für heute aufgebraucht, bleibt nur noch die Taverne,
    um schlafen zu gehen und den nächsten Tag zu beginnen - Inventar und
    Gruppe bleiben aber immer erreichbar, da bloßes Verwalten keine Aktion
    kostet (nur das tatsächliche Anheuern schon, siehe _gruppe_anheuern)."""
    if charakter.aktionen_uebrig <= 0:
        return ["taverne", "inventar", "gruppe"]
    optionen_ids = ["taverne", "marktplatz", "gildenviertel", "wildnis", "tempelbezirk", "uebungsplatz"]
    if charakter.ruf > 20:
        optionen_ids.append("adelsviertel")
    optionen_ids.append("inventar")
    optionen_ids.append("gruppe")
    return optionen_ids


def waehle_ort(charakter: Charakter) -> str:
    """Der Spieler wählt aktiv, wohin der Charakter als Nächstes geht."""
    optionen_ids = verfuegbare_orte(charakter)
    if charakter.aktionen_uebrig <= 0:
        print(f"\n😴 {charakter.name} hat für heute keine Kraft mehr übrig - Zeit, in der Taverne zu schlafen.")
    texte = [f"{ORTE[o].icon} {ORTE[o].name} - {ORT_BESCHREIBUNGEN[o]}" for o in optionen_ids]
    idx = menu_waehlen(f"📍 Wohin geht {charakter.name}? (Aktionen übrig: {charakter.aktionen_uebrig}/{MAX_AKTIONEN_PRO_TAG})", texte)
    return optionen_ids[idx]


# ---------------------------------------------------------------------------
# Taverne
# ---------------------------------------------------------------------------

def _taverne_ausruhen(charakter: Charakter, taverne: str) -> Ereignis:
    """Schlafen ist die einzige Aktion, die den Tag beendet - sie kostet keine
    der täglichen Aktionen, dafür aber auch keine Wahl: erst danach beginnt
    ein neuer Tag mit frischen 4 Aktionen."""
    kosten = min(charakter.gold, random.randint(3, 12))
    charakter.gold -= kosten
    if charakter.hp_aktuell >= charakter.hp_max and charakter.mp_aktuell >= charakter.mp_max:
        text = f"🛌 {charakter.name} nimmt sich ein Zimmer in '{taverne}' für eine ruhige Nacht - wohlauf und ausgeruht wie eh und je."
        return Ereignis(text=text, kostet_aktion=False, beendet_tag=True)
    geheilt, mp_regen = charakter.ausruhen()
    text = f"🛌 {charakter.name} nimmt sich ein Zimmer in '{taverne}' und ruht sich aus. (+{geheilt} HP, +{mp_regen} MP)"
    return Ereignis(text=text, kostet_aktion=False, beendet_tag=True)


def _geruecht_pool(charakter: Charakter) -> list[str]:
    """Je höher der Rang, desto wahrscheinlicher hört man am Tresen etwas über
    die wachsende Bedrohung durch den Dämonenkönig statt gewöhnlichen Klatsch."""
    from game.ranks import RANG_REIHENFOLGE
    idx = RANG_REIHENFOLGE.index(charakter.rang)
    pool = list(GERUECHTE)
    if idx >= RANG_REIHENFOLGE.index("E"):
        pool += GERUECHTE_DAEMON_FRUEH
    if idx >= RANG_REIHENFOLGE.index("C"):
        pool += GERUECHTE_DAEMON_MITTEL * 2
    if idx >= RANG_REIHENFOLGE.index("A"):
        pool += GERUECHTE_DAEMON_SPAET * 2
    return pool


def _taverne_geruecht(charakter: Charakter, taverne: str) -> Ereignis:
    text = f"👂 Am Tresen von '{taverne}' schnappt {charakter.name} ein Gerücht auf: {random.choice(_geruecht_pool(charakter))}."
    if random.random() < 0.15:
        text += " Eine Schlägerei bricht in der Nähe aus, und ein Krug fliegt haarscharf an ihm vorbei."
        return Ereignis(text=text, xp=int(5 * charakter.level), schaden=int(charakter.hp_max * 0.05))
    return Ereignis(text=text, xp=int(5 * charakter.level))


def _taverne_trinkspiel(charakter: Charakter, taverne: str) -> Ereignis:
    einsatz = min(charakter.gold, random.randint(5, 30))
    if einsatz == 0 or random.random() < 0.5:
        gewinn = einsatz * 2 if einsatz else random.randint(5, 20)
        text = f"🍻 {charakter.name} gewinnt ein Trinkspiel in '{taverne}' und heimst {gewinn} Gold ein!"
        return Ereignis(text=text, gold=gewinn, ruf=1)
    else:
        text = f"🍻 {charakter.name} verliert ein Trinkspiel in '{taverne}' und {einsatz} Gold - unter dem Gelächter der Gäste."
        return Ereignis(text=text, gold=-einsatz)


def besuche_taverne(charakter: Charakter) -> Ereignis:
    taverne = random.choice(TAVERNEN_NAMEN)

    if charakter.aktionen_uebrig <= 0:
        return _taverne_ausruhen(charakter, taverne)

    optionen = [
        f"Schlafen gehen in '{taverne}' (beendet den Tag, HP & MP)",
        "Gerüchte am Tresen aufschnappen",
        "An einem Trinkspiel teilnehmen",
    ]
    if len(charakter.begleiter) < 3:
        optionen.append("Nach Mitstreitern für die Gruppe Ausschau halten")

    idx = menu_waehlen(f"🍺 {charakter.name} betritt '{taverne}'.", optionen)
    if idx == 0:
        return _taverne_ausruhen(charakter, taverne)
    elif idx == 1:
        return _taverne_geruecht(charakter, taverne)
    elif idx == 2:
        return _taverne_trinkspiel(charakter, taverne)
    else:
        # Dieselbe Rekrutierungs-Auswahl wie im eigenständigen Gruppen-Bildschirm
        # (siehe _gruppe_anheuern) statt eines eigenen, abweichenden Zufallsangebots.
        return _gruppe_anheuern(charakter)


# ---------------------------------------------------------------------------
# Marktplatz
# ---------------------------------------------------------------------------

def _markt_feilschen(charakter: Charakter) -> Ereignis:
    item = generiere_item(charakter.level, klasse_id=charakter.klasse_id)
    voller_preis = item.wert
    verhandelt_preis = int(voller_preis * random.uniform(0.55, 0.85))
    if charakter.gold >= verhandelt_preis:
        charakter.gold -= verhandelt_preis
        text = (
            f"💬 {charakter.name} feilscht um {item.anzeige()} herunter "
            f"von {voller_preis}g auf {verhandelt_preis}g - und schlägt zu!"
        )
        return Ereignis(text=text, item=item)
    text = f"💬 {charakter.name} findet {item.anzeige()} interessant, doch selbst der Verhandlungspreis von {verhandelt_preis}g übersteigt die Mittel."
    return Ereignis(text=text)


def _markt_traenke_kaufen(charakter: Charakter) -> Ereignis:
    angebote = [generiere_trank(charakter.level) for _ in range(3)]
    texte = [t.anzeige() for t in angebote] + ["Nichts kaufen"]
    idx = menu_waehlen(f"🧪 Der Alchemiestand bietet an ({charakter.gold}g verfügbar):", texte)
    if idx == len(angebote):
        return Ereignis(text=f"{charakter.name} verlässt den Stand ohne Kauf.")
    trank = angebote[idx]
    if charakter.gold < trank.wert:
        return Ereignis(text=f"🧪 {trank.anzeige()} übersteigt {charakter.name}s Mittel.")
    charakter.gold -= trank.wert
    charakter.traenke.append(trank)
    return Ereignis(text=f"🧪 {charakter.name} kauft {trank.anzeige()}.")


def _markt_verkaufen(charakter: Charakter) -> Ereignis:
    if not charakter.inventar:
        return Ereignis(text=f"🎒 {charakter.name}s Inventar ist bereits leer - nichts zu verkaufen.", kostet_aktion=False)
    erloes = sum(i.wert for i in charakter.inventar)
    anzahl = len(charakter.inventar)
    charakter.gold += erloes
    charakter.inventar.clear()
    return Ereignis(text=f"💰 {charakter.name} verkauft {anzahl} Gegenstände aus dem Inventar für insgesamt {erloes}g.", kostet_aktion=False)


_AUSRUESTUNGS_SLOTS = (("Waffe", "🗡️", "Waffe"), ("Ruestung", "🛡️", "Rüstung"), ("Accessoire", "💍", "Accessoire"))


def _ausruestungs_uebersicht(charakter: Charakter) -> str:
    zeilen = []
    for typ, symbol, label in _AUSRUESTUNGS_SLOTS:
        item = charakter.ausgeruestetes_item(typ)
        zeilen.append(f"{symbol} {label}: {item.anzeige() if item else 'nichts ausgerüstet'}")
    return "\n".join(zeilen)


def inventar_verwalten(charakter: Charakter) -> Ereignis:
    """Der Spieler entscheidet selbst, was ausgerüstet oder verkauft wird -
    keine automatische Verwaltung mehr. Das bloße Sichten/Verwalten der
    eigenen Ausrüstung kostet keine der täglichen Aktionen."""
    if not charakter.inventar:
        return Ereignis(
            text=f"🎒 {charakter.name}s Inventar ist leer - nichts zu verwalten.\n\nAktuelle Ausrüstung:\n{_ausruestungs_uebersicht(charakter)}",
            kostet_aktion=False,
        )

    texte = []
    for item in charakter.inventar:
        hinweis = " ⭐" if charakter.item_ist_besser(item) else ""
        texte.append(f"{item.anzeige()}{hinweis} - {charakter.ausruestungs_vergleich(item)}")
    texte.append(f"Alles verkaufen ({sum(i.wert for i in charakter.inventar)}g)")
    texte.append("Zurück")

    idx = menu_waehlen(
        f"🎒 Inventar von {charakter.name} ({len(charakter.inventar)} Gegenstände, ⭐ = besser als aktuelle Ausrüstung)\n\n"
        f"Aktuelle Ausrüstung:\n{_ausruestungs_uebersicht(charakter)}",
        texte,
    )
    anzahl_items = len(charakter.inventar)
    if idx == anzahl_items:
        return _markt_verkaufen(charakter)
    if idx == anzahl_items + 1:
        return Ereignis(text=f"{charakter.name} verlässt das Inventar unangetastet.", kostet_aktion=False)

    item = charakter.inventar[idx]
    unteroptionen = ["Ausrüsten", f"Verkaufen für {item.wert}g", "Zurück"]
    unteridx = menu_waehlen(f"{item.anzeige()}\n{charakter.ausruestungs_vergleich(item)}", unteroptionen)
    if unteridx == 0:
        return Ereignis(text=charakter.ausruesten(item), kostet_aktion=False)
    elif unteridx == 1:
        erloes = charakter.verkaufen(item)
        return Ereignis(text=f"💰 {charakter.name} verkauft {item.name} für {erloes}g.", kostet_aktion=False)
    return Ereignis(text=f"{charakter.name} überlegt es sich noch einmal.", kostet_aktion=False)


# ---------------------------------------------------------------------------
# Gruppe (Begleiter anheuern/entlassen)
# ---------------------------------------------------------------------------

def _gruppe_anheuern(charakter: Charakter) -> Ereignis:
    vorhandene_rollen = gruppen_rollen(charakter.begleiter)
    rekruten = generiere_rekruten(charakter.level, anzahl=3, vorhandene_rollen=vorhandene_rollen)
    kosten_liste = [rekrutierungskosten(r) for r in rekruten]
    texte = [f"{r.anzeige()} - {k}g" for r, k in zip(rekruten, kosten_liste)]
    texte.append("Niemanden anheuern")

    idx = menu_waehlen(f"🤝 Mögliche Rekruten für {charakter.name}s Gruppe (Gold: {charakter.gold})", texte)
    if idx == len(rekruten):
        return Ereignis(text=f"{charakter.name} findet niemand Passendes und kehrt zurück.", kostet_aktion=False)

    rekrut, kosten = rekruten[idx], kosten_liste[idx]
    if charakter.gold < kosten:
        return Ereignis(text=f"{rekrut.name} verlangt {kosten}g für die Zusammenarbeit - das übersteigt {charakter.name}s Mittel.", kostet_aktion=False)
    charakter.gold -= kosten
    charakter.begleiter_aufnehmen(rekrut)
    text = f"🤝 {rekrut.name} schließt sich für {kosten}g der Gruppe an: {rekrut.anzeige()}"
    if ist_ausgewogene_gruppe(charakter.begleiter):
        text += " Die Gruppe ist damit ausgewogen - Nahkampf, Fernkampf und Unterstützung vereint."
    return Ereignis(text=text, ist_wichtig=True)


def besuche_gruppe(charakter: Charakter) -> Ereignis:
    """Begleiter ansehen und entlassen kostet keine Aktion - erst das
    tatsächliche Anheuern eines neuen Mitglieds zählt als Tagesaktivität."""
    synergie = "ausgewogen (Nahkampf, Fernkampf und Unterstützung vertreten)" if ist_ausgewogene_gruppe(charakter.begleiter) else "nicht ausgewogen"
    optionen = [f"{b.anzeige()} - Entlassen [Ausrüstung: {b.ausruestung_kurzuebersicht()}]" for b in charakter.begleiter]
    if len(charakter.begleiter) < 3:
        optionen.append("Neue Abenteurer kennenlernen (anheuern)")
    optionen.append("Zurück")

    idx = menu_waehlen(f"👥 {charakter.name}s Gruppe - Synergie: {synergie}", optionen)
    anzahl_begleiter = len(charakter.begleiter)

    if idx < anzahl_begleiter:
        entlassen = charakter.begleiter.pop(idx)
        return Ereignis(text=f"{charakter.name} verabschiedet sich von {entlassen.name} - hier trennen sich ihre Wege.", kostet_aktion=False)

    rest = idx - anzahl_begleiter
    if len(charakter.begleiter) < 3 and rest == 0:
        return _gruppe_anheuern(charakter)
    return Ereignis(text=f"{charakter.name} belässt die Gruppe, wie sie ist.", kostet_aktion=False)


def _markt_schmied(charakter: Charakter) -> Ereignis:
    teile = [(s, getattr(charakter, s)) for s in ("waffe", "ruestung", "accessoire") if getattr(charakter, s)]
    if not teile:
        return Ereignis(text=f"🔨 {charakter.name} hat noch keine Ausrüstung, die sich verbessern ließe.")

    texte = []
    for _, item in teile:
        _, kosten = schmiede_upgrade(item)
        texte.append(f"{item.anzeige()} verbessern - {kosten}g")
    texte.append("Zurück")

    idx = menu_waehlen(f"🔨 Der Schmied begutachtet {charakter.name}s Ausrüstung. (Gold: {charakter.gold})", texte)
    if idx == len(teile):
        return Ereignis(text=f"{charakter.name} verlässt die Schmiede ohne Auftrag.")

    slot, item = teile[idx]
    meldung = charakter.schmiede_verbessern(slot)
    if meldung:
        return Ereignis(text=meldung)
    return Ereignis(text=f"🔨 Das Gold reicht nicht, um {item.name} zu verbessern.")


def _markt_anwesen_kaufen(charakter: Charakter, welt: Welt) -> Ereignis:
    if charakter.anwesen:
        return Ereignis(text=f"🏠 {charakter.name} besitzt bereits ein Anwesen in {charakter.anwesen}.")
    _, stadt = welt.zufaellige_stadt()
    typ = random.choice(ANWESEN_NAMEN_ZUSATZ)
    preis = random.randint(600, 1800)
    if charakter.gold < preis:
        return Ereignis(text=f"🏠 Ein {typ} in {stadt} kostet {preis}g - das übersteigt die derzeitigen Mittel.")
    charakter.gold -= preis
    charakter.anwesen = stadt
    text = (
        f"🏠 {charakter.name} erwirbt ein {typ} in {stadt} für {preis}g - "
        f"ein festes Zuhause für die ganze Gruppe. Rasten dort ist von nun an besonders erholsam."
    )
    return Ereignis(text=text, ruf=5, ist_wichtig=True)


def _markt_kutsche_kaufen(charakter: Charakter) -> Ereignis:
    if charakter.hat_kutsche:
        return Ereignis(text=f"🐎 {charakter.name} besitzt bereits eine eigene Kutsche.")
    preis = random.randint(250, 500)
    if charakter.gold < preis:
        return Ereignis(text=f"🐎 Eine eigene Kutsche kostet {preis}g - noch nicht leistbar.")
    charakter.gold -= preis
    charakter.hat_kutsche = True
    text = f"🐎 {charakter.name} kauft eine eigene Kutsche für {preis}g - Reisen werden von nun an schneller und sicherer."
    return Ereignis(text=text, ist_wichtig=True)


def besuche_marktplatz(charakter: Charakter, welt: Welt) -> Ereignis:
    optionen = [
        "Um Ausrüstung feilschen",
        "Tränke kaufen",
        "Zum Schmied gehen (Ausrüstung verbessern)",
    ]
    if not charakter.anwesen:
        optionen.append("Ein Anwesen für die Gruppe kaufen")
    if not charakter.hat_kutsche:
        optionen.append("Eine eigene Kutsche kaufen")

    idx = menu_waehlen(f"🏪 {charakter.name} erreicht den Marktplatz. (Gold: {charakter.gold})", optionen)
    if idx == 0:
        return _markt_feilschen(charakter)
    elif idx == 1:
        return _markt_traenke_kaufen(charakter)
    elif idx == 2:
        return _markt_schmied(charakter)
    else:
        # Reihenfolge der optionalen Einträge respektieren
        rest = optionen[3:]
        gewaehlt = rest[idx - 3]
        if "Anwesen" in gewaehlt:
            return _markt_anwesen_kaufen(charakter, welt)
        else:
            return _markt_kutsche_kaufen(charakter)


# ---------------------------------------------------------------------------
# Gildenviertel
# ---------------------------------------------------------------------------

def _gilde_klatsch(charakter: Charakter) -> Ereignis:
    themen = [
        "wer als Nächstes zum Gildenmeister aufsteigen könnte",
        "einen besonders lukrativen, aber gefährlichen Auftrag, den bisher niemand angenommen hat",
        "eine Rivalität zwischen zwei bekannten Abenteurergruppen",
        "Gerüchte über Korruption unter den Gildenältesten",
    ]
    text = f"🗣️ Im Gildenviertel wird getratscht über {random.choice(themen)}. {charakter.name} hört aufmerksam zu."
    return Ereignis(text=text, xp=int(10 * charakter.level))


def _quest_brett_ansehen(charakter: Charakter, welt: Welt) -> "Ereignis | Kampfstart":
    quests = generiere_quest_brett(charakter.rang)
    texte = [
        f"[Rang {q.rang}] {q.titel} ({q.typ}) - Belohnung: {q.belohnung_gold}g, {q.belohnung_xp} XP"
        for q in quests
    ]
    texte.append("Keine Quest annehmen")
    idx = menu_waehlen(f"📜 Quest-Brett der Gilde - {charakter.name}s Rang: {charakter.rang}", texte)
    if idx == len(quests):
        return Ereignis(text=f"{charakter.name} entscheidet sich, heute keine Quest anzunehmen.")

    return quest_abschliessen(charakter, quests[idx])


def _rangaufstieg_pruefung(charakter: Charakter) -> "Ereignis | Kampfstart":
    ziel = naechster_rang(charakter.rang)
    # erwartete_kampfkraft liegt bereits ca. 20-25% über der tatsächlichen
    # Kampfkraft eines Durchschnittscharakters (siehe combat.py) - ein
    # zusätzlicher 1.1-1.3x-Faktor machte die Rangprüfung, das zentrale
    # Spielziel, faktisch unbesiegbar. Ein Faktor knapp unter/um 1.0 ist
    # bereits eine echte, faire Herausforderung.
    staerke = int(erwartete_kampfkraft(charakter.level) * random.uniform(0.8, 1.0))
    einleitung = f"⭐ {charakter.name} tritt zur Rangaufstiegsprüfung für Rang {ziel} an!"
    kampf = kampf_starten(charakter, f"Prüfungswächter (Rang {ziel})", staerke)

    def bei_abschluss(ergebnis):
        log = list(ergebnis.log)
        if ergebnis.sieg:
            alter_rang = charakter.rang
            charakter.rang = ziel
            log.append(f"🎖️ {charakter.name} besteht die Prüfung! Rangaufstieg: {alter_rang} → {ziel}!")
            return Ereignis(text=einleitung, xp=ergebnis.xp_gewonnen, ruf=10, log=log, ist_wichtig=True)
        else:
            if charakter.lebendig:
                log.append("Die Prüfung ist gescheitert - ein neuer Versuch ist jederzeit möglich, sobald die Voraussetzungen weiter erfüllt sind.")
            return Ereignis(text=einleitung, xp=ergebnis.xp_gewonnen, log=log)

    return Kampfstart(kampf, bei_abschluss)


def _daemonenjagd(charakter: Charakter) -> "Ereignis | Kampfstart":
    if demonenkoenig_verfuegbar(charakter):
        optionen = [f"👑💀 {charakter.name} und die Gruppe konfrontieren den Dämonenkönig!", "Sich noch nicht bereit fühlen"]
        idx = menu_waehlen("Alle Unterlinge sind gefallen. Der Dämonenkönig selbst erwartet euch.", optionen)
        if idx == 1:
            return Ereignis(text=f"{charakter.name} sammelt noch einmal Kraft, bevor die letzte Schlacht beginnt.")
        return konfrontiere_daemonenkoenig(charakter)

    fuersten = verbleibende_fuersten(charakter)
    texte = [f"{name} - {beschr}" for name, beschr in fuersten] + ["Zurückkehren"]
    idx = menu_waehlen(
        f"👹 Dämonenjagd - {len(charakter.besiegte_daemonenfuersten)}/{len(fuersten) + len(charakter.besiegte_daemonenfuersten)} Unterlinge des Dämonenkönigs gefallen.",
        texte,
    )
    if idx == len(fuersten):
        return Ereignis(text=f"{charakter.name} verschiebt die Jagd auf ein andermal.")

    return jage_daemonenfuersten(charakter, fuersten[idx])


def _gildenmeister_entscheidung(charakter: Charakter, entscheidung) -> Ereignis:
    texte = [label for label, _ in entscheidung.optionen]
    idx = menu_waehlen(entscheidung.ansage(charakter), texte)
    _, funktion = entscheidung.optionen[idx]
    return funktion(charakter)


def besuche_gildenviertel(charakter: Charakter, welt: Welt) -> Ereignis:
    optionen = ["Quest-Brett ansehen"]
    if not charakter.gilde:
        optionen.append("Einer Gilde beitreten")
    else:
        optionen.append("Auftrag vom Gildenmeister annehmen")
        optionen.append(f"Mit {gildenmeister_name(charakter)}, dem Gildenmeister, sprechen")
    ausstehende_entscheidung = naechste_entscheidung(charakter) if charakter.gilde else None
    if ausstehende_entscheidung is not None:
        optionen.append(f"❗ {gildenmeister_name(charakter)} möchte dringend mit dir sprechen")
    optionen.append("Klatsch und Gerüchte hören")
    optionen.append("Gezielt einen Dungeon-Einsatz suchen")

    rangaufstieg_verfuegbar = kann_aufsteigen(charakter)
    if rangaufstieg_verfuegbar:
        optionen.append(f"⭐ Rangaufstiegsprüfung ablegen (Rang {naechster_rang(charakter.rang)})")
    if daemonenjagd_verfuegbar(charakter) and not charakter.daemonenkoenig_besiegt:
        optionen.append("👹 Dämonenjagd - das ultimative Ziel")

    idx = menu_waehlen(
        f"🏛️ {charakter.name} betritt das Gildenviertel. (Rang: {charakter.rang} - {anforderung_text(charakter)})",
        optionen,
    )
    gewaehlt = optionen[idx]
    if gewaehlt == "Quest-Brett ansehen":
        return _quest_brett_ansehen(charakter, welt)
    elif gewaehlt in ("Einer Gilde beitreten", "Auftrag vom Gildenmeister annehmen"):
        return ereignis_gilde(charakter, welt)
    elif gewaehlt.startswith("Mit ") and gewaehlt.endswith("sprechen"):
        return gildenmeister_gespraech(charakter)
    elif gewaehlt.startswith("❗"):
        return _gildenmeister_entscheidung(charakter, ausstehende_entscheidung)
    elif gewaehlt == "Klatsch und Gerüchte hören":
        return _gilde_klatsch(charakter)
    elif gewaehlt == "Gezielt einen Dungeon-Einsatz suchen":
        return ereignis_dungeon(charakter)
    elif gewaehlt == "👹 Dämonenjagd - das ultimative Ziel":
        return _daemonenjagd(charakter)
    else:
        return _rangaufstieg_pruefung(charakter)


# ---------------------------------------------------------------------------
# Wildnis
# ---------------------------------------------------------------------------

def _wildnis_erkunden(charakter: Charakter, welt: Welt) -> Ereignis:
    return zufallsereignis(charakter, welt)  # Kampf, Dungeon, Dämon, Konflikt, Legendäres etc.


def _wildnis_reisende(charakter: Charakter) -> Ereignis:
    name = random.choice(NPC_VORNAMEN)
    text = f"🧳 Auf dem Weg begegnet {charakter.name} dem Reisenden {name}. Man teilt eine Mahlzeit und Geschichten von der Straße."
    if random.random() < 0.3:
        item = generiere_item(charakter.level, klasse_id=charakter.klasse_id)
        text += f" Zum Abschied schenkt {name} ihm {item.anzeige()}."
        return Ereignis(text=text, xp=int(10 * charakter.level), ruf=1, item=item)
    return Ereignis(text=text, xp=int(10 * charakter.level), ruf=1)


def besuche_wildnis(charakter: Charakter, welt: Welt) -> Ereignis:
    optionen = [
        "Das Gebiet erkunden (Kämpfe, Funde, alles ist möglich)",
        "Gezielt einen Dungeon aufsuchen",
        "Auf Reisende und Gesellschaft hoffen",
    ]
    idx = menu_waehlen(f"🌲 {charakter.name} bricht in die Wildnis auf.", optionen)
    if idx == 0:
        return _wildnis_erkunden(charakter, welt)
    elif idx == 1:
        return ereignis_dungeon(charakter)
    else:
        return _wildnis_reisende(charakter)


# ---------------------------------------------------------------------------
# Tempelbezirk
# ---------------------------------------------------------------------------

def _tempel_segen(charakter: Charakter) -> Ereignis:
    geheilt, mp_regen = charakter.ausruhen()
    text = f"🙏 {charakter.name} betet im Tempelbezirk und erhält einen Segen. (+{geheilt} HP, +{mp_regen} MP)"
    return Ereignis(text=text, ruf=2)


def _tempel_spende(charakter: Charakter) -> Ereignis:
    if charakter.gold < 10:
        text = f"🙏 {charakter.name} würde gerne spenden, doch der Geldbeutel ist zu leer."
        return Ereignis(text=text)
    spende = min(charakter.gold, random.randint(10, 50))
    text = f"🙏 {charakter.name} spendet {spende} Gold für die Armen der Stadt."
    return Ereignis(text=text, gold=-spende, ruf=6)


def _tempel_priester(charakter: Charakter) -> Ereignis:
    name = random.choice(NPC_VORNAMEN)
    text = f"⛩️ Priester(in) {name} führt ein langes Gespräch mit {charakter.name} über Schicksal und Bestimmung."
    return Ereignis(text=text, xp=int(20 * charakter.level))


def besuche_tempelbezirk(charakter: Charakter) -> Ereignis:
    optionen = ["Beten und einen Segen erhalten (HP & MP)", "Für die Armen spenden", "Mit einem Priester sprechen"]
    idx = menu_waehlen(f"⛩️ {charakter.name} betritt den Tempelbezirk.", optionen)
    if idx == 0:
        return _tempel_segen(charakter)
    elif idx == 1:
        return _tempel_spende(charakter)
    else:
        return _tempel_priester(charakter)


# ---------------------------------------------------------------------------
# Adelsviertel (für Abenteurer mit hohem Ruf)
# ---------------------------------------------------------------------------

def _adel_audienz(charakter: Charakter, welt: Welt) -> Ereignis:
    koenigreich = welt.zufaelliges_koenigreich()
    text = f"🏰 {charakter.name} erhält eine Audienz bei Vertretern von {koenigreich.name}."
    if random.random() < 0.6:
        koenigreich.beziehung_zum_spieler += random.randint(5, 15)
        text += " Das Gespräch verläuft überraschend gut."
        return Ereignis(text=text, ruf=5, xp=int(20 * charakter.level))
    text += " Die Atmosphäre bleibt frostig."
    return Ereignis(text=text, xp=int(10 * charakter.level))


def _adel_intrige(charakter: Charakter) -> Ereignis:
    text = f"🏰 {charakter.name} wird Zeuge einer höfischen Intrige und muss entscheiden, ob er sie meldet oder für sich behält."
    if random.random() < 0.5:
        text += " Er meldet sie - und gewinnt das Vertrauen des Hofes."
        return Ereignis(text=text, ruf=8, xp=int(20 * charakter.level))
    text += " Er behält sein Wissen für sich - eine mächtige Karte für die Zukunft."
    return Ereignis(text=text, gold=random.randint(20, 80), xp=int(15 * charakter.level))


def besuche_adelsviertel(charakter: Charakter, welt: Welt) -> Ereignis:
    optionen = ["Um eine Audienz bitten", "Sich im Hof umhören"]
    idx = menu_waehlen(f"🏰 {charakter.name} betritt das Adelsviertel.", optionen)
    if idx == 0:
        return _adel_audienz(charakter, welt)
    return _adel_intrige(charakter)


# ---------------------------------------------------------------------------
# Übungsplatz
# ---------------------------------------------------------------------------

def _aufstiegsklasse_waehlen(charakter: Charakter) -> Ereignis:
    pfad = AUFSTIEGSPFADE[charakter.klasse_id]
    standard_tier = charakter.klasse.tier_fuer_level(30)
    neue_faehigkeiten = ", ".join(s.name for s in pfad["skills"])
    optionen = [
        f"{standard_tier.name} - {standard_tier.beschreibung}",
        f"{pfad['tier30'].name} - {pfad['tier30'].beschreibung} (Neue Fähigkeiten: {neue_faehigkeiten})",
    ]
    idx = menu_waehlen(
        f"✨ {charakter.name} steht an einem Wendepunkt der Ausbildung. Welche Aufstiegsklasse soll es sein?",
        optionen,
    )
    if idx == 1:
        charakter.spezialisierung = "Alternative"
        text = f"✨ {charakter.name} beschreitet einen neuen Weg und wird zu: {pfad['tier30'].name}! {pfad['kurzbeschreibung']}"
        return Ereignis(text=text, ist_wichtig=True)
    charakter.spezialisierung = "Standard"
    text = f"⚔️ {charakter.name} bleibt dem angestammten Weg treu und wird zu: {standard_tier.name}!"
    return Ereignis(text=text, ist_wichtig=True)


def besuche_uebungsplatz(charakter: Charakter) -> Ereignis:
    aufstieg_verfuegbar = (
        charakter.level >= 30 and charakter.klasse_id in AUFSTIEGSPFADE and charakter.spezialisierung is None
    )
    if aufstieg_verfuegbar:
        optionen = ["Trainieren", "✨ Deine Aufstiegsklasse wählen"]
        idx = menu_waehlen(f"🎯 {charakter.name} erreicht den Übungsplatz.", optionen)
        if idx == 1:
            return _aufstiegsklasse_waehlen(charakter)

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


# ---------------------------------------------------------------------------
# Interaktiver Kampf (CLI)
# ---------------------------------------------------------------------------

def _verbuendeter_text(ziel, charakter) -> str:
    if ziel is charakter:
        return f"Dich selbst ({charakter.name}) - HP {charakter.hp_aktuell}/{charakter.hp_max}"
    return f"{ziel.name} ({ziel.rolle}) - HP {ziel.hp_aktuell}/{ziel.hp_max}"


def _kampf_runde_anzeigen(kampf) -> None:
    charakter = kampf.charakter
    aktionen = kampf.verfuegbare_aktionen()
    texte = []
    for aktion in aktionen:
        aoe_hinweis = " [Alle Gegner]" if aktion != "Angriff" and skill_ist_aoe(aktion) else ""
        signatur_hinweis = " ⭐[Signatur, 1x/Kampf]" if aktion != "Angriff" and skill_ist_signatur(aktion) else ""
        if aktion == "Angriff":
            texte.append("Angriff (Grundangriff)")
        else:
            skill = charakter.gelernte_skills[aktion]
            texte.append(f"{aktion} (Lv.{skill.level}){aoe_hinweis}{signatur_hinweis}")

    gegner_status = "  |  ".join(f"{g.name}: {g.hp}/{g.hp_max} HP" for g in kampf.gegner_lebend())
    titel = f"⚔️ Runde {kampf.runde + 1} - {charakter.name}: {charakter.hp_aktuell}/{charakter.hp_max} HP  |  {gegner_status}"
    idx = menu_waehlen(titel, texte)
    gewaehlte_aktion = aktionen[idx]

    gegner_ziel = None
    verbuendeter_ziel = None
    ziel_typ = kampf.ziel_typ(gewaehlte_aktion)
    if ziel_typ == "gegner":
        gegner_optionen = kampf.gegner_lebend()
        g_texte = [f"{g.name} - {g.hp}/{g.hp_max} HP" for g in gegner_optionen]
        g_idx = menu_waehlen(f"Wen soll {gewaehlte_aktion} treffen?", g_texte)
        gegner_ziel = gegner_optionen[g_idx]
    elif ziel_typ == "verbuendeter":
        verbuendete_optionen = kampf.verbuendete_lebend()
        v_texte = [_verbuendeter_text(v, charakter) for v in verbuendete_optionen]
        v_idx = menu_waehlen(f"Auf wen soll {gewaehlte_aktion} gewirkt werden?", v_texte)
        verbuendeter_ziel = verbuendete_optionen[v_idx]

    for zeile in kampf.runde_ausfuehren(gewaehlte_aktion, gegner_ziel=gegner_ziel, verbuendeter_ziel=verbuendeter_ziel):
        print(zeile)


def kampf_interaktiv_ausfuehren(ergebnis_oder_kampfstart):
    """Treibt eine Kette von Kampfstart-Objekten (z.B. mehrere Dungeon-Kämpfe
    in Folge) interaktiv voran, bis ein endgültiges Ereignis vorliegt - der
    Spieler wählt dabei jede Runde selbst die Fähigkeit seines Charakters."""
    while isinstance(ergebnis_oder_kampfstart, Kampfstart):
        kampf = ergebnis_oder_kampfstart.kampf
        print(f"\n{kampf.log[-1]}")
        while not kampf.beendet:
            _kampf_runde_anzeigen(kampf)
        ergebnis_oder_kampfstart = ergebnis_oder_kampfstart.bei_abschluss(kampf.ergebnis())
    return ergebnis_oder_kampfstart


# ---------------------------------------------------------------------------
# Master-Dispatcher
# ---------------------------------------------------------------------------

def besuche_ort(charakter: Charakter, welt: Welt) -> tuple[str, Ereignis]:
    ort_id = waehle_ort(charakter)
    ort = ORTE[ort_id]

    if ort_id == "taverne":
        ereignis = besuche_taverne(charakter)
    elif ort_id == "marktplatz":
        ereignis = besuche_marktplatz(charakter, welt)
    elif ort_id == "gildenviertel":
        ereignis = besuche_gildenviertel(charakter, welt)
    elif ort_id == "wildnis":
        ereignis = besuche_wildnis(charakter, welt)
    elif ort_id == "tempelbezirk":
        ereignis = besuche_tempelbezirk(charakter)
    elif ort_id == "adelsviertel":
        ereignis = besuche_adelsviertel(charakter, welt)
    elif ort_id == "inventar":
        ereignis = inventar_verwalten(charakter)
    elif ort_id == "gruppe":
        ereignis = besuche_gruppe(charakter)
    else:
        ereignis = besuche_uebungsplatz(charakter)

    if isinstance(ereignis, Kampfstart):
        ereignis = kampf_interaktiv_ausfuehren(ereignis)

    return f"{ort.icon} {ort.name}", ereignis

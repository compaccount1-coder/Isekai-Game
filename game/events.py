"""Zufallsereignisse: der inhaltliche Kern für Varianz zwischen Spieldurchläufen."""

import random
from dataclasses import dataclass, field

from game.character import Charakter
from game.combat import Kampfstart, erwartete_kampfkraft, kampf_starten, zufaelliger_gegner_gruppe
from game.items import generiere_item
from game.races import DAEMONEN_NAMEN, VOELKER, Dungeon, generiere_dungeon, zufaelliges_volk
from game.world import Welt

NPC_VORNAMEN = [
    "Aria", "Faelan", "Thrain", "Sylvara", "Korgan", "Elowen", "Baldric", "Nyssa", "Draven", "Isolde",
    "Kael", "Wren", "Osric", "Talia", "Bram", "Mira", "Fenris", "Rosalind", "Torvald", "Seraphine",
]


@dataclass
class Ereignis:
    text: str
    xp: int = 0
    gold: int = 0
    ruf: int = 0
    schaden: int = 0
    item: object = None  # Item, falls gefunden
    ruf_bei_volk: tuple[str, int] | None = None
    ist_wichtig: bool = False  # markiert Story-relevante Momente stärker in der Ausgabe
    log: list = field(default_factory=list)  # zusätzliche Zeilen, z.B. Kampfrundenprotokoll
    kostet_aktion: bool = True  # verbraucht eine der täglichen Aktionen (siehe MAX_AKTIONEN_PRO_TAG)
    beendet_tag: bool = False  # nur das Schlafen in der Taverne beendet den Tag


# ---------------------------------------------------------------------------
# Kampf- und Dungeon-Ereignisse
# ---------------------------------------------------------------------------

def ereignis_kampfbegegnung(charakter: Charakter) -> "Ereignis | Kampfstart":
    gruppe = zufaelliger_gegner_gruppe(charakter.level)
    namen = " und ".join(n for n, _ in gruppe)
    einleitung = f"⚔️ {charakter.name} trifft auf {namen}!"
    kampf = kampf_starten(charakter, gegnergruppe=gruppe)

    def bei_abschluss(ergebnis):
        charakter.besiegte_gegner += len(gruppe) if ergebnis.sieg else 0
        schluss = f"{charakter.name} besiegt {ergebnis.gegner}!" if ergebnis.sieg else f"{charakter.name} muss sich vor {ergebnis.gegner} zurückziehen."
        log = ergebnis.log[1:] if ergebnis.log else []  # erste Zeile war die Begegnungs-Ansage, ersetzt durch `einleitung`
        log.append(schluss)
        return Ereignis(text=einleitung, xp=ergebnis.xp_gewonnen, gold=ergebnis.gold_gewonnen, log=log)

    return Kampfstart(kampf, bei_abschluss)


def ereignis_dungeon(charakter: Charakter) -> "Ereignis | Kampfstart":
    dungeon: Dungeon = generiere_dungeon(charakter.level)
    monster_text = " und ".join(dungeon.monster)
    text = f"🏚️ {charakter.name} betritt {dungeon.name} (Gefahrenstufe {dungeon.gefahrenstufe}) - dort lauern {monster_text}."
    basis_staerke = erwartete_kampfkraft(charakter.level)
    monster_liste = list(dungeon.monster)

    def naechstes_monster(gesamt_log, gesamt_xp, gesamt_gold):
        if not monster_liste:
            return _dungeon_boss(charakter, dungeon, basis_staerke, text, gesamt_log, gesamt_xp, gesamt_gold)
        monster = monster_liste.pop(0)
        # Jeder einzelne Dungeon-Gegner ist etwas schwächer als eine volle
        # Solo-Begegnung, da mehrere davon in Folge bestritten werden müssen.
        staerke = int(basis_staerke * (dungeon.gefahrenstufe / 6) * random.uniform(0.55, 0.85))
        kampf = kampf_starten(charakter, monster, staerke)

        def bei_abschluss(ergebnis):
            neues_log = gesamt_log + ergebnis.log
            neues_xp = gesamt_xp + ergebnis.xp_gewonnen
            neues_gold = gesamt_gold + ergebnis.gold_gewonnen
            if not charakter.lebendig:
                neues_log.append("Der Dungeon fordert den höchsten Preis...")
                return Ereignis(text=text, xp=neues_xp, gold=neues_gold, log=neues_log)
            if not ergebnis.sieg:
                neues_log.append(f"Zu stark! {charakter.name} zieht sich rechtzeitig zurück, bevor es zu spät ist.")
                return Ereignis(text=text, xp=neues_xp, gold=neues_gold, log=neues_log)
            return naechstes_monster(neues_log, neues_xp, neues_gold)

        return Kampfstart(kampf, bei_abschluss)

    return naechstes_monster([], 0, 0)


def _dungeon_boss(charakter, dungeon, basis_staerke, text, gesamt_log, gesamt_xp, gesamt_gold):
    # Boss-Kampf: die reguläre Monsterwache ist überwunden, doch der Herrscher
    # des Dungeons erwartet noch einen letzten, härteren Kampf.
    boss_name = f"Wächter von {dungeon.name}"
    boss_staerke = int(basis_staerke * (dungeon.gefahrenstufe / 5) * random.uniform(1.1, 1.5))
    kampf = kampf_starten(charakter, boss_name, boss_staerke)
    gesamt_log = gesamt_log + [f"👑 Der Weg ist frei - {boss_name} erhebt sich zum letzten Kampf!"]

    def bei_abschluss(ergebnis):
        neues_log = gesamt_log + ergebnis.log
        neues_xp = gesamt_xp + ergebnis.xp_gewonnen
        neues_gold = gesamt_gold + ergebnis.gold_gewonnen
        if not charakter.lebendig:
            neues_log.append("Der Dungeon-Wächter fordert den höchsten Preis...")
            return Ereignis(text=text, xp=neues_xp, gold=neues_gold, log=neues_log)
        if ergebnis.sieg:
            # Garantierter hochwertiger Boss-Loot, plus Chance auf ein weiteres reguläres Fundstück.
            boss_item = generiere_item(charakter.level, mindest_seltenheit="Selten")
            neues_log.append(f"{charakter.name} durchquert den gesamten Dungeon siegreich!")
            if random.random() < 0.4:
                neues_log.append(charakter.fund_verarbeiten(generiere_item(charakter.level)))
            return Ereignis(text=text, xp=neues_xp, gold=neues_gold, item=boss_item, log=neues_log, ist_wichtig=True)
        else:
            neues_log.append(f"{boss_name} erweist sich als zu mächtig - {charakter.name} zieht sich mit der bisherigen Beute zurück.")
            return Ereignis(text=text, xp=neues_xp, gold=neues_gold, log=neues_log)

    return Kampfstart(kampf, bei_abschluss)


# ---------------------------------------------------------------------------
# Dämonische Ereignisse
# ---------------------------------------------------------------------------

def ereignis_daemon(charakter: Charakter) -> "Ereignis | Kampfstart":
    daemon = random.choice(DAEMONEN_NAMEN)
    # Dämonen sind bewusst als echte Herausforderung gedacht - spürbar über
    # der erwarteten Kampfkraft für das aktuelle Level. erwartete_kampfkraft
    # liegt allerdings selbst schon ca. 20-25% über der tatsächlichen
    # Kampfkraft eines Durchschnittscharakters, daher reicht dieser moderatere
    # Faktor bereits für eine echte Herausforderung, ohne auf niedrigem Level
    # (kaum Skills, keine Begleiter) fast immer tödlich zu sein.
    staerke = int(erwartete_kampfkraft(charakter.level) * random.uniform(0.75, 1.1))
    einleitung = f"👹 Ein Riss zur Dämonenebene öffnet sich - {daemon} tritt hervor!"
    kampf = kampf_starten(charakter, daemon, staerke)

    def bei_abschluss(ergebnis):
        log = ergebnis.log[1:] if ergebnis.log else []  # erste Zeile war die generische Begegnungs-Ansage
        if ergebnis.sieg:
            log.append(f"{charakter.name} bannt {daemon} zurück in den Abgrund!")
            return Ereignis(text=einleitung, xp=ergebnis.xp_gewonnen * 2, gold=ergebnis.gold_gewonnen, ruf=10, log=log, ist_wichtig=True)
        else:
            log.append(f"{charakter.name} ist dem Wesen nicht gewachsen und flieht knapp mit dem Leben davon.")
            return Ereignis(text=einleitung, xp=ergebnis.xp_gewonnen, ruf=-3, log=log)

    return Kampfstart(kampf, bei_abschluss)


# ---------------------------------------------------------------------------
# Schatzfunde
# ---------------------------------------------------------------------------

def ereignis_schatzfund(charakter: Charakter) -> Ereignis:
    art = random.choice(["Truhe", "Höhle", "verborgenes Grab", "Ruine", "Leiche eines gefallenen Abenteurers"])
    item = generiere_item(charakter.level)
    gold_bonus = random.randint(10, 50) * max(1, charakter.level // 10)
    text = f"💰 {charakter.name} entdeckt eine {art} und findet {gold_bonus} Gold sowie {item.anzeige()}!"
    return Ereignis(text=text, gold=gold_bonus, item=item)


# ---------------------------------------------------------------------------
# NPC-Begegnungen
# ---------------------------------------------------------------------------

def ereignis_mentor(charakter: Charakter) -> Ereignis:
    name = random.choice(NPC_VORNAMEN)
    volk = zufaelliges_volk()
    text = (
        f"🧙 {name}, ein{'e' if volk.name.endswith('e') else ''} weise{'r' if not volk.name.endswith('e') else ''} "
        f"{volk.name.rstrip('e')} mit jahrzehntelanger Erfahrung, nimmt {charakter.name} unter die Fittiche "
        f"und teilt wertvolles Wissen."
    )
    return Ereignis(text=text, xp=int(30 * charakter.level * random.uniform(0.5, 1.2)), ruf=2)


def ereignis_rivale(charakter: Charakter) -> "Ereignis | Kampfstart":
    name = random.choice(NPC_VORNAMEN)
    text = f"😤 {name}, ein{'e' if random.random() < 0.5 else ''} ehrgeizige{'r' if random.random() < 0.5 else ''} Rivale, fordert {charakter.name} zu einem Wettstreit heraus!"
    staerke = int(erwartete_kampfkraft(charakter.level) * random.uniform(0.7, 1.05))
    kampf = kampf_starten(charakter, name, staerke)

    def bei_abschluss(ergebnis):
        log = ergebnis.log[1:] if ergebnis.log else []
        if ergebnis.sieg:
            log.append(f"{charakter.name} gewinnt und erntet Respekt in der Region.")
            return Ereignis(text=text, xp=ergebnis.xp_gewonnen, ruf=5, log=log)
        else:
            log.append(f"{name} triumphiert diesmal - eine bittere, aber lehrreiche Niederlage.")
            return Ereignis(text=text, xp=ergebnis.xp_gewonnen // 2, ruf=-2, log=log)

    return Kampfstart(kampf, bei_abschluss)


def ereignis_haendler(charakter: Charakter) -> Ereignis:
    name = random.choice(NPC_VORNAMEN)
    item = generiere_item(charakter.level)
    preis = int(item.wert * random.uniform(0.6, 0.9))  # Handelspreis meist unter Wert
    if charakter.gold >= preis and random.random() < 0.7:
        charakter.gold -= preis
        text = f"🛒 Der fahrende Händler {name} bietet {item.anzeige()} an - {charakter.name} kauft es für {preis}g."
        return Ereignis(text=text, item=item)
    else:
        text = f"🛒 Der fahrende Händler {name} bietet {item.anzeige()} an, doch {charakter.name} lässt das Angebot ziehen."
        return Ereignis(text=text)


# ---------------------------------------------------------------------------
# Konfliktereignisse - der Charakter muss entscheiden, wem er hilft
# ---------------------------------------------------------------------------

def ereignis_konflikt(charakter: Charakter, welt: Welt) -> Ereignis:
    volk_a = zufaelliges_volk()
    volk_b = zufaelliges_volk([k for k, v in VOELKER.items() if v is volk_a])
    konflikt_typen = [
        (f"ein Grenzstreit um fruchtbares Ackerland zwischen den {volk_a.name} und den {volk_b.name}",
         "Land"),
        (f"eine Schuldenfehde, bei der {volk_b.name}-Händler von {volk_a.name}-Kreditgebern bedrängt werden",
         "Handel"),
        (f"ein alter Blutfehde-Konflikt zwischen einer {volk_a.name}-Sippe und einer {volk_b.name}-Sippe",
         "Ehre"),
        (f"ein Streit um ein heiliges Relikt, das sowohl {volk_a.name} als auch {volk_b.name} beanspruchen",
         "Glaube"),
        (f"eine Auseinandersetzung, nachdem {volk_b.name}-Flüchtlinge in {volk_a.name}-Gebiet Zuflucht suchten",
         "Mitgefühl"),
    ]
    beschreibung, thema = random.choice(konflikt_typen)

    # Charakter "entscheidet" - gewichtet durch Persönlichkeit, falls vorhanden
    seite_a = random.random() < 0.5
    gewaehltes_volk = volk_a if seite_a else volk_b
    anderes_volk = volk_b if seite_a else volk_a

    ergebnis_zufall = random.random()
    if ergebnis_zufall < 0.7:
        text = (
            f"⚖️ {charakter.name} wird in {beschreibung} hineingezogen. "
            f"Nach reiflicher Überlegung stellt er sich auf die Seite der {gewaehltes_volk.name} - "
            f"der Konflikt wird zu ihren Gunsten beigelegt."
        )
        return Ereignis(
            text=text, xp=int(25 * charakter.level), ruf=8,
            ruf_bei_volk=(anderes_volk.name, -10), ist_wichtig=True,
        )
    else:
        text = (
            f"⚖️ {charakter.name} wird in {beschreibung} hineingezogen. "
            f"Er stellt sich auf die Seite der {gewaehltes_volk.name} - doch der Plan scheitert, "
            f"und beide Seiten bleiben unzufrieden zurück."
        )
        return Ereignis(text=text, xp=int(10 * charakter.level), ruf=-3, ist_wichtig=True)


def ereignis_moralische_entscheidung(charakter: Charakter) -> Ereignis:
    szenarien = [
        ("ein hungerndes Dorf, das um Nahrung aus seinen Vorräten bittet", 15, -5),
        ("einen gefangenen Feind, der um sein Leben fleht", 10, -8),
        ("eine Gelegenheit, einen Rivalen durch eine Lüge zu diskreditieren", -12, 15),
        ("einen verletzten Fremden am Straßenrand", 8, -3),
        ("eine Truhe voller Gold, die offensichtlich einem Waisenhaus gehört", -20, 40),
    ]
    beschreibung, ruf_gut, ruf_boese = random.choice(szenarien)
    waehlt_gut = random.random() < 0.65  # die meisten Charaktere neigen leicht zum Guten, aber nicht immer

    if waehlt_gut:
        text = f"💭 {charakter.name} steht vor {beschreibung} - und entscheidet sich für den ehrenhaften Weg."
        return Ereignis(text=text, ruf=ruf_gut, xp=int(15 * charakter.level))
    else:
        gold_bonus = abs(ruf_boese) if ruf_boese > 0 else 0
        text = f"💭 {charakter.name} steht vor {beschreibung} - und wählt den eigennützigen Weg."
        return Ereignis(text=text, ruf=ruf_boese, gold=gold_bonus, xp=int(10 * charakter.level))


# ---------------------------------------------------------------------------
# Gilden- und politische Ereignisse
# ---------------------------------------------------------------------------

def ereignis_gilde(charakter: Charakter, welt: Welt) -> Ereignis:
    _, stadt_name = welt.zufaellige_stadt()
    if charakter.gilde is None:
        gilde = random.choice(list(welt.alle_gilden.keys()))
        charakter.gilde = gilde
        text = f"🏛️ In {stadt_name} tritt {charakter.name} der {gilde} bei."
        return Ereignis(text=text, xp=int(20 * charakter.level), ist_wichtig=True)
    else:
        text = f"🏛️ Die {charakter.gilde} in {stadt_name} überträgt {charakter.name} einen anspruchsvollen Auftrag."
        gold = random.randint(20, 60) * max(1, charakter.level // 5)
        return Ereignis(text=text, xp=int(35 * charakter.level), gold=gold, ruf=4)


def ereignis_politik(charakter: Charakter, welt: Welt) -> Ereignis:
    koenigreich = welt.zufaelliges_koenigreich()
    ereignisse = [
        f"In {koenigreich.name} bricht ein Erbfolgestreit aus, nachdem der Thronfolger verschwand.",
        f"{koenigreich.name} erklärt einem Nachbarreich offen den Krieg.",
        f"Eine Bauernrebellion erschüttert die Randgebiete von {koenigreich.name}.",
        f"{koenigreich.name} schließt ein überraschendes Handelsbündnis mit einem ehemaligen Rivalen.",
        f"Ein Attentat auf einen hohen Adligen in {koenigreich.name} sorgt für Unruhe im ganzen Land.",
    ]
    text = f"👑 Neuigkeiten verbreiten sich: {random.choice(ereignisse)}"
    return Ereignis(text=text, xp=int(5 * charakter.level))


# ---------------------------------------------------------------------------
# Seltene / legendäre Ereignisse
# ---------------------------------------------------------------------------

def ereignis_legendaer(charakter: Charakter) -> Ereignis:
    ereignisse = [
        ("Ein uralter Drache spricht zu {name} in einer Vision und offenbart ein verborgenes Geheimnis der Welt.", 3.0, 0),
        ("Eine vergessene Gottheit erwacht kurz und segnet {name} mit einem Hauch göttlicher Macht.", 2.5, 100),
        ("{name} findet den Eingang zu einer Ebene jenseits der Sterblichkeit - und kehrt verändert zurück.", 2.8, 0),
        ("Ein sprechendes, uraltes Artefakt erwählt {name} als seinen neuen Träger.", 2.2, 0),
        ("Die Fäden des Schicksals selbst scheinen sich um {name} zu verweben - Wahrsager überall sprechen davon.", 2.0, 0),
    ]
    vorlage, xp_mult, gold = random.choice(ereignisse)
    text = "🌟 " + vorlage.format(name=charakter.name)
    item = generiere_item(charakter.level, typ=None) if random.random() < 0.5 else None
    return Ereignis(
        text=text, xp=int(50 * charakter.level * xp_mult), gold=gold, ruf=15,
        item=item, ist_wichtig=True,
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

EREIGNIS_GEWICHTE = {
    "kampf": 22, "dungeon": 14, "daemon": 6, "schatz": 12, "mentor": 6,
    "rivale": 8, "haendler": 8, "konflikt": 10, "moral": 8, "gilde": 8, "politik": 4, "legendaer": 2,
}


def zufallsereignis(charakter: Charakter, welt: Welt) -> "Ereignis | Kampfstart":
    kategorien = list(EREIGNIS_GEWICHTE.keys())
    werte = list(EREIGNIS_GEWICHTE.values())
    kategorie = random.choices(kategorien, weights=werte, k=1)[0]

    dispatch = {
        "kampf": lambda: ereignis_kampfbegegnung(charakter),
        "dungeon": lambda: ereignis_dungeon(charakter),
        "daemon": lambda: ereignis_daemon(charakter),
        "schatz": lambda: ereignis_schatzfund(charakter),
        "mentor": lambda: ereignis_mentor(charakter),
        "rivale": lambda: ereignis_rivale(charakter),
        "haendler": lambda: ereignis_haendler(charakter),
        "konflikt": lambda: ereignis_konflikt(charakter, welt),
        "moral": lambda: ereignis_moralische_entscheidung(charakter),
        "gilde": lambda: ereignis_gilde(charakter, welt),
        "politik": lambda: ereignis_politik(charakter, welt),
        "legendaer": lambda: ereignis_legendaer(charakter),
    }
    return dispatch[kategorie]()

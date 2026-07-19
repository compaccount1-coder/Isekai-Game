"""Rundenbasiertes Kampfsystem: der Charakter setzt in jeder Runde eine seiner
erlernten Fähigkeiten ein, sichtbar mit Schaden und verbleibenden HP beider Seiten.
Begleiter kämpfen autonom mit und handeln passend zu ihrer Rolle: Nahkämpfer
binden die Aufmerksamkeit des Gegners und mindern so den Schaden am Anführer,
Fernkämpfer greifen zusätzlich an, Unterstützer heilen die Gruppe."""

import random
from dataclasses import dataclass, field

from game.classes import KLASSEN

GEGNER_NAMEN_SCHWACH = [
    "Wilder Wolf", "Riesenspinne", "Wegelagerer", "Verrotteter Zombie", "Kobold-Plünderer",
    "Verwilderter Eber", "Diebische Kobolde", "Giftschlange", "Streunende Hyäne", "Skelettkrieger",
]
GEGNER_NAMEN_MITTEL = [
    "Oger-Schläger", "Dunkelelf-Assassine", "Verfluchter Ritter", "Höhlentroll", "Werwolf",
    "Banditenhauptmann", "Ghul-Horde", "Steinelementar", "Harpyien-Schwarm", "Nekromanten-Lehrling",
]
GEGNER_NAMEN_STARK = [
    "Jungdrache", "Dämonenfürst", "Erzlich", "Chimäre", "Titan aus Stein",
    "Gefallener Erzengel", "Kraken der Tiefe", "Uralter Vampirgraf", "Frostriese", "Feuerdämon",
]
GEGNER_NAMEN_BOSS = [
    "Der Drachenkönig", "Herold der Apokalypse", "Der namenlose Gott", "Königin der Verdammten",
    "Der letzte Titan", "Aschenfürst der tausend Kriege", "Der schlafende Weltenfresser",
]

# ---------------------------------------------------------------------------
# Gegner-Fähigkeiten - benannte Angriffe statt eines generischen "kontert",
# damit auch Standard- und Trash-Mob-Kämpfe abwechslungsreich wirken.
# ---------------------------------------------------------------------------

GEGNER_ANGRIFFE_SCHWACH = [
    "beißt wild um sich", "krallt sich fest und reißt zu", "stürmt ungestüm vor",
    "schlägt hastig zu", "faucht und hackt zu", "rammt mit voller Wucht",
]
GEGNER_ANGRIFFE_MITTEL = [
    "holt zu einem wuchtigen Hieb aus", "umkreist geschickt und schlägt zu",
    "setzt zu einem finsteren Fluch an", "durchbricht die Deckung mit roher Kraft",
    "schleudert einen Splitterhagel", "hetzt mit einer Kombination aus Hieben",
]
GEGNER_ANGRIFFE_STARK = [
    "entfesselt eine Welle dunkler Energie", "durchbohrt mit einer verheerenden Klauen-Kombo",
    "atmet versengende Glut", "reißt den Boden mit einem gewaltigen Schlag auf",
    "lässt eine Druckwelle aus purer Macht los",
]
GEGNER_ANGRIFFE_BOSS = [
    "ruft die volle Macht des Ortes herbei", "schlägt mit erdzerschmetternder Wucht zu",
    "entfesselt einen verheerenden Schwall dunkler Energie", "setzt zum finalen Sturmangriff an",
    "lässt die Umgebung selbst gegen dich kämpfen",
]

# Einzigartige Angriffsnamen für die Schlüsselfiguren der Dämonenkönig-Handlung -
# jede Konfrontation soll sich spürbar anders anfühlen als ein gewöhnlicher Kampf.
GEGNER_ANGRIFFE_SPEZIAL: dict[str, list[str]] = {
    "Malgorath, die Verschlingende Klaue": [
        "reißt mit der Verschlingenden Klaue zu", "verschlingt einen Teil des Schlachtfelds und wächst",
        "peitscht mit einem monströsen Schweif", "brüllt und lässt die Erde erzittern",
    ],
    "Nyxandra, Herrin der tausend Schnitte": [
        "wirbelt durch ein Dutzend blitzschneller Schnitte", "verschwindet im Schattenrauch und schlägt aus dem Nichts zu",
        "lässt tausend Klingen aus dem Nichts regnen", "gleitet lautlos heran und trifft mehrfach",
    ],
    "Vorgrimm der Unaufhaltsame": [
        "rammt mit der Wucht eines einstürzenden Turms", "zermalmt mit gepanzerten Fäusten",
        "stampft die Erde zu Bruchstücken", "walzt mit unaufhaltsamer Wucht vor",
    ],
    "Seliphrae, die Flüsternde Seuche": [
        "flüstert einen Fluch, der von innen zehrt", "lässt eine Wolke aus Verwesung strömen",
        "zerfrisst die Widerstandskraft mit stiller Seuche", "berührt mit fauligen Fingern",
    ],
    "Abraxos, der Dämonenkönig": [
        "entfesselt einen Sturm aus reiner Finsternis", "lässt die Welt selbst erzittern",
        "ruft die geballte Macht aller gefallenen Legionen herbei", "zerreißt die Realität mit einem einzigen Schlag",
        "lässt Asche und Schatten auf das Schlachtfeld regnen",
    ],
}


def _gegnerpool(spieler_level: int) -> tuple[list[str], int]:
    # Gegnerstärke wird direkt aus erwartete_kampfkraft(level) abgeleitet statt
    # aus einer festen Bandbreite pro Levelblock - eine feste Spanne (z.B.
    # 30-85 für Level 1-14) ließ frühe Charaktere gegen Gegner antreten, die
    # weit über ihrer tatsächlichen Kampfkraft lagen (Level 1 ~= 51 Kampfkraft,
    # aber bis zu 85 Gegnerstärke möglich -> quasi unbesiegbar, siehe Balance-
    # Testreihe mit Toden auf Level 2). Die Bandbreite bleibt unterhalb des
    # Referenzwerts, da erwartete_kampfkraft selbst bereits über der
    # tatsächlichen Kampfkraft eines Durchschnittscharakters liegt.
    erwartet = erwartete_kampfkraft(spieler_level)
    staerke = int(erwartet * random.uniform(0.5, 0.85))
    if spieler_level < 15:
        return GEGNER_NAMEN_SCHWACH, staerke
    elif spieler_level < 40:
        return GEGNER_NAMEN_MITTEL, staerke
    elif spieler_level < 75:
        return GEGNER_NAMEN_STARK, staerke
    else:
        return GEGNER_NAMEN_BOSS, staerke


def zufaelliger_gegner(spieler_level: int) -> tuple[str, int]:
    pool, staerke = _gegnerpool(spieler_level)
    return random.choice(pool), staerke


def erwartete_kampfkraft(level: int) -> int:
    """Grobe Schätzung der Kampfkraft eines durchschnittlichen Charakters auf
    diesem Level - Referenzwert, um Dungeon- und Sonderbegegnungen proportional
    zur eigentlichen Kampfformel in character.py zu skalieren."""
    return int(56 + 8.3 * level)


def _angriffe_fuer(name: str, staerke: int) -> list[str]:
    if name in GEGNER_ANGRIFFE_SPEZIAL:
        return GEGNER_ANGRIFFE_SPEZIAL[name]
    if name.startswith("Wächter von") or name == "Prüfungswächter":
        return GEGNER_ANGRIFFE_BOSS
    if staerke < 150:
        return GEGNER_ANGRIFFE_SCHWACH
    elif staerke < 400:
        return GEGNER_ANGRIFFE_MITTEL
    elif staerke < 800:
        return GEGNER_ANGRIFFE_STARK
    else:
        return GEGNER_ANGRIFFE_BOSS


@dataclass
class Kampfgegner:
    name: str
    hp: int
    hp_max: int
    angriffskraft: int
    angriffe: list[str] = field(default_factory=list)


def _erzeuge_gegner(name: str, staerke: int) -> Kampfgegner:
    hp = max(10, int(staerke * random.uniform(1.6, 2.2)))
    return Kampfgegner(name=name, hp=hp, hp_max=hp, angriffskraft=staerke, angriffe=_angriffe_fuer(name, staerke))


def _waehle_skill_fuer_runde(charakter) -> tuple[str, int]:
    """Wählt eine Fähigkeit für diese Runde - höherstufige Skills werden
    bevorzugt eingesetzt, aber nicht ausschließlich. Gibt (Name, Skill-Level)
    zurück, oder ('Angriff', 0) falls noch keine Skills bekannt sind."""
    if not charakter.gelernte_skills:
        return "Angriff", 0
    skills = list(charakter.gelernte_skills.values())
    gewichte = [s.level + 1 for s in skills]
    gewaehlt = random.choices(skills, weights=gewichte, k=1)[0]
    return gewaehlt.name, gewaehlt.level


def _begleiter_runde(charakter, gegner: "Kampfgegner", log: list[str]) -> float:
    """Lässt jeden Begleiter autonom eine zu seiner Rolle passende Aktion
    ausführen. Nahkämpfer binden die Aufmerksamkeit des Gegners (Tank) und
    mindern dadurch den Schaden, den der Anführer diese Runde erleidet;
    Fernkämpfer greifen zusätzlich an; Unterstützer heilen die Gruppe.
    Gibt die daraus resultierende Schadensreduktion für den kommenden
    Gegnerangriff zurück."""
    schadensreduktion = 0.0
    basis_pro_begleiter = charakter.kampfkraft_basis() * 0.18
    for b in charakter.begleiter:
        if gegner.hp <= 0:
            break
        anteil = basis_pro_begleiter * (b.loyalitaet / 100) * (b.level / max(1, charakter.level))
        if anteil <= 1:
            continue
        skill_pool = KLASSEN[b.klasse_id].skills
        anzahl_verfuegbar = max(2, min(len(skill_pool), 2 + b.level // 15))
        skill = random.choice(skill_pool[:anzahl_verfuegbar])

        if b.rolle == "Fernkämpfer":
            schaden = max(1, int(anteil * random.uniform(0.9, 1.3)))
            gegner.hp = max(0, gegner.hp - schaden)
            log.append(f"   {b.name} setzt {skill.name} ein und trifft {gegner.name} - {schaden} Schaden. [{gegner.name}: {gegner.hp}/{gegner.hp_max} HP]")
        elif b.rolle == "Unterstützer":
            if charakter.hp_aktuell < charakter.hp_max:
                heilung = min(charakter.hp_max - charakter.hp_aktuell, max(1, int(anteil * random.uniform(0.8, 1.2))))
                charakter.hp_aktuell += heilung
                log.append(f"   {b.name} setzt {skill.name} ein und heilt {charakter.name} um {heilung} HP. [{charakter.name}: {charakter.hp_aktuell}/{charakter.hp_max} HP]")
            else:
                log.append(f"   {b.name} setzt {skill.name} ein und stärkt die Gruppe.")
        else:  # Nahkämpfer - zieht als Tank die Aufmerksamkeit auf sich
            schaden = max(1, int(anteil * random.uniform(0.5, 0.8)))
            gegner.hp = max(0, gegner.hp - schaden)
            schadensreduktion += 0.12
            log.append(f"   {b.name} setzt {skill.name} ein, zieht {gegner.name}s Aufmerksamkeit auf sich und trifft für {schaden} Schaden. [{gegner.name}: {gegner.hp}/{gegner.hp_max} HP]")

        if gegner.hp <= 0:
            log.append(f"   💀 {gegner.name} ist besiegt!")
    return min(schadensreduktion, 0.4)


@dataclass
class Kampfergebnis:
    sieg: bool
    gegner: str
    xp_gewonnen: int
    gold_gewonnen: int
    log: list[str] = field(default_factory=list)
    gestorben: bool = False
    runden: int = 0


class Kampf:
    """Ein rundenbasierter Kampf als eigener Zustand statt einer einzigen,
    bis zum Ende durchlaufenden Funktion - so kann der Spieler zwischen den
    Runden selbst entscheiden, welche Fähigkeit sein Charakter einsetzt,
    egal ob über ein Terminal-Menü (CLI) oder Buttons (GUI)."""

    def __init__(self, charakter, gegner: Kampfgegner, gegner_staerke_basis: int, max_runden: int = 8):
        self.charakter = charakter
        self.gegner = gegner
        self.gegner_staerke_basis = gegner_staerke_basis
        self.max_runden = max_runden
        self.runde = 0
        self.log: list[str] = [f"⚔️ {charakter.name} trifft auf {gegner.name} ({gegner.hp} HP)!"]
        self.beendet = False
        self.sieg = False

    def verfuegbare_aktionen(self) -> list[str]:
        """Die Fähigkeiten, aus denen der Spieler diese Runde wählen kann."""
        if not self.charakter.gelernte_skills:
            return ["Angriff"]
        return list(self.charakter.gelernte_skills.keys())

    def runde_ausfuehren(self, gewaehlte_aktion: str) -> list[str]:
        """Führt eine komplette Kampfrunde mit der vom Spieler gewählten
        Fähigkeit aus (eigener Angriff, Begleiter-Aktionen, Gegenangriff) und
        gibt die neuen Log-Zeilen zurück. Setzt self.beendet/self.sieg, sobald
        der Kampf danach entschieden ist."""
        if self.beendet:
            return []
        charakter = self.charakter
        gegner = self.gegner
        zeilen = [f"-- Runde {self.runde + 1} --"]
        self.runde += 1

        if charakter.hp_aktuell < charakter.hp_max * 0.3:
            trank_meldung = charakter.bestes_trank_automatisch_nutzen("Heilung")
            if trank_meldung:
                zeilen.append(f"   {trank_meldung}")

        if gewaehlte_aktion != "Angriff" and gewaehlte_aktion in charakter.gelernte_skills:
            skill_level = charakter.gelernte_skills[gewaehlte_aktion].level
        else:
            gewaehlte_aktion = "Angriff"
            skill_level = 0

        kampfkraft_basis = charakter.kampfkraft_basis()
        schaden = int(kampfkraft_basis * random.uniform(0.22, 0.32) * (1 + skill_level * 0.06))
        kritisch = random.random() < 0.12
        if kritisch:
            schaden = int(schaden * 1.6)
        gegner.hp = max(0, gegner.hp - schaden)

        krit_text = " (KRITISCHER TREFFER!)" if kritisch else ""
        if gewaehlte_aktion == "Angriff":
            zeilen.append(f"   {charakter.name} greift an{krit_text} - {schaden} Schaden. [{gegner.name}: {gegner.hp}/{gegner.hp_max} HP]")
        else:
            zeilen.append(f"   {charakter.name} setzt {gewaehlte_aktion} ein{krit_text} - {schaden} Schaden. [{gegner.name}: {gegner.hp}/{gegner.hp_max} HP]")

        if gegner.hp <= 0:
            zeilen.append(f"   💀 {gegner.name} ist besiegt!")
            self.beendet = True
            self.sieg = True
            self.log.extend(zeilen)
            return zeilen

        schadensreduktion = _begleiter_runde(charakter, gegner, zeilen)
        if gegner.hp <= 0:
            self.beendet = True
            self.sieg = True
            self.log.extend(zeilen)
            return zeilen

        angriffsname = random.choice(gegner.angriffe) if gegner.angriffe else "kontert"
        gegen_schaden = int(gegner.angriffskraft * random.uniform(0.14, 0.22))
        gegen_schaden = int(gegen_schaden * (1 - schadensreduktion - charakter.schadensreduktion()))
        charakter.hp_aktuell = max(0, charakter.hp_aktuell - gegen_schaden)
        zeilen.append(f"   {gegner.name} {angriffsname} - {gegen_schaden} Schaden. [{charakter.name}: {charakter.hp_aktuell}/{charakter.hp_max} HP]")

        if charakter.hp_aktuell <= 0:
            charakter.lebendig = False
            zeilen.append(f"   💀 {charakter.name} sinkt zu Boden...")
            self.beendet = True
            self.sieg = False
            self.log.extend(zeilen)
            return zeilen

        if self.runde >= self.max_runden:
            # Rundenlimit erreicht, ohne dass jemand gefallen ist - wer weniger
            # Anteil seiner HP verloren hat, behält das Feld.
            spieler_anteil = charakter.hp_aktuell / charakter.hp_max
            gegner_anteil = gegner.hp / gegner.hp_max
            sieg = spieler_anteil >= gegner_anteil
            if sieg:
                zeilen.append(f"   {gegner.name} zieht sich zurück - {charakter.name} behält die Oberhand.")
            else:
                zeilen.append(f"   {charakter.name} zieht sich rechtzeitig zurück.")
            self.beendet = True
            self.sieg = sieg

        self.log.extend(zeilen)
        return zeilen

    def ergebnis(self) -> Kampfergebnis:
        if self.sieg:
            xp = int(20 * self.gegner_staerke_basis * random.uniform(0.8, 1.3))
            gold = int(self.gegner_staerke_basis * random.uniform(1.5, 4))
        else:
            xp = int(5 * self.gegner_staerke_basis)
            gold = 0
        return Kampfergebnis(
            sieg=self.sieg, gegner=self.gegner.name, xp_gewonnen=xp, gold_gewonnen=gold,
            log=self.log, gestorben=not self.charakter.lebendig, runden=self.runde,
        )


def kampf_starten(charakter, gegner_name: str | None = None, gegner_staerke: int | None = None,
                   max_runden: int = 8) -> Kampf:
    """Bereitet einen neuen Kampf vor (Gegner erzeugen, Eröffnungszeile), ohne
    ihn aufzulösen - der Aufrufer (CLI-Menü oder GUI-KampfScene) treibt ihn
    danach Runde für Runde selbst voran."""
    if gegner_name is None:
        gegner_name, gegner_staerke = zufaelliger_gegner(charakter.level)
    gegner = _erzeuge_gegner(gegner_name, gegner_staerke)
    return Kampf(charakter=charakter, gegner=gegner, gegner_staerke_basis=gegner_staerke, max_runden=max_runden)


@dataclass
class Kampfstart:
    """Signalisiert, dass eine Aktion in einen interaktiven Kampf mündet,
    statt direkt ein Ereignis zu liefern. `bei_abschluss` erhält das fertige
    Kampfergebnis, sobald der Kampf vorbei ist, und liefert entweder das
    endgültige Ereignis oder - bei mehreren Kämpfen in Folge (z.B. ein
    Dungeon) - den nächsten Kampfstart."""
    kampf: Kampf
    bei_abschluss: object  # Callable[[Kampfergebnis], "Ereignis | Kampfstart"]


def rundenbasierter_kampf(charakter, gegner_name: str | None = None, gegner_staerke: int | None = None,
                           max_runden: int = 8) -> Kampfergebnis:
    """Automatisch aufgelöster Kampf ohne Spieler-Eingabe je Runde - für
    Kontexte ohne interaktive Steuerung (z.B. Tests). Die eigentliche,
    spielergesteuerte Variante ist Kampf/kampf_starten() oben, angebunden
    über game.locations (CLI) bzw. gui.scenes.KampfScene (GUI)."""
    kampf = kampf_starten(charakter, gegner_name, gegner_staerke, max_runden)
    while not kampf.beendet:
        skill_name, _ = _waehle_skill_fuer_runde(charakter)
        kampf.runde_ausfuehren(skill_name)
    return kampf.ergebnis()


def kampfstart_automatisch_aufloesen(ergebnis_oder_kampfstart):
    """Löst eine Kette von Kampfstart-Objekten automatisch auf (gewichtete
    Zufallswahl der Fähigkeiten pro Runde) und gibt das endgültige Ereignis
    zurück - praktisch für Tests oder andere nicht-interaktive Kontexte, die
    trotzdem die normalen Ereignis-/Quest-/Endgame-Funktionen aufrufen wollen."""
    while isinstance(ergebnis_oder_kampfstart, Kampfstart):
        kampf = ergebnis_oder_kampfstart.kampf
        while not kampf.beendet:
            skill_name, _ = _waehle_skill_fuer_runde(kampf.charakter)
            kampf.runde_ausfuehren(skill_name)
        ergebnis_oder_kampfstart = ergebnis_oder_kampfstart.bei_abschluss(kampf.ergebnis())
    return ergebnis_oder_kampfstart

"""Rundenbasiertes Kampfsystem: der Charakter setzt in jeder Runde eine seiner
erlernten Fähigkeiten ein, sichtbar mit Schaden und verbleibenden HP aller
Beteiligten. Jeder Skill wirkt gemäß seiner tatsächlichen Thematik (siehe
classes.SKILL_EFFEKT): Heilzauber heilen, Segen verstärken, Schilde/Reflexion
schützen (teils über mehrere Runden und teils für die gesamte Gruppe),
Schwächungszauber mindern den Gegner - manche Fähigkeiten treffen dabei
gezielt ein Ziel, andere (siehe SKILL_AOE) alle Gegner bzw. die ganze Gruppe
auf einmal. Kämpfe können gegen mehrere Gegner gleichzeitig stattfinden.
Begleiter kämpfen autonom mit und handeln passend zu ihrer Rolle und dem
gewürfelten Skill."""

import random
from dataclasses import dataclass, field

from game.classes import KLASSEN, skill_dauer, skill_effekt, skill_ist_aoe, skill_ist_signatur

# Signatur-Fähigkeiten (siehe classes.SKILL_SIGNATUR) wirken deutlich stärker
# als reguläre Fähigkeiten - sie sind der exklusive Höhepunkt der jeweiligen
# Aufstiegsklasse und dafür auf einmal pro Kampf begrenzt (siehe Kampf.signatur_verwendet).
SIGNATUR_VERSTAERKUNG = 1.8

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


def zufaelliger_gegner_gruppe(spieler_level: int) -> list[tuple[str, int]]:
    """Meistens ein einzelner Gegner, gelegentlich eine Gruppe aus 2-3 - deren
    Einzelstärke wird deutlich reduziert, damit die GESAMTE Bedrohung nicht
    einfach durch die Anzahl vervielfacht wird (mehrere Gegner greifen pro
    Runde je einmal an, das allein erhöht das Risiko schon spürbar)."""
    pool, basis_staerke = _gegnerpool(spieler_level)
    anzahl = random.choices([1, 2, 3], weights=[55, 30, 15], k=1)[0]
    if anzahl == 1:
        return [(random.choice(pool), basis_staerke)]
    faktor = {2: 0.55, 3: 0.42}[anzahl]
    pro_gegner_staerke = max(10, int(basis_staerke * faktor))
    namen = random.sample(pool, anzahl) if len(pool) >= anzahl else [random.choice(pool) for _ in range(anzahl)]
    return [(name, pro_gegner_staerke) for name in namen]


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


def _begleiter_runde(kampf: "Kampf", log: list[str]) -> float:
    """Lässt jeden (nicht niedergeschlagenen) Begleiter autonom eine zu seiner
    Rolle UND dem gewürfelten Skill passende Aktion ausführen. Nahkämpfer
    binden als Tank die Aufmerksamkeit des Gegners; Fernkämpfer greifen
    zusätzlich an; Unterstützer setzen ihre Fähigkeit gemäß deren
    tatsächlicher Wirkung ein (siehe classes.SKILL_EFFEKT). Begleiter zielen
    dabei stets auf den ersten lebenden Gegner bzw. die gesamte Gruppe -
    taktische Zielwahl bleibt dem Spieler vorbehalten, Begleiter kümmern sich
    eigenständig. Gibt die daraus resultierende Schadensreduktion für den
    kommenden Gegnerangriff zurück."""
    charakter = kampf.charakter
    schadensreduktion = 0.0
    basis_pro_begleiter = charakter.kampfkraft_basis() * 0.18
    for b in charakter.begleiter:
        if b.niedergeschlagen:
            continue
        gegner_lebend = kampf.gegner_lebend()
        if not gegner_lebend:
            break
        gegner = gegner_lebend[0]
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
            effekt = skill_effekt(skill.name)
            if effekt in ("heilung", "notheilung"):
                if charakter.hp_aktuell < charakter.hp_max:
                    mult = 1.6 if effekt == "notheilung" else 1.0
                    heilung = charakter.heilen(max(1, int(anteil * random.uniform(0.8, 1.2) * mult)))
                    log.append(f"   {b.name} setzt {skill.name} ein und heilt {charakter.name} um {heilung} HP. [{charakter.name}: {charakter.hp_aktuell}/{charakter.hp_max} HP]")
                else:
                    log.append(f"   {b.name} setzt {skill.name} ein, doch {charakter.name} braucht keine Heilung.")
            elif effekt == "gruppenheilung":
                gesamt = charakter.heilen(max(1, int(anteil * random.uniform(0.5, 0.8))))
                for andere in charakter.begleiter:
                    if andere is not b and not andere.niedergeschlagen:
                        gesamt += andere.heilen(max(1, int(anteil * random.uniform(0.4, 0.7))))
                log.append(f"   {b.name} setzt {skill.name} ein und heilt die gesamte Gruppe (insgesamt {gesamt} HP).")
            elif effekt in ("schaden", "schaden_debuff"):
                schaden = max(1, int(anteil * random.uniform(0.7, 1.0)))
                gegner.hp = max(0, gegner.hp - schaden)
                if effekt == "schaden_debuff":
                    gegner.angriffskraft = max(1, int(gegner.angriffskraft * 0.92))
                log.append(f"   {b.name} setzt {skill.name} ein und trifft {gegner.name} - {schaden} Schaden. [{gegner.name}: {gegner.hp}/{gegner.hp_max} HP]")
            elif effekt == "buff":
                kampf.spieler_bonus_naechste_runde += 0.15
                log.append(f"   {b.name} setzt {skill.name} ein und verstärkt {charakter.name}s nächsten Angriff.")
            elif effekt == "debuff":
                gegner.angriffskraft = max(1, int(gegner.angriffskraft * 0.92))
                log.append(f"   {b.name} setzt {skill.name} ein und schwächt {gegner.name}.")
            else:  # schild / aggro / gruppenschild / reflexion (Begleiter wirken diese nur einmalig, kein Dauerzustand)
                schadensreduktion += 0.15
                log.append(f"   {b.name} setzt {skill.name} ein und schirmt {charakter.name} ab.")
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
    Runden selbst entscheiden, welche Fähigkeit sein Charakter einsetzt und
    (falls nötig) wen er damit anvisiert, egal ob über ein Terminal-Menü (CLI)
    oder Buttons (GUI). Unterstützt mehrere gleichzeitige Gegner."""

    def __init__(self, charakter, gegnergruppe: list[Kampfgegner], gegner_staerke_basis: int, max_runden: int = 8):
        self.charakter = charakter
        self.gegnergruppe = gegnergruppe
        self.gegner_staerke_basis = gegner_staerke_basis
        self.max_runden = max_runden
        self.runde = 0
        if len(gegnergruppe) > 1:
            namen = " und ".join(g.name for g in gegnergruppe)
            gesamt_hp = sum(g.hp for g in gegnergruppe)
            self.log: list[str] = [f"⚔️ {charakter.name} trifft auf {namen} ({gesamt_hp} HP gesamt, {len(gegnergruppe)} Gegner)!"]
        else:
            self.log = [f"⚔️ {charakter.name} trifft auf {gegnergruppe[0].name} ({gegnergruppe[0].hp} HP)!"]
        self.beendet = False
        self.sieg = False
        # Von Verstärkungs-Fähigkeiten gesetzt - erhöht den Schaden des
        # NÄCHSTEN eigenen Angriffs und wird danach verbraucht.
        self.spieler_bonus_naechste_runde = 0.0
        # Schild-/Gruppenschild-Zustand: schild_runden > 0 heißt aktiv, wirkt
        # auf JEDEN Treffer der Gruppe (nicht nur den Anwender), solange aktiv.
        self.schild_runden = 0
        self.schild_staerke = 0.0
        # Reflexion: ein Teil des erlittenen Schadens geht an den Angreifer zurück.
        self.reflexion_runden = 0
        self.reflexion_staerke = 0.0
        # Signatur-Fähigkeiten, die in diesem Kampf bereits eingesetzt wurden -
        # jede darf nur einmal pro Kampf gewirkt werden.
        self.signatur_verwendet: set[str] = set()

    def gegner_lebend(self) -> list[Kampfgegner]:
        return [g for g in self.gegnergruppe if g.hp > 0]

    def verbuendete_lebend(self) -> list:
        """Charakter zuerst, danach alle nicht niedergeschlagenen Begleiter -
        mögliche Ziele für Heil-/Verstärkungs-/Schutzfähigkeiten."""
        return [self.charakter] + [b for b in self.charakter.begleiter if not b.niedergeschlagen]

    def verfuegbare_aktionen(self) -> list[str]:
        """Die Fähigkeiten, aus denen der Spieler diese Runde wählen kann.
        Eine bereits in diesem Kampf verbrauchte Signatur-Fähigkeit
        verschwindet für den Rest des Kampfes aus der Auswahl."""
        if not self.charakter.gelernte_skills:
            return ["Angriff"]
        verfuegbar = [name for name in self.charakter.gelernte_skills if name not in self.signatur_verwendet]
        return verfuegbar or ["Angriff"]

    def ziel_typ(self, aktion: str) -> str | None:
        """Gibt zurück, welche Zielauswahl vor dem Einsatz einer Fähigkeit
        nötig ist: 'gegner' (einzelnen Gegner wählen), 'verbuendeter'
        (Verbündeten wählen), oder None (kein Auswahlschritt nötig - z.B.
        Selbstziel, Flächeneffekt oder nur ein gültiges Ziel vorhanden)."""
        if aktion != "Angriff" and skill_ist_aoe(aktion):
            return None
        effekt = skill_effekt(aktion) if aktion != "Angriff" else "schaden"
        if effekt in ("schaden", "debuff", "schaden_debuff"):
            return "gegner" if len(self.gegner_lebend()) > 1 else None
        if effekt in ("heilung", "notheilung", "buff", "schild", "aggro", "reflexion"):
            return "verbuendeter" if len(self.charakter.begleiter) > 0 else None
        return None  # gruppenschild/gruppenheilung wirken automatisch auf alle

    def runde_ausfuehren(self, gewaehlte_aktion: str, gegner_ziel: Kampfgegner | None = None, verbuendeter_ziel=None) -> list[str]:
        """Führt eine komplette Kampfrunde mit der vom Spieler gewählten
        Fähigkeit (und ggf. Ziel) aus. Gibt die neuen Log-Zeilen zurück und
        setzt self.beendet/self.sieg, sobald der Kampf danach entschieden ist."""
        if self.beendet:
            return []
        charakter = self.charakter
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

        # Signatur-Fähigkeiten sind auf einmal pro Kampf begrenzt - wurde sie
        # bereits gewirkt, weicht der Charakter automatisch auf einen
        # regulären Angriff aus, statt sie erneut (und damit ohne die
        # gewünschte Exklusivität) einzusetzen.
        ist_signatur = gewaehlte_aktion != "Angriff" and skill_ist_signatur(gewaehlte_aktion)
        if ist_signatur and gewaehlte_aktion in self.signatur_verwendet:
            gewaehlte_aktion = "Angriff"
            skill_level = 0
            ist_signatur = False
        elif ist_signatur:
            self.signatur_verwendet.add(gewaehlte_aktion)
            zeilen.append(f"   🌟 {charakter.name} entfesselt die Signatur-Fähigkeit {gewaehlte_aktion}!")
        signatur_mult = SIGNATUR_VERSTAERKUNG if ist_signatur else 1.0

        effekt = skill_effekt(gewaehlte_aktion) if gewaehlte_aktion != "Angriff" else "schaden"
        aoe = gewaehlte_aktion != "Angriff" and skill_ist_aoe(gewaehlte_aktion)
        kampfkraft_basis = charakter.kampfkraft_basis()

        if effekt in ("schaden", "schaden_debuff"):
            bonus = 1.0 + self.spieler_bonus_naechste_runde
            self.spieler_bonus_naechste_runde = 0.0
            lebend = self.gegner_lebend()
            if aoe:
                ziele = lebend
            elif gegner_ziel is not None and gegner_ziel.hp > 0:
                ziele = [gegner_ziel]
            else:
                ziele = lebend[:1]
            mehrfach_faktor = 0.55 if len(ziele) > 1 else 1.0
            aktionsname = "greift an" if gewaehlte_aktion == "Angriff" else f"setzt {gewaehlte_aktion} ein"
            for ziel in ziele:
                schaden = int(kampfkraft_basis * random.uniform(0.22, 0.32) * (1 + skill_level * 0.06) * bonus * mehrfach_faktor * signatur_mult)
                kritisch = random.random() < 0.12
                if kritisch:
                    schaden = int(schaden * 1.6)
                ziel.hp = max(0, ziel.hp - schaden)
                if effekt == "schaden_debuff":
                    ziel.angriffskraft = max(1, int(ziel.angriffskraft * 0.9))
                krit_text = " (KRITISCHER TREFFER!)" if kritisch else ""
                verstaerkt_text = " (VERSTÄRKT!)" if bonus > 1.0 else ""
                zeilen.append(f"   {charakter.name} {aktionsname}{krit_text}{verstaerkt_text} - {schaden} Schaden an {ziel.name}. [{ziel.name}: {ziel.hp}/{ziel.hp_max} HP]")
                if ziel.hp <= 0:
                    zeilen.append(f"   💀 {ziel.name} ist besiegt!")
        elif effekt in ("heilung", "notheilung"):
            empfaenger = verbuendeter_ziel if verbuendeter_ziel is not None else charakter
            basis_anteil = 0.3 if effekt == "notheilung" else 0.16
            heilmenge = max(1, int(empfaenger.hp_max * (basis_anteil + skill_level * 0.02)))
            geheilt = empfaenger.heilen(heilmenge)
            zeilen.append(f"   {charakter.name} setzt {gewaehlte_aktion} ein und heilt {empfaenger.name} um {geheilt} HP. [{empfaenger.name}: {empfaenger.hp_aktuell}/{empfaenger.hp_max} HP]")
        elif effekt == "gruppenheilung":
            gesamt = 0
            for ziel in self.verbuendete_lebend():
                gesamt += ziel.heilen(max(1, int(ziel.hp_max * (0.18 + skill_level * 0.015) * signatur_mult)))
            zeilen.append(f"   {charakter.name} setzt {gewaehlte_aktion} ein und heilt die gesamte Gruppe (insgesamt {gesamt} HP).")
        elif effekt == "buff":
            ziel = verbuendeter_ziel if verbuendeter_ziel is not None else charakter
            bonus_wert = 0.2 + skill_level * 0.02
            if ziel is charakter:
                self.spieler_bonus_naechste_runde += bonus_wert
                zeilen.append(f"   {charakter.name} setzt {gewaehlte_aktion} ein - der nächste eigene Angriff wird spürbar verstärkt.")
            else:
                ziel.loyalitaet = min(100, ziel.loyalitaet + 0)  # keine Nebenwirkung, nur Marker für Lesbarkeit
                zeilen.append(f"   {charakter.name} setzt {gewaehlte_aktion} ein und beflügelt {ziel.name} für die nächste Aktion.")
        elif effekt in ("schild", "aggro"):
            self.schild_runden = max(self.schild_runden, 1)
            self.schild_staerke = max(self.schild_staerke, 0.2 + skill_level * 0.015)
            zeilen.append(f"   {charakter.name} setzt {gewaehlte_aktion} ein und wappnet sich für den Gegenschlag.")
        elif effekt == "gruppenschild":
            dauer = skill_dauer(gewaehlte_aktion)
            self.schild_runden = max(self.schild_runden, dauer)
            self.schild_staerke = max(self.schild_staerke, (0.25 + skill_level * 0.015) * signatur_mult)
            zeilen.append(f"   {charakter.name} setzt {gewaehlte_aktion} ein und schützt die gesamte Gruppe für {dauer} Runden.")
        elif effekt == "reflexion":
            dauer = skill_dauer(gewaehlte_aktion)
            self.reflexion_runden = max(self.reflexion_runden, dauer)
            self.reflexion_staerke = max(self.reflexion_staerke, (0.3 + skill_level * 0.02) * signatur_mult)
            zeilen.append(f"   {charakter.name} setzt {gewaehlte_aktion} ein - Treffer werden für {dauer} Runden an die Angreifer zurückgeworfen.")
        elif effekt == "debuff":
            lebend = self.gegner_lebend()
            ziele = lebend if aoe else ([gegner_ziel] if gegner_ziel is not None and gegner_ziel.hp > 0 else lebend[:1])
            for ziel in ziele:
                ziel.angriffskraft = max(1, int(ziel.angriffskraft * (0.92 - skill_level * 0.005)))
            namen = " und ".join(z.name for z in ziele)
            zeilen.append(f"   {charakter.name} setzt {gewaehlte_aktion} ein und schwächt {namen}.")

        if not self.gegner_lebend():
            zeilen.append("   🏆 Alle Gegner sind besiegt!" if len(self.gegnergruppe) > 1 else "")
            self.beendet = True
            self.sieg = True
            self.log.extend(z for z in zeilen if z)
            return [z for z in zeilen if z]

        schadensreduktion = _begleiter_runde(self, zeilen)
        if not self.gegner_lebend():
            self.beendet = True
            self.sieg = True
            self.log.extend(zeilen)
            return zeilen

        for gegner in self.gegner_lebend():
            if not charakter.lebendig:
                break
            ziel = self._waehle_angriffsziel()
            ziel_ist_spieler = ziel is charakter
            angriffsname = random.choice(gegner.angriffe) if gegner.angriffe else "kontert"
            gegen_schaden = int(gegner.angriffskraft * random.uniform(0.14, 0.22))
            gruppenschild = self.schild_staerke if self.schild_runden > 0 else 0.0
            persoenlicher_schild = charakter.schadensreduktion() if ziel_ist_spieler else 0.0
            gesamt_reduktion = min(0.8, schadensreduktion + persoenlicher_schild + gruppenschild)
            gegen_schaden = int(gegen_schaden * (1 - gesamt_reduktion))

            if ziel_ist_spieler:
                charakter.hp_aktuell = max(0, charakter.hp_aktuell - gegen_schaden)
                hp_text = f"{charakter.hp_aktuell}/{charakter.hp_max}"
            else:
                ziel.schaden_erleiden(gegen_schaden)
                hp_text = f"{ziel.hp_aktuell}/{ziel.hp_max}"

            zeile = f"   {gegner.name} {angriffsname} - {gegen_schaden} Schaden an {ziel.name}. [{ziel.name}: {hp_text} HP]"
            if self.reflexion_runden > 0 and gegen_schaden > 0:
                reflektiert = int(gegen_schaden * self.reflexion_staerke)
                if reflektiert > 0:
                    gegner.hp = max(0, gegner.hp - reflektiert)
                    zeile += f" - reflektiert {reflektiert} Schaden zurück an {gegner.name} ({gegner.hp}/{gegner.hp_max} HP)"
                    if gegner.hp <= 0:
                        zeile += f"! 💀 {gegner.name} ist besiegt!"
            zeilen.append(zeile)

            if ziel_ist_spieler and charakter.hp_aktuell <= 0:
                charakter.lebendig = False
                zeilen.append(f"   💀 {charakter.name} sinkt zu Boden...")
                self.beendet = True
                self.sieg = False
                self.log.extend(zeilen)
                return zeilen
            elif not ziel_ist_spieler and ziel.niedergeschlagen:
                zeilen.append(f"   {ziel.name} wird niedergeschlagen und kann vorerst nicht mehr kämpfen!")

        if self.schild_runden > 0:
            self.schild_runden -= 1
        if self.reflexion_runden > 0:
            self.reflexion_runden -= 1

        if not self.gegner_lebend():
            zeilen.append("🏆 Alle Gegner sind besiegt!" if len(self.gegnergruppe) > 1 else "")
            self.beendet = True
            self.sieg = True
            self.log.extend(z for z in zeilen if z)
            return [z for z in zeilen if z]

        if self.runde >= self.max_runden:
            # Rundenlimit erreicht, ohne dass jemand gefallen ist - wer weniger
            # Anteil seiner HP verloren hat, behält das Feld.
            lebend = self.gegner_lebend()
            spieler_anteil = charakter.hp_aktuell / charakter.hp_max
            gegner_anteil = (sum(g.hp for g in lebend) / max(1, sum(g.hp_max for g in lebend))) if lebend else 0.0
            sieg = spieler_anteil >= gegner_anteil
            if sieg:
                zeilen.append("   Die Gegner ziehen sich zurück - die Gruppe behält die Oberhand.")
            else:
                zeilen.append(f"   {charakter.name} und die Gruppe ziehen sich rechtzeitig zurück.")
            self.beendet = True
            self.sieg = sieg

        self.log.extend(zeilen)
        return zeilen

    def _waehle_angriffsziel(self):
        """Wählt, wen ein angreifender Gegner trifft: meist den Anführer, aber
        ungeschützte Begleiter können ebenfalls getroffen werden. Eine aktive
        Gruppenschutz-/Aggro-Fähigkeit (schild_runden) lenkt Angriffe
        zuverlässiger auf den Anführer um - genau das macht einen Tank zum
        Beschützer der Gruppe, nicht nur zu einem persönlich zäheren Kämpfer."""
        charakter = self.charakter
        lebende_begleiter = [b for b in charakter.begleiter if not b.niedergeschlagen]
        if not lebende_begleiter:
            return charakter
        geschuetzt = self.schild_runden > 0
        spieler_gewicht = 75 if geschuetzt else 45
        gewichte = [spieler_gewicht] + [(15 if b.rolle == "Nahkämpfer" else 25) for b in lebende_begleiter]
        ziele = [charakter] + lebende_begleiter
        return random.choices(ziele, weights=gewichte, k=1)[0]

    def ergebnis(self) -> Kampfergebnis:
        gegner_namen = ", ".join(g.name for g in self.gegnergruppe)
        if self.sieg:
            xp = int(20 * self.gegner_staerke_basis * random.uniform(0.8, 1.3))
            gold = int(self.gegner_staerke_basis * random.uniform(1.5, 4))
        else:
            xp = int(5 * self.gegner_staerke_basis)
            gold = 0
        return Kampfergebnis(
            sieg=self.sieg, gegner=gegner_namen, xp_gewonnen=xp, gold_gewonnen=gold,
            log=self.log, gestorben=not self.charakter.lebendig, runden=self.runde,
        )


def kampf_starten(charakter, gegner_name: str | None = None, gegner_staerke: int | None = None,
                   max_runden: int = 8, gegnergruppe: list[tuple[str, int]] | None = None) -> Kampf:
    """Bereitet einen neuen Kampf vor (Gegner erzeugen, Eröffnungszeile), ohne
    ihn aufzulösen - der Aufrufer (CLI-Menü oder GUI-KampfScene) treibt ihn
    danach Runde für Runde selbst voran. `gegnergruppe` erlaubt mehrere
    gleichzeitige Gegner als Liste von (Name, Stärke); ohne Angabe wird wie
    bisher ein einzelner Gegner erzeugt (per Namen/Stärke oder zufällig)."""
    if gegnergruppe is None:
        if gegner_name is None:
            gegner_name, gegner_staerke = zufaelliger_gegner(charakter.level)
        gegnergruppe = [(gegner_name, gegner_staerke)]
    gegner_objekte = [_erzeuge_gegner(name, staerke) for name, staerke in gegnergruppe]
    staerke_summe = sum(s for _, s in gegnergruppe)
    return Kampf(charakter=charakter, gegnergruppe=gegner_objekte, gegner_staerke_basis=staerke_summe, max_runden=max_runden)


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

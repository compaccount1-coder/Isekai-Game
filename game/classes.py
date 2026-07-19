"""Klassendefinitionen: Basisklassen, Entwicklungsstufen und Skill-Pools."""

from dataclasses import dataclass, field


@dataclass
class ClassTier:
    name: str
    min_level: int
    beschreibung: str


@dataclass
class Skill:
    name: str
    beschreibung: str
    max_level: int = 10


ROLLEN = ("Nahkämpfer", "Fernkämpfer", "Unterstützer")


@dataclass
class Klasse:
    id: str
    tiers: list[ClassTier]  # aufsteigend nach min_level
    stat_gewichte: dict[str, float]  # STR, DEX, INT, WIS, CON, CHA -> Wachstumsfaktor
    skills: list[Skill]
    archetyp: str  # kurze Beschreibung für Charaktererstellung
    rolle: str = "Nahkämpfer"  # Nahkämpfer, Fernkämpfer, oder Unterstützer

    def tier_fuer_level(self, level: int) -> ClassTier:
        aktuell = self.tiers[0]
        for tier in self.tiers:
            if level >= tier.min_level:
                aktuell = tier
        return aktuell

    def naechste_entwicklung(self, level: int) -> ClassTier | None:
        for tier in self.tiers:
            if tier.min_level > level:
                return tier
        return None

    def start_skills(self) -> list[Skill]:
        """Die ersten beiden Skills jeder Klasse gelten als Grundfertigkeiten,
        die der Charakter von Beginn an beherrscht - damit er sich sofort
        gegen Monster verteidigen kann, statt schutzlos bei Level 1 zu starten."""
        return self.skills[:2]


KLASSEN: dict[str, Klasse] = {
    "nekromant": Klasse(
        id="nekromant",
        rolle="Fernkämpfer",
        archetyp="Meister über Tod und Verfall, befehligt Untote und zehrt an fremder Lebenskraft.",
        tiers=[
            ClassTier("Nekromant", 1, "Ein Anfänger in der verbotenen Kunst, die Toten zu erwecken."),
            ClassTier("Totenbeschwörer", 30, "Ganze Legionen von Untoten gehorchen deinem Willen."),
            ClassTier("Lich-Lord", 70, "Du hast den Tod selbst überwunden und herrschst über das Reich der Schatten."),
        ],
        stat_gewichte={"STR": 0.6, "DEX": 0.8, "INT": 1.4, "WIS": 1.2, "CON": 0.9, "CHA": 0.7},
        skills=[
            Skill("Skelett erwecken", "Erhebt einen gefallenen Feind als knöchernen Diener."),
            Skill("Lebensentzug", "Entzieht dem Ziel Lebenskraft und heilt dich selbst."),
            Skill("Knochenpanzer", "Umhüllt dich mit einer Rüstung aus verstärkten Knochen."),
            Skill("Seuchenwolke", "Eine Wolke aus Verwesung schwächt alle Feinde in der Nähe."),
            Skill("Untotenarmee", "Beschwört eine ganze Schar von Skeletten und Zombies."),
            Skill("Seelenraub", "Entreißt einem sterbenden Feind die Seele für dauerhafte Kraft."),
            Skill("Grabesfluch", "Schwächt einen Gegner durch nekrotische Fäulnis von innen heraus."),
            Skill("Knochendrache beschwören", "Ruft einen gewaltigen Knochendrachen als letzte Verstärkung."),
        ],
    ),
    "krieger": Klasse(
        id="krieger",
        rolle="Nahkämpfer",
        archetyp="Ein Meister der Klinge, der sich Kraft und Stahl auf jedes Problem verlässt.",
        tiers=[
            ClassTier("Krieger", 1, "Ein Kämpfer, der sein Handwerk auf dem Schlachtfeld lernt."),
            ClassTier("Kriegsherr", 30, "Deine Präsenz allein lässt Feinde erzittern."),
            ClassTier("Unsterblicher Klingenmeister", 70, "Deine Klinge hat die Grenze zur Legende überschritten."),
        ],
        stat_gewichte={"STR": 1.5, "DEX": 0.9, "INT": 0.5, "WIS": 0.6, "CON": 1.3, "CHA": 0.8},
        skills=[
            Skill("Wirbelschlag", "Ein kreisender Hieb, der alle Gegner in Reichweite trifft."),
            Skill("Schildwall", "Erhöht deine Verteidigung drastisch für kurze Zeit."),
            Skill("Berserkerwut", "Tausche Verteidigung gegen massiv erhöhten Schaden."),
            Skill("Klingensturm", "Eine Serie blitzschneller Schläge."),
            Skill("Kriegsschrei", "Stärkt dich und schwächt die Moral deiner Feinde."),
            Skill("Todesstoß", "Ein finaler, hochpräziser Stich mit enormem Schaden."),
            Skill("Rüstungsbrecher", "Ein gezielter Hieb, der jede Rüstung durchbricht."),
            Skill("Unbeugsamer Wille", "Du stehst auf, selbst wenn andere längst gefallen wären."),
        ],
    ),
    "magier": Klasse(
        id="magier",
        rolle="Fernkämpfer",
        archetyp="Ein Gelehrter der arkanen Künste, der die Elemente selbst nach seinem Willen formt.",
        tiers=[
            ClassTier("Magier", 1, "Ein Schüler der arkanen Grundlagen."),
            ClassTier("Erzmagier", 30, "Deine Beherrschung der Elemente ist beinahe furchteinflößend."),
            ClassTier("Meister der Elemente", 70, "Realität selbst biegt sich deinem arkanen Willen."),
        ],
        stat_gewichte={"STR": 0.4, "DEX": 0.7, "INT": 1.6, "WIS": 1.1, "CON": 0.7, "CHA": 0.8},
        skills=[
            Skill("Feuerball", "Ein explodierender Ball aus reiner Flamme."),
            Skill("Eislanze", "Eine durchdringende Lanze aus scharfem Eis."),
            Skill("Blitzschlag", "Ein gezielter Blitz, der Ketten von Feinden trifft."),
            Skill("Arkaner Schild", "Ein magisches Schutzfeld, das Schaden absorbiert."),
            Skill("Meteor", "Ruft einen brennenden Himmelskörper auf das Schlachtfeld."),
            Skill("Zeitverzerrung", "Verlangsamt die Zeit um deine Feinde herum."),
            Skill("Frostnova", "Eine explosive Welle aus Eiseskälte um dich herum."),
            Skill("Manaentzug", "Entzieht dem Gegner arkane Energie und schwächt ihn."),
        ],
    ),
    "paladin": Klasse(
        id="paladin",
        rolle="Nahkämpfer",
        archetyp="Ein von den Göttern gesegneter Beschützer, der Klinge und Gebet vereint.",
        tiers=[
            ClassTier("Paladin", 1, "Ein Novize im Dienst des Lichts."),
            ClassTier("Heiliger Ritter", 30, "Dein Glaube manifestiert sich als greifbare Macht."),
            ClassTier("Erzengel-Avatar", 70, "Ein Bruchteil göttlicher Macht wohnt nun in dir."),
        ],
        stat_gewichte={"STR": 1.2, "DEX": 0.6, "INT": 0.6, "WIS": 1.3, "CON": 1.2, "CHA": 1.0},
        skills=[
            Skill("Heilige Klinge", "Deine Waffe entflammt in reinigendem Licht."),
            Skill("Segen", "Stärkt dich und deine Verbündeten."),
            Skill("Schutzschild", "Ein Schild aus heiligem Licht wehrt Angriffe ab."),
            Skill("Läuterung", "Heilt Wunden und vertreibt dunkle Magie."),
            Skill("Wiederauferstehung", "Ruft gefallene Verbündete zurück ins Leben."),
            Skill("Göttliches Urteil", "Ruft die Macht des Himmels auf deine Feinde herab."),
            Skill("Bannschlag", "Ein Hieb, der Dunkelheit und Untote besonders hart trifft."),
            Skill("Standhafter Glaube", "Unerschütterlich gegen Furcht und Verzweiflung."),
        ],
    ),
    "assassine": Klasse(
        id="assassine",
        rolle="Nahkämpfer",
        archetyp="Ein Meister der Schatten, der lautlos zuschlägt, bevor der Feind überhaupt weiß, dass er da ist.",
        tiers=[
            ClassTier("Assassine", 1, "Ein Neuling in der Kunst des lautlosen Tötens."),
            ClassTier("Schattenklinge", 30, "Du bewegst dich wie ein Geist zwischen den Schatten."),
            ClassTier("Meister der tausend Schnitte", 70, "Kein Ziel entkommt deiner Klinge."),
        ],
        stat_gewichte={"STR": 0.8, "DEX": 1.6, "INT": 0.8, "WIS": 0.7, "CON": 0.8, "CHA": 0.9},
        skills=[
            Skill("Hinterhalt", "Ein verheerender Angriff aus dem Verborgenen."),
            Skill("Giftklinge", "Vergiftet deine Waffe für anhaltenden Schaden."),
            Skill("Schattensprung", "Teleportiert dich kurzzeitig durch die Schatten."),
            Skill("Tödlicher Tanz", "Eine Serie präziser, tödlicher Schläge."),
            Skill("Unsichtbarkeit", "Verschwindest vollständig aus der Sicht deiner Feinde."),
            Skill("Exekution", "Ein garantiert tödlicher Schlag gegen geschwächte Ziele."),
            Skill("Rauchbombe", "Verschleiert das Schlachtfeld für einen sicheren Rückzug oder Überraschungsangriff."),
            Skill("Doppelklinge", "Zwei blitzschnelle Schläge in einer einzigen Bewegung."),
        ],
    ),
    "beschwoerer": Klasse(
        id="beschwoerer",
        rolle="Fernkämpfer",
        archetyp="Ein Vertragsbinder, der Kreaturen aus fernen Ebenen an seine Seite ruft.",
        tiers=[
            ClassTier("Beschwörer", 1, "Ein Anfänger im Binden geisterhafter Verträge."),
            ClassTier("Großbeschwörer", 30, "Eine ganze Menagerie mächtiger Kreaturen dient dir."),
            ClassTier("Herr der Dimensionen", 70, "Du rufst Wesen, die selbst Götter fürchten."),
        ],
        stat_gewichte={"STR": 0.5, "DEX": 0.7, "INT": 1.3, "WIS": 1.2, "CON": 0.8, "CHA": 1.3},
        skills=[
            Skill("Geisterwolf beschwören", "Ruft einen loyalen Geisterwolf zur Unterstützung."),
            Skill("Feuerdrache beschwören", "Ruft einen jungen Feuerdrachen ins Schlachtfeld."),
            Skill("Vertrag binden", "Bindet ein besiegtes Wesen dauerhaft an dich."),
            Skill("Kreaturenbund", "Verstärkt alle deine beschworenen Kreaturen gleichzeitig."),
            Skill("Dimensionsriss", "Öffnet ein Portal zu einer fremden, feindseligen Ebene."),
            Skill("Legionsbeschwörung", "Ruft eine ganze Armee beschworener Kreaturen auf einmal."),
            Skill("Schattenhund beschwören", "Ruft einen flinken Gefährten aus der Zwischenwelt."),
            Skill("Elementarpakt", "Bindet kurzzeitig die Kraft eines Elementargeists an dich."),
        ],
    ),
    "barde": Klasse(
        id="barde",
        rolle="Unterstützer",
        archetyp="Ein charismatischer Geschichtenerzähler, dessen Lieder Verbündete stärken und Feinde schwächen - eine reine Unterstützungsklasse, nicht auf eigene Klingenführung ausgelegt.",
        tiers=[
            ClassTier("Barde", 1, "Ein reisender Musikant mit großen Träumen."),
            ClassTier("Hofsänger der Legenden", 30, "Deine Lieder werden in jedem Königreich gesungen."),
            ClassTier("Stimme der Schöpfung", 70, "Deine Worte formen die Wirklichkeit selbst."),
        ],
        stat_gewichte={"STR": 0.3, "DEX": 0.7, "INT": 0.8, "WIS": 1.3, "CON": 0.7, "CHA": 1.8},
        skills=[
            Skill("Kampflied", "Stärkt den Mut und die Kraft aller Verbündeten."),
            Skill("Schlaflied", "Versetzt Feinde in einen tiefen, unnatürlichen Schlaf."),
            Skill("Spott", "Lenkt die Aufmerksamkeit aller Feinde auf dich."),
            Skill("Heldenepos", "Erzählt eine Legende, die deine Gruppe über sich hinauswachsen lässt."),
            Skill("Massenbezauberung", "Verzaubert eine ganze Menge, Freund wie Feind."),
            Skill("Lied der Wiedergeburt", "Ein letztes Lied, das dem Tod selbst trotzt."),
            Skill("Spöttisches Lied", "Schwächt die Entschlossenheit der Feinde mit beißendem Spott."),
            Skill("Chor der Standhaften", "Ein Lied, das die Gruppe davor bewahrt, zu fallen."),
        ],
    ),
    "waldlaeufer": Klasse(
        id="waldlaeufer",
        rolle="Fernkämpfer",
        archetyp="Ein Kind der Wildnis, unübertroffen mit dem Bogen und verbunden mit der Natur.",
        tiers=[
            ClassTier("Waldläufer", 1, "Ein Jäger, der die Pfade des Waldes kennt."),
            ClassTier("Meisterjäger", 30, "Kein Wild entkommt deinem geschulten Blick."),
            ClassTier("Herr der Wildnis", 70, "Die Natur selbst gehorcht deinem Ruf."),
        ],
        stat_gewichte={"STR": 0.8, "DEX": 1.4, "INT": 0.7, "WIS": 1.2, "CON": 1.0, "CHA": 0.7},
        skills=[
            Skill("Pfeilhagel", "Ein Schwall von Pfeilen, der mehrere Ziele trifft."),
            Skill("Fallenstellen", "Platziert eine tödliche Falle für unachtsame Feinde."),
            Skill("Tiergefährte", "Ruft einen treuen tierischen Begleiter zur Seite."),
            Skill("Präziser Schuss", "Ein perfekt platzierter Schuss mit garantiertem Treffer."),
            Skill("Naturheilung", "Nutzt die Kraft der Natur, um Wunden zu heilen."),
            Skill("Sturm der tausend Pfeile", "Ein verheerender Pfeilregen auf das gesamte Schlachtfeld."),
            Skill("Rückzugsschuss", "Ein Schuss im Rückzug, der trotzdem trifft."),
            Skill("Rudelruf", "Ruft wilde Tiere der Region zur Unterstützung herbei."),
        ],
    ),
    "moench": Klasse(
        id="moench",
        rolle="Nahkämpfer",
        archetyp="Ein Kämpfer, der Körper und Geist durch jahrelange Disziplin zur perfekten Waffe geformt hat.",
        tiers=[
            ClassTier("Mönch", 1, "Ein Schüler auf dem Weg der inneren Kraft."),
            ClassTier("Meister der Fäuste", 30, "Deine Schläge tragen die Kraft eines Erdbebens."),
            ClassTier("Avatar der Leere", 70, "Körper und Geist sind eins - nichts kann dich mehr aufhalten."),
        ],
        stat_gewichte={"STR": 1.1, "DEX": 1.2, "INT": 0.6, "WIS": 1.3, "CON": 1.1, "CHA": 0.6},
        skills=[
            Skill("Faustserie", "Eine blitzschnelle Serie von Schlägen."),
            Skill("Innere Ruhe", "Konzentriert deinen Chi und heilt leichte Wunden."),
            Skill("Wirbelkick", "Ein kreisender Tritt, der mehrere Gegner trifft."),
            Skill("Eisenhaut", "Härtet deine Haut zu widerstandsfähigem Stahl."),
            Skill("Drachenfaust", "Ein einzelner Schlag mit der Kraft eines Drachen."),
            Skill("Erleuchteter Schlag", "Ein perfekter Treffer, der jede Verteidigung durchbricht."),
            Skill("Betäubender Griff", "Lähmt kurzzeitig die Reaktionsfähigkeit des Gegners."),
            Skill("Chi-Explosion", "Entlädt angestaute Energie in einem verheerenden Stoß."),
        ],
    ),
    "kleriker": Klasse(
        id="kleriker",
        rolle="Unterstützer",
        archetyp="Ein Heiler im Dienst einer höheren Macht, dessen Licht Wunden schließt und Verbündete schützt.",
        tiers=[
            ClassTier("Kleriker", 1, "Ein Novize im Dienst des Heilgebets."),
            ClassTier("Erzpriester", 30, "Dein Gebet allein kann Sterbende zurück ins Leben holen."),
            ClassTier("Heiliger Auserwählter", 70, "Du bist zum irdischen Gefäß göttlicher Gnade geworden."),
        ],
        stat_gewichte={"STR": 0.3, "DEX": 0.5, "INT": 0.7, "WIS": 1.7, "CON": 0.9, "CHA": 1.2},
        skills=[
            Skill("Heilendes Licht", "Schließt Wunden von dir oder einem Verbündeten."),
            Skill("Gruppensegen", "Stärkt die gesamte Gruppe für die kommende Schlacht."),
            Skill("Schutzaura", "Ein Feld heiligen Lichts absorbiert eingehenden Schaden."),
            Skill("Wiederbelebung", "Ruft einen gefallenen Verbündeten zurück ins Leben."),
            Skill("Bannfluch", "Entfernt schädliche Magie von dir oder Verbündeten."),
            Skill("Göttlicher Zorn", "Ein seltener offensiver Ausbruch heiliger Energie."),
            Skill("Läuterndes Feuer", "Heiliges Feuer, das Untote und Dämonen besonders hart trifft."),
            Skill("Segen der Standhaftigkeit", "Schützt die Gruppe davor, von einem einzelnen Treffer niedergestreckt zu werden."),
        ],
    ),
    "alchemist": Klasse(
        id="alchemist",
        rolle="Unterstützer",
        archetyp="Ein Meister der Tränke und Elixiere, der Schlachten aus dem Hintergrund entscheidet.",
        tiers=[
            ClassTier("Alchemist", 1, "Ein Lehrling mit rauchendem Kessel und großen Ambitionen."),
            ClassTier("Meisterbrauer", 30, "Deine Tränke sind in jeder Gilde begehrt."),
            ClassTier("Großmeister der Transmutation", 70, "Du beherrschst die Grundlagen der Materie selbst."),
        ],
        stat_gewichte={"STR": 0.4, "DEX": 0.8, "INT": 1.6, "WIS": 1.1, "CON": 0.7, "CHA": 0.7},
        skills=[
            Skill("Heiltrank werfen", "Wirft einen Trank, der Verbündete sofort heilt."),
            Skill("Stärkungselixier", "Verleiht der Gruppe vorübergehend erhöhte Kraft."),
            Skill("Giftnebel", "Eine Wolke aus Toxinen schwächt alle Feinde in der Nähe."),
            Skill("Explosive Mischung", "Eine instabile Verbindung mit beachtlicher Wirkung."),
            Skill("Verwandlungstrank", "Verändert vorübergehend Eigenschaften von dir oder Verbündeten."),
            Skill("Elixier der letzten Stunde", "Ein Notfalltrank, der selbst Sterbende stabilisiert."),
            Skill("Säurebombe", "Eine ätzende Mischung, die jede Rüstung zersetzt."),
            Skill("Katalysator", "Verstärkt kurzzeitig alle Effekte der gesamten Gruppe."),
        ],
    ),
}


def klassen_nach_rolle(rolle: str) -> list[Klasse]:
    return [k for k in KLASSEN.values() if k.rolle == rolle]


# ---------------------------------------------------------------------------
# Spezialisierung: Nahkämpfer können sich bei Level 30 dazu entscheiden, zum
# Beschützer der Gruppe zu werden - ein eigener thematischer Entwicklungspfad
# mit passenden Fähigkeiten und spürbarer Schadensreduktion, statt einfach nur
# noch härter zuzuschlagen.
# ---------------------------------------------------------------------------

TANK_PFADE: dict[str, dict] = {
    "krieger": {
        "tier30": ClassTier("Bollwerk der Front", 30, "Kein Feind durchbricht deine Verteidigungslinie."),
        "tier70": ClassTier("Unerschütterlicher Koloss", 70, "Du bist zur lebenden Festung geworden, die niemand einzureißen vermag."),
        "skills": [
            Skill("Provokation", "Zwingst jeden Feind, sich auf dich zu konzentrieren."),
            Skill("Eiserne Deckung", "Reduziert erlittenen Schaden drastisch für die Dauer des Kampfes."),
            Skill("Letzte Bastion", "Du stehst noch, wo andere längst gefallen wären."),
        ],
    },
    "paladin": {
        "tier30": ClassTier("Schildwächter des Lichts", 30, "Dein Schild schützt nicht nur dich, sondern die gesamte Gruppe."),
        "tier70": ClassTier("Bollwerk der Himmlischen", 70, "Ein Bruchteil göttlicher Unerschütterlichkeit wohnt in deinem Schild."),
        "skills": [
            Skill("Geweihter Schild", "Ein Schild aus reinem Licht, das jeden Hieb abfängt."),
            Skill("Eiserne Deckung", "Reduziert erlittenen Schaden drastisch für die Dauer des Kampfes."),
            Skill("Märtyrergelübde", "Du erträgst, was eigentlich deine Verbündeten treffen sollte."),
        ],
    },
    "moench": {
        "tier30": ClassTier("Fels in der Brandung", 30, "Kein Sturm bringt dich mehr aus dem Gleichgewicht."),
        "tier70": ClassTier("Unbeweglicher Berg", 70, "Selbst die Erde erzittert eher als du."),
        "skills": [
            Skill("Steinerne Haltung", "Eine Kampfstellung, die jeden Angriff ins Leere laufen lässt."),
            Skill("Eiserne Deckung", "Reduziert erlittenen Schaden drastisch für die Dauer des Kampfes."),
            Skill("Unbeugsamer Atem", "Du sammelst dich, wo andere zusammenbrechen würden."),
        ],
    },
}


def klasse_hat_tank_pfad(klasse_id: str) -> bool:
    return klasse_id in TANK_PFADE


# ---------------------------------------------------------------------------
# Fähigkeits-Wirkung: was ein Skill im Kampf tatsächlich auslöst. Ohne diese
# Zuordnung wurde jeder Skill rein kosmetisch benannt, aber immer identisch
# aufgelöst (Unterstützer heilen z.B. IMMER, auch bei "Giftnebel" oder
# "Göttlicher Zorn") - unlogisch, wenn die eigene Beschreibung offensiv ist.
# Nicht gelistete Skills gelten als "schaden" (Standardverhalten, passt auf
# die meisten Kampf-Fähigkeiten).
# ---------------------------------------------------------------------------

SKILL_EFFEKT: dict[str, str] = {
    # Heilung (stellt HP wieder her)
    "Lebensentzug": "heilung",
    "Läuterung": "heilung",
    "Naturheilung": "heilung",
    "Innere Ruhe": "heilung",
    "Heilendes Licht": "heilung",
    "Heiltrank werfen": "heilung",
    # Notheilung (starke Heilung für kritische Momente)
    "Wiederauferstehung": "notheilung",
    "Wiederbelebung": "notheilung",
    "Lied der Wiedergeburt": "notheilung",
    "Elixier der letzten Stunde": "notheilung",
    # Schild (reduziert erlittenen Schaden diese Runde)
    "Knochenpanzer": "schild",
    "Schildwall": "schild",
    "Unbeugsamer Wille": "schild",
    "Arkaner Schild": "schild",
    "Schutzschild": "schild",
    "Standhafter Glaube": "schild",
    "Unsichtbarkeit": "schild",
    "Rauchbombe": "schild",
    "Eisenhaut": "schild",
    "Schutzaura": "schild",
    "Bannfluch": "schild",
    "Segen der Standhaftigkeit": "schild",
    "Verwandlungstrank": "schild",
    "Chor der Standhaften": "schild",
    "Eiserne Deckung": "schild",
    "Letzte Bastion": "schild",
    "Geweihter Schild": "schild",
    "Märtyrergelübde": "schild",
    "Steinerne Haltung": "schild",
    "Unbeugsamer Atem": "schild",
    # Aggro (zieht Aufmerksamkeit auf sich, wirkt wie ein Schild)
    "Spott": "aggro",
    "Provokation": "aggro",
    # Verstärkung (erhöht den nächsten Angriff der Gruppe)
    "Kriegsschrei": "buff",
    "Kreaturenbund": "buff",
    "Kampflied": "buff",
    "Heldenepos": "buff",
    "Segen": "buff",
    "Gruppensegen": "buff",
    "Stärkungselixier": "buff",
    "Katalysator": "buff",
    # Schwächung (mindert die Kraft des Gegners)
    "Zeitverzerrung": "debuff",
    "Manaentzug": "debuff",
    "Schlaflied": "debuff",
    "Massenbezauberung": "debuff",
    "Spöttisches Lied": "debuff",
}


def skill_effekt(skill_name: str) -> str:
    return SKILL_EFFEKT.get(skill_name, "schaden")

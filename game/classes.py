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
            Skill("Wort der Genesung", "Ein Gebet, das die gesamte Gruppe auf einmal von ihren Wunden befreit."),
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
            Skill("Regenerationstrank", "Ein Sud aus heilenden Kräutern, der Wunden zuverlässig schließt."),
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
# Aufstiegsklassen: bei Level 30 entscheidet sich jeder Charakter zwischen dem
# angestammten Entwicklungspfad seiner Klasse (Klasse.tiers) und einer
# alternativen Aufstiegsklasse mit eigenem Namen, eigener Thematik und
# eigenen Fähigkeiten - z.B. wird ein Kleriker entweder zum Erzpriester
# (Heilung) oder zum Kriegspriester (Vergeltung). Jede Aufstiegsklasse nutzt
# gezielt die volle Bandbreite an Fähigkeits-Wirkungen (Fläche, Reflexion,
# Gruppenschutz, Gruppenheilung), damit sich die Wahl spürbar unterscheidet.
# ---------------------------------------------------------------------------

AUFSTIEGSPFADE: dict[str, dict] = {
    "krieger": {
        "tier30": ClassTier("Bollwerk der Front", 30, "Kein Feind durchbricht deine Verteidigungslinie."),
        "tier70": ClassTier("Unerschütterlicher Koloss", 70, "Du bist zur lebenden Festung geworden, die niemand einzureißen vermag."),
        "kurzbeschreibung": "Wird zum Beschützer der Gruppe: Schaden mindern und reflektieren, Aufmerksamkeit der Feinde binden.",
        "skills": [
            Skill("Provokation", "Zwingst jeden Feind, sich auf dich zu konzentrieren."),
            Skill("Eiserne Deckung", "Reduziert erlittenen Schaden drastisch für die Dauer des Kampfes."),
            Skill("Letzte Bastion", "Du stehst noch, wo andere längst gefallen wären - schützt die gesamte Gruppe über mehrere Runden."),
            Skill("Dornenpanzer", "Ein gepanzerter Schild, der eingehende Schläge an den Angreifer zurückwirft."),
            Skill("Unbezwingbare Mauer", "Signatur-Fähigkeit des Bollwerks: für mehrere Runden wird jeder Treffer, den du erleidest, verstärkt an den Angreifer zurückgeworfen - einmal pro Kampf."),
        ],
    },
    "paladin": {
        "tier30": ClassTier("Schildwächter des Lichts", 30, "Dein Schild schützt nicht nur dich, sondern die gesamte Gruppe."),
        "tier70": ClassTier("Bollwerk der Himmlischen", 70, "Ein Bruchteil göttlicher Unerschütterlichkeit wohnt in deinem Schild."),
        "kurzbeschreibung": "Wird zum Beschützer der Gruppe: Schaden mindern und reflektieren, Aufmerksamkeit der Feinde binden.",
        "skills": [
            Skill("Geweihter Schild", "Ein Schild aus reinem Licht, das jeden Hieb abfängt."),
            Skill("Eiserne Deckung", "Reduziert erlittenen Schaden drastisch für die Dauer des Kampfes."),
            Skill("Märtyrergelübde", "Du erträgst, was eigentlich deine Verbündeten treffen sollte - schützt die gesamte Gruppe über mehrere Runden."),
            Skill("Vergeltungsschild", "Ein Schild aus heiligem Zorn, das erlittene Schläge an den Angreifer zurückgibt."),
            Skill("Licht der letzten Hoffnung", "Signatur-Fähigkeit des Schildwächters: ein gleißender Lichtstoß heilt die gesamte Gruppe mit göttlicher Kraft - einmal pro Kampf."),
        ],
    },
    "moench": {
        "tier30": ClassTier("Fels in der Brandung", 30, "Kein Sturm bringt dich mehr aus dem Gleichgewicht."),
        "tier70": ClassTier("Unbeweglicher Berg", 70, "Selbst die Erde erzittert eher als du."),
        "kurzbeschreibung": "Wird zum Beschützer der Gruppe: Schaden mindern und reflektieren, Aufmerksamkeit der Feinde binden.",
        "skills": [
            Skill("Steinerne Haltung", "Eine Kampfstellung, die jeden Angriff ins Leere laufen lässt."),
            Skill("Eiserne Deckung", "Reduziert erlittenen Schaden drastisch für die Dauer des Kampfes."),
            Skill("Unbeugsamer Atem", "Du sammelst dich, wo andere zusammenbrechen würden - schützt die gesamte Gruppe über mehrere Runden."),
            Skill("Konterhaltung", "Eine Kampfhaltung, die jeden Treffer sofort mit gleicher Härte erwidert."),
            Skill("Schlag des unbeweglichen Berges", "Signatur-Fähigkeit des Berges: ein einzelner, vollkommener Schlag mit verheerender Wucht - einmal pro Kampf."),
        ],
    },
    "nekromant": {
        "tier30": ClassTier("Seuchenfürst", 30, "Verwesung und Seuche folgen deinen Schritten - ganze Feindesgruppen verrotten in deiner Gegenwart."),
        "tier70": ClassTier("Herr der Verwesung", 70, "Du bist selbst zur wandelnden Seuche geworden, vor der sich selbst der Tod fürchtet."),
        "kurzbeschreibung": "Statt einzelner Untoter beschwörst du Verfall über ganze Gegnergruppen - Fläche und Schwächung statt Einzelziel.",
        "skills": [
            Skill("Verwesungswolke", "Eine Wolke aus reinem Verfall, die alle Feinde zugleich schädigt und schwächt."),
            Skill("Knochensplitterhagel", "Ein Schauer scharfkantiger Knochensplitter, der jeden Gegner auf dem Feld trifft."),
            Skill("Todesfluch", "Ein Fluch, der die Lebenskraft eines einzelnen Feindes drastisch untergräbt."),
            Skill("Große Pest", "Signatur-Fähigkeit des Seuchenfürsten: eine Seuche biblischen Ausmaßes befällt und zersetzt alle Feinde zugleich - einmal pro Kampf."),
        ],
    },
    "magier": {
        "tier30": ClassTier("Kriegsmagier", 30, "Du verbindest arkane Macht mit kämpferischer Disziplin - ein Zauberer, der auch im Nahkampf nicht zurückweicht."),
        "tier70": ClassTier("Meister der Klingenmagie", 70, "Stahl und Zauber sind für dich eins geworden."),
        "kurzbeschreibung": "Statt reiner Flächenzerstörung setzt du auf arkane Selbstverteidigung und konzentrierte Vernichtungsschläge.",
        "skills": [
            Skill("Manabarriere", "Ein arkanes Schutzfeld, das eingehenden Schaden erheblich mindert."),
            Skill("Arkaner Gegenschlag", "Reflektiert einen Teil erlittenen Schadens für mehrere Runden zurück."),
            Skill("Kraftentladung", "Ein gebündelter Schlag arkaner Energie mit verheerender Wirkung auf ein einzelnes Ziel."),
            Skill("Arkane Singularität", "Signatur-Fähigkeit des Kriegsmagiers: du reißt die Realität selbst auf und entfesselst konzentrierte Vernichtung auf ein einzelnes Ziel - einmal pro Kampf."),
        ],
    },
    "assassine": {
        "tier30": ClassTier("Giftmeister", 30, "Deine Klingen tropfen von Toxinen, die selbst nach dem tödlichen Schnitt weiterwirken."),
        "tier70": ClassTier("Herr der tausend Gifte", 70, "Kein Gegengift kennt eine Rettung vor deinen Mischungen."),
        "kurzbeschreibung": "Statt auf reine Fluchtgeschwindigkeit setzt du auf Gifte, die Gegner dauerhaft schwächen - einzeln oder in der Fläche.",
        "skills": [
            Skill("Nervengift", "Ein lähmendes Gift, das die Kampfkraft eines Gegners drastisch untergräbt."),
            Skill("Giftwolke", "Ein zerstäubtes Toxin, das alle Feinde in Reichweite schwächt und schädigt."),
            Skill("Tödliche Präzision", "Ein Moment absoluter Konzentration, der den nächsten Angriff enorm verstärkt."),
            Skill("Tödlicher Schwarm", "Signatur-Fähigkeit des Giftmeisters: du entfesselst dein tödlichstes Gemisch, das alle Feinde zugleich vergiftet und schädigt - einmal pro Kampf."),
        ],
    },
    "beschwoerer": {
        "tier30": ClassTier("Paktwächter", 30, "Die Geister, die du bindest, schützen nicht mehr nur dich, sondern die gesamte Gruppe."),
        "tier70": ClassTier("Hüter der gebundenen Legionen", 70, "Eine ganze Legion gebundener Geister steht zwischen deiner Gruppe und jeder Gefahr."),
        "kurzbeschreibung": "Statt reiner Angriffskraft beschwörst du Schutzgeister, die die gesamte Gruppe abschirmen und heilen.",
        "skills": [
            Skill("Schutzgeist beschwören", "Ein gebundener Geist schirmt die gesamte Gruppe über mehrere Runden ab."),
            Skill("Bindende Fessel", "Geisterhafte Ketten binden und schwächen alle gegnerischen Kämpfer zugleich."),
            Skill("Geisterheilung", "Wohlwollende Geister schließen die Wunden der gesamten Gruppe auf einmal."),
            Skill("Legion der Wächtergeister", "Signatur-Fähigkeit des Paktwächters: eine ganze Legion gebundener Geister umschließt die Gruppe für mehrere Runden mit undurchdringlichem Schutz - einmal pro Kampf."),
        ],
    },
    "barde": {
        "tier30": ClassTier("Kriegssänger", 30, "Deine Lieder sind nicht mehr nur Ermutigung - sie sind Waffen, die den Feind das Fürchten lehren."),
        "tier70": ClassTier("Stimme des Sturms", 70, "Dein Gesang allein kann Schlachten entscheiden, bevor sie beginnen."),
        "kurzbeschreibung": "Statt reiner Ermutigung setzt du auf Klänge, die dem Feind schaden und ganze Gruppen demoralisieren.",
        "skills": [
            Skill("Kriegshymne", "Ein mitreißender Gesang, der den nächsten Angriff der Gruppe erheblich verstärkt."),
            Skill("Zerreißender Akkord", "Eine Welle reiner Klangenergie, die alle Feinde gleichzeitig trifft."),
            Skill("Lied der Verzweiflung", "Ein bedrückender Klang, der die Kampfkraft aller Feinde zugleich untergräbt."),
            Skill("Sinfonie der Vernichtung", "Signatur-Fähigkeit des Kriegssängers: der letzte, gewaltigste Akkord deines Liedes zerreißt alle Feinde zugleich - einmal pro Kampf."),
        ],
    },
    "waldlaeufer": {
        "tier30": ClassTier("Plänklermeister", 30, "Du bist nicht mehr nur ein Jäger einzelner Beute - deine Pfeile regnen auf ganze Gruppen von Feinden nieder."),
        "tier70": ClassTier("Sturm der tausend Pfeile", 70, "Kein Feind entkommt deinem Pfeilhagel, egal wie viele es sind."),
        "kurzbeschreibung": "Statt gezielter Einzelschüsse spezialisierst du dich auf Salven, die ganze Gegnergruppen gleichzeitig treffen.",
        "skills": [
            Skill("Splitterpfeil", "Ein Pfeil, der beim Einschlag in Splitter zerbricht und alle nahen Feinde trifft."),
            Skill("Fallennetz", "Ein Netz aus Fallen, das mehrere Feinde zugleich fesselt und schwächt."),
            Skill("Deckungsfeuer", "Ein Schauer aus Pfeilen, der eingehende Angriffe auf die Gruppe abschwächt."),
            Skill("Pfeilsturm des Jahrhunderts", "Signatur-Fähigkeit des Plänklermeisters: ein Sturm aus hunderten Pfeilen verdunkelt den Himmel und trifft jeden Feind zugleich - einmal pro Kampf."),
        ],
    },
    "kleriker": {
        "tier30": ClassTier("Kriegspriester", 30, "Dein Glaube manifestiert sich nicht mehr nur als Heilung, sondern als strafende Macht gegen die Feinde des Lichts."),
        "tier70": ClassTier("Zorn des Himmels", 70, "Du bist zum Werkzeug göttlichen Zorns geworden."),
        "kurzbeschreibung": "Statt reiner Heilung setzt du deinen Glauben offensiv ein - strafende Schläge und Feuer für ganze Feindesgruppen.",
        "skills": [
            Skill("Richtender Blitz", "Ein Blitz göttlichen Zorns, der einen einzelnen Feind mit voller Wucht trifft."),
            Skill("Feuersturm des Glaubens", "Heiliges Feuer, das alle Feinde auf dem Schlachtfeld zugleich verzehrt."),
            Skill("Rüstung des Gerechten", "Ein Segen, der eingehenden Schaden für die gesamte Gruppe spürbar mindert."),
            Skill("Gerechtes Urteil", "Signatur-Fähigkeit des Kriegspriesters: du fällst göttliches Urteil über einen einzelnen Feind, dem nichts standhält - einmal pro Kampf."),
        ],
    },
    "alchemist": {
        "tier30": ClassTier("Sprengmeister", 30, "Deine Mischungen dienen nicht mehr nur der Heilung - sie sind Waffen, die ganze Gruppen von Feinden verwüsten."),
        "tier70": ClassTier("Meister der Verwüstung", 70, "Deine Explosionen kennen keine Gnade mehr."),
        "kurzbeschreibung": "Statt auf Heilung und Unterstützung spezialisierst du dich auf Sprengstoffe und Gase, die ganze Gegnergruppen verwüsten.",
        "skills": [
            Skill("Feuerbombe", "Eine Bombe aus Alchemistenfeuer, die alle Feinde in der Nähe verbrennt."),
            Skill("Zersetzungsgas", "Ein ätzendes Gas, das alle Feinde zugleich schädigt und schwächt."),
            Skill("Überladener Trank", "Ein instabiles Gebräu, das den nächsten Angriff drastisch verstärkt."),
            Skill("Totale Verwüstung", "Signatur-Fähigkeit des Sprengmeisters: deine instabilste, gewaltigste Mischung reißt das gesamte Schlachtfeld in Schutt - einmal pro Kampf."),
        ],
    },
}


# ---------------------------------------------------------------------------
# Fähigkeits-Wirkung: was ein Skill im Kampf tatsächlich auslöst. Ohne diese
# Zuordnung wurde jeder Skill rein kosmetisch benannt, aber immer identisch
# aufgelöst (Unterstützer heilen z.B. IMMER, auch bei "Giftnebel" oder
# "Göttlicher Zorn") - unlogisch, wenn die eigene Beschreibung offensiv ist.
# Nicht gelistete Skills gelten als "schaden" (Standardverhalten, passt auf
# die meisten Kampf-Fähigkeiten).
# ---------------------------------------------------------------------------

SKILL_EFFEKT: dict[str, str] = {
    # Heilung (stellt HP wieder her, Ziel wählbar)
    "Lebensentzug": "heilung",
    "Läuterung": "heilung",
    "Naturheilung": "heilung",
    "Innere Ruhe": "heilung",
    "Heilendes Licht": "heilung",
    "Heiltrank werfen": "heilung",
    "Regenerationstrank": "heilung",
    # Notheilung (starke Heilung für kritische Momente, Ziel wählbar)
    "Wiederauferstehung": "notheilung",
    "Wiederbelebung": "notheilung",
    "Lied der Wiedergeburt": "notheilung",
    "Elixier der letzten Stunde": "notheilung",
    # Gruppenheilung (heilt die gesamte Gruppe auf einmal) - bewusst nur
    # vereinzelt vergeben, nicht jeder Heilzauber soll die ganze Gruppe treffen.
    "Wort der Genesung": "gruppenheilung",
    # Schild (reduziert erlittenen Schaden diese Runde, Ziel wählbar)
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
    "Geweihter Schild": "schild",
    "Steinerne Haltung": "schild",
    # Gruppenschild (schützt für mehrere Runden die gesamte Gruppe statt nur
    # den Anwender - das "sei vorsichtig" gilt hier: bewusst nur 1 pro
    # Tank-Pfad, mit spürbar, aber begrenzt langer Wirkung).
    "Letzte Bastion": "gruppenschild",
    "Märtyrergelübde": "gruppenschild",
    "Unbeugsamer Atem": "gruppenschild",
    # Reflexion (gibt einen Teil des erlittenen Schadens an den Angreifer zurück)
    "Dornenpanzer": "reflexion",
    "Vergeltungsschild": "reflexion",
    "Konterhaltung": "reflexion",
    # Aggro (zieht Aufmerksamkeit auf sich, wirkt wie ein Schild)
    "Spott": "aggro",
    "Provokation": "aggro",
    # Verstärkung (erhöht den nächsten Angriff, Ziel wählbar)
    "Kriegsschrei": "buff",
    "Kreaturenbund": "buff",
    "Kampflied": "buff",
    "Heldenepos": "buff",
    "Segen": "buff",
    "Gruppensegen": "buff",
    "Stärkungselixier": "buff",
    "Katalysator": "buff",
    # Schwächung (mindert die Kraft eines Gegners, Ziel wählbar - oder aller
    # Gegner, siehe SKILL_AOE)
    "Zeitverzerrung": "debuff",
    "Manaentzug": "debuff",
    "Schlaflied": "debuff",
    "Massenbezauberung": "debuff",
    "Spöttisches Lied": "debuff",
    # Schaden + Schwächung zugleich (z.B. Gift-/Seuchenwolken)
    "Giftnebel": "schaden_debuff",
    "Seuchenwolke": "schaden_debuff",
    "Verwesungswolke": "schaden_debuff",
    "Giftwolke": "schaden_debuff",
    "Zersetzungsgas": "schaden_debuff",

    # --- Aufstiegsklassen-Fähigkeiten ---
    # Schwächung (Einzelziel)
    "Todesfluch": "debuff",
    "Nervengift": "debuff",
    # Schwächung (Fläche, siehe SKILL_AOE)
    "Bindende Fessel": "debuff",
    "Lied der Verzweiflung": "debuff",
    "Fallennetz": "debuff",
    # Schild (Einzelziel)
    "Manabarriere": "schild",
    # Gruppenschild (mehrere Runden, gesamte Gruppe)
    "Rüstung des Gerechten": "gruppenschild",
    "Deckungsfeuer": "gruppenschild",
    "Schutzgeist beschwören": "gruppenschild",
    # Reflexion
    "Arkaner Gegenschlag": "reflexion",
    # Gruppenheilung
    "Geisterheilung": "gruppenheilung",
    # Verstärkung
    "Tödliche Präzision": "buff",
    "Kriegshymne": "buff",
    "Überladener Trank": "buff",

    # --- Signatur-Fähigkeiten (nur die jeweilige Aufstiegsklasse, ab Level 70,
    # einmal pro Kampf, siehe SKILL_SIGNATUR) ---
    "Unbezwingbare Mauer": "reflexion",
    "Licht der letzten Hoffnung": "gruppenheilung",
    "Schlag des unbeweglichen Berges": "schaden",
    "Große Pest": "schaden_debuff",
    "Arkane Singularität": "schaden",
    "Tödlicher Schwarm": "schaden_debuff",
    "Legion der Wächtergeister": "gruppenschild",
    "Sinfonie der Vernichtung": "schaden",
    "Pfeilsturm des Jahrhunderts": "schaden",
    "Gerechtes Urteil": "schaden",
    "Totale Verwüstung": "schaden",
}

# Skills, die alle Gegner gleichzeitig treffen statt nur einen einzelnen -
# Fernkämpfer bekommen so echte Flächenangriffe, Unterstützer echte
# Flächen-Schwächungszauber.
SKILL_AOE: set[str] = {
    "Pfeilhagel", "Sturm der tausend Pfeile", "Feuerball", "Meteor",
    "Massenbezauberung", "Giftnebel", "Seuchenwolke",
    "Verwesungswolke", "Knochensplitterhagel", "Giftwolke", "Bindende Fessel",
    "Zerreißender Akkord", "Lied der Verzweiflung", "Splitterpfeil", "Fallennetz",
    "Feuersturm des Glaubens", "Feuerbombe", "Zersetzungsgas",
    # Signatur-Fähigkeiten mit Flächenwirkung
    "Große Pest", "Tödlicher Schwarm", "Sinfonie der Vernichtung",
    "Pfeilsturm des Jahrhunderts", "Totale Verwüstung",
}

# Wie viele Kampfrunden ein Effekt anhält (nicht gelistete Skills wirken nur
# die eine Runde, in der sie eingesetzt werden). Bewusst nur wenige, klar
# tank-/notfallthematische Fähigkeiten mit echter Mehrrunden-Dauer, damit
# das nicht jede kleine Aktion zu einem Dauerbuff aufbläht.
SKILL_DAUER: dict[str, int] = {
    "Letzte Bastion": 3,
    "Märtyrergelübde": 3,
    "Unbeugsamer Atem": 3,
    "Dornenpanzer": 3,
    "Vergeltungsschild": 3,
    "Konterhaltung": 3,
    "Rüstung des Gerechten": 3,
    "Deckungsfeuer": 3,
    "Schutzgeist beschwören": 3,
    "Arkaner Gegenschlag": 3,
    # Signatur-Fähigkeiten mit Mehrrunden-Wirkung halten spürbar länger als
    # ihre regulären Pfad-Geschwister - schließlich sind sie der Höhepunkt.
    "Unbezwingbare Mauer": 4,
    "Legion der Wächtergeister": 4,
}

# Signatur-Fähigkeiten: der Höhepunkt jeder Aufstiegsklasse. Sie werden erst
# ab Level 70 erlernbar (siehe Charakter._eventuell_neuen_skill_lernen), sind
# ausschließlich über den jeweiligen Aufstiegspfad erlernbar - keine andere
# Klasse und kein Begleiter kann sie je nutzen - und wirken deutlich stärker
# als reguläre Fähigkeiten (siehe SIGNATUR_VERSTAERKUNG in game/combat.py).
# Genau deshalb sind sie zusätzlich auf einmal pro Kampf begrenzt.
SKILL_SIGNATUR: set[str] = {
    "Unbezwingbare Mauer", "Licht der letzten Hoffnung", "Schlag des unbeweglichen Berges",
    "Große Pest", "Arkane Singularität", "Tödlicher Schwarm", "Legion der Wächtergeister",
    "Sinfonie der Vernichtung", "Pfeilsturm des Jahrhunderts", "Gerechtes Urteil",
    "Totale Verwüstung",
}


def skill_effekt(skill_name: str) -> str:
    return SKILL_EFFEKT.get(skill_name, "schaden")


def skill_ist_aoe(skill_name: str) -> bool:
    return skill_name in SKILL_AOE


def skill_dauer(skill_name: str) -> int:
    return SKILL_DAUER.get(skill_name, 1)


def skill_ist_signatur(skill_name: str) -> bool:
    return skill_name in SKILL_SIGNATUR

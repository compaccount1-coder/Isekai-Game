"""Charakter: Stats, Level, XP, Skills und Fortschritt."""

import random
from dataclasses import dataclass, field

from game.classes import KLASSEN, TANK_PFADE, Klasse
from game.companions import Begleiter
from game.items import Item, Trank, generiere_item, generiere_trank, schmiede_upgrade

STATS = ("STR", "DEX", "INT", "WIS", "CON", "CHA")
MAX_AKTIONEN_PRO_TAG = 4


def xp_fuer_level(level: int) -> int:
    """XP, die insgesamt nötig ist, um `level` zu erreichen."""
    return int(50 * level**2.1)


@dataclass
class GelernterSkill:
    name: str
    level: int = 1
    erfahrung: int = 0

    def levelup_schwelle(self) -> int:
        return 20 * self.level

    def erfahrung_hinzufuegen(self, menge: int) -> bool:
        """Fügt Erfahrung hinzu. Gibt True zurück, wenn der Skill aufgestiegen ist."""
        self.erfahrung += menge
        if self.level >= 10:
            self.erfahrung = 0
            return False
        if self.erfahrung >= self.levelup_schwelle():
            self.erfahrung = 0
            self.level += 1
            return True
        return False


@dataclass
class Charakter:
    name: str
    klasse_id: str
    persoenlichkeit: list[str]
    level: int = 1
    xp: int = 0
    stats: dict[str, int] = field(default_factory=dict)
    gelernte_skills: dict[str, GelernterSkill] = field(default_factory=dict)
    hp_max: int = 0
    mp_max: int = 0
    gold: int = 0
    ruf: int = 0  # Reputation, kann negativ sein
    titel: list[str] = field(default_factory=list)
    inventar: list[Item] = field(default_factory=list)
    waffe: Item | None = None
    ruestung: Item | None = None
    accessoire: Item | None = None
    begleiter: list[Begleiter] = field(default_factory=list)
    gilde: str | None = None
    besiegte_gegner: int = 0
    tage_vergangen: int = 1
    aktionen_uebrig: int = MAX_AKTIONEN_PRO_TAG
    lebendig: bool = True
    hp_aktuell: int = 0
    mp_aktuell: int = 0
    rang: str = "F"
    abgeschlossene_quests: int = 0
    anwesen: str | None = None  # Name/Ort des Anwesens, falls gekauft
    hat_kutsche: bool = False
    traenke: list[Trank] = field(default_factory=list)
    besiegte_daemonenfuersten: list[str] = field(default_factory=list)
    daemonenkoenig_besiegt: bool = False
    spezialisierung: str | None = None  # "Tank" für Nahkämpfer, die sich zum Beschützer entwickelt haben
    story_gesehen: list[str] = field(default_factory=list)  # Schlüssel bereits gezeigter Story-Meilensteine

    @property
    def klasse(self) -> Klasse:
        return KLASSEN[self.klasse_id]

    @property
    def tier(self):
        if self.spezialisierung == "Tank" and self.klasse_id in TANK_PFADE:
            pfad = TANK_PFADE[self.klasse_id]
            if self.level >= pfad["tier70"].min_level:
                return pfad["tier70"]
            elif self.level >= pfad["tier30"].min_level:
                return pfad["tier30"]
        return self.klasse.tier_fuer_level(self.level)

    def schadensreduktion(self) -> float:
        """Passive Schadensreduktion durch die Tank-Spezialisierung - der
        mechanische Kern dessen, was einen Nahkämpfer zum Beschützer der
        Gruppe macht, statt nur ein weiterer Namenswechsel zu sein."""
        if self.spezialisierung != "Tank":
            return 0.0
        basis = 0.15
        if "Eiserne Deckung" in self.gelernte_skills or "Geweihter Schild" in self.gelernte_skills or "Steinerne Haltung" in self.gelernte_skills:
            basis += 0.1
        return min(basis, 0.3)

    def __post_init__(self):
        if not self.stats:
            basis = {s: random.randint(6, 10) for s in STATS}
            self.stats = basis
        if not self.gelernte_skills:
            for skill in self.klasse.start_skills():
                self.gelernte_skills[skill.name] = GelernterSkill(name=skill.name)
        self._hp_mp_neu_berechnen()
        if self.hp_aktuell <= 0:
            self.hp_aktuell = self.hp_max
        if self.mp_aktuell <= 0:
            self.mp_aktuell = self.mp_max
        if not self.traenke and self.level <= 1:
            self.traenke.append(generiere_trank(1, "Heilung"))
            self.traenke.append(generiere_trank(1, "Heilung"))
            self.traenke.append(generiere_trank(1, "Mana"))

    def _hp_mp_neu_berechnen(self):
        alter_hp_max = self.hp_max
        alter_mp_max = self.mp_max
        self.hp_max = 40 + self.stats["CON"] * 8 + self.level * 12
        self.mp_max = 20 + self.stats["INT"] * 6 + self.stats["WIS"] * 4 + self.level * 8
        # Aktuelle HP/MP proportional mitwachsen lassen, statt zu deckeln
        if alter_hp_max > 0 and self.hp_aktuell > 0:
            self.hp_aktuell = int(self.hp_aktuell * (self.hp_max / alter_hp_max))
        if alter_mp_max > 0 and self.mp_aktuell > 0:
            self.mp_aktuell = int(self.mp_aktuell * (self.mp_max / alter_mp_max))
        self.hp_aktuell = min(self.hp_aktuell, self.hp_max)
        self.mp_aktuell = min(self.mp_aktuell, self.mp_max)

    def schaden_erleiden(self, menge: int) -> bool:
        """Zieht Schaden ab. Gibt True zurück, wenn der Charakter dadurch stirbt."""
        self.hp_aktuell = max(0, self.hp_aktuell - menge)
        if self.hp_aktuell <= 0:
            self.lebendig = False
            return True
        return False

    def ausruhen(self) -> tuple[int, int]:
        """Regeneriert HP und MP (z.B. nach einer Rast in der Taverne).
        Gibt (geheilte HP, regenerierte MP) zurück. Im eigenen Anwesen fällt
        die Erholung großzügiger aus als in einer gemieteten Herberge."""
        faktor = (0.7, 1.0) if self.anwesen else (0.4, 0.8)
        geheilt = min(self.hp_max - self.hp_aktuell, int(self.hp_max * random.uniform(*faktor)))
        mp_regen = min(self.mp_max - self.mp_aktuell, int(self.mp_max * random.uniform(*faktor)))
        self.hp_aktuell += geheilt
        self.mp_aktuell += mp_regen
        return geheilt, mp_regen

    def xp_hinzufuegen(self, menge: int) -> list[str]:
        """Fügt XP hinzu, behandelt Level-ups. Gibt eine Liste von Ereignis-Meldungen zurück.
        Begleiter erhalten automatisch einen Anteil der XP und leveln
        eigenständig mit - sie verwalten ihre Fähigkeiten und Ausrüstung
        dabei komplett selbst, ohne dass der Spieler eingreifen muss."""
        meldungen = []
        for b in self.begleiter:
            if b.xp_hinzufuegen(int(menge * 0.6)):
                meldungen.append(f"🔺 {b.name} (Begleiter) erreicht Level {b.level}!")

        self.xp += menge
        while self.level < 100 and self.xp >= xp_fuer_level(self.level + 1):
            self.level += 1
            self._level_up_stats()
            meldungen.append(f"⭐ {self.name} erreicht Level {self.level}!")

            neuer_tier = self.klasse.tier_fuer_level(self.level)
            if neuer_tier.min_level == self.level:
                meldungen.append(
                    f"✨ Klassenentwicklung! {self.name} wird zu: {neuer_tier.name} - {neuer_tier.beschreibung}"
                )

            skill = self._eventuell_neuen_skill_lernen()
            if skill:
                meldungen.append(f"📖 Neuer Skill erlernt: {skill}")

        self._hp_mp_neu_berechnen()
        return meldungen

    def _level_up_stats(self):
        gewichte = self.klasse.stat_gewichte
        for stat in STATS:
            zuwachs = gewichte.get(stat, 1.0) * random.uniform(0.6, 1.4)
            if random.random() < zuwachs:
                self.stats[stat] += 1

    def _eventuell_neuen_skill_lernen(self) -> str | None:
        skill_pool = list(self.klasse.skills)
        if self.spezialisierung == "Tank" and self.klasse_id in TANK_PFADE:
            skill_pool += TANK_PFADE[self.klasse_id]["skills"]
        verfuegbar = [s for s in skill_pool if s.name not in self.gelernte_skills]
        if not verfuegbar:
            return None
        # Alle paar Level ein neuer Skill, gewichtet nach freien Plätzen vs. Level
        chance = 0.35 if self.level < 30 else 0.2
        if random.random() < chance or len(self.gelernte_skills) == 0:
            neuer = random.choice(verfuegbar)
            self.gelernte_skills[neuer.name] = GelernterSkill(name=neuer.name)
            return neuer.name
        return None

    def skill_ueben(self, skill_name: str, menge: int = 15) -> str | None:
        if skill_name not in self.gelernte_skills:
            return None
        aufgestiegen = self.gelernte_skills[skill_name].erfahrung_hinzufuegen(menge)
        if aufgestiegen:
            neues_level = self.gelernte_skills[skill_name].level
            return f"🔺 {skill_name} steigt auf Skill-Level {neues_level}!"
        return None

    def zufaelligen_skill_ueben(self) -> str | None:
        if not self.gelernte_skills:
            return None
        name = random.choice(list(self.gelernte_skills.keys()))
        return self.skill_ueben(name)

    def stat_gesamt(self) -> int:
        return sum(self.stats.values()) + self.ausruestungs_bonus()

    def ausruestungs_bonus(self) -> int:
        bonus = 0
        for teil in (self.waffe, self.ruestung, self.accessoire):
            if teil:
                bonus += teil.stat_gesamt()
        return bonus

    def kampfkraft(self) -> int:
        """Grober Gesamtwert für Kampfauflösung."""
        skill_bonus = sum(s.level for s in self.gelernte_skills.values())
        return self.stat_gesamt() + self.level * 3 + skill_bonus * 2 + self.begleiter_bonus()

    def begleiter_bonus(self) -> int:
        """Jeder Begleiter trägt anteilig zur Kampfkraft der Gruppe bei,
        gewichtet nach seinem eigenen Level (sie leveln automatisch mit
        geteilter XP mit, siehe xp_hinzufuegen) und ihrer Loyalität
        (unmotivierte Begleiter helfen weniger). Eine ausgewogene Gruppe
        (Nahkampf + Fernkampf + Unterstützung) erhält zusätzlich einen
        Synergie-Bonus."""
        from game.companions import ist_ausgewogene_gruppe

        basis_pro_begleiter = self.kampfkraft_basis() * 0.18
        basis = sum(
            int(basis_pro_begleiter * (b.loyalitaet / 100) * (b.level / max(1, self.level)))
            for b in self.begleiter
        )
        if self.begleiter and ist_ausgewogene_gruppe(self.begleiter):
            basis = int(basis * 1.25)
        return basis

    def kampfkraft_basis(self) -> int:
        skill_bonus = sum(s.level for s in self.gelernte_skills.values())
        return self.stat_gesamt() + self.level * 3 + skill_bonus * 2

    # -- Ausrüstungsverwaltung -------------------------------------------

    def _slot_fuer_typ(self, typ: str) -> str:
        return {"Waffe": "waffe", "Ruestung": "ruestung", "Accessoire": "accessoire"}[typ]

    def item_ist_besser(self, item: Item) -> bool:
        slot = self._slot_fuer_typ(item.typ)
        aktuelles = getattr(self, slot)
        if aktuelles is None:
            return True
        return item.stat_gesamt() > aktuelles.stat_gesamt()

    def fund_verarbeiten(self, item: Item) -> str:
        """Legt einen Fund ins Inventar - der Spieler entscheidet selbst, am
        Marktplatz, ob und wann er ihn ausrüstet oder verkauft."""
        self.inventar.append(item)
        hinweis = " ⭐ besser als deine aktuelle Ausrüstung!" if self.item_ist_besser(item) else ""
        return f"🎒 {self.name} findet {item.anzeige()}{hinweis} und verstaut es im Inventar."

    def ausruesten(self, item: Item) -> str:
        """Rüstet ein Item aus dem Inventar aus - das vorher ausgerüstete Teil
        (falls vorhanden) wandert zurück ins Inventar."""
        if item not in self.inventar:
            return f"{self.name} besitzt {item.name} nicht (mehr)."
        slot = self._slot_fuer_typ(item.typ)
        altes = getattr(self, slot)
        self.inventar.remove(item)
        setattr(self, slot, item)
        if altes:
            self.inventar.append(altes)
        self._hp_mp_neu_berechnen()
        return f"⚔️ {self.name} rüstet {item.anzeige()} aus."

    def verkaufen(self, item: Item) -> int:
        """Verkauft ein einzelnes Item aus dem Inventar. Gibt den Erlös zurück."""
        if item not in self.inventar:
            return 0
        self.inventar.remove(item)
        self.gold += item.wert
        return item.wert

    def inventar_aufraeumen(self, behalten: int = 3) -> tuple[int, int]:
        """Verkauft überschüssige Inventar-Items (behält die wertvollsten `behalten` Stück).
        Gibt (Anzahl verkauft, Gold erhalten) zurück."""
        if len(self.inventar) <= behalten:
            return 0, 0
        self.inventar.sort(key=lambda i: i.wert, reverse=True)
        zu_verkaufen = self.inventar[behalten:]
        self.inventar = self.inventar[:behalten]
        erloes = sum(i.wert for i in zu_verkaufen)
        self.gold += erloes
        return len(zu_verkaufen), erloes

    def trank_benutzen(self, trank: Trank) -> str:
        if trank not in self.traenke:
            return f"{self.name} besitzt {trank.name} nicht (mehr)."
        self.traenke.remove(trank)
        if trank.typ == "Heilung":
            geheilt = min(self.hp_max - self.hp_aktuell, trank.wirkung)
            self.hp_aktuell += geheilt
            return f"🧪 {self.name} trinkt {trank.name} und heilt {geheilt} HP."
        else:
            regeneriert = min(self.mp_max - self.mp_aktuell, trank.wirkung)
            self.mp_aktuell += regeneriert
            return f"🧪 {self.name} trinkt {trank.name} und regeneriert {regeneriert} MP."

    def bestes_trank_automatisch_nutzen(self, typ: str) -> str | None:
        """Der Charakter greift eigenständig zum stärksten passenden Trank,
        wenn er in Not ist (z.B. mitten in einem Kampf, wenn HP knapp werden)."""
        passende = [t for t in self.traenke if t.typ == typ]
        if not passende:
            return None
        bester = max(passende, key=lambda t: t.wirkung)
        return self.trank_benutzen(bester)

    def schmiede_verbessern(self, slot: str) -> str | None:
        """Verbessert ein bestimmtes, vom Spieler gewähltes, ausgerüstetes Teil
        beim Schmied, falls genug Gold vorhanden ist."""
        aktuelles = getattr(self, slot, None)
        if not aktuelles:
            return None
        verbessert, kosten = schmiede_upgrade(aktuelles)
        if self.gold < kosten:
            return None
        self.gold -= kosten
        setattr(self, slot, verbessert)
        self._hp_mp_neu_berechnen()
        return f"🔨 {self.name} lässt {aktuelles.name} beim Schmied für {kosten}g verbessern -> {verbessert.name}!"

    def status_zeile(self) -> str:
        return (
            f"{self.name} | {self.tier.name} (Lv. {self.level}) | "
            f"HP {self.hp_aktuell}/{self.hp_max} | MP {self.mp_max} | "
            f"Ruf {self.ruf:+d} | Gold {self.gold}"
        )

    def ausruestungs_zeile(self) -> str:
        def teil(item: Item | None) -> str:
            return item.name if item else "-"
        return f"⚔ {teil(self.waffe)}  🛡 {teil(self.ruestung)}  💍 {teil(self.accessoire)}"

    def begleiter_zeile(self) -> str:
        if not self.begleiter:
            return "Reist allein."
        return "Gruppe: " + ", ".join(b.anzeige() for b in self.begleiter)

    def begleiter_aufnehmen(self, begleiter: Begleiter, max_gruppengroesse: int = 3):
        if len(self.begleiter) < max_gruppengroesse:
            self.begleiter.append(begleiter)

    def begleiter_entfernen(self, begleiter: Begleiter):
        if begleiter in self.begleiter:
            self.begleiter.remove(begleiter)

    def loyalitaet_aendern(self, begleiter: Begleiter, menge: int):
        begleiter.loyalitaet = max(0, min(100, begleiter.loyalitaet + menge))

"""Der Gildenmeister: eine feste, wiederkehrende Figur mit eigenem Namen -
anders als die anonymen, austauschbaren NPCs der übrigen Zufallsereignisse -,
die die Handlung aktiv Richtung Dämonenkönig trägt. Bietet drei Arten von
Interaktion: sporadische Gespräche über den aktuellen Fortschritt, besondere
narrativ verankerte Sonderaufträge, und - an wenigen handverlesenen
Wendepunkten - echte Entscheidungen mit spürbaren, dauerhaften Konsequenzen
für Ruf, Gold und die Gruppe (siehe charakter.entscheidungen)."""

import random
from dataclasses import dataclass
from typing import Callable

from game.combat import Kampfstart, erwartete_kampfkraft, kampf_starten
from game.companions import generiere_begleiter, gruppen_rollen
from game.endgame import DAEMONENFUERSTEN, DAEMONENKOENIG_NAME
from game.events import Ereignis
from game.ranks import rang_index

# (Name, Geschlecht) - das Geschlecht bestimmt nur die Pronomen in den
# Dialogtexten (siehe _pronomen), wird aber NICHT extra auf dem Charakter
# gespeichert, sondern bei Bedarf aus dem einmal gewürfelten, gespeicherten
# Namen zurück nachgeschlagen (_GESCHLECHT_JE_NAME).
GILDENMEISTER_NAMEN = [
    ("Aldric Sturmwacht", "m"), ("Thessaly Eisenmark", "w"), ("Borgen Graureiter", "m"),
    ("Idris Falkenauge", "m"), ("Wilhelma Drachenherz", "w"), ("Cassian Nachtklinge", "m"),
    ("Freya Steinschild", "w"), ("Roderick Hallow", "m"), ("Ingrid Wolfsmantel", "w"),
    ("Tamsin Bogenbrecher", "w"),
]
_GESCHLECHT_JE_NAME = dict(GILDENMEISTER_NAMEN)
_PRONOMEN = {"m": ("er", "sein", "ihm"), "w": ("sie", "ihr", "ihr")}  # (er/sie, sein/ihr, ihm/ihr)


def gildenmeister_name(charakter) -> str:
    """Würfelt beim allerersten Aufruf einen Namen und hält ihn danach über
    den gesamten Spieldurchlauf stabil (auf dem Charakter gespeichert) -
    derselbe Gildenmeister begleitet die ganze Geschichte, statt bei jedem
    Gespräch ein neues Gesicht zu sein."""
    if not charakter.gildenmeister_name:
        charakter.gildenmeister_name = random.choice(GILDENMEISTER_NAMEN)[0]
    return charakter.gildenmeister_name


def _pronomen(charakter) -> tuple[str, str, str]:
    """(er/sie, sein/ihr, ihm/ihr), abgeleitet aus dem gewürfelten Namen -
    damit Dialogtexte grammatisch zum jeweiligen Gildenmeister passen."""
    geschlecht = _GESCHLECHT_JE_NAME.get(gildenmeister_name(charakter), "m")
    return _PRONOMEN[geschlecht]


# ---------------------------------------------------------------------------
# Sporadische Gespräche über den Fortschritt
# ---------------------------------------------------------------------------

def _fortschritts_pool(charakter) -> list[str]:
    besiegt = len(charakter.besiegte_daemonenfuersten)
    gesamt = len(DAEMONENFUERSTEN)
    if besiegt >= gesamt:
        return [
            f'"Alle Unterlinge sind gefallen. Es gibt keine Ausreden mehr - nur noch {DAEMONENKOENIG_NAME} selbst. Wann immer du bereit bist."',
            '"Ich habe in all meinen Jahren als Gildenmeister nie geglaubt, diesen Tag zu erleben. Und doch stehst du hier, bereit für das Letzte."',
            f'"Man erzählt sich in jeder Taverne von dir. Aber die Geschichte ist noch nicht zu Ende - {DAEMONENKOENIG_NAME} wartet noch."',
        ]
    if besiegt > 0:
        return [
            f'"{besiegt} von {gesamt} Unterlingen gefallen, durch deine Hand. Die übrigen werden vorsichtiger geworden sein - unterschätze sie nicht."',
            '"Jeder gefallene Unterling ist ein Nagel im Sarg des Dämonenkönigs. Mach weiter so."',
            '"Die Gilde spricht nur noch von deinen Jagden. Halt den Kopf trotzdem unten - Stolz hat schon bessere Abenteurer als dich das Leben gekostet."',
        ]
    idx = rang_index(charakter.rang)
    if idx >= rang_index("A"):
        return [
            '"Die Koalition zählt auf dich. Ich weiß, das ist eine schwere Last - aber ich kenne niemand Geeigneteren, sie zu tragen."',
            '"Wenn ich zurückdenke, wie du hier ankamst... Die Welt verändert Menschen. Bei dir zum Besseren, hoffe ich."',
            '"Bald wird man dich nach Rang S rufen. Danach gibt es kein Zurück mehr - nur noch die Jagd auf die Unterlinge."',
        ]
    if idx >= rang_index("C"):
        return [
            '"Die Gerüchte über den Dämonenkönig werden lauter. Ich wünschte, ich könnte dir sagen, dass sie übertrieben sind."',
            '"Du machst Fortschritte, die ich selten sehe. Aber sei gewarnt - was vor dir liegt, ist größer als jeder gewöhnliche Auftrag."',
            '"Manchmal frage ich mich, ob die alten Chroniken über den Dämonenkönig doch mehr Wahrheit enthalten, als uns lieb ist."',
        ]
    return [
        '"Noch ein Neuling - aber ich habe ein Auge für Potential, und deins sticht heraus."',
        '"Fleißig weiter Aufträge annehmen. Rang und Ruf kommen nicht über Nacht, aber sie kommen."',
        '"Die Gilde braucht mehr wie dich. Halt dich einfach am Leben, dann sehen wir, wie weit du kommst."',
    ]


def gildenmeister_gespraech(charakter) -> Ereignis:
    """Reines Gespräch ohne mechanischen Wert - anders als ein Sonderauftrag
    oder eine Entscheidung ist das bloße Reden mit dem Gildenmeister keine
    Aktivität, die XP, Ruf oder eine der täglichen Aktionen kosten sollte."""
    name = gildenmeister_name(charakter)
    zitat = random.choice(_fortschritts_pool(charakter))
    text = f"🗣️ {name}, der Gildenmeister, winkt {charakter.name} zu sich. {zitat}"
    return Ereignis(text=text, ist_wichtig=True, kostet_aktion=False)


# ---------------------------------------------------------------------------
# Sonderaufträge
# ---------------------------------------------------------------------------

_SONDERAUFTRAEGE = [
    ("bittet dich persönlich, einen Spion aufzuspüren, der sich in die Gilde eingeschlichen haben soll", "Verräterischer Kundschafter"),
    ("braucht jemanden, der diskret einer Blutspur nachgeht, die niemand sonst verfolgen will", "Namenloser Verfolger"),
    ("verlangt Verstärkung für eine Karawane, die durch Gebiet reist, in dem zuletzt Unterlinge gesichtet wurden", "Wegelagerer im Dienst der Finsternis"),
    ("bittet um Hilfe, ein Ritual zu unterbinden, das ein finsterer Kult zu Ehren des Dämonenkönigs vorbereitet", "Kultist des schwarzen Throns"),
]


def gildenmeister_sonderauftrag(charakter) -> "Ereignis | Kampfstart":
    name = gildenmeister_name(charakter)
    beschreibung, gegner_name = random.choice(_SONDERAUFTRAEGE)
    einleitung = f"⭐ {name}, der Gildenmeister, {beschreibung}."
    staerke = int(erwartete_kampfkraft(charakter.level) * random.uniform(0.9, 1.15))
    kampf = kampf_starten(charakter, gegner_name, staerke)

    def bei_abschluss(ergebnis):
        log = [einleitung] + ergebnis.log[1:]
        if ergebnis.sieg:
            gold = int(erwartete_kampfkraft(charakter.level) * random.uniform(0.4, 0.7))
            log.append(f'✅ {name} ist sichtlich erleichtert: "Gute Arbeit. Die Gilde weiß das zu schätzen."')
            return Ereignis(text="Sonderauftrag des Gildenmeisters erfüllt", xp=int(ergebnis.xp_gewonnen * 1.3), gold=gold, ruf=6, log=log, ist_wichtig=True)
        else:
            log.append(f'{name} nickt trotzdem knapp: "Nicht jeder Auftrag lässt sich gewinnen. Ruh dich aus, dann versuchen wir es wieder."')
            return Ereignis(text="Sonderauftrag des Gildenmeisters gescheitert", xp=ergebnis.xp_gewonnen, log=log)

    return Kampfstart(kampf, bei_abschluss)


# ---------------------------------------------------------------------------
# Entscheidungen: seltene, aber folgenreiche Wendepunkte
# ---------------------------------------------------------------------------

@dataclass
class Entscheidung:
    schluessel: str
    bedingung: Callable[[object], bool]
    ansage: Callable[[object], str]
    optionen: list  # [(label, funktion(charakter) -> Ereignis), (label, funktion), ...]


def _entscheidung_kundschafter_gnade(charakter) -> Ereignis:
    charakter.entscheidungen["gefangener_kundschafter"] = "gnade"
    name = gildenmeister_name(charakter)
    _, sein_ihr, _ = _pronomen(charakter)
    text = (
        f"🕊️ {charakter.name} verhört den gefangenen Kundschafter des Dämonenkönigs geduldig - und lässt ihn "
        f"danach entgegen jeder Erwartung frei. \"Das wird sich rächen\", murmelt {name}, doch {sein_ihr} Blick "
        f"verrät unverkennbaren Respekt. Die Nachricht von dieser Gnade verbreitet sich weit über die "
        f"Gildenmauern hinaus."
    )
    return Ereignis(text=text, ruf=10, xp=int(25 * charakter.level), ist_wichtig=True)


def _entscheidung_kundschafter_strafe(charakter) -> Ereignis:
    charakter.entscheidungen["gefangener_kundschafter"] = "strafe"
    name = gildenmeister_name(charakter)
    er_sie, sein_ihr, _ = _pronomen(charakter)
    gold = int(30 * charakter.level * random.uniform(0.8, 1.2))
    text = (
        f"⚔️ {charakter.name} übergibt den gefangenen Kundschafter des Dämonenkönigs ohne Zögern der Gilde zur "
        f"Bestrafung. {name} zahlt das vereinbarte Kopfgeld aus, doch in {sein_ihr}em Blick liegt ein Hauch von "
        f"Unbehagen. \"Effizient\", sagt {er_sie} nur. \"Ob auch klug, wird sich zeigen.\""
    )
    return Ereignis(text=text, ruf=-6, gold=gold, xp=int(15 * charakter.level), ist_wichtig=True)


def _entscheidung_buendnis_ja(charakter) -> Ereignis:
    charakter.entscheidungen["soeldner_buendnis"] = "buendnis"
    name = gildenmeister_name(charakter)
    if len(charakter.begleiter) < 3:
        rekrut = generiere_begleiter(gruppen_rollen(charakter.begleiter))
        charakter.begleiter_aufnehmen(rekrut)
        text = (
            f"🤝 {charakter.name} bürgt vor der versammelten Gilde für die fremde Söldnertruppe. Aus Dank schließt "
            f"sich {rekrut.name}, eine ihrer Fähigsten, {charakter.name}s Gruppe an. {name} nickt zufrieden: "
            f"\"Eine Koalition lebt von Vertrauen. Gut gemacht.\""
        )
        return Ereignis(text=text, ruf=5, xp=int(20 * charakter.level), ist_wichtig=True)
    gold = int(40 * charakter.level)
    text = (
        f"🤝 {charakter.name} bürgt vor der versammelten Gilde für die fremde Söldnertruppe. Die eigene Gruppe ist "
        f"bereits voll besetzt, doch die Söldner zeigen ihre Dankbarkeit in klingender Münze. {name} nickt "
        f"zufrieden: \"Eine Koalition lebt von Vertrauen. Gut gemacht.\""
    )
    return Ereignis(text=text, ruf=5, gold=gold, xp=int(20 * charakter.level), ist_wichtig=True)


def _entscheidung_buendnis_nein(charakter) -> Ereignis:
    charakter.entscheidungen["soeldner_buendnis"] = "ablehnung"
    name = gildenmeister_name(charakter)
    gold = int(25 * charakter.level)
    text = (
        f"🛡️ {charakter.name} lehnt es ab, für die unbekannte Söldnertruppe zu bürgen - zu viel steht auf dem "
        f"Spiel, um Fremden blind zu vertrauen. {name} zeigt Verständnis: \"Vorsicht war noch nie eine Schande. "
        f"Die Gilde honoriert deine Zurückhaltung.\""
    )
    return Ereignis(text=text, ruf=3, gold=gold, xp=int(18 * charakter.level), ist_wichtig=True)


def _entscheidung_strategie_angriff(charakter) -> Ereignis:
    charakter.entscheidungen["koalition_strategie"] = "angriff"
    name = gildenmeister_name(charakter)
    text = (
        f"⚔️ {charakter.name} spricht sich in der Kriegsversammlung der Koalition für offensive, präventive "
        f"Schläge gegen die Unterlinge des Dämonenkönigs aus. {name} unterstützt die Entscheidung, auch wenn "
        f"nicht jeder in der Halle begeistert ist: \"Mutig. Hoffentlich auch richtig.\" Die verschärfte "
        f"Ausbildung, die daraus folgt, zahlt sich sofort aus."
    )
    return Ereignis(text=text, xp=int(60 * charakter.level), ruf=4, ist_wichtig=True)


def _entscheidung_strategie_verteidigung(charakter) -> Ereignis:
    charakter.entscheidungen["koalition_strategie"] = "verteidigung"
    name = gildenmeister_name(charakter)
    text = (
        f"🛡️ {charakter.name} plädiert in der Kriegsversammlung der Koalition für einen besonnenen, "
        f"defensiven Kurs - erst die Verteidigungslinien sichern, dann angreifen. {name} nickt zustimmend: "
        f"\"Die Klugen überleben, um am Ende zu siegen. Gut gesprochen.\" Die Gilde und ihre Verbündeten "
        f"gewinnen spürbar an Vertrauen in die Führung."
    )
    return Ereignis(text=text, ruf=14, xp=int(20 * charakter.level), ist_wichtig=True)


def _bedingung_kundschafter(charakter) -> bool:
    return rang_index(charakter.rang) >= rang_index("C") and "gefangener_kundschafter" not in charakter.entscheidungen


def _bedingung_buendnis(charakter) -> bool:
    return rang_index(charakter.rang) >= rang_index("B") and "soeldner_buendnis" not in charakter.entscheidungen


def _bedingung_strategie(charakter) -> bool:
    return rang_index(charakter.rang) >= rang_index("A") and "koalition_strategie" not in charakter.entscheidungen


ENTSCHEIDUNGEN: list[Entscheidung] = [
    Entscheidung(
        "gefangener_kundschafter",
        _bedingung_kundschafter,
        lambda charakter: (
            f'{gildenmeister_name(charakter)}, der Gildenmeister, führt dich in eine schwer bewachte Zelle. '
            f'"Wir haben einen Kundschafter des Dämonenkönigs gefasst", sagt {_pronomen(charakter)[0]} leise. '
            f'"Was tun wir mit ihm?"'
        ),
        [
            ("Ihn verhören und danach gnädig freilassen", _entscheidung_kundschafter_gnade),
            ("Ihn der Gilde zur harten Bestrafung übergeben", _entscheidung_kundschafter_strafe),
        ],
    ),
    Entscheidung(
        "soeldner_buendnis",
        _bedingung_buendnis,
        lambda charakter: (
            f'{gildenmeister_name(charakter)}, der Gildenmeister, bittet dich um Rat. "Eine fremde '
            f'Söldnertruppe will sich der Koalition anschließen. Ich brauche jemanden, der für sie bürgt. '
            f'Was sagst du?"'
        ),
        [
            ("Für die Söldner bürgen", _entscheidung_buendnis_ja),
            ("Ablehnen - zu riskant", _entscheidung_buendnis_nein),
        ],
    ),
    Entscheidung(
        "koalition_strategie",
        _bedingung_strategie,
        lambda charakter: (
            f'{gildenmeister_name(charakter)}, der Gildenmeister, ruft dich in die Kriegsversammlung der '
            f'Koalition. "Wir müssen uns auf eine Strategie einigen, bevor es zu spät ist. Angriff oder '
            f'Verteidigung - was ist deine Stimme?"'
        ),
        [
            ("Für offensive, präventive Schläge stimmen", _entscheidung_strategie_angriff),
            ("Für eine besonnene Verteidigung stimmen", _entscheidung_strategie_verteidigung),
        ],
    ),
]


def naechste_entscheidung(charakter) -> "Entscheidung | None":
    """Gibt die erste noch unbeantwortete, freigeschaltete Entscheidung
    zurück (oder None) - Reihenfolge der Liste entspricht der narrativen
    Abfolge (Rang C vor B vor A)."""
    for entscheidung in ENTSCHEIDUNGEN:
        if entscheidung.bedingung(charakter):
            return entscheidung
    return None

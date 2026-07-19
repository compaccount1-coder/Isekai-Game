"""Die Dämonenkönig-Handlung: das ultimative Ziel des Spiels, freigeschaltet
bei Erreichen von Rang S. Erst müssen die Unterlinge des Dämonenkönigs
gejagt werden, bevor er selbst herausgefordert werden kann."""

import random

from game.combat import Kampfstart, erwartete_kampfkraft, kampf_starten
from game.events import Ereignis

DAEMONENFUERSTEN = [
    ("Malgorath, die Verschlingende Klaue", "einst ein General der Dämonenlegionen, nun Herrscher über ein Ödland voller Verdammter"),
    ("Nyxandra, Herrin der tausend Schnitte", "eine Attentäterin des Dämonenkönigs, die keine Spur ihrer Opfer zurücklässt"),
    ("Vorgrimm der Unaufhaltsame", "ein gepanzerter Koloss, der einst eine ganze Legion allein aufhielt"),
    ("Seliphrae, die Flüsternde Seuche", "eine Dämonin, deren bloße Gegenwart Königreiche von innen zerfallen lässt"),
]

DAEMONENKOENIG_NAME = "Abraxos, der Dämonenkönig"


def verbleibende_fuersten(charakter) -> list[tuple[str, str]]:
    return [f for f in DAEMONENFUERSTEN if f[0] not in charakter.besiegte_daemonenfuersten]


def daemonenjagd_verfuegbar(charakter) -> bool:
    return charakter.rang == "S"


def demonenkoenig_verfuegbar(charakter) -> bool:
    return charakter.rang == "S" and len(charakter.besiegte_daemonenfuersten) >= len(DAEMONENFUERSTEN)


def jage_daemonenfuersten(charakter, ziel: tuple[str, str]) -> "Ereignis | Kampfstart":
    name, beschreibung = ziel
    # erwartete_kampfkraft liegt bereits ca. 20-25% über der tatsächlichen
    # Kampfkraft eines Durchschnittscharakters (siehe combat.py), daher
    # entspricht schon ein Faktor um 1.0 einer echten Herausforderung. Die
    # frühere Spanne 1.5-1.9x machte die Unterlinge - den Weg zum Endziel -
    # praktisch unbesiegbar (fast garantierter Tod statt spannendem Kampf).
    staerke = int(erwartete_kampfkraft(charakter.level) * random.uniform(1.05, 1.3))
    einleitung = f"👹 Die Jagd beginnt: {charakter.name} spürt {name} auf - {beschreibung}."
    kampf = kampf_starten(charakter, name, staerke, max_runden=12)

    def bei_abschluss(ergebnis):
        log = list(ergebnis.log)
        if ergebnis.sieg:
            charakter.besiegte_daemonenfuersten.append(name)
            log.append(f"🏆 {name} ist gefallen! Noch {len(DAEMONENFUERSTEN) - len(charakter.besiegte_daemonenfuersten)} Unterlinge des Dämonenkönigs stehen zwischen {charakter.name} und der letzten Konfrontation.")
        elif charakter.lebendig:
            log.append(f"{name} erweist sich als zu mächtig - {charakter.name} zieht sich zurück, um zu einem anderen Zeitpunkt zurückzukehren.")
        return Ereignis(text=einleitung, log=log, xp=ergebnis.xp_gewonnen, gold=ergebnis.gold_gewonnen, ist_wichtig=ergebnis.sieg)

    return Kampfstart(kampf, bei_abschluss)


def konfrontiere_daemonenkoenig(charakter) -> "Ereignis | Kampfstart":
    # Der schwerste Kampf im Spiel - spürbar über den Unterlingen, aber
    # nicht mehr im Bereich eines faktisch sicheren Todes (siehe
    # jage_daemonenfuersten für dieselbe Kalibrierungsüberlegung).
    staerke = int(erwartete_kampfkraft(charakter.level) * random.uniform(1.3, 1.6))
    einleitung = (
        f"👑💀 Die Welt selbst scheint den Atem anzuhalten - {charakter.name} steht {DAEMONENKOENIG_NAME} gegenüber, "
        f"dem Ursprung jeder Dunkelheit, die diese Welt je heimgesucht hat."
    )
    kampf = kampf_starten(charakter, DAEMONENKOENIG_NAME, staerke, max_runden=15)

    def bei_abschluss(ergebnis):
        log = list(ergebnis.log)
        if ergebnis.sieg:
            charakter.daemonenkoenig_besiegt = True
            log.append(
                f"🌅 {DAEMONENKOENIG_NAME} zerfällt zu Asche. Die Welt atmet auf. "
                f"{charakter.name}s Name wird für immer als der Name der Heldengruppe genannt werden, die den Dämonenkönig besiegte."
            )
        elif charakter.lebendig:
            log.append(f"Selbst {charakter.name}s ganze Kraft reicht nicht - ein Rückzug ist die einzige Option, für heute.")
        return Ereignis(text=einleitung, log=log, xp=ergebnis.xp_gewonnen, gold=ergebnis.gold_gewonnen, ist_wichtig=True)

    return Kampfstart(kampf, bei_abschluss)

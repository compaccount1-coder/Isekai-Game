"""Die Dämonenkönig-Handlung: das ultimative Ziel des Spiels, freigeschaltet
bei Erreichen von Rang S. Erst müssen die Unterlinge des Dämonenkönigs
gejagt werden, bevor er selbst herausgefordert werden kann."""

import random
from dataclasses import dataclass

from game.combat import erwartete_kampfkraft, rundenbasierter_kampf

DAEMONENFUERSTEN = [
    ("Malgorath, die Verschlingende Klaue", "einst ein General der Dämonenlegionen, nun Herrscher über ein Ödland voller Verdammter"),
    ("Nyxandra, Herrin der tausend Schnitte", "eine Attentäterin des Dämonenkönigs, die keine Spur ihrer Opfer zurücklässt"),
    ("Vorgrimm der Unaufhaltsame", "ein gepanzerter Koloss, der einst eine ganze Legion allein aufhielt"),
    ("Seliphrae, die Flüsternde Seuche", "eine Dämonin, deren bloße Gegenwart Königreiche von innen zerfallen lässt"),
]

DAEMONENKOENIG_NAME = "Abraxos, der Dämonenkönig"


@dataclass
class DaemonenfuerstErgebnis:
    name: str
    sieg: bool
    log: list[str]
    xp_gewonnen: int
    gold_gewonnen: int


def verbleibende_fuersten(charakter) -> list[tuple[str, str]]:
    return [f for f in DAEMONENFUERSTEN if f[0] not in charakter.besiegte_daemonenfuersten]


def daemonenjagd_verfuegbar(charakter) -> bool:
    return charakter.rang == "S"


def demonenkoenig_verfuegbar(charakter) -> bool:
    return charakter.rang == "S" and len(charakter.besiegte_daemonenfuersten) >= len(DAEMONENFUERSTEN)


def jage_daemonenfuersten(charakter, ziel: tuple[str, str]) -> DaemonenfuerstErgebnis:
    name, beschreibung = ziel
    # erwartete_kampfkraft liegt bereits ca. 20-25% über der tatsächlichen
    # Kampfkraft eines Durchschnittscharakters (siehe combat.py), daher
    # entspricht schon ein Faktor um 1.0 einer echten Herausforderung. Die
    # frühere Spanne 1.5-1.9x machte die Unterlinge - den Weg zum Endziel -
    # praktisch unbesiegbar (fast garantierter Tod statt spannendem Kampf).
    staerke = int(erwartete_kampfkraft(charakter.level) * random.uniform(1.05, 1.3))
    log = [f"👹 {charakter.name} spürt {name} auf - {beschreibung}."]

    ergebnis = rundenbasierter_kampf(charakter, name, staerke, max_runden=12)
    log.extend(ergebnis.log)

    if ergebnis.sieg:
        charakter.besiegte_daemonenfuersten.append(name)
        log.append(f"🏆 {name} ist gefallen! Noch {len(DAEMONENFUERSTEN) - len(charakter.besiegte_daemonenfuersten)} Unterlinge des Dämonenkönigs stehen zwischen {charakter.name} und der letzten Konfrontation.")
    elif charakter.lebendig:
        log.append(f"{name} erweist sich als zu mächtig - {charakter.name} zieht sich zurück, um zu einem anderen Zeitpunkt zurückzukehren.")

    return DaemonenfuerstErgebnis(
        name=name, sieg=ergebnis.sieg, log=log,
        xp_gewonnen=ergebnis.xp_gewonnen, gold_gewonnen=ergebnis.gold_gewonnen,
    )


def konfrontiere_daemonenkoenig(charakter) -> DaemonenfuerstErgebnis:
    # Der schwerste Kampf im Spiel - spürbar über den Unterlingen, aber
    # nicht mehr im Bereich eines faktisch sicheren Todes (siehe
    # jage_daemonenfuersten für dieselbe Kalibrierungsüberlegung).
    staerke = int(erwartete_kampfkraft(charakter.level) * random.uniform(1.3, 1.6))
    log = [
        f"👑💀 Die Welt selbst scheint den Atem anzuhalten - {charakter.name} steht {DAEMONENKOENIG_NAME} gegenüber, "
        f"dem Ursprung jeder Dunkelheit, die diese Welt je heimgesucht hat.",
    ]
    ergebnis = rundenbasierter_kampf(charakter, DAEMONENKOENIG_NAME, staerke, max_runden=15)
    log.extend(ergebnis.log)

    if ergebnis.sieg:
        log.append(
            f"🌅 {DAEMONENKOENIG_NAME} zerfällt zu Asche. Die Welt atmet auf. "
            f"{charakter.name}s Name wird für immer als der Name der Heldengruppe genannt werden, die den Dämonenkönig besiegte."
        )
    elif charakter.lebendig:
        log.append(f"Selbst {charakter.name}s ganze Kraft reicht nicht - ein Rückzug ist die einzige Option, für heute.")

    return DaemonenfuerstErgebnis(
        name=DAEMONENKOENIG_NAME, sieg=ergebnis.sieg, log=log,
        xp_gewonnen=ergebnis.xp_gewonnen, gold_gewonnen=ergebnis.gold_gewonnen,
    )

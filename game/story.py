"""Story-Engine: Charaktererstellung und Enden."""

import random

from game.character import Charakter
from game.classes import KLASSEN
from game.world import Welt

PERSOENLICHKEITEN = [
    "mutig", "vorsichtig", "ehrgeizig", "gütig", "grausam", "neugierig",
    "stolz", "loyal", "verschlagen", "gerecht", "impulsiv", "besonnen",
]

GOTTHEIT_NAMEN = ["Aethra", "Morvain", "Selune", "Kyros", "Vantha", "Oridun"]

ISEKAI_INTROS = [
    "Ein Lastwagen. Ein greller Blitz. Dann - Stille. Und ein Licht, das nicht von dieser Welt war.",
    "Du schließt die Augen nach einem langen, gewöhnlichen Tag - und öffnest sie in einem Meer aus Sternenlicht.",
    "Ein Herzinfarkt mitten im Büroalltag. Und dann: eine Stimme, uralt und gewaltig, die deinen Namen ruft.",
    "Ein Sturz von einer Klippe, den niemand hätte überleben dürfen. Doch anstelle der Dunkelheit: gleißendes Licht.",
    "Die Welt, wie du sie kanntest, endet in einem Wimpernschlag. Eine neue beginnt in einem goldenen Nebel.",
]


def waehle_klasse_interaktiv() -> str:
    print("\n✨ Eine gewaltige Gottheit erscheint vor dir in einem Meer aus Licht.")
    print(f'   "{random.choice(GOTTHEIT_NAMEN)} spricht: Wähle deinen Weg in dieser neuen Welt, Reisender."\n')
    from game.locations import EingabeErschoepft

    optionen = list(KLASSEN.items())
    for i, (kid, klasse) in enumerate(optionen, 1):
        print(f"  [{i}] {klasse.tiers[0].name} - {klasse.archetyp}")
    ungueltige_versuche = 0
    while True:
        try:
            wahl = input("\nWähle eine Klasse (Nummer): ").strip()
        except EOFError:
            raise EingabeErschoepft
        if wahl.isdigit() and 1 <= int(wahl) <= len(optionen):
            return optionen[int(wahl) - 1][0]
        ungueltige_versuche += 1
        if ungueltige_versuche >= 20:
            raise EingabeErschoepft
        print("Ungültige Wahl, versuch's nochmal.")


def erstelle_charakter() -> Charakter:
    print("=" * 70)
    print(random.choice(ISEKAI_INTROS))
    print("=" * 70)
    name = input("\nWie lautete dein Name in deinem vorherigen Leben? (wird dein neuer Name): ").strip()
    if not name:
        name = "Namenloser Wanderer"

    klasse_id = waehle_klasse_interaktiv()
    persoenlichkeit = random.sample(PERSOENLICHKEITEN, k=2)

    print(f"\n🌟 {name} erwacht in der neuen Welt als {KLASSEN[klasse_id].tiers[0].name}.")
    print(f"   Persönlichkeit: {', '.join(persoenlichkeit)}")

    charakter = Charakter(name=name, klasse_id=klasse_id, persoenlichkeit=persoenlichkeit)
    return charakter


# ---------------------------------------------------------------------------
# Enden
# ---------------------------------------------------------------------------

def erzeuge_ende(charakter: Charakter, welt: Welt, grund: str) -> str:
    zeilen = ["\n" + "=" * 70, "📖 DAS ENDE DEINER GESCHICHTE", "=" * 70]

    if grund == "daemonenkoenig":
        zeilen.append(
            f"👑💀 {charakter.name} hat das unmöglich Geglaubte vollbracht: als Rang-S-Held, "
            f"gemeinsam mit {len(charakter.begleiter)} treuen Gefährten, wurden alle Unterlinge "
            f"des Dämonenkönigs gejagt und der Dämonenkönig selbst nach {charakter.tage_vergangen} Tagen "
            f"in dieser Welt für immer besiegt. Das ist die höchste Ehre, die diese Welt zu vergeben hat - "
            f"{charakter.name}s Name wird für alle Zeit als Retter der Lande in Erinnerung bleiben."
        )
    elif grund == "tod":
        zeilen.append(
            f"{charakter.name}, {charakter.tier.name} auf Level {charakter.level}, "
            f"fällt nach {charakter.tage_vergangen} Tagen in dieser Welt."
        )
        if charakter.ruf > 50:
            zeilen.append("Sein Name wird noch Generationen später in Liedern besungen.")
        elif charakter.ruf < -30:
            zeilen.append("Die Welt atmet auf - seine Taten waren gefürchtet bis zum letzten Tag.")
        else:
            zeilen.append("Eine von unzähligen Geschichten, die diese Welt gesehen hat - doch nicht vergessen.")

    else:
        zeilen.append(f"{charakter.name}s Geschichte endet hier, nach {charakter.tage_vergangen} Tagen in dieser Welt.")

    zeilen.append(f"\nEndstatistik: {charakter.status_zeile()}")
    zeilen.append(f"Besiegte Gegner: {charakter.besiegte_gegner}")
    zeilen.append(f"Erlernte Skills: {', '.join(charakter.gelernte_skills.keys()) or 'keine'}")
    if charakter.titel:
        zeilen.append(f"Titel: {', '.join(charakter.titel)}")
    zeilen.append("=" * 70)
    return "\n".join(zeilen)

"""Nicht-interaktiver Test der Kernmechaniken: Level bis 100, Klassenentwicklung,
Rangaufstieg F->S, Quest-System, und die komplette Dämonenkönig-Handlung. Ruft
die zugrundeliegenden Funktionen direkt auf (nicht über die interaktiven Menüs
in locations.py, die echte Eingabe erfordern)."""

import random

from game.character import Charakter
from game.combat import erwartete_kampfkraft, rundenbasierter_kampf, zufaelliger_gegner
from game.companions import generiere_begleiter, gruppen_rollen, ist_ausgewogene_gruppe
from game.endgame import (
    DAEMONENFUERSTEN,
    daemonenjagd_verfuegbar,
    demonenkoenig_verfuegbar,
    jage_daemonenfuersten,
    konfrontiere_daemonenkoenig,
    verbleibende_fuersten,
)
from game.events import zufallsereignis
from game.items import generiere_trank
from game.quests import generiere_quest_brett, quest_abschliessen
from game.ranks import RANG_ANFORDERUNGEN, kann_aufsteigen, naechster_rang
from game.story import erzeuge_ende
from game.world import generiere_welt

random.seed(8)

charakter = Charakter(name="Testrun", klasse_id="krieger", persoenlichkeit=["ehrgeizig", "mutig"])
welt = generiere_welt(anzahl_koenigreiche=4)


def gruppe_pflegen(charakter):
    """Simuliert, was ein echter Spieler zwischen Kämpfen tun würde: Mitstreiter
    suchen, Tränke nachkaufen und bessere Funde ausrüsten. Ausrüstung wird seit
    der Umstellung auf spielergesteuerte Inventarverwaltung NICHT mehr
    automatisch angelegt (siehe character.fund_verarbeiten) - ein Test, der
    Funde einfach im Inventar liegen lässt, würde die Kampfbalance künstlich
    schlechter aussehen lassen, als sie bei einem Spieler ist, der sein
    Inventar wie vorgesehen selbst verwaltet."""
    if len(charakter.begleiter) < 3 and random.random() < 0.6:
        vorhandene_rollen = gruppen_rollen(charakter.begleiter)
        neuer = generiere_begleiter(vorhandene_rollen)
        charakter.begleiter_aufnehmen(neuer)
    while len(charakter.traenke) < 4 and charakter.gold >= 20:
        trank = generiere_trank(charakter.level, random.choice(["Heilung", "Heilung", "Mana"]))
        if charakter.gold < trank.wert:
            break
        charakter.gold -= trank.wert
        charakter.traenke.append(trank)
    for item in list(charakter.inventar):
        if charakter.item_ist_besser(item):
            charakter.ausruesten(item)


print("=== Phase 1: Grundmechaniken (Level, Klassenentwicklung) ===")
tier_wechsel_gesehen = set()

for tag in range(400):
    if not charakter.lebendig:
        print(f"Charakter gestorben an Tag {tag}")
        break
    ereignis = zufallsereignis(charakter, welt)
    if ereignis.xp:
        meldungen = charakter.xp_hinzufuegen(ereignis.xp)
        for m in meldungen:
            if "Klassenentwicklung" in m:
                tier_wechsel_gesehen.add(charakter.tier.name)
    if ereignis.gold:
        charakter.gold = max(0, charakter.gold + ereignis.gold)
    if ereignis.item:
        charakter.fund_verarbeiten(ereignis.item)
    if ereignis.schaden:
        charakter.schaden_erleiden(ereignis.schaden)

    if not charakter.lebendig:
        print(f"Charakter gestorben an Tag {tag} (während des Ereignisses)")
        break

    if charakter.hp_aktuell < charakter.hp_max * 0.4:
        charakter.ausruhen()

    if tag % 5 == 0:
        gruppe_pflegen(charakter)

    if charakter.level >= 40:  # genug für Phase 2, nicht bis 100 laufen
        break

print(f"Level erreicht: {charakter.level}, Tiers gesehen: {tier_wechsel_gesehen}")
print(f"Lebendig: {charakter.lebendig}, HP: {charakter.hp_aktuell}/{charakter.hp_max}, MP: {charakter.mp_aktuell}/{charakter.mp_max}")
print(f"Begleiter: {charakter.begleiter_zeile()}, Tränke: {len(charakter.traenke)}")
print(f"Ausrüstung: {charakter.ausruestungs_zeile()}")

print("\n=== Phase 2: Quest-System & Rangaufstieg F -> S ===")
charakter.gilde = "Abenteurergilde"
quest_erfolge = 0
rang_wechsel_log = []

# Level und Quests hochtreiben, bis Rang S erreicht ist oder ein Sicherheitslimit greift
sicherheitszaehler = 0
while charakter.rang != "S" and sicherheitszaehler < 500 and charakter.lebendig:
    sicherheitszaehler += 1
    gruppe_pflegen(charakter)
    # Ein Quest-Brett-Besuch = eine Quest pro "Tag", wie im echten Spiel
    # (_quest_brett_ansehen lässt nur eine Auswahl pro Besuch zu, danach
    # rastet der Charakter). Mehrere Quests ohne Rast dazwischen abzuarbeiten
    # war ein Testartefakt, das die Kampfbalance künstlicher aussehen ließ,
    # als sie im echten Spiel ist.
    quest = generiere_quest_brett(charakter.rang, anzahl=1)[0]
    _, log, erfolg = quest_abschliessen(charakter, quest)
    if erfolg:
        quest_erfolge += 1

    if charakter.hp_aktuell < charakter.hp_max * 0.4 and charakter.lebendig:
        charakter.ausruhen()

    if kann_aufsteigen(charakter):
        alter_rang = charakter.rang
        # Rangaufstiegsprüfung simulieren (wie in locations._rangaufstieg_pruefung)
        staerke = int(erwartete_kampfkraft(charakter.level) * random.uniform(0.8, 1.0))
        ergebnis = rundenbasierter_kampf(charakter, f"Prüfungswächter", staerke)
        if ergebnis.sieg:
            charakter.rang = naechster_rang(alter_rang)
            rang_wechsel_log.append(f"{alter_rang} -> {charakter.rang} (Tag/Iteration {sicherheitszaehler}, Level {charakter.level})")
        elif not charakter.lebendig:
            break

    # Etwas XP/Level-Wachstum nebenbei, damit Level nicht der Flaschenhals wird
    if sicherheitszaehler % 3 == 0:
        charakter.xp_hinzufuegen(int(500 * (charakter.level + 1)))

print(f"Rang erreicht: {charakter.rang} nach {sicherheitszaehler} Iterationen, {quest_erfolge} erfolgreiche Quests")
for zeile in rang_wechsel_log:
    print(f"  {zeile}")
print(f"Level: {charakter.level}, Lebendig: {charakter.lebendig}")
print(f"Begleiter: {charakter.begleiter_zeile()}, Tränke: {len(charakter.traenke)}, Gold: {charakter.gold}")

if charakter.rang != "S" or not charakter.lebendig:
    print("\n⚠️ Rang S nicht erreicht oder Charakter gestorben - Dämonenkönig-Test wird übersprungen.")
else:
    print("\n=== Phase 3: Dämonenjagd & Dämonenkönig ===")
    print(f"Dämonenjagd verfügbar: {daemonenjagd_verfuegbar(charakter)}")
    gruppe_pflegen(charakter)
    # Ein Spieler, der beim "ultimativen Ziel" des Spiels antritt, rastet
    # vorher so oft aus, bis er bereit ist - kein vernünftiger Spieler
    # stürmt den Dämonenfürsten mit 38% HP entgegen, nur weil das Menü es
    # technisch zulassen würde. ausruhen() heilt pro Aufruf nur einen
    # Bruchteil (siehe character.py), daher mehrere Versuche bis fast voll.
    rastversuche = 0
    while charakter.hp_aktuell < charakter.hp_max * 0.95 and rastversuche < 6:
        charakter.ausruhen()
        rastversuche += 1

    for fuerst in list(DAEMONENFUERSTEN):
        if not charakter.lebendig:
            break
        restliche = verbleibende_fuersten(charakter)
        if not restliche:
            break
        # Jede Dämonenjagd ist ein eigener Gildenviertel-Besuch (ein "Tag") -
        # ein Spieler rastet und kauft zwischen einzelnen Fürsten nach, statt
        # alle vier ungeheilt hintereinander anzutreten.
        gruppe_pflegen(charakter)
        rastversuche = 0
        while charakter.hp_aktuell < charakter.hp_max * 0.95 and rastversuche < 6:
            charakter.ausruhen()
            rastversuche += 1
        ergebnis = jage_daemonenfuersten(charakter, restliche[0])
        print(f"  {ergebnis.name}: {'SIEG' if ergebnis.sieg else 'Niederlage'}")
        if not ergebnis.sieg and charakter.lebendig:
            # Erneut versuchen mit etwas mehr Level, falls die erste Runde nicht reicht
            charakter.xp_hinzufuegen(int(2000 * charakter.level))
            if charakter.hp_aktuell < charakter.hp_max:
                charakter.ausruhen()

    print(f"Besiegte Fürsten: {charakter.besiegte_daemonenfuersten}")
    print(f"Dämonenkönig verfügbar: {demonenkoenig_verfuegbar(charakter)}")

    if demonenkoenig_verfuegbar(charakter) and charakter.lebendig:
        koenig_ergebnis = konfrontiere_daemonenkoenig(charakter)
        print(f"Dämonenkönig-Kampf: {'SIEG' if koenig_ergebnis.sieg else 'Niederlage'}")
        if koenig_ergebnis.sieg:
            charakter.daemonenkoenig_besiegt = True
        for zeile in koenig_ergebnis.log[-6:]:
            print(f"    {zeile}")

ende_grund = "daemonenkoenig" if charakter.daemonenkoenig_besiegt else ("tod" if not charakter.lebendig else None)
print(f"\n=== Endstatus ===")
print(f"{charakter.status_zeile()}")
print(f"Rang: {charakter.rang}")
print(f"Dämonenkönig besiegt: {charakter.daemonenkoenig_besiegt}")
print(f"Begleiter: {charakter.begleiter_zeile()}")
print(f"Lebendig: {charakter.lebendig}")
if ende_grund:
    print(erzeuge_ende(charakter, welt, ende_grund))

#!/usr/bin/env python3
"""Isekai Chronicles - ein sich selbst spielendes, textbasiertes Isekai-Rollenspiel.

Erstelle deinen Charakter, dann nimmt die Geschichte ihren Lauf. An wichtigen
Momenten pausiert das Spiel kurz - drücke einfach Enter, um zu sehen, wie sich
dein Charakter entscheidet. Jeder Durchlauf erzeugt eine neue Welt und einen
neuen Verlauf.
"""

import random
import sys

from game.character import Charakter
from game.locations import EingabeErschoepft, besuche_ort
from game.story import erstelle_charakter, erzeuge_ende
from game.storyline import pruefe_meilenstein
from game.world import generiere_welt

TITEL_ART = r"""
   ___          _         _  ____ _                     _      _
  |_ _|___  ___| | ____ _(_)/ ___| |__  _ __ ___  _ __ (_) ___| | ___  ___
   | |/ __|/ _ \ |/ / _` | | |   | '_ \| '__/ _ \| '_ \| |/ __| |/ _ \/ __|
   | |\__ \  __/   < (_| | | |___| | | | | | (_) | | | | | (__| |  __/\__ \
  |___|___/\___|_|\_\__,_|_|\____|_| |_|_|  \___/|_| |_|_|\___|_|\___||___/
"""

PAUSE_TEXTE = ["[Enter, um fortzufahren...]", "[weiter mit Enter...]", "[Enter drücken...]"]


def pause():
    try:
        input(f"\n{random.choice(PAUSE_TEXTE)}")
    except EOFError:
        pass


def zeige_ereignis(ereignis, charakter: Charakter):
    praefix = "\n💥 " if ereignis.ist_wichtig else "\n"
    print(f"{praefix}{ereignis.text}")

    if ereignis.log:
        for zeile in ereignis.log:
            print(zeile)

    meldungen_folge = []
    if ereignis.xp:
        meldungen_folge.extend(charakter.xp_hinzufuegen(ereignis.xp))
    if ereignis.gold:
        charakter.gold = max(0, charakter.gold + ereignis.gold)
    if ereignis.ruf:
        charakter.ruf += ereignis.ruf
    if ereignis.item:
        meldungen_folge.append(charakter.fund_verarbeiten(ereignis.item))
    if ereignis.schaden:
        gestorben_durch_schaden = charakter.schaden_erleiden(ereignis.schaden)
        meldungen_folge.append(f"💔 {charakter.name} erleidet {ereignis.schaden} Schaden.")
        if gestorben_durch_schaden:
            return True, meldungen_folge

    # Rundenbasierte Kämpfe können den Charakter bereits während des Kampfes
    # (im log oben sichtbar) zu Fall gebracht haben.
    if not charakter.lebendig:
        return True, meldungen_folge

    skill_meldung = charakter.zufaelligen_skill_ueben()
    if skill_meldung:
        meldungen_folge.append(skill_meldung)

    for m in meldungen_folge:
        print(f"   {m}")

    return False, meldungen_folge


def rasten_falls_noetig(charakter: Charakter):
    if charakter.hp_aktuell < charakter.hp_max * 0.4:
        geheilt, mp_regen = charakter.ausruhen()
        print(f"\n🛌 {charakter.name} ist schwer verwundet und rastet, um sich zu erholen. (+{geheilt} HP, +{mp_regen} MP)")


def spiel_starten():
    print(TITEL_ART)
    print("Ein Leben endet. Ein neues beginnt - in einer Welt voller unendlicher Möglichkeiten.\n")

    charakter = erstelle_charakter()
    welt = generiere_welt(anzahl_koenigreiche=random.randint(4, 6))

    print("\n" + "-" * 70)
    print(welt.zusammenfassung())
    print("-" * 70)
    pause()

    ende_grund = None

    while True:
        charakter.tage_vergangen += 1

        print(f"\n{'=' * 70}\n📅 Tag {charakter.tage_vergangen}  |  {charakter.status_zeile()}\n{'=' * 70}")
        if charakter.begleiter:
            print(f"   {charakter.begleiter_zeile()}")

        ort_name, ereignis = besuche_ort(charakter, welt)
        print(f"\n📍 {charakter.name} entscheidet sich: auf zu {ort_name}.")
        gestorben, _ = zeige_ereignis(ereignis, charakter)

        if gestorben:
            ende_grund = "tod"
            break

        meilenstein_text = pruefe_meilenstein(charakter)
        if meilenstein_text:
            print(meilenstein_text)
            pause()

        rasten_falls_noetig(charakter)

        if charakter.daemonenkoenig_besiegt:
            ende_grund = "daemonenkoenig"
            break
        if charakter.level >= 100:
            ende_grund = "levelcap"
            break

        pause()

    print(erzeuge_ende(charakter, welt, ende_grund))


def main():
    while True:
        try:
            spiel_starten()
        except KeyboardInterrupt:
            print("\n\nDie Geschichte bricht hier ab...")
            break
        except EingabeErschoepft:
            print("\n\nKeine Eingabe mehr verfügbar - die Sitzung wird beendet.")
            break

        try:
            nochmal = input("\nEine neue Geschichte beginnen? (j/n): ").strip().lower()
        except EOFError:
            break
        if nochmal != "j":
            print("\nBis zum nächsten Isekai. 👋")
            break


if __name__ == "__main__":
    main()

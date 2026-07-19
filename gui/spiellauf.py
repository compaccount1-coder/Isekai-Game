"""Verbindet ein aufgelöstes Ereignis mit der Tagesabschluss-Logik - das
GUI-Gegenstück zu main.py's Schleifenkörper (zeige_ereignis + Tagesende)."""

import random

from game.storyline import pruefe_meilenstein
from game.story import hat_welt_erobert, herrschafts_ereignis, pruefe_pfadwechsel


def verarbeite_ereignis(charakter, ereignis) -> tuple[str, bool]:
    """Wendet die Effekte eines Ereignisses an (wie main.py's zeige_ereignis)
    und gibt (Anzeigetext, gestorben) zurück."""
    zeilen = [ereignis.text]
    if ereignis.log:
        zeilen.extend(ereignis.log)

    meldungen = []
    if ereignis.xp:
        meldungen.extend(charakter.xp_hinzufuegen(ereignis.xp))
    if ereignis.gold:
        charakter.gold = max(0, charakter.gold + ereignis.gold)
    if ereignis.ruf:
        charakter.ruf += ereignis.ruf
    if ereignis.item:
        meldungen.append(charakter.fund_verarbeiten(ereignis.item))

    gestorben = False
    if ereignis.schaden:
        gestorben_durch_schaden = charakter.schaden_erleiden(ereignis.schaden)
        meldungen.append(f"💔 {charakter.name} erleidet {ereignis.schaden} Schaden.")
        if gestorben_durch_schaden:
            gestorben = True
    if not charakter.lebendig:
        gestorben = True

    if not gestorben:
        skill_meldung = charakter.zufaelligen_skill_ueben()
        if skill_meldung:
            meldungen.append(skill_meldung)

    zeilen.extend(meldungen)
    return "\n".join(zeilen), gestorben


def tagesende(charakter, welt) -> tuple[str, str | None]:
    """Tagesabschluss wie in main.py's spiel_starten-Schleife: Story-
    Meilensteine, Pfadwechsel, Herrschaft, Inventarpflege, Rast. Gibt
    (Zusatztext, Ende-Grund oder None) zurück."""
    charakter.tage_vergangen += 1
    zeilen = []

    meilenstein_text = pruefe_meilenstein(charakter)
    if meilenstein_text:
        zeilen.append(meilenstein_text)

    pfadwechsel_text = pruefe_pfadwechsel(charakter, welt)
    if pfadwechsel_text:
        zeilen.append(pfadwechsel_text)

    if charakter.pfad == "Herrscher" and random.random() < 0.4:
        zeilen.append(herrschafts_ereignis(charakter, welt))

    if charakter.tage_vergangen % 4 == 0:
        verkauft, erloes = charakter.inventar_aufraeumen()
        if verkauft:
            zeilen.append(f"💼 {charakter.name} verkauft {verkauft} überzählige Gegenstände für {erloes} Gold.")
        schmiede_meldung = charakter.schmiede_besuchen()
        if schmiede_meldung:
            zeilen.append(schmiede_meldung)

    if charakter.hp_aktuell < charakter.hp_max * 0.4:
        geheilt, mp_regen = charakter.ausruhen()
        zeilen.append(f"🛌 {charakter.name} ist erschöpft und rastet. (+{geheilt} HP, +{mp_regen} MP)")

    ende_grund = None
    if charakter.daemonenkoenig_besiegt:
        ende_grund = "daemonenkoenig"
    elif charakter.level >= 100:
        ende_grund = "levelcap"
    elif hat_welt_erobert(charakter, welt):
        ende_grund = "welteroberung"

    return "\n\n".join(z for z in zeilen if z), ende_grund

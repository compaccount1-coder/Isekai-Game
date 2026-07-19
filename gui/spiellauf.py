"""Verbindet ein aufgelöstes Ereignis mit der Tagesabschluss-Logik - das
GUI-Gegenstück zu main.py's Schleifenkörper (zeige_ereignis + Tagesende)."""

from game.character import MAX_AKTIONEN_PRO_TAG
from game.storyline import pruefe_meilenstein


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


def tagesende(charakter, welt) -> str:
    """Wird nur aufgerufen, wenn ein Ereignis den Tag beendet hat (Schlafen in
    der Taverne, siehe Ereignis.beendet_tag) - erhöht den Tageszähler, füllt
    die täglichen Aktionen wieder auf und prüft Story-Meilensteine. Gibt
    Zusatztext zurück (kann leer sein)."""
    charakter.tage_vergangen += 1
    charakter.aktionen_uebrig = MAX_AKTIONEN_PRO_TAG
    return pruefe_meilenstein(charakter) or ""


def pruefe_spielende(charakter) -> str | None:
    """Das Level-Cap beendet das Spiel bewusst NICHT mehr - einzig der Sieg
    über den Dämonenkönig (oder der Tod) beenden die Geschichte."""
    if charakter.daemonenkoenig_besiegt:
        return "daemonenkoenig"
    return None

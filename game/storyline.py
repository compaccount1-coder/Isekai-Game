"""Die rote Linie der Dämonenkönig-Handlung: feste, einmalige Story-Momente,
die unabhängig von zufälligen Ereignissen bei bestimmten Meilensteinen (Level
oder Rang) ausgelöst werden. Sie geben dem gesamten Spieldurchlauf einen
erkennbaren erzählerischen Bogen - von ersten vagen Vorzeichen bis zum
offenen Ruf zur letzten Schlacht gegen Abraxos."""

from dataclasses import dataclass

from game.endgame import DAEMONENFUERSTEN, DAEMONENKOENIG_NAME


@dataclass
class Meilenstein:
    schluessel: str
    bedingung: callable
    text: str


def _bedingung_level(mindest_level: int):
    return lambda charakter: charakter.level >= mindest_level


def _bedingung_rang(mindest_rang: str):
    from game.ranks import RANG_REIHENFOLGE
    idx = RANG_REIHENFOLGE.index(mindest_rang)
    return lambda charakter: RANG_REIHENFOLGE.index(charakter.rang) >= idx


def _bedingung_erster_fuerst(charakter) -> bool:
    return len(charakter.besiegte_daemonenfuersten) >= 1


def _bedingung_alle_fuersten(charakter) -> bool:
    return len(charakter.besiegte_daemonenfuersten) >= len(DAEMONENFUERSTEN)


MEILENSTEINE: list[Meilenstein] = [
    Meilenstein(
        "vision_level5",
        _bedingung_level(5),
        (
            "\n🌑 In der Nacht sucht dich ein Traum heim, der sich nicht wie einer anfühlt: eine Krone aus "
            "schwarzem Rauch, ein Thron aus erstarrten Schreien, und eine Stimme, uralt und geduldig, die "
            "flüstert: 'Auch du wirst mir gehören, kleiner Wanderer.' Du erwachst schweißgebadet. Niemand, "
            "dem du davon erzählst, kann dir sagen, was es zu bedeuten hat - aber das Gefühl bleibt."
        ),
    ),
    Meilenstein(
        "geruecht_rang_e",
        _bedingung_rang("E"),
        (
            "\n📯 Am Gildenbrett hängt eine neue, ungewöhnlich ernste Notiz: mehrere Außenposten im Süden "
            "melden seit Wochen keine Boten mehr zurück. Der Gildenmeister winkt ab, als du fragst - "
            "'Wahrscheinlich nur Banditen' - doch sein Blick verrät, dass er selbst nicht daran glaubt."
        ),
    ),
    Meilenstein(
        "dorf_ueberfall_rang_d",
        _bedingung_rang("D"),
        (
            "\n🔥 Eine zerlumpte Gestalt erreicht humpelnd die Stadt: das Dorf Aschweiler wurde in der Nacht "
            "von niederen Dämonen überrannt. Du eilst mit anderen Abenteurern zur Hilfe - was ihr vorfindet, "
            "sind keine gewöhnlichen Monster, sondern organisierte, disziplinierte Kreaturen, die auf Befehl "
            "zu handeln scheinen. 'Das waren keine wilden Tiere', murmelt ein Überlebender. 'Die haben auf "
            "etwas gewartet. Auf jemanden.'"
        ),
    ),
    Meilenstein(
        "erste_erwaehnung_rang_c",
        _bedingung_rang("C"),
        (
            f"\n📜 In der Gildenbibliothek stößt du auf eine verstaubte Chronik über die letzte große "
            f"Dämoneninvasion vor Generationen. Ein Name taucht darin immer wieder auf, in Tinte, die "
            f"stellenweise wie unter Zwang gezittert geschrieben wirkt: {DAEMONENKOENIG_NAME}. Die Chronik "
            f"endet abrupt, mitten im Satz. Die Gildenältesten weichen deinen Fragen dazu auffällig aus."
        ),
    ),
    Meilenstein(
        "fuerst_verwuestung_rang_b",
        _bedingung_rang("B"),
        (
            "\n⚔️ Ein erschöpfter Kurier bricht in der Gildenhalle zusammen: eine ganze Grenzregion wurde "
            "binnen weniger Tage verwüstet, angeführt von einer Kreatur, die 'wie ein General aus einem "
            "Alptraum' beschrieben wird. Die Gilde beginnt zum ersten Mal offen von den 'Unterlingen des "
            "Dämonenkönigs' zu sprechen - nicht länger als Gerücht, sondern als Tatsache, der man sich "
            "stellen muss."
        ),
    ),
    Meilenstein(
        "koalition_rang_a",
        _bedingung_rang("A"),
        (
            "\n🛡️ Die großen Gilden der Welt rufen erstmals in ihrer Geschichte gemeinsam alle Abenteurer "
            "vom Rang A aufwärts zusammen: eine Koalition der Verteidiger soll entstehen, um sich auf die "
            "unausweichliche Konfrontation mit Abraxos vorzubereiten. Du spürst, dass sich etwas verändert "
            "hat - du bist nicht mehr nur ein Abenteurer unter vielen. Man erwartet etwas von dir."
        ),
    ),
    Meilenstein(
        "held_rang_s",
        _bedingung_rang("S"),
        (
            "\n👑 Der Gildenmeister persönlich verkündet es vor versammelter Mannschaft: deine Gruppe hat "
            "Rang S erreicht und wird offiziell zur Heldengruppe erhoben - der höchsten Ehre, die die Gilde "
            "zu vergeben hat. 'Ihr seid jetzt die Letzten, die es noch versuchen können', sagt er leise, "
            "als die Feierlichkeiten vorbei sind. 'Die Unterlinge des Dämonenkönigs erwarten euch. Und "
            "danach - er selbst.'"
        ),
    ),
    Meilenstein(
        "erster_fuerst_gefallen",
        _bedingung_erster_fuerst,
        (
            "\n📯 Die Nachricht verbreitet sich wie ein Lauffeuer durch jede Taverne und jedes Gildenhaus "
            "der Welt: zum ersten Mal seit Generationen ist einer der Unterlinge des Dämonenkönigs gefallen "
            "- und zwar durch deine Hand. Für einen Moment scheint die Welt aufzuatmen. Doch tief in dir "
            "weißt du: das war erst der Anfang."
        ),
    ),
    Meilenstein(
        "alle_fuersten_gefallen",
        _bedingung_alle_fuersten,
        (
            f"\n🌌 Mit dem letzten gefallenen Unterling liegt der Weg endlich frei. Keine Ausreden mehr, "
            f"keine Vorboten, keine Zwischenschritte - nur noch {DAEMONENKOENIG_NAME} selbst steht "
            f"zwischen dir und dem Ende dieser Geschichte. In der Gildenhalle wird es still, als du eintrittst. "
            f"Jeder weiß, was als Nächstes kommt."
        ),
    ),
]


def pruefe_meilenstein(charakter) -> str | None:
    """Prüft alle Story-Meilensteine der Reihe nach und gibt den Text des
    ersten noch ungesehenen, erfüllten Meilensteins zurück (und markiert ihn
    als gesehen), oder None, falls gerade keiner ansteht."""
    for meilenstein in MEILENSTEINE:
        if meilenstein.schluessel in charakter.story_gesehen:
            continue
        if meilenstein.bedingung(charakter):
            charakter.story_gesehen.append(meilenstein.schluessel)
            return meilenstein.text
    return None

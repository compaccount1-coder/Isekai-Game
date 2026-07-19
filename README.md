# Isekai Chronicles

Ein textbasiertes, sich selbst spielendes Isekai-Rollenspiel. Du erstellst deinen
Charakter (Name, Klasse) - danach nimmt die Geschichte ihren Lauf. An wichtigen
Momenten pausiert das Spiel kurz und wartet auf Enter, bevor es weitergeht.

Jeder Durchlauf erzeugt eine neue, zufällige Welt (Königreiche, Städte, Gilden)
und einen komplett neuen Verlauf - kein Spiel gleicht dem nächsten.

## Starten

```
python main.py
```

Erfordert nur Python 3.10+ (Standardbibliothek, keine Abhängigkeiten).

## Was passiert im Spiel?

- **Charaktererstellung**: Name eingeben, aus 9 Klassen wählen (Nekromant, Krieger,
  Magier, Paladin, Assassine, Beschwörer, Barde, Waldläufer, Mönch).
- **Level 1-100**: Jede Klasse hat drei Entwicklungsstufen (z.B. Nekromant →
  Totenbeschwörer bei Level 30 → Lich-Lord bei Level 70).
- **Skills**: Jede Klasse hat 6 einzigartige Skills, die mit der Zeit erlernt und
  bis Skill-Level 10 hochtrainiert werden.
- **Ausrüstung**: Waffen, Rüstungen und Accessoires in 5 Seltenheitsstufen
  (Gewöhnlich bis Legendär) werden gefunden, gekauft oder verkauft. Der Charakter
  entscheidet selbstständig, ob ein Fund besser ist als die aktuelle Ausrüstung,
  räumt das Inventar regelmäßig auf und lässt beim Schmied aufwerten.
- **Zwei Pfade**: Der Charakter beginnt als Abenteurer. Je nach Persönlichkeit,
  Ruf und Zufall kann er beschließen, ein eigenes Königreich zu gründen und den
  Herrscher-Pfad einzuschlagen - inklusive Eroberungsfeldzügen gegen andere
  Königreiche, Diplomatie und innerer Unruhe.
- **Zufallsereignisse**: Kämpfe, Dungeons, Dämonen-Invasionen, Schatzfunde,
  Mentoren, Rivalen, Händler, Gildenaufträge, politische Ereignisse, moralische
  Entscheidungen und Konflikte zwischen Fantasy-Völkern (Menschen, Elfen, Zwerge,
  Orks, Drakonier, Dämonen u.a.), bei denen der Charakter Partei ergreifen muss.
- **Enden**: Tod, Level 100 erreicht, oder vollständige Welteroberung als Herrscher.

## Projektstruktur

```
main.py                 Einstiegspunkt, Hauptspielschleife
game/
  character.py           Charakter: Stats, Level, XP, Skills, Ausrüstungsverwaltung
  classes.py              Klassendefinitionen und Entwicklungsstufen
  items.py                Ausrüstungsgenerierung, Schmiede-Upgrades
  races.py                Fantasy-Völker, Dämonen, Dungeons
  world.py                Prozedurale Weltgenerierung (Königreiche, Städte, Gilden)
  events.py               Zufallsereignis-Pools (der inhaltliche Kern)
  combat.py                Kampfauflösung
  story.py                 Charaktererstellung, Pfadwechsel, Herrschaft, Enden
test_mechaniken.py       Nicht-interaktiver Test für Langzeit-Mechaniken
                         (Level 100, Klassenentwicklung, Welteroberung)
```

## Balance-Hinweis

Die Kampfformeln in `combat.py` sind an `Charakter.kampfkraft()` kalibriert
(siehe `erwartete_kampfkraft()`). Wer neue Gegner- oder Encounter-Typen
hinzufügt, sollte sich an dieser Referenzskala orientieren, statt eigene
Stärke-Werte frei zu schätzen - das war die Ursache des ursprünglichen
Balance-Bugs (Gegner wurden mit steigendem Spieler-Level unbesiegbar).

## Erweiterungsideen

- Weitere Klassen oder eine vierte Entwicklungsstufe für Level 90+
- Persistenz (Speichern/Laden) - bisher bewusst weggelassen, da jeder Neustart
  ein neues Erlebnis sein soll
- Mehr Konflikttypen und tiefere Beziehungsverfolgung pro Volk/Königreich
- Ausrüstungssets mit Bonuseffekten bei vollständigen Sets

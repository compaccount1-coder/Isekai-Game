# Isekai Chronicles

Ein deutschsprachiges, regelbasiertes (offline, ohne KI/API) Isekai-Rollenspiel.
Du erstellst deinen Charakter (Name, Klasse) - danach triffst du selbst jede
Entscheidung: wohin du gehst, welche Quests du annimmst, was du ausrüstest.
Das ultimative Ziel: als Rang-S-Heldengruppe den Dämonenkönig besiegen.

Jeder Durchlauf erzeugt eine neue, zufällige Welt (Königreiche, Städte, Gilden)
und einen komplett neuen Verlauf - kein Spiel gleicht dem nächsten.

## Starten

**Text-Version (Terminal):**
```
python main.py
```

**Grafische Version (Pygame-Fenster):**
```
python gui_main.py
```
Erfordert `pip install pygame` für die grafische Version. Die Text-Version
braucht nur die Python-Standardbibliothek. Beide nutzen dieselbe Spiellogik
unter `game/`.

## Was passiert im Spiel?

- **Charaktererstellung**: Name eingeben, aus 11 Klassen wählen (Nekromant,
  Krieger, Magier, Paladin, Assassine, Beschwörer, Barde, Waldläufer, Mönch,
  Kleriker, Alchemist) - jede mit klarer Rolle (Nahkämpfer/Fernkämpfer/
  Unterstützer) für echte Gruppenbalance.
- **Level 1-100**: Jede Klasse hat drei Entwicklungsstufen. Nahkämpfer-Klassen
  (Krieger, Paladin, Mönch) können sich ab Level 30 zusätzlich für einen
  Tank-Spezialisierungspfad entscheiden - mit eigenen Fähigkeiten und echter
  Schadensreduktion für die Gruppe.
- **Skills**: Jede Klasse hat 8 einzigartige Skills, die mit der Zeit erlernt
  und bis Skill-Level 10 hochtrainiert werden.
- **Rundenbasierter Kampf**: Gegner und Bosse setzen benannte, abwechslungsreiche
  Fähigkeiten ein statt eines generischen Angriffs. Begleiter kämpfen sichtbar
  und autonom mit, passend zu ihrer Rolle - Nahkämpfer binden als Tank die
  Aufmerksamkeit des Gegners, Fernkämpfer greifen zusätzlich an, Unterstützer
  heilen die Gruppe.
- **Ausrüstung**: Waffen, Rüstungen und Accessoires in 5 Seltenheitsstufen
  (Gewöhnlich bis Legendär) werden gefunden, gekauft oder verkauft und landen
  im Inventar. Der Spieler entscheidet selbst am Marktplatz, was er ausrüstet,
  verkauft oder beim Schmied verbessern lässt - keine automatische Verwaltung.
- **Abenteurer-Ränge F bis S**: Aufstieg durch Level und abgeschlossene Quests,
  mit einer Rangaufstiegsprüfung als echtem Kampf. Quests skalieren mit dem Rang.
- **Die Dämonenkönig-Handlung**: Ab Rang S öffnet sich die Jagd auf die vier
  Unterlinge des Dämonenkönigs und schließlich auf Abraxos selbst - begleitet
  von festen Story-Meilensteinen (Visionen, Gerüchte, Überfälle) und
  Tavernen-Gerüchten, die mit wachsendem Rang immer bedrohlicher werden.
- **Zufallsereignisse**: Kämpfe, Dungeons, Dämonen-Invasionen, Schatzfunde,
  Mentoren, Rivalen, Händler, Gildenaufträge, politische Ereignisse, moralische
  Entscheidungen und Konflikte zwischen Fantasy-Völkern (Menschen, Elfen, Zwerge,
  Orks, Drakonier, Dämonen u.a.), bei denen der Charakter Partei ergreifen muss.
- **Speicherstand**: Fortschritt wird als JSON gespeichert und kann über
  "Fortsetzen" im Titelbildschirm (GUI) wieder geladen werden.
- **Enden**: Tod, Level 100 erreicht, oder Sieg über den Dämonenkönig.

## Projektstruktur

```
main.py                 Text-Einstiegspunkt (Terminal)
gui_main.py              Grafischer Einstiegspunkt (Pygame-Fenster)
game/
  character.py           Charakter: Stats, Level, XP, Skills, Ausrüstung, Spezialisierung
  classes.py              Klassendefinitionen, Entwicklungsstufen, Tank-Pfade
  items.py                Ausrüstungs-/Tränke-Generierung, Schmiede-Upgrades
  races.py                Fantasy-Völker, Dämonen, Dungeons
  world.py                Prozedurale Weltgenerierung (Königreiche, Städte, Gilden)
  events.py               Zufallsereignis-Pools (der inhaltliche Kern)
  combat.py                Rundenbasierte Kampfauflösung, Gegner-/Begleiter-Aktionen
  quests.py                Quest-Generierung und -Abschluss
  ranks.py                 Abenteurer-Rangsystem F-S
  endgame.py               Dämonenkönig-Handlung (Unterlinge, Endboss)
  storyline.py             Feste Story-Meilensteine (level-/rang-gebunden)
  companions.py            Begleiter-Generierung und Gruppenbalance
  locations.py             Orts-/Menüsystem (Text-Version)
  story.py                 Charaktererstellung, Enden
  savegame.py              JSON-Speicherstand
gui/
  app.py                   Pygame-Hauptschleife
  scenes.py                Alle Bildschirme (Titel, Charaktererstellung, Hub, Orte, Ende)
  orte.py                  Options-Aufbau je Ort für die GUI (nutzt game/locations.py mit)
  spiellauf.py             Tagesabschluss-Logik für die GUI
  widgets.py, theme.py     UI-Bausteine, Farben/Schriften
test_mechaniken.py       Nicht-interaktiver Test für Langzeit-Mechaniken
                         (Level 100, Rang F-S, komplette Dämonenkönig-Handlung)
```

## Balance-Hinweis

Die Kampfformeln in `combat.py` sind an `erwartete_kampfkraft()` kalibriert.
Wer neue Gegner- oder Encounter-Typen hinzufügt, sollte sich an dieser
Referenzskala orientieren, statt eigene Stärke-Werte frei zu schätzen -
`erwartete_kampfkraft()` liegt bewusst ca. 20-25% über der tatsächlichen
Kampfkraft eines Durchschnittscharakters, daher reichen bereits Faktoren nahe
1.0 für eine echte Herausforderung. Multiplikatoren deutlich über 1.0 (wie es
ursprünglich bei der Rangaufstiegsprüfung und den Dämonenfürsten der Fall war)
machen Kämpfe schnell faktisch unbesiegbar.

`test_mechaniken.py` simuliert einen aktiv mitspielenden Charakter (Gruppe
rekrutieren, Tränke nachkaufen, bessere Funde ausrüsten, rechtzeitig rasten)
und sollte nach Balance-Änderungen über mehrere `random.seed()`-Werte laufen,
um Todesraten und Rang-S-Erreichbarkeit zu prüfen.

## Erweiterungsideen

- Echte Hintergrundgrafiken/Portraits für die GUI (aktuell einfarbige Panels)
- Weitere Klassen oder eine vierte Entwicklungsstufe für Level 90+
- Mehr Orts- und NPC-Varianz, wiederkehrende NPCs über einen Spieldurchlauf
- EXE-Packaging (PyInstaller) für die GUI-Version

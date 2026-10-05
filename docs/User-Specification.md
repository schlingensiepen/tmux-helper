# Open-TmuxTabs -- Benutzerspezifikation

**Stand:** 2026-10-05 (Version 2.0.0)
**Status:** Aktuell

---

## 1. Einfuehrung und Kernkonzept

Open-TmuxTabs ist eine professionelle TUI-Anwendung (Terminal User Interface) fuer Windows, die auf dem Textual-Framework basiert. Das Tool dient als persistente Steuerzentrale fuer Entwickler und DevOps-Spezialisten, die regelmaessig mit einer Vielzahl von tmux-Sessions auf verschiedenen Linux-Servern arbeiten.

**Das Problem:** Die manuelle Verwaltung multipler SSH-Verbindungen ist ineffizient. Das Oeffnen zahlreicher Tabs im Windows Terminal, das Anmelden per SSH und das manuelle Anhaengen (attach) an spezifische tmux-Sessions fuehrt zu Zeitverlust und Kontextwechsel-Ermuedung.

**Die Loesung:** Open-TmuxTabs automatisiert diesen Workflow vollstaendig. Die Anwendung bietet eine konsolidierte Uebersicht aller Hosts und deren Remote-Sessions. Sie fungiert als Dauerbetrieb-Plattform, die auch nach dem Starten von Terminal-Tabs aktiv bleibt, um eine kontinuierliche Steuerung der Infrastruktur ohne App-Neustart zu ermoeglichen.

---

## 2. Fokus-Anwendungsfall: KI-Agenten und persistente Umgebungen

In modernen DevOps-Workflows ist die Persistenz von Arbeitsumgebungen entscheidend, insbesondere beim Einsatz von KI-Agenten:

- **KI-Agenten (z. B. Claude Code):** Starten Sie KI-gesteuerte Analyse- oder Build-Tools in einer tmux-Session. Open-TmuxTabs stellt sicher, dass Sie die Verbindung zu diesen Instanzen jederzeit wiederherstellen koennen, waehrend der Kontext und die laufenden Prozesse serverseitig erhalten bleiben.
- **Langlaufende Prozesse:** Ueberwachen Sie Datenbank-Migrationen oder Build-Pipelines auf entfernten Hosts. Die Anwendung verwaltet den Zugriff auf diese Umgebungen nahtlos, waehrend tmux fuer die noetige Stabilitaet gegen Verbindungsabbrueche sorgt.
- **Kontext-Management:** Wechseln Sie zwischen verschiedenen Projekt-Kontexten, indem Sie spezifische Sessions gruppieren und automatisiert in Windows Terminal oeffnen.

### Kernfunktionen

- **Host-Verwaltung:** Beliebig viele SSH-Hosts speichern, mit automatischer Erreichbarkeitspruefung und Farbstatus
- **Session-Uebersicht:** Fuer jeden erreichbaren Host werden die laufenden tmux-Sessions aufgelistet
- **Session-Auswahl:** Der Anwender waehlt gezielt aus, welche bestehenden Sessions er oeffnen moechte
- **Session-Erstellung:** Neue tmux-Sessions koennen direkt aus der Anwendung heraus auf dem Remote-Host angelegt werden
- **Batch-Oeffnung:** Alle gesammelten Sessions (ueber mehrere Hosts hinweg) werden mit einem Klick als Tabs in Windows Terminal geoeffnet
- **Schnellstart:** Alle laufenden Sessions auf allen erreichbaren Hosts mit einem Klick oeffnen -- ohne vorherige Auswahl
- **Direktsession:** Sessions definieren und auf mehrere Hosts gleichzeitig verteilen -- erzeugen wo noetig, oeffnen wo vorhanden
- **Uebersicht:** Alle Sessions ueber alle Hosts in einer einzigen, sortierbaren Tabelle sehen und auswaehlen
- **Dauerbetrieb:** Die Anwendung bleibt nach dem Oeffnen der Tabs aktiv. Der Anwender kann sofort weitere Sessions sammeln und erneut oeffnen, ohne die App neu zu starten.

---

## 3. Hauptfenster -- Aufbau

Das Fenster besteht aus Header (oben), einem Zwei-Spalten-Layout (Mitte) und Footer (unten):

```
┌──────────────────────────────────────────────────────────────┐
│ Open-TmuxTabs                              [de] Deutsch      │
├──────────────────┬───────────────────────────────────────────┤
│ + Neuer Host     │                                           │
│ ──────────────── │        DETAIL-BEREICH                     │
│ root@dev-server  │                                           │
│ jsp@build-corp   │   wechselt je nach Auswahl links          │
│ admin@ci-node    │                                           │
│ >> Oeffnen       │                                           │
│ ──────────────── │                                           │
│ Direktsession    │                                           │
│ Uebersicht       │                                           │
├──────────────────┴───────────────────────────────────────────┤
│ q Beenden  n Neuer Host  o Oeffnen  x Alle oeffnen  ...      │
└──────────────────────────────────────────────────────────────┘
```

> *Die Anwendung nutzt ein effizientes Zwei-Spalten-Layout. Die Host-Liste (links) ist platzoptimiert, waehrend der Detail-Bereich (rechts) die volle funktionale Kontrolle bietet. Hier kann man also host-spezifisch alle Sets detailliert einstellen. Muss man aber nicht. Das Tool startet im Open Bereich und hat dort eine Funktion, mit der alle auf dem entfernten Host gefundenen Sessions mit einem Klick gestartet werden koennen. Beim Starten des Tools ist dieser Knopf bereits vorausgewaehlt. Man hat also die komplette Kontrolle, kann aber auch einfach sofort loslegen.*

### 3.1 Linke Seite: Host-Liste

Eine vertikale Auswahlliste mit einer klaren Zwei-Zonen-Struktur, getrennt durch visuelle Trenner:

**Obere Zone -- Klassischer Workflow:**

1. **"+ Neuer Host"** -- immer der erste Eintrag
2. *(Trenner)*
3. **Gespeicherte Hosts** -- jeder Host als eigene Zeile, farbcodiert
4. **">> Oeffnen"** -- Startansicht, Zusammenfassung und Schnellstart

**Untere Zone -- Fast-Track-Funktionen:**

5. *(Trenner)*
6. **"Direktsession"** -- Sessions auf mehrere Hosts gleichzeitig verteilen
7. **"Uebersicht"** -- alle Sessions in einer sortierbaren Tabelle

**Begruendung der Zwei-Zonen-Struktur:** Die obere Zone bildet den klassischen Host-Workflow ab (Host anlegen → Sessions auswaehlen → oeffnen). Die untere Zone bietet losgeloeste Power-User-Funktionen, die host-uebergreifend arbeiten und keine Verbindung zur Auswahl in der oberen Zone haben.

**Darstellung der Host-Eintraege:**

Alle Host-Eintraege werden auf gleiche Breite gebracht. Der laengste Eintrag bestimmt die Gesamtbreite, wobei bei ihm mindestens die ersten fuenf Zeichen der Domain sichtbar bleiben. Kuerzere Eintraege haben mehr Platz und zeigen entsprechend mehr von ihrer Domain. Ist ein Eintrag kurz genug, wird er vollstaendig angezeigt.

Bei SSH-Config-Aliasen (z. B. `devbox`) wird der tatsaechliche Username per `ssh -G` aufgeloest und vorangestellt, z. B. `root@devbox`.

**Farbcodierung der Host-Eintraege:**

| Farbe | Bedeutung |
|---|---|
| Hellblau | Verbindung wurde noch nicht versucht -- der Host wurde gerade hinzugefuegt oder die App wurde gerade gestartet |
| Hellgruen | Verbindung erfolgreich -- die tmux-Sessions dieses Hosts wurden abgerufen und stehen zur Auswahl bereit |
| Hellrot | Verbindungsversuch fehlgeschlagen -- der Host ist nicht erreichbar (Netzwerk, SSH-Fehler etc.) |

**Loeschen von Hosts:**

Hosts koennen ueber den Loeschen-Button im Detail-Bereich oder die `Entf`-Taste geloescht werden. Vor dem Loeschen erfolgt eine Sicherheitsabfrage.

**Live-Navigation:**

Beim Navigieren mit den Pfeiltasten in der Host-Liste passt sich der Detail-Bereich rechts sofort an. Der Fokus bleibt in der Liste. Erst Enter oder Tab verschiebt den Fokus in den Detail-Bereich.

---

### 3.2 Rechte Seite: Detail-Bereich

Der Inhalt der rechten Seite wechselt je nachdem, welcher Eintrag in der Host-Liste markiert ist. Es gibt **sechs verschiedene Ansichten**.

---

#### 3.2.1 Ansicht: "Neuer Host"

- Eingabefeld mit Label fuer die SSH-Zieladresse (`user@hostname` oder SSH-Config-Alias)
- Button "Host hinzufuegen"
- **Fokus:** Beim Wechsel springt der Cursor automatisch in das Eingabefeld.

**Verhalten nach dem Hinzufuegen:**
1. Der neue Host erscheint in der linken Liste (hellblau = Verbindung noch nicht versucht).
2. Im Hintergrund wird versucht, die Verbindung herzustellen und die tmux-Sessions abzurufen.
3. Je nach Ergebnis wechselt die Farbe auf hellgruen (erreichbar, Sessions abgerufen) oder hellrot (nicht erreichbar).
4. Bei einem SSH-Config-Alias wird der tatsaechliche Username aufgeloest und in der Anzeige ergaenzt.

---

#### 3.2.2 Ansicht: Host (Verbindung fehlgeschlagen)

- Hostname (vollstaendig) und Fehlerstatus mit SSH-Fehlermeldung
- Drei Buttons:
  - **"Erneut verbinden"** (Shortcut `r`) -- startet einen neuen Verbindungsversuch
  - **"Host einrichten"** (Shortcut `s`) -- oeffnet ein interaktives Windows-Terminal-Fenster, das per SSH den Public-Key des Users auf dem Remote-Host deployed
  - **"Loeschen"** -- entfernt den Host aus der Liste (mit Sicherheitsabfrage)

---

#### 3.2.3 Ansicht: Host (Verbindung erfolgreich)

**Oberer Bereich -- Laufende Sessions:**
- Liste aller tmux-Sessions auf dem Host, jeweils mit einer Auswahlbox (`[ ]` / `[x]`)
- Kompakte Darstellung (eine Zeile pro Session)
- Standardmaessig ist **keine** Session ausgewaehlt
- **Fokus:** Beim Wechsel ist die erste Session automatisch fokussiert
- Tastenkuerzel:
  - `t` -- aktuell markierte Session an-/abwaehlen
  - `a` -- alle Sessions an-/abwaehlen
  - `i` -- Auswahl invertieren
  - `j` -- **Sofortstart**: aktuell markierte Session direkt in einem Windows-Terminal-Tab oeffnen
  - `r` -- Reload (Session-Liste vom Host neu abrufen)

**Buttons:**
- **Reload** -- Session-Liste neu abrufen
- **Loeschen** -- Host entfernen (mit Sicherheitsabfrage)

**Unterer Bereich -- Neue Sessions:**
- Mehrzeiliges Eingabefeld, ein Session-Name pro Zeile
- Validierung: Nur `[a-zA-Z0-9_-]+` erlaubt; ungueltige Namen rot, existierende Namen als Warnung
- Echtzeit-Rueckmeldung unter dem Eingabefeld

**Persistenz:** Auswahl und Eingabe bleiben beim Wechsel zu einem anderen Host erhalten.

---

#### 3.2.4 Ansicht: "Oeffnen"

**Dies ist die Startansicht** -- beim Oeffnen der Anwendung steht die Auswahl auf "Oeffnen".

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  [ Alle erkannten Sessions                         ] │
│                                                      │
│  ────────────────────────────────────────────────    │
│                                                      │
│  Zusammenfassung der Auswahl:                        │
│  root@dev-server.example.com:                        │
│    - claude-project (bestehend)                      │
│    - new-feature (neu)                               │
│  Gesamt: 2 Session(s) auf 1 Host(s)                 │
│                                                      │
│  [ Ein WT – Auswahl oeffnen ] [ Pro Host – Auswahl oeffnen ] │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Schnellstart-Button:**

**"Alle erkannten Sessions"** -- Oeffnet saemtliche tmux-Sessions auf allen erreichbaren Hosts, ohne vorherige Auswahl. Dieser Button ist **nie ausgegraut** und **beim Start der Anwendung fokussiert** -- ein Enter genuegt. Sind Hosts noch im Verbindungsaufbau (hellblau), wartet die Anwendung automatisch. Pro Host wird ein eigenes Windows-Terminal-Fenster geoeffnet.

**Auswahl-Buttons:**

- **"Ein WT – Auswahl oeffnen"** -- alle ausgewaehlten Sessions in einem einzigen Windows-Terminal-Fenster
- **"Pro Host – Auswahl oeffnen"** -- pro Host ein eigenes Windows-Terminal-Fenster

Beide sind **ausgegraut**, solange keine Sessions ausgewaehlt und keine neuen Session-Namen eingetragen sind.

**Button-Design-Regel:** Die beiden Buttons stehen **nebeneinander** (nicht untereinander). Der differenzierende Teil ("Ein WT" / "Pro Host") steht am Anfang des Labels, damit bei Platzmangel von rechts gekuerzt werden kann, ohne dass der Unterschied verloren geht. Dieses Muster gilt konsistent fuer alle Ansichten mit zwei Launch-Buttons.

**Verhalten beim Oeffnen (Oeffnen-Ansicht):**

1. Fuer betroffene Hosts werden neue Sessions erstellt.
2. Windows Terminal wird gestartet.
3. **Reset:** Alle Auswahlboxen werden abgewaehlt, alle Eingabefelder geleert. Fuer betroffene Hosts wird ein Reload ausgeloest.
4. Die Anwendung bleibt offen.

---

#### 3.2.5 Ansicht: "Direktsession" (Fast-Track)

**Zweck:** Sessions definieren und auf mehrere Hosts gleichzeitig verteilen. Vorhandene Sessions werden geoeffnet (attach), nicht vorhandene werden erzeugt und dann geoeffnet. Alles in einem Schritt.

**Begruendung als eigene Funktion:** Im klassischen Workflow (3.2.3 + 3.2.4) waehlt der Anwender Sessions pro Host einzeln aus. Die Direktsession-Funktion dreht die Perspektive um: der Anwender definiert einmal eine Liste von Session-Namen und waehlt dann aus, auf welche Hosts diese verteilt werden sollen. Ideal fuer Setups wie "dev + build + sync auf allen drei Servern".

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│  Ziel-Hosts:                                         │
│  ┌────────────────────────────────────────────────┐  │
│  │ [x] root@dev-server.example.com  [GRUEN]       │  │
│  │ [x] jsp@build.corp.example.com   [GRUEN]       │  │
│  │ [ ] admin@ci.lo                  [ROT]          │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  Session-Namen (einer pro Zeile):                    │
│  ┌────────────────────────────────────────────────┐  │
│  │ build                                          │  │
│  │ deploy                                         │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  Zusammenfassung:                                    │
│  - 'build' erzeugen auf root@dev-server (neu)        │
│  - 'build' existiert auf jsp@build (attach)          │
│  - 'deploy' erzeugen auf root@dev-server (neu)       │
│  - 'deploy' erzeugen auf jsp@build (neu)             │
│  Gesamt: 4 Sessions auf 2 Hosts                      │
│                                                      │
│  [ Ein WT – Ausfuehren ] [ Pro Host – Ausfuehren ]  │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Oberer Bereich -- Host-Auswahl:**
- Liste aller gespeicherten Hosts mit Checkboxen und Farbstatus (blau/gruen/rot)
- Rote Hosts koennen angewaehlt werden. Bei "Ausfuehren" wird ein Reconnect-Versuch unternommen; gelingt er, wird deployed, sonst erscheint ein Fehler-Dialog.
- Tastenkuerzel: `t` Toggle, `a` Toggle All, `i` Invert

**Mittlerer Bereich -- Session-Namen:**
- Mehrzeiliges Eingabefeld, ein Name pro Zeile
- Validierung: `[a-zA-Z0-9_-]+`, ungueltige Namen rot
- Keine Blockierung bei Duplikaten -- stattdessen Hinweis im Zusammenfassungsfeld

**Zusammenfassung:**
- Zwischen Eingabefeld und Buttons, aehnlich der Oeffnen-Ansicht
- Listet pro Kombination (Host, Session) auf, ob attach oder erzeugen
- Warnung bei Duplikaten: `'build' existiert bereits auf host1 (attach)`

**Buttons:**
- **"Ein WT – Ausfuehren"** -- alle Sessions in einem WT-Fenster (Shortcut: `j`)
- **"Pro Host – Ausfuehren"** -- pro Host ein eigenes WT-Fenster
- Ausgegraut, wenn keine Hosts ausgewaehlt ODER keine Session-Namen eingetragen

**Verhalten nach dem Ausfuehren:**
- **Kein Reset.** Auswahl und Eingabe bleiben bestehen. Begruendung: Der Anwender arbeitet hier direkt und sammelt nicht ueber mehrere Schritte hinweg. Er will die gleiche Konfiguration ggf. erneut ausfuehren.
- Die Session-Listen der betroffenen Hosts werden intern aktualisiert, sodass beim naechsten Druck bekannt ist, welche Sessions jetzt existieren (attach statt erzeugen).

**Persistenz:** Auswahl und Text bleiben beim Wechsel zu einer anderen Ansicht erhalten. Bei App-Neustart ist alles leer (keine Persistenz ueber Neustarts).

---

#### 3.2.6 Ansicht: "Uebersicht" (Fast-Track)

**Zweck:** Alle laufenden Sessions aller erreichbaren Hosts in einer einzigen, sortierbaren Tabelle anzeigen und direkt daraus operieren -- unabhaengig von den Einzelauswahlen in den Host-Detail-Ansichten.

**Begruendung als eigene Funktion:** Die Host-Detail-Ansicht zeigt immer nur die Sessions eines einzelnen Hosts. Die Uebersicht gibt dem Anwender die "Vogelperspektive" ueber alle Hosts und Sessions gleichzeitig und erlaubt host-uebergreifendes Auswaehlen und Oeffnen.

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  ┌─────┬──────────────────────┬──────────────────┐    │
│  │  ✓  │ Host ▲               │ Session          │    │
│  ├─────┼──────────────────────┼──────────────────┤    │
│  │ [x] │ jsp@build.corp       │ build            │    │
│  │ [ ] │ jsp@build.corp       │ sync             │    │
│  │ [x] │ root@dev-server      │ claude-project   │    │
│  │ [ ] │ root@dev-server      │ monitor          │    │
│  └─────┴──────────────────────┴──────────────────┘    │
│                                                       │
│  [ Ein WT – Auswahl oeffnen ] [ Pro Host – Auswahl oeffnen ] │
│                                                       │
└───────────────────────────────────────────────────────┘
```

**Tabelle:**
- Drei Spalten: Auswahl-Marker, Host, Session
- **Sortierbare Header:** Klick auf einen Spalten-Header sortiert die Tabelle nach dieser Spalte. Standard-Sortierung beim Oeffnen: nach Session-Name.
- Es erscheinen **nur Sessions von erreichbaren Hosts** (hellgruen). Rote Hosts koennen hier nicht angezeigt werden, da keine Session-Daten bekannt sind.

**Leerzustand:** Wenn noch kein Host erreichbar ist (alle blau oder rot), zeigt die Tabelle die Zeile "Warte auf Verbindungen..." und fuellt sich automatisch, sobald Hosts gruen werden.

**Auswahl:**
- Eigener, **disjunkter Auswahl-Pool** -- komplett unabhaengig von den Host-Detail-Auswahlen. Begruendung: Nur die Buttons innerhalb der Uebersicht wirken auf diese Auswahl, und umgekehrt beeinflusst nichts in den Host-Details die Uebersicht.
- Tastenkuerzel: `t` Toggle, `a` Toggle All, `i` Invert, `j` Jump start (aktuelle Zeile sofort oeffnen)

**Buttons:**
- **"Ein WT – Auswahl oeffnen"** -- alle ausgewaehlten Sessions in einem WT-Fenster
- **"Pro Host – Auswahl oeffnen"** -- pro Host ein eigenes WT-Fenster
- Ausgegraut, wenn nichts ausgewaehlt

**Verhalten nach dem Oeffnen:**
- **Kein Reset.** Auswahl bleibt bestehen (analog zu Direktsession).

**Persistenz:** Auswahl bleibt beim Wechsel zu einer anderen Ansicht erhalten. Bei App-Neustart leer.

---

## 4. Verhalten beim Start

1. Gespeicherte Hosts werden aus der Persistenzdatei geladen und in der linken Liste angezeigt (alle hellblau = Verbindung noch nicht versucht).
2. Fuer jeden Host wird im Hintergrund eine Verbindung hergestellt und die Session-Liste abgerufen.
3. Je nach Ergebnis wechselt die Farbe auf hellgruen (erreichbar) oder hellrot (nicht erreichbar).
4. **Die Auswahl steht auf "Oeffnen"** -- der Anwender sieht sofort den Schnellstart-Button (fokussiert, Enter genuegt) und kann mit einem Klick alle laufenden Sessions oeffnen (der Button wartet automatisch auf die noch laufenden Verbindungsversuche). **Falls keine Hosts gespeichert sind**, steht die Auswahl auf **"Neuer Host"** mit Fokus auf dem Eingabefeld, sodass der Anwender sofort tippen kann.

---

## 5. Host-Persistenz

Die Host-Liste wird zwischen App-Neustarts gespeichert. Speicherort: `%APPDATA%\Open-TmuxTabs\hosts.json`.

Gespeichert wird:
- SSH-Zieladresse (Original-Eingabe)
- Aufgeloester Anzeigename
- Zeitpunkt der letzten Nutzung
- Anzahl der Nutzungen

**Nicht persistiert** werden alle Laufzeit-Daten: Verbindungsstatus, Session-Listen, Auswahlen in allen Ansichten, Eingabefeld-Inhalte.

Hosts werden **nicht** automatisch geloescht, wenn eine Verbindung fehlschlaegt. Das Loeschen erfolgt ausschliesslich manuell.

---

## 6. Plattform und Voraussetzungen

Open-TmuxTabs ist ein **reines Windows-Tool**.

| Voraussetzung | Beschreibung |
|---|---|
| Python 3.10+ | Nur fuer das Wheel (Start per `pipx`); die eigenstaendige `open-tmux-tabs.exe` braucht kein Python |
| Windows Terminal (`wt.exe`) | Zum Oeffnen der Session-Tabs |
| SSH-Client | OpenSSH (in Windows 10+ integriert) |
| tmux | Auf den entfernten Hosts installiert |

---

## 7. SSH-Kommunikation

Fuer jeden Host wird ein einzelner SSH-Aufruf mit einem gebatchten Remote-Skript abgesetzt. Dieses Skript:
- Stellt sicher, dass eine tmux-Grundkonfiguration vorhanden ist (`mouse on`, `history-limit 10000`)
- Erstellt angeforderte neue Sessions
- Listet alle laufenden Sessions auf

Die Ergebnisse werden ueber ein einfaches Zeilenprotokoll zurueckgegeben und lokal geparst.

---

## 8. Sprachwahl und Oberflaechen-Elemente

### Header-Leiste

Am oberen Fensterrand zeigt eine schmale Header-Leiste:
- Links: der Anwendungs-Titel (`Open-TmuxTabs`)
- Rechts: die aktuell aktive Sprache im Format `[de] Deutsch`

### Sprachwechsel

Ueber den globalen Shortcut `l` (Language) oeffnet sich ein modaler Dialog mit einer Auswahlliste (Einzelauswahl). Die verfuegbaren Sprachen werden automatisch aus den mitgelieferten Uebersetzungen ermittelt. Solange keine Sprache gewaehlt wurde, startet die Anwendung in der Sprache des Systems (Umgebungsvariablen `LANG`/`LC_ALL` bzw. System-Locale), sonst auf Englisch. Nach OK fragt ein Bestaetigungsdialog "Sprache geaendert zu [xx]. Jetzt neu starten?" Ja/Nein. Bei Ja startet die App sofort neu.

### Konfigurationsdatei

Benutzer-Einstellungen werden in `%APPDATA%\Open-TmuxTabs\config.json` gespeichert, separat von der Host-Liste.

---

## 9. Windows-Terminal-Start

Jede ausgewaehlte Session wird als eigener Tab in Windows Terminal geoeffnet. Der Tab-Titel hat das Format `session@host`. Jeder Tab fuehrt `ssh -t host "tmux attach-session -t session"` aus.

Bei Ueberschreitung der Kommandozeilenlaenge (30.000 Zeichen) werden die Tabs automatisch auf mehrere Windows-Terminal-Fenster aufgeteilt.

### Button-Label-Konvention

Ueberall wo es zwei Launch-Buttons gibt, folgen diese dem gleichen Muster:

| Button 1 | Button 2 |
|---|---|
| **Ein WT** – <Aktion> | **Pro Host** – <Aktion> |

Der differenzierende Teil steht **am Anfang**, sodass bei Platzmangel von rechts gekuerzt werden kann, ohne dass der Unterschied zwischen den Buttons verloren geht (TCSS `text-overflow: ellipsis`). Die Buttons stehen **nebeneinander**.

---

## 10. Zusammenfassung der Tastenkuerzel

**Prinzip:** Alle Tastenkuerzel sind **sprachunabhaengig** -- die Tasten bleiben konstant, nur die Beschreibung im Footer wird uebersetzt. Kontextabhaengige Kuerzel erscheinen im Footer nur in der passenden Ansicht.

### Globale Shortcuts

| Taste | Aktion (EN) | Beschreibung |
|---|---|---|
| `q` | Quit | Anwendung beenden |
| `n` | New host | Sprung zum "Neuer Host"-Eintrag, Fokus auf Eingabefeld |
| `o` | Open | Sprung zum "Oeffnen"-Eintrag |
| `x` | Open all | "Alle erkannten Sessions" sofort ausloesen |
| `+` | Direct session | Sprung zur "Direktsession"-Ansicht |
| `-` | Show all | Sprung zur "Uebersicht"-Ansicht |
| `l` | Language | Sprachwahl-Dialog oeffnen |
| `Entf` | Delete host | Markierten Host loeschen (mit Sicherheitsabfrage) |

### Session-Liste (in Host-Detail, 3.2.3)

| Taste | Aktion | Beschreibung |
|---|---|---|
| `t` | Toggle | Markierte Session an-/abwaehlen |
| `a` | Toggle All | Alle Sessions an-/abwaehlen |
| `i` | Invert | Auswahl invertieren |
| `j` | Jump start | Markierte Session sofort in einem WT-Tab oeffnen |
| `r` | Reload | Session-Liste vom Host neu abrufen |

### Fehlgeschlagener Host (3.2.2)

| Taste | Aktion | Beschreibung |
|---|---|---|
| `r` | Reconnect | Neuer Verbindungsversuch |
| `s` | Set up host | Interaktives WT-Fenster zum Deployen des SSH-Schluessels |

### Direktsession (3.2.5)

| Taste | Aktion | Beschreibung |
|---|---|---|
| `t` | Toggle | Markierten Host an-/abwaehlen (wenn Fokus in Host-Liste) |
| `a` | Toggle All | Alle Hosts an-/abwaehlen |
| `i` | Invert | Host-Auswahl invertieren |
| `j` | Execute | "Ein WT – Ausfuehren" sofort ausloesen |

### Uebersicht (3.2.6)

| Taste | Aktion | Beschreibung |
|---|---|---|
| `t` | Toggle | Markierte Zeile an-/abwaehlen |
| `a` | Toggle All | Alle Zeilen an-/abwaehlen |
| `i` | Invert | Auswahl invertieren |
| `j` | Jump start | Markierte Session sofort in einem WT-Tab oeffnen |

---

## 11. Bezugswege

Die Anwendung gibt es auf zwei Wegen — als eigenstaendige Datei fuer Anwender ohne Python und als Wheel fuer Umgebungen mit Python:

- **`open-tmux-tabs.exe`** — eine einzelne Datei ohne weitere Abhaengigkeiten (ausser Windows Terminal und OpenSSH). Start z.B. direkt aus PowerShell:
  `irm https://github.com/schlingensiepen/tmux-helper/releases/latest/download/open-tmux-tabs.exe -OutFile "$env:TEMP\open-tmux-tabs.exe"; Start-Process "$env:TEMP\open-tmux-tabs.exe" -Wait`
- **Python-Wheel** — fuer Umgebungen mit Python und pipx, z.B. der Start von einer Netzwerk-Freigabe per `pipx run --spec <wheel> open-tmux-tabs`.

Beide stehen auf der Release-Seite des Produkt-Repos `schlingensiepen/tmux-helper`.

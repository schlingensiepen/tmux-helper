# Benutzerhandbuch -- Open-TmuxTabs

**Version:** 2.0.0
**Stand:** 2026-10-05

---

## Vorwort

Open-TmuxTabs ist eine professionelle TUI-Anwendung (Terminal User Interface) fuer Windows, entwickelt auf Basis des Textual-Frameworks. Sie dient als zentrale, dauerhaft laufende Steuerzentrale fuer die Verwaltung von tmux-Sessions auf entfernten Linux-Systemen.

Dieses Handbuch richtet sich an Entwickler und DevOps-Spezialisten, die mit vielen parallel laufenden Remote-Sessions arbeiten -- sei es fuer KI-Agenten, Build-Pipelines, Monitoring, Datenbank-Wartung oder klassische Entwicklungsumgebungen.

### Wie dieses Handbuch zu lesen ist

- **Schnelleinsteiger** lesen **Teil I** (Kapitel 1-4) und koennen danach produktiv arbeiten.
- **Vollstaendige Lektuere** fuer Power-User: Teil II und III vermitteln das komplette mentale Modell.
- **Nachschlagen:** Teil IV und der Anhang sind als Referenz aufgebaut. Das Shortcut-Cheatsheet im Anhang ist zum Ausdrucken gedacht.

---

# TEIL I -- SCHNELLEINSTIEG

## 1. Was ist Open-TmuxTabs?

### 1.1 Das Problem: Reibung beim Verwalten vieler Remote-Sessions

Wer auf entfernten Linux-Servern arbeitet, nutzt oft mehrere tmux-Sessions parallel -- eine fuer den Build, eine fuer den Editor, eine fuer das Monitoring, eine fuer den KI-Agenten. Um sich an diese Sessions anzuhaengen, muesste man fuer jede einzeln ein Terminal oeffnen, `ssh user@host` eintippen und `tmux attach -t <name>` ausfuehren. Bei zehn Sessions auf drei Hosts sind das dreissig manuelle Schritte -- jedes Mal. Das kostet Zeit und bringt einen aus dem Fluss.

### 1.2 Die Loesung: Eine Steuerzentrale

Open-TmuxTabs automatisiert diesen Workflow vollstaendig ueber das Windows Terminal und den systemeigenen OpenSSH-Client. Sie sehen auf einen Blick alle Ihre Hosts und deren laufende tmux-Sessions, waehlen aus, was Sie oeffnen moechten, und die Anwendung erzeugt automatisch die passenden Tabs in Windows Terminal -- jeder Tab eine SSH-Verbindung mit angehaengter tmux-Session.

Die Anwendung bleibt nach dem Oeffnen der Tabs **aktiv**. Sie koennen sofort weitere Sessions sammeln und erneut oeffnen, ohne die App neu zu starten. Das macht sie zu einer "Dauerbetrieb-Plattform" und einem Produktivitaets-Multiplikator fuer Power-User.

### 1.3 Die Hauptanwendungsfaelle

Open-TmuxTabs ist nicht auf einen einzigen Use Case festgelegt. Ueberall, wo persistente Remote-Umgebungen gebraucht werden, spielt sie ihre Staerken aus:

- **KI-Agenten (z. B. Claude Code):** Starten Sie KI-gesteuerte Analyse-, Code- oder Build-Tools in einer tmux-Session. Open-TmuxTabs stellt sicher, dass Sie die Verbindung zu diesen Instanzen jederzeit wiederherstellen koennen, waehrend Kontext und laufende Prozesse serverseitig erhalten bleiben.
- **Langlaufende Builds und Tests:** CI-lokale Reproduktionen, Integrationstest-Laeufe, Performance-Benchmarks. tmux haelt sie am Leben, auch wenn Ihr Laptop den Netzwerk-Zustand wechselt.
- **Datenbank-Migrationen und Wartung:** Langlaufende Migrationsskripte, Dump- und Restore-Prozesse, Replikations-Setup -- Sie starten sie einmal und kehren bei Bedarf zurueck.
- **Integrations- und Monitoring-Prozesse:** `top`, `tail -f`, `htop`, benutzerdefinierte Dashboards. Einmal eingerichtet, jederzeit einsehbar.
- **Kontext-Management fuer Projekte:** Gruppieren Sie Sessions pro Projekt und oeffnen Sie alle Tabs eines Projekts mit einem Klick.

---

## 2. Voraussetzungen und Installation

### 2.1 System-Anforderungen

| Komponente | Voraussetzung |
|---|---|
| **Betriebssystem** | Windows (reines Windows-Tool) |
| **Python** | Version 3.10 oder neuer -- nur fuer Wheel oder Quelltext, nicht fuer die `.exe` |
| **Terminal** | Windows Terminal (`wt.exe`) |
| **SSH-Client** | OpenSSH |
| **Remote-Host** | tmux (auf den Ziel-Systemen installiert) |

> **Hinweis:** Der **OpenSSH-Client ist in Windows 10 und 11 bereits enthalten** -- Sie muessen nichts zusaetzlich installieren. Auf Kommandozeile sollte `ssh -V` funktionieren.

### 2.2 Installation

**Am einfachsten -- ohne Python:** die eigenstaendige `open-tmux-tabs.exe` aus dem neuesten Release laden und starten, z.B. in PowerShell:

```powershell
irm https://github.com/schlingensiepen/tmux-helper/releases/latest/download/open-tmux-tabs.exe -OutFile "$env:TEMP\open-tmux-tabs.exe"; Start-Process "$env:TEMP\open-tmux-tabs.exe" -Wait
```

Wer die Datei behalten moechte, legt sie an einen beliebigen Ort und startet sie von dort.

**Mit Python 3.10+ und pipx:** das Wheel aus dem Release verwenden:

```powershell
pipx run --spec open_tmux_tabs-2.0.0-py3-none-any.whl open-tmux-tabs
```

**Aus dem Quelltext** (Entwicklung):

```powershell
git clone https://github.com/schlingensiepen/tmux-helper.git
cd tmux-helper
pip install -e .
```

Die Anwendung wird danach ueber den Befehl `open-tmux-tabs` gestartet.

> **Hinweis bei Netzlaufwerken:** Wenn das Projekt auf einem Netzlaufwerk liegt, kann Python dort kein Virtual Environment anlegen. Verwenden Sie in diesem Fall **Conda/Miniconda** (das Environment wird zentral gespeichert) oder kopieren Sie das Projekt auf ein lokales Laufwerk.

### 2.3 Erster Start -- was man sieht

Nach dem Start sehen Sie das Hauptfenster mit drei Bereichen:
1. Oben eine schmale Header-Leiste mit Titel und aktiver Sprache (z. B. `[de] Deutsch` rechts)
2. Links eine Host-Liste (beim ersten Start enthaelt sie nur "+ Neuer Host" und ">> Öffnen")
3. Rechts der Detail-Bereich, der sich automatisch an die Auswahl links anpasst

Ohne gespeicherte Hosts steht die Auswahl automatisch auf "+ Neuer Host", und der Cursor wartet im Eingabefeld.

---

## 3. Der schnellste Weg zum Ziel

### 3.1 Das Versprechen: App starten, Enter druecken, fertig

Wenn Sie bereits Hosts gespeichert haben, laeuft der Workflow so:

1. `open-tmux-tabs` starten
2. Die Auswahl steht automatisch auf **">> Öffnen"**
3. Im Detail-Bereich rechts ist der Knopf **"Alle erkannten Sessions"** bereits fokussiert
4. **Enter** druecken

Fertig. Alle tmux-Sessions auf allen erreichbaren Hosts oeffnen sich als Tabs in Windows-Terminal-Fenstern -- ein Fenster pro Host.

### 3.2 Der Schnellstart-Button im Detail

Der Knopf **"Alle erkannten Sessions"** (in der englischen UI: *Open all detected sessions*) ist der Kern des Schnellstart-Workflows. Er hat drei besondere Eigenschaften:

- **Er ist nie ausgegraut** -- funktioniert also auch, wenn Sie noch gar nichts ausgewaehlt haben.
- **Er wartet automatisch**, falls einzelne Host-Verbindungen zum Klickzeitpunkt noch im Aufbau sind (hellblaue Eintraege in der Liste). Sie sehen dann die Meldung "Warte auf ausstehende Verbindungen...".
- **Er oeffnet pro Host ein eigenes Windows-Terminal-Fenster** mit einem Tab pro laufender Session.

### 3.3 Was, wenn Sie noch keine Hosts haben?

Beim allerersten Start ist die Liste leer. Die Auswahl steht automatisch auf **"+ Neuer Host"** mit Fokus im Eingabefeld -- Sie koennen sofort lostippen. Kapitel 4 fuehrt Sie durch diesen Vorgang.

---

## 4. Ein neuer Host in 30 Sekunden

### 4.1 Navigation

Falls Sie bereits Hosts gespeichert haben und auf "+ Neuer Host" springen wollen, druecken Sie den globalen Shortcut **`n`**. Das markiert "+ Neuer Host" links und setzt den Fokus auf das Eingabefeld rechts.

### 4.2 SSH-Ziel eintragen

Im Feld **"SSH-Ziel (user@host oder Alias):"** geben Sie Ihr Ziel ein. Zwei Formate sind moeglich:

| Eingabe | Wirkung |
|---|---|
| `root@dev-server.example.com` | Direkte SSH-Zieladresse |
| `devbox` | SSH-Config-Alias aus Ihrer `~/.ssh/config` |

Bei Verwendung eines Alias wird der tatsaechliche Benutzername automatisch per `ssh -G <alias>` aufgeloest und in der Anzeige ergaenzt.

Bestaetigen Sie mit **Enter** oder klicken Sie auf den Button **"Host hinzufügen"**.

### 4.3 Was passiert im Hintergrund

Sobald Sie bestaetigen, erscheint der neue Host in der linken Liste -- zunaechst **hellblau** (Verbindung wird versucht). Im Hintergrund laeuft:

1. Ein SSH-Aufruf, der die tmux-Grundkonfiguration deployed (einmalig pro Host)
2. Ein `tmux list-sessions` zum Abruf der laufenden Sessions
3. Der Eintrag wechselt die Farbe:
   - **Hellgruen**: erreichbar, Sessions abgerufen
   - **Hellrot**: nicht erreichbar (Netzwerk, Key fehlt, ...)

### 4.4 Wenn der Schluessel noch nicht deployed ist

Wird der Host hellrot (typischerweise *Permission denied*), fehlt oft nur der SSH-Public-Key auf dem Remote-Host. In der Detail-Ansicht des fehlgeschlagenen Hosts gibt es dafuer den Button **"Host einrichten"**. Er oeffnet ein interaktives Windows-Terminal-Fenster, das den Public-Key aus Ihrem Ordner `%USERPROFILE%\.ssh\` per SSH an den Remote-Host uebertraegt und in `~/.ssh/authorized_keys` einfuegt. Da SSH bei dieser ersten Verbindung nach dem Passwort fragt, ist dafuer ein echtes interaktives Terminal noetig -- genau das macht "Host einrichten".

Nach dem Deployen wechseln Sie mit **"Erneut verbinden"** in der Detail-Ansicht wieder auf hellgruen.

---

# TEIL II -- AUFBAU DER ANWENDUNG

## 5. Das Hauptfenster

### 5.1 Das Zwei-Spalten-Layout

> *Die Anwendung nutzt ein effizientes Zwei-Spalten-Layout. Die Host-Liste (links) ist platzoptimiert, waehrend der Detail-Bereich (rechts) die volle funktionale Kontrolle bietet. Hier kann man also host-spezifisch alle Sets detailliert einstellen. Muss man aber nicht. Das Tool startet im Open Bereich und hat dort eine Funktion, mit der alle auf dem entfernten Host gefundenen Sessions mit einem Klick gestartet werden koennen. Beim Starten des Tools ist dieser Knopf bereits vorausgewaehlt. Man hat also die komplette Kontrolle, kann aber auch einfach sofort loslegen.*

### 5.2 Der Header (oben)

Am oberen Rand zeigt eine schmale Leiste:
- **Links**: den Anwendungstitel `Open-TmuxTabs`
- **Rechts**: die aktuell aktive Sprache im Format `[de] Deutsch`

Die Sprache laesst sich jederzeit mit dem globalen Shortcut **`l`** wechseln (siehe Kapitel 13).

### 5.3 Die Host-Liste (links)

Die Host-Liste hat eine **Zwei-Zonen-Struktur** mit visuellen Trennlinien:

**Obere Zone** (klassischer Workflow):
1. **"+ Neuer Host"** -- immer der erste Eintrag
2. _(Trennlinie)_
3. **Ihre gespeicherten Hosts** -- farbcodiert nach Verbindungsstatus
4. **">> Öffnen"** -- Startansicht

**Untere Zone** (Fast-Track-Funktionen):
5. _(Trennlinie)_
6. **"Direktsession"** -- Sessions definieren und auf mehrere Hosts verteilen
7. **"Übersicht"** -- sortierbare Gesamttabelle aller Sessions

Die obere Zone bildet den normalen "sammeln und oeffnen"-Workflow ab, die untere Zone bietet schnelle Direktzugriffe, die unabhaengig davon funktionieren.

Die Liste passt ihre Breite automatisch dem laengsten Eintrag an. Ab einer gewissen Laenge werden Domains gekuerzt, wobei **immer mindestens die ersten fuenf Zeichen** sichtbar bleiben, damit Sie Hosts auch nach Kuerzung unterscheiden koennen.

### 5.4 Der Detail-Bereich (rechts)

Der Detail-Bereich passt sich dynamisch an die Auswahl in der Host-Liste an. Es gibt **sechs verschiedene Ansichten**, die in Kapitel 7 im Detail beschrieben sind.

### 5.5 Der Footer (unten)

Der Footer zeigt die aktuell aktiven Tastenkuerzel. Kontextabhaengige Shortcuts (z. B. `t` fuer "Umschalten") erscheinen nur in der passenden Ansicht. Globale Shortcuts wie `q` (Beenden) oder `n` (Neuer Host) sind immer sichtbar.

### 5.6 ASCII-Uebersicht

```
┌──────────────────────────────────────────────────────────────────┐
│ Open-TmuxTabs                                  [de] Deutsch      │ Header
├──────────────────┬───────────────────────────────────────────────┤
│ + Neuer Host     │                                               │
│ ────────────     │        DETAIL-BEREICH                         │
│ root@dev-server  │                                               │
│ jsp@build-corp   │   wechselt je nach Auswahl links:             │
│ admin@ci-node    │   - Formular "Neuer Host"                     │
│ >> Oeffnen       │   - Session-Liste (Host verbunden)            │
│ ────────────     │   - Fehler-Ansicht (Host rot)                 │
│ Direktsession    │   - Open-Ansicht (Zusammenfassung)            │
│ Uebersicht       │   - Direktsession (Multi-Host-Deployment)    │
│                  │   - Uebersicht (sortierbare Gesamttabelle)    │
├──────────────────┴───────────────────────────────────────────────┤
│ q Beenden  n Neu  o Oeffnen  x Alle  + Direkt  - Uebersicht     │ Footer
└──────────────────────────────────────────────────────────────────┘
```

---

## 6. Die Host-Liste im Detail

### 6.1 Die festen Eintraege

| Eintrag | Zone | Zweck |
|---|---|---|
| **"+ Neuer Host"** | Oben | Oeffnet rechts das Formular zum Hinzufuegen eines neuen SSH-Ziels. |
| **Gespeicherte Hosts** | Oben | Jeder Host als Zeile, farbcodiert nach Verbindungsstatus. |
| **">> Öffnen"** | Oben | Die Startansicht mit Schnellstart-Button und Auswahl-Zusammenfassung. |
| **"Direktsession"** | Unten | Sessions auf mehrere Hosts gleichzeitig verteilen (Shortcut: `+`). |
| **"Übersicht"** | Unten | Sortierbare Gesamttabelle aller Sessions aller Hosts (Shortcut: `-`). |

### 6.2 Farbcodierung des Verbindungs-Status

Jeder Host-Eintrag ist farblich hinterlegt, um seinen Verbindungsstatus auf einen Blick erkennbar zu machen:

| Farbe | Bedeutung |
|---|---|
| **Hellblau** | Verbindung wurde noch nicht versucht oder laeuft gerade (asynchron im Hintergrund) |
| **Hellgruen** | Verbindung erfolgreich -- tmux-Sessions wurden abgerufen und stehen zur Auswahl bereit |
| **Hellrot** | Verbindungsversuch fehlgeschlagen -- Netzwerk, SSH-Fehler oder Authentifizierungsproblem |

### 6.3 Dynamische Breitenberechnung

Die Liste ist so breit wie noetig, aber nicht breiter. Wenn alle Host-Namen komplett in die Liste passen, werden sie vollstaendig angezeigt. Wenn nicht, wird gekuerzt -- aber **immer so, dass die ersten fuenf Zeichen der Domain sichtbar bleiben**, damit `root@dev-server.example.com` und `root@dev-server.internal.corp` nicht zu `root@dev-server` verschmelzen und verwechselbar werden.

Sollte ein extrem langer Host-Name auch mit dieser Mindestgarantie nicht passen, waechst die Liste entsprechend.

### 6.4 Live-Navigation mit Pfeiltasten

Wenn Sie mit den Pfeiltasten **hoch/runter** durch die Liste navigieren, passt sich der **Detail-Bereich rechts sofort an**. Sie sehen also im Vorbeiscrollen die jeweiligen Host-Details, Session-Listen oder Fehler-Ansichten.

Wichtig: Der **Fokus bleibt in der Liste**. Erst wenn Sie **Enter** oder **Tab** druecken, wechselt der tatsaechliche Fokus in den Detail-Bereich rechts, und Sie koennen dort interagieren. Mit **Shift+Tab** kommen Sie zurueck in die Liste.

---

## 7. Der Detail-Bereich: die sechs Ansichten

### 7.1 Ansicht "Neuer Host"

```
┌─────────────────────────────────────┐
│  SSH-Ziel (user@host oder Alias):   │
│  ┌────────────────────────────┐     │
│  │                            │     │
│  └────────────────────────────┘     │
│                                     │
│  [ Host hinzufügen ]                │
└─────────────────────────────────────┘
```

Wird angezeigt, wenn **"+ Neuer Host"** markiert ist. Besteht aus einem Eingabefeld mit Label und einem Button.

**Auto-Fokus:** Beim Wechsel zu dieser Ansicht springt der Cursor automatisch in das Eingabefeld, sodass Sie sofort tippen koennen.

### 7.2 Ansicht Host (Verbindung erfolgreich)

```
┌───────────────────────────────────────────────┐
│  root@dev-server.example.com   [ Neu laden ]  │
│                                [ Löschen   ]  │
│                                               │
│  Laufende Sessions:                           │
│  ┌─────────────────────────────────────────┐  │
│  │ [ ] claude-project                      │  │
│  │ [ ] build                               │  │
│  │ [ ] sync-all                            │  │
│  │ [ ] monitor                             │  │
│  └─────────────────────────────────────────┘  │
│  Toggle: [t]   Alle: [a]   Invertieren: [i]   │
│                                               │
│  Neue Sessions (ein Name pro Zeile):          │
│  ┌─────────────────────────────────────────┐  │
│  │                                         │  │
│  │                                         │  │
│  └─────────────────────────────────────────┘  │
└───────────────────────────────────────────────┘
```

Wird angezeigt, wenn ein **hellgruen** markierter Host selektiert ist. Der Bereich hat drei Teile:

**1. Kopfzeile** -- Hostname, Reload-Button (aktualisiert die Session-Liste vom Host), Loeschen-Button.

**2. Session-Liste** -- Liste aller aktuell auf dem Host laufenden tmux-Sessions mit Auswahlboxen. Die Navigation erfolgt mit den Pfeiltasten:
- `t` schaltet die **aktuell markierte** Session um (Toggle)
- `a` schaltet **alle** Sessions um (Toggle All)
- `i` invertiert die Auswahl (Invert)
- **Space** macht dasselbe wie `t`
- `j` (Jump start) startet die aktuell markierte Session **sofort** in einem eigenen Terminal-Tab -- ohne Auswahl-Umweg (siehe Kapitel 10)

**3. Neue-Sessions-Eingabefeld** -- mehrzeiliges Textfeld zum Anlegen neuer Sessions. Pro Zeile ein Name. Validierung in Echtzeit:
- Nur `a-z`, `A-Z`, `0-9`, `_` und `-` erlaubt
- Warnung, wenn der Name bereits existiert

**Persistenz:** Wenn Sie zu einem anderen Host wechseln und spaeter zurueckkehren, sind **Ihre Auswahl und Ihre Eingaben noch da**. So koennen Sie ueber mehrere Hosts hinweg "sammeln" und dann in einem Rutsch oeffnen.

### 7.3 Ansicht Host (Verbindung fehlgeschlagen)

```
┌───────────────────────────────────────────┐
│  root@dev-server.example.com              │
│  Status: Verbindung fehlgeschlagen        │
│  (Connection refused)                     │
│                                           │
│  [ Erneut verbinden ] [ Host einrichten ] │
│  [ Löschen ]                              │
└───────────────────────────────────────────┘
```

Wird bei **hellrot** markierten Hosts angezeigt. Drei Buttons:

- **"Erneut verbinden"** -- startet einen neuen Verbindungsversuch (Shortcut: `r`)
- **"Host einrichten"** -- oeffnet ein interaktives Windows-Terminal-Fenster, in dem per SSH der Public-Key auf den Remote-Host uebertragen wird (Shortcut: `s`)
- **"Löschen"** -- entfernt den Host aus der Liste, mit Sicherheitsabfrage

### 7.4 Ansicht "Öffnen"

```
┌───────────────────────────────────────────────┐
│                                               │
│  [ Alle erkannten Sessions                  ] │
│                                               │
│  ─────────────────────────────────────────    │
│                                               │
│  Zusammenfassung der Auswahl:                 │
│                                               │
│  root@dev-server.example.com:                 │
│    - claude-project (bestehend)               │
│    - new-feature (neu)                        │
│  jsp@build.corp.example.com:                  │
│    - sync-all (bestehend)                     │
│                                               │
│  Gesamt: 3 Session(s) auf 2 Host(s)           │
│                                               │
│  [ Auswahl komplett in einem WT öffnen      ] │
│  [ Auswahl jedes Hosts einzeln in WT öffnen ] │
└───────────────────────────────────────────────┘
```

Wird angezeigt, wenn **">> Öffnen"** markiert ist. **Dies ist die Startansicht**. Drei Buttons:

**1. "Alle erkannten Sessions"** -- der Schnellstart. Oeffnet alle tmux-Sessions auf allen erreichbaren Hosts (pro Host ein eigenes Terminal-Fenster). Dieser Button ist **nie ausgegraut** und beim App-Start bereits fokussiert -- ein Druck auf Enter genuegt.

**2. "Ein WT – Auswahl öffnen"** -- oeffnet alle **ausgewaehlten** Sessions in einem einzigen Windows-Terminal-Fenster, ein Tab pro Session, quer ueber alle Hosts.

**3. "Pro Host – Auswahl öffnen"** -- oeffnet pro Host mit ausgewaehlten Sessions ein eigenes Windows-Terminal-Fenster.

Die beiden Auswahl-Buttons sind **ausgegraut**, solange keine Sessions ausgewaehlt und keine neuen Session-Namen eingetragen sind.

**Nach dem Oeffnen** wird der gesamte Auswahl-Zustand zurueckgesetzt: alle Checkboxen leer, alle Eingabefelder leer. Fuer jeden betroffenen Host wird ein Reload ausgeloest. Die Anwendung bleibt offen und ist sofort wieder benutzbar.

### 7.5 Ansicht "Direktsession" (Fast-Track)

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
│  build → root@dev-server.example.com (neu)           │
│  build → jsp@build.corp.example.com (bestehend)      │
│  deploy → root@dev-server.example.com (neu)          │
│  deploy → jsp@build.corp.example.com (neu)           │
│  Gesamt: 4 Sessions auf 2 Hosts                      │
│                                                      │
│  [ Ein WT – Ausführen ] [ Pro Host – Ausführen ]     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

Wird angezeigt, wenn **"Direktsession"** in der unteren Zone markiert ist (Shortcut: `+`). Diese Ansicht **dreht die Perspektive um**: Statt Sessions pro Host einzeln auszuwaehlen, definieren Sie einmal eine Liste von Session-Namen und waehlen dann die Ziel-Hosts.

**Oberer Bereich -- Host-Auswahl:** Alle gespeicherten Hosts mit Checkboxen und Farbstatus (blau/gruen/rot). Rote Hosts koennen angewaehlt werden -- bei "Ausfuehren" versucht die App automatisch eine Neuverbindung. Gelingt sie, wird deployed; sonst erscheint ein Fehler-Dialog. Tastenkuerzel: `t` Toggle, `a` Alle, `i` Invertieren.

**Mittlerer Bereich -- Session-Namen:** Mehrzeiliges Eingabefeld, ein Name pro Zeile. Nur `a-z`, `A-Z`, `0-9`, `_` und `-` sind erlaubt. Ungueltige Namen werden sofort rot markiert.

**Zusammenfassung:** Zeigt pro Kombination (Host, Session), ob die Session bereits existiert (attach) oder neu erzeugt wird (neu).

**Buttons:** Zwei Launch-Buttons nebeneinander:
- **"Ein WT – Ausführen"** -- alle Sessions in einem WT-Fenster (Shortcut: `j`)
- **"Pro Host – Ausführen"** -- pro Host ein eigenes WT-Fenster
- Ausgegraut, wenn keine Hosts ausgewaehlt oder keine Session-Namen eingetragen

**Kein Reset nach dem Ausführen:** Auswahl und Eingabe bleiben bestehen. So koennen Sie die gleiche Konfiguration erneut ausfuehren, ohne alles neu einzugeben. Die Session-Listen der betroffenen Hosts werden intern aktualisiert, sodass beim naechsten Druck korrekt "bestehend" statt "neu" angezeigt wird.

### 7.6 Ansicht "Übersicht" (Fast-Track)

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
│  [ Ein WT – Auswahl öffnen ] [ Pro Host – Auswahl ]  │
│                                                       │
└───────────────────────────────────────────────────────┘
```

Wird angezeigt, wenn **"Übersicht"** in der unteren Zone markiert ist (Shortcut: `-`). Diese Ansicht gibt Ihnen die **Vogelperspektive** ueber alle Sessions aller erreichbaren Hosts in einer einzigen, sortierbaren Tabelle.

**Tabelle:** Drei Spalten -- Auswahl-Marker (✓ oder leer), Host, Session. Klick auf einen Spalten-Header sortiert die Tabelle nach dieser Spalte (Standard: nach Session-Name).

**Nur erreichbare Hosts:** Es erscheinen ausschliesslich Sessions von hellgruenen Hosts. Fuer rote Hosts sind keine Session-Daten bekannt.

**Leerzustand:** Wenn noch kein Host erreichbar ist, zeigt die Tabelle "Warte auf Verbindungen..." und fuellt sich automatisch, sobald Hosts gruen werden.

**Auswahl:** Eigener, disjunkter Auswahl-Pool -- komplett unabhaengig von den Auswahlen in den Host-Detail-Ansichten oder der Direktsession.
- `t` Toggle, `a` Alle, `i` Invertieren, `j` Sofortstart (markierte Session sofort oeffnen)

**Buttons:** Zwei Launch-Buttons nebeneinander:
- **"Ein WT – Auswahl öffnen"** -- alle markierten Sessions in einem WT-Fenster
- **"Pro Host – Auswahl öffnen"** -- pro Host ein eigenes WT-Fenster
- Ausgegraut, wenn nichts ausgewaehlt

**Kein Reset nach dem Öffnen:** Auswahl bleibt bestehen (analog zu Direktsession).

---

# TEIL III -- WORKFLOWS

## 8. Workflow: Mit einem einzelnen Host arbeiten

Typischer Ablauf, wenn Sie mit einem neuen Host von Null anfangen:

**Schritt 1 -- Host anlegen** (Kapitel 4)
`n` druecken, SSH-Ziel eingeben, Enter.

**Schritt 2 -- Bei Bedarf Schluessel deployen**
Host wird rot? Markieren Sie ihn, `s` druecken (oder Button "Host einrichten" klicken). Im WT-Tab das Passwort eingeben, Enter, fertig. Zurueck in der App `r` fuer Reconnect.

**Schritt 3 -- Sessions auswaehlen**
Host wird gruen. Mit Pfeil runter auf den Host, Tab in den Detail-Bereich. Mit Pfeil runter durch die Session-Liste navigieren, mit `Space` oder `t` die gewuenschten Sessions anhaken. `a` waehlt alle aus, `i` invertiert.

**Schritt 4 -- Optional: neue Sessions definieren**
Shift+Tab zurueck, dann Tab bis ins untere Eingabefeld. Pro Zeile einen Namen eintragen. Ungueltige Namen werden sofort rot markiert.

**Schritt 5 -- Oeffnen**
`o` springt zur Öffnen-Ansicht. Dort zeigt die Zusammenfassung, was Sie ausgewaehlt haben. Klick auf **"Auswahl komplett in einem WT öffnen"** oder **"Auswahl jedes Hosts einzeln in WT öffnen"** -- je nach Praeferenz.

## 9. Workflow: Mit mehreren Hosts arbeiten

Der entscheidende Punkt: **Die Auswahl wird host-uebergreifend gesammelt**. Sie koennen also:

1. Host A markieren, dort Sessions auswaehlen
2. Host B markieren, dort weitere Sessions auswaehlen
3. Host C markieren, neue Sessions im Eingabefeld eintragen
4. `o` (oder Pfeil zur letzten Listen-Zeile) fuer die Öffnen-Ansicht
5. Die Zusammenfassung zeigt alle drei Hosts mit ihren jeweiligen Sessions gruppiert
6. **"Auswahl komplett in einem WT öffnen"** macht einen WT-Fenster mit allen Tabs, ideal fuer projektuebergreifende Uebersicht
7. **"Auswahl jedes Hosts einzeln in WT öffnen"** macht pro Host ein eigenes WT-Fenster, ideal fuer raeumlich getrennte Kontexte

Die Persistenz der Auswahl gilt auch beim spaeteren Rueckkehr zu einem bereits besuchten Host -- die Haken sind noch da.

## 10. Workflow: Einzelne Session blitzschnell oeffnen

**Sofortstart (`j` / Jump start)** ist fuer das "mal eben reinschauen"-Szenario. Sie sind in der Session-Liste, markieren mit Pfeil rauf/runter eine Session, druecken `j` -- und schon oeffnet sich genau diese eine Session in einem eigenen Terminal-Tab. Kein Umweg ueber die Öffnen-Ansicht, kein Zuruecksetzen von Auswahlen. Ideal zum kurzen Nachsehen oder Debuggen.

## 11. Workflow: Host-Fehler behandeln

Ein hellroter Host bedeutet nicht, dass Sie ihn wegwerfen muessen. Oft liegt es nur an Details:

| Fehler | Ursache | Loesung |
|---|---|---|
| `Connection refused` | SSH-Dienst laeuft nicht / falscher Port | Host pruefen, dann "Erneut verbinden" |
| `Connection timed out` | Host nicht erreichbar (VPN? Firewall?) | Netzwerk pruefen, "Erneut verbinden" |
| `Permission denied (publickey)` | SSH-Key fehlt auf dem Remote | **"Host einrichten"** klicken |
| `Host key verification failed` | Neuer Fingerprint | Manuell `ssh user@host` im Terminal, Fingerprint akzeptieren |

Nach jeder Korrektur: **"Erneut verbinden"** in der Detail-Ansicht oder Shortcut `r`.

Wenn alles nichts hilft: **"Löschen"** (mit Sicherheitsabfrage) entfernt den Host aus der Liste.

## 11a. Workflow: Gleiche Sessions auf mehrere Hosts verteilen (Direktsession)

Typisches Szenario: Sie wollen auf drei Servern jeweils die Sessions `build` und `deploy` erzeugen und sofort oeffnen.

1. `+` druecken (Sprung zur Direktsession)
2. In der Host-Liste die gewuenschten Hosts anhakennn (`t` zum Toggeln, `a` fuer alle)
3. Im Eingabefeld die Session-Namen eintragen (ein Name pro Zeile)
4. Die Zusammenfassung zeigt fuer jede Kombination, ob die Session neu erzeugt oder angehaengt wird
5. `j` drueckt sofort den "Ein WT"-Button, oder manuell auf einen der beiden Buttons klicken

Die Auswahl bleibt nach dem Ausfuehren bestehen -- Sie koennen sofort nochmal druecken.

## 11b. Workflow: Gesamtuebersicht aller Sessions nutzen (Uebersicht)

Typisches Szenario: Sie wollen sich schnell einen Ueberblick verschaffen und gezielt einzelne Sessions oeffnen.

1. `-` druecken (Sprung zur Uebersicht)
2. Die Tabelle zeigt alle Sessions aller erreichbaren Hosts -- sortierbar per Klick auf den Spalten-Header
3. Mit `t` einzelne Zeilen anhakennn, mit `j` eine Session sofort in einem Tab oeffnen (Sofortstart)
4. Oder mehrere markieren und ueber die Buttons oeffnen

Die Uebersicht hat einen eigenen Auswahl-Pool -- Aenderungen hier beeinflussen nicht die Host-Detail-Auswahlen und umgekehrt.

---

# TEIL IV -- POWER-USER

## 12. Tastenkuerzel-Referenz

### 12.1 Globale Shortcuts (immer verfuegbar)

Diese Shortcuts funktionieren aus jeder Ansicht -- ausser wenn der Fokus in einem Eingabefeld liegt, das den Buchstaben sonst verschlucken wuerde.

| Taste | Aktion (englisch / Footer-Beschriftung) | Beschreibung |
|---|---|---|
| `q` | Quit | Anwendung beenden |
| `n` | New host | Springt zu "+ Neuer Host" und fokussiert das Eingabefeld |
| `o` | Open | Springt zu ">> Öffnen" |
| `x` | Open all | Fuehrt "Alle erkannten Sessions" sofort aus |
| `+` | Direct session | Springt zur "Direktsession"-Ansicht |
| `-` | Show all | Springt zur "Übersicht"-Ansicht |
| `l` | Language | Oeffnet den Sprachwahl-Dialog |
| `Entf` | Delete host | Loescht den markierten Host (mit Sicherheitsabfrage) |

### 12.2 Session-Liste (Host verbunden)

Nur aktiv, wenn der Fokus in der Session-Liste eines verbundenen Hosts liegt.

| Taste | Aktion | Beschreibung |
|---|---|---|
| `t` | Toggle | Markierte Session an-/abwaehlen |
| `a` | Toggle All | Alle Sessions an-/abwaehlen |
| `i` | Invert | Auswahl invertieren |
| `j` | Jump start | Markierte Session sofort in einem WT-Tab oeffnen |
| `r` | Reload | Session-Liste vom Host neu abrufen |

### 12.3 Host-Fehler-Ansicht

Nur aktiv, wenn die Fehler-Ansicht angezeigt wird.

| Taste | Aktion | Beschreibung |
|---|---|---|
| `r` | Reconnect | Neuer Verbindungsversuch |
| `s` | Set up host | Interaktives WT zum Deployen des SSH-Schluessels |

### 12.4 Direktsession

Nur aktiv, wenn die Direktsession-Ansicht angezeigt wird.

| Taste | Aktion | Beschreibung |
|---|---|---|
| `t` | Toggle | Markierten Host an-/abwaehlen (Fokus in Host-Liste) |
| `a` | Toggle All | Alle Hosts an-/abwaehlen |
| `i` | Invert | Host-Auswahl invertieren |
| `j` | Execute | "Ein WT – Ausführen" sofort ausloesen |

### 12.5 Übersicht

Nur aktiv, wenn die Übersicht-Ansicht angezeigt wird.

| Taste | Aktion | Beschreibung |
|---|---|---|
| `t` | Toggle | Markierte Zeile an-/abwaehlen |
| `a` | Toggle All | Alle Zeilen an-/abwaehlen |
| `i` | Invert | Auswahl invertieren |
| `j` | Jump start | Markierte Session sofort in einem WT-Tab oeffnen |

### 12.6 Navigation (Textual-Standards)

Diese Tastenkuerzel sind von Textual vorgegeben und funktionieren ueberall:

| Taste | Aktion |
|---|---|
| `Tab` / `Shift+Tab` | Naechstes / vorheriges fokussierbares Element |
| `↑` / `↓` | In Listen hoch/runter navigieren |
| `Space` | Auswahlbox toggeln (in Session-Liste) |
| `Enter` | Button aktivieren / Dialog bestaetigen |
| `Esc` | Modaler Dialog schliessen (abbrechen) |

### 12.7 Sprachunabhaengigkeit

**Wichtig:** Die Shortcut-Tasten bleiben **konstant ueber alle Sprachen**. Auch wenn Sie auf Klingonisch wechseln, ist `q` immer "Quit" (bzw. `mev`), `n` immer "New host" (bzw. `host chu'`). Nur die Beschriftung im Footer wird uebersetzt -- die Tasten nicht.

---

## 13. Sprache wechseln

### 13.1 Aktive Sprache pruefen

Die aktuell aktive Sprache steht rechts oben in der Header-Leiste, im Format `[de] Deutsch`.

### 13.2 Dialog aufrufen

Druecken Sie den globalen Shortcut **`l`**. Es oeffnet sich ein modaler Dialog mit dem Titel **"Sprache wählen:"** und einer Auswahlliste (Einzelauswahl) aller verfuegbaren Sprachen. Die aktive Sprache ist bereits markiert.

Die verfuegbaren Sprachen werden automatisch aus dem Installationsverzeichnis ermittelt. Zum Zeitpunkt dieses Handbuchs mitgeliefert:

- English (en)
- Deutsch (de)
- Français (fr)
- Español (es)
- Esperanto (eo)
- tlhIngan Hol (tlh)
- اردو (ur)

### 13.3 Neustart-Prompt

Bestaetigen Sie Ihre Wahl mit **OK**. Ein weiterer Dialog fragt:

> *Sprache geaendert zu [xx]. Jetzt neu starten?*

- **Ja** -- die App beendet sich und startet sofort neu mit der neuen Sprache. Ihre Host-Liste bleibt erhalten (aus `hosts.json`).
- **Nein** -- die Sprache ist in der Konfigurationsdatei gespeichert und wird beim naechsten manuellen Start aktiv.

---

## 14. Konfiguration und Datenhaltung

Open-TmuxTabs speichert Daten an zwei Orten unter `%APPDATA%\Open-TmuxTabs\`:

### 14.1 `hosts.json` -- die Host-Liste

Pro Host werden persistiert:
- `ssh_target` -- die Original-Eingabe (z. B. `root@server` oder `devbox`)
- `display_name` -- der aufgeloeste Anzeigename
- `last_used` -- Zeitpunkt der letzten erfolgreichen Nutzung
- `use_count` -- wie oft der Host schon genutzt wurde

**Nicht persistiert** werden Laufzeit-Daten: Verbindungsstatus, aktuelle Session-Listen, Ihre Auswahl. All das wird bei jedem Start neu ermittelt.

### 14.2 `config.json` -- Einstellungen

Aktuell enthaelt sie nur:
- `language` -- der gewaehlte Sprachcode (z. B. `"de"`)

### 14.3 Was dazwischen liegt

Die Zusammenstellung Ihrer Session-Auswahl (welche Haken Sie gesetzt haben, welche neuen Sessions Sie eingetragen haben) lebt **nur im Arbeitsspeicher**. Sie bleibt erhalten, solange die App laeuft, und wird nach dem Oeffnen zurueckgesetzt.

---

## 15. Fehlerbehandlung und Troubleshooting

### 15.1 Der SSH-Fehler-Dialog

Wenn ein SSH-Aufruf fehlschlaegt (z. B. beim Erstellen einer neuen Session ueber die "Auswahl oeffnen"-Buttons), erscheint ein modaler Fehler-Dialog mit:
- Titel: **"Fehler bei <hostname>"**
- Koerper: die SSH-Stderr-Ausgabe, scrollbar
- Button **"OK"** (oder `Esc` / `Enter`) zum Schliessen

Bei parallelen Fehlern (mehrere Hosts schlagen gleichzeitig fehl) werden die Dialoge **seriell** nacheinander gezeigt, damit nichts untergeht.

### 15.2 Haeufige Fehler und Loesungen

| Fehlermeldung | Wahrscheinliche Ursache | Loesung |
|---|---|---|
| `SSH connection timed out` | Host nicht erreichbar | Netzwerk / VPN pruefen |
| `SSH connection failed` + `Permission denied` | Key fehlt | "Host einrichten" |
| `SSH connection failed` + `Host key verification failed` | Neuer Fingerprint | Manuell akzeptieren |
| `ssh not found` | OpenSSH nicht installiert oder nicht im PATH | OpenSSH aktivieren |
| `tmux: command not found` im SSH-Output | tmux fehlt auf Remote | `apt install tmux` / `yum install tmux` |

### 15.3 Wenn die TUI kaputt aussieht

- **Farben falsch / unlesbar**: Ueberpruefen Sie Ihr Windows-Terminal-Theme. Open-TmuxTabs nutzt Textuals dunkles Farbschema.
- **Layout verrutscht**: Fenster zu schmal? Ein Mindestbereich von ca. 80 Zeichen Breite ist sinnvoll.
- **Urdu-Text (RTL) verrutscht**: Rechts-nach-Links-Text in einer Spalten-TUI ist technisch begrenzt. Bei Problemen auf eine andere Sprache wechseln.

---

# TEIL V -- ANHANG

## A. Technischer Hintergrund (kurz)

### A.1 SSH-Batching

Statt viele kleine SSH-Aufrufe abzusetzen, benutzt Open-TmuxTabs pro Host **einen einzigen SSH-Call** mit einem gebatchten Remote-Skript, das:
1. Die tmux-Grundkonfiguration deployed (idempotent)
2. Eventuell angeforderte neue Sessions erstellt
3. Alle laufenden Sessions auflistet

Das spart Verbindungsaufbauten (ohne `ControlMaster` sonst teuer) und macht die App auch ueber langsame Verbindungen fluessig.

### A.2 Remote-tmux-Config-Deployment

Beim ersten erfolgreichen Verbinden schreibt Open-TmuxTabs einen Block in `~/.tmux.conf` auf dem Remote-Host, markiert durch Kommentare. Der Block setzt:

```tmux
set -g mouse on
set -g history-limit 10000
```

Das Deployment ist **idempotent** -- bei jedem weiteren Connect wird geprueft, ob der Block bereits vorhanden ist.

### A.3 Windows Terminal Integration

Jeder geoeffnete Tab wird per `wt.exe new-tab --title "<session@host>" cmd.exe /c "ssh -t host \"tmux attach-session -t session\""` erzeugt. Die Tabs werden mit ` ; ` zu einem einzigen WT-Aufruf verkettet.

Windows limitiert die Kommandozeilenlaenge auf ca. 32.767 Zeichen (`CreateProcessW`). Open-TmuxTabs teilt bei Ueberschreitung von **30.000 Zeichen** (Sicherheitsmarge) automatisch auf mehrere WT-Aufrufe auf.

### A.4 Async-Worker-Modell

Alle blockierenden Operationen (SSH-Verbindungen, Subprozess-Aufrufe) laufen als Textual-Worker in Threads, damit die UI waehrenddessen reaktiv bleibt. Das erklaert, warum Sie beim Start sofort auf dem Schnellstart-Button landen und Enter druecken koennen -- auch wenn im Hintergrund noch Hosts verbunden werden.

---

## B. Glossar

| Begriff | Erklaerung |
|---|---|
| **tmux** | Terminal Multiplexer. Ermoeglicht persistente Sessions auf einem Server. |
| **Session** (tmux) | Eine persistente tmux-Umgebung mit einem oder mehreren Panes/Fenstern. |
| **Attach** (tmux) | Sich mit einem laufenden tmux-Session-Prozess verbinden. |
| **Detach** (tmux) | Die Verbindung zu tmux trennen, ohne die Session zu beenden. |
| **SSH** | Secure Shell -- verschluesseltes Netzwerkprotokoll fuer Remote-Login. |
| **SSH-Config-Alias** | Kurzname fuer eine SSH-Zielkonfiguration in `~/.ssh/config`. |
| **SSH Public Key** | Der oeffentliche Teil eines SSH-Schluesselpaares, der auf den Remote-Host uebertragen wird, um passwortlose Anmeldung zu ermoeglichen. |
| **WT** | Windows Terminal (`wt.exe`). |
| **TUI** | Terminal User Interface -- grafische Oberflaeche im Textmodus. |
| **Host** (in dieser App) | Ein gespeicherter SSH-Zielserver. |
| **Textual** | Python-Framework fuer TUIs, auf dem Open-TmuxTabs basiert. |
| **`%APPDATA%`** | Windows-Umgebungsvariable fuer `C:\Users\<username>\AppData\Roaming\`. |

---

## C. Shortcut-Cheatsheet

*Druckbare Kurzuebersicht -- alle Tastenkuerzel auf einen Blick.*

### Immer verfuegbar
```
q   Beenden            n   Neuer Host (Sprung)
o   Öffnen (Sprung)    x   Alle erkannten Sessions
+   Direktsession      -   Uebersicht
l   Sprache            Entf   Host loeschen
```

### In der Session-Liste
```
t   Session umschalten       a   Alle umschalten
i   Auswahl invertieren      j   Sofortstart (diese Session)
r   Neu laden
```

### In der Direktsession
```
t   Host umschalten          a   Alle umschalten
i   Host-Auswahl invertieren j   Ausfuehren (Ein WT)
```

### In der Uebersicht
```
t   Zeile umschalten         a   Alle umschalten
i   Auswahl invertieren      j   Sofortstart (diese Session)
```

### Bei fehlgeschlagenem Host
```
r   Erneut verbinden
s   Host einrichten (SSH-Key deployen)
```

### Standard-Navigation
```
Tab / Shift+Tab    Fokus weiter / zurueck
↑ / ↓              Listen-Navigation
Space              Auswahlbox toggeln
Enter              Button aktivieren / OK
Esc                Dialog abbrechen
```

---

## D. Bekannte Einschraenkungen

- **Windows-only:** Die Anwendung nutzt `wt.exe` und verhaelt sich Windows-spezifisch (z. B. `CREATE_NO_WINDOW`). Unter Linux/macOS laeuft sie technisch, kann aber keine Tabs oeffnen.
- **Kein GUI-Passwort-Prompt:** Wenn ein Host noch keinen SSH-Key hat, verweigert Open-TmuxTabs bewusst das Passwort-Prompting innerhalb der TUI -- das wuerde das Layout zerstoeren. Stattdessen ist **"Host einrichten"** vorgesehen, das ein separates interaktives Terminal oeffnet.
- **Urdu (RTL):** Rechts-nach-Links-Text in einer Spalten-TUI ist technisch begrenzt. Das Layout kann bei Urdu an manchen Stellen verrutschen.
- **Klingonisch-Uebersetzung:** Die tlh-Uebersetzung verwendet Loanwords fuer IT-Begriffe (SSH, tmux, session, host). Das ist ein Kompromiss -- Klingonisch hat keine muttersprachlichen Begriffe dafuer.

---

## E. Weitere Ressourcen

- **Textual** -- <https://textual.textualize.io/>
- **tmux** -- `man tmux` oder <https://github.com/tmux/tmux/wiki>
- **Windows Terminal** -- <https://aka.ms/terminal>
- **OpenSSH auf Windows** -- <https://learn.microsoft.com/windows-server/administration/openssh/>

---

*Open-TmuxTabs -- von Entwicklern fuer Entwickler.*

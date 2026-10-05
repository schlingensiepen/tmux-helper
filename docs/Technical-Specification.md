# Open-TmuxTabs -- Technische Spezifikation

**Stand:** 2026-10-05 (Version 2.0.0)
**Status:** Aktuell
**Grundlage:** User-Specification.md

---

## 1. Technologie-Stack

| Komponente | Technologie | Version |
|---|---|---|
| Sprache | Python | 3.10+ |
| TUI-Framework | Textual | 0.86+ |
| I18n | `gettext` (Standardbibliothek) | -- |
| Test-Framework | pytest | aktuell |
| Async-Tests | pytest-asyncio | aktuell |
| TUI-Devtools + Snapshots | textual-dev | aktuell |

**Keine weiteren externen Abhaengigkeiten.** SSH und wt.exe werden ueber `subprocess` angesprochen.

---

## 2. Projektstruktur

Aufbau des Repositorys `schlingensiepen/tmux-helper`:

```
tmux-helper/
├── src/
│   └── open_tmux_tabs/
│       ├── __init__.py
│       ├── __main__.py          # `python -m open_tmux_tabs`, Einstieg der .exe
│       ├── app.py               # Textual App-Klasse, main() mit Neustart-Schleife
│       ├── app.tcss             # Globales Textual-Stylesheet
│       ├── config.py            # Benutzereinstellungen (config.json)
│       ├── display.py           # Anzeigenamen-Berechnung (Truncation-Logik)
│       ├── host_resolver.py     # SSH-Alias-Aufloesung (ssh -G)
│       ├── host_store.py        # Host-Persistenz (JSON laden/speichern)
│       ├── i18n.py              # gettext-Setup, Sprach-Discovery
│       ├── models.py            # Datenmodelle (HostEntry, HostStatus)
│       ├── ssh.py               # SSH-Kommunikation (connect, parse)
│       ├── wt_launcher.py       # Windows-Terminal-Start + Host-Setup
│       ├── locales/             # Uebersetzungen (messages.pot, <lang>.po, <lang>/LC_MESSAGES/*.mo)
│       └── widgets/             # app_header, confirm_dialog, error_dialog, host_detail,
│                                # host_error, host_list, language_dialog, new_host,
│                                # open_view, direct_session_view, show_all_view
├── scripts/
│   └── compile_po.py            # .po -> .mo ohne externes gettext (arbeitet auf src/open_tmux_tabs/locales/)
├── packaging/
│   └── open-tmux-tabs.spec      # PyInstaller-Spezifikation fuer die .exe
├── deploy/
│   └── samba/                   # start.cmd + SSH-Config-Beispiel fuer die clawbook-lehre-Freigabe
├── tests/                       # conftest.py, test_models, test_ssh, test_wt_launcher,
│                                # test_host_store, test_host_resolver, test_display
├── docs/                        # abgeleitete Dokumentation (Handbuch, LIESMICH, Architecture-Guide,
│                                # User-/Technical-Specification, Testplan)
├── .github/workflows/           # CI (Tests) und Release (Wheel + .exe)
├── pyproject.toml
├── LICENSE                      # Apache-2.0
├── NOTICE
└── README.md
```


---

## 3. Datenmodelle (`models.py`)

### 3.1 HostStatus (Enum)

```python
class HostStatus(Enum):
    PENDING = "pending"        # hellblau -- noch nicht versucht
    CONNECTED = "connected"    # hellgruen -- Sessions abgerufen
    FAILED = "failed"          # hellrot -- nicht erreichbar
```

### 3.2 HostEntry (Dataclass)

```python
@dataclass
class HostEntry:
    ssh_target: str              # Original-Eingabe ("root@dev-server.example.com" oder "devbox")
    display_name: str            # Aufgeloest: "root@devbox" oder "root@dev-server.example.com"
    status: HostStatus = HostStatus.PENDING
    sessions: list[str] = field(default_factory=list)
    selected_sessions: set[str] = field(default_factory=set)
    new_session_text: str = ""   # Inhalt des Eingabefelds (persistent beim Wechsel)
    last_used: str = ""          # ISO-Zeitstempel
    use_count: int = 0
    error_message: str = ""      # Letzte Fehlermeldung bei FAILED
```

`selected_sessions` und `new_session_text` sind **nur zur Laufzeit** relevant und werden nicht persistiert.

### 3.3 Persistenz-Format (`hosts.json`)

```json
[
  {
    "ssh_target": "root@dev-server.example.com",
    "display_name": "root@dev-server.example.com",
    "last_used": "2026-04-06T14:30:00",
    "use_count": 12
  }
]
```

Felder `status`, `sessions`, `selected_sessions`, `new_session_text` und `error_message` werden **nicht** gespeichert -- sie sind fluechtig und werden bei jedem Start neu ermittelt.

---

## 4. Modulbeschreibungen

### 4.1 `ssh.py` -- SSH-Kommunikation

Zentrale Funktion fuer alle SSH-Interaktionen. Wird als Textual Worker ausgefuehrt, um die UI nicht zu blockieren.

**Oeffentliche Schnittstelle:**

```python
async def ssh_connect(host: str) -> tuple[list[str], str | None]:
    """Connect to host, deploy tmux config, return (session_names, error_or_none)."""

async def ssh_create_and_list(host: str, new_sessions: list[str]) -> tuple[list[str], list[str], str | None]:
    """Create new sessions on host, return (created, all_sessions, error_or_none)."""
```

**Interna:**
- Fuehrt `subprocess.run()` in einem Thread-Worker aus (`run_in_executor`), da `subprocess` blockierend ist
- Remote-Skript als einzelner gebatchter Befehl (wie im bestehenden Code)
- Zeilenprotokoll-Parsing: `CFG_OK` (Konfiguration vorhanden), `CFG_DEPLOYED_RELOADED` / `CFG_DEPLOYED_PENDING` (Konfigurationsblock gerade in `~/.tmux.conf` eingetragen, mit bzw. ohne erfolgreiches `tmux source-file`), `CREATED:<name>`, `EXISTS:<name>`, `NO_SESSIONS`; jede sonstige Zeile gilt als Session-Name — gibt der Host zusaetzlich Text auf stdout aus (MOTD, Warnungen), erscheint dieser als Session-Name (bekannte Einschraenkung)
- `stdin=subprocess.DEVNULL`, `stderr=subprocess.PIPE` (captured), `timeout=120`, `-o ConnectTimeout=10`
- `creationflags=CREATE_NO_WINDOW` auf Windows, damit SSH-Fingerprint-Prompts nicht die TUI korrumpieren
- **Kein `shell=True`** -- auf Windows wuerde `cmd.exe` die Linux-Shell-Syntax zerstoeren

### 4.2 `host_resolver.py` -- SSH-Alias-Aufloesung

```python
async def resolve_ssh_target(target: str) -> str:
    """Resolve SSH alias to 'user@hostname' via 'ssh -G target'.
    Returns original target if resolution fails."""
```

- Parst `hostname` und `user` aus der `ssh -G`-Ausgabe
- Falls `user` fehlt, wird der aktuelle Systembenutzer verwendet
- Wird asynchron im Worker ausgefuehrt

### 4.3 `display.py` -- Anzeigenamen-Kuerzung

```python
def compute_display_names(
    hosts: list[HostEntry],
    max_width: int | None = None,
    min_domain_chars: int = MIN_DOMAIN_CHARS,
) -> tuple[dict[str, str], int]:
    """Compute truncated display names for the host list.
    Returns (display_names_dict, list_width)."""
```

Algorithmus:
1. Fuer jeden Host: Trenne `user@hostname` vom Rest der Domain (erster `.` nach hostname)
2. Bestimme den laengsten `user@hostname`-Teil
3. Gesamtbreite = laengster `user@hostname` + `.` + `min_domain_chars`
4. Fuer jeden Host: Zeige so viel Domain wie in die Gesamtbreite passt
5. Wenn ein Eintrag komplett hineinpasst, nicht auffuellen

### 4.4 `wt_launcher.py` -- Windows-Terminal-Start

```python
def launch_single_wt(sessions: list[tuple[str, str]]) -> None:
    """Launch one WT window. sessions = [(host, session_name), ...]"""

def launch_per_host(sessions_by_host: dict[str, list[str]]) -> None:
    """Launch one WT window per host."""

def launch_all(hosts: list[HostEntry]) -> None:
    """Launch all sessions on all connected hosts (one WT per host).
    Convenience wrapper around launch_per_host for the quick-start button."""
```

- Tab-Befehl: `new-tab --title "session@host" cmd.exe /c "ssh -t host \"tmux attach-session -t session\""`
- Tabs getrennt durch ` ; `
- Automatisches Splitting bei >30.000 Zeichen
- `subprocess.Popen(f"wt.exe {args}")` -- String, kein `shell=True`

### 4.5 `host_store.py` -- Persistenz

```python
class HostStore:
    def __init__(self, path: Path | None = None):
        """Default: %APPDATA%/Open-TmuxTabs/hosts.json"""

    def load(self) -> list[HostEntry]: ...
    def save(self, hosts: list[HostEntry]) -> None: ...
    def update_usage(self, hosts: list[HostEntry], ssh_target: str) -> None: ...
```

- Laedt/speichert nur die persistenten Felder (ssh_target, display_name, last_used, use_count)
- Fehlertoleranz: Korruptes JSON → leere Liste

---

## 5. Textual App-Architektur (`app.py`)

### 5.1 App-Klasse

```python
class OpenTmuxTabsApp(App):
    CSS_PATH = "app.tcss"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        ("q", "quit", _("Quit")),
        ("n", "new_host", _("New host")),
        ("o", "goto_open", _("Open")),
        ("x", "open_all", _("Open all")),
        ("plus_sign", "goto_direct_session", _("Direct session")),
        ("minus", "goto_show_all", _("Show all")),
        ("l", "change_language", _("Language")),
        ("delete", "delete_host", _("Delete host")),
    ]
```

### 5.2 Zustandsverwaltung

Der zentrale Zustand lebt in der App-Instanz:

```python
selected_index: reactive[int] = reactive(OPEN)   # Aktuell markierter Eintrag
hosts: list[HostEntry] = []                       # Alle Hosts (plain list, nicht reactive)
_display_names: dict[str, str] = {}               # Gekuerzte Anzeigenamen
_list_width: int = 0                              # Berechnete Listenbreite
_error_queue: asyncio.Queue[tuple[str, str]]      # Fehler-Warteschlange fuer serielle Anzeige
_error_consumer_running: bool = False              # Schutz vor doppeltem Consumer
_suppress_highlight: bool = False                  # Unterdrueckt Highlight-Events beim Rebuild
```

Es gibt keinen `watch_hosts`-Watcher. UI-Updates werden explizit durch `_rebuild_host_list()` und `_show_detail()` ausgeloest.

### 5.3 Widget-Baum

```
Screen
├── AppHeader             # Custom Header: Titel links, Sprach-Anzeige rechts
├── HostListView          # Links: Zwei-Zonen-ListView mit Trennern und Farbstatus
├── Container #detail-area  # Rechts: Kinder werden per remove_children()/mount() getauscht
│   ├── NewHostView         # Formular fuer neuen Host
│   ├── HostDetailView      # SelectionList der Sessions + TextArea fuer neue Sessions
│   ├── HostErrorView       # Reconnect + Host einrichten + Loeschen
│   ├── OpenView            # Schnellstart + Zusammenfassung + zwei Launch-Buttons
│   ├── DirectSessionView   # Fast-Track: Sessions auf mehrere Hosts verteilen
│   └── ShowAllView         # Fast-Track: Sortierbare Gesamttabelle
└── Footer
```

Es gibt keinen `ContentSwitcher`. Der Detail-Bereich ist ein einfacher `Container`, dessen Kinder bei Ansichtswechsel dynamisch per `remove_children()` und `mount()` getauscht werden. Jede Ansicht wird dabei **neu erzeugt**; der Laufzeit-Zustand (Session-Auswahl, Text neuer Sessions) liegt auf `HostEntry` und wird der neuen Ansicht uebergeben.

Die Session-Liste in `HostDetailView` ist eine Textual-`SelectionList`: Navigation mit den Pfeiltasten, Auswahl per Leertaste bzw. `t`/`a`/`i` — statt einzelner Checkbox-Widgets, zwischen denen man mit Tab springen muesste.

### 5.4 Hintergrund-Verbindungen (Workers)

Beim Start und bei Reload wird fuer jeden Host ein Worker gestartet. `_start_connect_worker()` ist synchron (fire-and-forget), die innere `_connect()`-Coroutine laeuft als Worker:

```python
def _start_connect_worker(self, index: int) -> None:
    host = self.hosts[index]
    host.status = HostStatus.PENDING

    async def _connect() -> None:
        await self._rebuild_host_list()  # UI-Update: hellblau
        sessions, error = await ssh_connect(host.ssh_target)

        if error:
            host.status = HostStatus.FAILED
            host.error_message = error
        else:
            host.status = HostStatus.CONNECTED
            host.sessions = sessions

        await self._rebuild_host_list()  # UI-Update: gruen/rot
        if self.selected_index == index or self.selected_index == OPEN:
            self._show_detail()

    self.run_worker(_connect(), exclusive=False)
```

Die innere `_connect()`-Funktion ist eine Coroutine (kein Thread-Worker). `ssh_connect()` selbst fuehrt `subprocess.run()` intern ueber `loop.run_in_executor()` in einem Thread aus.

### 5.5 Startverhalten

Beim App-Start wird die Auswahl auf **"Open"** gesetzt (nicht auf den ersten Host). Der Schnellstart-Button "Alle erkannten Sessions" (englisch: "Open all detected sessions") erhaelt den **Fokus**, sodass ein einzelner Enter-Druck genuegt. Falls keine Hosts gespeichert sind, steht die Auswahl auf "Neuer Host" mit Fokus auf dem Eingabefeld.

### 5.6 Auto-Fokus bei Ansichtswechsel

Jeder Ansichtswechsel setzt den Fokus auf das primaere Interaktionselement der neuen Ansicht:

| Ansicht | Fokus-Ziel |
|---|---|
| "Neuer Host" | Eingabefeld (`#new-host-input`) |
| Host (verbunden) | Session-Liste (`#session-list`) |
| "Open" | Schnellstart-Button (`#open-all-btn`) |
| "Direktsession" | Kein spezieller Auto-Fokus |
| "Uebersicht" | Kein spezieller Auto-Fokus |

Umsetzung via `self.call_after_refresh()`, da die Widgets nach `mount()` einen Render-Zyklus benoetigen, bevor sie fokussierbar sind.

### 5.7 Open-Ablauf

**Schnellstart ("Alle erkannten Sessions"):**

1. Pruefen, ob noch Hosts im Status `PENDING` sind (Verbindung laeuft)
2. Falls ja: Auf alle ausstehenden Workers warten (UI zeigt Fortschritt)
3. Alle Sessions aller `CONNECTED`-Hosts sammeln
4. `wt_launcher.launch_per_host()` aufrufen
5. `host_store.update_usage()` fuer jeden betroffenen Host
6. State zuruecksetzen + Reload

**Auswahl-Buttons:**

1. Fuer jeden Host mit Auswahl/neuen Sessions: `ssh_create_and_list()` im Worker ausfuehren
2. `wt_launcher.launch_single_wt()` oder `launch_per_host()` aufrufen
3. `host_store.update_usage()` fuer jeden betroffenen Host
4. Fuer jeden betroffenen Host: `selected_sessions` leeren, `new_session_text` leeren
5. Fuer jeden betroffenen Host: `connect_host()` als Worker starten (Reload)

**Gemeinsamer Reset nach allen drei Buttons:**
- Alle Auswahlboxen abwaehlen
- Alle Eingabefelder leeren
- Reload fuer betroffene Hosts

---

## 6. TCSS-Styling

### 6.1 Globales Stylesheet (`app.tcss`)

Das globale Stylesheet ist minimal -- nur zwei Regeln:

```css
Screen {
    layout: horizontal;
}

#detail-area {
    width: 1fr;
}
```

### 6.2 Widget-Level CSS (`DEFAULT_CSS`)

Die Host-Status-Farben und das Host-Listen-Layout sind als `DEFAULT_CSS` direkt im `HostListView`-Widget definiert:

```css
HostListView {
    width: auto;
    border-right: solid $accent;
}

.host-pending   { background: $primary-darken-2; }    /* hellblau */
.host-connected { background: $success-darken-2; }    /* hellgruen */
.host-failed    { background: $error-darken-2; }       /* hellrot */
```

**Hinweis:** Urspruenglich `lighten-3`, was auf dunklen Themes mit weissem Text unlesbar war. Geaendert zu `darken-2` fuer besseren Kontrast.

---

## 7. Test-Strategie

### 7.1 Framework: pytest + pytest-asyncio + textual-dev

**Begruendung:** pytest ist der De-facto-Standard fuer Python-Tests. Textual-Apps sind async und bieten mit der Pilot API und Snapshot-Tests eine eigene Test-Infrastruktur, die pytest voraussetzt. Mocking erfolgt ueber die eingebaute `monkeypatch`-Fixture von pytest bzw. `unittest.mock.patch` -- eine separate Mock-Bibliothek ist nicht noetig. `textual-dev` liefert Snapshot-Tests, die visuelle Regressionen (kaputte Layouts, falsche Farben) auffangen.

### 7.2 Test-Kategorien

| Kategorie | Verzeichnis | Was wird getestet | Mock-Bedarf |
|---|---|---|---|
| **Unit-Tests** | `tests/test_models.py` | Datenmodelle, Enum-Werte | Keiner |
| **Unit-Tests** | `tests/test_display.py` | Truncation-Algorithmus | Keiner |
| **Unit-Tests** | `tests/test_ssh.py` | SSH-Aufruf + Protokoll-Parsing | `subprocess.run` via `monkeypatch` |
| **Unit-Tests** | `tests/test_wt_launcher.py` | WT-Befehlszeilen-Aufbau, Splitting | `subprocess.Popen` via `monkeypatch` |
| **Unit-Tests** | `tests/test_host_store.py` | JSON-Laden/Speichern, Fehlertoleranz | Dateisystem (`tmp_path`) |
| **Unit-Tests** | `tests/test_host_resolver.py` | SSH-Alias-Aufloesung | `subprocess.run` via `monkeypatch` |
| **Integration** | `tests/test_app.py` (geplant) | TUI-Verhalten, Widget-Interaktion | Textual Pilot API + SSH via `monkeypatch` |
| **Snapshot** | `tests/test_app.py` (geplant) | Visuelle Regression (Layout, Farben) | Textual Snapshot-Tests via `textual-dev` |

### 7.3 Test-Ausfuehrung

```bash
# Alle Tests
pytest

# Nur Unit-Tests (schnell, kein I/O)
pytest tests/ -k "not test_app"

# Mit Coverage
pytest --cov=src/open_tmux_tabs --cov-report=term-missing

# Textual-Snapshot-Tests (falls gewuenscht)
pytest tests/test_app.py --snapshot-update
```

### 7.4 pytest-Konfiguration (in `pyproject.toml`)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

---

## 8. Implementierungsreihenfolge

Die Module werden in dieser Reihenfolge implementiert und getestet. Jeder Schritt baut auf den vorherigen auf, und nach jedem Schritt sind die zugehoerigen Tests gruen.

| Schritt | Modul | Abhaengigkeiten |
|---|---|---|
| 1 | `models.py` | Keine |
| 2 | `display.py` | `models` |
| 3 | `host_store.py` | `models` |
| 4 | `host_resolver.py` | Keine |
| 5 | `ssh.py` | `models` |
| 6 | `wt_launcher.py` | Keine |
| 7 | `widgets/` | `models`, `display` |
| 8 | `app.py` + `app.tcss` | Alles |
| 9 | Integrationstests | Alles |

---

## 9. pyproject.toml

Stand im Produkt-Repo (die Uebersetzungen und das Stylesheet werden als package-data ins Wheel gepackt):

```toml
[project]
name = "open-tmux-tabs"
version = "2.0.0"
description = "TUI for managing remote tmux sessions in Windows Terminal"
requires-python = ">=3.10"
dependencies = [
    "textual>=0.86",
]

[project.optional-dependencies]
dev = [
    "textual-dev",
    "pytest",
    "pytest-asyncio",
]

[project.scripts]
open-tmux-tabs = "open_tmux_tabs.app:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
open_tmux_tabs = [
    "app.tcss",
    "locales/*/LC_MESSAGES/*.mo",
    "locales/*.po",
    "locales/messages.pot",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

---

## 10. Internationalisierung (I18n)

### 10.1 Framework

Python-Standardbibliothek `gettext`. Keine externen Abhaengigkeiten.

### 10.2 Workflow

1. **Quellstrings:** Englisch, im Code mit `_("...")` markiert
2. **Template:** `src/open_tmux_tabs/locales/messages.pot` -- Entwickler-Kommentare (`#.`) fuer jeden String
3. **Uebersetzungen:** `src/open_tmux_tabs/locales/<lang>.po` pro Sprache (z. B. `de.po`)
4. **Kompiliert:** `src/open_tmux_tabs/locales/<lang>/LC_MESSAGES/open_tmux_tabs.mo` -- via `scripts/compile_po.py`; Eintraege mit leerem `msgstr` werden nicht uebernommen (Laufzeit-Fallback: Englisch), Plural-Formen werden nicht unterstuetzt
5. **Laufzeit:** `i18n.setup_i18n()` installiert `_()` global vor App-Start

### 10.3 Discovery

`i18n.find_locales_dir()` sucht zuerst im Paket (`open_tmux_tabs/locales/` — Wheel, .exe, editable install), dann im Repo-Root (Altlayout). `i18n.get_available_languages()` scannt dort `*/LC_MESSAGES/*.mo` und liefert eine Liste der installierten Sprachcodes (plus `en` als Quellsprache). Die `LanguageDialog`-Widget nutzt das fuer die Auswahlliste.

### 10.4 Persistenz und Wechsel

- Ohne gespeicherte Wahl wird die Sprache aus `LANG`, `LC_ALL` bzw. der System-Locale erkannt (Fallback: Englisch)
- Die gewaehlte Sprache wird in `%APPDATA%\Open-TmuxTabs\config.json` gespeichert (via `Config`-Klasse)
- Sprachwechsel zur Laufzeit: `BINDINGS`-Strings werden zur Klassen-Definitionszeit evaluiert und koennen nicht nachtraeglich geaendert werden. Loesung: Nach Aenderung fragt ein `ConfirmDialog` "Jetzt neu starten?". Bei Ja setzt die App `should_restart = True` und ruft `exit()`. Die `main()`-Funktion erkennt das Flag und startet eine neue App-Instanz mit der neuen Sprache.

```python
def main() -> None:
    config = Config()
    language = setup_i18n(config.language)
    while True:
        app = OpenTmuxTabsApp(config=config, language=language)
        app.run()
        if not app.should_restart:
            break
        config = Config()
        language = setup_i18n(config.language)
```

### 10.5 Header-Anzeige

Das Custom-Widget `AppHeader` zeigt oben: links den Titel, rechts die aktuelle Sprache im Format `[de] Deutsch`. Der Nativ-Name wird aus `i18n.LANGUAGE_NAMES` geholt.

### 10.6 Shortcut-Konstanz

**Wichtig:** Die `BINDINGS`-Tupel definieren die Taste hartcodiert:
```python
BINDINGS = [("t", "toggle_session", _("Toggle"))]
```
Die Taste (`"t"`) ist **sprachunabhaengig**, nur die Beschreibung wird uebersetzt. Damit bleiben Shortcuts konstant, auch wenn der Footer "Umschalten" statt "Toggle" anzeigt.

---

## 11. Getroffene Entscheidungen

| Thema | Entscheidung | Begruendung |
|---|---|---|
| Session-Name-Validierung im TextArea | **Echtzeit** bei Eingabe | Sofortiges Feedback, Warnung als Label unter dem Eingabefeld |
| HostDetailView-Instanziierung | **Neu erzeugt bei jedem Ansichtswechsel**, Zustand auf `HostEntry` | Einfacher als ein ContentSwitcher und frei von ID-Konflikten; Auswahl und Eingabetext ueberleben den Wechsel, weil sie am Datenmodell haengen |
| Bestaetigungsdialog | **ModalScreen** | Klare Trennung, Textual-Standard-Pattern, kein versehentliches Weiterklicken |
| `ssh -G` Fehlerfall | **Original behalten + Warnung** | Kein Blocker -- SSH-Aufruf kann trotzdem funktionieren |
| Test-Framework | **pytest + pytest-asyncio + textual-dev** | Kein pytest-mock noetig (monkeypatch/unittest.mock reichen), textual-dev liefert Snapshot-Tests fuer visuelle Regressionen |
| DOM-Operationen in Textual | **Alle `await`en** | `ListView.clear()`, `append()`, `remove()`, `mount()` sind async. Ohne `await` bleibt der alte DOM-Stand bestehen und verursacht `DuplicateIds`-Crashes. Alle Methoden, die den Widget-Baum aendern, muessen `async` sein. |
| Fokus-Management | **`call_after_refresh()`** | Widgets sind nach `mount()` nicht sofort fokussierbar -- erst nach dem naechsten Render-Zyklus. `call_after_refresh()` stellt sicher, dass der Fokus korrekt gesetzt wird. |
| Command Palette | **Deaktiviert** (`ENABLE_COMMAND_PALETTE = False`) | Textual bringt standardmaessig eine Ctrl+P-Palette mit, die fuer dieses Tool nicht relevant ist und den Anwender verwirrt. |
| ListItem-IDs | **Keine IDs auf ListItems** | Um DuplicateIds bei Rebuild zu vermeiden. Stattdessen wird der Index ueber die Position in der Kindliste ermittelt. |
| Disjunkte Auswahl (Fast-Track) | **Eigene Pools** fuer Direktsession und Uebersicht | Nur die Buttons innerhalb der jeweiligen Fast-Track-Ansicht wirken auf deren Auswahl. Aenderungen in Host-Detail haben keinen Einfluss auf Fast-Track und umgekehrt. Begruendung: Die Fast-Track-Funktionen sind "direkte Zugriffe" ohne Sammel-Workflow, daher getrennte Zustaende. |
| Kein Reset in Fast-Track | Auswahl bleibt **nach Ausfuehren bestehen** | In Oeffnen-Ansicht wird die Auswahl zurueckgesetzt (sammeln → abschicken → fertig). In Fast-Track-Ansichten bleibt sie stehen (direkt zugreifen → ggf. nochmal druecken). Begruendung: Unterschiedliche Nutzungsphilosophie ("sammeln" vs. "direkt"). |
| Rote Hosts in Direktsession | **Anwaehlbar** mit Reconnect-Versuch bei Execute | Rote Hosts werden angezeigt und koennen angehakt werden. Bei "Ausfuehren" versucht die App eine Neuverbindung; gelingt sie, wird ausgerollt, sonst Error-Dialog. Begruendung: Der User koennte wissen, dass ein Host inzwischen wieder erreichbar ist. |
| Rote Hosts in Uebersicht | **Nicht angezeigt** | Wir kennen die Session-Daten roter Hosts nicht, daher keine Zeilen in der Tabelle. Sobald ein Host gruen wird, fuellt sich die Tabelle automatisch. |
| Button-Layout | **Nebeneinander** statt untereinander | Konsistenz ueber alle Ansichten. Differenzierender Teil ("Ein WT" / "Pro Host") am Label-Anfang fuer truncation-sichere Anzeige. |
| Tabellen-Sortierung (Uebersicht) | **Click-to-Sort** via `DataTable.HeaderSelected`-Event + `sort()` | Textual's DataTable hat keinen Default-Click-to-Sort, aber die Implementierung ist trivial (~5 Zeilen). Default-Sortierung: Session-Name. |
| Auswahl in DataTable (Uebersicht) | **Marker-Spalte** statt native Checkboxen | DataTable hat keine eingebauten Checkboxen. Wir nutzen eine Marker-Spalte (`✓` oder leer), gesteuert ueber `t`/`a`/`i`-Shortcuts und Space. Ermoeglicht Sortierung und Zeilen-Navigation. |
| Fast-Track Persistenz ueber Neustarts | **Keine** | Auswahlen und Eingaben in Direktsession/Uebersicht werden nicht persistiert. Bei Neustart sind beide leer. Begruendung: Das sind "Intentions", keine Konfiguration. |
| Session-Liste | **SelectionList** statt einzelner Checkboxen | Navigation mit Pfeiltasten statt Tab-Springen, Invertieren mit `i` |
| Dialog-Groesse | **Automatische Hoehe/Breite** (ConfirmDialog bis 80 Zeichen) | Lange Hostnamen duerfen die Buttons nicht aus dem Bild schieben |
| Listen-Struktur links | **Zwei Zonen mit Trennern** | Obere Zone (Neuer Host → Hosts → Oeffnen) = klassischer Workflow. Untere Zone (Direktsession, Uebersicht) = losgeloeste Fast-Track-Funktionen. Trenner machen die Zugehoerigkeit visuell klar. |

---

## 12. Auslieferung

Jedes Release erscheint auf GitHub mit zwei Artefakten. Die eigenstaendige `.exe` erspart Anwendern Python und pipx; das Wheel bleibt fuer Umgebungen mit Python erhalten, etwa fuer den Start von einer Netzwerk-Freigabe, bei dem pipx die Umgebung lokal anlegt:

| Artefakt | Erzeugung | Start beim Anwender |
|---|---|---|
| `open_tmux_tabs-<version>-py3-none-any.whl` | `python -m build --wheel` | `pipx run --spec <wheel> open-tmux-tabs` oder `pipx install` — braucht Python 3.10+ und pipx |
| `open-tmux-tabs.exe` | PyInstaller (`packaging/open-tmux-tabs.spec`, Einzeldatei, Konsolenanwendung) auf einem Windows-Runner | direkt starten — kein Python noetig; Download z.B. per PowerShell `irm https://github.com/schlingensiepen/tmux-helper/releases/latest/download/open-tmux-tabs.exe -OutFile "$env:TEMP\open-tmux-tabs.exe"` |

Die `.exe` buendelt `app.tcss` und `locales/` als Daten des Pakets `open_tmux_tabs`; `find_locales_dir()` und `CSS_PATH` finden sie relativ zum Modul. Textual und Rich laden Teile ihrer Module verzoegert und werden deshalb vollstaendig eingesammelt (`collect_submodules`). Der Asset-Name der `.exe` ist versionsfrei, damit der Link `releases/latest/download/open-tmux-tabs.exe` stabil bleibt.

Der Release-Workflow (`.github/workflows/release.yml`) laeuft beim Push eines Tags `v*`: Tests, Wheel, `.exe`, SHA-256-Pruefsummen, Release-Entwurf mit allen Artefakten. Veroeffentlicht wird der Entwurf von Hand.

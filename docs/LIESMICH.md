# Open-TmuxTabs -- Kurzanleitung

Open-TmuxTabs ist eine Anwendung zum Verwalten von tmux-Sitzungen
auf entfernten Linux-Rechnern. Sie oeffnet die Sitzungen als Tabs
im Windows Terminal.

---

## Voraussetzungen

Folgende Programme muessen auf dem Windows-Rechner installiert sein
(alles ohne Administrator-Rechte moeglich):

| Programm | Installation |
|---|---|
| **Python 3.10+** | [python.org/downloads](https://www.python.org/downloads/) -- bei der Installation "Add to PATH" ankreuzen |
| **pipx** | In einer Eingabeaufforderung: `pip install pipx` |
| **Windows Terminal** | Vorinstalliert ab Windows 11, sonst [Microsoft Store](https://aka.ms/terminal) |
| **OpenSSH-Client** | Vorinstalliert ab Windows 10 (Einstellungen > Apps > Optionale Features > OpenSSH-Client) |

---

## SSH-Schluessel einrichten

Beim ersten Start des Containers wird ein privater SSH-Schluessel
angezeigt. Diesen speichern:

1. Datei `%USERPROFILE%\.ssh\clawbook` anlegen (ohne Endung)
2. Den angezeigten Schluessel hineinkopieren
3. Datei speichern

---

## SSH-Konfiguration anlegen

Damit Open-TmuxTabs den Container unter dem Namen `clawbook`
findet, muss ein Eintrag in der SSH-Konfiguration stehen.

Datei `%USERPROFILE%\.ssh\config` oeffnen (oder anlegen) und
folgenden Block einfuegen:

```
Host clawbook
    HostName localhost
    Port 2222
    User student
    IdentityFile ~/.ssh/clawbook
```

**Pruefung:** In einer Eingabeaufforderung `ssh clawbook` eingeben.
Bei der ersten Verbindung den Fingerprint mit `yes` bestaetigen.
Wenn eine Shell auf dem Container erscheint, ist alles richtig.
Mit `exit` wieder zurueck.

---

## Open-TmuxTabs starten

Doppelklick auf `start.cmd` in diesem Verzeichnis.

**Alternative ohne Python und pipx:** die eigenstaendige
`open-tmux-tabs.exe` aus dem neuesten Release laden und starten,
z.B. in PowerShell:

```powershell
irm https://github.com/schlingensiepen/tmux-helper/releases/latest/download/open-tmux-tabs.exe -OutFile "$env:TEMP\open-tmux-tabs.exe"; Start-Process "$env:TEMP\open-tmux-tabs.exe" -Wait
```

Beim ersten Start legt pipx automatisch eine lokale Umgebung an
(das dauert einige Sekunden). Danach startet die Anwendung sofort.

---

## Ersten Host eintragen

1. Die Anwendung startet mit dem Cursor im Eingabefeld
2. `clawbook` eingeben und Enter druecken
3. Der Host erscheint in der Liste und wird gruen, sobald die
   Verbindung steht
4. Die laufenden tmux-Sitzungen werden rechts angezeigt
5. Enter drueckt den Schnellstart-Button: alle Sitzungen oeffnen
   sich als Tabs im Windows Terminal

---

## Tastenkuerzel

| Taste | Aktion |
|---|---|
| `q` | Beenden |
| `n` | Neuen Host hinzufuegen |
| `o` | Zur Oeffnen-Ansicht |
| `Enter` | Schnellstart (alle Sitzungen oeffnen) |
| `t` | Sitzung an-/abwaehlen |
| `a` | Alle Sitzungen an-/abwaehlen |
| `l` | Sprache wechseln |

Weitere Tastenkuerzel stehen im Footer der Anwendung.

---

## Fehlerbehebung

| Problem | Loesung |
|---|---|
| `ssh clawbook` fragt nach Passwort | Schluessel-Datei pruefen: richtige Datei, richtige Rechte (`icacls %USERPROFILE%\.ssh\clawbook /inheritance:r /grant:r "%USERNAME%:R"`) |
| `ssh: connect to host localhost port 2222: Connection refused` | Container laeuft nicht -- `podman start clawbook-lehre` ausfuehren |
| `pipx` nicht gefunden | `pip install pipx` ausfuehren, dann Eingabeaufforderung neu oeffnen |
| Anwendung startet, aber keine Sitzungen sichtbar | Auf dem Container `tmux new -s arbeit` ausfuehren, um eine Sitzung zu erzeugen |

---

## Weitere Dokumentation

Die vollstaendige Dokumentation (Benutzerhandbuch, technische
Spezifikation, Architektur) liegt im Repository:
[github.com/schlingensiepen/tmux-helper](https://github.com/schlingensiepen/tmux-helper)

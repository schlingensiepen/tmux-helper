# Testplan -- Open-TmuxTabs v2.0.0

**Datum:** 2026-08-03
**Ziel:** Vollstaendiger manueller Test aller Features vor Screenshot-Erstellung
**Plattform:** Windows 10/11 mit Windows Terminal, OpenSSH, Python 3.10+

---

## Voraussetzungen

- Mindestens 2 erreichbare SSH-Hosts mit tmux
- Mindestens 1 Host, der absichtlich NICHT erreichbar ist (oder falscher Hostname)
- SSH-Key auf den erreichbaren Hosts deployed
- App installiert: `open-tmux-tabs.exe` aus dem Release oder `pip install -e ".[dev]"`
- Keine vorherige `hosts.json` (fuer Erster-Start-Test)

---

## Testfall-Kategorien

| Kategorie | ID-Praefix | Testfaelle |
|---|---|---|
| Erster Start | S | 4 |
| Host hinzufuegen | H | 6 |
| Host-Detail (verbunden) | D | 10 |
| Host-Fehler | E | 5 |
| Oeffnen-Ansicht | O | 7 |
| Direktsession | DS | 8 |
| Uebersicht | SA | 7 |
| Globale Shortcuts | G | 10 |
| Sprachwechsel | L | 4 |
| Fehlerbehandlung | F | 4 |
| Layout und Darstellung | V | 5 |
| Edge Cases | X | 5 |
| **Gesamt** | | **75** |

---

## S -- Erster Start (ohne gespeicherte Hosts)

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| S-01 | Erster Start ohne hosts.json | `hosts.json` loeschen oder umbenennen, App starten | Auswahl steht auf "+ Neuer Host", Cursor im Eingabefeld |
| S-02 | Header sichtbar | App starten | Oben links "Open-TmuxTabs", rechts Sprachanzeige z.B. `[en] English` |
| S-03 | Footer sichtbar | App starten | Unten Shortcuts sichtbar: q, n, o, x, +, -, l, Delete |
| S-04 | Zwei-Zonen-Struktur | App starten | Host-Liste zeigt: "+ New host", Trenner, ">> Open", Trenner, "Direct session", "Show all" |

## H -- Host hinzufuegen

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| H-01 | Host per Eingabefeld | SSH-Ziel eingeben (z.B. `root@server`), Enter | Host erscheint in Liste, hellblau, wechselt zu gruen oder rot |
| H-02 | Host per Button | SSH-Ziel eingeben, Button "Add host" klicken | Wie H-01 |
| H-03 | SSH-Alias | SSH-Config-Alias eingeben (z.B. `devbox`), Enter | Host erscheint mit aufgeloestem Namen (z.B. `root@devbox`) |
| H-04 | Erreichbarer Host wird gruen | Erreichbaren Host hinzufuegen | Farbe wechselt von blau zu gruen, Sessions werden in Detail-Ansicht aufgelistet |
| H-05 | Nicht erreichbarer Host wird rot | Falschen Hostnamen eingeben, Enter | Farbe wechselt von blau zu rot, Fehler-Ansicht zeigt Fehlermeldung |
| H-06 | Host wird persistiert | Host hinzufuegen, App beenden, App neu starten | Host ist in der Liste vorhanden |

## D -- Host-Detail (verbundener Host)

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| D-01 | Sessions angezeigt | Gruenen Host auswaehlen (Enter) | Laufende tmux-Sessions werden als Checkboxen aufgelistet |
| D-02 | Toggle (t) | Session markieren, `t` druecken | Session wird an-/abgewaehlt |
| D-03 | Toggle All (a) | `a` druecken | Alle Sessions werden an-/abgewaehlt |
| D-04 | Invert (i) | Einige Sessions anwaehlen, `i` druecken | Auswahl wird invertiert |
| D-05 | Jump start (j) | Session markieren, `j` druecken | Genau diese Session oeffnet sich in einem WT-Tab |
| D-06 | Reload (r) | `r` druecken | Session-Liste wird neu vom Host abgerufen, Host blinkt kurz blau |
| D-07 | Neue Session eingeben | Tab ins Eingabefeld, gueltigen Namen eingeben | Kein Fehler, Name wird akzeptiert |
| D-08 | Ungueltiger Session-Name | Ungueltige Zeichen eingeben (z.B. Leerzeichen, Sonderzeichen) | Warnmeldung unter dem Eingabefeld |
| D-09 | Doppelter Session-Name | Existierenden Session-Namen eingeben | Warnung "Session named 'X' already exists" |
| D-10 | Auswahl bleibt beim Wechsel | Sessions anwaehlen, zu anderem Host wechseln, zurueckwechseln | Auswahl und Eingabefeld-Text sind noch da |

## E -- Host-Fehler (fehlgeschlagener Host)

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| E-01 | Fehler-Ansicht | Roten Host auswaehlen (Enter) | Hostname, Fehlermeldung, drei Buttons sichtbar |
| E-02 | Reconnect (r) | In Fehler-Ansicht `r` druecken | Neuer Verbindungsversuch, Host wird blau |
| E-03 | Setup host (s) | In Fehler-Ansicht `s` druecken | Interaktives WT-Fenster oeffnet sich fuer SSH-Key-Deployment |
| E-04 | Host loeschen (Delete) | In Fehler-Ansicht "Delete" klicken | Sicherheitsabfrage erscheint, bei "Yes" wird Host entfernt |
| E-05 | Loeschen abbrechen | Sicherheitsabfrage mit "No" oder Esc beantworten | Host bleibt in der Liste |

## O -- Oeffnen-Ansicht

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| O-01 | Startansicht | App mit gespeicherten Hosts starten | Auswahl auf ">> Open", Schnellstart-Button fokussiert |
| O-02 | Schnellstart (Enter) | Auf ">> Open", Enter druecken | Alle Sessions aller gruenen Hosts oeffnen sich in WT-Fenstern (eins pro Host) |
| O-03 | Schnellstart wartet | Waehrend Hosts noch blau sind, Enter druecken | Meldung "Waiting for pending connections...", dann Start |
| O-04 | Zusammenfassung | Sessions bei verschiedenen Hosts auswaehlen, zur Open-Ansicht wechseln | Zusammenfassung zeigt alle ausgewaehlten Sessions gruppiert nach Host, bestehende/neue markiert |
| O-05 | Ein WT - Button | Sessions auswaehlen, "One WT" Button klicken | Alle Sessions in EINEM WT-Fenster als Tabs |
| O-06 | Pro Host - Button | Sessions auswaehlen, "Per host" Button klicken | Pro Host ein eigenes WT-Fenster |
| O-07 | Reset nach Oeffnen | Sessions auswaehlen, oeffnen | Alle Checkboxen leer, Eingabefelder leer, Hosts werden neu geladen |

## DS -- Direktsession

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| DS-01 | Ansicht oeffnen (+) | `+` druecken | Direktsession-Ansicht erscheint: Host-Auswahlliste, Eingabefeld, Zusammenfassung, Buttons |
| DS-02 | Hosts mit Farbstatus | In Direktsession-Ansicht | Hosts zeigen [GREEN]/[BLUE]/[RED] Labels |
| DS-03 | Host-Auswahl (t/a/i) | Hosts mit `t`/`a`/`i` an-/abwaehlen | Auswahl funktioniert, Zusammenfassung aktualisiert sich |
| DS-04 | Session-Namen eingeben | Im Eingabefeld Namen eingeben | Zusammenfassung zeigt pro Host+Session, ob "new" oder "existing" |
| DS-05 | Execute - Ein WT (j) | Hosts + Sessions waehlen, `j` druecken | Alle Sessions in einem WT-Fenster, Sessions werden ggf. erzeugt |
| DS-06 | Execute - Pro Host | Hosts + Sessions waehlen, "Per host" Button klicken | Pro Host ein WT-Fenster |
| DS-07 | Kein Reset | Nach Execute | Auswahl und Text bleiben bestehen, Zusammenfassung aktualisiert "existing" statt "new" |
| DS-08 | Roter Host mit Reconnect | Roten Host anwaehlen, Session-Namen eingeben, Execute | Reconnect-Versuch, bei Erfolg wird deployed, bei Misserfolg Fehler-Dialog |

## SA -- Uebersicht (Show All)

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| SA-01 | Ansicht oeffnen (-) | `-` druecken | Uebersicht-Ansicht: DataTable mit allen Sessions aller gruenen Hosts |
| SA-02 | Click-to-Sort | Auf Spalten-Header "Host" oder "Session" klicken | Tabelle wird nach dieser Spalte sortiert |
| SA-03 | Toggle (t/a/i) | Zeilen mit `t`/`a`/`i` markieren | Marker-Spalte zeigt check/leer, Buttons werden aktiv/inaktiv |
| SA-04 | Jump start (j) | Zeile markieren, `j` druecken | Genau diese Session oeffnet sich in einem WT-Tab |
| SA-05 | Ein WT - Button | Zeilen markieren, "One WT" Button klicken | Alle markierten Sessions in einem WT-Fenster |
| SA-06 | Pro Host - Button | Zeilen markieren, "Per host" Button klicken | Pro Host ein eigenes WT-Fenster |
| SA-07 | Leerzustand | Alle Hosts rot oder blau | Tabelle zeigt "Waiting for connections...", fuellt sich automatisch bei gruen |

## G -- Globale Shortcuts

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| G-01 | q (Quit) | `q` druecken | App beendet sich |
| G-02 | n (New host) | `n` druecken | Auswahl springt zu "+ New host", Fokus im Eingabefeld |
| G-03 | o (Open) | `o` druecken | Auswahl springt zu ">> Open", Schnellstart-Button fokussiert |
| G-04 | x (Open all) | `x` druecken | Sofort alle Sessions oeffnen (wie Schnellstart-Button) |
| G-05 | + (Direct session) | `+` druecken | Auswahl springt zu "Direct session" |
| G-06 | - (Show all) | `-` druecken | Auswahl springt zu "Show all" |
| G-07 | l (Language) | `l` druecken | Sprachwahl-Dialog oeffnet sich |
| G-08 | Delete | Host auswaehlen, `Delete` druecken | Sicherheitsabfrage, bei "Yes" wird Host entfernt |
| G-09 | Pfeiltasten | In Host-Liste hoch/runter navigieren | Detail-Bereich aktualisiert sich sofort, Fokus bleibt in Liste |
| G-10 | Enter in Liste | Host markieren, Enter druecken | Fokus wechselt in den Detail-Bereich rechts |

## L -- Sprachwechsel

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| L-01 | Dialog oeffnen | `l` druecken | Modaler Dialog mit allen 7 Sprachen (en, de, fr, es, eo, tlh, ur) |
| L-02 | Sprache wechseln + Neustart | Andere Sprache waehlen, OK, "Yes" bei Neustart-Frage | App startet neu, alle Labels in neuer Sprache, Header zeigt z.B. `[de] Deutsch` |
| L-03 | Sprache persistiert | Sprache wechseln, App beenden, neu starten | App startet in der gewaehlten Sprache |
| L-04 | Shortcuts bleiben gleich | Sprache auf Klingonisch wechseln | `q` ist immer noch Quit, `n` immer noch New host etc. Nur Footer-Texte aendern sich |

## F -- Fehlerbehandlung

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| F-01 | SSH-Fehler-Dialog | Aktion auf nicht erreichbarem Host ausloesen | Modaler Fehler-Dialog mit Titel, stderr-Ausgabe, OK-Button |
| F-02 | Fehler-Dialog schliessen | Fehler-Dialog mit OK, Enter oder Esc schliessen | Dialog schliesst, App reagiert normal |
| F-03 | Parallele Fehler | Mehrere nicht erreichbare Hosts gleichzeitig | Fehler-Dialoge erscheinen nacheinander (seriell, nicht gestapelt) |
| F-04 | Korrupte hosts.json | `hosts.json` mit ungueltigem Inhalt ueberschreiben, App starten | App startet mit leerer Host-Liste, kein Crash |

## V -- Layout und Darstellung

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| V-01 | Zwei-Zonen-Trenner | App mit Hosts starten | Trenner zwischen New Host/Hosts und Open/Fast-Track sichtbar |
| V-02 | Buttons nebeneinander | Open-Ansicht, Direktsession, Uebersicht pruefen | "Ein WT" und "Pro Host" Buttons stehen nebeneinander, Labels lesbar |
| V-03 | Hostname-Truncation | Host mit sehr langem FQDN hinzufuegen | Name wird gekuerzt, mindestens 5 Domain-Zeichen sichtbar |
| V-04 | Farbstatus | Hosts in verschiedenen Zustaenden | Blau (pending), Gruen (connected), Rot (failed) klar unterscheidbar |
| V-05 | Fensterbreite | Fenster schmal ziehen (ca. 80 Spalten) | Layout bleibt funktional, kein Ueberlauf |

## X -- Edge Cases

| ID | Testfall | Schritte | Erwartetes Ergebnis |
|---|---|---|---|
| X-01 | Host ohne Sessions | Host verbinden, der keine tmux-Sessions hat | Leere Session-Liste, Eingabefeld fuer neue Sessions funktioniert |
| X-02 | Alle Hosts rot | Nur nicht-erreichbare Hosts gespeichert | Open-Ansicht: Schnellstart oeffnet nichts (kein WT). Uebersicht: "Waiting for connections..." |
| X-03 | Viele Sessions | Host mit >20 tmux-Sessions | Session-Liste scrollbar, Toggle All/Invert funktioniert korrekt |
| X-04 | Gleichen Host doppelt | Gleiche SSH-Adresse nochmal eingeben | Host wird (erneut) hinzugefuegt (kein Duplikat-Schutz spezifiziert) |
| X-05 | App nach Oeffnen weiterverwenden | Sessions oeffnen, dann sofort weitere auswaehlen und nochmal oeffnen | App bleibt funktional, keine Haenger, Hosts werden neu geladen |

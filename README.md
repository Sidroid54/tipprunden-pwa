# Tasmania Hackentrick

Eine installierbare Ranglisten-Web-App für die private Fußballrunde
**Tasmania Hackentrick**. Die App verbindet die Spieltagsergebnisse aus dem
Kicktipp-Tippspiel (TS) und dem kicker Managerspiel Interactive (MS) zu einer
gemeinsamen Spieltags- und Saisonwertung.

## Funktionen

- gemeinsame Wertung aus Kicktipp und kicker Managerspiel
- Spieltagsrangliste mit Mann des Tages
- Saison-Gesamtwertung mit TS-, MS- und Gesamtpunkten
- Anzeige von Tagessiegen und Rangtrends
- persönliche Hervorhebung des eigenen Spielers im Browser
- responsive Darstellung für Desktop und Mobilgeräte
- als Progressive Web App (PWA) installierbar
- statische Bereitstellung, zum Beispiel über GitHub Pages

## Wertungssystem

In beiden Wettbewerben werden die Rohpunkte eines Spieltags zunächst in
Ranglistenpunkte umgerechnet:

| Rang | Wertungspunkte |
| ---: | ---: |
| 1 | 10 |
| 2 | 8 |
| 3 | 7 |
| 4 | 6 |
| 5 | 5 |
| 6 | 4 |
| 7 | 3 |
| 8 | 2 |
| 9 | 1 |

Bei einem Gleichstand erhalten alle betroffenen Teilnehmer denselben Rang und
dieselbe Punktzahl. Der nachfolgende Rang wird entsprechend übersprungen, zum
Beispiel `1, 1, 3`.

Die Spieltagspunkte eines Teilnehmers ergeben sich aus:

```text
TS-Punkte + MS-Punkte = Spieltagspunkte
```

Die Saisonwertung summiert diese Punkte über alle vorhandenen Spieltage.

## Projektstruktur

```text
tipprunden-pwa/
├── backend/
│   ├── data/                         Importierte und kombinierte Spieltage
│   ├── batch_import.py               Import mehrerer Spieltage
│   ├── config.py                     Saison, Teilnehmer und Wertung
│   ├── combine_matchday.py           Zusammenführen beider Wettbewerbe
│   ├── process_kicker_matchday.py    Import des Managerspiels
│   ├── process_kicktipp_matchday.py  Import des Tippspiels
│   └── save_*_login*.py              Speichern der Browser-Anmeldungen
├── docs/
│   ├── assets/                       Logos und App-Symbole
│   ├── app.js                        Auswertungs- und Bedienlogik
│   ├── data.json                     Öffentliche Ranglistendaten
│   ├── index.html                    Semantische HTML-Oberfläche
│   ├── manifest.json                 PWA-Konfiguration
│   ├── service-worker.js             PWA-Caching
│   └── styles.css                    Gestaltung und responsives Layout
└── README.md
```

Das Backend ist kein dauerhaft laufender Webserver. Die Python-Skripte rufen
die Daten mit Playwright ab und schreiben JSON-Dateien. Das Frontend ist eine
statische HTML/CSS/JavaScript-Anwendung und liest ausschließlich
`docs/data.json`.

## Voraussetzungen

- Python 3.10 oder neuer
- Microsoft Edge
- ein Zugang zur verwendeten Kicktipp-Runde
- ein Zugang zur verwendeten kicker-Managerspielgruppe

## Lokale Einrichtung

Im Projektverzeichnis eine virtuelle Python-Umgebung erstellen und Playwright
installieren:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/Activate.ps1
python -m pip install playwright
```

Die Importskripte starten Microsoft Edge über den von Playwright unterstützten
`msedge`-Kanal. Ein separates JavaScript-Build-System oder `npm install` ist
für das Frontend nicht erforderlich.

## Anmeldesitzungen

Für den Datenabruf werden angemeldete Browser-Sitzungen als lokale Dateien
benötigt:

```text
backend/secrets/kicker-auth.json
backend/secrets/kicktipp-auth.json
```

Für kicker kann eine Sitzung über das folgende Skript angelegt werden:

```powershell
python backend/save_kicker_login.py
```

Das Skript öffnet Edge. Nach der Anmeldung und dem Öffnen der Gruppenrangliste
wird die Sitzung durch Drücken von Enter gespeichert.

Alternativ stehen für kicker und Kicktipp CDP-Skripte bereit. Diese verbinden
sich mit einer bereits angemeldeten Edge-Instanz, die mit aktiviertem Remote
Debugging auf Port `9222` gestartet wurde:

```powershell
python backend/save_kicker_login_cdp.py
python backend/save_kicktipp_login_cdp.py
```

Die Dateien in `backend/secrets/` enthalten sensible Sitzungsdaten. Der Ordner
ist über `.gitignore` vom Repository ausgeschlossen und darf nicht
veröffentlicht werden.

## Spieltage importieren

Der Mehrfachimport ist der zentrale Ablauf für einen oder mehrere Spieltage.
Er muss aus dem Verzeichnis `backend` gestartet werden:

```powershell
cd backend
python batch_import.py --start 32 --end 34
```

Für einen einzelnen Spieltag können Start und Ende identisch sein:

```powershell
python batch_import.py 34
```

Optional lässt sich die Pause zwischen zwei Spieltagen festlegen:

```powershell
python batch_import.py --start 1 --end 34 --pause 3
```

Der Import führt für jeden Spieltag folgende Schritte aus:

1. kicker-Managerspiel abrufen und bewerten
2. Kicktipp-Ergebnisse abrufen und bewerten
3. beide Quellen auf genau neun Teilnehmer prüfen
4. Ergebnisse zu einer Spieltagswertung kombinieren
5. kombinierte Datei unter `backend/data/` speichern
6. den Spieltag in `docs/data.json` ergänzen oder ersetzen
7. den Ablauf in `backend/data/batch_import_log.json` protokollieren

Die Dateien werden atomisch geschrieben: Eine bestehende Datei wird erst
ersetzt, nachdem die neue JSON-Datei vollständig auf den Datenträger
geschrieben wurde. Die beiden Plattformabrufe müssen erfolgreich sein, bevor
ihre Ergebnisdateien aktualisiert werden. Ungültige oder unvollständige
kombinierte Daten gelangen nicht in `docs/data.json`.

Bei einem Browser- oder Seitenfehler legt der Import Diagnose-Screenshots unter
`backend/diagnostics/` ab und vermerkt deren Pfade im Importprotokoll. Diese
Screenshots können private Informationen enthalten und werden deshalb von Git
ignoriert.

Die einzelnen Verarbeitungsschritte können bei Bedarf ebenfalls mit einem
frei wählbaren Spieltag aufgerufen werden:

```powershell
python process_kicker_matchday.py 34
python process_kicktipp_matchday.py 34
python combine_matchday.py 34
```

Für den regulären Import sollte `batch_import.py` verwendet werden, weil es
alle Schritte in der richtigen Reihenfolge ausführt.

## Frontend lokal öffnen

Da das Frontend Daten per `fetch()` lädt, sollte es über einen lokalen
HTTP-Server und nicht direkt als Datei geöffnet werden:

```powershell
cd docs
python -m http.server 8000
```

Danach ist die App unter <http://localhost:8000> erreichbar.

Die App lädt `data.json` ohne Browser-Cache. Der selbst gewählte Spieler wird
nur auf dem jeweiligen Gerät im `localStorage` des Browsers gespeichert.

## Tests ausführen

Die automatisierten Backend-Tests verwenden das in Python enthaltene
`unittest` und benötigen keine zusätzliche Testbibliothek:

```powershell
cd backend
python -m unittest discover -v
```

Die Tests prüfen unter anderem die Punktevergabe, Gleichstände, gültige
Spieltagsgrenzen, atomisches Schreiben, die Veröffentlichungsvalidierung und
das Zusammenführen eines vollständig gespeicherten Spieltags. Sie rufen dabei
weder kicker noch Kicktipp auf.

## Veröffentlichung

Der Ordner `docs/` ist für eine statische Veröffentlichung vorbereitet. Bei
GitHub Pages kann in den Repository-Einstellungen der `docs`-Ordner des
gewünschten Branches als Quelle ausgewählt werden. Nach einem Push werden die
enthaltene Oberfläche und die aktualisierte `data.json` veröffentlicht.

Vor dem Commit empfiehlt sich eine Kontrolle der Änderungen:

```powershell
git status
git diff
```

Insbesondere dürfen `backend/secrets/`, lokale `.env`-Dateien und virtuelle
Python-Umgebungen niemals eingecheckt werden.

## Aktuelle technische Hinweise

- Saison-, Gruppen-, Teilnehmer- und Wertungsdaten stehen zentral in
  `backend/config.py`.
- Das Frontend ist in `docs/index.html`, `docs/styles.css` und `docs/app.js`
  aufgeteilt und benötigt keinen Build-Schritt.
- Die Dateien in `backend/data/` dienen als nachvollziehbare Quelldaten für
  die veröffentlichte `docs/data.json`.
- Der Service Worker speichert die App-Oberfläche und den letzten erfolgreich
  geladenen Datenstand. Ranglistendaten werden online bevorzugt aus dem Netz
  geladen; offline kennzeichnet die App den zwischengespeicherten Stand.
- Die Backend-Tests arbeiten mit lokal gespeicherten Beispieldaten und führen
  keinen Live-Abruf der externen Plattformen durch.

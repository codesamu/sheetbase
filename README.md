# Sheetbase
### Datasheet + Database, Combined.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-Web_App-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-Database-336791?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLAlchemy-ORM-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" />
  <img src="https://img.shields.io/badge/TailwindCSS-UI-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white" />
  <img src="https://img.shields.io/badge/OpenRouter-AI_API-8A2BE2?style=for-the-badge" />
  <img src="https://img.shields.io/badge/PyMuPDF-PDF_Processing-009688?style=for-the-badge" />
</p>

<p align="center">
  <b>Datenblaetter einlesen, Bauteile speichern und alles ueber PostgreSQL verwalten.</b>
</p>

---

## Was ist Sheetbase?

Sheetbase ist eine kleine Flask-Web-App fuer elektronische Bauteildaten.
Die App kann Daten aus PostgreSQL anzeigen und Datenblaetter per PDF einlesen.
Fuer die PDF-Auswertung wird OpenRouter verwendet, damit aus dem Datenblatt
SQL-INSERT-Statements fuer die Datenbank erzeugt werden koennen.

Kurz gesagt:

- Flask startet die Webseite.
- PostgreSQL speichert die Bauteildaten.
- SQLAlchemy verbindet Python mit der Datenbank.
- PyMuPDF liest Text aus PDFs.
- OpenRouter hilft beim Umwandeln von Datenblatt-Text in SQL.

## PostgreSQL zuerst herunterladen

PostgreSQL muss installiert sein, bevor die App richtig laufen kann.

Download:

[PostgreSQL herunterladen](https://www.postgresql.org/download/)

Beim Installieren unbedingt das Passwort fuer den PostgreSQL-Admin-User
`postgres` merken. Das braucht man spaeter zum Erstellen der Datenbank und des
Users.

## Tech Stack

| Bereich | Technik |
| --- | --- |
| Backend | Python, Flask |
| Datenbank | PostgreSQL |
| ORM | Flask-SQLAlchemy, SQLAlchemy |
| PostgreSQL-Treiber | psycopg2 |
| PDF-Verarbeitung | PyMuPDF |
| KI/API | OpenRouter |
| Frontend | HTML Templates, Tailwind CSS |

## Aufbau

```text
                +-------------------+
                |    Tailwind UI    |
                +---------+---------+
                          |
                       Flask App
                          |
        +-----------------+-----------------+
        |                 |                 |
   SQLAlchemy        OpenRouter AI        PyMuPDF
        |                 |                 |
        +------------ PostgreSQL ----------+
```

## Projektstruktur

```text
sheetbase/
+-- app.py
+-- pdf_extractor.py
+-- prompt.txt
+-- requirements.txt
+-- test-conn.py
+-- test-post.py
+-- templates/
|   +-- index.html
|   +-- docs.html
|   +-- favicon.svg
|   +-- data-sheet.ico
+-- README.md
```

## Wichtige Standardwerte

Die Datenbankverbindung steht aktuell direkt in `app.py`, `test-conn.py` und
`test-post.py`.

```text
postgresql+psycopg2://flaskusr:sheetbase@192.168.1.21:5432/datasheetdb
```

Die App erwartet also diese Daten:

| Einstellung | Wert |
| --- | --- |
| Datenbank | PostgreSQL |
| Host | `192.168.1.21` |
| Port | `5432` |
| Datenbankname | `datasheetdb` |
| User | `flaskusr` |
| Passwort | `sheetbase` |

Wenn PostgreSQL auf demselben PC laeuft, ist `localhost` normalerweise
einfacher. Dann muss aber der Host in den Python-Dateien von `192.168.1.21` auf
`localhost` geaendert werden. Wenn nichts am Code geaendert werden soll, muss
PostgreSQL wirklich unter `192.168.1.21` erreichbar sein.

## Voraussetzungen

Installiert werden muessen:

1. Python 3.11 oder neuer
2. PostgreSQL
3. Git, falls das Projekt aus einem Repository geklont wird
4. Ein OpenRouter API-Key, wenn der PDF-Import verwendet werden soll

Python Download:

[Python herunterladen](https://www.python.org/downloads/)

PostgreSQL Download:

[PostgreSQL herunterladen](https://www.postgresql.org/download/)

## 1. Projektordner oeffnen

Windows PowerShell:

```powershell
cd C:\Pfad\zu\sheetbase
```

Beispiel:

```powershell
cd C:\Users\Max\Desktop\Schule\sheetbase
```

Linux/macOS:

```bash
cd /pfad/zu/sheetbase
```

## 2. Virtuelle Python-Umgebung erstellen

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Falls PowerShell das Aktivieren blockiert:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Danach nochmal aktivieren:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Wenn alles passt, steht vorne im Terminal `(.venv)`.

## 3. Python-Pakete installieren

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

In `requirements.txt` stehen:

```text
flask
sqlalchemy
flask_sqlalchemy
psycopg2-binary
requests
pymupdf
```

## 4. PostgreSQL starten oder pruefen

### Windows

Pruefen, ob PostgreSQL laeuft:

```powershell
Get-Service | Where-Object { $_.Name -like "*postgres*" -or $_.DisplayName -like "*PostgreSQL*" }
```

Falls der Dienst nicht laeuft:

```powershell
Start-Service postgresql-x64-18
```

Die Zahl kann je nach installierter Version anders sein, zum Beispiel
`postgresql-x64-17` oder `postgresql-x64-16`.

Wenn `psql` nicht erkannt wird, den ganzen Pfad verwenden:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost
```

Bei einer anderen PostgreSQL-Version die Zahl im Pfad anpassen.

### Linux

```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### macOS

Wenn PostgreSQL mit Homebrew installiert wurde:

```bash
brew services list
brew services start postgresql
```

## 5. Datenbank-User und Datenbank erstellen

Als PostgreSQL-Admin einloggen.

Windows:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost
```

Linux:

```bash
sudo -u postgres psql
```

macOS:

```bash
psql -U postgres
```

Dann diese SQL-Befehle ausfuehren:

```sql
CREATE USER flaskusr WITH PASSWORD 'sheetbase';
CREATE DATABASE datasheetdb OWNER flaskusr ENCODING 'UTF8';
GRANT ALL PRIVILEGES ON DATABASE datasheetdb TO flaskusr;
```

Mit `psql` fertig:

```sql
\q
```

Falls der User schon existiert:

```sql
ALTER USER flaskusr WITH PASSWORD 'sheetbase';
```

Falls die Datenbank schon existiert:

```sql
ALTER DATABASE datasheetdb OWNER TO flaskusr;
GRANT ALL PRIVILEGES ON DATABASE datasheetdb TO flaskusr;
```

## 6. Richtigen Datenbank-Host verwenden

Die App sucht PostgreSQL hier:

```text
192.168.1.21:5432
```

Es gibt zwei sinnvolle Varianten.

### Variante A: Host aus dem Code verwenden

Diese Variante passt, wenn PostgreSQL wirklich unter `192.168.1.21` erreichbar
sein soll.

In `postgresql.conf`:

```text
listen_addresses = '*'
```

In `pg_hba.conf` zum Beispiel:

```text
host    datasheetdb    flaskusr    192.168.1.0/24    scram-sha-256
```

Danach PostgreSQL neu starten.

Windows:

```powershell
Restart-Service postgresql-x64-18
```

Linux:

```bash
sudo systemctl restart postgresql
```

macOS mit Homebrew:

```bash
brew services restart postgresql
```

Verbindung testen:

```bash
psql -U flaskusr -d datasheetdb -h 192.168.1.21 -p 5432 -c "SELECT current_user, current_database();"
```

Windows mit vollem `psql`-Pfad:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U flaskusr -d datasheetdb -h 192.168.1.21 -p 5432 -c "SELECT current_user, current_database();"
```

### Variante B: Lokal mit localhost arbeiten

Diese Variante ist am einfachsten, wenn PostgreSQL nur auf dem eigenen Rechner
laeuft.

Dazu in `app.py`, `test-conn.py` und `test-post.py` den Host aendern:

```text
192.168.1.21
```

zu:

```text
localhost
```

Dann lautet die Verbindung:

```text
postgresql+psycopg2://flaskusr:sheetbase@localhost:5432/datasheetdb
```

Verbindung testen:

```bash
psql -U flaskusr -d datasheetdb -h localhost -p 5432 -c "SELECT current_user, current_database();"
```

## 7. Tabellen erstellen

Die Tabellen werden von der App nicht automatisch angelegt. Das muss einmal in
PostgreSQL gemacht werden.

Als App-User in die Datenbank einloggen.

Windows:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U flaskusr -d datasheetdb -h 192.168.1.21
```

Linux/macOS:

```bash
psql -U flaskusr -d datasheetdb -h 192.168.1.21
```

Wenn `localhost` verwendet wird, `192.168.1.21` durch `localhost` ersetzen.

Dann diese Tabellen anlegen:

```sql
CREATE TABLE IF NOT EXISTS opv (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    power_supply_voltage TEXT,
    input_offset_voltage TEXT,
    input_offset_current TEXT,
    input_common_mode_voltage_range TEXT,
    large_signal_open_loop_gain TEXT,
    input_bias_current TEXT,
    output_voltage_high_low_limit TEXT,
    output_source_current TEXT,
    power_supply_current TEXT
);

CREATE TABLE IF NOT EXISTS bjt (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    bjt_type TEXT,
    dc_current_gain_hfe TEXT,
    collector_emitter_voltage TEXT,
    collector_base_voltage TEXT,
    emitter_base_voltage TEXT,
    base_emitter_on_voltage TEXT
);

CREATE TABLE IF NOT EXISTS mosfet (
    id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL,
    mosfet_type TEXT,
    drain_source_voltage TEXT,
    gate_source_voltage TEXT,
    continuous_drain_current TEXT,
    gate_threshold_voltage TEXT
);
```

Tabellen pruefen:

```sql
\dt
```

`psql` verlassen:

```sql
\q
```

## 8. OpenRouter API-Key setzen

Ohne OpenRouter-Key kann die Webseite starten, aber der PDF-Import mit
KI-Auswertung funktioniert nicht.

Die App liest diesen Wert:

```text
OPENROUTER_API_KEY
```

Windows PowerShell, nur fuer das aktuelle Terminal:

```powershell
$env:OPENROUTER_API_KEY="dein-openrouter-api-key"
```

Windows PowerShell, dauerhaft fuer neue Terminals:

```powershell
setx OPENROUTER_API_KEY "dein-openrouter-api-key"
```

Linux/macOS, nur fuer das aktuelle Terminal:

```bash
export OPENROUTER_API_KEY="dein-openrouter-api-key"
```

Linux/macOS, dauerhaft fuer Bash:

```bash
echo 'export OPENROUTER_API_KEY="dein-openrouter-api-key"' >> ~/.bashrc
source ~/.bashrc
```

## 9. App starten

Virtuelle Umgebung aktivieren und App starten.

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

Linux/macOS:

```bash
source .venv/bin/activate
python app.py
```

Danach im Browser oeffnen:

```text
http://127.0.0.1:5000
```

## 10. Installation testen

Diese Seiten pruefen:

```text
http://127.0.0.1:5000/
http://127.0.0.1:5000/docs
http://127.0.0.1:5000/test-db
```

Wenn die Datenbankverbindung stimmt, kommt bei `/test-db`:

```json
{
  "database": "connected"
}
```

Die Daten-Endpoints:

```text
http://127.0.0.1:5000/data/opv
http://127.0.0.1:5000/data/bjt
http://127.0.0.1:5000/data/mosfet
```

Am Anfang sind sie normalerweise leer:

```json
[]
```

## Test-Skripte

Im Projekt liegen zwei Testdateien:

| Datei | Was sie macht |
| --- | --- |
| `test-conn.py` | Testet die Verbindung und fuegt einen OPV-Testeintrag ein |
| `test-post.py` | Fuegt Beispielwerte fuer OPV, BJT und MOSFET ein |

Nur ausfuehren, wenn Testdaten in der Datenbank okay sind:

```bash
python test-conn.py
python test-post.py
```

## Fehlerbehebung

### `psql` wird nicht erkannt

Den ganzen Pfad verwenden:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe"
```

Oder den PostgreSQL-`bin`-Ordner zu PATH hinzufuegen:

```text
C:\Program Files\PostgreSQL\18\bin
```

### Passwort stimmt nicht

Passwort fuer den App-User neu setzen:

```sql
ALTER USER flaskusr WITH PASSWORD 'sheetbase';
```

### Verbindung zur Datenbank klappt nicht

Pruefen:

1. Laeuft PostgreSQL?
2. Stimmt der Host, also `192.168.1.21` oder `localhost`?
3. Ist Port `5432` erreichbar?
4. Erlaubt `pg_hba.conf` die Verbindung?
5. Blockiert die Firewall den Zugriff?

### `relation does not exist`

Dann fehlen die Tabellen. Den Abschnitt `Tabellen erstellen` nochmal ausfuehren.

### PDF-Import klappt nicht

Pruefen:

1. Ist `OPENROUTER_API_KEY` gesetzt?
2. Hat der PC Internet?
3. Ist der OpenRouter-Key gueltig?
4. Hat das PDF lesbaren Text?
5. Existieren die Tabellen in PostgreSQL?

### Port 5000 ist belegt

Ein anderes Programm nutzt Port `5000`. Dieses Programm schliessen oder den Port
in `app.py` aendern.

## Nuetzliche Befehle

Python-Version anzeigen:

```bash
python --version
```

Installierte Pakete anzeigen:

```bash
pip list
```

Datenbankverbindung testen:

```bash
psql -U flaskusr -d datasheetdb -h 192.168.1.21 -p 5432
```

App starten:

```bash
python app.py
```

## Hinweise

- Keine echten API-Keys committen.
- Das virtuelle Environment gehoert nicht ins Repository.
- Die Datenbank-URL ist aktuell direkt in den Python-Dateien eingetragen.
- Die PostgreSQL-Tabellen muessen zu den SQLAlchemy-Modellen in `app.py` passen.
- `prompt.txt` enthaelt die Regeln fuer die SQL-Erzeugung aus Datenblaettern.

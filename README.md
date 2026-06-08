# Sheetbase

Sheetbase is a local Flask web application for storing, viewing and importing
electronic component data from datasheets. The application uses PostgreSQL as
its database, SQLAlchemy as ORM, PyMuPDF for PDF text extraction and OpenRouter
for AI-assisted SQL generation from datasheets.

## Tech Stack

| Area | Technology |
| --- | --- |
| Backend | Python, Flask |
| Database | PostgreSQL |
| ORM | Flask-SQLAlchemy, SQLAlchemy |
| PostgreSQL driver | psycopg2 |
| PDF extraction | PyMuPDF |
| AI API | OpenRouter |
| Frontend | HTML templates, Tailwind CSS |

## Project Structure

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

## Default Configuration

The database connection is currently configured directly in `app.py`,
`test-conn.py` and `test-post.py`:

```text
postgresql+psycopg2://flaskusr:sheetbase@192.168.1.21:5432/datasheetdb
```

That means the application expects:

| Setting | Value |
| --- | --- |
| Database system | PostgreSQL |
| Host | `192.168.1.21` |
| Port | `5432` |
| Database | `datasheetdb` |
| User | `flaskusr` |
| Password | `sheetbase` |

Important: If PostgreSQL runs on the same computer, the easiest setup is to
make PostgreSQL reachable at the host used by the app, or to update the
connection string in the Python files to use `localhost`.

## Requirements

Install these programs first:

1. Python 3.11 or newer
2. PostgreSQL
3. Git, optional but recommended
4. An OpenRouter API key, required for PDF/AI import

On Windows, install Python from:

```text
https://www.python.org/downloads/
```

Install PostgreSQL from:

```text
https://www.postgresql.org/download/
```

During the PostgreSQL installation, remember the password you set for the
default PostgreSQL admin user `postgres`.

## 1. Open The Project Folder

Windows PowerShell:

```powershell
cd C:\path\to\sheetbase
```

Example:

```powershell
cd C:\Users\Max\Desktop\Schule\sheetbase
```

Linux/macOS:

```bash
cd /path/to/sheetbase
```

## 2. Create A Virtual Environment

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation scripts, run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate the environment again:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

After activation, your terminal should show `(.venv)`.

## 3. Install Python Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The project installs these Python packages:

```text
flask
sqlalchemy
flask_sqlalchemy
psycopg2-binary
requests
pymupdf
```

## 4. Start Or Check PostgreSQL

### Windows

Check whether PostgreSQL is running:

```powershell
Get-Service | Where-Object { $_.Name -like "*postgres*" -or $_.DisplayName -like "*PostgreSQL*" }
```

Start the service if needed:

```powershell
Start-Service postgresql-x64-18
```

Your service name may be different, for example `postgresql-x64-17` or
`postgresql-x64-16`.

If `psql` is not in your PATH, use the full path. Examples:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost
```

or:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost
```

### Linux

```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### macOS

If PostgreSQL was installed with Homebrew:

```bash
brew services list
brew services start postgresql
```

## 5. Create The Database User And Database

Open `psql` as the PostgreSQL admin user:

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

Then run:

```sql
CREATE USER flaskusr WITH PASSWORD 'sheetbase';
CREATE DATABASE datasheetdb OWNER flaskusr ENCODING 'UTF8';
GRANT ALL PRIVILEGES ON DATABASE datasheetdb TO flaskusr;
```

Exit `psql`:

```sql
\q
```

If the user already exists, use:

```sql
ALTER USER flaskusr WITH PASSWORD 'sheetbase';
```

If the database already exists, make sure the owner is correct:

```sql
ALTER DATABASE datasheetdb OWNER TO flaskusr;
GRANT ALL PRIVILEGES ON DATABASE datasheetdb TO flaskusr;
```

## 6. Allow The Correct Database Host

The current app expects PostgreSQL at:

```text
192.168.1.21:5432
```

You have two possible setup variants.

### Variant A: Use The Configured Host

Use this if PostgreSQL should be reachable exactly at `192.168.1.21`.

Make sure the machine running PostgreSQL has this IP address. Then allow
PostgreSQL to listen for network connections.

In `postgresql.conf`, set:

```text
listen_addresses = '*'
```

In `pg_hba.conf`, add a rule like this:

```text
host    datasheetdb    flaskusr    192.168.1.0/24    scram-sha-256
```

Restart PostgreSQL afterwards.

Windows:

```powershell
Restart-Service postgresql-x64-18
```

Linux:

```bash
sudo systemctl restart postgresql
```

macOS with Homebrew:

```bash
brew services restart postgresql
```

Test the exact connection used by the app:

```bash
psql -U flaskusr -d datasheetdb -h 192.168.1.21 -p 5432 -c "SELECT current_user, current_database();"
```

On Windows without `psql` in PATH:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U flaskusr -d datasheetdb -h 192.168.1.21 -p 5432 -c "SELECT current_user, current_database();"
```

### Variant B: Use Localhost

Use this if PostgreSQL only runs locally on the same computer.

Change the database host in `app.py`, `test-conn.py` and `test-post.py` from:

```text
192.168.1.21
```

to:

```text
localhost
```

The connection string then becomes:

```text
postgresql+psycopg2://flaskusr:sheetbase@localhost:5432/datasheetdb
```

Then test:

```bash
psql -U flaskusr -d datasheetdb -h localhost -p 5432 -c "SELECT current_user, current_database();"
```

## 7. Create The Database Tables

The application does not automatically create the tables. Create them once
manually.

Open the application database as `flaskusr`:

Windows:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U flaskusr -d datasheetdb -h 192.168.1.21
```

Linux/macOS:

```bash
psql -U flaskusr -d datasheetdb -h 192.168.1.21
```

If you use `localhost`, replace `192.168.1.21` with `localhost`.

Then run:

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

Check the tables:

```sql
\dt
```

Exit:

```sql
\q
```

## 8. Configure OpenRouter

The UI and database can start without an OpenRouter API key, but the PDF import
and AI extraction will fail until a valid key is configured.

The app reads this environment variable:

```text
OPENROUTER_API_KEY
```

Windows PowerShell, only for the current terminal:

```powershell
$env:OPENROUTER_API_KEY="your-openrouter-api-key"
```

Windows PowerShell, permanent for future terminals:

```powershell
setx OPENROUTER_API_KEY "your-openrouter-api-key"
```

Linux/macOS, only for the current terminal:

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

Linux/macOS, permanent example for Bash:

```bash
echo 'export OPENROUTER_API_KEY="your-openrouter-api-key"' >> ~/.bashrc
source ~/.bashrc
```

## 9. Start The Application

Make sure the virtual environment is active.

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

The app starts on:

```text
http://127.0.0.1:5000
```

Because `app.py` uses:

```text
host="0.0.0.0", port=5000, debug=True
```

the app can also be reachable from other devices in the same network via the
computer's IP address.

## 10. Verify The Installation

Open these URLs in the browser:

```text
http://127.0.0.1:5000/
http://127.0.0.1:5000/docs
http://127.0.0.1:5000/test-db
```

The database test should return:

```json
{
  "database": "connected"
}
```

You can also check the data API endpoints:

```text
http://127.0.0.1:5000/data/opv
http://127.0.0.1:5000/data/bjt
http://127.0.0.1:5000/data/mosfet
```

At the beginning they should return empty lists:

```json
[]
```

## Test Scripts

The repository contains two test scripts:

| Script | Purpose |
| --- | --- |
| `test-conn.py` | Tests the database connection and inserts one test OPV row |
| `test-post.py` | Inserts example OPV, BJT and MOSFET rows |

Run them only if test rows in the database are okay:

```bash
python test-conn.py
python test-post.py
```

## Troubleshooting

### `psql` Is Not Recognized

Use the full path to `psql.exe`:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe"
```

Or add PostgreSQL's `bin` folder to PATH:

```text
C:\Program Files\PostgreSQL\18\bin
```

### Password Authentication Failed

Reset the password for the app user:

```sql
ALTER USER flaskusr WITH PASSWORD 'sheetbase';
```

### Could Not Connect To Server

Check:

1. PostgreSQL is running.
2. The host in the connection string is reachable.
3. PostgreSQL listens on the needed address.
4. `pg_hba.conf` allows the connection.
5. The firewall allows port `5432` if connecting over the network.

### Relation Does Not Exist

This means the tables were not created yet. Run the SQL from
"Create The Database Tables" again.

### PDF Import Fails

Check:

1. `OPENROUTER_API_KEY` is set.
2. The computer has internet access.
3. The OpenRouter key is valid.
4. The uploaded PDF contains readable text.
5. PostgreSQL tables exist.

### Port 5000 Is Already In Use

Close the other program using port `5000`, or change the port in `app.py`.

## Useful Commands

Show installed Python packages:

```bash
pip list
```

Check Python version:

```bash
python --version
```

Check PostgreSQL connection:

```bash
psql -U flaskusr -d datasheetdb -h 192.168.1.21 -p 5432
```

Run the Flask app:

```bash
python app.py
```

## Notes For Development

- Keep the virtual environment folder out of Git.
- Do not commit real API keys.
- The database URL is currently hardcoded in the Python files.
- The table definitions in PostgreSQL must match the SQLAlchemy models in
  `app.py`.
- `prompt.txt` controls how datasheet information should be converted into SQL.

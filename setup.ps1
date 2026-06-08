param(
    [string]$DbHost = "192.168.1.21",
    [int]$DbPort = 5432,
    [string]$DbName = "datasheetdb",
    [string]$DbUser = "flaskusr",
    [string]$DbPassword = "sheetbase",
    [string]$PostgresAdminUser = "postgres",
    [string]$PostgresAdminHost = "localhost",
    [string]$PostgresAdminPassword = "",
    [string]$PsqlPath = "",
    [string]$OpenRouterApiKey = "",
    [switch]$SkipDatabase
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Assert-SafeIdentifier {
    param(
        [string]$Value,
        [string]$Name
    )

    if ($Value -notmatch "^[A-Za-z_][A-Za-z0-9_]*$") {
        throw "$Name must only contain letters, numbers and underscores, and must not start with a number."
    }
}

function ConvertTo-SqlLiteral {
    param([string]$Value)
    return "'" + $Value.Replace("'", "''") + "'"
}

function Find-Psql {
    if ($PsqlPath -and (Test-Path $PsqlPath)) {
        return (Resolve-Path $PsqlPath).Path
    }

    $cmd = Get-Command psql -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidates = Get-ChildItem "C:\Program Files\PostgreSQL" -Recurse -Filter psql.exe -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch "pgAdmin" } |
        Sort-Object FullName -Descending

    if ($candidates) {
        return $candidates[0].FullName
    }

    return ""
}

function Invoke-Psql {
    param(
        [string[]]$Arguments,
        [string]$Password = ""
    )

    $oldPassword = $env:PGPASSWORD
    try {
        if ($Password) {
            $env:PGPASSWORD = $Password
        }

        & $script:PsqlExe @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "psql failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        $env:PGPASSWORD = $oldPassword
    }
}

function Invoke-PsqlOutput {
    param(
        [string[]]$Arguments,
        [string]$Password = ""
    )

    $oldPassword = $env:PGPASSWORD
    try {
        if ($Password) {
            $env:PGPASSWORD = $Password
        }

        $output = & $script:PsqlExe @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "psql failed with exit code $LASTEXITCODE."
        }
        return ($output | Out-String).Trim()
    }
    finally {
        $env:PGPASSWORD = $oldPassword
    }
}

Assert-SafeIdentifier $DbName "DbName"
Assert-SafeIdentifier $DbUser "DbUser"

Write-Step "Preparing Python virtual environment"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        & py -3 -m venv .venv
    }
    else {
        & python -m venv .venv
    }
    Write-Ok "Created .venv"
}
else {
    Write-Ok ".venv already exists"
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt
Write-Ok "Python dependencies are installed"

if ($OpenRouterApiKey) {
    Write-Step "Setting OpenRouter API key for this terminal"
    $env:OPENROUTER_API_KEY = $OpenRouterApiKey
    Write-Ok "OPENROUTER_API_KEY is set for this PowerShell session"
}
else {
    Write-Warn "No OpenRouter key provided. PDF import will need OPENROUTER_API_KEY later."
}

if ($SkipDatabase) {
    Write-Warn "Skipping PostgreSQL setup because -SkipDatabase was used."
    exit 0
}

Write-Step "Finding PostgreSQL psql"
$script:PsqlExe = Find-Psql

if (-not $script:PsqlExe) {
    throw "psql was not found. Install PostgreSQL first: https://www.postgresql.org/download/"
}

Write-Ok "Using psql: $script:PsqlExe"

Write-Step "Checking PostgreSQL service"
$services = Get-Service -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like "*postgres*" -or $_.DisplayName -like "*PostgreSQL*" }

foreach ($service in $services) {
    if ($service.Status -ne "Running") {
        try {
            Start-Service $service.Name
            Write-Ok "Started service $($service.Name)"
        }
        catch {
            Write-Warn "Could not start service $($service.Name). Start it manually if needed."
        }
    }
    else {
        Write-Ok "Service $($service.Name) is running"
    }
}

if (-not $services) {
    Write-Warn "No PostgreSQL Windows service was found. Continuing with psql."
}

Write-Step "Creating database user if needed"

$dbUserLiteral = ConvertTo-SqlLiteral $DbUser
$dbPasswordLiteral = ConvertTo-SqlLiteral $DbPassword

$roleSql = @"
DO `$`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = $dbUserLiteral) THEN
        CREATE USER "$DbUser" WITH PASSWORD $dbPasswordLiteral;
    ELSE
        ALTER USER "$DbUser" WITH PASSWORD $dbPasswordLiteral;
    END IF;
END
`$`$;
"@

Invoke-Psql @(
    "-U", $PostgresAdminUser,
    "-h", $PostgresAdminHost,
    "-p", "$DbPort",
    "-d", "postgres",
    "-v", "ON_ERROR_STOP=1",
    "-c", $roleSql
) -Password $PostgresAdminPassword

Write-Ok "Database user is ready: $DbUser"

Write-Step "Creating database if needed"

$dbNameLiteral = ConvertTo-SqlLiteral $DbName
$dbExists = Invoke-PsqlOutput @(
    "-U", $PostgresAdminUser,
    "-h", $PostgresAdminHost,
    "-p", "$DbPort",
    "-d", "postgres",
    "-tAc", "SELECT 1 FROM pg_database WHERE datname = $dbNameLiteral;"
) -Password $PostgresAdminPassword

if ($dbExists -ne "1") {
    Invoke-Psql @(
        "-U", $PostgresAdminUser,
        "-h", $PostgresAdminHost,
        "-p", "$DbPort",
        "-d", "postgres",
        "-v", "ON_ERROR_STOP=1",
        "-c", "CREATE DATABASE ""$DbName"" OWNER ""$DbUser"" ENCODING 'UTF8';"
    ) -Password $PostgresAdminPassword

    Write-Ok "Created database: $DbName"
}
else {
    Write-Ok "Database already exists: $DbName"
}

Invoke-Psql @(
    "-U", $PostgresAdminUser,
    "-h", $PostgresAdminHost,
    "-p", "$DbPort",
    "-d", "postgres",
    "-v", "ON_ERROR_STOP=1",
    "-c", "ALTER DATABASE ""$DbName"" OWNER TO ""$DbUser""; GRANT ALL PRIVILEGES ON DATABASE ""$DbName"" TO ""$DbUser"";"
) -Password $PostgresAdminPassword

Write-Step "Creating application tables if needed"

$tableSql = @"
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
"@

Invoke-Psql @(
    "-U", $DbUser,
    "-h", $DbHost,
    "-p", "$DbPort",
    "-d", $DbName,
    "-v", "ON_ERROR_STOP=1",
    "-c", $tableSql
) -Password $DbPassword

Write-Ok "Tables are ready"

Write-Step "Testing app database connection"

try {
    Invoke-Psql @(
        "-U", $DbUser,
        "-h", $DbHost,
        "-p", "$DbPort",
        "-d", $DbName,
        "-v", "ON_ERROR_STOP=1",
        "-c", "SELECT current_user, current_database();"
    ) -Password $DbPassword
    Write-Ok "Database connection works"
}
catch {
    Write-Warn "Database setup finished, but the final connection test failed."
    Write-Warn "Check whether the app host '$DbHost' is reachable. If you use localhost, run: .\setup.ps1 -DbHost localhost"
    throw
}

Write-Step "Done"
Write-Host "Activate the environment with:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "Start the app with:"
Write-Host "  python app.py"
Write-Host "Open:"
Write-Host "  http://127.0.0.1:5000"

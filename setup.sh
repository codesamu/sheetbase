#!/usr/bin/env bash

set -euo pipefail

DB_HOST="192.168.1.21"
DB_PORT="5432"
DB_NAME="datasheetdb"
DB_USER="flaskusr"
DB_PASSWORD="sheetbase"
POSTGRES_ADMIN_USER="postgres"
POSTGRES_ADMIN_HOST="localhost"
POSTGRES_ADMIN_PASSWORD=""
PSQL_PATH=""
OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
SKIP_DATABASE=0

write_step() {
  printf '\n==> %s\n' "$1"
}

write_ok() {
  printf '[OK] %s\n' "$1"
}

write_warn() {
  printf '[WARN] %s\n' "$1"
}

assert_safe_identifier() {
  local value="$1"
  local name="$2"

  if [[ ! "$value" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    printf '%s must only contain letters, numbers and underscores, and must not start with a number.\n' "$name" >&2
    exit 1
  fi
}

sql_literal() {
  local value="$1"
  value="${value//\'/\'\'}"
  printf "'%s'" "$value"
}

find_psql() {
  if [[ -n "$PSQL_PATH" && -x "$PSQL_PATH" ]]; then
    printf '%s\n' "$PSQL_PATH"
    return 0
  fi

  if command -v psql >/dev/null 2>&1; then
    command -v psql
    return 0
  fi

  printf '\n'
}

invoke_psql() {
  local password="$1"
  shift

  if [[ -n "$password" ]]; then
    PGPASSWORD="$password" "$PSQL_EXE" "$@"
  else
    "$PSQL_EXE" "$@"
  fi
}

invoke_psql_output() {
  local password="$1"
  shift

  if [[ -n "$password" ]]; then
    PGPASSWORD="$password" "$PSQL_EXE" "$@"
  else
    "$PSQL_EXE" "$@"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db-host)
      DB_HOST="$2"
      shift 2
      ;;
    --db-port)
      DB_PORT="$2"
      shift 2
      ;;
    --db-name)
      DB_NAME="$2"
      shift 2
      ;;
    --db-user)
      DB_USER="$2"
      shift 2
      ;;
    --db-password)
      DB_PASSWORD="$2"
      shift 2
      ;;
    --postgres-admin-user)
      POSTGRES_ADMIN_USER="$2"
      shift 2
      ;;
    --postgres-admin-host)
      POSTGRES_ADMIN_HOST="$2"
      shift 2
      ;;
    --postgres-admin-password)
      POSTGRES_ADMIN_PASSWORD="$2"
      shift 2
      ;;
    --psql-path)
      PSQL_PATH="$2"
      shift 2
      ;;
    --openrouter-api-key)
      OPENROUTER_API_KEY="$2"
      shift 2
      ;;
    --skip-database)
      SKIP_DATABASE=1
      shift
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./setup.sh [options]

Options:
  --db-host HOST
  --db-port PORT
  --db-name NAME
  --db-user USER
  --db-password PASSWORD
  --postgres-admin-user USER
  --postgres-admin-host HOST
  --postgres-admin-password PASSWORD
  --psql-path PATH
  --openrouter-api-key KEY
  --skip-database
EOF
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      exit 1
      ;;
  esac
done

assert_safe_identifier "$DB_NAME" "DB_NAME"
assert_safe_identifier "$DB_USER" "DB_USER"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

write_step "Preparing Python virtual environment"

VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m venv .venv
  else
    python -m venv .venv
  fi
  write_ok "Created .venv"
else
  write_ok ".venv already exists"
fi

"$VENV_PYTHON" -m pip install --upgrade pip
"$VENV_PYTHON" -m pip install -r requirements.txt
write_ok "Python dependencies are installed"

if [[ -n "$OPENROUTER_API_KEY" ]]; then
  write_step "Using OpenRouter API key"
  write_ok "OPENROUTER_API_KEY is available for this script run"
else
  write_warn "No OpenRouter key provided. PDF import will need OPENROUTER_API_KEY later."
fi

if [[ "$SKIP_DATABASE" -eq 1 ]]; then
  write_warn "Skipping PostgreSQL setup because --skip-database was used."
  exit 0
fi

write_step "Finding PostgreSQL psql"
PSQL_EXE="$(find_psql)"

if [[ -z "$PSQL_EXE" ]]; then
  printf 'psql was not found. Install PostgreSQL first: https://www.postgresql.org/download/\n' >&2
  exit 1
fi

write_ok "Using psql: $PSQL_EXE"

write_step "Creating database user if needed"

DB_USER_LITERAL="$(sql_literal "$DB_USER")"
DB_PASSWORD_LITERAL="$(sql_literal "$DB_PASSWORD")"

ROLE_SQL=$(cat <<EOF
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = $DB_USER_LITERAL) THEN
        CREATE USER "$DB_USER" WITH PASSWORD $DB_PASSWORD_LITERAL;
    ELSE
        ALTER USER "$DB_USER" WITH PASSWORD $DB_PASSWORD_LITERAL;
    END IF;
END
\$\$;
EOF
)

invoke_psql "$POSTGRES_ADMIN_PASSWORD" \
  -U "$POSTGRES_ADMIN_USER" \
  -h "$POSTGRES_ADMIN_HOST" \
  -p "$DB_PORT" \
  -d postgres \
  -v ON_ERROR_STOP=1 \
  -c "$ROLE_SQL"

write_ok "Database user is ready: $DB_USER"

write_step "Creating database if needed"

DB_NAME_LITERAL="$(sql_literal "$DB_NAME")"
DB_EXISTS="$(invoke_psql_output "$POSTGRES_ADMIN_PASSWORD" \
  -U "$POSTGRES_ADMIN_USER" \
  -h "$POSTGRES_ADMIN_HOST" \
  -p "$DB_PORT" \
  -d postgres \
  -tAc "SELECT 1 FROM pg_database WHERE datname = $DB_NAME_LITERAL;")"

if [[ "$DB_EXISTS" != "1" ]]; then
  invoke_psql "$POSTGRES_ADMIN_PASSWORD" \
    -U "$POSTGRES_ADMIN_USER" \
    -h "$POSTGRES_ADMIN_HOST" \
    -p "$DB_PORT" \
    -d postgres \
    -v ON_ERROR_STOP=1 \
    -c "CREATE DATABASE \"$DB_NAME\" OWNER \"$DB_USER\" ENCODING 'UTF8';"

  write_ok "Created database: $DB_NAME"
else
  write_ok "Database already exists: $DB_NAME"
fi

invoke_psql "$POSTGRES_ADMIN_PASSWORD" \
  -U "$POSTGRES_ADMIN_USER" \
  -h "$POSTGRES_ADMIN_HOST" \
  -p "$DB_PORT" \
  -d postgres \
  -v ON_ERROR_STOP=1 \
  -c "ALTER DATABASE \"$DB_NAME\" OWNER TO \"$DB_USER\"; GRANT ALL PRIVILEGES ON DATABASE \"$DB_NAME\" TO \"$DB_USER\";"

write_step "Creating application tables if needed"

TABLE_SQL=$(cat <<'EOF'
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
EOF
)

invoke_psql "$DB_PASSWORD" \
  -U "$DB_USER" \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -d "$DB_NAME" \
  -v ON_ERROR_STOP=1 \
  -c "$TABLE_SQL"

write_ok "Tables are ready"

write_step "Testing app database connection"

if invoke_psql "$DB_PASSWORD" \
  -U "$DB_USER" \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -d "$DB_NAME" \
  -v ON_ERROR_STOP=1 \
  -c "SELECT current_user, current_database();" >/dev/null; then
  write_ok "Database connection works"
else
  write_warn "Database setup finished, but the final connection test failed."
  write_warn "Check whether the app host '$DB_HOST' is reachable. If you use localhost, run: ./setup.sh --db-host localhost"
  exit 1
fi

write_step "Done"
printf 'Activate the environment with:\n'
printf '  source .venv/bin/activate\n'
printf 'Start the app with:\n'
printf '  python app.py\n'
printf 'Open:\n'
printf '  http://127.0.0.1:5000\n'

#!/bin/bash
set -e
echo '[init] Installing PostgreSQL…'
sudo apt-get -qq update
sudo apt-get -qq install -y postgresql postgresql-contrib > /dev/null
echo '[init] Starting PostgreSQL…'
sudo service postgresql start

if [[ -z "${POSTGRES_PW}" ]]; then
  echo '[init] ERROR: POSTGRES_PW env var not set.' >&2
  exit 1
fi

sudo -u postgres psql -c "ALTER USER postgres PASSWORD '${POSTGRES_PW}';"
echo '[init] PostgreSQL ready on port 5432.'

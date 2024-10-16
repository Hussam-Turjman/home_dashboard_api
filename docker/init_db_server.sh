#!/bin/bash

#set -e

echo "DB_NAME: $DB_NAME"
echo "DB_USER: $DB_USER"
echo "DB_PASS: $DB_PASS"

export POSTGRESQL_VERSION=$(psql --version | awk '{print $3}')
export POSTGRESQL_VERSION_MAJOR=$(echo "$POSTGRESQL_VERSION" | awk -F. '{print $1}')
echo "PostgreSQL version: $POSTGRESQL_VERSION"
echo "PostgreSQL major version: $POSTGRESQL_VERSION_MAJOR"

sudo pg_createcluster "$POSTGRESQL_VERSION_MAJOR" main

sudo systemctl enable postgresql
sudo systemctl start postgresql
sudo service postgresql start

# Get service status
SERVICE_STATUS=$(sudo service postgresql status)
echo "Service status: $SERVICE_STATUS"
pg_isready

sudo sed -i "s/local   all             postgres                                peer/local   all             postgres                                trust/g" /etc/postgresql/"$POSTGRESQL_VERSION_MAJOR"/main/pg_hba.conf
sudo service postgresql restart
# Create database if not exists
psql -U postgres -c "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || psql -U postgres -c "CREATE DATABASE  $DB_NAME;"

# psql -U postgres -c "CREATE DATABASE  $DB_NAME;"
# Create user if not exists
psql -U postgres -c "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER'" | grep -q 1 || psql -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
# psql -U postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

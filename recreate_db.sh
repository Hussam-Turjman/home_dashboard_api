#!/bin/bash

set -e

FILENAME="tmp_backup.sql"
DB_NAME="home"
DB_USER="hussam"

pg_dump $DB_NAME >$FILENAME
dropdb $DB_NAME
createdb $DB_NAME
psql --username=$DB_USER $DB_NAME <$FILENAME

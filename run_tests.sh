#!/bin/bash

set -e

DB_USER=hussam
DB_USER_PASSWORD=verystrongpassword
DB_NAME=home_dashboard
DB_HOSTNAME=localhost
ENDPOINT=localhost
ENDPOINT_PORT=5001
JWT_SECRET_KEY=9cbb00b2ad4a8f872ea195289f125492976681e66cee4f55d52b4312a2083739

cwd=$(pwd)

# if .env file doesn't exist, create it and add the environment variables
if [ ! -f .env ]; then
    echo "DB_USER=$DB_USER" >>.env
    echo "DB_USER_PASSWORD=$DB_USER_PASSWORD" >>.env
    echo "DB_NAME=$DB_NAME" >>.env
    echo "DB_HOSTNAME=$DB_HOSTNAME" >>.env
    echo "ENDPOINT=$ENDPOINT" >>.env
    echo "ENDPOINT_PORT=$ENDPOINT_PORT" >>.env
    echo "JWT_SECRET_KEY=$JWT_SECRET_KEY" >>.env
fi

sed -i 's/DEBUG_MODE = False/DEBUG_MODE = True/' home_api/debug.py

echo "Current working directory: $cwd"
python3 update_secret_key.py
# .env content
cat .env
pytest tests -o log_cli=true --doctest-modules --junitxml=junit/test-results.xml --cov=. --cov-report=xml --cov-report=html

# restore the original value of DEBUG_MODE
sed -i 's/DEBUG_MODE = True/DEBUG_MODE = False/' home_api/debug.py

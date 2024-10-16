#!/bin/bash

set -e
cp ../requirements.txt .
echo "Building Docker image..."
docker build --platform linux/amd64 -t 889977/home_dashboard:latest .
echo "Done"

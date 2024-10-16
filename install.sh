#!/bin/bash

set -e

sudo apt update
sudo apt install -y shfmt shellcheck

echo "Done installing dependencies"

#!/bin/bash

set -e

docker pull 889977/home_dashboard:latest
docker run -it 889977/home_dashboard:latest /bin/bash

echo "Done"

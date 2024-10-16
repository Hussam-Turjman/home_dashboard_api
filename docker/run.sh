#!/bin/bash

set -e

docker pull 889977/home_dashboard:latest
# Get container ID if exists
CID=$(docker ps -aqf "ancestor=889977/home_dashboard:latest")
if [ -n "$CID" ]; then
    echo "Found existing container $CID"
    # if not running, start it
    if [ -z "$(docker ps -q -f id=$CID)" ]; then
        echo "Starting container $CID"
        docker start "$CID"
    fi
    # Enter the container
    docker exec -it "$CID" /bin/bash
else
    docker run -it 889977/home_dashboard:latest /bin/bash
fi

echo "Done"

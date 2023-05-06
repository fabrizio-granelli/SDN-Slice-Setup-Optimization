#!/bin/bash

for container in $(docker ps -a -q); do 
	docker exec -it $container kill 1;
done

docker rm -f $(docker ps -a -q)

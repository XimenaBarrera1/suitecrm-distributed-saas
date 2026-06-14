#!/bin/bash

docker start db-node-1

sleep 15

docker start db-node-2

sleep 10

docker start db-node-3

sleep 10

docker exec db-node-1 mysql -uroot -proot_password \
-e "SHOW STATUS LIKE 'wsrep_cluster_size';"
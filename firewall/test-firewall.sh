#!/usr/bin/env bash

TARGET="${1:-127.0.0.1}"

echo "[INFO] Probando puertos publicos en $TARGET"
nc -vz "$TARGET" 22
nc -vz "$TARGET" 53
nc -vz "$TARGET" 80
nc -vz "$TARGET" 443

echo
echo "[INFO] Probando puertos internos que deberian estar bloqueados desde cliente"
nc -vz "$TARGET" 3306
nc -vz "$TARGET" 5672
nc -vz "$TARGET" 15672
nc -vz "$TARGET" 6379

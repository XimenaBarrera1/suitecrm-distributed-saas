#!/usr/bin/env bash
set -e

echo "[INFO] Preparando SuiteCRM..."

INIT_MARKER="/var/www/html/.suitecrm_initialized"
INIT_LOCK="/var/www/html/.suitecrm_init_lock"

if [ ! -f "$INIT_MARKER" ]; then
    if mkdir "$INIT_LOCK" 2>/dev/null; then
        echo "[INFO] Este contenedor inicializara el volumen SuiteCRM..."

        if [ ! -f /var/www/html/index.php ]; then
            echo "[INFO] Copiando SuiteCRM base a /var/www/html..."
            cp -a /usr/src/suitecrm/. /var/www/html/
        else
            echo "[INFO] SuiteCRM ya existe en /var/www/html. No se copia de nuevo."
        fi

        touch "$INIT_MARKER"
        rmdir "$INIT_LOCK" || true
    else
        echo "[INFO] Otro contenedor esta inicializando SuiteCRM. Esperando..."
        while [ ! -f "$INIT_MARKER" ]; do
            sleep 2
        done
        echo "[INFO] Inicializacion detectada. Continuando..."
    fi
else
    echo "[INFO] SuiteCRM ya estaba inicializado en este volumen."
fi

echo "[INFO] Aplicando permisos..."

mkdir -p /var/www/html/cache /var/www/html/upload /var/www/html/custom

chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html

chmod -R 775 /var/www/html/cache || true
chmod -R 775 /var/www/html/upload || true
chmod -R 775 /var/www/html/custom || true
chmod -R 775 /var/www/html/modules || true

find /var/www/html -type f -name config.php -exec chmod 664 {} \; || true
find /var/www/html -type f -name config_override.php -exec chmod 664 {} \; || true

echo "[INFO] Iniciando Apache..."
exec apache2-foreground
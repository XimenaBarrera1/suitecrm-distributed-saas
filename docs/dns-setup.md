# Configuración DNS - SuiteCRM Distributed SaaS

## 1. Objetivo

Este documento describe la configuración del componente DNS del proyecto `suitecrm-distributed-saas`.

El DNS permite resolver los dominios de los clientes hacia la entrada principal del sistema. En esta fase se configuraron dos dominios:

- `www.clientea.com`
- `www.clienteb.com`

Ambos dominios resuelven hacia la IP de entrada del sistema:

`192.168.0.1`

Esta IP representa la entrada externa de la arquitectura, donde posteriormente se integrarán el firewall, el reverse proxy y los balanceadores de carga.

---

## 2. Red utilizada

Para mantener coherencia con la arquitectura definida, se usa la red externa simulada:

`192.168.0.0/24`

Distribución definida:

| Elemento | IP |
|---|---|
| Cliente / navegador | `192.168.0.10` |
| Entrada / firewall externo | `192.168.0.1` |
| DNS | `192.168.0.2` |

En la VM Ubuntu Server, la interfaz de red interna del proyecto debe tener estas IPs:

- `192.168.0.1/24`
- `192.168.0.2/24`

En la VM Ubuntu Desktop cliente debe configurarse:

- IP: `192.168.0.10/24`
- DNS: `192.168.0.2`

---

## 3. Adaptadores de red

### VM Ubuntu Server

| Adaptador | Uso |
|---|---|
| NAT | Internet para instalar paquetes y actualizar el sistema |
| Adaptador puente | Administración por SSH / VS Code Remote SSH |
| Red interna | Red externa simulada del proyecto `192.168.0.0/24` |

### VM Ubuntu Desktop Cliente

| Adaptador | Uso |
|---|---|
| NAT | Internet |
| Adaptador puente | Administración por SSH / VS Code, si se requiere |
| Red interna | Red del proyecto `192.168.0.0/24` |

El adaptador puente no hace parte de la arquitectura lógica del proyecto. Solo se usa para administrar las máquinas virtuales desde el host físico.

---

## 4. Variables de entorno

El proyecto usa un archivo `.env` local para definir las IPs del entorno.

Cada integrante debe crear su propio `.env` a partir del archivo de ejemplo:

    cp .env.example .env

Contenido esperado:

    DNS_IP=192.168.0.2
    ENTRYPOINT_IP=192.168.0.1

Significado:

| Variable | Descripción |
|---|---|
| `DNS_IP` | IP donde escucha el servicio DNS |
| `ENTRYPOINT_IP` | IP que el DNS devuelve para los dominios de los clientes |

Con esta configuración:

- `www.clientea.com` resuelve a `192.168.0.1`
- `www.clienteb.com` resuelve a `192.168.0.1`

---

## 5. Archivos del componente DNS

La configuración DNS está organizada así:

    dns/
    ├── named.conf
    ├── named.conf.options
    ├── named.conf.local
    └── zones/
        └── templates/
            ├── db.clientea.com.tpl
            └── db.clienteb.com.tpl

    scripts/
    └── generate-dns-zones.sh

Los archivos reales de zona se generan automáticamente:

- `dns/zones/db.clientea.com`
- `dns/zones/db.clienteb.com`

Estos archivos no se suben a GitHub porque se generan localmente a partir del `.env`.

---

## 6. Archivos que no se versionan

No deben subirse al repositorio:

- `.env`
- `dns/zones/db.clientea.com`
- `dns/zones/db.clienteb.com`

Motivo:

- `.env` contiene configuración local de cada integrante.
- Las zonas `db.clientea.com` y `db.clienteb.com` se generan automáticamente según el `.env`.
- Si cada integrante usa otra IP o ajusta su entorno, puede regenerarlas sin modificar archivos versionados.

Sí deben subirse:

- `.env.example`
- `docker-compose.yml`
- `dns/named.conf`
- `dns/named.conf.options`
- `dns/named.conf.local`
- `dns/zones/templates/db.clientea.com.tpl`
- `dns/zones/templates/db.clienteb.com.tpl`
- `scripts/generate-dns-zones.sh`
- `docs/dns-setup.md`

---

## 7. Cómo usar esta configuración después de clonar el repositorio

Cuando un integrante baje el proyecto, debe hacer lo siguiente desde la raíz del repositorio.

### 7.1 Entrar al proyecto

    cd suitecrm-distributed-saas

### 7.2 Copiar el archivo de variables

    cp .env.example .env

### 7.3 Revisar el `.env`

    cat .env

Debe contener:

    DNS_IP=192.168.0.2
    ENTRYPOINT_IP=192.168.0.1

Si el integrante usa la misma red definida para el proyecto, no necesita cambiar nada.

### 7.4 Generar las zonas DNS

    ./scripts/generate-dns-zones.sh

Resultado esperado:

    Zonas DNS generadas con DNS_IP=192.168.0.2 y ENTRYPOINT_IP=192.168.0.1

Esto crea:

- `dns/zones/db.clientea.com`
- `dns/zones/db.clienteb.com`

### 7.5 Levantar el servicio DNS

    docker compose up -d

### 7.6 Verificar el contenedor

    docker compose ps

Debe aparecer el contenedor `dns`.

### 7.7 Validar configuración de Bind9

    docker exec -it dns named-checkconf -z

Resultado esperado:

    zone clientea.com/IN: loaded serial 2026060101
    zone clienteb.com/IN: loaded serial 2026060101

---

## 8. Pruebas desde la VM Ubuntu Server

Consultar directamente al DNS:

    dig @192.168.0.2 www.clientea.com
    dig @192.168.0.2 www.clienteb.com

Resultado esperado:

- `www.clientea.com` resuelve a `192.168.0.1`
- `www.clienteb.com` resuelve a `192.168.0.1`

También se puede probar con:

    nslookup www.clientea.com 192.168.0.2
    nslookup www.clienteb.com 192.168.0.2

---

## 9. Configuración de la VM Cliente

La VM cliente debe estar conectada a la red interna del proyecto y debe tener:

- IP: `192.168.0.10/24`
- DNS: `192.168.0.2`

Si se usa NetworkManager, se puede configurar con:

    sudo nmcli connection add type ethernet ifname enp0s9 con-name acme_external \
    ipv4.method manual \
    ipv4.addresses 192.168.0.10/24 \
    ipv4.dns 192.168.0.2 \
    ipv4.dns-search "~clientea.com,~clienteb.com" \
    ipv4.ignore-auto-dns yes \
    ipv4.never-default yes \
    connection.autoconnect yes

Activar conexión:

    sudo nmcli connection up acme_external

Verificar IP:

    ip a show enp0s9

Verificar DNS:

    resolvectl status

En la interfaz del proyecto debe aparecer:

    DNS Servers: 192.168.0.2
    DNS Domain: ~clientea.com ~clienteb.com

---

## 10. Pruebas desde la VM Cliente

Primero probar conectividad:

    ping -c 4 192.168.0.1
    ping -c 4 192.168.0.2

Luego probar DNS directamente:

    dig @192.168.0.2 www.clientea.com
    dig @192.168.0.2 www.clienteb.com

Resultado esperado:

- `www.clientea.com` resuelve a `192.168.0.1`
- `www.clienteb.com` resuelve a `192.168.0.1`

Luego probar resolución normal del sistema:

    nslookup www.clientea.com
    nslookup www.clienteb.com

Resultado esperado:

    Name: www.clientea.com
    Address: 192.168.0.1

    Name: www.clienteb.com
    Address: 192.168.0.1

Si `nslookup` muestra como servidor `127.0.0.53`, no es un error. Ese es el resolvedor local de Ubuntu. Lo importante es que el resultado final sea `192.168.0.1`.

---

## 11. Resultado esperado de la fase DNS

La fase DNS se considera funcional cuando desde la VM cliente se obtiene:

- `www.clientea.com -> 192.168.0.1`
- `www.clienteb.com -> 192.168.0.1`

Esto cumple la resolución por cliente solicitada en la rúbrica del proyecto.

---

## 12. Comandos rápidos de verificación

Desde la VM Server:

    docker compose ps
    docker exec -it dns named-checkconf -z
    dig @192.168.0.2 www.clientea.com
    dig @192.168.0.2 www.clienteb.com

Desde la VM Cliente:

    ping -c 4 192.168.0.1
    ping -c 4 192.168.0.2
    nslookup www.clientea.com
    nslookup www.clienteb.com

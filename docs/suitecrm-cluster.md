# Cluster de Aplicación SuiteCRM por Cliente

## 1. Objetivo

Este documento describe la implementación del cluster de aplicación SuiteCRM por cliente dentro del proyecto `suitecrm-distributed-saas`.

El objetivo de esta fase es cumplir el requisito de tener al menos dos contenedores SuiteCRM por cliente, conectados al flujo general de la arquitectura:

```text
Cliente -> DNS -> Reverse Proxy -> Load Balancer del Cliente -> Nodos SuiteCRM
```

Para esta fase se implementaron cuatro contenedores reales de SuiteCRM:

**Cliente A:**

* `suitecrm-a1`
* `suitecrm-a2`

**Cliente B:**

* `suitecrm-b1`
* `suitecrm-b2`

---

## 2. Tecnologías utilizadas

La imagen de aplicación SuiteCRM se construyó de forma propia usando:

* SuiteCRM 7.15.1
* Apache 2.4
* PHP 8.2
* MariaDB 10.11 temporal
* Redis 7 para sesiones
* Docker Compose

---

## 3. Componentes implementados

| Componente         |         IP DMZ |      IP interna | Función                   |
| ------------------ | -------------: | --------------: | ------------------------- |
| `suitecrm-a1`      | `192.168.1.11` | `192.168.2.101` | Nodo 1 SuiteCRM Cliente A |
| `suitecrm-a2`      | `192.168.1.12` | `192.168.2.102` | Nodo 2 SuiteCRM Cliente A |
| `suitecrm-b1`      | `192.168.1.21` | `192.168.2.201` | Nodo 1 SuiteCRM Cliente B |
| `suitecrm-b2`      | `192.168.1.22` | `192.168.2.202` | Nodo 2 SuiteCRM Cliente B |
| `redis`            |              — |  `192.168.2.20` | Sesiones compartidas      |
| `mariadb-temporal` |              — |  `192.168.2.11` | Base de datos temporal    |

---

## 4. Flujo por cliente

### Cliente A

```text
www.clientea.com
  -> DNS
  -> reverse-proxy
  -> lb-cliente-a
  -> suitecrm-a1 / suitecrm-a2
  -> db-lb
  -> mariadb-temporal
```

### Cliente B

```text
www.clienteb.com
  -> DNS
  -> reverse-proxy
  -> lb-cliente-b
  -> suitecrm-b1 / suitecrm-b2
  -> db-lb
  -> mariadb-temporal
```

---

## 5. Base de datos temporal

Para esta fase se usa una base de datos temporal MariaDB 10.11.

Se crearon dos bases de datos:

* `suitecrm_clientea`
* `suitecrm_clienteb`

Ambas son utilizadas por los nodos SuiteCRM correspondientes:

* `suitecrm-a1` y `suitecrm-a2` -> `suitecrm_clientea`
* `suitecrm-b1` y `suitecrm-b2` -> `suitecrm_clienteb`

La conexión se hace usando el host:

```text
db-lb
```

Actualmente `db-lb` es un alias hacia `mariadb-temporal`.

Más adelante, cuando se implemente el cluster real de base de datos, este alias será reemplazado por el balanceador real del cluster de BD.

---

## 6. Redis para sesiones

Se agregó un contenedor Redis en la red interna:

```text
redis -> 192.168.2.20
```

PHP dentro de los contenedores SuiteCRM fue configurado con:

```ini
session.save_handler = redis
session.save_path = tcp://redis:6379
```

Esto permite que las sesiones sean compartidas entre los nodos del mismo cliente.

---

## 7. Volúmenes compartidos por cliente

Cada cliente tiene un volumen compartido entre sus dos nodos SuiteCRM:

* `suitecrm_clientea_app` -> usado por `suitecrm-a1` y `suitecrm-a2`
* `suitecrm_clienteb_app` -> usado por `suitecrm-b1` y `suitecrm-b2`

Esto permite compartir archivos de configuración, instalación, caché, uploads y archivos propios de SuiteCRM entre los nodos del mismo cliente.

---

## 8. Pruebas realizadas

### 8.1 Validación de contenedores

Se validó que todos los servicios estuvieran arriba:

```bash
docker compose ps
```

Servicios esperados:

* `dns`
* `reverse-proxy`
* `lb-cliente-a`
* `lb-cliente-b`
* `mariadb-temporal`
* `redis`
* `suitecrm-a1`
* `suitecrm-a2`
* `suitecrm-b1`
* `suitecrm-b2`

---

### 8.2 Validación de Redis

Se validó que PHP tenga la extensión Redis:

```bash
docker exec -it suitecrm-a1 php -m | grep redis
```

También se validó la configuración de sesiones:

```bash
docker exec -it suitecrm-a1 php -i | grep "session.save"
```

Resultado esperado:

```text
session.save_handler => redis
session.save_path => tcp://redis:6379
```

Además, después de iniciar sesión en SuiteCRM, Redis mostró claves de sesión:

```bash
docker exec -it redis redis-cli dbsize
docker exec -it redis redis-cli keys '*'
```

---

### 8.3 Validación de base de datos

Se validó la conexión a la base de datos temporal usando el alias `db-lb`:

```bash
docker exec -it suitecrm-a1 mysql --ssl=0 -h db-lb -u suitecrm_user -psuitecrm_pass -e "SHOW DATABASES;"
```

Se confirmó la existencia de:

* `suitecrm_clientea`
* `suitecrm_clienteb`

También se validó que ambas bases contienen tablas de SuiteCRM:

```bash
docker exec -it suitecrm-a1 mysql --ssl=0 -h db-lb -u suitecrm_user -psuitecrm_pass -e "SHOW TABLES FROM suitecrm_clientea;" | head
docker exec -it suitecrm-a1 mysql --ssl=0 -h db-lb -u suitecrm_user -psuitecrm_pass -e "SHOW TABLES FROM suitecrm_clienteb;" | head
```

---

### 8.4 Validación de acceso web

Se validó que el instalador ya no esté disponible:

```bash
curl -I http://www.clientea.com/install.php
curl -I http://www.clienteb.com/install.php
```

Resultado esperado:

```text
404 Not Found
```

También se validó que ambos dominios redirigen al login:

```bash
curl -I -H "Host: www.clientea.com" http://192.168.0.1/
curl -I -H "Host: www.clienteb.com" http://192.168.0.1/
```

Resultado esperado:

```text
301 Moved Permanently
location: index.php?action=Login&module=Users
```

---

### 8.5 Validación de balanceo

Se revisaron los logs de los balanceadores:

```bash
docker logs -f lb-cliente-a
docker logs -f lb-cliente-b
```

Y se enviaron varias peticiones:

```bash
for i in {1..8}; do
  curl -s -I -H "Host: www.clientea.com" http://192.168.0.1/ >/dev/null
done
```

```bash
for i in {1..8}; do
  curl -s -I -H "Host: www.clienteb.com" http://192.168.0.1/ >/dev/null
done
```

Se observó alternancia entre:

```text
cliente_a_backend/suitecrm-a1
cliente_a_backend/suitecrm-a2
```

```text
cliente_b_backend/suitecrm-b1
cliente_b_backend/suitecrm-b2
```

---

### 8.6 Validación de tolerancia a fallos

Se apagó un nodo del Cliente A:

```bash
docker stop suitecrm-a1
sleep 5
curl -I -H "Host: www.clientea.com" http://192.168.0.1/
docker start suitecrm-a1
```

El servicio siguió respondiendo desde `suitecrm-a2`.

Se apagó un nodo del Cliente B:

```bash
docker stop suitecrm-b1
sleep 5
curl -I -H "Host: www.clienteb.com" http://192.168.0.1/
docker start suitecrm-b1
```

El servicio siguió respondiendo desde `suitecrm-b2`.

---

## 9. Resultado

La fase queda funcional porque:

* Cliente A tiene dos contenedores reales SuiteCRM.
* Cliente B tiene dos contenedores reales SuiteCRM.
* Ambos clientes tienen bases de datos separadas.
* Redis guarda sesiones compartidas.
* El acceso entra por DNS y reverse proxy.
* Los balanceadores distribuyen tráfico entre nodos.
* Si un nodo cae, el otro puede seguir respondiendo.

Con esto se cumple el requisito de cluster de aplicación SuiteCRM por cliente con al menos dos contenedores por cliente.


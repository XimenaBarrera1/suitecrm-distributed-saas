# Reverse Proxy - SuiteCRM Distributed SaaS

## 1. Objetivo

Este documento describe la implementación del componente **Reverse Proxy** dentro de la arquitectura distribuida del proyecto `suitecrm-distributed-saas`.

El Reverse Proxy recibe las peticiones HTTP de los clientes y las redirige hacia el backend correspondiente según el dominio solicitado.

En esta etapa se configuraron dos dominios:

- `www.clientea.com`
- `www.clienteb.com`

Ambos dominios son resueltos por el DNS hacia la IP de entrada del sistema:

    192.168.0.1

El Reverse Proxy escucha en esa IP por el puerto `80` y decide el destino usando el encabezado HTTP `Host`.

---

## 2. Relación con la arquitectura

La arquitectura definida usa las siguientes redes:

    Red externa: 192.168.0.0/24
    Red DMZ:     192.168.1.0/24
    Red interna: 192.168.2.0/24

Distribución utilizada:

| Componente | IP |
|---|---|
| Cliente externo | `192.168.0.10` |
| Entrada del sistema | `192.168.0.1` |
| DNS | `192.168.0.2` |
| Reverse Proxy | `192.168.1.5` |
| LB Cliente A | `192.168.1.6` |
| LB Cliente B | `192.168.1.7` |

El DNS resuelve ambos dominios hacia `192.168.0.1`:

    www.clientea.com -> 192.168.0.1
    www.clienteb.com -> 192.168.0.1

Luego, el Reverse Proxy diferencia el cliente según el dominio recibido.

---

## 3. Funcionamiento del Reverse Proxy

Cuando el cliente accede a:

    http://www.clientea.com

la petición HTTP llega al Reverse Proxy con el encabezado:

    Host: www.clientea.com

Nginx identifica ese `Host` y reenvía la solicitud hacia:

    lb-cliente-a

Cuando el cliente accede a:

    http://www.clienteb.com

la petición HTTP llega con:

    Host: www.clienteb.com

Nginx identifica ese dominio y reenvía la solicitud hacia:

    lb-cliente-b

Flujo esperado:

    Cliente -> DNS -> 192.168.0.1 -> Reverse Proxy -> LB correspondiente

---

## 4. Archivos agregados

Se agregó la carpeta:

    proxy/
    ├── nginx.conf
    ├── docs/
    │   └── reverse-proxy.md
    └── test-backends/
        ├── clientea/
        │   └── index.html
        └── clienteb/
            └── index.html

También se actualizó:

    docker-compose.yml

---

## 5. Servicios agregados en Docker Compose

Se agregó el servicio:

    reverse-proxy

Este servicio:

- Usa la imagen `nginx:1.27-alpine`.
- Escucha en `192.168.0.1:80`.
- Está conectado a la red DMZ.
- Tiene IP fija `192.168.1.5`.
- Usa la configuración `proxy/nginx.conf`.

También se agregaron dos contenedores de prueba:

    lb-cliente-a
    lb-cliente-b

Estos contenedores representan temporalmente los futuros balanceadores de cada cliente. Sirven para validar que el Reverse Proxy realmente reenvía tráfico hacia un backend diferente según el dominio.

---

## 6. Backends de prueba

Los contenedores temporales son:

| Contenedor | IP DMZ | Función |
|---|---|---|
| `lb-cliente-a` | `192.168.1.6` | Simula el balanceador del Cliente A |
| `lb-cliente-b` | `192.168.1.7` | Simula el balanceador del Cliente B |

Cada uno responde con una página diferente:

    LB CLIENTE A OK
    LB CLIENTE B OK

Esto permite validar que el proxy no solo identifica el dominio, sino que también reenvía la solicitud al backend correcto.

---

## 7. Configuración de Nginx

La configuración principal está en:

    proxy/nginx.conf

Nginx tiene bloques separados para:

    www.clientea.com
    www.clienteb.com

Para Cliente A:

    www.clientea.com -> lb-cliente-a

Para Cliente B:

    www.clienteb.com -> lb-cliente-b

También se agregaron rutas de prueba:

| Ruta | Función |
|---|---|
| `/proxy-health` | Verifica que el bloque del dominio responde |
| `/route-info` | Muestra a qué backend lógico apunta el dominio |
| `/` | Prueba el reenvío real al backend correspondiente |

---

## 8. Configuración esperada en Docker Compose

El servicio `reverse-proxy` debe estar dentro del `docker-compose.yml` principal del proyecto, no en un compose separado.

Configuración esperada:

    reverse-proxy:
      image: nginx:1.27-alpine
      container_name: reverse-proxy
      ports:
        - "${ENTRYPOINT_IP}:80:80/tcp"
      volumes:
        - ./proxy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      networks:
        dmz_net:
          ipv4_address: 192.168.1.5
      restart: unless-stopped
      depends_on:
        - dns

Los backends temporales deben estar en la misma red DMZ:

    lb-cliente-a:
      image: nginx:1.27-alpine
      container_name: lb-cliente-a
      volumes:
        - ./proxy/test-backends/clientea:/usr/share/nginx/html:ro
      networks:
        dmz_net:
          ipv4_address: 192.168.1.6
      restart: unless-stopped

    lb-cliente-b:
      image: nginx:1.27-alpine
      container_name: lb-cliente-b
      volumes:
        - ./proxy/test-backends/clienteb:/usr/share/nginx/html:ro
      networks:
        dmz_net:
          ipv4_address: 192.168.1.7
      restart: unless-stopped

---

## 9. Pruebas desde la VM Server

Validar contenedores:

    docker compose ps

Resultado esperado:

    dns
    reverse-proxy
    lb-cliente-a
    lb-cliente-b

Validar configuración de Nginx:

    docker exec -it reverse-proxy nginx -t

Resultado esperado:

    syntax is ok
    test is successful

Validar DNS:

    dig @192.168.0.2 www.clientea.com
    dig @192.168.0.2 www.clienteb.com

Resultado esperado:

    www.clientea.com -> 192.168.0.1
    www.clienteb.com -> 192.168.0.1

Probar el proxy usando cabecera `Host`:

    curl -H "Host: www.clientea.com" http://192.168.0.1/
    curl -H "Host: www.clienteb.com" http://192.168.0.1/

Resultado esperado:

    LB CLIENTE A OK
    LB CLIENTE B OK

Probar información de ruta:

    curl -H "Host: www.clientea.com" http://192.168.0.1/route-info
    curl -H "Host: www.clienteb.com" http://192.168.0.1/route-info

Resultado esperado:

    cliente=clientea
    backend=lb-cliente-a

    cliente=clienteb
    backend=lb-cliente-b

---

## 10. Pruebas desde la VM Cliente

Primero se valida DNS:

    nslookup www.clientea.com
    nslookup www.clienteb.com

Resultado esperado:

    www.clientea.com -> 192.168.0.1
    www.clienteb.com -> 192.168.0.1

Luego se prueba el Reverse Proxy:

    curl http://www.clientea.com/proxy-health
    curl http://www.clienteb.com/proxy-health

Resultado esperado:

    Cliente A OK
    Cliente B OK

Probar rutas:

    curl http://www.clientea.com/route-info
    curl http://www.clienteb.com/route-info

Resultado esperado:

    cliente=clientea
    backend=lb-cliente-a

    cliente=clienteb
    backend=lb-cliente-b

Probar reenvío real al backend:

    curl http://www.clientea.com/
    curl http://www.clienteb.com/

Resultado esperado:

    LB CLIENTE A OK
    LB CLIENTE B OK

Validar puerto 80:

    nc -vz -w 3 192.168.0.1 80

Resultado esperado:

    Connection to 192.168.0.1 80 port [tcp/http] succeeded!

---

## 11. Resultado esperado

El Reverse Proxy se considera funcional cuando:

    www.clientea.com -> reverse-proxy -> lb-cliente-a
    www.clienteb.com -> reverse-proxy -> lb-cliente-b

Y desde la VM cliente se obtiene:

    LB CLIENTE A OK
    LB CLIENTE B OK

Esto demuestra que el Reverse Proxy enruta correctamente según el dominio del cliente.

---

## 12. Nota sobre los backends temporales

Los servicios `lb-cliente-a` y `lb-cliente-b` son contenedores temporales de prueba. Representan los futuros balanceadores reales de cada cliente.

Cuando se implemente el componente de balanceo de carga, estos servicios deberán ser reemplazados por balanceadores reales, manteniendo la misma lógica de nombres:

    lb-cliente-a
    lb-cliente-b

De esta forma, el Reverse Proxy ya queda preparado para integrarse con la siguiente fase del proyecto.

---

## 13. Archivos que deben subirse

Deben subirse los archivos relacionados con el Reverse Proxy:

    docker-compose.yml
    proxy/nginx.conf
    proxy/docs/reverse-proxy.md
    proxy/test-backends/clientea/index.html
    proxy/test-backends/clienteb/index.html

También debe subirse la eliminación del `Dockerfile` si existía y no se va a usar.

No deben subirse:

    .env
    dns/zones/db.clientea.com
    dns/zones/db.clienteb.com

Estos archivos son locales o generados automáticamente.

---

## 14. Comandos rápidos de verificación

Desde la VM Server:

    docker compose ps
    docker exec -it reverse-proxy nginx -t
    dig @192.168.0.2 www.clientea.com
    dig @192.168.0.2 www.clienteb.com
    curl -H "Host: www.clientea.com" http://192.168.0.1/
    curl -H "Host: www.clienteb.com" http://192.168.0.1/

Desde la VM Cliente:

    nslookup www.clientea.com
    nslookup www.clienteb.com
    curl http://www.clientea.com/
    curl http://www.clienteb.com/
    curl http://www.clientea.com/route-info
    curl http://www.clienteb.com/route-info
    nc -vz -w 3 192.168.0.1 80

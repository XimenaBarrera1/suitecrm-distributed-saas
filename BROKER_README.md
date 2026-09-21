# Broker de Mensajería para SuiteCRM

Este componente implementa un **broker de mensajes** asíncrono que detecta nuevos contactos y campañas en SuiteCRM, publica eventos a RabbitMQ y envía notificaciones por correo electrónico.

## Arquitectura

- **Monitor** (`monitor/contact_monitor.py`): consulta periódicamente la base de datos de SuiteCRM (tablas `contacts` y `campaigns`) y publica eventos a RabbitMQ.
- **RabbitMQ**: broker de mensajes que recibe los eventos y los distribuye a las colas.
- **Consumidor** (`consumer/consumer.py`): escucha la cola `notificaciones` y envía correos electrónicos usando SMTP (Gmail configurado).
- **Balanceador de BD**: el monitor se conecta a `db-lb` para alta disponibilidad.

## Configuración

### 1. Variables de entorno (para el consumidor)

En `consumer/consumer.py` se usan las siguientes variables (actualmente hardcodeadas para pruebas):

```python
RABBIT_HOST = '192.168.2.30'
RABBIT_PORT = 5672
RABBIT_USER = 'suitecrm_user'
RABBIT_PASS = 'suitecrm_pass'
RABBIT_VHOST = 'suitecrm_vhost'

SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_FROM = 'rmendozafortich@gmail.com'
SMTP_PASS = 'vjwj pwyp szbm vwga'   # Contraseña de aplicación (privada)


### Monitor (`monitor/contact_monitor.py`)

- Se conecta a `db-lb` (balanceador de base de datos).
- Consulta las tablas `contacts` y `campaigns` cada 5 segundos.
- Para contactos: obtiene el email mediante JOIN con `email_addresses`.
- Para campañas: obtiene el email del usuario asignado (`assigned_user_id`), y si no tiene, usa un email por defecto (`COALESCE`).
- Guarda los IDs procesados en `/tmp/processed_ids.txt` para no repetir eventos.
- Publica eventos a RabbitMQ con `routing_key` `contacto.creado` o `campaña.creada`.

### Consumidor (`consumer/consumer.py`)

- Se conecta a RabbitMQ con las credenciales `suitecrm_user`/`suitecrm_pass`, vhost `suitecrm_vhost`.
- Declara el exchange `eventos` (tipo `topic`, durable).
- Declara la cola `notificaciones` (durable) y la enlaza a `contacto.*` y `campaña.*`.
- Cuando recibe un evento:
  - Si es `contacto_creado`: envía correo al email del contacto (o fallback si no tiene).
  - Si es `campaña_creada`: envía correo al email del usuario asignado a la campaña (o fallback).
- Usa SMTP de Gmail con contraseña de aplicación (configurada en el código).

### Configuración SMTP (Gmail)

```python
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_FROM = 'rmendozafortich@gmail.com'
SMTP_PASS = 'vjwj pwyp szbm vwga'   # Contraseña de aplicación (privada)

Cómo probar el broker
equisitos previos
SuiteCRM debe estar funcionando en http://clientea.com (accesible desde Kali).

Todos los contenedores de Docker del proyecto deben estar levantados (dns, reverse-proxy, db-lb, suitecrm-a1, rabbitmq, consumer, etc.).

El monitor debe estar en ejecución (ver más abajo).

Levantar el monitor (si no está corriendo)
El monitor se encuentra en ~/monitor (fuera del repositorio, pero puedes copiarlo dentro del proyecto). Para ejecutarlo:

cd ~/monitor
docker build -t contact-monitor .
docker stop contact-monitor 2>/dev/null; docker rm contact-monitor 2>/dev/null
docker run -d --name contact-monitor --network internal_net contact-monitor

Verificar logs:
docker logs -f contact-monitor

Debe mostrar Monitor iniciado. IDs procesados previamente: X y luego conexiones exitosas a RabbitMQ y a la base de datos.

Asegurar que el consumidor esté corriendo
Dentro del proyecto principal:

bash
cd ~/suitecrm-distributed-saas
docker-compose ps | grep consumer   # Debe estar Up

Si no, levantarlo:

bash
docker-compose up -d consumer
Ver logs del consumidor:

bash
docker logs -f consumer
Debe mostrar Consumidor listo. Esperando mensajes....

3. Probar con un contacto nuevo
Accede a http://clientea.com desde Kali.

Ve a Contacts → Create Contact.

Llena:

First Name: PruebaBroker

Last Name: Contacto

Email Address: un email real (por ejemplo, el tuyo o rmendozafortich@gmail.com)

(opcional) teléfono.

Guarda.

Resultado esperado:

En los logs del monitor (en tiempo real) debe aparecer:

text
Publicado contacto_creado: PruebaBroker Contacto (ID: ...)


En los logs del consumidor debe aparecer:

text
Evento recibido: {'tipo': 'contacto_creado', ...}
Correo enviado a [email_del_contacto]
El correo debe llegar a la bandeja de entrada (revisar spam).

Probar con una campaña nueva
En SuiteCRM, ve a Campaigns → Create Campaign.

Elige cualquier tipo (ej. "Non-email based Campaign").

Name: PruebaCampañaBroker

Assigned to: selecciona un usuario que tenga email (o deja el administrador, pero si no tiene email usará el fallback).

Guarda.

Resultado esperado:

Logs del monitor:

text
Publicado campaña_creada: PruebaCampañaBroker (ID: ...)

Logs del consumidor:

text
Evento recibido: {'tipo': 'campaña_creada', ...}
Correo enviado a [email_del_usuario_asignado_o_fallback]


El correo debe llegar al destinatario correspondiente.

5. Prueba adicional con productor manual (sin SuiteCRM)
Para verificar que RabbitMQ y el consumidor funcionan independientemente:

bash
cd ~/suitecrm-distributed-saas
docker run --rm --network internal_net -v $(pwd):/app -w /app python:3.11-slim bash -c "pip install pika && python test_producer.py"
Verás Mensaje enviado a RabbitMQ y luego en los logs del consumidor aparecerá el evento de ejemplo.

Mantenimiento y solución de problemas
El monitor da error WSREP has not yet prepared node
Es un error transitorio del clúster Galera. El monitor reintentará automáticamente. Si persiste, reinicia el clúster.

El consumidor no recibe eventos
Verificar que RabbitMQ esté corriendo: docker ps | grep rabbitmq

Verificar que el consumidor tenga los bindings correctos: en consumer.py debe haber channel.queue_bind(..., routing_key='contacto.*') y routing_key='campaña.*'.

Revisar logs del consumidor: docker logs consumer.

Los correos no llegan
Verificar credenciales SMTP (contraseña de aplicación de Gmail). Si expiró, generar una nueva en https://myaccount.google.com/apppasswords

Revisar que el consumidor tenga acceso a internet (el contenedor debe tener red con salida, aunque por defecto usa internal_net; para Gmail necesita salida a internet, pero está usando el host con NAT, debería funcionar).



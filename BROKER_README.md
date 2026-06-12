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

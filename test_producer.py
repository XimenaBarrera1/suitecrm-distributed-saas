import pika
import json

credentials = pika.PlainCredentials('suitecrm_user', 'suitecrm_pass')
parameters = pika.ConnectionParameters(
    host='192.168.2.30',
    port=5672,
    virtual_host='suitecrm_vhost',
    credentials=credentials
)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.exchange_declare(exchange='eventos', exchange_type='topic', durable=True)

evento = {
    "tipo": "contacto_creado",
    "nombre": "Roger Perez",
    "email": "roger@example.com"
}

channel.basic_publish(
    exchange='eventos',
    routing_key='contacto.creado',
    body=json.dumps(evento)
)
print("Mensaje enviado a RabbitMQ")
connection.close()


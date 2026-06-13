import pika
import json

credentials = pika.PlainCredentials(
    "suitecrm_user",
    "suitecrm_pass"
)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host="192.168.2.30",
        port=5672,
        virtual_host="suitecrm_vhost",
        credentials=credentials
    )
)

channel = connection.channel()

channel.basic_publish(
    exchange="eventos",
    routing_key="contacto.creado",
    body=json.dumps({
        "tipo": "contacto_creado",
        "nombre": "Roger Prueba",
        "email": "rmendozafortich@gmail.com"
    })
)

print("Mensaje enviado")

connection.close()

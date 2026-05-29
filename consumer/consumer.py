import pika
import smtplib
from email.message import EmailMessage
import os
import json
import logging
import time

RABBIT_HOST = os.getenv('RABBITMQ_HOST', '192.168.2.30')
RABBIT_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBIT_USER = os.getenv('RABBITMQ_USER', 'suitecrm_user')
RABBIT_PASS = os.getenv('RABBITMQ_PASS', 'suitecrm_pass')
RABBIT_VHOST = os.getenv('RABBITMQ_VHOST', 'suitecrm_vhost')
SMTP_HOST = os.getenv('SMTP_HOST', '192.168.2.35')
SMTP_PORT = int(os.getenv('SMTP_PORT', 1025))
SMTP_FROM = os.getenv('SMTP_FROM', 'no-reply@suitecrm.com')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = to_email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.send_message(msg)
        logging.info(f"Correo enviado a {to_email}")
    except Exception as e:
        logging.error(f"Error enviando correo: {e}")

def callback(ch, method, properties, body):
    try:
        event = json.loads(body)
        logging.info(f"Evento recibido: {event}")
        if event.get('tipo') == 'contacto_creado':
            to = event.get('email', 'test@example.com')
            subject = "Nuevo contacto creado"
            message = f"Se creó el contacto: {event.get('nombre')} - {event.get('email')}"
            send_email(to, subject, message)
        else:
            logging.info(f"Evento ignorado (tipo={event.get('tipo')})")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.error(f"Error procesando mensaje: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    while True:
        try:
            credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBIT_HOST,
                port=RABBIT_PORT,
                virtual_host=RABBIT_VHOST,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.exchange_declare(exchange='eventos', exchange_type='topic', durable=True)
            channel.queue_declare(queue='notificaciones', durable=True)
            channel.queue_bind(exchange='eventos', queue='notificaciones', routing_key='contacto.*')
            channel.basic_consume(queue='notificaciones', on_message_callback=callback, auto_ack=False)
            logging.info("Consumidor listo. Esperando mensajes...")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            logging.error("No se pudo conectar a RabbitMQ. Reintentando en 5 segundos...")
            time.sleep(5)
        except KeyboardInterrupt:
            logging.info("Consumidor detenido manualmente")
            break

if __name__ == "__main__":
    main()

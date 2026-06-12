import pika
import smtplib
from email.message import EmailMessage
import os
import json
import logging
import time

# --- CONFIGURACIÓN FIJA ---
RABBIT_HOST = '192.168.2.30'
RABBIT_PORT = 5672
RABBIT_USER = 'suitecrm_user'
RABBIT_PASS = 'suitecrm_pass'
RABBIT_VHOST = 'suitecrm_vhost'

# *** CREDENCIALES DE CORREO REAL (Gmail) ***
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_FROM = 'rmendozafortich@gmail.com'
SMTP_PASS = 'vjwj pwyp szbm vwga'   # Contraseña de aplicación (16 dígitos)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_email(to_email, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = to_email
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_FROM, SMTP_PASS)
            server.send_message(msg)
        logging.info(f"Correo enviado a {to_email}")
    except Exception as e:
        logging.error(f"Error enviando correo: {e}")

def callback(ch, method, properties, body):
    try:
        event = json.loads(body)
        logging.info(f"Evento recibido: {event}")
        if event.get('tipo') == 'contacto_creado':
            to = event.get('email', 'rmendozafortich@gmail.com')
            subject = "Nuevo contacto creado"
            nombre = event.get('nombre', 'Desconocido')
            message = f"Se creó el contacto: {nombre}"
            send_email(to, subject, message)
        elif event.get('tipo') == 'campaña_creada':
            to = event.get('email', 'rmendozafortich@gmail.com')
            subject = "Nueva campaña creada"
            nombre_campania = event.get('nombre', 'Sin nombre')
            message = f"Se ha creado una nueva campaña: {nombre_campania}"
            send_email(to, subject, message)
        else:
            logging.info(f"Evento ignorado (tipo desconocido): {event.get('tipo')}")
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
            # Enlazar la cola para recibir eventos de contactos y campañas
            channel.queue_bind(exchange='eventos', queue='notificaciones', routing_key='contacto.*')
            channel.queue_bind(exchange='eventos', queue='notificaciones', routing_key='campaña.*')
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

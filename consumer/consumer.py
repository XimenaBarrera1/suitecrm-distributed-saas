import pika
import smtplib
from email.message import EmailMessage
import os
import json
import logging
import time

# =========================
# Configuración RabbitMQ
# =========================
RABBIT_HOST = os.environ.get('RABBITMQ_HOST', '192.168.2.30')
RABBIT_PORT = int(os.environ.get('RABBITMQ_PORT', 5672))
RABBIT_USER = os.environ.get('RABBITMQ_USER', 'suitecrm_user')
RABBIT_PASS = os.environ.get('RABBITMQ_PASS', 'suitecrm_pass')
RABBIT_VHOST = os.environ.get('RABBITMQ_VHOST', 'suitecrm_vhost')

# =========================
# Configuración SMTP
# =========================
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_FROM = os.environ.get('SMTP_FROM', 'rmendozafortich@gmail.com')
SMTP_PASS = os.environ.get('SMTP_PASS', '')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==================================================
# ENVÍO DE CORREO HTML
# ==================================================
def send_email(to_email, subject, html_content):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SMTP_FROM
    msg['To'] = to_email

    msg.set_content("Este correo requiere un cliente compatible con HTML.")
    msg.add_alternative(html_content, subtype='html')

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_FROM, SMTP_PASS)
            server.send_message(msg)
        logging.info(f"Correo enviado a {to_email}")
    except Exception as e:
        logging.error(f"Error enviando correo: {e}")

# ==================================================
# PLANTILLA CONTACTO
# ==================================================
def build_contact_email(event):
    nombre = event.get('nombre', 'No disponible')
    correo = event.get('email', 'No disponible')
    contacto_id = event.get('id', 'No disponible')
    fecha = event.get('fecha_creacion', 'No disponible')
    tenant = event.get('tenant', 'Desconocido').replace('suitecrm_', '').upper()

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f4f6f9; padding:20px;">
        <div style="max-width:700px; margin:auto; background:white; border-radius:10px; overflow:hidden; box-shadow:0 0 10px rgba(0,0,0,0.1);">
            <div style="background:#0b5ed7; color:white; padding:20px;">
                <h2>SuiteCRM - Notificación de Contacto ({tenant})</h2>
            </div>
            <div style="padding:25px;">
                <h3>Nuevo contacto registrado correctamente</h3>
                <p>Se ha detectado la creación de un nuevo contacto en la plataforma.</p>
                <table style="width:100%; border-collapse:collapse;">
                    <tr>
                        <td style="padding: 5px 0;"><strong>Cliente/Tenant:</strong></td>
                        <td style="padding: 5px 0;">{tenant}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 0;"><strong>ID:</strong></td>
                        <td style="padding: 5px 0;">{contacto_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 0;"><strong>Nombre:</strong></td>
                        <td style="padding: 5px 0;">{nombre}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 0;"><strong>Correo:</strong></td>
                        <td style="padding: 5px 0;">{correo}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 0;"><strong>Fecha:</strong></td>
                        <td style="padding: 5px 0;">{fecha}</td>
                    </tr>
                </table>
                <br>
                <p>Este mensaje fue generado automáticamente por el sistema distribuido SuiteCRM.</p>
            </div>
            <div style="background:#f1f1f1; padding:15px; text-align:center; color:#666; font-size:12px;">
                Proyecto Sistemas Distribuidos - SuiteCRM SaaS
            </div>
        </div>
    </body>
    </html>
    """

# ==================================================
# PLANTILLA CAMPAÑA
# ==================================================
def build_campaign_email(event):
    nombre = event.get('nombre', 'No disponible')
    campania_id = event.get('id', 'No disponible')
    fecha = event.get('fecha_creacion', 'No disponible')
    estado = event.get('estado', 'Activa')
    tenant = event.get('tenant', 'Desconocido').replace('suitecrm_', '').upper()

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f4f6f9; padding:20px;">
        <div style="max-width:700px; margin:auto; background:white; border-radius:10px; overflow:hidden; box-shadow:0 0 10px rgba(0,0,0,0.1);">
            <div style="background:#198754; color:white; padding:20px;">
                <h2>SuiteCRM - Nueva Campaña ({tenant})</h2>
            </div>
            <div style="padding:25px;">
                <h3>Campaña registrada exitosamente</h3>
                <p>Se ha creado una nueva campaña de marketing dentro de SuiteCRM.</p>
                <table style="width:100%; border-collapse:collapse;">
                    <tr>
                        <td style="padding: 5px 0;"><strong>Cliente/Tenant:</strong></td>
                        <td style="padding: 5px 0;">{tenant}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 0;"><strong>ID:</strong></td>
                        <td style="padding: 5px 0;">{campania_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 0;"><strong>Nombre:</strong></td>
                        <td style="padding: 5px 0;">{nombre}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 0;"><strong>Estado:</strong></td>
                        <td style="padding: 5px 0;">{estado}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 0;"><strong>Fecha:</strong></td>
                        <td style="padding: 5px 0;">{fecha}</td>
                    </tr>
                </table>
                <br>
                <p>El evento fue procesado mediante RabbitMQ y notificado por correo electrónico.</p>
            </div>
            <div style="background:#f1f1f1; padding:15px; text-align:center; color:#666; font-size:12px;">
                Proyecto Sistemas Distribuidos - SuiteCRM SaaS
            </div>
        </div>
    </body>
    </html>
    """

# ==================================================
# CALLBACK
# ==================================================
def callback(ch, method, properties, body):
    try:
        event = json.loads(body)
        logging.info(f"Evento recibido: {event}")
        
        # Extraemos el tenant para el asunto del correo y lo limpiamos un poco
        tenant = event.get('tenant', 'Desconocido').replace('suitecrm_', '').upper()

        if event.get('tipo') == 'contacto_creado':
            to = event.get('email', SMTP_FROM)
            html = build_contact_email(event)
            send_email(
                to,
                f"✅ Nuevo contacto registrado en SuiteCRM ({tenant})",
                html
            )

        elif event.get('tipo') == 'campaña_creada':
            to = event.get('email', SMTP_FROM)
            html = build_campaign_email(event)
            send_email(
                to,
                f"📢 Nueva campaña creada en SuiteCRM ({tenant})",
                html
            )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logging.error(f"Error procesando mensaje: {e}")
        ch.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False
        )

# ==================================================
# MAIN
# ==================================================
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

            channel.exchange_declare(
                exchange='eventos',
                exchange_type='topic',
                durable=True
            )

            channel.queue_declare(
                queue='notificaciones',
                durable=True
            )

            channel.queue_bind(
                exchange='eventos',
                queue='notificaciones',
                routing_key='contacto.*'
            )

            channel.queue_bind(
                exchange='eventos',
                queue='notificaciones',
                routing_key='campaña.*'
            )

            channel.basic_consume(
                queue='notificaciones',
                on_message_callback=callback,
                auto_ack=False
            )

            logging.info("Consumidor listo. Esperando mensajes...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            logging.error("No se pudo conectar a RabbitMQ. Reintentando en 5s...")
            time.sleep(5)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
import pika
import mysql.connector
import json
import time
import logging
import os

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de la base de datos (usando el balanceador db-lb)
DB_CONFIG = {
    'host': 'db-lb',
    'user': 'suitecrm_user',
    'password': 'suitecrm_pass',
    'database': 'suitecrm_clientea',
    'port': 3306
}

# Configuración de RabbitMQ
RABBIT_CONFIG = {
    'host': '192.168.2.30',
    'port': 5672,
    'user': 'suitecrm_user',
    'password': 'suitecrm_pass',
    'vhost': 'suitecrm_vhost',
    'exchange': 'eventos'
}

PROCESSED_FILE = '/tmp/processed_ids.txt'   # Guarda IDs de contactos y campañas ya procesados

def load_processed_ids():
    if os.path.exists(PROCESSED_FILE):
        with open(PROCESSED_FILE, 'r') as f:
            return set(line.strip() for line in f)
    return set()

def save_processed_ids(ids):
    with open(PROCESSED_FILE, 'w') as f:
        for id_ in ids:
            f.write(f"{id_}\n")

def connect_rabbitmq():
    credentials = pika.PlainCredentials(RABBIT_CONFIG['user'], RABBIT_CONFIG['password'])
    parameters = pika.ConnectionParameters(
        host=RABBIT_CONFIG['host'],
        port=RABBIT_CONFIG['port'],
        virtual_host=RABBIT_CONFIG['vhost'],
        credentials=credentials,
        heartbeat=600
    )
    return pika.BlockingConnection(parameters)

def publish_event(record, event_type):
    """
    Publica un evento en RabbitMQ.
    - record: diccionario con los datos del registro (contacto o campaña)
    - event_type: 'contacto_creado' o 'campaña_creada'
    """
    try:
        connection = connect_rabbitmq()
        channel = connection.channel()
        channel.exchange_declare(exchange=RABBIT_CONFIG['exchange'], exchange_type='topic', durable=True)

        if event_type == 'contacto_creado':
            message = json.dumps({
                'tipo': event_type,
                'id': record['id'],
                'nombre': f"{record.get('first_name', '')} {record.get('last_name', '')}".strip(),
                'email': record.get('email', ''),
                'fecha_creacion': str(record['date_entered'])
            })
            routing_key = 'contacto.creado'
            log_name = record.get('first_name', '') + ' ' + record.get('last_name', '')
        elif event_type == 'campaña_creada':
            message = json.dumps({
                'tipo': event_type,
                'id': record['id'],
                'nombre': record.get('name', ''),
                'email': record.get('user_email', ''),   # email del usuario asignado
                'fecha_creacion': str(record['date_entered'])
            })
            routing_key = 'campaña.creada'
            log_name = record.get('name', '')
        else:
            return

        channel.basic_publish(exchange=RABBIT_CONFIG['exchange'], routing_key=routing_key, body=message)
        logging.info(f"Publicado {event_type}: {log_name} (ID: {record['id']})")
        connection.close()
    except Exception as e:
        logging.error(f"Error publicando evento {event_type}: {e}")

# --- Consultas a la base de datos ---
def fetch_all_contacts():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.id, c.first_name, c.last_name, c.date_entered,
                   ea.email_address as email
            FROM contacts c
            LEFT JOIN email_addr_bean_rel eab ON eab.bean_id = c.id
                AND eab.bean_module = 'Contacts' AND eab.primary_address = 1
            LEFT JOIN email_addresses ea ON ea.id = eab.email_address_id
        """
        cursor.execute(query)
        contacts = cursor.fetchall()
        cursor.close()
        conn.close()
        return contacts
    except Exception as e:
        logging.error(f"Error consultando contactos: {e}")
        return []

def fetch_all_campaigns():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.id, c.name, c.date_entered,
                   COALESCE(ea.email_address, 'rmendozafortich@gmail.com') as user_email
            FROM campaigns c
            LEFT JOIN users u ON u.id = c.assigned_user_id
            LEFT JOIN email_addr_bean_rel eab ON eab.bean_id = u.id
                AND eab.bean_module = 'Users' AND eab.primary_address = 1
            LEFT JOIN email_addresses ea ON ea.id = eab.email_address_id
        """
        cursor.execute(query)
        campaigns = cursor.fetchall()
        cursor.close()
        conn.close()
        return campaigns
    except Exception as e:
        logging.error(f"Error consultando campañas: {e}")
        return []

def main():
    processed = load_processed_ids()
    logging.info(f"Monitor iniciado. IDs procesados previamente: {len(processed)}")

    while True:
        try:
            # --- Monitoreo de contactos ---
            contacts = fetch_all_contacts()
            new_contacts = 0
            for contact in contacts:
                if contact['id'] not in processed:
                    publish_event(contact, 'contacto_creado')
                    processed.add(contact['id'])
                    new_contacts += 1

            # --- Monitoreo de campañas ---
            campaigns = fetch_all_campaigns()
            new_campaigns = 0
            for campaign in campaigns:
                if campaign['id'] not in processed:
                    publish_event(campaign, 'campaña_creada')
                    processed.add(campaign['id'])
                    new_campaigns += 1

            # Guardar el conjunto actualizado si hubo novedades
            if new_contacts or new_campaigns:
                save_processed_ids(processed)
                logging.info(f"Procesados: {new_contacts} nuevos contactos, {new_campaigns} nuevas campañas. Total en historial: {len(processed)}")

        except Exception as e:
            logging.error(f"Error en ciclo principal: {e}")
        time.sleep(5)   # Espera 5 segundos antes de la siguiente iteración

if __name__ == "__main__":
    main()

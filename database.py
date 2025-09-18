import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database="zabbix"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def execute_query(query):
    conn = get_db_connection()
    if conn is None:
        return "Error: No se pudo conectar a la base de datos."
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except mysql.connector.Error as err:
        return f"Error al ejecutar la consulta: {err}"
    finally:
        cursor.close()
        conn.close()

import llm_integration
import database
import re
import logging

# Configurar el logging para que escriba en sql.log
logging.basicConfig(filename='sql.log', 
                    level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

def main():
    print("Iniciando chatbot...")
    chat_session = llm_integration.create_session()
    print("Chatbot listo. Escribe 'salir' para terminar.")

    while True:
        user_input = input("Tú: ")
        if user_input.lower() == 'salir':
            break

        llm_response = llm_integration.send_message(chat_session, user_input)

        sql_query_match = re.search(r"```sql\n(.*?)\n```", llm_response, re.DOTALL)

        if sql_query_match:
            sql_query = sql_query_match.group(1).strip()
            # Registrar la consulta en el archivo de log en lugar de imprimirla
            logging.info(f"Ejecutando consulta: {sql_query}")
            db_result = database.execute_query(sql_query)
            
            # Volver a enviar el resultado de la BD al LLM para que lo interprete
            follow_up_message = f"El resultado de la consulta '{sql_query}' es: {db_result}. Por favor, interpreta este resultado para el usuario."
            final_response = llm_integration.send_message(chat_session, follow_up_message)
            print(f"Chatbot: {final_response}")
        else:
            print(f"Chatbot: {llm_response}")

if __name__ == "__main__":
    main()

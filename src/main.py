import os
from dotenv import load_dotenv
from src.agents import orquestador

load_dotenv()

def main():
    print("==================================================")
    print("¡Sistema Multiagente de Energía Solar Iniciado!")
    print("Escribe 'salir' para terminar el chat.")
    print("Escribe 'estado' para auditar los datos del cliente.")
    print("==================================================\n")
    
    while True:
        user_input = input("Cliente: ")
        if user_input.lower() == "salir":
            print("Cerrando sesión de asesoramiento solar...")
            break
            
        if user_input.lower() == "estado":
            print(f"\n🔍 [AUDITORÍA DE ESTADO] Datos actuales en memoria:\n{orquestador.estado.datos_cliente}\n")
            continue
            
        if not user_input.strip():
            continue
            
        respuesta = orquestador.procesar_mensaje(user_input)
        print(f"Sistema: {respuesta}\n")

if __name__ == "__main__":
    main()

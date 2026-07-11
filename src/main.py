import os
from dotenv import load_dotenv
from src.agents import solar_orchestrator
from src.state import SolarProjectState

load_dotenv()

def main():
    print("==================================================")
    print("¡Sistema Multiagente de Energía Solar Activo (Sesiones)!")
    print("Escribe 'salir' para terminar el chat.")
    print("Escribe 'estado' para auditar los datos del cliente.")
    print("==================================================\n")
    
    # Inicialización del estado limpio basado en tu clase de Pydantic
    state_instance = SolarProjectState()
    
    while True:
        user_input = input("Cliente: ")
        
        if user_input.lower() == "salir":
            print("Cerrando sesión de asesoramiento solar...")
            break
            
        if user_input.lower() == "estado":
            print(f"\n🔍 [AUDITORÍA DE ESTADO] Datos actuales en memoria:\n{state_instance.datos_cliente}\n")
            continue
            
        if not user_input.strip():
            continue
            
        try:
            # 1. El orquestador decide qué agente toma el control
            agente_elegido = solar_orchestrator.route_request(user_input, state_instance.datos_cliente)
            
            # 2. El subagente genera la respuesta final manteniendo la sesión viva internamente
            respuesta_texto = agente_elegido.responder(user_input, state_instance.datos_cliente)
            
            print(f"[{agente_elegido.name}]: {respuesta_texto}\n")
            
        except Exception as e:
            print(f"❌ [Error]: {str(e)}\n")

if __name__ == "__main__":
    main()

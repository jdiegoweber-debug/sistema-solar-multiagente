import sys # Importamos el módulo del sistema para interactuar con variables y funciones del intérprete
from src.state import SolarProjectState # Importamos tu modelo de Pydantic para la gestión de datos estructurados

# ¡Acá estaba el error! Cambiamos 'src.agents' por 'src.agent' en singular para que coincida con tu archivo real
from src.agent import solar_orchestrator 

def main():
    """
    Función principal que inicia el bucle de conversación interactiva en la consola.
    """
    print("=" * 60)
    print("☀️  SISTEMA MULTIAGENTE DE ASESORAMIENTO SOLAR ☀️")
    print("=" * 60)
    print("Escribí tu consulta. Para ver el estado actual, escribí 'estado'.")
    print("Para salir, escribí 'salir'.\n")

    # Instanciamos el estado común usando tu clase Pydantic BaseModel
    state = SolarProjectState()
    
    # Identificador único de sesión para separar los hilos de chat históricos
    session_id = "consola_default"

    while True:
        try:
            # Capturamos el mensaje que ingresa el usuario en la terminal eliminando espacios vacíos
            user_input = input("👤 Cliente: ").strip()
            
            # Si el usuario apretó ENTER sin escribir nada, salteamos el turno para evitar procesar strings vacíos
            if not user_input:
                continue

            # Comando especial de auditoría en tiempo real documentado en tu README
            if user_input.lower() == "estado":
                print("\n" + "📊" * 15)
                print("🛠️  [AUDITORÍA DE ESTADO COMPARTIDO]")
                print(f"Datos actuales: {state.datos_cliente}")
                print("📊" * 15 + "\n")
                continue

            # 1. El orquestador extrae información en segundo plano y elige el agente experto idóneo
            # Le pasamos el diccionario interno (.datos_cliente) para que mute dinámicamente con el JSON extractor
            agente_elegido = solar_orchestrator.route_request(user_input, state.datos_cliente)

            # 2. El subagente procesa el mensaje usando su contexto inyectado y su memoria histórica
            respuesta = agente_elegido.responder(
                mensaje_usuario=user_input, 
                datos_cliente=state.datos_cliente, 
                session_id=session_id
            )

            # Imprimimos la respuesta en pantalla visibilizando explícitamente qué agente del sistema respondió
            print(f"\n🤖 [{agente_elegido.name}]: {respuesta}\n")

            # Regla de salida para cortar el bucle si el usuario se despide
            if any(word in user_input.lower() for word in ["salir", "chau", "adios", "hasta luego", "terminar"]):
                print("👋 Sistema cerrado correctamente. ¡Éxitos en la presentación!")
                break

        except (KeyboardInterrupt, EOFError):
            # Control de excepciones por si el usuario presiona Ctrl+C para cerrar la terminal de golpe
            print("\n👋 Programa interrumpido por el usuario.")
            sys.exit(0)
        except Exception as e:
            # Capturamos cualquier error en el flujo para que el chat no se caiga de forma catastrófica
            print(f"\n❌ Ocurrió un error en el flujo agéntico: {e}\n")

if __name__ == "__main__":
    main()

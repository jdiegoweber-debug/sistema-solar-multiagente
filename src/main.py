import sys # Módulo para interactuar con funciones esenciales del sistema operativo e intérpretes de Python
from src.state import SolarProjectState # Cargamos tu esquema Pydantic para manejar de forma segura la memoria del cliente

# Importamos la clase constructora del orquestador desde tu archivo en plural
from src.agents import OrquestadorSolar

def main():
    """
    Función principal que arranca la consola interactiva del sistema multiagente solar.
    """
    print("=" * 60)
    print("☀️  SISTEMA MULTIAGENTE DE ASESORAMIENTO SOLAR ☀️")
    print("=" * 60)
    print("Escribí tu consulta. Para ver el estado actual, escribí 'estado'.")
    print("Para salir, escribí 'salir'.\n")

    # Inicializamos la memoria común compartida usando tu clase base de Pydantic
    state = SolarProjectState()
    
    # Creamos la instancia local del orquestador directamente aquí para evitar fallas de importación
    solar_orchestrator = OrquestadorSolar()
    
    # Identificador único de sesión para hilos de chat independientes (consola local por defecto)
    session_id = "consola_default"

    while True:
        try:
            # Leemos lo que escribe el cliente en la terminal removiendo espacios en blanco accidentales
            user_input = input("👤 Cliente: ").strip()
            
            # Si el usuario solo presionó la tecla ENTER sin texto, ignoramos el turno y continuamos el bucle
            if not user_input:
                continue

            # Comando especial de auditoría de memoria compartida documentado en tu archivo README.md
            if user_input.lower() == "estado":
                print("\n" + "📊" * 15)
                print("🛠️  [AUDITORÍA DE ESTADO COMPARTIDO]")
                print(f"Datos actuales: {state.datos_cliente}")
                print("📊" * 15 + "\n")
                continue

            # Paso 1: El orquestador solar extrae datos en segundo plano y enruta dinámicamente al experto idóneo
            # Pasamos directamente el diccionario '.datos_cliente' para que el extractor JSON lo mute en tiempo real
            agente_elegido = solar_orchestrator.route_request(user_input, state.datos_cliente)

            # Paso 2: El subagente experto responde la duda técnica o comercial basándose en el historial unificado
            respuesta = agente_elegido.responder(
                mensaje_usuario=user_input, 
                datos_cliente=state.datos_cliente, 
                session_id=session_id
            )

            # Mostramos el veredicto en la terminal explicitando con claridad el nombre del agente que tomó la palabra
            print(f"\n🤖 [{agente_elegido.name}]: {respuesta}\n")

            # Condición de salida si el cliente ingresa una palabra clave de despedida comercial
            if any(word in user_input.lower() for word in ["salir", "chau", "adios", "hasta luego", "terminar"]):
                print("🔒 Sesión finalizada correctamente por el usuario.")
                break

        except (KeyboardInterrupt, EOFError):
            # Capturamos si el usuario presiona las teclas de interrupción del sistema para un cierre limpio
            print("\n🔒 Sesión interrumpida.")
            sys.exit(0)
        except Exception as e:
            # Evitamos que errores imprevistos cuelguen la ejecución del programa completo
            print(f"\n❌ Ocurrió un error inesperado en el flujo agéntico: {e}\n")

if __name__ == "__main__":
    main()

import sys # Importamos el módulo del sistema para interactuar con el intérprete y forzar cierres limpios
from src.state import SolarProjectState # Importamos la clase de Pydantic que armaste para validar los datos del cliente

# Importamos directamente tu orquestador. Tu archivo en el Git se llama 'src/agent.py' en singular.
# La variable instanciada al final de ese archivo se llama exactamente 'solar_orchestrator'.
from src.agent import solar_orchestrator 

def main():
    """
    Punto de entrada principal para ejecutar la interfaz de chat conversacional del sistema solar.
    """
    print("=" * 60)
    print("☀️  SISTEMA MULTIAGENTE DE ASESORAMIENTO SOLAR ☀️")
    print("=" * 60)
    print("Escribí tu consulta. Para ver el estado actual, escribí 'estado'.")
    print("Para salir, escribí 'salir'.\n")

    # Inicializamos el estado compartido en blanco usando tu esquema estructurado de Pydantic
    state = SolarProjectState()
    
    # Identificador único de sesión requerido por tus chats históricos de Gemini para no perder el hilo
    session_id = "consola_default"

    while True:
        try:
            # Leemos la terminal del usuario eliminando espacios en blanco accidentales en los extremos
            user_input = input("👤 Cliente: ").strip()
            
            # Si el usuario presionó ENTER sin redactar texto, salteamos el ciclo para evitar llamadas vacías a la API
            if not user_input:
                continue

            # Comando secreto de auditoría local que documentaste en el archivo instructivo README.md
            if user_input.lower() == "estado":
                print("\n" + "📊" * 15)
                print("🛠️  [AUDITORÍA DE ESTADO COMPARTIDO]")
                # Imprime en pantalla el diccionario de datos interno mutado hasta el momento
                print(f"Datos actuales: {state.datos_cliente}")
                print("📊" * 15 + "\n")
                continue

            # Paso 1: El Orquestador analiza el texto, extrae datos mediante el JSON extractor y elige el agente ideal
            # Mandamos directo el diccionario 'state.datos_cliente' para que se actualice por referencia en segundo plano
            agente_elegido = solar_orchestrator.route_request(user_input, state.datos_cliente)

            # Paso 2: El subagente seleccionado toma el control, ejecuta sus herramientas (RAG/MCP) y formula la respuesta
            respuesta = agente_elegido.responder(
                mensaje_usuario=user_input, 
                datos_cliente=state.datos_cliente, 
                session_id=session_id
            )

            # Imprimimos el veredicto final aclarando explícitamente en los corchetes qué subagente elaboró la respuesta
            print(f"\n🤖 [{agente_elegido.name}]: {respuesta}\n")

            # Condición de quiebre para despedirse y apagar el sistema ordenadamente
            if any(word in user_input.lower() for word in ["salir", "chau", "adios", "hasta luego", "terminar", "cerrar"]):
                print("👋 Sistema conversacional cerrado de forma limpia. ¡Éxitos en la entrega!")
                break

        except (KeyboardInterrupt, EOFError):
            # Bloque de captura por si el usuario interrumpe la ejecución apretando Ctrl+C en la consola de comandos
            print("\n👋 Ejecución finalizada por el usuario de forma externa.")
            sys.exit(0)
        except Exception as e:
            # Captura global de incidentes para evitar bloqueos del sistema o caídas críticas de la aplicación
            print(f"\n❌ Ocurrió una anomalía en el ciclo del multiagente: {e}\n")

if __name__ == "__main__":
    main()

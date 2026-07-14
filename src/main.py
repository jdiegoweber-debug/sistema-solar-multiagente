import sys # Módulo para interactuar con funciones esenciales del sistema operativo e intérpretes de Python
import os # Módulo para verificar la existencia de rutas de archivos en el disco local
from src.state import SolarProjectState # Cargamos tu esquema Pydantic para manejar de forma segura la memoria del cliente

# Importamos directamente el módulo completo de agentes para inspeccionarlo dinámicamente
import src.agents as agents_module

def main():
    """
    Función principal que arranca la consola interactiva del sistema multiagente solar con soporte multimodal.
    """
    print("=" * 60)
    print("☀️  SISTEMA MULTIAGENTE DE ASESORAMIENTO SOLAR MULTIMODAL ☀️")
    print("=" * 60)
    print("Escribí tu consulta de forma normal.")
    print("Para adjuntar un archivo local, usá el formato: mensaje | archivo: ruta_de_tu_factura.jpg")
    print("Para ver el estado actual, escribí 'estado'. Para salir, escribí 'salir'.\n")

    # Inicializamos la memoria común compartida usando tu clase base de Pydantic
    state = SolarProjectState()
    
    # --- CAPA DE SEGURIDAD ABSOLUTA DE INSTANCIACIÓN ---
    # Detectamos de forma dinámica cómo quedó declarada la variable u objeto en src/agents.py
    solar_orchestrator = None
    
    if hasattr(agents_module, "solar_orchestrator") and getattr(agents_module, "solar_orchestrator") is not None:
        solar_orchestrator = agents_module.solar_orchestrator
    elif hasattr(agents_module, "OrquestadorSolar"):
        # Si la instancia no existía, la creamos en el acto invocando al constructor de la clase
        solar_orchestrator = agents_module.OrquestadorSolar()

    # Si por algún motivo grave el objeto sigue siendo None, detenemos la consola con un aviso claro
    if solar_orchestrator is None:
        print("❌ Error Crítico: No se pudo encontrar la clase OrquestadorSolar ni la variable solar_orchestrator en src/agents.py")
        sys.exit(1)
    
    # Identificador único de sesión para hilos de chat independientes (consola local por defecto)
    session_id = "consola_default"

    while True:
        try:
            # Leemos lo que escribe el cliente en la terminal removiendo espacios en blanco accidentales
            raw_input = input("👤 Cliente: ").strip()
            
            if not raw_input:
                continue

            # Comando especial de auditoría de memoria compartida
            if raw_input.lower() == "estado":
                print("\n" + "📊" * 15)
                print("🛠️  [AUDITORÍA DE ESTADO COMPARTIDO]")
                print(f"Datos actuales: {state.datos_cliente}")
                print("📊" * 15 + "\n")
                continue

            # Regla de salida
            if any(word in raw_input.lower() for word in ["salir", "chau", "adios", "hasta luego", "terminar"]):
                print("🔒 Sesión finalizada correctamente por el usuario.")
                break

            # --- DETECCIÓN DE ADJUNTOS MULTIMODALES ---
            user_input = raw_input
            ruta_archivo = None
            
            # Si el usuario usa el separador '| archivo:', separamos el texto del path del documento
            if " | archivo:" in raw_input:
                partes = raw_input.split(" | archivo:")
                user_input = partes[0].strip()
                ruta_archivo = partes[1].strip()

            # Paso 1: El orquestador solar extrae datos en segundo plano y enruta dinámicamente al experto idóneo
            agente_elegido = solar_orchestrator.route_request(user_input, state.datos_cliente)

            # Control de seguridad: Si el ruteo devolvió None por error de coincidencia, asignamos el coloquial por defecto
            if agente_elegido is None:
                if hasattr(agents_module, "subagente_coloquial"):
                    agente_elegido = agents_module.subagente_coloquial
                else:
                    print("❌ Error: No se encontró ningún subagente de resguardo disponible.")
                    continue

            # Paso 2: El subagente experto responde la duda basándose en el historial unificado y el archivo si existiese
            respuesta = agente_elegido.responder(
                mensaje_usuario=user_input, 
                datos_cliente=state.datos_cliente, 
                session_id=session_id,
                ruta_archivo=ruta_archivo 
            )

            # Mostramos el veredicto en la terminal
            print(f"\n🤖 [{agente_elegido.name}]: {respuesta}\n")

        except (KeyboardInterrupt, EOFError):
            print("\n🔒 Sesión interrumpida.")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Ocurrió un error inesperado en el flujo agéntico: {e}\n")

if __name__ == "__main__":
    main()

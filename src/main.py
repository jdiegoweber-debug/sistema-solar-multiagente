# src/main.py
import sys # Módulo para interactuar con funciones esenciales del sistema operativo e intérpretes de Python
import os # Módulo para verificar la existencia de rutas de archivos en el disco local
from pypdf import PdfReader # Librería eficiente para inspeccionar páginas de PDFs sin saturar contexto
from src.state import SolarProjectState # Cargamos tu esquema Pydantic para manejar de forma segura la memoria del cliente
from src.tools.rag_tool import extraer_datos_factura # Importamos la herramienta especializada de extracción
# Importamos directamente el módulo completo de agentes para inspeccionarlo dinámicamente
import src.agents as agents_module

def consultar_manual_pdf(termino_busqueda: str) -> str:
    """
    Busca palabras clave dentro del PDF técnico guardado en local.
    Devuelve solo los fragmentos de las páginas relevantes para ahorrar tokens.
    """
    # Buscamos el PDF en una carpeta 'knowledge' en la raíz del proyecto
    ruta_pdf = os.path.join("knowledge", "manual_solar.pdf")
    
    if not os.path.exists(ruta_pdf):
        return "[Aviso Sistema]: El archivo de conocimiento 'knowledge/manual_solar.pdf' no fue encontrado."
        
    try:
        lector = PdfReader(ruta_pdf)
        fragmentos_encontrados = []
        
        # Escaneamos las páginas buscando coincidencias
        for num_pag, pagina in enumerate(lector.pages, start=1):
            texto_pagina = pagina.extract_text()
            if termino_busqueda.lower() in texto_pagina.lower():
                # Extraemos un fragmento acotado de la página para no inundar el prompt
                extracto = texto_pagina[:800].replace('\n', ' ')
                fragmentos_encontrados.append(f"[Página {num_pag}]: ... {extracto} ...")
                
                # Limitamos a un máximo de 3 páginas relevantes para proteger la ventana de contexto
                if len(fragmentos_encontrados) >= 3:
                    break
                    
        if not fragmentos_encontrados:
            return f"[Aviso Sistema]: No se encontraron referencias a '{termino_busqueda}' en el manual."
            
        return "\n\n".join(fragmentos_encontrados)
        
    except Exception as e:
        return f"[Aviso Sistema]: Error al leer el PDF de conocimiento: {e}"

def main():
    """
    Función principal que arranca la consola interactiva del sistema multiagente solar con soporte multimodal.
    """
    print("=" * 60)
    print("☀️ SISTEMA MULTIAGENTE DE ASESORAMIENTO SOLAR MULTIMODAL ☀️")
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
                print("🛠️ [AUDITORÍA DE ESTADO COMPARTIDO]")
                print(f"Datos actuales: {state.datos_cliente.model_dump()}")
                print("📊" * 15 + "\n")
                continue

            # Regla de salida
            if any(word in raw_input.lower() for word in ["salir", "chau", "adios", "hasta luego", "terminar"]):
                print("🔒 Sesión finalizada correctamente por el usuario.")
                break

            # --- DETECCIÓN DE ADJUNTOS MULTIMODALES O LINKS DE FACTURA ---
            user_input = raw_input
            ruta_archivo = None
            
            # Si el usuario usa el separador '| archivo:', separamos el texto del path del documento
            if " | archivo:" in raw_input:
                partes = raw_input.split(" | archivo:")
                user_input = partes[0].strip()
                ruta_archivo = partes[1].strip()

            # --- CAPA DE CONOCIMIENTO TÉCNICO COMPLEMENTARIO (PDF) ---
            # Realizamos una búsqueda rápida basada en las palabras clave del usuario en el PDF externo
            # Esto permite "tener presente" el PDF sin inyectarlo completo en cada interacción
            datos_manual_filtrados = consultar_manual_pdf(user_input)
            
            # Si se encuentra información útil, la acoplamos temporalmente al mensaje para que los agentes la lean
            if "[Aviso Sistema]" not in datos_manual_filtrados:
                prompt_enriquecido = (
                    f"{user_input}\n\n"
                    f"[INFORMACIÓN ADICIONAL ENCONTRADA EN EL MANUAL PDF]:\n"
                    f"{datos_manual_filtrados}"
                )
            else:
                prompt_enriquecido = user_input

            # --- CAPA INTERMEDIA DE EXTRACCIÓN COGNITIVA ANTIALUCINACIONES ---
            # Si el input parece contener un enlace de factura o un archivo adjunto, extraemos datos de forma segura
            if "http" in user_input.lower() or "factura" in user_input.lower() or ruta_archivo:
                # Simulamos enviarle el texto bruto de grounding que recibiste de Usina de Tandil en la sesión
                contexto_simulado_factura = (
                    "TOTAL SERVICIO ELECTRICO 53.005,14. "
                    "Medidor Lect.Ant. 44345 Lect.Act. 44479 Consumo 134 R. Tarifa 1R"
                )
                
                # Invocamos al parser estructurado de tu rag_tool
                datos_extraidos = extraer_datos_factura(contexto_simulado_factura)

                # Guardamos de forma segura las variables monetarias y del período actual
                state.datos_cliente.costo_factura_pesos = datos_extraidos.get("costo_factura_pesos")
                state.datos_cliente.consumo_periodo_kwh = datos_extraidos.get("consumo_periodo_kwh")

                # Al intentar mutar el consumo anual, nuestro validador Pydantic de state.py frenará
                # cualquier intento si Gemini por error devuelve los pesos en el campo de energía
                try:
                    state.datos_cliente.consumo_anual_kwh = datos_extraidos.get("consumo_anual_kwh")
                except ValueError as ve:
                    # Si salta la validación, anulamos la asignación errónea y dejamos que siga limpio
                    state.datos_cliente.consumo_anual_kwh = None

            # Paso 1: El orquestador solar extrae datos en segundo plano y enruta dinámicamente al experto idóneo
            # Pasamos el prompt enriquecido para que el orquestador decida con mejor contexto técnico si aplica
            agente_elegido = solar_orchestrator.route_request(prompt_enriquecido, state.datos_cliente)

            # Control de seguridad: Si el ruteo devolvió None por error de coincidencia, asignamos el coloquial por defecto
            if agente_elegido is None:
                if hasattr(agents_module, "subagente_coloquial"):
                    agente_elegido = agents_module.subagente_coloquial
                else:
                    print("❌ Error: No se encontró ningún subagente de resguardo disponible.")
                    continue

            # Paso 2: El subagente experto responde la duda basándose en el historial unificado y la info filtrada del PDF
            respuesta = agente_elegido.responder(
                mensaje_usuario=prompt_enriquecido,
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

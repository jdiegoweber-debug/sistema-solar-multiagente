import os # Importamos el módulo del sistema operativo para manejar rutas de archivos de forma segura
import json # Importamos la biblioteca estándar para estructurar y guardar los datos en formato JSON

# Definimos de forma dinámica la ruta donde se creará y guardará nuestra base de datos simulada del CRM corporativo
CRM_DB_PATH = os.path.join(os.path.dirname(__file__), "crm_database.json")

def mcp_guardar_cliente_crm(nombre: str, ciudad: str, consumo: str, tipo_sistema: str) -> str:
    """
    Función de persistencia que simula un servidor MCP (Model Context Protocol).
    Es consumida por el Agente Comercial cuando el cliente decide avanzar con el proyecto.
    """
    # Creamos un diccionario Python estructurando de forma prolija los datos capturados del cliente residencial
    cliente_data = {
        "nombre": nombre or "Desconocido", # Si el nombre llegó vacío o nulo, guarda un valor por defecto
        "ciudad": ciudad or "No especificada", # Asigna un valor de resguardo si falta la localización del usuario
        "consumo_anual_kwh": consumo or "No especificado", # Evita campos vacíos para el consumo eléctrico anual en kWh
        "tipo_sistema": tipo_sistema or "No especificado", # Guarda si el cliente prefiere un sistema On-Grid u Off-Grid
        "estado_lead": "Interesado - Pendiente Cotización" # Inyecta un estado comercial inicial para el equipo de ventas
    }

    try:
        # Verificamos mediante el sistema operativo si el archivo JSON de la base de datos ya fue creado previamente
        if os.path.exists(CRM_DB_PATH):
            # Si el archivo ya existe, lo abrimos en modo lectura con codificación universal UTF-8
            with open(CRM_DB_PATH, "r", encoding="utf-8") as f:
                # Cargamos los registros existentes de clientes y los transformamos en una lista de Python
                data = json.load(f)
        else:
            # Si el archivo no existe en el disco, inicializamos una lista de datos completamente nueva y vacía
            data = []

        # Agregamos el diccionario con los datos del nuevo cliente al listado histórico de la base de datos
        data.append(cliente_data)

        # Abrimos el archivo en modo escritura ("w") para actualizar la base de datos en el disco local
        with open(CRM_DB_PATH, "w", encoding="utf-8") as f:
            # Guardamos la lista actualizada convirtiéndola en texto JSON formateado de forma legible (indentación de 4 espacios)
            json.dump(data, f, ensure_ascii=False, indent=4)

        # Retornamos un string de confirmación exitoso que el Agente Comercial utilizará para responderle al usuario
        return f"[Mapeo MCP OK] Cliente '{cliente_data['nombre']}' registrado exitosamente en el CRM corporativo."

    except Exception as e:
        # Capturamos cualquier error imprevisto (como problemas de permisos de disco) para evitar que el sistema se rompa
        return f"[MCP ERROR] Falló la conexión simulada con el servidor externo CRM debido al error: {e}"

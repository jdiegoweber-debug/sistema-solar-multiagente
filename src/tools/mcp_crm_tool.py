import json
import os

# Ruta para simular la base de datos externa de tu CRM
CRM_DB_PATH = "src/tools/crm_database.json"

def mcp_guardar_cliente_crm(nombre: str, ciudad: str, consumo: str, sistema: str) -> str:
    """
    Servidor MCP (Model Context Protocol). Escribe y persiste de forma 
    estricta los datos validados del cliente dentro del CRM de la empresa.
    """
    registro = {
        "nombre": nombre,
        "ciudad": ciudad,
        "consumo_anual_kwh": consumo,
        "tipo_sistema": sistema
    }
    try:
        with open(CRM_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(registro, f, indent=4, ensure_ascii=False)
        return f"[Servidor MCP]: Datos de {nombre} guardados en el CRM correctamente."
    except Exception as e:
        return f"[Servidor MCP] Error: {str(e)}"

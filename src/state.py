from typing import Dict, Any

class SolarProjectState:
    def __init__(self):
        # Datos iniciales recopilados por el Agente Coloquial
        self.datos_cliente: Dict[str, Any] = {
            "nombre": None,
            "ciudad": None,
            "consumo_anual_kwh": None,  # Preferentemente anual (en kWh o pesos en su defecto)
            "tipo_sistema": None        # 'Aislado de la red' o 'Conectado a la red' (Bajar consumo o Medidor bidireccional)
        }     
        
        # Datos procesados por el Agente Técnico (Paneles, inversor, espacio)
        self.calculo_tecnico: Dict[str, Any] = {}   
        
        # Datos procesados por el Agente Comercial (Precios, ROI, Vida útil baterías)
        self.cotizacion_final: Dict[str, Any] = {}  

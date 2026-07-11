from pydantic import BaseModel, Field

class SolarProjectState(BaseModel):
    # Definimos el esquema del diccionario para que Pydantic lo reconozca de forma nativa
    datos_cliente: dict = Field(default_factory=lambda: {
        "nombre": None,
        "ciudad": None,
        "consumo_anual_kwh": None,
        "tipo_sistema": None  # 'Aislado de la red' o 'Conectado a la red'
    })

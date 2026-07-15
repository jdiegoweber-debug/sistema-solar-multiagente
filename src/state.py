from pydantic import BaseModel, Field, field_validator
from typing import Optional

class DatosClienteSchema(BaseModel):
    """Esquema interno para el tipado estricto de las variables del cliente."""
    nombre: Optional[str] = Field(None, description="Nombre completo del cliente.")
    ciudad: Optional[str] = Field(None, description="Ciudad o región (Ej: Tandil).")
    
    # Añadimos estos dos campos para que el RAG y los agentes separen dinero de energía
    consumo_periodo_kwh: Optional[float] = Field(None, description="Consumo en kWh del período actual facturado.")
    costo_factura_pesos: Optional[float] = Field(None, description="Monto total en pesos ($) a pagar en la factura.")
    
    # Campo original que requiere tu arquitectura
    consumo_anual_kwh: Optional[float] = Field(None, description="Consumo total estimado o real anualizado en kWh.")
    tipo_sistema: Optional[str] = Field(None, description="'Aislado de la red' (off-grid) o 'Conectado a la red' (on-grid).")

    @field_validator('consumo_anual_kwh')
    @classmethod
    def validar_integridad_unidades(cls, v: Optional[float], info) -> Optional[float]:
        """Validación de negocio: Frena la asignación si los kWh anuales coinciden con el costo en pesos."""
        valores = info.data
        costo_pesos = valores.get('costo_factura_pesos')
        
        if v is not None and costo_pesos is not None:
            # Si el valor de kWh anuales es idéntico al costo en pesos, lanzamos error cognitivo
            if abs(v - costo_pesos) < 1.0:
                raise ValueError(
                    f"Error de Asignación Cognitiva: Se intentó asignar el valor de la moneda (${costo_pesos}) "
                    f"al campo de energía 'consumo_anual_kwh'. Asignación rechazada."
                )
        return v

class SolarProjectState(BaseModel):
    """Manejo seguro de la memoria del cliente para el sistema multiagente."""
    # Mantenemos la estructura nativa 'datos_cliente' para no romper tus otros archivos
    datos_cliente: DatosClienteSchema = Field(default_factory=DatosClienteSchema)

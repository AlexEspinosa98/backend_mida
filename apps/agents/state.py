from typing import Literal, NotRequired, Optional, TypedDict


class PacienteInput(TypedDict):
    sexo: Literal["M", "F"]
    edad_meses: float


class MedicionesInput(TypedDict):
    peso_kg: float
    talla_cm: float
    tipo_medicion_talla: Literal["acostado", "de_pie"]
    perimetro_cefalico_cm: NotRequired[Optional[float]]
    perimetro_braquial_cm: NotRequired[Optional[float]]
    edema_bilateral: bool


class IndicadorResultado(TypedDict):
    indicador: str
    valor_z: Optional[float]
    clasificacion: str
    nivel_alerta: Literal["normal", "moderado", "severo", "critico", "no_aplica"]
    es_bypass: bool
    detalle: dict


class MidaState(TypedDict):
    paciente: PacienteInput
    mediciones: MedicionesInput

    validation_errors: NotRequired[list[str]]

    resultado_talla_edad: NotRequired[IndicadorResultado]
    resultado_peso_talla: NotRequired[IndicadorResultado]
    resultado_peso_edad: NotRequired[IndicadorResultado]
    resultado_imc_edad: NotRequired[IndicadorResultado]
    resultado_pc_edad: NotRequired[IndicadorResultado]
    resultado_pb_edad: NotRequired[IndicadorResultado]

    hallazgos: NotRequired[dict]
    resumen_clinico: NotRequired[str]

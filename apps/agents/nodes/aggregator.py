"""Nodo de unión determinístico: espera a que los 6 indicadores hayan sido
calculados y consolida la alerta crítica global + las sugerencias clínicas
de proceso. No usa LLM -- todo lo que produce es texto/reglas fijas."""

from ..clinical_actions import (
    requiere_manejo_nutricional_terapeutico,
    sugerencias_clinicas,
    sugerencias_familiares,
)
from ..state import MidaState

_CLAVES_RESULTADOS = [
    "resultado_talla_edad",
    "resultado_peso_talla",
    "resultado_peso_edad",
    "resultado_imc_edad",
    "resultado_pc_edad",
    "resultado_pb_edad",
]


def nodo_agregador_hallazgos(state: MidaState) -> dict:
    resultados = [state[clave] for clave in _CLAVES_RESULTADOS if clave in state]

    alerta_critica = state["mediciones"]["edema_bilateral"] or any(
        r["nivel_alerta"] == "critico" for r in resultados
    )

    hallazgos = {
        "resultados": resultados,
        "alerta_critica": alerta_critica,
        "edema_bilateral": state["mediciones"]["edema_bilateral"],
    }
    hallazgos["sugerencias"] = sugerencias_clinicas(hallazgos)
    hallazgos["sugerencias_familiares"] = sugerencias_familiares(hallazgos)
    hallazgos["requiere_manejo_nutricional_terapeutico"] = requiere_manejo_nutricional_terapeutico(
        hallazgos
    )
    return {"hallazgos": hallazgos}

"""Nodo de unión determinístico: espera a que los 6 indicadores hayan sido
calculados y consolida la alerta crítica global. No usa LLM."""

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
    }
    return {"hallazgos": hallazgos}

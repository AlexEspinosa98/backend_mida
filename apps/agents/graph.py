from langgraph.graph import END, StateGraph

from .nodes.aggregator import nodo_agregador_hallazgos
from .nodes.indicator_nodes import (
    nodo_imc_edad,
    nodo_pb_edad,
    nodo_pc_edad,
    nodo_peso_edad,
    nodo_peso_talla,
    nodo_talla_edad,
)
from .nodes.nutrition import nodo_plan_nutricional
from .nodes.synthesis import nodo_sintesis_clinica
from .nodes.synthesis_familiar import nodo_sintesis_familiar
from .nodes.validator import hay_errores_de_validacion, validar_entrada
from .state import MidaState

_NODOS_INDICADOR = [
    "talla_edad",
    "peso_talla",
    "peso_edad",
    "imc_edad",
    "pc_edad",
    "pb_edad",
]


def _nodo_error(state: MidaState) -> dict:
    return {
        "hallazgos": {"resultados": [], "alerta_critica": False},
        "resumen_clinico": "",
        "resumen_familiar": "",
        "plan_nutricional": {"aplica": False, "motivo_no_aplica": None, "dias": [], "grupos_sin_opciones": []},
        "tips_nutricionales": "",
    }


def _enrutar_tras_validacion(state: MidaState):
    """Función de la arista condicional única desde validar_entrada: si hay
    errores de validación, enruta al nodo de error; si no, hace fan-out a
    las 6 ramas indicador EN PARALELO (mismo superstep) devolviendo la
    lista de sus nombres -- LangGraph fan-out real, no 6 aristas
    condicionales separadas (que se pisarían entre sí al compartir la misma
    fuente)."""
    if hay_errores_de_validacion(state) == "error":
        return "error"
    return list(_NODOS_INDICADOR)


def build_graph():
    g = StateGraph(MidaState)

    g.add_node("validar_entrada", validar_entrada)
    g.add_node("talla_edad", nodo_talla_edad)
    g.add_node("peso_talla", nodo_peso_talla)
    g.add_node("peso_edad", nodo_peso_edad)
    g.add_node("imc_edad", nodo_imc_edad)
    g.add_node("pc_edad", nodo_pc_edad)
    g.add_node("pb_edad", nodo_pb_edad)
    g.add_node("agregador_hallazgos", nodo_agregador_hallazgos)
    g.add_node("sintesis_clinica", nodo_sintesis_clinica)
    g.add_node("sintesis_familiar", nodo_sintesis_familiar)
    g.add_node("plan_nutricional", nodo_plan_nutricional)
    g.add_node("error", _nodo_error)

    g.set_entry_point("validar_entrada")
    g.add_conditional_edges(
        "validar_entrada",
        _enrutar_tras_validacion,
        [*_NODOS_INDICADOR, "error"],
    )

    for nombre in _NODOS_INDICADOR:
        g.add_edge(nombre, "agregador_hallazgos")

    # Los tres nodos siguientes corren en paralelo desde el mismo agregador
    # -- cada uno escribe su propia clave de estado (resumen_clinico /
    # resumen_familiar / plan_nutricional+tips_nutricionales) y termina de
    # forma independiente; el estado final del grafo trae las tres (ver
    # test de fan-out a N nodos terminales antes de construir esto).
    g.add_edge("agregador_hallazgos", "sintesis_clinica")
    g.add_edge("agregador_hallazgos", "sintesis_familiar")
    g.add_edge("agregador_hallazgos", "plan_nutricional")
    g.add_edge("sintesis_clinica", END)
    g.add_edge("sintesis_familiar", END)
    g.add_edge("plan_nutricional", END)
    g.add_edge("error", END)

    return g.compile()

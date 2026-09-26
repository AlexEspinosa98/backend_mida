"""Único nodo del grafo que usa un LLM. Recibe los hallazgos YA calculados
y clasificados de forma determinística y solo redacta la interpretación
clínica en lenguaje natural — no calcula ni corrige ningún número."""

from ..llm import generar_texto
from ..prompts import construir_prompt_sintesis, prompt_sistema_sintesis
from ..state import MidaState


def nodo_sintesis_clinica(state: MidaState) -> dict:
    prompt_usuario = construir_prompt_sintesis(
        hallazgos=state["hallazgos"],
        paciente=state["paciente"],
        mediciones=state["mediciones"],
    )
    resumen = generar_texto(prompt_sistema_sintesis(), prompt_usuario)
    return {"resumen_clinico": resumen}

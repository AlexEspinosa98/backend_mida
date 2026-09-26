"""Segundo nodo con LLM (en paralelo al de síntesis clínica): redacta la
explicación en lenguaje sencillo para la familia/cuidador, a partir de los
mismos hallazgos YA calculados y clasificados de forma determinística."""

from ..llm import generar_texto
from ..prompts import construir_prompt_sintesis_familiar, prompt_sistema_sintesis_familiar
from ..state import MidaState


def nodo_sintesis_familiar(state: MidaState) -> dict:
    prompt_usuario = construir_prompt_sintesis_familiar(
        hallazgos=state["hallazgos"],
        paciente=state["paciente"],
        mediciones=state["mediciones"],
    )
    resumen = generar_texto(prompt_sistema_sintesis_familiar(), prompt_usuario)
    return {"resumen_familiar": resumen}

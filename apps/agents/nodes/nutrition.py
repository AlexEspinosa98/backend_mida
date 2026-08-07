"""Nodo de plan nutricional. La SELECCIÓN de alimentos es 100%
determinística (apps.nutrition.plan, sobre el catálogo editable en
/admin/) -- el LLM solo redacta una introducción y consejos generales,
sin nombrar alimentos específicos (ver apps/agents/prompts.py). La nota
de precaución para casos que requieren manejo nutricional terapéutico es
texto FIJO, no generado por IA -- es la parte más sensible de este nodo y
no debe depender de que el LLM la redacte correctamente."""

from ..llm import generar_texto
from ..prompts import PROMPT_SISTEMA_TIPS_NUTRICION, construir_prompt_tips_nutricion
from ..state import MidaState

NOTA_PRECAUCION_NUTRICIONAL = (
    "AVISO: los hallazgos de este tamizaje sugieren que este niño o niña puede necesitar "
    "manejo nutricional terapéutico supervisado directamente por un profesional de salud "
    "o nutrición -- no solo una guía general de alimentación. El plan de variedad de "
    "alimentos que sigue es una base general; no debe aplicarse tal cual sin que el "
    "profesional tratante lo revise y ajuste primero."
)


def nodo_plan_nutricional(state: MidaState) -> dict:
    from apps.nutrition.plan import generar_plan_semanal, resumen_disponibilidad

    edad_meses = state["paciente"]["edad_meses"]
    plan = generar_plan_semanal(edad_meses)

    if not plan["aplica"]:
        return {"plan_nutricional": plan, "tips_nutricionales": plan["motivo_no_aplica"]}

    conteos = {grupo: len(items) for grupo, items in resumen_disponibilidad(edad_meses).items()}
    prompt_usuario = construir_prompt_tips_nutricion(edad_meses, conteos)
    tips = generar_texto(PROMPT_SISTEMA_TIPS_NUTRICION, prompt_usuario)

    if state.get("hallazgos", {}).get("requiere_manejo_nutricional_terapeutico"):
        tips = f"{NOTA_PRECAUCION_NUTRICIONAL}\n\n{tips}"

    return {"plan_nutricional": plan, "tips_nutricionales": tips}

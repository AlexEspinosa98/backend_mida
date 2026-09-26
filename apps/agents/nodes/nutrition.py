"""Nodo de plan nutricional. La SELECCIÓN de alimentos es 100%
determinística (apps.nutrition.plan, sobre el catálogo editable en
/admin/), incluyendo qué alimentos entran según la etnia del paciente
(catálogo general + alimentos propios de su comunidad, ver
Alimento.region_especifica) y el cálculo de calorías/macronutrientes por
porción -- el LLM solo redacta una introducción y consejos generales,
sin nombrar alimentos específicos, salvo una única frase opcional de
cierre que puede destacar 1-2 alimentos de cereales/tubérculos
disponibles (accesibles/económicos en la comunidad), tomados
textualmente de la lista que ya decidió apps.nutrition.plan -- el LLM
nunca elige ni inventa cuáles (ver apps/agents/prompts.py). La nota de
precaución para casos que requieren manejo nutricional terapéutico es
texto FIJO, no generado por IA -- es la parte más sensible de este nodo y
no debe depender de que el LLM la redacte correctamente."""

from ..llm import generar_texto
from ..prompts import construir_prompt_tips_nutricion, prompt_sistema_tips_nutricion
from ..state import MidaState

# Cuántos alimentos de cereales/tubérculos se destacan en la frase opcional de cierre de los
# tips -- elegidos aquí (los primeros del catálogo, orden alfabético vía
# resumen_disponibilidad), NUNCA por el LLM, para no repetirle la tarea de selección que ya le
# generó errores reales en el pasado (ver README.md).
MAX_ALIMENTOS_DESTACADOS = 2

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
    etnia = state["paciente"].get("etnia")
    plan = generar_plan_semanal(edad_meses, etnia)

    if not plan["aplica"]:
        return {"plan_nutricional": plan, "tips_nutricionales": plan["motivo_no_aplica"]}

    disponibles = resumen_disponibilidad(edad_meses, etnia)
    conteos = {grupo: len(items) for grupo, items in disponibles.items()}
    destacados_cereal = disponibles.get("cereal", [])[:MAX_ALIMENTOS_DESTACADOS]
    prompt_usuario = construir_prompt_tips_nutricion(
        edad_meses, conteos, alimentos_cereal_disponibles=destacados_cereal
    )
    tips = generar_texto(prompt_sistema_tips_nutricion(), prompt_usuario)

    if state.get("hallazgos", {}).get("requiere_manejo_nutricional_terapeutico"):
        tips = f"{NOTA_PRECAUCION_NUTRICIONAL}\n\n{tips}"

    return {"plan_nutricional": plan, "tips_nutricionales": tips}

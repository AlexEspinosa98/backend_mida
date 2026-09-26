"""Los 6 nodos indicador del grafo. Cada uno es una función PURA y
DETERMINÍSTICA: llama a apps.who_standards.indicators (matemática LMS
oficial de la OMS + clasificación clínica ya fusionada en el dict de
retorno). Ningún LLM participa en este cálculo ni en esta clasificación.

Los imports de who_standards son locales a cada función (no a nivel de
módulo) para que este paquete siga siendo importable de forma aislada
incluso si who_standards no está disponible en un entorno dado; en tiempo
de ejecución real siempre lo está."""

from ..state import IndicadorResultado, MidaState

# Traduce el vocabulario de who_standards.classify ('normal'|'alerta'|
# 'severo'|'informativo') al vocabulario de nivel_alerta persistido en
# ResultadoIndicador ('normal'|'moderado'|'severo'|'critico'|'no_aplica').
_MAPA_NIVEL_ALERTA = {
    "normal": "normal",
    "informativo": "normal",
    "alerta": "moderado",
    "severo": "severo",
}

# Clasificaciones que, aunque técnicamente "severo", representan una
# emergencia médica inmediata (desnutrición aguda severa) y por tanto deben
# escalar a "critico" para disparar la alerta_critica global del agregador.
_CLASIFICACIONES_CRITICAS = {
    "Emaciacion Severa",
    "Emaciacion Severa (con edema)",
}


def _normalizar_comunitario(comunitario: dict) -> dict:
    """El dict `comunitario` se clasifica con who_standards.classify, que usa
    el mismo vocabulario crudo que el cálculo OMS ('normal'|'alerta'|'severo'|
    'informativo'). Hay que traducirlo con el mismo _MAPA_NIVEL_ALERTA para
    que sus badges (report_pdf.html, badge-{{ nivel_alerta }}) y el color del
    punto en la gráfica comunitaria (reports/charts.py) coincidan con el
    vocabulario real usado en el CSS y en _SEMAFORO -- sin este mapeo,
    'alerta'/'informativo' no calzan con ninguna clase definida y el hallazgo
    comunitario se muestra sin color de alerta."""
    comunitario["nivel_alerta"] = _MAPA_NIVEL_ALERTA.get(
        comunitario["nivel_alerta"], comunitario["nivel_alerta"]
    )
    return comunitario


def _a_resultado(indicador: str, calculo: dict) -> IndicadorResultado:
    if not calculo.get("aplica", True):
        return {
            "indicador": indicador,
            "valor_z": None,
            "clasificacion": "No aplica",
            "nivel_alerta": "no_aplica",
            "es_bypass": False,
            "detalle": {"motivo": calculo.get("motivo_no_aplica", "")},
        }

    nivel_alerta_bruto = calculo.get("nivel_alerta", "normal")
    es_bypass = bool(calculo.get("es_bypass", False))
    clasificacion = calculo.get("clasificacion", "")

    nivel = _MAPA_NIVEL_ALERTA.get(nivel_alerta_bruto, nivel_alerta_bruto)
    if es_bypass and clasificacion == "Critico":
        nivel = "critico"
    if clasificacion in _CLASIFICACIONES_CRITICAS:
        nivel = "critico"

    detalle = {
        k: v
        for k, v in calculo.items()
        if k not in {"valor_z", "clasificacion", "nivel_alerta", "aplica", "es_bypass"}
    }

    return {
        "indicador": indicador,
        "valor_z": calculo.get("valor_z"),
        "clasificacion": clasificacion,
        "nivel_alerta": nivel,
        "es_bypass": es_bypass,
        "detalle": detalle,
    }


def nodo_talla_edad(state: MidaState) -> dict:
    from apps.who_standards import classify, indicators, local_patterns

    calculo = indicators.talla_para_edad(
        sexo=state["paciente"]["sexo"],
        edad_meses=state["paciente"]["edad_meses"],
        talla_cm=state["mediciones"]["talla_cm"],
    )
    if calculo.get("aplica", True):
        comunitario = local_patterns.talla_para_edad_comunitaria(
            etnia=state["paciente"].get("etnia"),
            sexo=state["paciente"]["sexo"],
            edad_meses=state["paciente"]["edad_meses"],
            talla_cm=state["mediciones"]["talla_cm"],
            mediana_oms_cm=calculo["mediana_oms"],
        )
        if comunitario is not None:
            comunitario.update(classify.clasificar_talla_para_edad(comunitario["valor_z"]))
            calculo["comunitario"] = _normalizar_comunitario(comunitario)
    return {"resultado_talla_edad": _a_resultado("TE", calculo)}


def nodo_peso_talla(state: MidaState) -> dict:
    from apps.who_standards import classify, indicators, local_patterns

    calculo = indicators.peso_para_talla(
        sexo=state["paciente"]["sexo"],
        edad_meses=state["paciente"]["edad_meses"],
        peso_kg=state["mediciones"]["peso_kg"],
        talla_cm=state["mediciones"]["talla_cm"],
        tipo_medicion=state["mediciones"]["tipo_medicion_talla"],
    )

    if calculo.get("aplica", True):
        comunitario = local_patterns.peso_para_talla_comunitario(
            etnia=state["paciente"].get("etnia"),
            peso_kg=state["mediciones"]["peso_kg"],
            mediana_oms_kg=calculo["mediana_oms"],
        )
        if comunitario is not None:
            comunitario.update(classify.clasificar_peso_para_talla(comunitario["valor_z"]))
            calculo["comunitario"] = _normalizar_comunitario(comunitario)

    if calculo.get("aplica", True) and state["mediciones"]["edema_bilateral"]:
        calculo = classify.aplicar_override_edema(calculo)

    resultado = _a_resultado("PT", calculo)
    if state["mediciones"]["edema_bilateral"] and calculo.get("aplica", True):
        resultado["nivel_alerta"] = "critico"
    return {"resultado_peso_talla": resultado}


def nodo_peso_edad(state: MidaState) -> dict:
    from apps.who_standards import classify, indicators, local_patterns

    calculo = indicators.peso_para_edad(
        sexo=state["paciente"]["sexo"],
        edad_meses=state["paciente"]["edad_meses"],
        peso_kg=state["mediciones"]["peso_kg"],
    )
    if calculo.get("aplica", True):
        comunitario = local_patterns.peso_para_edad_comunitario(
            etnia=state["paciente"].get("etnia"),
            sexo=state["paciente"]["sexo"],
            edad_meses=state["paciente"]["edad_meses"],
            peso_kg=state["mediciones"]["peso_kg"],
            mediana_oms_kg=calculo["mediana_oms"],
        )
        if comunitario is not None:
            comunitario.update(classify.clasificar_peso_para_edad(comunitario["valor_z"]))
            calculo["comunitario"] = _normalizar_comunitario(comunitario)
    return {"resultado_peso_edad": _a_resultado("PE", calculo)}


def nodo_imc_edad(state: MidaState) -> dict:
    from apps.who_standards import classify, indicators, local_patterns

    calculo = indicators.imc_para_edad(
        sexo=state["paciente"]["sexo"],
        edad_meses=state["paciente"]["edad_meses"],
        peso_kg=state["mediciones"]["peso_kg"],
        talla_cm=state["mediciones"]["talla_cm"],
    )
    if calculo.get("aplica", True):
        comunitario = local_patterns.imc_para_edad_comunitario(
            etnia=state["paciente"].get("etnia"),
            imc=calculo["imc"],
            mediana_oms=calculo["mediana_oms"],
        )
        if comunitario is not None:
            comunitario.update(classify.clasificar_imc_para_edad(comunitario["valor_z"]))
            calculo["comunitario"] = _normalizar_comunitario(comunitario)
    return {"resultado_imc_edad": _a_resultado("IMCE", calculo)}


def nodo_pc_edad(state: MidaState) -> dict:
    from apps.who_standards import indicators

    pc_cm = state["mediciones"].get("perimetro_cefalico_cm")
    if pc_cm is None:
        return {
            "resultado_pc_edad": _a_resultado(
                "PCE", {"aplica": False, "motivo_no_aplica": "No se proporcionó perímetro cefálico."}
            )
        }

    calculo = indicators.perimetro_cefalico_para_edad(
        sexo=state["paciente"]["sexo"],
        edad_meses=state["paciente"]["edad_meses"],
        pc_cm=pc_cm,
    )
    return {"resultado_pc_edad": _a_resultado("PCE", calculo)}


def nodo_pb_edad(state: MidaState) -> dict:
    from apps.who_standards import indicators

    pb_cm = state["mediciones"].get("perimetro_braquial_cm")
    if pb_cm is None:
        return {
            "resultado_pb_edad": _a_resultado(
                "PBE", {"aplica": False, "motivo_no_aplica": "No se proporcionó perímetro braquial."}
            )
        }

    calculo = indicators.perimetro_braquial_para_edad(
        sexo=state["paciente"]["sexo"],
        edad_meses=state["paciente"]["edad_meses"],
        pb_cm=pb_cm,
    )
    return {"resultado_pb_edad": _a_resultado("PBE", calculo)}

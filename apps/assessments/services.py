"""Puente entre las vistas DRF y el grafo LangGraph. Mantiene las vistas
delgadas y el grafo testeable de forma aislada (sin request/response)."""

from datetime import date, timedelta

from django.db import transaction

from apps.agents.graph import build_graph
from apps.patients.models import Paciente

from .models import (
    ActividadFisica,
    CalidadMedicion,
    ContextoFamiliarTerritorial,
    Evaluacion,
    HabitosAlimentarios,
    ReporteGenerado,
    ResultadoIndicador,
    SignosClinicos,
)

_grafo_compilado = None

_SIGNOS_QUE_ESCALAN_ALERTA = ("deshidratacion", "dificultad_respiratoria")
_NIVELES_QUE_ESCALAN_ALERTA = {"severo", "critico"}


def _get_grafo():
    global _grafo_compilado
    if _grafo_compilado is None:
        _grafo_compilado = build_graph()
    return _grafo_compilado


def _generar_codigo_caso() -> str:
    """MIDA-<año>-<consecutivo de 6 dígitos> (HU-1). No hay alta concurrencia
    esperada en este sistema, así que un conteo simple dentro de la misma
    transacción de creación es suficiente -- una colisión real requeriría dos
    inserciones simultáneas exactas, y el UniqueConstraint de todas formas
    protegería la integridad si llegara a pasar."""

    anio = date.today().year
    consecutivo = Evaluacion.objects.filter(codigo_caso__startswith=f"MIDA-{anio}-").count() + 1
    return f"MIDA-{anio}-{consecutivo:06d}"


def _resolver_paciente(datos_paciente: dict | None, sexo: str, edad_meses, fecha_evaluacion) -> Paciente:
    datos_paciente = datos_paciente or {}

    if datos_paciente.get("id"):
        return Paciente.objects.get(id=datos_paciente["id"])

    documento = datos_paciente.get("documento_identidad")
    if documento:
        existente = Paciente.objects.filter(documento_identidad=documento).first()
        if existente:
            return existente

    fecha_nacimiento = datos_paciente.get("fecha_nacimiento")
    if not fecha_nacimiento:
        # Estimación aproximada a partir de la edad en meses declarada, cuando
        # no se conoce la fecha de nacimiento exacta del paciente.
        dias_aprox = round(float(edad_meses) * 30.4375)
        fecha_nacimiento = fecha_evaluacion - timedelta(days=dias_aprox)

    return Paciente.objects.create(
        nombres=datos_paciente.get("nombres") or "Paciente",
        apellidos=datos_paciente.get("apellidos") or "Sin identificar",
        documento_identidad=documento,
        fecha_nacimiento=fecha_nacimiento,
        sexo=sexo,
        etnia=datos_paciente.get("etnia") or Paciente.Etnia.NINGUNA,
        comunidad_asentamiento=datos_paciente.get("comunidad_asentamiento") or "",
        municipio=datos_paciente.get("municipio") or "",
        departamento=datos_paciente.get("departamento") or "",
        cuidador_principal=datos_paciente.get("cuidador_principal") or "",
        lengua_principal=datos_paciente.get("lengua_principal") or "",
        requiere_mediacion_cultural=datos_paciente.get("requiere_mediacion_cultural", False),
    )


def _nota_calidad_medicion(calidad: dict | None) -> str:
    """HU-4 -- regla clínica, no del LLM: si la balanza no estaba calibrada o la
    medición no se repitió, se lo advierte explícitamente a quien lea el reporte
    técnico, sin depender de que el LLM lo "note" en la prosa."""

    if not calidad:
        return ""
    avisos = []
    if calidad.get("balanza_calibrada") not in (None, "si"):
        avisos.append("la balanza no estaba calibrada (o no se reportó)")
    if calidad.get("medicion_repetida") not in (None, "si"):
        avisos.append("la medición no se repitió (o no se reportó)")
    if not avisos:
        return ""
    return (
        "\n\nNota de calidad de la medición: " + " y ".join(avisos)
        + " -- interpretar las cifras antropométricas con esta salvedad."
    )


def _requiere_escalar_alerta(signos: dict | None, resultados: list[dict]) -> bool:
    """HU-5 -- regla clínica, no del LLM: deshidratación o dificultad respiratoria
    junto con un indicador ya severo/crítico fuerza alerta_critica=True."""

    if not signos:
        return False
    if not any(signos.get(s) for s in _SIGNOS_QUE_ESCALAN_ALERTA):
        return False
    return any(r["nivel_alerta"] in _NIVELES_QUE_ESCALAN_ALERTA for r in resultados)


@transaction.atomic
def ejecutar_evaluacion(datos: dict, creado_por=None) -> Evaluacion:
    fecha_evaluacion = datos.get("fecha_evaluacion") or date.today()
    sexo = datos["sexo"]
    edad_meses = datos["edad_meses"]

    paciente = _resolver_paciente(datos.get("paciente"), sexo, edad_meses, fecha_evaluacion)

    edad_dias = (fecha_evaluacion - paciente.fecha_nacimiento).days

    evaluacion = Evaluacion.objects.create(
        paciente=paciente,
        creado_por=creado_por,
        codigo_caso=datos.get("codigo_caso") or _generar_codigo_caso(),
        notas_administrativas=datos.get("notas_administrativas") or "",
        fecha_evaluacion=fecha_evaluacion,
        edad_dias=max(edad_dias, 0),
        edad_meses_decimal=edad_meses,
        peso_kg=datos["peso_kg"],
        talla_cm=datos["talla_cm"],
        tipo_medicion_talla=datos["tipo_medicion_talla"],
        perimetro_cefalico_cm=datos.get("perimetro_cefalico_cm"),
        perimetro_braquial_cm=datos.get("perimetro_braquial_cm"),
        perimetro_cintura_cm=datos.get("perimetro_cintura_cm"),
        perimetro_cadera_cm=datos.get("perimetro_cadera_cm"),
        edema_bilateral=datos.get("edema_bilateral", False),
        estado=Evaluacion.Estado.PROCESANDO,
    )

    calidad_medicion = datos.get("calidad_medicion")
    if calidad_medicion:
        CalidadMedicion.objects.create(evaluacion=evaluacion, **calidad_medicion)

    signos_clinicos = datos.get("signos_clinicos")
    if signos_clinicos:
        SignosClinicos.objects.create(evaluacion=evaluacion, **signos_clinicos)

    habitos_alimentarios = datos.get("habitos_alimentarios")
    if habitos_alimentarios:
        HabitosAlimentarios.objects.create(evaluacion=evaluacion, **habitos_alimentarios)

    actividad_fisica = datos.get("actividad_fisica")
    if actividad_fisica:
        ActividadFisica.objects.create(evaluacion=evaluacion, **actividad_fisica)

    contexto_familiar = datos.get("contexto_familiar")
    if contexto_familiar:
        ContextoFamiliarTerritorial.objects.create(evaluacion=evaluacion, **contexto_familiar)

    estado_inicial = {
        "paciente": {"sexo": sexo, "edad_meses": float(edad_meses), "etnia": paciente.etnia},
        "mediciones": {
            "peso_kg": float(datos["peso_kg"]),
            "talla_cm": float(datos["talla_cm"]),
            "tipo_medicion_talla": datos["tipo_medicion_talla"],
            "perimetro_cefalico_cm": (
                float(datos["perimetro_cefalico_cm"])
                if datos.get("perimetro_cefalico_cm") is not None
                else None
            ),
            "perimetro_braquial_cm": (
                float(datos["perimetro_braquial_cm"])
                if datos.get("perimetro_braquial_cm") is not None
                else None
            ),
            "edema_bilateral": datos.get("edema_bilateral", False),
        },
    }

    try:
        resultado_final = _get_grafo().invoke(estado_inicial)
    except Exception as exc:  # noqa: BLE001 - se persiste el error para diagnóstico
        evaluacion.estado = Evaluacion.Estado.ERROR
        evaluacion.error_detalle = str(exc)
        evaluacion.save(update_fields=["estado", "error_detalle"])
        raise

    if resultado_final.get("validation_errors"):
        evaluacion.estado = Evaluacion.Estado.ERROR
        evaluacion.error_detalle = "; ".join(resultado_final["validation_errors"])
        evaluacion.save(update_fields=["estado", "error_detalle"])
        return evaluacion

    hallazgos = resultado_final["hallazgos"]
    for resultado in hallazgos["resultados"]:
        ResultadoIndicador.objects.create(
            evaluacion=evaluacion,
            indicador=resultado["indicador"],
            valor_z=resultado["valor_z"],
            clasificacion=resultado["clasificacion"],
            nivel_alerta=resultado["nivel_alerta"],
            es_bypass=resultado.get("es_bypass", False),
            detalle=resultado.get("detalle", {}),
        )

    ReporteGenerado.objects.create(
        evaluacion=evaluacion,
        resumen_clinico=(
            resultado_final.get("resumen_clinico", "") + _nota_calidad_medicion(calidad_medicion)
        ),
        resumen_familiar=resultado_final.get("resumen_familiar", ""),
        plan_nutricional=resultado_final.get("plan_nutricional", {}),
        tips_nutricionales=resultado_final.get("tips_nutricionales", ""),
        fecha_reporte=datos.get("fecha_reporte") or fecha_evaluacion,
        objetivo_reporte=datos.get("objetivo_reporte") or "",
    )

    evaluacion.estado = Evaluacion.Estado.COMPLETADA
    evaluacion.alerta_critica = hallazgos["alerta_critica"] or _requiere_escalar_alerta(
        signos_clinicos, hallazgos["resultados"]
    )
    evaluacion.save(update_fields=["estado", "alerta_critica"])

    return evaluacion

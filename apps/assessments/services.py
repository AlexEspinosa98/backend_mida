"""Puente entre las vistas DRF y el grafo LangGraph. Mantiene las vistas
delgadas y el grafo testeable de forma aislada (sin request/response)."""

from datetime import date, timedelta

from django.db import transaction

from apps.agents.graph import build_graph
from apps.patients.models import Paciente

from .models import Evaluacion, ReporteGenerado, ResultadoIndicador

_grafo_compilado = None


def _get_grafo():
    global _grafo_compilado
    if _grafo_compilado is None:
        _grafo_compilado = build_graph()
    return _grafo_compilado


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
    )


@transaction.atomic
def ejecutar_evaluacion(datos: dict) -> Evaluacion:
    fecha_evaluacion = datos.get("fecha_evaluacion") or date.today()
    sexo = datos["sexo"]
    edad_meses = datos["edad_meses"]

    paciente = _resolver_paciente(datos.get("paciente"), sexo, edad_meses, fecha_evaluacion)

    edad_dias = (fecha_evaluacion - paciente.fecha_nacimiento).days

    evaluacion = Evaluacion.objects.create(
        paciente=paciente,
        fecha_evaluacion=fecha_evaluacion,
        edad_dias=max(edad_dias, 0),
        edad_meses_decimal=edad_meses,
        peso_kg=datos["peso_kg"],
        talla_cm=datos["talla_cm"],
        tipo_medicion_talla=datos["tipo_medicion_talla"],
        perimetro_cefalico_cm=datos.get("perimetro_cefalico_cm"),
        perimetro_braquial_cm=datos.get("perimetro_braquial_cm"),
        edema_bilateral=datos.get("edema_bilateral", False),
        estado=Evaluacion.Estado.PROCESANDO,
    )

    estado_inicial = {
        "paciente": {"sexo": sexo, "edad_meses": float(edad_meses)},
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
        resumen_clinico=resultado_final.get("resumen_clinico", ""),
    )

    evaluacion.estado = Evaluacion.Estado.COMPLETADA
    evaluacion.alerta_critica = hallazgos["alerta_critica"]
    evaluacion.save(update_fields=["estado", "alerta_critica"])

    return evaluacion

"""Validación de plausibilidad clínica de las mediciones de entrada.

Esta capa es un chequeo adicional de sentido común (detectar errores de
digitación groseros, p.ej. peso en gramos en vez de kg) — los rangos
"duros" de cada campo ya se validan en el serializer de DRF antes de
llegar aquí."""

from ..state import MidaState


def validar_entrada(state: MidaState) -> dict:
    errores: list[str] = []

    edad_meses = state["paciente"]["edad_meses"]
    peso_kg = state["mediciones"]["peso_kg"]
    talla_cm = state["mediciones"]["talla_cm"]
    tipo_medicion = state["mediciones"]["tipo_medicion_talla"]

    imc = peso_kg / ((talla_cm / 100) ** 2)
    if not (5.0 <= imc <= 40.0):
        errores.append(
            f"IMC calculado ({imc:.1f}) fuera de un rango fisiológicamente plausible "
            "para un niño de 0-5 años; revise peso y talla."
        )

    if edad_meses < 24 and tipo_medicion == "de_pie":
        # Válido pero atípico: se corrige más adelante con el ajuste de 0.7cm.
        pass
    if edad_meses >= 24 and tipo_medicion == "acostado":
        pass

    if edad_meses < 0 or edad_meses > 60:
        errores.append("La edad debe estar entre 0 y 60 meses (0-5 años).")

    return {"validation_errors": errores}


def hay_errores_de_validacion(state: MidaState) -> str:
    return "error" if state.get("validation_errors") else "continuar"

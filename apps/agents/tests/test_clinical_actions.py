"""Tests del ajuste biocultural: la comparación comunitaria (Kogui/Arhuaco)
debe de-escalar la URGENCIA de las sugerencias para T/E y P/E cuando
contradice el hallazgo OMS, sin cambiar la clasificación OMS mostrada, y
sin de-escalar nunca un hallazgo crítico (edema, MUAC<11.5cm)."""

from __future__ import annotations

from apps.agents.clinical_actions import sugerencias_clinicas, sugerencias_familiares


def _resultado(indicador, nivel_alerta, clasificacion, comunitario=None):
    return {
        "indicador": indicador,
        "nivel_alerta": nivel_alerta,
        "clasificacion": clasificacion,
        "detalle": {"comunitario": comunitario} if comunitario else {},
    }


def test_comunitario_normal_deescala_te_severo_a_seguimiento_habitual():
    hallazgos = {
        "alerta_critica": False,
        "edema_bilateral": False,
        "resultados": [
            _resultado(
                "TE",
                "severo",
                "Talla Baja Severa",
                comunitario={"etnia": "kogui", "nivel_alerta": "normal", "clasificacion": "Normal"},
            ),
            _resultado("PE", "normal", "Normal"),
            _resultado("IMCE", "normal", "Normal"),
        ],
    }
    sugerencias = sugerencias_clinicas(hallazgos)
    # No debe aparecer la sugerencia de remisión prioritaria de "severo"...
    assert not any("Remisión prioritaria" in s for s in sugerencias)
    # ...sino la de seguimiento habitual...
    assert any("controles de crecimiento según el calendario habitual" in s for s in sugerencias)
    # ...y debe explicar el ajuste biocultural.
    assert any("Kogui" in s and "no confirma" in s for s in sugerencias)


def test_sin_comparacion_comunitaria_no_hay_deescalada():
    hallazgos = {
        "alerta_critica": False,
        "edema_bilateral": False,
        "resultados": [_resultado("TE", "severo", "Talla Baja Severa")],
    }
    sugerencias = sugerencias_clinicas(hallazgos)
    assert any("Remisión prioritaria" in s for s in sugerencias)
    assert not any("no confirma" in s for s in sugerencias)


def test_comunitario_normal_no_deescala_alerta_critica_por_edema():
    hallazgos = {
        "alerta_critica": True,
        "edema_bilateral": True,
        "resultados": [
            _resultado(
                "TE",
                "severo",
                "Talla Baja Severa",
                comunitario={"etnia": "kogui", "nivel_alerta": "normal", "clasificacion": "Normal"},
            ),
            _resultado("PT", "critico", "Emaciacion Severa (con edema)"),
        ],
    }
    sugerencias = sugerencias_clinicas(hallazgos)
    assert any("INMEDIATA" in s for s in sugerencias)


def test_comunitario_normal_no_deescala_muac_bypass_critico():
    # es_bypass (MUAC<11.5cm) no debe de-escalarse nunca -- _tiene_ajuste_biocultural
    # solo aplica a nivel_alerta moderado/severo, "critico" queda excluido.
    hallazgos = {
        "alerta_critica": True,
        "edema_bilateral": False,
        "resultados": [
            _resultado("PBE", "critico", "Critico"),
            _resultado(
                "TE",
                "severo",
                "Talla Baja Severa",
                comunitario={"etnia": "arhuaco", "nivel_alerta": "normal", "clasificacion": "Normal"},
            ),
        ],
    }
    sugerencias = sugerencias_clinicas(hallazgos)
    assert any("INMEDIATA" in s for s in sugerencias)


def test_comunitario_severo_no_deescala_nada():
    # Si la comparación comunitaria TAMBIÉN muestra hallazgo (no "normal"),
    # no hay de-escalada -- ambas comparaciones coinciden en que hay riesgo.
    hallazgos = {
        "alerta_critica": False,
        "edema_bilateral": False,
        "resultados": [
            _resultado(
                "TE",
                "severo",
                "Talla Baja Severa",
                comunitario={"etnia": "kogui", "nivel_alerta": "severo", "clasificacion": "Talla Baja Severa"},
            ),
        ],
    }
    sugerencias = sugerencias_clinicas(hallazgos)
    assert any("Remisión prioritaria" in s for s in sugerencias)


def test_version_familiar_tambien_deescala_y_explica():
    hallazgos = {
        "alerta_critica": False,
        "edema_bilateral": False,
        "resultados": [
            _resultado(
                "PE",
                "moderado",
                "Desnutricion Global Moderada",
                comunitario={"etnia": "arhuaco", "nivel_alerta": "normal", "clasificacion": "Normal"},
            ),
        ],
    }
    sugerencias = sugerencias_familiares(hallazgos)
    assert not any("2 a 4 semanas" in s for s in sugerencias)
    assert any("comunidad Arhuaco" in s for s in sugerencias)

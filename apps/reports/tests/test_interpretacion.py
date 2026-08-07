from __future__ import annotations

from apps.reports.interpretacion import construir_conclusion


def test_conclusion_normal_sin_comunitario_es_breve():
    r = {"valor_z": -0.5, "clasificacion": "Normal", "nivel_alerta": "normal", "detalle": {}}
    texto = construir_conclusion("IMCE", r)
    assert "Normal" in texto
    assert "z = -0.50" in texto
    assert "comunidad" not in texto


def test_conclusion_no_aplica_usa_motivo():
    r = {
        "valor_z": None,
        "clasificacion": "No aplica",
        "nivel_alerta": "no_aplica",
        "detalle": {"motivo": "No se proporcionó perímetro cefálico."},
    }
    texto = construir_conclusion("PCE", r)
    assert texto == "No se proporcionó perímetro cefálico."


def test_conclusion_severo_incluye_significado_glosario():
    r = {
        "valor_z": -3.2,
        "clasificacion": "Talla Baja Severa",
        "nivel_alerta": "severo",
        "detalle": {},
    }
    texto = construir_conclusion("TE", r)
    assert "Talla Baja Severa" in texto
    assert "desnutrición sostenida" in texto  # viene de glosario.significado_bajo


def test_conclusion_con_comunitario_discrepante_explica_ajuste():
    r = {
        "valor_z": -3.26,
        "clasificacion": "Talla Baja Severa",
        "nivel_alerta": "severo",
        "detalle": {
            "comunitario": {
                "etnia": "kogui",
                "valor_z": -0.11,
                "clasificacion": "Normal",
                "nivel_alerta": "normal",
            }
        },
    }
    texto = construir_conclusion("TE", r)
    assert "comunidad Kogui" in texto
    assert "rasgo de crecimiento poblacional saludable" in texto


def test_conclusion_con_comunitario_coincidente_refuerza():
    r = {
        "valor_z": -2.5,
        "clasificacion": "Delgadez Moderada",
        "nivel_alerta": "moderado",
        "detalle": {
            "comunitario": {
                "etnia": "arhuaco",
                "valor_z": -2.1,
                "clasificacion": "Delgadez Moderada",
                "nivel_alerta": "moderado",
            }
        },
    }
    texto = construir_conclusion("IMCE", r)
    assert "coinciden" in texto
    assert "rasgo de crecimiento poblacional saludable" not in texto

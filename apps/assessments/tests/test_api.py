from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.assessments.models import Evaluacion, ResultadoIndicador

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _mock_llm():
    """Los tests de API no necesitan un modelo GGUF real cargado -- se
    mockean los tres puntos donde el grafo llama al LLM (síntesis clínica,
    síntesis familiar y tips nutricionales, que corren en paralelo)."""
    with (
        patch("apps.agents.nodes.synthesis.generar_texto", return_value="Resumen clínico de prueba."),
        patch(
            "apps.agents.nodes.synthesis_familiar.generar_texto",
            return_value="Resumen familiar de prueba.",
        ),
        patch(
            "apps.agents.nodes.nutrition.generar_texto",
            return_value="Introducción y consejos de prueba.",
        ),
    ):
        yield


def _payload(**overrides):
    base = {
        "sexo": "M",
        "fecha_evaluacion": "2025-06-01",
        "edad_meses": 12,
        "peso_kg": 9.0,
        "talla_cm": 74.0,
        "tipo_medicion_talla": "acostado",
        "perimetro_cefalico_cm": 45.0,
        "perimetro_braquial_cm": 14.5,
        "edema_bilateral": False,
        "paciente": {
            "nombres": "Test",
            "apellidos": "Paciente",
            "fecha_nacimiento": "2024-06-01",
        },
    }
    base.update(overrides)
    return base


def test_post_evaluacion_devuelve_201_con_6_resultados():
    client = APIClient()
    resp = client.post("/api/v1/evaluaciones/", _payload(), format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["estado"] == "completada"
    assert len(resp.data["resultados"]) == 6
    assert resp.data["reporte"]["resumen_clinico"] == "Resumen clínico de prueba."
    assert resp.data["reporte"]["resumen_familiar"] == "Resumen familiar de prueba."
    assert resp.data["reporte_familiar_pdf_url"].endswith("/reporte-familiar/")


def test_post_evaluacion_edema_fuerza_alerta_critica():
    client = APIClient()
    resp = client.post("/api/v1/evaluaciones/", _payload(edema_bilateral=True), format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["alerta_critica"] is True
    pt = next(r for r in resp.data["resultados"] if r["indicador"] == "PT")
    assert pt["nivel_alerta"] == "critico"


def test_post_evaluacion_muac_critico_fuerza_alerta_critica():
    client = APIClient()
    resp = client.post(
        "/api/v1/evaluaciones/",
        _payload(perimetro_braquial_cm=10.5, edad_meses=20),
        format="json",
    )

    assert resp.status_code == 201, resp.data
    assert resp.data["alerta_critica"] is True
    pb = next(r for r in resp.data["resultados"] if r["indicador"] == "PBE")
    assert pb["es_bypass"] is True
    assert pb["nivel_alerta"] == "critico"


def test_post_evaluacion_sin_perimetros_opcionales_marca_no_aplica():
    client = APIClient()
    payload = _payload()
    del payload["perimetro_cefalico_cm"]
    del payload["perimetro_braquial_cm"]

    resp = client.post("/api/v1/evaluaciones/", payload, format="json")

    assert resp.status_code == 201, resp.data
    pce = next(r for r in resp.data["resultados"] if r["indicador"] == "PCE")
    pbe = next(r for r in resp.data["resultados"] if r["indicador"] == "PBE")
    assert pce["nivel_alerta"] == "no_aplica"
    assert pbe["nivel_alerta"] == "no_aplica"


def test_post_evaluacion_datos_invalidos_devuelve_400():
    client = APIClient()
    resp = client.post("/api/v1/evaluaciones/", _payload(peso_kg=999), format="json")
    assert resp.status_code == 400


def test_get_evaluacion_detalle():
    client = APIClient()
    creado = client.post("/api/v1/evaluaciones/", _payload(), format="json")
    eval_id = creado.data["id"]

    resp = client.get(f"/api/v1/evaluaciones/{eval_id}/")
    assert resp.status_code == 200
    assert resp.data["id"] == eval_id


def test_get_reporte_pdf():
    client = APIClient()
    creado = client.post("/api/v1/evaluaciones/", _payload(), format="json")
    eval_id = creado.data["id"]

    resp = client.get(f"/api/v1/evaluaciones/{eval_id}/reporte/")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    content = b"".join(resp.streaming_content)
    assert content[:4] == b"%PDF"


def test_get_reporte_familiar_pdf():
    client = APIClient()
    creado = client.post("/api/v1/evaluaciones/", _payload(), format="json")
    eval_id = creado.data["id"]

    resp = client.get(f"/api/v1/evaluaciones/{eval_id}/reporte-familiar/")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    content = b"".join(resp.streaming_content)
    assert content[:4] == b"%PDF"


def test_post_evaluacion_kogui_agrega_comparacion_comunitaria_y_deescala_sugerencia():
    client = APIClient()
    payload = _payload(
        edad_meses=36,
        peso_kg=12.0,
        talla_cm=84.0,
        tipo_medicion_talla="de_pie",
    )
    payload["paciente"]["etnia"] = "kogui"
    resp = client.post("/api/v1/evaluaciones/", payload, format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["paciente"]["etnia"] == "kogui"

    te = next(r for r in resp.data["resultados"] if r["indicador"] == "TE")
    assert te["nivel_alerta"] == "severo"  # la clasificación OMS no se oculta
    comunitario = te["detalle"]["comunitario"]
    assert comunitario["etnia"] == "kogui"
    assert comunitario["nivel_alerta"] == "normal"

    reporte = client.get(f"/api/v1/evaluaciones/{resp.data['id']}/reporte/")
    assert reporte.status_code == 200


def test_post_evaluacion_sin_etnia_no_agrega_comparacion_comunitaria():
    client = APIClient()
    resp = client.post("/api/v1/evaluaciones/", _payload(), format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["paciente"]["etnia"] == "ninguna"
    te = next(r for r in resp.data["resultados"] if r["indicador"] == "TE")
    assert "comunitario" not in te["detalle"]


def test_historial_paciente():
    client = APIClient()
    creado = client.post("/api/v1/evaluaciones/", _payload(), format="json")
    paciente_id = creado.data["paciente"]["id"]

    resp = client.get(f"/api/v1/pacientes/{paciente_id}/evaluaciones/")
    assert resp.status_code == 200
    assert len(resp.data) == 1

"""Genera, por cada indicador OMS calculado, una gráfica de crecimiento
(bandas de referencia OMS ±1/±2/±3 DE + el punto del paciente) como PNG
en base64, para embeber directamente en el PDF (auto-contenido, sin
archivos temporales que limpiar)."""

import base64
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from apps.who_standards import lms, loader

# Paleta (ver skill de dataviz / references/palette.md de este proyecto):
# superficie clara, tinta neutra, y paleta de estado fija para zonas de riesgo.
_SUPERFICIE = "#fcfcfb"
_INK_PRIMARIO = "#0b0b0b"
_INK_SECUNDARIO = "#52514e"
_INK_MUTED = "#898781"
_GRID = "#e1e0d9"
_MEDIANA = "#256abf"
_ESTADO_GOOD = "#0ca30c"
_ESTADO_WARNING = "#fab219"
_ESTADO_CRITICAL = "#d03b3b"

_NOMBRES_INDICADOR = {
    "TE": "Talla para la Edad",
    "PT": "Peso para la Talla",
    "PE": "Peso para la Edad",
    "IMCE": "IMC para la Edad",
    "PCE": "Perímetro Cefálico para la Edad",
    "PBE": "Perímetro Braquial para la Edad",
}

_UNIDADES_Y = {
    "TE": "Talla (cm)",
    "PT": "Peso (kg)",
    "PE": "Peso (kg)",
    "IMCE": "IMC (kg/m²)",
    "PCE": "Perímetro cefálico (cm)",
    "PBE": "Perímetro braquial (cm)",
}


def _color_estado(nivel_alerta: str) -> str:
    if nivel_alerta in ("severo", "critico"):
        return _ESTADO_CRITICAL
    if nivel_alerta == "moderado":
        return _ESTADO_WARNING
    return _ESTADO_GOOD


def generar_grafico_indicador(sexo: str, indicador: str, resultado) -> str | None:
    """resultado: instancia de ResultadoIndicador (o dict equivalente) con
    valor_z, clasificacion, nivel_alerta y detalle (que trae tabla_usada,
    edad_meses, x_input y, para PT, talla_cm_ajustada). Devuelve un data URI
    base64 listo para <img src="..."> o None si el indicador no aplica."""

    detalle = resultado.detalle if hasattr(resultado, "detalle") else resultado["detalle"]
    valor_z = resultado.valor_z if hasattr(resultado, "valor_z") else resultado["valor_z"]
    nivel_alerta = resultado.nivel_alerta if hasattr(resultado, "nivel_alerta") else resultado["nivel_alerta"]
    clasificacion = resultado.clasificacion if hasattr(resultado, "clasificacion") else resultado["clasificacion"]

    tabla = detalle.get("tabla_usada")
    if valor_z is None or not tabla:
        return None

    df = loader.get_table(tabla, sexo)
    col = loader.INDEX_COLUMN[tabla]

    if tabla in ("wfl", "wfh"):
        x_paciente = float(detalle["talla_cm_ajustada"])
        x_label = "Longitud/Talla (cm)"
    else:
        x_paciente = float(detalle["edad_meses"])
        x_label = "Edad (meses)"
    y_paciente = float(detalle["x_input"])

    xs = df[col].to_numpy(dtype=float)
    bandas = {}
    for z in (-3, -2, -1, 0, 1, 2, 3):
        bandas[z] = np.array(
            [lms.value_at_zscore(z, row.L, row.M, row.S) for row in df.itertuples()]
        )

    fig, ax = plt.subplots(figsize=(6.4, 4.0), dpi=150)
    fig.patch.set_facecolor(_SUPERFICIE)
    ax.set_facecolor(_SUPERFICIE)

    # Límites del eje Y calculados a mano (en vez de dejar que fill_between
    # los extienda al infinito) para poder sombrear "más allá de 3 DE" con
    # un límite finito y predecible.
    y_min_datos = min(bandas[-3].min(), y_paciente)
    y_max_datos = max(bandas[3].max(), y_paciente)
    _pad = (y_max_datos - y_min_datos) * 0.08
    y_lo, y_hi = y_min_datos - _pad, y_max_datos + _pad

    # Zonas de riesgo sombreadas -- misma convención de color que las
    # tarjetas/badges del reporte: verde -2..+2 (normal), ámbar 2..3
    # (moderado, requiere seguimiento), rojo más allá de 3 DE (severo/
    # crítico, requiere atención prioritaria). Ver "Leyenda de colores" en
    # la plantilla del reporte técnico para la explicación completa.
    ax.fill_between(xs, y_lo, bandas[-3], color=_ESTADO_CRITICAL, alpha=0.07, linewidth=0)
    ax.fill_between(xs, bandas[3], y_hi, color=_ESTADO_CRITICAL, alpha=0.07, linewidth=0)
    ax.fill_between(xs, bandas[-3], bandas[-2], color=_ESTADO_WARNING, alpha=0.08, linewidth=0)
    ax.fill_between(xs, bandas[2], bandas[3], color=_ESTADO_WARNING, alpha=0.08, linewidth=0)
    ax.fill_between(xs, bandas[-2], bandas[2], color=_ESTADO_GOOD, alpha=0.06, linewidth=0)
    ax.set_ylim(y_lo, y_hi)

    for z in (-3, 3):
        ax.plot(xs, bandas[z], color=_INK_MUTED, linewidth=0.8, linestyle=":")
    for z in (-2, 2):
        ax.plot(xs, bandas[z], color=_INK_SECUNDARIO, linewidth=1.1, linestyle="--")
    for z in (-1, 1):
        ax.plot(xs, bandas[z], color=_INK_MUTED, linewidth=0.8, linestyle=":")
    ax.plot(xs, bandas[0], color=_MEDIANA, linewidth=1.8, linestyle="-")

    for z in (-3, -2, -1, 0, 1, 2, 3):
        ax.annotate(
            f"{z:+d}" if z != 0 else "0",
            xy=(xs[-1], bandas[z][-1]),
            xytext=(4, 0),
            textcoords="offset points",
            fontsize=6.5,
            color=_INK_MUTED,
            va="center",
        )

    color_punto = _color_estado(nivel_alerta)
    ax.scatter(
        [x_paciente],
        [y_paciente],
        s=70,
        color=color_punto,
        edgecolor=_INK_PRIMARIO,
        linewidth=1.0,
        zorder=5,
        label="Paciente",
    )
    ax.annotate(
        f"Paciente: {clasificacion} (z={valor_z:.2f})",
        xy=(x_paciente, y_paciente),
        xytext=(8, 8),
        textcoords="offset points",
        fontsize=7.5,
        color=_INK_PRIMARIO,
        weight="bold",
    )

    ax.set_title(_NOMBRES_INDICADOR.get(indicador, indicador), fontsize=11, color=_INK_PRIMARIO, pad=10)
    ax.set_xlabel(x_label, fontsize=8.5, color=_INK_SECUNDARIO)
    ax.set_ylabel(_UNIDADES_Y.get(indicador, ""), fontsize=8.5, color=_INK_SECUNDARIO)
    ax.tick_params(colors=_INK_SECUNDARIO, labelsize=7.5)
    ax.grid(True, color=_GRID, linewidth=0.6)
    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.legend(loc="upper left", fontsize=7.5, frameon=False)

    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", facecolor=_SUPERFICIE)
    plt.close(fig)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"

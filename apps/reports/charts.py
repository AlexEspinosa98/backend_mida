"""Genera, por cada indicador OMS calculado, una o dos gráficas de
crecimiento como PNG en base64 (para embeber directamente en el PDF, sin
archivos temporales que limpiar):

- `generar_grafico_oms`: bandas de referencia OMS (±1/±2/±3 DE, curva LMS
  real) + el punto del paciente. Siempre disponible.
- `generar_grafico_comunitario`: bandas de referencia LOCALES (Kogui o
  Arhuaco, aproximación estadística media±DE -- ver
  apps/who_standards/local_patterns.py) + el mismo punto del paciente.
  Solo quando el resultado trae `detalle.comunitario` (etnia con patrón
  local disponible para ese indicador)."""

import base64
import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from apps.who_standards import local_patterns, lms, loader

# Paleta (ver skill de dataviz / references/palette.md de este proyecto):
# superficie clara, tinta neutra, y paleta de estado fija para zonas de riesgo.
_SUPERFICIE = "#fcfcfb"
_INK_PRIMARIO = "#0b0b0b"
_INK_SECUNDARIO = "#52514e"
_INK_MUTED = "#898781"
_GRID = "#e1e0d9"
_MEDIANA_OMS = "#256abf"
_MEDIANA_COMUNITARIA = "#4a3aa7"
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

# Indicadores cuyo desfase comunitario se aplica con rampa 0-24 meses
# (están indexados por edad, y el estudio documenta/grafica esa forma
# creciente). Peso-para-talla e IMC usan offset constante -- ver
# apps/who_standards/local_patterns.py.
_INDICADORES_CON_RAMPA_EDAD = {"TE", "PE"}


def _color_estado(nivel_alerta: str) -> str:
    if nivel_alerta in ("severo", "critico"):
        return _ESTADO_CRITICAL
    if nivel_alerta == "moderado":
        return _ESTADO_WARNING
    return _ESTADO_GOOD


def _extraer_campos(resultado):
    detalle = resultado.detalle if hasattr(resultado, "detalle") else resultado["detalle"]
    valor_z = resultado.valor_z if hasattr(resultado, "valor_z") else resultado["valor_z"]
    nivel_alerta = (
        resultado.nivel_alerta if hasattr(resultado, "nivel_alerta") else resultado["nivel_alerta"]
    )
    clasificacion = (
        resultado.clasificacion if hasattr(resultado, "clasificacion") else resultado["clasificacion"]
    )
    return detalle, valor_z, nivel_alerta, clasificacion


def _eje_x(tabla, detalle):
    if tabla in ("wfl", "wfh"):
        return float(detalle["talla_cm_ajustada"]), "Longitud/Talla (cm)"
    return float(detalle["edad_meses"]), "Edad (meses)"


def _limites_y(bandas, y_paciente):
    y_min_datos = min(bandas[-3].min(), y_paciente)
    y_max_datos = max(bandas[3].max(), y_paciente)
    pad = (y_max_datos - y_min_datos) * 0.08
    return y_min_datos - pad, y_max_datos + pad


def _nueva_figura(figsize=(5.4, 3.7)):
    fig, ax = plt.subplots(figsize=figsize, dpi=150)
    fig.patch.set_facecolor(_SUPERFICIE)
    ax.set_facecolor(_SUPERFICIE)
    return fig, ax


def _dibujar_zonas_y_bandas(ax, xs, bandas, y_lo, y_hi, color_mediana, estilo_mediana="-"):
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
    ax.plot(xs, bandas[0], color=color_mediana, linewidth=1.8, linestyle=estilo_mediana, label="Mediana")

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


def _dibujar_paciente(ax, x_paciente, y_paciente, nivel_alerta, clasificacion, valor_z):
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
        f"{clasificacion} (z={valor_z:.2f})",
        xy=(x_paciente, y_paciente),
        xytext=(8, 8),
        textcoords="offset points",
        fontsize=7.5,
        color=_INK_PRIMARIO,
        weight="bold",
    )


def _finalizar(fig, ax, titulo, x_label, y_label):
    ax.set_title(titulo, fontsize=10.5, color=_INK_PRIMARIO, pad=9)
    ax.set_xlabel(x_label, fontsize=8, color=_INK_SECUNDARIO)
    ax.set_ylabel(y_label, fontsize=8, color=_INK_SECUNDARIO)
    ax.tick_params(colors=_INK_SECUNDARIO, labelsize=7)
    ax.grid(True, color=_GRID, linewidth=0.6)
    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.legend(loc="upper left", fontsize=7, frameon=False)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", facecolor=_SUPERFICIE)
    plt.close(fig)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def generar_grafico_oms(sexo: str, indicador: str, resultado) -> str | None:
    """Gráfica contra el patrón OMS (bandas LMS reales). None si el
    indicador no aplica para esta evaluación."""
    detalle, valor_z, nivel_alerta, clasificacion = _extraer_campos(resultado)

    tabla = detalle.get("tabla_usada")
    if valor_z is None or not tabla:
        return None

    df = loader.get_table(tabla, sexo)
    col = loader.INDEX_COLUMN[tabla]
    xs = df[col].to_numpy(dtype=float)
    bandas = {
        z: np.array([lms.value_at_zscore(z, row.L, row.M, row.S) for row in df.itertuples()])
        for z in (-3, -2, -1, 0, 1, 2, 3)
    }

    x_paciente, x_label = _eje_x(tabla, detalle)
    y_paciente = float(detalle["x_input"])
    y_lo, y_hi = _limites_y(bandas, y_paciente)

    fig, ax = _nueva_figura()
    _dibujar_zonas_y_bandas(ax, xs, bandas, y_lo, y_hi, _MEDIANA_OMS)
    _dibujar_paciente(ax, x_paciente, y_paciente, nivel_alerta, clasificacion, valor_z)

    titulo = f"{_NOMBRES_INDICADOR.get(indicador, indicador)} — Patrón OMS"
    return _finalizar(fig, ax, titulo, x_label, _UNIDADES_Y.get(indicador, ""))


def generar_grafico_comunitario(sexo: str, indicador: str, resultado) -> str | None:
    """Gráfica contra el patrón comunitario (Kogui/Arhuaco), como
    aproximación mediana±DE (no una curva LMS -- ver PROVENANCE.md).
    Devuelve None si este resultado no trae comparación comunitaria."""
    detalle, _valor_z_oms, _nivel_oms, _clasif_oms = _extraer_campos(resultado)
    comunitario = detalle.get("comunitario")
    if comunitario is None:
        return None

    tabla = detalle.get("tabla_usada")
    if not tabla:
        return None

    df = loader.get_table(tabla, sexo)
    col = loader.INDEX_COLUMN[tabla]
    xs = df[col].to_numpy(dtype=float)

    mediana_oms_curva = np.array(
        [lms.value_at_zscore(0, row.L, row.M, row.S) for row in df.itertuples()]
    )
    offset = comunitario.get(
        "offset_meseta_cm", comunitario.get("offset_meseta_kg", comunitario.get("offset_meseta"))
    )
    sd = comunitario["sd"]

    if indicador in _INDICADORES_CON_RAMPA_EDAD:
        rampa = np.array([local_patterns.factor_rampa(x) for x in xs])
    else:
        rampa = np.ones_like(xs)

    mediana_local = mediana_oms_curva + offset * rampa
    bandas = {z: mediana_local + z * sd for z in (-3, -2, -1, 0, 1, 2, 3)}

    x_paciente, x_label = _eje_x(tabla, detalle)
    y_paciente = float(detalle["x_input"])
    y_lo, y_hi = _limites_y(bandas, y_paciente)

    fig, ax = _nueva_figura()
    _dibujar_zonas_y_bandas(ax, xs, bandas, y_lo, y_hi, _MEDIANA_COMUNITARIA, estilo_mediana="-.")
    _dibujar_paciente(
        ax,
        x_paciente,
        y_paciente,
        comunitario["nivel_alerta"],
        comunitario["clasificacion"],
        comunitario["valor_z"],
    )

    etnia_legible = comunitario["etnia"].capitalize()
    titulo = f"{_NOMBRES_INDICADOR.get(indicador, indicador)} — Patrón {etnia_legible} (aprox.)"
    return _finalizar(fig, ax, titulo, x_label, _UNIDADES_Y.get(indicador, ""))

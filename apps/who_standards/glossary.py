"""Contenido explicativo ESTÁTICO (no generado por LLM) sobre los 6
indicadores OMS: qué miden, qué significa clínicamente cada banda de
desviación estándar, y una descripción de la población de referencia OMS.

Se mantiene como texto fijo -- no generado por IA -- porque son
definiciones técnicas estándar (documentadas por la OMS) que no deben
quedar sujetas a que un LLM las parafrasee o se equivoque al explicarlas.
El LLM del nodo de síntesis recibe este texto como INSUMO para narrar el
reporte, nunca lo redacta desde cero.

Pure Python -- no Django imports.
"""
from __future__ import annotations

EXPLICACION_ESTANDAR_OMS = (
    "Los indicadores de este reporte se calculan comparando las mediciones del "
    "niño o niña contra los patrones de crecimiento infantil de la Organización "
    "Mundial de la Salud (OMS, 2006). Estos patrones se construyeron a partir de "
    "un estudio internacional (Multicentre Growth Reference Study) con miles de "
    "niños y niñas de distintos países, criados en condiciones favorables para un "
    "crecimiento saludable (buena alimentación, sin enfermedades frecuentes, "
    "acceso a atención en salud). Representan cómo debería crecer, en promedio, "
    "un niño o niña sano en cualquier parte del mundo -- no son un estándar de "
    "un solo país o una sola comunidad, sino una referencia internacional."
)

EXPLICACION_DESVIACION_ESTANDAR = (
    "¿Qué es la 'desviación estándar' (DE, también llamada 'z-score' o simplemente "
    "'z')? Es una forma de medir qué tan lejos está una medición del valor típico "
    "('mediana') para la edad y sexo del niño o niña, usando como unidad la "
    "variación normal que existe entre niños sanos -- no centímetros ni "
    "kilogramos directamente, sino 'cuántos pasos' de esa variación normal hay "
    "de distancia. Un z de 0 significa exactamente el valor típico; un z de -1 "
    "significa una desviación estándar por debajo del típico; un z de -2, dos "
    "desviaciones estándar por debajo; y así sucesivamente. El signo (+/-) indica "
    "si está por encima o por debajo del valor típico."
    "\n\n"
    "Cada gráfica muestra una línea central (la mediana OMS) y bandas a su "
    "alrededor marcadas en desviaciones estándar: +1/-1, +2/-2 y +3/-3. Mientras "
    "más lejos esté el punto del niño de la línea central, mayor es la diferencia "
    "respecto al patrón esperado. Entre -2 y +2 DE se considera dentro del rango "
    "normal para la mayoría de los indicadores. Pasar de -2 DE (hacia abajo) o "
    "+2 DE (hacia arriba, según el indicador) suele marcar el inicio de un "
    "hallazgo que amerita seguimiento; pasar de -3 o +3 DE indica una desviación "
    "severa que amerita atención médica prioritaria."
)

# Explica el mismo significado clínico que classify.py aplica en código, pero
# en prosa para el reporte -- debe mantenerse alineado con las bandas reales
# de apps/who_standards/classify.py si esas bandas cambian.
LEYENDA_COLORES = [
    {
        "clave": "normal",
        "color": "verde",
        "nivel": "Normal",
        "rango": "Entre -2 y +2 DE",
        "explicacion": (
            "El valor está dentro de la variación esperada para la edad y sexo del "
            "niño o niña. No se requiere ninguna acción adicional a partir de este "
            "hallazgo."
        ),
    },
    {
        "clave": "moderado",
        "color": "amarillo",
        "nivel": "Moderado",
        "rango": "Entre -3 y -2 DE, o entre +2 y +3 DE (según el indicador)",
        "explicacion": (
            "El valor se aleja de forma moderada del patrón esperado. Amerita "
            "seguimiento cercano (repetir el control en unas semanas) aunque no "
            "sea, por sí solo, una urgencia."
        ),
    },
    {
        "clave": "severo",
        "color": "rojo (severo)",
        "nivel": "Severo",
        "rango": "Más allá de -3 o +3 DE",
        "explicacion": (
            "Desviación importante del patrón esperado. Amerita remisión "
            "prioritaria y no debe esperar al próximo control de rutina."
        ),
    },
    {
        "clave": "critico",
        "color": "rojo (crítico)",
        "nivel": "Crítico",
        "rango": (
            "Edema bilateral presente, o perímetro braquial menor a 11.5cm "
            "(bypass por corte absoluto, independiente del z-score)"
        ),
        "explicacion": (
            "Signo de emergencia nutricional reconocido por la OMS/UNICEF "
            "independientemente de los demás hallazgos -- amerita remisión médica "
            "inmediata, sin esperar estudios adicionales."
        ),
    },
    {
        "clave": "no_aplica",
        "color": "gris",
        "nivel": "No aplica",
        "rango": "Fuera del rango de edad cubierto por el indicador, o dato no proporcionado",
        "explicacion": (
            "No se pudo calcular este indicador para esta evaluación (por ejemplo, "
            "el perímetro braquial no aplica antes de los 3 meses de edad)."
        ),
    },
]

GLOSARIO_INDICADORES: dict[str, dict] = {
    "TE": {
        "nombre": "Talla para la Edad",
        "que_mide": (
            "El crecimiento longitudinal (talla/longitud) acumulado a lo largo del "
            "tiempo, comparado con niños de la misma edad y sexo."
        ),
        "diagnostico_asociado": "Desnutrición crónica (retraso en talla / 'stunting').",
        "significado_bajo": (
            "Una talla baja para la edad (z por debajo de -2) sugiere que el niño "
            "no ha crecido en estatura lo esperado durante un período prolongado, "
            "típicamente por desnutrición sostenida, enfermedades repetidas, o "
            "condiciones socioeconómicas adversas durante meses o años."
        ),
        "significado_alto": (
            "Una talla alta para la edad no es, por sí sola, un hallazgo de "
            "riesgo nutricional -- es informativa (talla familiar, variación "
            "normal)."
        ),
    },
    "PT": {
        "nombre": "Peso para la Talla",
        "que_mide": (
            "La relación entre el peso corporal actual y la talla/longitud "
            "actual -- refleja el estado nutricional RECIENTE, no acumulado."
        ),
        "diagnostico_asociado": "Desnutrición aguda / emaciación ('wasting').",
        "significado_bajo": (
            "Un peso bajo para la talla (z por debajo de -2) indica pérdida de "
            "masa corporal reciente -- típicamente por enfermedad aguda, "
            "escasez puntual de alimentos, o infecciones recientes. Es el "
            "indicador que más rápido cambia y el que se usa para tamizaje de "
            "emergencia nutricional."
        ),
        "significado_alto": (
            "Un peso alto para la talla (z por encima de +2) indica sobrepeso; "
            "por encima de +3, obesidad."
        ),
    },
    "PE": {
        "nombre": "Peso para la Edad",
        "que_mide": (
            "La proporción global del peso corporal respecto a la edad "
            "cronológica -- un indicador general que combina efectos crónicos "
            "y agudos, sin distinguir entre ellos."
        ),
        "diagnostico_asociado": "Desnutrición global.",
        "significado_bajo": (
            "Un peso bajo para la edad (z por debajo de -2) indica que el niño "
            "pesa menos de lo esperado para su edad; puede deberse tanto a "
            "retraso de talla crónico como a pérdida de peso reciente, o ambos "
            "-- por eso se interpreta junto con talla-para-edad y "
            "peso-para-talla, no de forma aislada."
        ),
        "significado_alto": (
            "La OMS no define una categoría de 'sobrepeso' basada solo en este "
            "indicador -- para eso se usa peso-para-talla o IMC-para-edad."
        ),
    },
    "IMCE": {
        "nombre": "IMC para la Edad",
        "que_mide": (
            "El índice de masa corporal (peso entre talla al cuadrado) "
            "comparado con niños de la misma edad y sexo -- otra forma de "
            "evaluar la relación peso/talla, preferida en algunos contextos "
            "clínicos por encima de peso-para-talla."
        ),
        "diagnostico_asociado": "Delgadez / sobrepeso / obesidad.",
        "significado_bajo": (
            "Un IMC bajo para la edad (z por debajo de -2) indica delgadez, en "
            "línea con el mismo fenómeno que detecta peso-para-talla."
        ),
        "significado_alto": (
            "Un IMC alto para la edad (z por encima de +2) indica sobrepeso; "
            "por encima de +3, obesidad -- importante para la evaluación del "
            "equilibrio corporal desde la primera infancia."
        ),
    },
    "PCE": {
        "nombre": "Perímetro Cefálico para la Edad",
        "que_mide": (
            "El crecimiento del cráneo, que en los primeros años de vida "
            "refleja de forma indirecta el desarrollo del tejido cerebral."
        ),
        "diagnostico_asociado": "Microcefalia / macrocefalia.",
        "significado_bajo": (
            "Un perímetro cefálico bajo para la edad (z por debajo de -2, "
            "microcefalia) es una alerta de posible afectación del desarrollo "
            "neurológico y amerita evaluación médica -- no se explica por "
            "desnutrición reciente, así que un hallazgo aislado aquí merece "
            "atención independiente de los demás indicadores."
        ),
        "significado_alto": (
            "Un perímetro cefálico alto para la edad (z por encima de +2, "
            "macrocefalia) también amerita evaluación médica para descartar "
            "causas que requieran seguimiento."
        ),
    },
    "PBE": {
        "nombre": "Perímetro Braquial para la Edad",
        "que_mide": (
            "La reserva de tejido muscular y graso en la parte media del brazo "
            "-- un indicador rápido de reserva nutricional, muy usado en "
            "tamizaje comunitario porque no requiere calcular edad exacta ni "
            "hacer cuentas."
        ),
        "diagnostico_asociado": "Riesgo nutricional / depleción de masa muscular.",
        "significado_bajo": (
            "Este indicador se interpreta principalmente por un punto de corte "
            "directo en centímetros (no solo por z-score): menos de 11.5cm es "
            "un signo de desnutrición aguda severa que requiere remisión "
            "médica inmediata, independientemente de los demás hallazgos; "
            "entre 11.5 y 12.5cm indica riesgo nutricional que amerita "
            "vigilancia cercana."
        ),
        "significado_alto": "Un perímetro braquial normal-alto no se interpreta como hallazgo de riesgo.",
    },
}

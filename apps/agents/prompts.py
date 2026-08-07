PROMPT_SISTEMA_SINTESIS = """Eres un asistente clínico que redacta, en español, la sección de \
"Impresión clínica y sugerencias" de un reporte de tamizaje nutricional infantil (0-5 años) \
basado en los indicadores antropométricos de la OMS, dirigido a un médico.

Reglas estrictas:
- Los hallazgos (z-scores y clasificaciones) que se te entregan ya fueron calculados con las \
fórmulas oficiales de la OMS. NO debes recalcularlos, corregirlos, inventar nuevos valores \
numéricos, ni contradecir la clasificación dada.
- Usa exclusivamente los números, clasificaciones y hechos provistos; si necesitas citar un \
z-score o una clasificación, cópialo tal cual te lo dieron. No inventes hallazgos que no estén \
en la lista (por ejemplo, no menciones edema, fiebre, u otro signo clínico si no aparece \
explícitamente marcado como presente).
- El campo "Edema bilateral" solo puede tener el valor "Sí" o "No", tal como se te da. Si dice \
"No", el resumen NO debe mencionar edema como hallazgo presente en el paciente (puedes omitirlo \
por completo, o a lo sumo indicar que no hay signos de edema).
- El nivel de urgencia de cada indicador está EXCLUSIVAMENTE en su campo "nivel_alerta" \
(normal / moderado / severo / critico). Nunca infieras urgencia de otras palabras en la línea, \
como "corte absoluto" o "medido en cm" -- esas solo describen el MÉTODO de clasificación, no la \
gravedad. Por ejemplo, un indicador con nivel_alerta=normal debe describirse como normal, \
incluso si su línea menciona que se clasificó por un punto de corte en centímetros.
- NUNCA combines una clasificación "Normal" con la palabra "moderado", "severo" o "crítico" en \
la misma frase -- si nivel_alerta=normal, esa es la única palabra de urgencia que puedes usar \
para ese indicador. No trates de mostrar variedad de vocabulario a costa de precisión.
- No repitas el z-score y la clasificación de CADA indicador uno por uno como una lista. En vez \
de eso, agrupa en una sola frase corta los indicadores con nivel_alerta=normal (ej. "Los demás \
indicadores están dentro de lo esperado para su edad") y dedica el detalle de tu redacción a \
los indicadores que NO son normales (moderado/severo/critico), citando su z-score y \
clasificación exactos.
- Se te entrega una lista de "Sugerencias de proceso" (remisión, seguimiento, vigilancia) ya \
decidida por reglas clínicas fijas. Debes incorporarlas a tu redacción de forma fiel -- \
menciona todas las que se te dieron, en tus propias palabras, pero NO agregues sugerencias \
adicionales que no estén en la lista (nada de tratamientos, dosis, ni recomendaciones \
nutricionales específicas -- ese alcance no está definido todavía).
- Sé conciso pero completo (un párrafo de 6-10 líneas), en lenguaje clínico apropiado para un \
profesional de la salud, sin emojis ni encabezados.
- Si "Alerta crítica global" dice "Sí", menciónala explícitamente al inicio del párrafo. Si dice \
"No", no afirmes que hay una alerta crítica.
- Termina siempre recordando que este resumen es apoyo a la decisión clínica y no reemplaza \
el juicio profesional médico."""


PROMPT_SISTEMA_SINTESIS_FAMILIAR = """Eres un asistente que redacta, en español sencillo y \
cálido, la explicación de un tamizaje de crecimiento infantil (0-5 años) para la familia o \
cuidador de un niño o niña, SIN usar jerga médica ni mostrar números técnicos (z-scores).

Reglas estrictas:
- Usa exclusivamente los hechos y clasificaciones que se te entregan. No inventes hallazgos, \
no cambies una clasificación por otra, y no agregues información que no esté en los datos \
dados.
- NO uses la palabra "z-score" ni cites valores numéricos de desviación estándar -- en su lugar, \
describe si cada aspecto está "dentro de lo esperado para su edad" o "requiere atención", \
según el nivel_alerta dado (normal = dentro de lo esperado; moderado/severo/critico = requiere \
atención, con más urgencia mientras más alto el nivel).
- El campo "Edema bilateral" solo puede tener el valor "Sí" o "No". Si dice "No", NO menciones \
edema como algo presente.
- No repitas cada indicador uno por uno. Agrupa en una sola frase los que están \
"dentro de lo esperado" (nivel_alerta=normal) y dedica el detalle a los que "requieren \
atención" (moderado/severo/critico) -- nunca describas el mismo indicador con las dos \
etiquetas a la vez.
- Se te entrega una lista de "Sugerencias de proceso" (ya decididas, no las inventes ni las \
cambies) -- explícaselas a la familia en lenguaje simple y accionable (ej. "es importante \
llevar a su hijo/a a una consulta médica pronto" en vez de "remisión prioritaria").
- Si "Alerta crítica global" dice "Sí", el primer párrafo debe dejar clara la urgencia de buscar \
atención médica, en tono calmado pero directo -- sin generar pánico innecesario.
- Explica brevemente, en una frase, que estas gráficas comparan el crecimiento del niño o niña \
con el patrón de crecimiento saludable de la Organización Mundial de la Salud (un grupo de \
referencia internacional de niños sanos), no con un solo país o comunidad.
- Tono cálido, respetuoso, en 2-3 párrafos cortos. Nunca uses emojis.
- Termina siempre invitando a resolver dudas con el médico o profesional de salud que atiende \
al niño o niña -- este resumen no reemplaza esa consulta."""


_NOMBRES_INDICADOR = {
    "TE": "Talla para la Edad",
    "PT": "Peso para la Talla",
    "PE": "Peso para la Edad",
    "IMCE": "IMC para la Edad",
    "PCE": "Perímetro Cefálico para la Edad",
    "PBE": "Perímetro Braquial para la Edad",
}


def _lineas_base(
    hallazgos: dict, paciente: dict, mediciones: dict, clave_sugerencias: str = "sugerencias"
) -> list[str]:
    edema_texto = "Sí (presente)" if mediciones["edema_bilateral"] else "No (ausente)"
    lineas = [
        f"Paciente: sexo={paciente['sexo']}, edad={paciente['edad_meses']:.1f} meses.",
        f"Mediciones: peso={mediciones['peso_kg']} kg, talla={mediciones['talla_cm']} cm "
        f"({mediciones['tipo_medicion_talla']}), "
        f"perímetro cefálico={mediciones.get('perimetro_cefalico_cm')}, "
        f"perímetro braquial={mediciones.get('perimetro_braquial_cm')}.",
        f"Edema bilateral: {edema_texto}.",
        f"Alerta crítica global: {'Sí' if hallazgos.get('alerta_critica') else 'No'}.",
        "Hallazgos por indicador:",
    ]
    for r in hallazgos.get("resultados", []):
        nombre = _NOMBRES_INDICADOR.get(r["indicador"], r["indicador"])
        lineas.append(
            f"- {nombre}: z={r['valor_z']}, clasificación='{r['clasificacion']}', "
            f"nivel_alerta={r['nivel_alerta']}"
            + (
                " (nota: clasificado por punto de corte absoluto en cm, no por z-score -- "
                "el nivel_alerta indicado ya es el correcto, no lo cambies)"
                if r.get("es_bypass")
                else ""
            )
        )
    lineas.append("Sugerencias de proceso (ya decididas, no inventar otras):")
    for s in hallazgos.get(clave_sugerencias, []):
        lineas.append(f"- {s}")
    return lineas


def construir_prompt_sintesis(hallazgos: dict, paciente: dict, mediciones: dict) -> str:
    lineas = _lineas_base(hallazgos, paciente, mediciones)
    lineas.append(
        "\nRedacta la impresión clínica y sugerencias siguiendo las reglas del sistema, usando "
        "solo estos datos. Recuerda: si 'Edema bilateral' dice 'No (ausente)', no afirmes que el "
        "paciente tiene edema; y no agregues sugerencias fuera de la lista dada."
    )
    return "\n".join(lineas)


def construir_prompt_sintesis_familiar(hallazgos: dict, paciente: dict, mediciones: dict) -> str:
    lineas = _lineas_base(hallazgos, paciente, mediciones, clave_sugerencias="sugerencias_familiares")
    lineas.append(
        "\nRedacta la explicación para la familia siguiendo las reglas del sistema: sin "
        "z-scores, sin jerga médica, en tono cálido. Recuerda: si 'Edema bilateral' dice 'No "
        "(ausente)', no lo menciones como presente; y no agregues sugerencias fuera de la lista "
        "dada."
    )
    return "\n".join(lineas)

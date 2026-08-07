PROMPT_SISTEMA_SINTESIS = """Eres un asistente clínico que redacta, en español, la sección de \
"Impresión clínica" de un reporte de tamizaje nutricional infantil (0-5 años) basado en los \
indicadores antropométricos de la OMS, dirigido a un médico.

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
- Sé conciso (un párrafo de 4-8 líneas), en lenguaje clínico apropiado para un profesional de \
la salud, sin emojis ni encabezados.
- Si "Alerta crítica global" dice "Sí", menciónala explícitamente al inicio del párrafo. Si dice \
"No", no afirmes que hay una alerta crítica.
- Termina siempre recordando que este resumen es apoyo a la decisión clínica y no reemplaza \
el juicio profesional médico."""


_NOMBRES_INDICADOR = {
    "TE": "Talla para la Edad",
    "PT": "Peso para la Talla",
    "PE": "Peso para la Edad",
    "IMCE": "IMC para la Edad",
    "PCE": "Perímetro Cefálico para la Edad",
    "PBE": "Perímetro Braquial para la Edad",
}


def construir_prompt_sintesis(hallazgos: dict, paciente: dict, mediciones: dict) -> str:
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
    lineas.append(
        "\nRedacta la impresión clínica siguiendo las reglas del sistema, usando solo estos "
        "datos. Recuerda: si 'Edema bilateral' dice 'No (ausente)', no afirmes que el paciente "
        "tiene edema."
    )
    return "\n".join(lineas)

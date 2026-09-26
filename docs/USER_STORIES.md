# Historias de usuario — MIDA (ampliación del formulario de tamizaje)

**Estado: propuesta de diseño, nada de esto está implementado todavía.** Documenta cómo se vería
la ampliación del formulario que ya existe (`Paciente` + `Evaluacion`, hoy solo nombres, sexo,
etnia, peso, talla, perímetros braquial/cefálico, edema) para cubrir el formulario completo de
identificación del caso, y la separación en dos sesiones (médico / comunidad).

## Principio general: se guarda todo, cada reporte usa solo lo suyo

Todo lo que se recolecta en el formulario se guarda en la base de datos como parte del caso —
nada se descarta. Pero cada reporte generado (técnico, familiar) solo LEE los campos que le
corresponden a su audiencia; el resto queda disponible para consulta/auditoría del caso, pero
nunca se le pasa al LLM ni aparece en un PDF donde no aplica (ej. las observaciones de la
autoridad tradicional no tienen por qué aparecer en el reporte técnico para el médico).

## Modelo de datos — qué ya existe y qué es nuevo

**Ya existe** (`apps.patients.Paciente` / `apps.assessments.Evaluacion`): nombres, apellidos,
documento de identidad, fecha de nacimiento, sexo, etnia (pueblo indígena), peso, talla, tipo de
medición de talla, perímetro braquial, perímetro cefálico, edema bilateral.

**Todo lo demás es nuevo** — un modelo por sección del formulario, cada uno `OneToOneField` a
`Evaluacion` (no a `Paciente`, porque calidad de medición/signos clínicos/hábitos son cosas del
momento del tamizaje, no datos permanentes de la persona):

```
Paciente ──< Evaluacion >── ResultadoIndicador (ya existe)
                │        >── ReporteGenerado (ya existe)
                ├── CalidadMedicion        (nuevo, 1:1)
                ├── SignosClinicos         (nuevo, 1:1)
                ├── HabitosAlimentarios    (nuevo, 1:1)
                ├── ActividadFisica        (nuevo, 1:1)
                └── ContextoFamiliarTerritorial (nuevo, 1:1)
```

Varios campos del formulario son un mismo patrón "Sí / No / No reportado" (balanza calibrada,
antecedentes familiares, inseguridad alimentaria...) — se modelan todos con el mismo
`TextChoices` compartido para no repetir la lógica:

```python
class TriEstado(models.TextChoices):
    SI = "si", "Sí"
    NO = "no", "No"
    NO_REPORTADO = "no_reportado", "No reportado"
```

---

## HU-1 — Identificar el caso con un código y una fecha de reporte propios

Como médico o encargado de comunidad quiero que cada tamizaje tenga un código de caso único y
una fecha de reporte (distinta de la fecha en que se tomó la medición), para poder referenciar un
caso concreto en comunicaciones externas sin exponer el UUID interno.

- `Evaluacion.codigo_caso` — `CharField` único, generado por el sistema si no se manda uno
  explícito (ej. `MIDA-2026-000123`), o proporcionado a mano por quien registra el caso.
- `ReporteGenerado.fecha_reporte` — fecha en la que se generó/emitió el reporte (puede ser
  distinta de `Evaluacion.fecha_evaluacion`, que sigue siendo la fecha en que se tomó la
  medición física).
- `ReporteGenerado.objetivo_pdf` — texto libre corto, para qué se está generando este reporte en
  concreto (ej. "Remisión a control pediátrico", "Seguimiento trimestral") — se le pasa al LLM
  como contexto adicional al redactar, sin que invente un objetivo que no se le dio.

## HU-2 — Datos culturales y territoriales del menor

Como médico quiero registrar dónde vive el menor y con qué lengua/cultura se identifica, para que
el reporte familiar pueda redactarse en un lenguaje culturalmente apropiado y el reporte técnico
tenga contexto territorial completo.

- Se agregan a `Paciente`: `comunidad_asentamiento`, `municipio`, `departamento` (obligatorio,
  igual que en el formulario), `cuidador_principal`, `lengua_principal`,
  `requiere_mediacion_cultural` (booleano).
- `Paciente.Etnia` gana más opciones además de Kogui/Arhuaco (Kágaba es el autónimo Kogui — se
  deja como alias de display, no como una opción nueva separada, para no duplicar el mismo
  pueblo bajo dos códigos distintos en la base).
- Si `requiere_mediacion_cultural=True`, el LLM recibe una instrucción explícita de evitar
  tecnicismos médicos y priorizar comparaciones cotidianas al redactar el resumen familiar.

## HU-3 — Mediciones antropométricas ampliadas (cintura y cadera)

Como médico quiero registrar perímetro de cintura y de cadera además de lo que ya se mide, para
casos donde esos datos aporten al criterio clínico aunque no alimenten ningún indicador OMS de
los 6 ya calculados.

- `Evaluacion.perimetro_cintura_cm` y `Evaluacion.perimetro_cadera_cm` — `DecimalField`
  opcionales, igual que ya son opcionales `perimetro_cefalico_cm`/`perimetro_braquial_cm`.
- **No generan un indicador OMS nuevo** — no hay tabla LMS oficial de cintura/cadera para 0-5
  años en este tamizaje — quedan solo como dato clínico de contexto, visibles en el reporte
  técnico, nunca usados para calcular un `ResultadoIndicador`.
- `fecha_evaluacion` (ya existe) es también la fecha de medición del formulario — no se duplica
  un campo nuevo para lo mismo.

## HU-4 — Calidad de la medición

Como médico quiero dejar constancia de si el instrumento estaba calibrado y si la medición se
repitió, para que quien lea el reporte técnico sepa qué tan confiable es el dato — un peso tomado
con una balanza no calibrada no debería pesar igual en la interpretación que uno tomado con
protocolo completo.

- Nuevo modelo `CalidadMedicion` (`OneToOneField` a `Evaluacion`):
  - `balanza_calibrada` (`TriEstado`)
  - `instrumentos_validados` (`TriEstado`) — el segundo selector "No reportado" del formulario
  - `medicion_repetida` (`TriEstado`)
  - `observaciones` (texto libre)
- El resumen clínico del LLM menciona explícitamente cuando `balanza_calibrada != "si"` o
  `medicion_repetida != "si"`, como una nota de precaución — nunca lo omite silenciosamente.

## HU-5 — Signos clínicos presentes al momento de la medición

Como médico quiero marcar qué signos clínicos observé en el menor durante la visita, para que el
reporte técnico incluya el cuadro clínico completo, no solo las cifras antropométricas.

- Nuevo modelo `SignosClinicos` (1:1 a `Evaluacion`), un `BooleanField` por cada signo del
  formulario: `fatiga`, `decaimiento`, `fiebre`, `diarrea`, `vomito`, `perdida_peso_reciente`,
  `rechazo_alimento`, `deshidratacion`, `dificultad_respiratoria`. Más `observaciones` (texto
  libre).
- **Regla clínica, no del LLM** (mismo patrón que `clinical_actions.py` ya usa para las
  sugerencias de próximos pasos): si `deshidratacion=True` o `dificultad_respiratoria=True`
  junto con un indicador ya `severo`/`crítico`, `Evaluacion.alerta_critica` se marca `True`
  automáticamente, sin esperar a que el LLM lo "note" en la prosa.
- Estos campos **solo aparecen en el reporte técnico**, nunca en el familiar — no tiene sentido
  listarle a un cuidador una lista de síntomas en jerga clínica sin la interpretación de un
  profesional al lado.

## HU-6 — Hábitos alimentarios reportados por la familia

Como médico o encargado de comunidad quiero registrar qué come habitualmente el menor (no lo que
debería comer — eso ya lo genera el plan nutricional de `apps.nutrition`), para que el resumen y
el plan sugerido partan de la realidad del hogar, no de un punto de partida genérico.

- Nuevo modelo `HabitosAlimentarios` (1:1 a `Evaluacion`): `numero_comidas_dia` (entero),
  `alimentos_frecuentes` (texto, una entrada por línea o separado por comas — se parsea a lista
  al leerlo, no se pide un formato estructurado en el formulario), `alimentos_escasos` (mismo
  formato), `cambios_recientes_alimentacion` (texto libre), `restricciones_culturales_familiares`
  (texto libre), `acceso_agua_segura` (`TriEstado`).
- **Importante para no confundir con el plan generado**: esto es lo que la familia YA hace, se le
  pasa al LLM como contexto de partida al generar `plan_nutricional` (HU ya existente) — el plan
  sigue viniendo del catálogo `Alimento`/`apps.nutrition`, pero ahora informado por lo que el
  hogar reporta tener disponible (cruza contra `alimentos_escasos` para no sugerir algo que la
  familia ya dijo que no consigue).

## HU-7 — Actividad física del menor

Como médico quiero registrar el nivel de actividad física y cualquier limitación de movimiento,
para completar el panorama de desarrollo, especialmente relevante si el menor tiene una condición
que restrinja su movimiento.

- Nuevo modelo `ActividadFisica` (1:1 a `Evaluacion`): `nivel_actividad`
  (`TextChoices`: bajo/moderado/alto), `actividades_diarias` (texto, incluida en el reporte
  técnico como contexto), `limitaciones` (texto libre).

## HU-8 — Contexto familiar y territorial

Como médico quiero registrar antecedentes familiares de baja talla y las condiciones del entorno
(inseguridad alimentaria, acceso a salud), para distinguir un caso con causa genética/familiar
probable de uno donde el entorno es el factor dominante — cambia la recomendación clínica.

- Nuevo modelo `ContextoFamiliarTerritorial` (1:1 a `Evaluacion`):
  `antecedentes_familiares_baja_talla` (`TriEstado`), `hermanos_baja_talla` (`TriEstado`),
  `inseguridad_alimentaria_reportada` (`TriEstado`), `dificultad_acceso_salud` (`TriEstado`),
  `observaciones_familia` (texto), `observaciones_autoridad_tradicional` (texto).
- `observaciones_autoridad_tradicional` es el único campo pensado explícitamente para que lo
  llene alguien de la comunidad (no necesariamente el médico) — ver HU-10/HU-11.

## HU-9 — Dos roles de acceso: médico y comunidad

Como administrador del sistema quiero que existan dos tipos de sesión con permisos distintos,
porque hoy la API no tiene ningún control de acceso (está abierta) y el formulario completo
(signos clínicos, calidad de medición) no debería estar en manos de alguien sin formación
clínica, mientras que el registro básico del caso y el reporte familiar sí.

- Se agrega autenticación por token (`rest_framework.authtoken`, mismo mecanismo ya usado en
  otros backends de este servidor) y un `PerfilUsuario` con `rol` (`medico` / `comunidad`),
  mismo patrón que `jornadas.PerfilUsuario` en el backend de Aluna Kunsamu.
- `IsMedico` / `IsComunidad` como `permission_classes` de DRF, aplicadas por endpoint (ver
  HU-10/HU-11).

## HU-10 — Sesión médico: captura el caso completo y genera ambos reportes

Como médico quiero poder llenar el formulario completo (identificación, mediciones, calidad,
signos clínicos, alimentación, actividad, contexto familiar) y generar tanto el reporte técnico
como el familiar desde una sola sesión, porque soy quien tiene el criterio clínico para
interpretar signos y calidad de medición.

- `POST /api/v1/evaluaciones/` (ya existe) se amplía para aceptar los bloques nuevos anidados en
  el payload (`calidad_medicion`, `signos_clinicos`, `habitos_alimentarios`, `actividad_fisica`,
  `contexto_familiar`), todos opcionales — un médico apurado puede seguir mandando solo lo
  mínimo de hoy y el caso queda incompleto pero válido, no rechazado.
- Requiere `rol=medico`. Genera `reporte_pdf_url` y `reporte_familiar_pdf_url` en la misma
  respuesta, igual que hoy.

## HU-11 — Sesión comunidad: registra el caso básico y accede al reporte familiar

Como encargado de comunidad (autoridad tradicional, promotor de salud comunitario) quiero poder
registrar las mediciones básicas de un menor y obtener el reporte familiar, sin necesitar acceso
a la parte clínica del formulario que no me corresponde evaluar.

- Mismo endpoint `POST /api/v1/evaluaciones/`, pero con `rol=comunidad`: los bloques
  `signos_clinicos` y `calidad_medicion` quedan **bloqueados** (`400` si se intenta mandarlos) —
  esos dos son criterio clínico, no un registro comunitario. El resto de bloques (cultural,
  hábitos, actividad, contexto familiar) sí están disponibles.
- La respuesta para `rol=comunidad` **no incluye `reporte_pdf_url`** (el técnico es solo para
  médico) — solo `reporte_familiar_pdf_url`. Si el caso tiene una `alerta_critica=True`, la
  respuesta además indica explícitamente que debe remitirse a valoración médica presencial, para
  que la ausencia del reporte técnico no se lea como "todo bien".
- `observaciones_autoridad_tradicional` (HU-8) es el campo pensado para llenarse justo en esta
  sesión.

## HU-12 — Cada reporte usa solo los campos de su audiencia

Como desarrollador del pipeline de análisis quiero que el payload que se le arma al LLM para cada
tipo de reporte incluya solo los campos relevantes para esa audiencia, para no filtrar
información clínica en el reporte familiar ni "aplanar" el reporte técnico con detalles que no
aportan a un profesional de salud.

| Bloque | Reporte técnico (médico) | Reporte familiar (cuidador/comunidad) |
|---|---|---|
| Identificación + culturales (HU-1/HU-2) | Sí, completo | Sí, sin el código de caso interno |
| Mediciones + indicadores OMS | Sí, con z-scores | Sí, en semáforo verde/amarillo/rojo (ya existe) |
| Cintura/cadera (HU-3) | Sí | No |
| Calidad de medición (HU-4) | Sí | No |
| Signos clínicos (HU-5) | Sí | No |
| Hábitos alimentarios (HU-6) | Sí (contexto) | Sí (para el plan nutricional) |
| Actividad física (HU-7) | Sí | Resumido, sin jerga |
| Contexto familiar/territorial (HU-8) | Sí | Solo lo que la propia familia reportó, no antecedentes clínicos interpretados |

Esto se implementa como dos funciones de armado de payload separadas (`_payload_tecnico` /
`_payload_familiar`), no un único payload con un flag — mismo espíritu que ya separa
`sintesis_clinica` de `sintesis_familiar` como nodos distintos del grafo LangGraph.

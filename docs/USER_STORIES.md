# Historias de usuario — MIDA (ampliación del formulario de tamizaje)

**Estado:** el flujo de acceso (HU-9 a HU-12) **está implementado**: login por token, acceso
restringido a médicos, y un flujo de superadmin para crear/editar/desactivar médicos y resetear
contraseñas — ver `apps/accounts/`.

El modelo de datos ampliado (HU-1 a HU-8) **está implementado y persistido** exactamente según el
contrato JSON documentado más abajo (`apps/patients/models.py`, `apps/assessments/models.py`,
`apps/assessments/serializers.py`, `apps/assessments/services.py`). Dos matices sobre qué tan
completa quedó cada una:

- **HU-4 y HU-5 sí tienen su regla clínica activa** (no solo el dato guardado): una calidad de
  medición deficiente agrega una nota de precaución al resumen técnico, y deshidratación/
  dificultad respiratoria junto con un indicador severo/crítico fuerza `alerta_critica=True`,
  automáticamente, sin depender del LLM.
- **HU-6 (hábitos alimentarios) por ahora solo se guarda** — todavía NO se cruza contra
  `alimentos_escasos` al generar el plan nutricional de `apps.nutrition` (el plan sigue
  viniendo solo del catálogo, sin ese contexto adicional). Queda como mejora pendiente.
- **HU-13 (separación técnico/familiar)**: los bloques nuevos se guardan y se devuelven completos
  en la respuesta de la API (para que el médico los consulte), pero el LLM de síntesis todavía no
  recibe un payload diferenciado por bloque — sigue recibiendo lo mismo que antes de esta
  ampliación. La lectura selectiva por audiencia descrita en HU-13 queda como trabajo futuro
  sobre el grafo de `apps.agents`.

Documenta cómo se vería la ampliación del formulario que ya existe (`Paciente` + `Evaluacion`,
hoy solo nombres, sexo, etnia, peso, talla, perímetros braquial/cefálico, edema) para cubrir el
formulario completo de identificación del caso, y el flujo de acceso: **ya no existe una sesión
de "comunidad" con acceso libre** — todo el registro del caso y la generación de reportes
(técnico y familiar) los hace un médico autenticado; un superadmin solo administra usuarios.

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

Como médico quiero que cada tamizaje tenga un código de caso único y
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

Como médico quiero registrar qué come habitualmente el menor (no lo que
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
- `observaciones_autoridad_tradicional` recoge lo que la autoridad tradicional o el promotor
  comunitario le haya comunicado al médico durante la visita — lo registra el médico en su misma
  sesión (ya no hay una sesión de comunidad aparte, ver HU-9/HU-10), como cualquier otro campo del
  formulario.

## Contrato JSON completo — `POST /api/v1/evaluaciones/`

**Este es el contrato que el backend va a implementar para aceptar el formulario completo.**
Todo lo de acá abajo son nombres y valores definitivos — el frontend puede alinearse a esto ya
mismo, en paralelo a que se implemente. Requiere sesión de médico (`Authorization: Token
<token>`), igual que hoy.

Todo lo que ya existe (`sexo`, `edad_meses`, `peso_kg`, `talla_cm`, `tipo_medicion_talla`,
`perimetro_cefalico_cm`, `perimetro_braquial_cm`, `edema_bilateral`, `paciente.*`) se mantiene
con el mismo nombre y las mismas validaciones que hoy — nada de eso cambia. Lo nuevo son los
campos de `paciente` de HU-2, los campos sueltos de HU-1/HU-3, y los cinco bloques anidados
opcionales de HU-4 a HU-8.

**Para evitar que se repita el mismo tipo de error 400 que ya salió** (`"masculino"` en vez de
`"M"`, `"pie"` en vez de `"de_pie"`), el backend va a **aceptar alias de entrada** en los dos
campos donde es más fácil equivocarse, y normalizarlos internamente — no hace falta que el
frontend traduzca a mano:

- `sexo`: acepta `"M"`, `"F"`, y también (sin distinguir mayúsculas) `"masculino"`, `"femenino"`.
- `tipo_medicion_talla`: acepta `"de_pie"`, `"acostado"`, y también `"pie"`/`"estatura"` (→
  `de_pie`), `"longitud"` (→ `acostado`).
- `paciente.etnia`: acepta `"kogui"` y también `"kaggaba"` (autónimo del mismo pueblo, ver HU-2)
  — ambos se guardan como `"kogui"`. `"arhuaco"` y `"ninguna"` se mantienen igual.

Todo lo demás (los `TriEstado`, los booleanos de `signos_clinicos`, `nivel_actividad`) **no**
tiene alias — son valores de un formulario cerrado, no texto libre del usuario, así que el
frontend debe mandarlos exactos como están documentados abajo.

### Ejemplo de payload completo

```json
{
  "codigo_caso": "KAG-20260927-125231",
  "fecha_reporte": "2026-09-27",
  "objetivo_reporte": "Seguimiento nutricional bimensual",
  "notas_administrativas": "Brigada territorial acompañada por cabildo local, comunidad de Seykúkui.",

  "paciente": {
    "nombres": "Samin K.",
    "apellidos": "Protegido por soberanía CARE",
    "etnia": "kogui",
    "comunidad_asentamiento": "Seykúkui",
    "municipio": "Santa Marta",
    "departamento": "magdalena",
    "cuidador_principal": "Madre (Saga)",
    "lengua_principal": "kaggaba",
    "requiere_mediacion_cultural": true
  },

  "sexo": "M",
  "fecha_evaluacion": "2026-09-27",
  "edad_meses": "24",
  "peso_kg": "11.45",
  "talla_cm": "84.5",
  "tipo_medicion_talla": "de_pie",
  "perimetro_cefalico_cm": "47.5",
  "perimetro_braquial_cm": "13.2",
  "perimetro_cintura_cm": "46.0",
  "perimetro_cadera_cm": "48.0",
  "edema_bilateral": false,

  "calidad_medicion": {
    "balanza_calibrada": "si",
    "instrumentos_validados": "si",
    "medicion_repetida": "si",
    "observaciones": "Medición tomada en bohío tradicional con piso de madera irregular; se usó base rígida nivelada. Niño cooperador."
  },

  "signos_clinicos": {
    "fatiga": false,
    "decaimiento": false,
    "fiebre": false,
    "diarrea": false,
    "vomito": false,
    "perdida_peso_reciente": false,
    "rechazo_alimento": false,
    "deshidratacion": false,
    "dificultad_respiratoria": false,
    "observaciones": ""
  },

  "habitos_alimentarios": {
    "numero_comidas_dia": 3,
    "alimentos_frecuentes": "Guineo verde, yuca dulce, malanga (ñame), frijol guajiro, plátano, leche materna.",
    "alimentos_escasos": "Huevos de campo, pescado de cuenca baja, aguacate, cítricos de temporada.",
    "cambios_recientes_alimentacion": "Cosecha baja de frijol por sequía.",
    "restricciones_culturales_familiares": "Ayuno ritual orientado por el Mamo, exclusión temporal de carnes rojas o grasas externas.",
    "acceso_agua_segura": "si"
  },

  "actividad_fisica": {
    "nivel_actividad": "moderado",
    "actividades_diarias": "Juegos en bohío y patio, caminatas cortas con la madre.",
    "limitaciones": ""
  },

  "contexto_familiar": {
    "antecedentes_familiares_baja_talla": "si",
    "hermanos_baja_talla": "no",
    "inseguridad_alimentaria_reportada": "no_reportado",
    "dificultad_acceso_salud": "si",
    "observaciones_familia": "Comentarios de la madre sobre buen apetito, ánimo y destrezas al caminar en montaña.",
    "observaciones_autoridad_tradicional": "Petición de armonización espiritual (pagamento), consentimiento para derivación médica si fuere requerida."
  }
}
```

### Todos los bloques son opcionales (excepto lo que ya era obligatorio hoy)

Un médico apurado puede seguir mandando solo `sexo`/`edad_meses`/`peso_kg`/`talla_cm`/
`tipo_medicion_talla` (lo mínimo de hoy) y el caso queda incompleto pero válido — nada de lo
nuevo es obligatorio. Si se omite `codigo_caso`, el sistema genera uno (`MIDA-2026-000123`).

### Referencia rápida de valores válidos

| Campo | Valores |
|---|---|
| `sexo` | `M`, `F` (alias: `masculino`, `femenino`) |
| `tipo_medicion_talla` | `de_pie`, `acostado` (alias: `pie`, `estatura`, `longitud`) |
| `paciente.etnia` | `ninguna`, `kogui` (alias: `kaggaba`), `arhuaco` |
| cualquier campo `TriEstado` (`balanza_calibrada`, `instrumentos_validados`, `medicion_repetida`, `acceso_agua_segura`, `antecedentes_familiares_baja_talla`, `hermanos_baja_talla`, `inseguridad_alimentaria_reportada`, `dificultad_acceso_salud`) | `si`, `no`, `no_reportado` (exactos, sin alias) |
| `actividad_fisica.nivel_actividad` | `bajo`, `moderado`, `alto` |
| booleanos de `signos_clinicos` | `true` / `false` |

### Respuesta

La respuesta de `EvaluacionSerializer` no cambia de forma — sigue trayendo `id`, `estado`,
`resultados` (los 6 indicadores OMS), `reporte` (resúmenes generados por el LLM),
`reporte_pdf_url`, `reporte_familiar_pdf_url`, `alerta_critica`. Los bloques nuevos
(`calidad_medicion`, `signos_clinicos`, etc.) se agregan como objetos anidados de solo lectura,
igual que ya se hace con `paciente`/`resultados`/`reporte` — se pueden consultar de vuelta en el
mismo `GET /api/v1/evaluaciones/{id}/`.

## HU-9 — Login obligatorio: solo médicos acceden al sistema

Como administrador del sistema quiero que ningún endpoint clínico sea accesible sin iniciar
sesión, porque hoy la API no tiene ningún control de acceso (está abierta) y ya no existe un
perfil de "comunidad" con acceso libre — todo el registro del caso (formulario completo) y la
generación de reportes (técnico y familiar) pasan a ser una tarea exclusiva del médico.

- Se agrega autenticación por token (`rest_framework.authtoken`, mismo mecanismo ya usado en
  otros backends de este servidor) y un `PerfilUsuario` con `rol` (`medico` / `superadmin`).
  Un usuario sin fila en `PerfilUsuario` (p. ej. el primer `createsuperuser` de despliegue) se
  trata como `superadmin` automáticamente, para que el primer usuario del sistema nunca quede
  bloqueado por falta de perfil.
- `POST /api/v1/auth/login/` — único endpoint público (`username` + `password`), devuelve un
  token y el `rol` del usuario. No hay registro público de cuentas: toda cuenta la crea un
  superadmin (ver HU-11).
- Todos los endpoints de evaluaciones (`/api/v1/evaluaciones/...`, `/api/v1/pacientes/.../
  evaluaciones/`) y el de catálogo de nutrición (`/api/v1/nutricion/catalogo/`) exigen rol
  `medico` o superior (`EsMedico`) vía `Authorization: Token <token>`. Sin token, o con un token
  de un usuario inactivo, la API responde `401`; con token válido pero sin rol suficiente,
  `403`.

## HU-10 — Sesión médico: captura el caso completo y genera ambos reportes

Como médico quiero poder llenar el formulario completo (identificación, mediciones, calidad,
signos clínicos, alimentación, actividad, contexto familiar) y generar tanto el reporte técnico
como el familiar desde una sola sesión, porque soy quien tiene el criterio clínico para
interpretar signos y calidad de medición — y porque ya no hay una sesión de comunidad aparte que
recoja una versión reducida del caso.

- `POST /api/v1/evaluaciones/` (ya existe) se amplía para aceptar los bloques nuevos anidados en
  el payload (`calidad_medicion`, `signos_clinicos`, `habitos_alimentarios`, `actividad_fisica`,
  `contexto_familiar`), todos opcionales — un médico apurado puede seguir mandando solo lo
  mínimo de hoy y el caso queda incompleto pero válido, no rechazado.
- Requiere sesión de médico (rol `medico` o `superadmin`, vía `EsMedico`). Genera
  `reporte_pdf_url` y `reporte_familiar_pdf_url` en la misma respuesta, igual que hoy — el
  médico decide con cuál de los dos se queda o cuál entrega según a quién se lo esté explicando.

## HU-11 — Superadmin: crear usuarios médicos

Como superadministrador quiero poder crear cuentas de médico (usuario, contraseña inicial, datos
básicos), porque ya no hay registro público y alguien tiene que dar de alta a cada médico que va
a usar el sistema.

- `POST /api/v1/usuarios/` — exclusivo de rol `superadmin` (`EsSuperadmin`). Recibe `username`,
  `password`, `email`, `first_name`, `last_name`, `rol` (`medico` o `superadmin`). Crea el
  `User` y su `PerfilUsuario` en el mismo paso.
- `GET /api/v1/usuarios/` / `GET /api/v1/usuarios/{id}/` — lista y detalle, para que el
  superadmin vea qué cuentas existen y con qué rol.
- Un superadmin puede crear a otro superadmin, no solo médicos — el sistema no limita cuántos
  superadmins hay, pero por defecto todo usuario nuevo se crea como `medico` si no se especifica
  otra cosa.

## HU-12 — Superadmin: modificar, desactivar y cambiar contraseña de usuarios

Como superadministrador quiero poder editar los datos de un usuario existente, desactivarlo si
deja de trabajar en el proyecto, y resetear su contraseña si la olvidó o si sospecho que quedó
expuesta — sin tener que borrar el historial de qué médico generó qué reporte.

- `PATCH /api/v1/usuarios/{id}/` — edita `email`, `first_name`, `last_name`, `rol`,
  `is_active`. Exclusivo de `EsSuperadmin`. No acepta cambiar la contraseña por esta vía (ver
  el punto siguiente) para que un `PATCH` normal de "editar mis datos" nunca deje una contraseña
  viajando por accidente.
- `DELETE /api/v1/usuarios/{id}/` — no borra el usuario, lo desactiva (`is_active=False`): el
  historial de evaluaciones/reportes generados por ese médico se conserva intacto, pero ya no
  puede iniciar sesión.
- `POST /api/v1/usuarios/{id}/cambiar-password/` — acción exclusiva del superadmin para fijarle
  una contraseña nueva a cualquier usuario. Al aplicarla, se invalida cualquier token de sesión
  previo de ese usuario (tiene que volver a iniciar sesión con la contraseña nueva) — un cambio
  de contraseña casi siempre ocurre porque la anterior se sospecha comprometida, así que dejar
  vivo el token viejo anularía el propósito del cambio.
- Un médico **no** tiene acceso a ninguno de estos endpoints sobre sí mismo ni sobre otros — el
  cambio de contraseña de un médico solo lo puede iniciar un superadmin (no hay flujo de
  "olvidé mi contraseña" autoservido en esta primera versión).

## HU-13 — Cada reporte usa solo los campos de su audiencia

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

# MIDA Backend — Tamizaje Nutricional Infantil (OMS)

Backend Django + LangGraph que recibe mediciones antropométricas de niños
de 0-5 años (edad, peso, talla, perímetro cefálico y braquial opcionales,
edema bilateral opcional, sexo), calcula los 6 indicadores oficiales de la
OMS (T/E, P/T, P/E, IMC/E, PC/E, PB/E) con las tablas LMS reales descargadas
de who.int, y genera un reporte clínico inicial en PDF con gráficas
comparativas contra las curvas de referencia OMS.

## Arquitectura

- **`apps/who_standards`** — matemática LMS + tablas OMS oficiales (CSV
  trazables, ver `apps/who_standards/data/PROVENANCE.md`) y clasificación
  clínica. Paquete Python puro, sin dependencia de Django.
- **`apps/agents`** — grafo LangGraph: un validador, 6 nodos indicador
  determinísticos (paralelos), un agregador, y un único nodo con LLM que
  redacta la impresión clínica en lenguaje natural a partir de los hallazgos
  ya calculados (nunca calcula ni corrige números).
- **`apps/patients` / `apps/assessments`** — modelos Django (Paciente,
  Evaluación, ResultadoIndicador, ReporteGenerado) y la API REST.
- **`apps/reports`** — gráficas (matplotlib) y PDF (WeasyPrint).

El LLM es un modelo local descargado de Hugging Face (Qwen2.5-3B-Instruct,
GGUF cuantizado, servido con `llama-cpp-python` sobre CPU) — costo cero, sin
API key, y horneado en la imagen Docker para funcionar sin conexión a
internet en runtime.

## Levantar en desarrollo (sin Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # y ajustar DJANGO_SETTINGS_MODULE=config.settings.local, LLM_MODEL_PATH local, etc.
python manage.py migrate
python manage.py runserver
```

Necesitas un archivo `.gguf` local (por ejemplo, descargado con
`huggingface_hub.hf_hub_download("Qwen/Qwen2.5-3B-Instruct-GGUF", "qwen2.5-3b-instruct-q4_k_m.gguf")`)
y apuntar `LLM_MODEL_PATH` a esa ruta.

## Levantar con Docker (despliegue on-premise)

```bash
cp .env.example .env   # editar SECRET_KEY, ALLOWED_HOSTS, credenciales Postgres
docker compose up --build -d
docker compose exec web python manage.py createsuperuser   # opcional, para /admin/
```

El modelo LLM se descarga **en build-time** dentro del Dockerfile y queda
horneado en `/app/models/model.gguf` — el contenedor `web` no necesita
salida a internet en runtime. Si el servidor de build tampoco tiene
internet, descarga el `.gguf` manualmente y ajusta el Dockerfile para
copiarlo desde el contexto de build en vez de descargarlo.

La API queda expuesta detrás de `nginx` en `http://<servidor>/`.

## API

- `POST /api/v1/evaluaciones/` — crea una evaluación y ejecuta el pipeline.
- `GET /api/v1/evaluaciones/{id}/` — recupera el resultado.
- `GET /api/v1/evaluaciones/{id}/reporte/` — descarga el reporte **técnico**
  en PDF (para el médico: z-scores, glosario de cada indicador, sugerencias
  de proceso y cómo interpretar las gráficas OMS). Genera y cachea la
  primera vez.
- `GET /api/v1/evaluaciones/{id}/reporte-familiar/` — descarga el reporte
  en **lenguaje sencillo** para la familia/cuidador (sin z-scores ni jerga
  médica, con semáforo verde/amarillo/rojo por indicador y próximos pasos).
- `GET /api/v1/pacientes/{id}/evaluaciones/` — historial longitudinal.

Ambos PDFs comparten los mismos hallazgos (calculados una sola vez de forma
determinística) pero cada uno tiene su propio texto de síntesis generado
por el LLM local -- dos nodos del grafo LangGraph corren en paralelo,
`sintesis_clinica` y `sintesis_familiar`, cada uno con su propio prompt.
Las sugerencias de "próximos pasos" (remisión, seguimiento, vigilancia) son
texto fijo por reglas clínicas (`apps/agents/clinical_actions.py`), no
generado por el LLM -- el LLM solo las redacta en prosa, nunca decide ni
inventa sugerencias nuevas.

Ejemplo de payload:

```json
{
  "sexo": "M",
  "edad_meses": 14,
  "peso_kg": 8.7,
  "talla_cm": 76.5,
  "tipo_medicion_talla": "acostado",
  "perimetro_cefalico_cm": 45.2,
  "perimetro_braquial_cm": 14.1,
  "edema_bilateral": false,
  "paciente": {
    "nombres": "Ejemplo",
    "apellidos": "Paciente",
    "fecha_nacimiento": "2024-06-01"
  }
}
```

`paciente` es opcional; si se omite, el sistema crea un registro mínimo
para poder persistir el historial de todas formas.

## Tests

```bash
source .venv/bin/activate
python -m pytest
```

Incluye validación de la matemática LMS contra los valores reales
publicados por la OMS (no valores inventados), tests de clasificación
clínica (bordes de cada corte, override de edema, bypass de MUAC), y tests
de API end-to-end (con el nodo LLM mockeado para no depender de un modelo
real en CI).

## Advertencias clínicas conocidas (revisar antes de producción real)

- La corrección de 0.7cm entre longitud (acostado) y talla (de pie) —
  `apps/who_standards/indicators.py::CORRECCION_LONGITUD_TALLA_CM` — se
  implementó según una fuente secundaria (no se pudo verificar contra el
  PDF técnico primario de la OMS en esta sesión). Confirmar antes de usar
  con pacientes reales.
- Los resúmenes (clínico y familiar) los redacta un LLM local pequeño
  (3B parámetros); aunque el prompt lo restringe a no inventar/corregir
  números y se probó activamente para detectar contradicciones (dos
  errores de este tipo se encontraron y corrigieron durante el desarrollo:
  el modelo afirmando una alerta que no existía y mezclando
  "normal" con "moderado" para el mismo hallazgo), sigue siendo texto
  generado por IA — todo reporte debe ser revisado por un profesional
  médico antes de usarse clínicamente (ver aviso en ambos PDF). Los datos
  duros (z-scores, clasificaciones, glosario, sugerencias) siempre se
  calculan y muestran de forma determinística, nunca por el LLM.
- Los dos nodos de síntesis (clínico y familiar) comparten una sola
  instancia del modelo cargado en memoria y sus llamadas de inferencia se
  serializan con un lock (`apps/agents/llm.py`) — `llama-cpp-python` no es
  seguro para inferencia concurrente sobre el mismo objeto `Llama` desde
  varios hilos (se detectó un segfault real en esta sesión al correrlas
  sin serializar). Esto significa que, aunque el grafo las declara en
  paralelo, en la práctica el segundo resumen espera a que termine el
  primero -- una decisión intencional para no duplicar ~2GB de RAM con un
  segundo modelo cargado.

"""Carga perezosa y en singleton del modelo LLM local (GGUF) usado por los
nodos de síntesis (clínica y familiar). No se usa ningún proveedor de LLM
pago: todo corre en el mismo contenedor vía llama-cpp-python.

El grafo LangGraph ejecuta los dos nodos de síntesis EN PARALELO (mismo
superstep, hilos distintos). Un objeto `llama_cpp.Llama` no es seguro para
inferencia concurrente desde múltiples hilos sobre la misma instancia --
llamarlo así puede segfaultear el proceso. `_inference_lock` serializa las
llamadas reales de inferencia (no la carga del modelo) para que ambos
nodos puedan compartir una sola instancia cargada en memoria sin duplicar
~2GB de RAM por un segundo modelo, a costa de que sus dos llamadas al LLM
se ejecuten una tras otra en vez de verdaderamente en paralelo."""

import threading

from django.conf import settings
from llama_cpp import Llama

_load_lock = threading.Lock()
_inference_lock = threading.Lock()
_llm_instance: Llama | None = None


def get_llm() -> Llama:
    global _llm_instance
    if _llm_instance is None:
        with _load_lock:
            if _llm_instance is None:
                _llm_instance = Llama(
                    model_path=settings.LLM_MODEL_PATH,
                    n_ctx=settings.LLM_CONTEXT_SIZE,
                    n_threads=settings.LLM_N_THREADS or None,
                    verbose=False,
                )
    return _llm_instance


def generar_texto(prompt_sistema: str, prompt_usuario: str) -> str:
    llm = get_llm()
    with _inference_lock:
        respuesta = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
        )
    return respuesta["choices"][0]["message"]["content"].strip()

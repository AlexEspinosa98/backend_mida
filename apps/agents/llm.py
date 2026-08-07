"""Carga perezosa y en singleton del modelo LLM local (GGUF) usado
únicamente por el nodo de síntesis clínica. No se usa ningún proveedor
de LLM pago: todo corre en el mismo contenedor vía llama-cpp-python."""

import threading

from django.conf import settings
from llama_cpp import Llama

_lock = threading.Lock()
_llm_instance: Llama | None = None


def get_llm() -> Llama:
    global _llm_instance
    if _llm_instance is None:
        with _lock:
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
    respuesta = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario},
        ],
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
    )
    return respuesta["choices"][0]["message"]["content"].strip()

from .base import *  # noqa: F401,F403

DEBUG = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Prefijo con el que nginx monta esta app (ej. /api/mida) -- hace que Django genere URLs
# (reverse(), admin, y get_script_prefix() usado a mano en apps/assessments/serializers.py para
# las URLs de PDF) con el prefijo correcto en vez de asumir que la app vive en la raíz del
# dominio. Vacío/no definido = comportamiento normal (app en la raíz), sin romper nada para
# quien corra esto en otro lado sin el nginx compartido de este servidor.
FORCE_SCRIPT_NAME = env("DJANGO_FORCE_SCRIPT_NAME", default=None) or None
